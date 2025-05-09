from rest_framework import generics, viewsets, status, views, filters
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import APIException
from django_filters.rest_framework import DjangoFilterBackend # For filtering list views
from .models import Document, GeneratedContent, Standard, StandardType
from .serializers import (
    DocumentSerializer,
    GeneratedContentSerializer,
    ContentGenerationRequestSerializer,
    StandardTypeSerializer,
    StandardCreateUpdateSerializer,
    StandardDetailSerializer
)
from .services import document_processor, rag_retriever, llm_engine, validator
from .services.validator import VALIDATION_MODEL_NAME
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
        standard_type_id = request.data.get('standard_type_id')

        if not file_obj:
            return Response({"error": "File not provided."}, status=status.HTTP_400_BAD_REQUEST)
        if not standard_type_id:
            return Response({"error": "Standard type ID not provided."}, status=status.HTTP_400_BAD_REQUEST)

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
                standard_type_id=standard_type_id
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
            logger.exception("Unexpected error during document upload and processing.")
            return Response({"error": f"Unexpected error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, document_id=None, *args, **kwargs):
        """
        Get all documents or a specific document by ID.
        If document_id is provided, returns a single document's metadata.
        Otherwise, returns a list of all documents.
        """
        if document_id:
            return self.view_document_by_id(request, document_id)
        else:
            return self.get_all_documents(request)

    def delete(self, request, document_id, *args, **kwargs):
        """
        Delete a document by ID, including its file in storage and related chunks.
        """
        success, error = document_processor.delete_document(document_id)
        if error:
            status_code = status.HTTP_404_NOT_FOUND if "not found" in error else status.HTTP_500_INTERNAL_SERVER_ERROR
            return Response({"error": error}, status=status_code)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_all_documents(self, request):
        """
        Returns a list of all uploaded documents with metadata.
        """
        documents, error = document_processor.get_all_documents()
        if error:
            return Response({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(documents, status=status.HTTP_200_OK)

    def view_document_by_id(self, request, document_id):
        """
        Retrieves and returns metadata of a single document by its ID.
        """
        document_data, error = document_processor.get_document_by_id(document_id)
        if error:
            status_code = status.HTTP_404_NOT_FOUND if "not found" in error else status.HTTP_500_INTERNAL_SERVER_ERROR
            return Response({"error": error}, status=status_code)
        return Response(document_data, status=status.HTTP_200_OK)

class ContentGenerationView(views.APIView):
    def post(self, request, *args, **kwargs):
        serializer = ContentGenerationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        topic = validated_data['topic']
        content_type = validated_data['content_type']
        model_name = validated_data['model_name']

         # Get standard type name
        standard_type = StandardType.objects.get(id=content_type, is_deleted=False)
        standard_type_name = standard_type.name
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
                content_type=standard_type_name,
                model_name=model_name,
                context=context # Will be None if fallback
            )

            # 3. Validation - Commented out
            # validation_results = validator.validate_generated_output(generated_text)
            # if 'error' in validation_results:
            #      logger.warning(f"Validation process encountered an issue: {validation_results['error']}")
            #      # Decide if you want to proceed without validation results or fail
            
            # Use empty dict for validation_results since we're skipping validation
            validation_results = {}

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
            model_list = list(llm_engine.AVAILABLE_MODELS.keys())
            return Response({"models": model_list}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception("Error retrieving available models")
            return Response(
                {"error": "Failed to retrieve available models"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class StandardTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing standard types.
    """
    queryset = StandardType.objects.filter(is_deleted=False)
    serializer_class = StandardTypeSerializer

class MedicalStandardView(views.APIView):
    """
    API endpoint for managing medical standards.
    """
    
    def post(self, request, *args, **kwargs):
        """
        Save a new medical standard.
        """
        serializer = StandardCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            standard = serializer.save()
            response_serializer = StandardDetailSerializer(standard)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, standard_id, *args, **kwargs):
        """
        Update an existing medical standard.
        """
        try:
            standard = Standard.objects.get(id=standard_id, is_deleted=False)
        except Standard.DoesNotExist:
            return Response({"error": "Standard not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = StandardCreateUpdateSerializer(standard, data=request.data, partial=True)
        if serializer.is_valid():
            updated_standard = serializer.save()
            response_serializer = StandardDetailSerializer(updated_standard)
            return Response(response_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, standard_id, *args, **kwargs):
        """
        Soft delete a medical standard.
        """
        try:
            standard = Standard.objects.get(id=standard_id, is_deleted=False)
        except Standard.DoesNotExist:
            return Response({"error": "Standard not found"}, status=status.HTTP_404_NOT_FOUND)
        
        standard.is_deleted = True
        standard.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def get(self, request, standard_id=None, *args, **kwargs):
        """
        Get a specific medical standard or list standards filtered by standard_type_id.
        """
        if standard_id:
            try:
                # Using select_related to perform the JOINs
                standard = Standard.objects.select_related(
                    'standard_type', 'generated_content'
                ).get(id=standard_id, is_deleted=False)
                serializer = StandardDetailSerializer(standard)
                return Response(serializer.data)
            except Standard.DoesNotExist:
                return Response({"error": "Standard not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Get standard_type_id from query parameters
            standard_type_id = request.query_params.get('standard_type_id')
            
            # Start with base queryset
            queryset = Standard.objects.select_related(
                'standard_type', 'generated_content'
            ).filter(is_deleted=False)
            
            # Filter by standard_type_id if provided
            if standard_type_id:
                queryset = queryset.filter(standard_type_id=standard_type_id)
                
            serializer = StandardDetailSerializer(queryset, many=True)
            return Response(serializer.data)
    
    def compare_standards(self, request, *args, **kwargs):
        """
        Compare two standard contents and analyze their differences using LLM.
        
        Expects:
        - content1: First standard content
        - content2: Second standard content
        - standard_type_id: UUID of the standard type
        """
        content1 = request.data.get('content1')
        content2 = request.data.get('content2')
        standard_type_id = request.data.get('standard_type_id')
        
        # Validate inputs
        if not content1 or not content2 or not standard_type_id:
            return Response(
                {"error": "Missing required parameters. Please provide content1, content2, and standard_type_id."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get standard type name
            standard_type = StandardType.objects.get(id=standard_type_id, is_deleted=False)
            standard_type_name = standard_type.name
        except StandardType.DoesNotExist:
            return Response(
                {"error": f"Standard type with ID {standard_type_id} not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Use the validation model for comparison
            comparison_result = llm_engine.compare_standard_contents(
                content1=content1,
                content2=content2,
                standard_type=standard_type_name,
                model_name=VALIDATION_MODEL_NAME
            )
            
            return Response(comparison_result, status=status.HTTP_200_OK)
                
        except ValueError as ve:
            logger.error(f"Validation error: {ve}")
            return Response(
                {"error": str(ve)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except RuntimeError as re:
            logger.error(f"Runtime error during comparison: {re}")
            return Response(
                {"error": f"Error comparing standards: {str(re)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error during comparison: {e}")
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class StandardSearchView(views.APIView):
    """
    API endpoint for searching medical standards.
    """
    
    def get(self, request, *args, **kwargs):
        """
        Search standards by type or title.
        """
        standard_type_id = request.query_params.get('standard_type_id')
        standard_title = request.query_params.get('standard_title')
        
        if not standard_type_id and not standard_title:
            return Response(
                {"error": "Please provide at least one search parameter (standard_type_id or standard_title)"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = Standard.objects.select_related(
            'standard_type', 'generated_content'
        ).filter(is_deleted=False)
        
        if standard_type_id:
            queryset = queryset.filter(standard_type_id=standard_type_id)
        
        if standard_title:
            queryset = queryset.filter(standard_title__icontains=standard_title)
        
        serializer = StandardDetailSerializer(queryset, many=True)
        return Response(serializer.data)

# Add this new view class for handling standard comparisons
class MedicalStandardCompareView(views.APIView):
    """
    API endpoint for comparing two medical standards.
    """
    def post(self, request):
        """
        Compare two standard contents and analyze their differences using LLM.
        
        Expects:
        - content1: First standard content
        - content2: Second standard content
        - standard_type_id: UUID of the standard type
        """
        content1 = request.data.get('content1')
        content2 = request.data.get('content2')
        standard_type_id = request.data.get('standard_type_id')
        
        # Validate inputs
        if not content1 or not content2 or not standard_type_id:
            return Response(
                {"error": "Missing required parameters. Please provide content1, content2, and standard_type_id."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get standard type name
            standard_type = StandardType.objects.get(id=standard_type_id, is_deleted=False)
            standard_type_name = standard_type.name
        except StandardType.DoesNotExist:
            return Response(
                {"error": f"Standard type with ID {standard_type_id} not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Use the validation model for comparison
            comparison_result = llm_engine.compare_standard_contents(
                content1=content1,
                content2=content2,
                standard_type=standard_type_name,
                model_name=VALIDATION_MODEL_NAME
            )
            
            return Response(comparison_result, status=status.HTTP_200_OK)
                
        except ValueError as ve:
            logger.error(f"Validation error: {ve}")
            return Response(
                {"error": str(ve)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except RuntimeError as re:
            logger.error(f"Runtime error during comparison: {re}")
            return Response(
                {"error": f"Error comparing standards: {str(re)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error during comparison: {e}")
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DocumentDownloadView(views.APIView):
    """
    API endpoint for downloading document files.
    """
    def get(self, request, document_id, *args, **kwargs):
        """
        Downloads a document file from Supabase storage.
        """
        file_content, file_name, content_type, error = document_processor.download_document(document_id)
        
        if error:
            status_code = status.HTTP_404_NOT_FOUND if "not found" in error else status.HTTP_500_INTERNAL_SERVER_ERROR
            return Response({"error": error}, status=status_code)
        
        # Create Django response with file content
        from django.http import HttpResponse
        response = HttpResponse(file_content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        
        return response
