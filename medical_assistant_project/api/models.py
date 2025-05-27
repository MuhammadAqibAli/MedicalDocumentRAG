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


class Complaint(models.Model):
    """
    Model for storing patient complaints and related information.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    reference_number = models.CharField(max_length=100, null=True, blank=True)
    practice = models.CharField(max_length=255, null=True, blank=True)
    form_date = models.DateField(null=True, blank=True)
    reporter_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='Person Completing the Report')
    group = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    patient_name = models.CharField(max_length=255, null=True, blank=True)
    patient_nhi = models.CharField(max_length=100, null=True, blank=True, verbose_name='Patient NHI')
    patient_dob = models.DateField(null=True, blank=True, verbose_name='Patient DOB')
    patient_email = models.EmailField(null=True, blank=True)
    patient_phone = models.CharField(max_length=50, null=True, blank=True, verbose_name='Patient Phone Number')
    is_acknowledged = models.BooleanField(default=False, verbose_name="Has the patient's complaint been acknowledged?")
    received_date = models.DateField(null=True, blank=True, verbose_name='Date Complaint was Received')
    complaint_method = models.CharField(max_length=100, null=True, blank=True)
    complaint_severity = models.CharField(max_length=100, null=True, blank=True)
    complaint_owner = models.CharField(max_length=255, null=True, blank=True)
    complaint_details = models.TextField(null=True, blank=True)
    action_taken = models.TextField(null=True, blank=True, verbose_name='Action Taken at the Time of Complaint and By Whom')
    is_notified_external = models.BooleanField(default=False, verbose_name='Was the complaint notified to an external organisation?')
    other_comments = models.TextField(null=True, blank=True, verbose_name='Any Other Comments')
    file_upload_path = models.CharField(max_length=1024, null=True, blank=True)
    request_review_by = models.CharField(max_length=255, null=True, blank=True)
    complaint_reason = models.TextField(null=True, blank=True, verbose_name='Reason for the Patient Complaint')
    is_resolved = models.BooleanField(default=False, verbose_name='Was the Complaint Successfully Resolved?')
    identified_issues = models.TextField(null=True, blank=True, verbose_name='Identified Issues as a Result of the Complaint')
    staff_skill_issues = models.TextField(null=True, blank=True, verbose_name='Issues Related to Staff Skill or Knowledge')
    policy_impact = models.TextField(null=True, blank=True, verbose_name='Did Practice Policies/Protocols Help or Hinder?')
    is_disclosure_required = models.BooleanField(default=False, verbose_name='Is Open Disclosure Required?')
    is_followup_required = models.BooleanField(default=False, verbose_name='Is Follow-Up Action Required?')
    is_event_analysis_required = models.BooleanField(default=False, verbose_name='Is Formal Significant Event Analysis Required?')
    is_training_required = models.BooleanField(default=False, verbose_name='Is Staff Training Required?')
    is_visible_to_users = models.BooleanField(default=True, verbose_name='Make Complaint Management Visible to Users')
    disable_editing = models.BooleanField(default=False, verbose_name='Disable Editing by Users')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Complaint: {self.title}"


# Simple Chatbot Models
class SimpleChatbotConversation(models.Model):
    """
    Model for tracking simple chatbot conversations.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    context = models.JSONField(default=dict, help_text="Conversation context and state")
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'simple_chatbot_conversations'
        ordering = ['-last_activity']

    def __str__(self):
        return f"Conversation {self.session_id} - {self.status}"


class SimpleChatbotMessage(models.Model):
    """
    Model for storing simple chatbot messages.
    """
    MESSAGE_TYPES = [
        ('user', 'User Message'),
        ('bot', 'Bot Response'),
        ('system', 'System Message'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(SimpleChatbotConversation, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    content = models.TextField()
    intent_detected = models.CharField(max_length=50, blank=True, null=True)
    confidence_score = models.FloatField(null=True, blank=True)
    metadata = models.JSONField(default=dict, help_text="Additional message metadata")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'simple_chatbot_messages'
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.message_type} - {self.content[:50]}..."
