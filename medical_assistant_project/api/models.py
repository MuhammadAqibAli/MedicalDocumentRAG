from django.db import models
from pgvector.django import VectorField
import uuid
import json

class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_name = models.CharField(max_length=255)
    standard_type = models.ForeignKey('StandardType', on_delete=models.CASCADE, related_name='documents')
    supabase_storage_path = models.CharField(max_length=1024)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(null=True, blank=True) # Optional: Store original metadata

    def __str__(self):
        return f"{self.standard_type.name}: {self.file_name}"

class DocumentChunk(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    chunk_text = models.TextField()
    # Ensure embedding dimensions match your chosen model (e.g., all-MiniLM-L6-v2 uses 384)
    embedding = VectorField(dimensions=384)
    metadata = models.JSONField(null=True, blank=True) # e.g., page number, chunk index
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chunk {self.id} from {self.document.file_name}"

class GeneratedContent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100) # e.g., Policy, Procedure
    generated_text = models.TextField()
    llm_model_used = models.CharField(max_length=200)
    # Store source chunk IDs for traceability if generated via RAG
    source_chunk_ids = models.JSONField(null=True, blank=True, default=list)
    validation_results = models.JSONField(null=True, blank=True) # Store validation flags/summary
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.content_type} on {self.topic} ({self.created_at.date()})"

class StandardType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Standard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    standard_title = models.CharField(max_length=255)
    standard_type = models.ForeignKey(StandardType, on_delete=models.CASCADE, related_name='standards')
    content = models.TextField()
    version = models.CharField(max_length=50)
    generated_content = models.ForeignKey(
        GeneratedContent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='standards'
    )
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.standard_title} (v{self.version})"

class QuestionOption(models.Model):
    """
    Model for storing predefined question options.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=100)
    property = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.label

class AuditQuestion(models.Model):
    """
    Model for storing audit questions generated based on policies.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question_text = models.TextField()
    policy_name = models.CharField(max_length=255)
    ai_model = models.CharField(max_length=200)
    options = models.JSONField(null=True, blank=True)  # Store options as JSON
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Audit question for {self.policy_name}"
