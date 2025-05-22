from rest_framework import serializers
from .models import Document, GeneratedContent, DocumentChunk, Standard, StandardType, QuestionOption, AuditQuestion
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
