from rest_framework import generics, viewsets, status, views, filters
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import APIException
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend # For filtering list views
from .models import (
    Document, GeneratedContent, Standard, StandardType, QuestionOption, AuditQuestion,
    Practice, FeedbackMethod, Feedback, FeedbackAttachment
)
from .models import Document, GeneratedContent, Standard, StandardType, QuestionOption, AuditQuestion, Complaint
from .serializers import (
    DocumentSerializer,
    GeneratedContentSerializer,
    ContentGenerationRequestSerializer,
    StandardTypeSerializer,
    StandardCreateUpdateSerializer,
    StandardDetailSerializer,
    QuestionOptionSerializer,
    AuditQuestionSerializer,
    AuditQuestionGenerationRequestSerializer,
    PracticeSerializer,
    FeedbackMethodSerializer,
    FeedbackSerializer,
    FeedbackListSerializer,
    FeedbackAttachmentSerializer,
    AuditQuestionGenerationRequestSerializer,
    ComplaintSerializer,
)
from .services import document_processor, rag_retriever, llm_engine, validator, feedback_processor, complaint_service
from .services.validator import VALIDATION_MODEL_NAME
import logging
import re
import json
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
logger = logging.getLogger(__name__)
from .services import user_service

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

class AuditQuestionGeneratorView(views.APIView):
    """
    API endpoint for generating audit questions based on a policy using OpenRouter API.
    """
    def post(self, request, *args, **kwargs):
        """
        Generate audit questions based on a policy using an AI model.

        Expects:
        - ai_model: The AI model to use from OpenRouter
        - policy_name: The name of the policy to generate questions about
        - number_of_questions: The total number of questions to generate
        """
        serializer = AuditQuestionGenerationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        ai_model = validated_data['ai_model']
        policy_name = validated_data['policy_name']
        number_of_questions = validated_data['number_of_questions']

        try:
            llm = llm_engine.get_llm_instance(ai_model)

            prompt = f"""
            Generate {number_of_questions} audit questions for the policy named "{policy_name}".

            Each question should be designed to assess compliance with the policy.
            Format the response as a JSON array of objects, where each object has the following structure:
            {{
                "question_text": "The text of the audit question",
                "options": ["Compliant", "Partial Compliant", "Non Compliant"]
            }}

            Make sure the questions are specific, clear, and directly related to compliance with the policy.
            IMPORTANT: The response should ONLY be the JSON array itself, without any surrounding text, explanations, or markdown formatting like ```json or ```.
            """ # Added a more explicit instruction to the LLM

            generated_text_raw = llm.invoke(prompt)

            # --- SOLUTION: Extract JSON from Markdown code block ---
            cleaned_json_text = generated_text_raw
            # Regex to find JSON possibly wrapped in markdown code blocks
            # It looks for ```json ... ``` or just ``` ... ```
            # and extracts the content within.
            # [\s\S] matches any character including newlines.
            # *? makes it non-greedy.
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", generated_text_raw)
            if match:
                cleaned_json_text = match.group(1).strip() # Get the captured group and strip whitespace
            else:
                # If no markdown block is found, try a more general cleanup.
                # This attempts to find the first '{' or '[' and the last '}' or ']'
                # This is a heuristic and might need adjustment if the LLM output varies a lot.
                start_json = -1
                end_json = -1

                first_brace = cleaned_json_text.find('{')
                first_bracket = cleaned_json_text.find('[')

                if first_brace != -1 and first_bracket != -1:
                    start_json = min(first_brace, first_bracket)
                elif first_brace != -1:
                    start_json = first_brace
                elif first_bracket != -1:
                    start_json = first_bracket


                if start_json != -1:
                    last_brace = cleaned_json_text.rfind('}')
                    last_bracket = cleaned_json_text.rfind(']')


                    if last_brace != -1 and last_bracket != -1:
                        end_json = max(last_brace, last_bracket)
                    elif last_brace != -1:
                        end_json = last_brace
                    elif last_bracket != -1:
                        end_json = last_bracket


                    if end_json != -1 and end_json >= start_json:
                        cleaned_json_text = cleaned_json_text[start_json : end_json+1]
                    else: # Fallback if sensible end not found
                        cleaned_json_text = cleaned_json_text.strip()
                        cleaned_json_text = cleaned_json_text.strip()
                else: # Fallback if sensible start not found
                    cleaned_json_text = cleaned_json_text.strip()
            # --- END SOLUTION ---

            try:
                # Parse the cleaned text as JSON
                questions_data = json.loads(cleaned_json_text)

                if not isinstance(questions_data, list):
                    # Log the problematic data for inspection
                    logger.error(f"Generated content parsed but is not a list. Content: {cleaned_json_text[:500]}") # Log first 500 chars
                    raise ValueError("Generated content is not a list of questions")

                stored_questions = []
                for question_data in questions_data:
                    if not isinstance(question_data, dict) or 'question_text' not in question_data:
                        logger.warning(f"Skipping malformed question object in list: {question_data}")
                        continue

                    question = AuditQuestion.objects.create(
                        question_text=question_data['question_text'],
                        policy_name=policy_name,
                        ai_model=ai_model,
                        options=question_data.get('options', ["Compliant", "Partial Compliant", "Non Compliant"])
                    )
                    stored_questions.append(question)

                serializer_out = AuditQuestionSerializer(stored_questions, many=True) # Renamed to avoid conflict
                return Response(serializer_out.data, status=status.HTTP_201_CREATED)

            except json.JSONDecodeError as e:
                # Log both raw and cleaned text for better debugging
                logger.error(
                    f"Failed to parse generated content as JSON: {e}. "
                    f"Raw text (first 500 chars): '{generated_text_raw[:500]}...'. "
                    f"Cleaned text (first 500 chars): '{cleaned_json_text[:500]}...'"
                )
                return Response(
                    {"error": "Failed to parse generated content as JSON from AI model. The model might have returned an invalid format."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            except ValueError as ve: # This will catch the "Generated content is not a list"
                logger.warning(f"Validation error in generated JSON structure: {ve}. Cleaned JSON: {cleaned_json_text[:500]}")
                return Response({"error": str(ve)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        except ValueError as ve: # This is for serializer.validated_data or llm_engine.get_llm_instance
            logger.warning(f"Audit question generation input error: {ve}")
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        # Make sure ServiceUnavailable is defined or imported if you use it
        # For example, if it's from openai: from openai import APIError as ServiceUnavailable
        # Or if it's a custom exception. For now, I'll make it more generic.
        except (ConnectionError, RuntimeError) as se: # Removed ServiceUnavailable for now, ensure it's defined if used
            logger.error(f"Audit question generation service error: {se}")
            # status_code = se.status_code if hasattr(se, 'status_code') and isinstance(se, ServiceUnavailable) else status.HTTP_503_SERVICE_UNAVAILABLE
            # Simplified for now:
            return Response({"error": f"Generation service error: {str(se)}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            logger.exception("Unexpected error during audit question generation.")
            return Response(
                {"error": f"An unexpected server error occurred during generation: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class AuditQuestionUpdateView(views.APIView):
    """
    API endpoint for updating a specific audit question.
    """
    def put(self, request, question_id, *args, **kwargs):
        """
        Update a specific audit question by its ID.
        """
        try:
            question = AuditQuestion.objects.get(id=question_id)
        except AuditQuestion.DoesNotExist:
            return Response({"error": "Audit question not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = AuditQuestionSerializer(question, data=request.data, partial=True)
        if serializer.is_valid():
            updated_question = serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AuditQuestionDeleteView(views.APIView):
    """
    API endpoint for deleting a specific audit question.
    """
    def delete(self, request, question_id, *args, **kwargs):
        """
        Delete a specific audit question by its ID.
        """
        try:
            question = AuditQuestion.objects.get(id=question_id)
        except AuditQuestion.DoesNotExist:
            return Response({"error": "Audit question not found"}, status=status.HTTP_404_NOT_FOUND)

        question.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class AuditQuestionListView(views.APIView):
    """
    API endpoint for listing all audit questions.
    """
    def get(self, request, *args, **kwargs):
        """
        Get all audit questions with optional filtering by policy_name.
        """
        policy_name = request.query_params.get('policy_name')

        # Start with all questions
        queryset = AuditQuestion.objects.all().order_by('-created_at')

        # Filter by policy_name if provided
        if policy_name:
            queryset = queryset.filter(policy_name__icontains=policy_name)

        serializer = AuditQuestionSerializer(queryset, many=True)
        return Response(serializer.data)

class PracticeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing medical practices.
    """
    queryset = Practice.objects.filter(is_active=True)
    serializer_class = PracticeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['name', 'is_active']
    search_fields = ['name', 'address', 'email']

class FeedbackMethodViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing feedback methods.
    """
    queryset = FeedbackMethod.objects.all()
    serializer_class = FeedbackMethodSerializer

class FeedbackViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing patient feedback.
    Supports filtering by status, practice, submitter, date ranges, etc.
    """
    queryset = Feedback.objects.all().order_by('-created_at')
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = {
        'status': ['exact'],
        'practice': ['exact'],
        'submitter': ['exact'],
        'management_owner': ['exact'],
        'review_requested_by': ['exact'],
        'form_date': ['gte', 'lte', 'exact'],
        'date_received': ['gte', 'lte', 'exact'],
        'created_at': ['gte', 'lte', 'date__gte', 'date__lte'],
    }
    search_fields = ['title', 'reference_number', 'patient_nhi', 'feedback_details']

    def get_serializer_class(self):
        """
        Return different serializers for list and detail views.
        """
        if self.action == 'list':
            return FeedbackListSerializer
        return FeedbackSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new feedback entry with optional file attachments.
        """
        # Extract files from request
        files = request.FILES.getlist('attachments')

        # Create serializer with data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Save feedback instance
        feedback = serializer.save()

        # Process attachments if any
        if files:
            for file in files:
                try:
                    feedback_processor.process_and_store_attachment(file, feedback)
                except Exception as e:
                    logger.error(f"Error processing attachment: {e}")
                    # Continue with other attachments even if one fails

        # Return the created feedback with updated serializer that includes attachments
        serializer = self.get_serializer(feedback)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['post'])
    def add_attachment(self, request, pk=None):
        """
        Add an attachment to an existing feedback entry.
        """
        feedback = self.get_object()
        file = request.FILES.get('file')

        if not file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            attachment = feedback_processor.process_and_store_attachment(file, feedback)
            serializer = FeedbackAttachmentSerializer(attachment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error adding attachment: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['delete'])
    def remove_attachment(self, request, pk=None):
        """
        Remove an attachment from a feedback entry.
        """
        attachment_id = request.query_params.get('attachment_id')
        if not attachment_id:
            return Response({"error": "attachment_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        success, error = feedback_processor.delete_feedback_attachment(attachment_id)
        if error:
            status_code = status.HTTP_404_NOT_FOUND if "not found" in error else status.HTTP_500_INTERNAL_SERVER_ERROR
            return Response({"error": error}, status=status_code)

        return Response(status=status.HTTP_204_NO_CONTENT)

class FeedbackAttachmentDownloadView(views.APIView):
    """
    API endpoint for downloading feedback attachments.
    """
    def get(self, request, attachment_id, *args, **kwargs):
        """
        Downloads a feedback attachment file from Supabase storage.
        """
        file_content, file_name, content_type, error = feedback_processor.get_feedback_attachment(attachment_id)

        if error:
            status_code = status.HTTP_404_NOT_FOUND if "not found" in error else status.HTTP_500_INTERNAL_SERVER_ERROR
            return Response({"error": error}, status=status_code)

        # Create Django response with file content
        from django.http import HttpResponse
        response = HttpResponse(file_content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'

        return response


class ComplaintView(views.APIView):
    """
    API endpoint for managing complaints.
    """
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, complaint_id=None, *args, **kwargs):
        """
        Get all complaints or a specific complaint by ID.
        If complaint_id is provided, returns a single complaint.
        Otherwise, returns a list of all complaints.
        """
        if complaint_id:
            complaint, error = complaint_service.get_complaint_by_id(complaint_id)
            if error:
                status_code = status.HTTP_404_NOT_FOUND if "not found" in error else status.HTTP_500_INTERNAL_SERVER_ERROR
                return Response({"error": error}, status=status_code)
            serializer = ComplaintSerializer(complaint)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            complaints, error = complaint_service.get_all_complaints()
            if error:
                return Response({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            serializer = ComplaintSerializer(complaints, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """
        Create a new complaint.
        """
        # Handle file upload if present
        file_obj = request.FILES.get('file_upload')
        file_upload_path = None

        if file_obj:
            # Upload file to Supabase storage
            file_upload_path, error = complaint_service.upload_complaint_file(file_obj, file_obj.name)
            if error:
                return Response({"error": f"File upload failed: {error}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Create serializer with request data
        serializer = ComplaintSerializer(data=request.data)
        if serializer.is_valid():
            # Save complaint with file path if uploaded
            complaint = serializer.save(file_upload_path=file_upload_path)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, complaint_id, *args, **kwargs):
        """
        Update an existing complaint.
        """
        try:
            complaint = Complaint.objects.get(id=complaint_id)
        except Complaint.DoesNotExist:
            return Response({"error": "Complaint not found"}, status=status.HTTP_404_NOT_FOUND)

        # Handle file upload if present
        file_obj = request.FILES.get('file_upload')
        if file_obj:
            # Upload new file to Supabase storage
            file_upload_path, error = complaint_service.upload_complaint_file(file_obj, file_obj.name)
            if error:
                return Response({"error": f"File upload failed: {error}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Update file path in request data
            request.data['file_upload_path'] = file_upload_path

        # Update complaint with request data
        serializer = ComplaintSerializer(complaint, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, complaint_id, *args, **kwargs):
        """
        Delete a complaint by ID, including its file in storage.
        """
        success, error = complaint_service.delete_complaint(complaint_id)
        if error:
            status_code = status.HTTP_404_NOT_FOUND if "not found" in error else status.HTTP_500_INTERNAL_SERVER_ERROR
            return Response({"error": error}, status=status_code)
        return Response(status=status.HTTP_204_NO_CONTENT)

class UserListView(views.APIView):
    """
    API endpoint for listing all users from Supabase auth.
    """
    def get(self, request, *args, **kwargs):
        """
        Get all users from Supabase auth.users table.
        """
        users, error = user_service.get_all_users()
        if error:
            return Response({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(users, status=status.HTTP_200_OK)


# Chatbot Views
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.parsers import JSONParser
from .models import (
    ChatbotIntent, ChatbotResponse, ChatbotConversation, ChatbotMessage,
    ChatbotQuickAction
)
from .serializers import (
    ChatbotIntentSerializer, ChatbotResponseSerializer, ChatbotConversationSerializer,
    ChatbotConversationListSerializer, ChatbotMessageSerializer, ChatbotQuickActionSerializer,
    ChatbotMessageRequestSerializer, ChatbotIntentDetectionSerializer,
    ChatbotActionRequestSerializer, ChatbotResponseDataSerializer
)
from .services.chatbot_engine import ChatbotEngine


@method_decorator(csrf_exempt, name='dispatch')
class ChatbotMessageView(views.APIView):
    """
    Main chatbot endpoint for processing user messages.
    """
    parser_classes = [JSONParser]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._chatbot_engine = None

    @property
    def chatbot_engine(self):
        if self._chatbot_engine is None:
            self._chatbot_engine = ChatbotEngine()
        return self._chatbot_engine

    def post(self, request, *args, **kwargs):
        """
        Process user message and return chatbot response.
        """
        try:
            import json

            # Parse JSON data from request body
            if hasattr(request, 'data'):
                # DRF request
                request_data = request.data
            else:
                # Standard Django request
                request_data = json.loads(request.body.decode('utf-8'))

            serializer = ChatbotMessageRequestSerializer(data=request_data)
            if not serializer.is_valid():
                return Response({
                    'error': 'Invalid request data',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            validated_data = serializer.validated_data
            message = validated_data['message']
            session_id = validated_data.get('session_id')
            user_context = validated_data.get('user_context', {})

            # Get user if authenticated
            user = None
            if hasattr(request, 'user') and request.user and request.user.is_authenticated:
                user = request.user
            elif user_context.get('user_id'):
                try:
                    user = User.objects.get(id=user_context['user_id'])
                except User.DoesNotExist:
                    pass

            # Process message through chatbot engine
            response_data = self.chatbot_engine.process_message(
                message=message,
                session_id=session_id,
                user=user,
                context=user_context
            )

            # Serialize response
            response_serializer = ChatbotResponseDataSerializer(data=response_data)
            if response_serializer.is_valid():
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            else:
                # Return raw response if serialization fails
                return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in ChatbotMessageView: {e}")
            return Response({
                'error': 'An unexpected error occurred',
                'message': 'I apologize, but I encountered an error. Please try again.',
                'response_type': 'error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatbotIntentDetectionView(views.APIView):
    """
    Endpoint for detecting intent from user message without processing.
    """
    parser_classes = [JSONParser]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._chatbot_engine = None

    @property
    def chatbot_engine(self):
        if self._chatbot_engine is None:
            self._chatbot_engine = ChatbotEngine()
        return self._chatbot_engine

    def post(self, request, *args, **kwargs):
        """
        Detect intent from user message.
        """
        try:
            import json

            # Parse JSON data from request body
            if hasattr(request, 'data'):
                # DRF request
                request_data = request.data
            else:
                # Standard Django request
                request_data = json.loads(request.body.decode('utf-8'))

            serializer = ChatbotIntentDetectionSerializer(data=request_data)
            if not serializer.is_valid():
                return Response({
                    'error': 'Invalid request data',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            message = serializer.validated_data['message']

            # Detect intent
            intent_type, confidence = self.chatbot_engine.intent_detector.detect_intent(message)

            # Get intent details
            intent = ChatbotIntent.objects.filter(intent_type=intent_type, is_active=True).first()

            return Response({
                'intent_type': intent_type,
                'confidence_score': confidence,
                'intent_name': intent.name if intent else None,
                'intent_description': intent.description if intent else None,
                'api_endpoint': intent.api_endpoint if intent else None
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in ChatbotIntentDetectionView: {e}")
            return Response({
                'error': 'An unexpected error occurred during intent detection'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatbotActionView(views.APIView):
    """
    Endpoint for executing specific actions based on intent.
    """
    parser_classes = [JSONParser]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._chatbot_engine = None

    @property
    def chatbot_engine(self):
        if self._chatbot_engine is None:
            self._chatbot_engine = ChatbotEngine()
        return self._chatbot_engine

    def post(self, request, *args, **kwargs):
        """
        Execute action for specific intent.
        """
        try:
            import json

            # Parse JSON data from request body
            if hasattr(request, 'data'):
                # DRF request
                request_data = request.data
            else:
                # Standard Django request
                request_data = json.loads(request.body.decode('utf-8'))

            serializer = ChatbotActionRequestSerializer(data=request_data)
            if not serializer.is_valid():
                return Response({
                    'error': 'Invalid request data',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            validated_data = serializer.validated_data
            intent_type = validated_data['intent_type']
            session_id = validated_data['session_id']
            parameters = validated_data.get('parameters', {})

            # Get user if authenticated
            user = None
            if hasattr(request, 'user') and request.user and request.user.is_authenticated:
                user = request.user

            # Execute action
            response_data = self.chatbot_engine.action_dispatcher.dispatch_action(
                intent_type=intent_type,
                message=f"Action triggered: {intent_type}",
                session_id=session_id,
                user=user,
                parameters=parameters
            )

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in ChatbotActionView: {e}")
            return Response({
                'error': 'An unexpected error occurred during action execution'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatbotQuickActionsView(views.APIView):
    """
    Endpoint for getting available quick actions.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._chatbot_engine = None

    @property
    def chatbot_engine(self):
        if self._chatbot_engine is None:
            self._chatbot_engine = ChatbotEngine()
        return self._chatbot_engine

    def get(self, request, *args, **kwargs):
        """
        Get available quick actions for the user.
        """
        try:
            user = None
            if hasattr(request, 'user') and request.user and request.user.is_authenticated:
                user = request.user

            quick_actions = self.chatbot_engine.get_quick_actions(user)

            return Response({
                'quick_actions': quick_actions,
                'count': len(quick_actions)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in ChatbotQuickActionsView: {e}")
            return Response({
                'error': 'An unexpected error occurred while fetching quick actions'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatbotConversationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing chatbot conversations.
    """
    queryset = ChatbotConversation.objects.all().order_by('-last_activity')

    def get_serializer_class(self):
        if self.action == 'list':
            return ChatbotConversationListSerializer
        return ChatbotConversationSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by user if authenticated
        if self.request.user and self.request.user.is_authenticated:
            queryset = queryset.filter(user=self.request.user)

        # Filter by session_id if provided
        session_id = self.request.query_params.get('session_id')
        if session_id:
            queryset = queryset.filter(session_id=session_id)

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark conversation as completed."""
        try:
            conversation = self.get_object()
            conversation.status = 'completed'
            conversation.completed_at = timezone.now()
            conversation.save()

            serializer = self.get_serializer(conversation)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error completing conversation: {e}")
            return Response({
                'error': 'Failed to complete conversation'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatbotIntentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing chatbot intents (admin/configuration).
    """
    queryset = ChatbotIntent.objects.filter(is_active=True).order_by('intent_type')
    serializer_class = ChatbotIntentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by intent type
        intent_type = self.request.query_params.get('intent_type')
        if intent_type:
            queryset = queryset.filter(intent_type=intent_type)

        # Filter by requires_auth
        requires_auth = self.request.query_params.get('requires_auth')
        if requires_auth is not None:
            requires_auth_bool = requires_auth.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(requires_auth=requires_auth_bool)

        return queryset


class ChatbotHealthView(views.APIView):
    """
    Health check endpoint for the chatbot service.
    """

    def get(self, request, *args, **kwargs):
        """
        Check if the chatbot service is healthy.
        """
        try:
            # Check if intents are loaded
            intent_count = ChatbotIntent.objects.filter(is_active=True).count()

            # Check if responses are available
            response_count = ChatbotResponse.objects.filter(is_active=True).count()

            # Check if quick actions are available
            quick_action_count = ChatbotQuickAction.objects.filter(is_active=True).count()

            return Response({
                'status': 'healthy',
                'service': 'chatbot',
                'version': '1.0.0',
                'statistics': {
                    'active_intents': intent_count,
                    'active_responses': response_count,
                    'active_quick_actions': quick_action_count
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in ChatbotHealthView: {e}")
            return Response({
                'status': 'unhealthy',
                'error': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)