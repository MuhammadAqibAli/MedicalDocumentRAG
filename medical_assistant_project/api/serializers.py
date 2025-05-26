from rest_framework import serializers
from .models import (
    Document, GeneratedContent, DocumentChunk, Standard, StandardType,
    QuestionOption, AuditQuestion, Practice, FeedbackMethod, Feedback, FeedbackAttachment,
    Complaint, ChatbotIntent, ChatbotResponse, ChatbotConversation, ChatbotMessage, ChatbotQuickAction
)
from .services.llm_engine import AVAILABLE_MODELS

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'file_name', 'standard_type', 'uploaded_at', 'metadata']
        read_only_fields = ['id', 'uploaded_at', 'supabase_storage_path'] # Path is internal

class GeneratedContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedContent
        fields = [
            'id', 'topic', 'content_type', 'generated_text', 'llm_model_used',
            'source_chunk_ids', 'validation_results', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

# Optional: Serializer for generating content request
class ContentGenerationRequestSerializer(serializers.Serializer):
    topic = serializers.CharField(max_length=255, required=True)
    content_type = serializers.CharField(max_length=100, required=True)
    model_name = serializers.ChoiceField(choices=list(AVAILABLE_MODELS.keys()), required=True) # Use keys from your config
    # Add other potential parameters like 'force_fallback' if needed

class StandardTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StandardType
        fields = ['id', 'name']

class StandardCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Standard
        fields = ['id', 'standard_title', 'standard_type', 'content', 'version', 'generated_content']
        read_only_fields = ['id']

class StandardDetailSerializer(serializers.ModelSerializer):
    standard_type_name = serializers.CharField(source='standard_type.name', read_only=True)
    llm_model_used = serializers.CharField(source='generated_content.llm_model_used', read_only=True, allow_null=True)
    is_ai_generated = serializers.SerializerMethodField()

    class Meta:
        model = Standard
        fields = [
            'id', 'standard_title', 'standard_type', 'standard_type_name',
            'content', 'version', 'generated_content', 'llm_model_used',
            'is_ai_generated', 'created_at', 'updated_at'
        ]

    def get_is_ai_generated(self, obj):
        return obj.generated_content is not None

class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ['id', 'label', 'property', 'created_at']
        read_only_fields = ['id', 'created_at']

class AuditQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditQuestion
        fields = ['id', 'question_text', 'policy_name', 'ai_model', 'options', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class AuditQuestionGenerationRequestSerializer(serializers.Serializer):
    ai_model = serializers.ChoiceField(choices=list(AVAILABLE_MODELS.keys()), required=True)
    policy_name = serializers.CharField(max_length=255, required=True)
    number_of_questions = serializers.IntegerField(min_value=1, max_value=50, required=True)

class PracticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Practice
        fields = ['id', 'name', 'address', 'contact_number', 'email', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['id', 'created_at', 'updated_at']

class FeedbackMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackMethod
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']

class FeedbackAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackAttachment
        fields = ['id', 'file_name', 'uploaded_at', 'supabase_storage_path']
        read_only_fields = ['id', 'uploaded_at', 'supabase_storage_path']

class FeedbackSerializer(serializers.ModelSerializer):
    attachments = FeedbackAttachmentSerializer(many=True, read_only=True)
    practice_name = serializers.CharField(source='practice.name', read_only=True)
    submitter_name = serializers.CharField(source='submitter.get_full_name', read_only=True)
    management_owner_name = serializers.CharField(source='management_owner.get_full_name', read_only=True, allow_null=True)
    review_requested_by_name = serializers.CharField(source='review_requested_by.get_full_name', read_only=True, allow_null=True)
    feedback_method_name = serializers.CharField(source='feedback_method.name', read_only=True, allow_null=True)

    class Meta:
        model = Feedback
        fields = [
            'id', 'title', 'reference_number', 'practice', 'practice_name',
            'form_date', 'submitter', 'submitter_name', 'group', 'email',
            'date_received', 'feedback_method', 'feedback_method_name',
            'patient_nhi', 'feedback_details', 'other_comments',
            'management_owner', 'management_owner_name',
            'review_requested_by', 'review_requested_by_name',
            'status', 'created_at', 'updated_at', 'attachments'
        ]
        read_only_fields = ['id', 'reference_number', 'created_at', 'updated_at']

class FeedbackListSerializer(serializers.ModelSerializer):
    practice_name = serializers.CharField(source='practice.name', read_only=True)
    submitter_name = serializers.CharField(source='submitter.get_full_name', read_only=True)
    attachment_count = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        fields = [
            'id', 'title', 'reference_number', 'practice_name',
            'form_date', 'submitter_name', 'patient_nhi',
            'status', 'created_at', 'updated_at', 'attachment_count'
        ]

    def get_attachment_count(self, obj):
        return obj.attachments.count()


class ComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = [
            'id', 'title', 'reference_number', 'practice', 'form_date',
            'reporter_name', 'group', 'email', 'patient_name', 'patient_nhi',
            'patient_dob', 'patient_email', 'patient_phone', 'is_acknowledged',
            'received_date', 'complaint_method', 'complaint_severity',
            'complaint_owner', 'complaint_details', 'action_taken',
            'is_notified_external', 'other_comments', 'file_upload_path',
            'request_review_by', 'complaint_reason', 'is_resolved',
            'identified_issues', 'staff_skill_issues', 'policy_impact',
            'is_disclosure_required', 'is_followup_required',
            'is_event_analysis_required', 'is_training_required',
            'is_visible_to_users', 'disable_editing', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'file_upload_path']


# Chatbot Serializers
class ChatbotIntentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatbotIntent
        fields = [
            'id', 'name', 'intent_type', 'description', 'keywords', 'patterns',
            'is_active', 'requires_auth', 'api_endpoint', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChatbotResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatbotResponse
        fields = [
            'id', 'intent', 'response_type', 'message', 'buttons', 'quick_replies',
            'is_active', 'priority', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ChatbotQuickActionSerializer(serializers.ModelSerializer):
    intent_name = serializers.CharField(source='intent.name', read_only=True)
    intent_type = serializers.CharField(source='intent.intent_type', read_only=True)

    class Meta:
        model = ChatbotQuickAction
        fields = [
            'id', 'title', 'description', 'intent', 'intent_name', 'intent_type',
            'button_text', 'icon', 'order', 'is_active', 'requires_auth', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ChatbotMessageSerializer(serializers.ModelSerializer):
    intent_name = serializers.CharField(source='intent_detected.name', read_only=True, allow_null=True)

    class Meta:
        model = ChatbotMessage
        fields = [
            'id', 'conversation', 'message_type', 'content', 'intent_detected',
            'intent_name', 'confidence_score', 'metadata', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class ChatbotConversationSerializer(serializers.ModelSerializer):
    messages = ChatbotMessageSerializer(many=True, read_only=True)
    current_intent_name = serializers.CharField(source='current_intent.name', read_only=True, allow_null=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True, allow_null=True)

    class Meta:
        model = ChatbotConversation
        fields = [
            'id', 'session_id', 'user', 'user_name', 'status', 'current_intent',
            'current_intent_name', 'context', 'started_at', 'last_activity',
            'completed_at', 'messages'
        ]
        read_only_fields = ['id', 'started_at', 'last_activity']


class ChatbotConversationListSerializer(serializers.ModelSerializer):
    current_intent_name = serializers.CharField(source='current_intent.name', read_only=True, allow_null=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True, allow_null=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatbotConversation
        fields = [
            'id', 'session_id', 'user', 'user_name', 'status', 'current_intent',
            'current_intent_name', 'started_at', 'last_activity', 'completed_at',
            'message_count'
        ]
        read_only_fields = ['id', 'started_at', 'last_activity']

    def get_message_count(self, obj):
        return obj.messages.count()


# Request/Response Serializers for Chatbot API
class ChatbotMessageRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000, required=True)
    session_id = serializers.CharField(max_length=255, required=False)
    user_context = serializers.JSONField(required=False, default=dict)


class ChatbotIntentDetectionSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000, required=True)


class ChatbotActionRequestSerializer(serializers.Serializer):
    intent_type = serializers.CharField(max_length=50, required=True)
    session_id = serializers.CharField(max_length=255, required=True)
    parameters = serializers.JSONField(required=False, default=dict)


class ChatbotResponseDataSerializer(serializers.Serializer):
    message = serializers.CharField()
    response_type = serializers.CharField()
    buttons = serializers.ListField(child=serializers.DictField(), required=False, default=list)
    quick_replies = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    intent_detected = serializers.CharField(required=False, allow_null=True)
    confidence_score = serializers.FloatField(required=False, allow_null=True)
    session_id = serializers.CharField()
    conversation_id = serializers.UUIDField(required=False, allow_null=True)
    metadata = serializers.JSONField(required=False, default=dict)
