from django.db import models
from pgvector.django import VectorField
import uuid
import json
from django.contrib.auth.models import User

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

class Practice(models.Model):
    """
    Model for storing medical practices.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    address = models.TextField(null=True, blank=True)
    contact_number = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class FeedbackMethod(models.Model):
    """
    Model for storing feedback methods (e.g., Email, Phone, In-person, etc.)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Feedback(models.Model):
    """
    Model for storing patient feedback.
    """
    # Status choices
    STATUS_NEW = 'New'
    STATUS_IN_PROGRESS = 'In Progress'
    STATUS_PENDING_REVIEW = 'Pending Review'
    STATUS_RESOLVED = 'Resolved'
    STATUS_CLOSED = 'Closed'

    STATUS_CHOICES = [
        (STATUS_NEW, 'New'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_PENDING_REVIEW, 'Pending Review'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_CLOSED, 'Closed'),
    ]

    # Required fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    reference_number = models.CharField(max_length=50, unique=True, blank=True)
    practice = models.ForeignKey(Practice, on_delete=models.CASCADE, related_name='feedback')
    form_date = models.DateField()
    submitter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_feedback')
    patient_nhi = models.CharField(max_length=100)
    feedback_details = models.TextField()

    # Optional fields
    group = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    date_received = models.DateField(null=True, blank=True)
    feedback_method = models.ForeignKey(FeedbackMethod, on_delete=models.SET_NULL, null=True, blank=True)
    other_comments = models.TextField(null=True, blank=True)
    management_owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_feedback')
    review_requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='review_requested_feedback')

    # System-managed fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.reference_number}"

    def save(self, *args, **kwargs):
        # Generate reference number if not provided
        if not self.reference_number:
            # Format: FB-YYYYMMDD-XXXX (where XXXX is a random 4-digit number)
            import random
            from datetime import date
            today = date.today().strftime('%Y%m%d')
            random_digits = str(random.randint(1000, 9999))
            self.reference_number = f"FB-{today}-{random_digits}"

        super().save(*args, **kwargs)

class FeedbackAttachment(models.Model):
    """
    Model for storing attachments related to feedback.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name='attachments')
    file_name = models.CharField(max_length=255)
    supabase_storage_path = models.CharField(max_length=1024)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.feedback.reference_number}: {self.file_name}"
