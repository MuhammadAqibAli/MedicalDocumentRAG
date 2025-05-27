"""
Simple Chatbot Service for Medical Assistant
Supports: Complaint Registration, Status Check, and Feedback Submission
"""

import re
import uuid
from typing import Dict, Any, Optional, Tuple
from django.utils import timezone
from django.contrib.auth.models import User


# Class-level storage for conversation contexts (shared across instances)
_conversation_contexts = {}

class SimpleChatbotService:
    """
    Simple chatbot service that handles basic medical assistant tasks.
    """

    def __init__(self):
        # Use class-level storage for conversation contexts
        self.conversation_contexts = _conversation_contexts

        self.intent_patterns = {
            'complaint_register': [
                r'\b(register|file|submit|create|new)\s+(complaint|issue)\b',
                r'\b(complaint|complain|problem|issue)\b.*\b(register|file|submit|new)\b',
                r'\b(want|need|would like)\s+to\s+(register|file|submit)\s+(complaint|issue)\b',
                r'\b(have|got)\s+(complaint|issue|problem)\b',
                r'\b(want|need|would like)\s+to\s+(register|file|submit)\s+a\s+(complaint|issue)\b',
                r'\bregister\s+complaint\b',
                r'\bfile\s+complaint\b',
                r'\bnew\s+complaint\b',
            ],
            'complaint_status': [
                r'\b(check|status|track|follow up)\s+(complaint|issue)\b',
                r'\b(complaint|issue)\s+(status|progress|update)\b',
                r'\b(where|what)\s+is\s+my\s+(complaint|issue)\b',
                r'\b(COMP-\d{4}-\d+)\b',  # Reference number pattern
            ],
            'feedback_submit': [
                r'\b(submit|give|provide|leave)\s+(feedback|review|comment)\b',
                r'\b(feedback|review|comment)\b.*\b(submit|give|provide|leave)\b',
                r'\b(want|need|would like)\s+to\s+(give|provide|submit)\s+(feedback|review)\b',
                r'\b(experience|service|care)\b.*\b(feedback|review)\b',
            ],
            'greeting': [
                r'\b(hello|hi|hey|good morning|good afternoon|good evening)\b',
                r'\b(help|assist|support)\b',
                r'^(start|begin)$',
            ]
        }

    def detect_intent(self, message: str) -> Tuple[str, float]:
        """
        Detect intent from user message using pattern matching.
        Returns (intent, confidence_score)
        """
        message_lower = message.lower().strip()

        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    # Simple confidence scoring based on pattern specificity
                    confidence = 0.8 if intent != 'greeting' else 0.6
                    return intent, confidence

        # Default to general inquiry
        return 'general_inquiry', 0.3

    def process_message(self, message: str, session_id: str = None, user: User = None) -> Dict[str, Any]:
        """
        Process user message and return appropriate response.
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        # Get or create conversation context
        conversation_context = self._get_conversation_context(session_id)

        # Check if we're in the middle of a form flow
        if conversation_context.get('current_flow'):
            response = self._handle_form_flow(message, conversation_context, user, session_id)
            response['session_id'] = session_id
            return response

        # Detect intent for new messages
        intent, confidence = self.detect_intent(message)

        # Create a mock conversation object for now (until database is ready)
        class MockConversation:
            def __init__(self, session_id):
                self.session_id = session_id
                self.id = str(uuid.uuid4())

        conversation = MockConversation(session_id)

        # Generate response based on intent
        response = self._generate_response(intent, message, conversation, conversation_context, session_id)

        # Add session_id to response
        response['session_id'] = session_id

        return response

    def _get_conversation_context(self, session_id: str) -> Dict[str, Any]:
        """Get or create conversation context for session."""
        if session_id not in self.conversation_contexts:
            self.conversation_contexts[session_id] = {
                'current_flow': None,
                'form_data': {},
                'current_step': 0,
                'created_at': timezone.now().isoformat()
            }

        # Clean up old sessions (older than 1 hour)
        current_time = timezone.now()
        sessions_to_remove = []
        for sid, context in self.conversation_contexts.items():
            try:
                created_at = timezone.datetime.fromisoformat(context['created_at'].replace('Z', '+00:00'))
                if (current_time - created_at).total_seconds() > 3600:  # 1 hour
                    sessions_to_remove.append(sid)
            except:
                pass

        for sid in sessions_to_remove:
            del self.conversation_contexts[sid]

        return self.conversation_contexts[session_id]

    def _update_conversation_context(self, session_id: str, updates: Dict[str, Any]):
        """Update conversation context."""
        context = self._get_conversation_context(session_id)
        context.update(updates)
        self.conversation_contexts[session_id] = context

    def _handle_form_flow(self, message: str, conversation_context: Dict[str, Any], user: User = None, session_id: str = None) -> Dict[str, Any]:
        """Handle form flow for complaint registration or feedback submission."""
        current_flow = conversation_context.get('current_flow')
        current_step = conversation_context.get('current_step', 0)
        form_data = conversation_context.get('form_data', {})

        # Handle cancel
        if message.lower() in ['cancel', 'stop', 'quit']:
            self._update_conversation_context(session_id, {
                'current_flow': None,
                'current_step': 0,
                'form_data': {}
            })
            return self._handle_greeting()

        if current_flow == 'complaint_register':
            return self._handle_complaint_form_step(message, current_step, form_data, session_id, user)
        elif current_flow == 'feedback_submit':
            return self._handle_feedback_form_step(message, current_step, form_data, session_id, user)

        # Fallback
        return self._handle_general_inquiry()

    def _get_or_create_conversation(self, session_id: str, user: User = None):
        """Get or create conversation session."""
        from ..models import SimpleChatbotConversation

        conversation, created = SimpleChatbotConversation.objects.get_or_create(
            session_id=session_id,
            defaults={
                'user': user,
                'status': 'active',
                'context': {}
            }
        )

        if not created:
            # Update last activity
            conversation.last_activity = timezone.now()
            conversation.save()

        return conversation

    def _log_message(self, conversation, message_type: str, content: str,
                    intent: str = None, confidence: float = None):
        """Log message to conversation history."""
        from ..models import SimpleChatbotMessage

        SimpleChatbotMessage.objects.create(
            conversation=conversation,
            message_type=message_type,
            content=content,
            intent_detected=intent,
            confidence_score=confidence,
            metadata={}
        )

    def _generate_response(self, intent: str, message: str, conversation, conversation_context: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Generate response based on detected intent."""

        if intent == 'greeting':
            return self._handle_greeting()
        elif intent == 'complaint_register':
            return self._handle_complaint_register(conversation_context, session_id)
        elif intent == 'complaint_status':
            return self._handle_complaint_status(message)
        elif intent == 'feedback_submit':
            return self._handle_feedback_submit(conversation_context, session_id)
        else:
            return self._handle_general_inquiry()

    def _handle_greeting(self) -> Dict[str, Any]:
        """Handle greeting intent."""
        return {
            'message': "Hello! I'm your medical assistant. I can help you with:\n\n• Register a complaint\n• Check complaint status\n• Submit feedback\n\nHow can I assist you today?",
            'response_type': 'greeting',
            'buttons': [
                {'text': 'Register Complaint', 'value': 'complaint_register', 'action': 'intent'},
                {'text': 'Check Status', 'value': 'complaint_status', 'action': 'intent'},
                {'text': 'Submit Feedback', 'value': 'feedback_submit', 'action': 'intent'}
            ],
            'quick_replies': ['Register complaint', 'Check status', 'Submit feedback'],
            'intent_detected': 'greeting',
            'confidence_score': 0.6
        }

    def _handle_complaint_register(self, conversation_context: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Handle complaint registration intent."""
        # Start the complaint registration flow
        self._update_conversation_context(session_id, {
            'current_flow': 'complaint_register',
            'current_step': 0,
            'form_data': {}
        })

        return {
            'message': "I'll help you register a complaint. Let's start by collecting some basic information.\n\nFirst, what is the title or brief description of your complaint?",
            'response_type': 'form_input',
            'buttons': [
                {'text': 'Cancel', 'value': 'cancel', 'action': 'intent'}
            ],
            'quick_replies': [],
            'intent_detected': 'complaint_register',
            'confidence_score': 0.8,
            'metadata': {
                'current_field': 'title',
                'flow': 'complaint_register',
                'step': 0
            }
        }

    def _handle_complaint_status(self, message: str) -> Dict[str, Any]:
        """Handle complaint status check intent."""
        # Check if message contains a reference number
        ref_match = re.search(r'\b(COMP-\d{4}-\d+)\b', message, re.IGNORECASE)

        if ref_match:
            ref_number = ref_match.group(1).upper()
            return {
                'message': f"I'll check the status of complaint {ref_number} for you. Please wait while I retrieve the information...",
                'response_type': 'status_check',
                'buttons': [
                    {'text': 'View Details', 'value': f'view_complaint_{ref_number}', 'action': 'redirect', 'url': f'/complaints/search?ref={ref_number}'},
                    {'text': 'Register New Complaint', 'value': 'complaint_register', 'action': 'intent'},
                    {'text': 'Main Menu', 'value': 'greeting', 'action': 'intent'}
                ],
                'quick_replies': ['View details', 'New complaint'],
                'intent_detected': 'complaint_status',
                'confidence_score': 0.9,
                'metadata': {
                    'reference_number': ref_number,
                    'api_endpoint': f'/api/complaints/?reference_number={ref_number}',
                    'method': 'GET'
                }
            }
        else:
            return {
                'message': "To check your complaint status, I'll need your complaint reference number. It usually starts with 'COMP-' followed by the year and a number (e.g., COMP-2024-001).\n\nPlease provide your reference number, or I can help you find it using other information.",
                'response_type': 'information_request',
                'buttons': [
                    {'text': 'I have reference number', 'value': 'provide_reference', 'action': 'input'},
                    {'text': 'Find by patient name', 'value': 'find_by_name', 'action': 'redirect', 'url': '/complaints/search'},
                    {'text': 'Main Menu', 'value': 'greeting', 'action': 'intent'}
                ],
                'quick_replies': ['I have the reference', 'Help me find it'],
                'intent_detected': 'complaint_status',
                'confidence_score': 0.7
            }

    def _handle_feedback_submit(self, conversation_context: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Handle feedback submission intent."""
        # Start the feedback submission flow
        self._update_conversation_context(session_id, {
            'current_flow': 'feedback_submit',
            'current_step': 0,
            'form_data': {}
        })

        return {
            'message': "I'd be happy to help you submit feedback about your experience.\n\nLet's start with a title for your feedback. What would you like to call this feedback?",
            'response_type': 'form_input',
            'buttons': [
                {'text': 'Cancel', 'value': 'cancel', 'action': 'intent'}
            ],
            'quick_replies': [],
            'intent_detected': 'feedback_submit',
            'confidence_score': 0.8,
            'metadata': {
                'current_field': 'title',
                'flow': 'feedback_submit',
                'step': 0
            }
        }

    def _handle_general_inquiry(self) -> Dict[str, Any]:
        """Handle general inquiry or fallback."""
        return {
            'message': "I'm here to help you with medical complaints and feedback. I can assist you with:\n\n• Registering a new complaint\n• Checking the status of an existing complaint\n• Submitting feedback about your experience\n\nWhat would you like to do?",
            'response_type': 'menu',
            'buttons': [
                {'text': 'Register Complaint', 'value': 'complaint_register', 'action': 'intent'},
                {'text': 'Check Status', 'value': 'complaint_status', 'action': 'intent'},
                {'text': 'Submit Feedback', 'value': 'feedback_submit', 'action': 'intent'}
            ],
            'quick_replies': ['Complaint', 'Status', 'Feedback'],
            'intent_detected': 'general_inquiry',
            'confidence_score': 0.3
        }

    def get_conversation_history(self, session_id: str) -> Dict[str, Any]:
        """Get conversation history for a session."""
        from ..models import SimpleChatbotConversation

        try:
            conversation = SimpleChatbotConversation.objects.get(session_id=session_id)
            messages = conversation.messages.all().order_by('timestamp')

            return {
                'session_id': session_id,
                'status': conversation.status,
                'started_at': conversation.started_at,
                'last_activity': conversation.last_activity,
                'messages': [
                    {
                        'type': msg.message_type,
                        'content': msg.content,
                        'intent': msg.intent_detected,
                        'confidence': msg.confidence_score,
                        'timestamp': msg.timestamp
                    }
                    for msg in messages
                ]
            }
        except SimpleChatbotConversation.DoesNotExist:
            return {'error': 'Conversation not found'}

    def _handle_complaint_form_step(self, message: str, current_step: int, form_data: Dict[str, Any], session_id: str, user: User = None) -> Dict[str, Any]:
        """Handle complaint form steps."""
        complaint_fields = [
            {'field': 'title', 'prompt': 'What is the title or brief description of your complaint?'},
            {'field': 'practice', 'prompt': 'Which practice or healthcare facility is this complaint about?'},
            {'field': 'reporter_name', 'prompt': 'What is your name (person completing this report)?'},
            {'field': 'patient_name', 'prompt': 'What is the patient\'s name (if different from reporter)?'},
            {'field': 'patient_nhi', 'prompt': 'What is the patient\'s NHI number?'},
            {'field': 'complaint_details', 'prompt': 'Please describe the details of your complaint:'},
            {'field': 'email', 'prompt': 'What is your email address for follow-up?'},
        ]

        # Store the current field value
        if current_step < len(complaint_fields):
            field_name = complaint_fields[current_step]['field']
            form_data[field_name] = message.strip()

        # Move to next step
        next_step = current_step + 1

        # Check if we have all required fields
        if next_step >= len(complaint_fields):
            return self._submit_complaint(form_data, session_id, user)

        # Ask for next field
        next_field = complaint_fields[next_step]
        self._update_conversation_context(session_id, {
            'current_step': next_step,
            'form_data': form_data
        })

        return {
            'message': f"Thank you! {next_field['prompt']}",
            'response_type': 'form_input',
            'buttons': [
                {'text': 'Cancel', 'value': 'cancel', 'action': 'intent'}
            ],
            'quick_replies': [],
            'metadata': {
                'current_field': next_field['field'],
                'step': next_step,
                'progress': f"{next_step + 1}/{len(complaint_fields)}"
            }
        }

    def _handle_feedback_form_step(self, message: str, current_step: int, form_data: Dict[str, Any], session_id: str, user: User = None) -> Dict[str, Any]:
        """Handle feedback form steps."""
        feedback_fields = [
            {'field': 'title', 'prompt': 'What would you like to call this feedback?'},
            {'field': 'practice', 'prompt': 'Which practice or healthcare facility is this feedback about?'},
            {'field': 'patient_nhi', 'prompt': 'What is the patient\'s NHI number?'},
            {'field': 'feedback_details', 'prompt': 'Please share your feedback details:'},
            {'field': 'email', 'prompt': 'What is your email address for follow-up?'},
        ]

        # Store the current field value
        if current_step < len(feedback_fields):
            field_name = feedback_fields[current_step]['field']
            form_data[field_name] = message.strip()

        # Move to next step
        next_step = current_step + 1

        # Check if we have all required fields
        if next_step >= len(feedback_fields):
            return self._submit_feedback(form_data, session_id, user)

        # Ask for next field
        next_field = feedback_fields[next_step]
        self._update_conversation_context(session_id, {
            'current_step': next_step,
            'form_data': form_data
        })

        return {
            'message': f"Thank you! {next_field['prompt']}",
            'response_type': 'form_input',
            'buttons': [
                {'text': 'Cancel', 'value': 'cancel', 'action': 'intent'}
            ],
            'quick_replies': [],
            'metadata': {
                'current_field': next_field['field'],
                'step': next_step,
                'progress': f"{next_step + 1}/{len(feedback_fields)}"
            }
        }

    def _submit_complaint(self, form_data: Dict[str, Any], session_id: str, user: User = None) -> Dict[str, Any]:
        """Submit complaint to database."""
        try:
            from datetime import date
            from ..models import Complaint
            import random

            # Generate reference number
            today = date.today().strftime('%Y%m%d')
            random_digits = str(random.randint(1000, 9999))
            reference_number = f"COMP-{today}-{random_digits}"

            # Create complaint (practice is CharField, not ForeignKey)
            complaint = Complaint.objects.create(
                title=form_data.get('title', '').strip(),
                practice=form_data.get('practice', '').strip(),  # CharField
                reporter_name=form_data.get('reporter_name', '').strip(),
                patient_name=form_data.get('patient_name', '').strip(),
                patient_nhi=form_data.get('patient_nhi', '').strip(),
                complaint_details=form_data.get('complaint_details', '').strip(),
                email=form_data.get('email', '').strip(),
                form_date=date.today(),
                reference_number=reference_number,
                is_acknowledged=False,
                is_visible_to_users=True
            )

            complaint_id = complaint.reference_number

            # Clear conversation context
            self._update_conversation_context(session_id, {
                'current_flow': None,
                'current_step': 0,
                'form_data': {}
            })

            return {
                'message': f"✅ Your complaint has been successfully submitted!\n\nComplaint ID: {complaint_id}\n\nYou will receive a confirmation email shortly. You can use this ID to check the status of your complaint.\n\nIs there anything else I can help you with?",
                'response_type': 'success',
                'buttons': [
                    {'text': 'Check Status', 'value': 'complaint_status', 'action': 'intent'},
                    {'text': 'Submit Another Complaint', 'value': 'complaint_register', 'action': 'intent'},
                    {'text': 'Main Menu', 'value': 'greeting', 'action': 'intent'}
                ],
                'quick_replies': ['Check status', 'New complaint', 'Main menu'],
                'metadata': {
                    'complaint_id': complaint_id,
                    'submission_successful': True,
                    'database_id': str(complaint.id)
                }
            }

        except Exception as e:
            return {
                'message': f"❌ Sorry, there was an error submitting your complaint: {str(e)}\n\nPlease try again or contact support.",
                'response_type': 'error',
                'buttons': [
                    {'text': 'Try Again', 'value': 'complaint_register', 'action': 'intent'},
                    {'text': 'Main Menu', 'value': 'greeting', 'action': 'intent'}
                ],
                'quick_replies': ['Try again', 'Main menu']
            }

    def _submit_feedback(self, form_data: Dict[str, Any], session_id: str, user: User = None) -> Dict[str, Any]:
        """Submit feedback to database."""
        try:
            from datetime import date
            from ..models import Feedback, Practice
            from django.contrib.auth.models import User as AuthUser

            # Get or create practice
            practice_name = form_data.get('practice', '').strip()
            practice = None
            if practice_name:
                practice, created = Practice.objects.get_or_create(
                    name=practice_name,
                    defaults={
                        'address': '',
                        'contact_number': '',  # Correct field name
                        'email': '',
                        'is_active': True
                    }
                )

            # Get or create a default user for feedback submission if no user provided
            if not user:
                user, created = AuthUser.objects.get_or_create(
                    username='chatbot_user',
                    defaults={
                        'email': 'chatbot@system.com',
                        'first_name': 'Chatbot',
                        'last_name': 'System'
                    }
                )

            # Create feedback
            feedback = Feedback.objects.create(
                title=form_data.get('title', '').strip(),
                practice=practice,
                patient_nhi=form_data.get('patient_nhi', '').strip(),
                feedback_details=form_data.get('feedback_details', '').strip(),
                email=form_data.get('email', '').strip(),
                form_date=date.today(),
                submitter=user,
                is_visible_to_users=True
            )

            feedback_id = feedback.reference_number

            # Clear conversation context
            self._update_conversation_context(session_id, {
                'current_flow': None,
                'current_step': 0,
                'form_data': {}
            })

            return {
                'message': f"✅ Your feedback has been successfully submitted!\n\nFeedback ID: {feedback_id}\n\nThank you for taking the time to share your experience. Your feedback helps us improve our services.\n\nIs there anything else I can help you with?",
                'response_type': 'success',
                'buttons': [
                    {'text': 'Submit Another Feedback', 'value': 'feedback_submit', 'action': 'intent'},
                    {'text': 'Register Complaint', 'value': 'complaint_register', 'action': 'intent'},
                    {'text': 'Main Menu', 'value': 'greeting', 'action': 'intent'}
                ],
                'quick_replies': ['New feedback', 'Register complaint', 'Main menu'],
                'metadata': {
                    'feedback_id': feedback_id,
                    'submission_successful': True,
                    'database_id': str(feedback.id)
                }
            }

        except Exception as e:
            return {
                'message': f"❌ Sorry, there was an error submitting your feedback: {str(e)}\n\nPlease try again or contact support.",
                'response_type': 'error',
                'buttons': [
                    {'text': 'Try Again', 'value': 'feedback_submit', 'action': 'intent'},
                    {'text': 'Main Menu', 'value': 'greeting', 'action': 'intent'}
                ],
                'quick_replies': ['Try again', 'Main menu']
            }
