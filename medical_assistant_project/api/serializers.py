from rest_framework import serializers
from .models import Document, GeneratedContent, DocumentChunk
from .services.llm_engine import AVAILABLE_MODELS

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'file_name', 'document_type', 'uploaded_at', 'metadata']
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