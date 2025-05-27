# Generated migration for chatbot models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0004_create_complaint_model'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatbotIntent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('intent_type', models.CharField(choices=[('complaint_register', 'Register Complaint'), ('complaint_status', 'Check Complaint Status'), ('feedback_submit', 'Submit Feedback'), ('document_upload', 'Upload Document/Standard'), ('content_generate', 'Generate Content'), ('audit_questions', 'Create Audit Questions'), ('general_inquiry', 'General Inquiry'), ('greeting', 'Greeting')], max_length=50)),
                ('description', models.TextField()),
                ('keywords', models.JSONField(default=list, help_text='Keywords that trigger this intent')),
                ('patterns', models.JSONField(default=list, help_text='Regex patterns for intent detection')),
                ('is_active', models.BooleanField(default=True)),
                ('requires_auth', models.BooleanField(default=False)),
                ('api_endpoint', models.CharField(blank=True, help_text='Associated API endpoint', max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='ChatbotResponse',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('response_type', models.CharField(choices=[('greeting', 'Greeting'), ('menu', 'Menu Options'), ('confirmation', 'Confirmation'), ('error', 'Error Message'), ('help', 'Help Message'), ('fallback', 'Fallback Response')], max_length=50)),
                ('message', models.TextField()),
                ('buttons', models.JSONField(default=list, help_text='Button options for the response')),
                ('quick_replies', models.JSONField(default=list, help_text='Quick reply options')),
                ('is_active', models.BooleanField(default=True)),
                ('priority', models.IntegerField(default=0, help_text='Higher priority responses are shown first')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('intent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='api.chatbotintent')),
            ],
            options={
                'ordering': ['-priority', 'created_at'],
            },
        ),
        migrations.CreateModel(
            name='ChatbotConversation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('session_id', models.CharField(max_length=255, unique=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('completed', 'Completed'), ('abandoned', 'Abandoned')], default='active', max_length=20)),
                ('context', models.JSONField(default=dict, help_text='Conversation context and state')),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('last_activity', models.DateTimeField(auto_now=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('current_intent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.chatbotintent')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ChatbotMessage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('message_type', models.CharField(choices=[('user', 'User Message'), ('bot', 'Bot Response'), ('system', 'System Message')], max_length=20)),
                ('content', models.TextField()),
                ('confidence_score', models.FloatField(blank=True, null=True)),
                ('metadata', models.JSONField(default=dict, help_text='Additional message metadata')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='api.chatbotconversation')),
                ('intent_detected', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.chatbotintent')),
            ],
            options={
                'ordering': ['timestamp'],
            },
        ),
        migrations.CreateModel(
            name='ChatbotQuickAction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('button_text', models.CharField(max_length=50)),
                ('icon', models.CharField(blank=True, help_text='Icon class or name', max_length=50, null=True)),
                ('order', models.IntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('requires_auth', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('intent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quick_actions', to='api.chatbotintent')),
            ],
            options={
                'ordering': ['order', 'title'],
            },
        ),
    ]
