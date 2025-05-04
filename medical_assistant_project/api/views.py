from rest_framework import generics, viewsets, status, views
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import APIException
from django_filters.rest_framework import DjangoFilterBackend # For filtering list views
from .models import Document, GeneratedContent
from .serializers import (
    DocumentSerializer,
    GeneratedContentSerializer,
    ContentGenerationRequestSerializer
)
from .services import document_processor, rag_retriever, llm_engine, validator
from .services.llm_engine import AVAILABLE_MODELS
import logging

logger = logging.getLogger(__name__)

class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = 'Service temporarily unavailable, try again later.'
    default_code = 'service_unavailable'

class DocumentUploadView(views.APIView):
    parser_classes = (MultiPartParser, FormParser)


    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        document_type = request.data.get('document_type')

        if not file_obj:
            return Response({"error": "File not provided."}, status=status.HTTP_400_BAD_REQUEST)
        if not document_type:
            return Response({"error": "Document type not provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Basic validation for file type (can be enhanced)
        allowed_extensions = ['.pdf', '.docx']
        import os
        ext = os.path.splitext(file_obj.name)[1].lower()
        if ext not in allowed_extensions:
             return Response({"error": f"Unsupported file type '{ext}'. Only PDF and DOCX allowed."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            doc_instance = document_processor.process_and_store_document(
                file_obj=file_obj,
                original_filename=file_obj.name,
                document_type=document_type
            )
            serializer = DocumentSerializer(doc_instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as ve:
            logger.warning(f"Document processing validation error: {ve}")
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except ConnectionError as ce:
             logger.error(f"Document processing connection error: {ce}")
             raise ServiceUnavailable(f"Storage connection error: {ce}")
        except RuntimeError as re:
             logger.error(f"Document processing runtime error: {re}")
             raise ServiceUnavailable(f"Processing error: {re}")
        except Exception as e:
            logger.exception("Unexpected error during document upload and processing.") # Log full traceback
            return Response({"error": "An unexpected server error occurred during processing."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ContentGenerationView(views.APIView):
    def post(self, request, *args, **kwargs):
        serializer = ContentGenerationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        topic = validated_data['topic']
        content_type = validated_data['content_type']
        model_name = validated_data['model_name']

        try:
            # 1. RAG Retrieval
            context, source_chunk_ids_or_error = rag_retriever.retrieve_relevant_chunks(query=topic)
            if context is None and isinstance(source_chunk_ids_or_error, str) and "Failed" in source_chunk_ids_or_error:
                 # Handle embedding or search failure differently from just 'not found'
                 logger.error(f"RAG retrieval failed: {source_chunk_ids_or_error}")
                 raise ServiceUnavailable(f"Knowledge base search failed: {source_chunk_ids_or_error}")
            elif context is None:
                 logger.info(f"No relevant context found for '{topic}'. Proceeding with fallback generation.")
                 source_chunk_ids = [] # Empty list if no context found
            else:
                 source_chunk_ids = source_chunk_ids_or_error # We got chunk IDs


            # 2. LLM Generation
            generated_text = llm_engine.generate_content_with_llm(
                topic=topic,
                content_type=content_type,
                model_name=model_name,
                context=context # Will be None if fallback
            )

            # 3. Validation
            validation_results = validator.validate_generated_output(generated_text)
            if 'error' in validation_results:
                 logger.warning(f"Validation process encountered an issue: {validation_results['error']}")
                 # Decide if you want to proceed without validation results or fail

            # 4. Store Generated Content
            content_instance = GeneratedContent.objects.create(
                topic=topic,
                content_type=content_type,
                generated_text=generated_text,
                llm_model_used=model_name,
                source_chunk_ids=source_chunk_ids, # Store the list of chunk IDs
                validation_results=validation_results
            )

            response_serializer = GeneratedContentSerializer(content_instance)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except ValueError as ve: # e.g., Invalid model name passed validation somehow
            logger.warning(f"Content generation input error: {ve}")
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except (ConnectionError, RuntimeError, ServiceUnavailable) as se: # Catch specific service/LLM errors
             logger.error(f"Content generation service error: {se}")
             # Use the status code from ServiceUnavailable if it's that type
             status_code = se.status_code if isinstance(se, ServiceUnavailable) else status.HTTP_503_SERVICE_UNAVAILABLE
             return Response({"error": f"Generation service error: {se}"}, status=status_code)
        except Exception as e:
            logger.exception("Unexpected error during content generation.")
            return Response({"error": "An unexpected server error occurred during generation."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GeneratedContentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing generated content.
    Supports filtering by content_type, llm_model_used, and date range.
    Example query: /api/generated-content/?content_type=Policy&llm_model_used=llama3-8b-instruct&created_after=2024-01-01
    """
    
    queryset = GeneratedContent.objects.all().order_by('-created_at')
    serializer_class = GeneratedContentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'content_type': ['exact', 'icontains'],
        'llm_model_used': ['exact'],
        'created_at': ['gte', 'lte', 'exact', 'date__gte', 'date__lte'], # Allows filtering by date ranges
        'topic': ['icontains'] # Add topic search
        # Filtering by validation score might require custom filter logic if score is nested in JSON
    }
    # Add pagination later if needed:
    # pagination_class = PageNumberPagination

class AvailableModelsView(views.APIView):
    """
    API endpoint that returns the list of available AI models.
    """
    def get(self, request, *args, **kwargs):
        try:
            # Extract just the model names (keys) from AVAILABLE_MODELS
            model_list = list(AVAILABLE_MODELS.keys())
            return Response({"models": model_list}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception("Error retrieving available models")
            return Response(
                {"error": "Failed to retrieve available models"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
