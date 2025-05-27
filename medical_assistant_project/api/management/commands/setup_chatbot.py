from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import ChatbotIntent, ChatbotResponse, ChatbotQuickAction


class Command(BaseCommand):
    help = 'Setup initial chatbot intents, responses, and quick actions'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up chatbot data...'))
        
        with transaction.atomic():
            self.create_intents()
            self.create_responses()
            self.create_quick_actions()
        
        self.stdout.write(self.style.SUCCESS('Chatbot setup completed successfully!'))

    def create_intents(self):
        """Create chatbot intents."""
        intents_data = [
            {
                'name': 'Greeting',
                'intent_type': 'greeting',
                'description': 'User greets the chatbot or starts conversation',
                'keywords': ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'start', 'help'],
                'patterns': [r'\b(hello|hi|hey|greetings?)\b', r'\bgood\s+(morning|afternoon|evening)\b'],
                'api_endpoint': None,
                'requires_auth': False
            },
            {
                'name': 'Register Complaint',
                'intent_type': 'complaint_register',
                'description': 'User wants to register a new complaint',
                'keywords': ['complaint', 'register', 'file', 'submit', 'report', 'issue', 'problem'],
                'patterns': [r'\b(register|file|submit)\s+(complaint|issue)\b', r'\bhave\s+a\s+(complaint|problem)\b'],
                'api_endpoint': '/api/complaints/',
                'requires_auth': False
            },
            {
                'name': 'Check Complaint Status',
                'intent_type': 'complaint_status',
                'description': 'User wants to check status of existing complaint',
                'keywords': ['status', 'check', 'complaint', 'reference', 'number', 'progress'],
                'patterns': [r'\bcheck\s+(status|complaint)\b', r'\bstatus\s+of\s+complaint\b'],
                'api_endpoint': '/api/complaints/{id}/',
                'requires_auth': False
            },
            {
                'name': 'Submit Feedback',
                'intent_type': 'feedback_submit',
                'description': 'User wants to submit feedback',
                'keywords': ['feedback', 'comment', 'suggestion', 'experience', 'review'],
                'patterns': [r'\b(submit|give|provide)\s+(feedback|comment)\b', r'\bfeedback\s+about\b'],
                'api_endpoint': '/api/feedback/',
                'requires_auth': False
            },
            {
                'name': 'Upload Document',
                'intent_type': 'document_upload',
                'description': 'User wants to upload a document or standard',
                'keywords': ['upload', 'document', 'file', 'standard', 'policy', 'procedure'],
                'patterns': [r'\b(upload|add)\s+(document|file|standard)\b'],
                'api_endpoint': '/api/upload/',
                'requires_auth': True
            },
            {
                'name': 'Generate Content',
                'intent_type': 'content_generate',
                'description': 'User wants to generate content using AI',
                'keywords': ['generate', 'create', 'content', 'policy', 'procedure', 'ai'],
                'patterns': [r'\b(generate|create)\s+(content|policy|procedure)\b'],
                'api_endpoint': '/api/generate/',
                'requires_auth': True
            },
            {
                'name': 'Create Audit Questions',
                'intent_type': 'audit_questions',
                'description': 'User wants to create audit questions',
                'keywords': ['audit', 'questions', 'compliance', 'assessment'],
                'patterns': [r'\b(audit|compliance)\s+questions?\b', r'\bcreate\s+audit\b'],
                'api_endpoint': '/api/audit-questions/generate/',
                'requires_auth': True
            },
            {
                'name': 'General Inquiry',
                'intent_type': 'general_inquiry',
                'description': 'General questions or requests for help',
                'keywords': ['help', 'what', 'how', 'can', 'do', 'options', 'menu'],
                'patterns': [r'\bwhat\s+can\s+you\s+do\b', r'\bshow\s+me\s+options\b'],
                'api_endpoint': None,
                'requires_auth': False
            }
        ]

        for intent_data in intents_data:
            intent, created = ChatbotIntent.objects.get_or_create(
                intent_type=intent_data['intent_type'],
                defaults=intent_data
            )
            if created:
                self.stdout.write(f'Created intent: {intent.name}')
            else:
                self.stdout.write(f'Intent already exists: {intent.name}')

    def create_responses(self):
        """Create chatbot responses."""
        responses_data = [
            {
                'response_type': 'greeting',
                'message': 'Hello! I\'m your medical assistant chatbot. I can help you with:\n\n• Registering complaints\n• Checking complaint status\n• Submitting feedback\n• Uploading documents\n• Generating content\n• Creating audit questions\n\nHow can I assist you today?',
                'buttons': [],
                'quick_replies': ['Register complaint', 'Check status', 'Submit feedback', 'Upload document'],
                'priority': 10
            },
            {
                'response_type': 'menu',
                'message': 'Here are the main things I can help you with:',
                'buttons': [],
                'quick_replies': ['Complaint', 'Feedback', 'Upload', 'Generate', 'Audit'],
                'priority': 5
            },
            {
                'response_type': 'help',
                'message': 'I\'m here to help! You can:\n\n1. **Register a complaint** - Report issues or concerns\n2. **Check complaint status** - Track your existing complaints\n3. **Submit feedback** - Share your experience\n4. **Upload documents** - Add policies, procedures, or standards\n5. **Generate content** - Create AI-powered medical content\n6. **Create audit questions** - Generate compliance questions\n\nJust tell me what you\'d like to do!',
                'buttons': [],
                'quick_replies': ['Main menu', 'Start over'],
                'priority': 8
            },
            {
                'response_type': 'fallback',
                'message': 'I\'m not sure I understand that. Could you please rephrase or choose from one of these options?',
                'buttons': [],
                'quick_replies': ['Help', 'Main menu', 'Start over'],
                'priority': 1
            },
            {
                'response_type': 'error',
                'message': 'I\'m sorry, but I encountered an error. Please try again or contact support if the problem persists.',
                'buttons': [],
                'quick_replies': ['Try again', 'Main menu'],
                'priority': 1
            }
        ]

        for response_data in responses_data:
            response, created = ChatbotResponse.objects.get_or_create(
                response_type=response_data['response_type'],
                defaults=response_data
            )
            if created:
                self.stdout.write(f'Created response: {response.response_type}')
            else:
                self.stdout.write(f'Response already exists: {response.response_type}')

    def create_quick_actions(self):
        """Create quick action buttons."""
        # Get intents for quick actions
        intents = {intent.intent_type: intent for intent in ChatbotIntent.objects.all()}
        
        quick_actions_data = [
            {
                'title': 'Register Complaint',
                'description': 'Report a medical issue or concern',
                'button_text': '📝 Register Complaint',
                'icon': 'complaint',
                'order': 1,
                'intent': intents.get('complaint_register'),
                'requires_auth': False
            },
            {
                'title': 'Check Status',
                'description': 'Check the status of your complaint',
                'button_text': '🔍 Check Status',
                'icon': 'search',
                'order': 2,
                'intent': intents.get('complaint_status'),
                'requires_auth': False
            },
            {
                'title': 'Submit Feedback',
                'description': 'Share your experience or suggestions',
                'button_text': '💬 Submit Feedback',
                'icon': 'feedback',
                'order': 3,
                'intent': intents.get('feedback_submit'),
                'requires_auth': False
            },
            {
                'title': 'Upload Document',
                'description': 'Upload medical documents or standards',
                'button_text': '📄 Upload Document',
                'icon': 'upload',
                'order': 4,
                'intent': intents.get('document_upload'),
                'requires_auth': True
            },
            {
                'title': 'Generate Content',
                'description': 'Create AI-powered medical content',
                'button_text': '🤖 Generate Content',
                'icon': 'generate',
                'order': 5,
                'intent': intents.get('content_generate'),
                'requires_auth': True
            },
            {
                'title': 'Audit Questions',
                'description': 'Create compliance audit questions',
                'button_text': '✅ Audit Questions',
                'icon': 'audit',
                'order': 6,
                'intent': intents.get('audit_questions'),
                'requires_auth': True
            }
        ]

        for action_data in quick_actions_data:
            if action_data['intent']:  # Only create if intent exists
                action, created = ChatbotQuickAction.objects.get_or_create(
                    title=action_data['title'],
                    defaults=action_data
                )
                if created:
                    self.stdout.write(f'Created quick action: {action.title}')
                else:
                    self.stdout.write(f'Quick action already exists: {action.title}')
            else:
                self.stdout.write(f'Skipping quick action {action_data["title"]} - intent not found')
