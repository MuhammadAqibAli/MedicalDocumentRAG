import logging
import re
import uuid
from typing import Dict, Any, Optional, Tuple, List, TYPE_CHECKING
from datetime import timedelta

if TYPE_CHECKING:
    from django.contrib.auth.models import User
    from ..models import ChatbotIntent, ChatbotResponse, ChatbotConversation, ChatbotMessage, ChatbotQuickAction

logger = logging.getLogger(__name__)


class IntentDetector:
    """
    Service for detecting user intents from natural language input.
    """

    def __init__(self):
        self.intents = self._load_intents()

    def _load_intents(self) -> Dict[str, Any]:
        """Load active intents from database."""
        from ..models import ChatbotIntent
        intents = {}
        for intent in ChatbotIntent.objects.filter(is_active=True):
            intents[intent.intent_type] = intent
        return intents

    def detect_intent(self, message: str, context: Dict[str, Any] = None) -> Tuple[Optional[str], float]:
        """
        Detect intent from user message.

        Args:
            message: User's input message
            context: Conversation context

        Returns:
            Tuple of (intent_type, confidence_score)
        """
        message_lower = message.lower().strip()

        # Check for exact keyword matches first
        for intent_type, intent in self.intents.items():
            confidence = self._calculate_keyword_confidence(message_lower, intent.keywords)
            if confidence > 0.7:  # High confidence threshold for keywords
                return intent_type, confidence

        # Check regex patterns
        for intent_type, intent in self.intents.items():
            confidence = self._calculate_pattern_confidence(message_lower, intent.patterns)
            if confidence > 0.6:  # Medium confidence threshold for patterns
                return intent_type, confidence

        # Contextual detection based on conversation state
        if context and context.get('current_intent'):
            current_intent = context['current_intent']
            if current_intent in self.intents:
                # Check if message is a continuation of current intent
                confidence = self._calculate_contextual_confidence(message_lower, current_intent)
                if confidence > 0.5:
                    return current_intent, confidence

        # Default to general inquiry if no specific intent detected
        return 'general_inquiry', 0.3

    def _calculate_keyword_confidence(self, message: str, keywords: List[str]) -> float:
        """Calculate confidence based on keyword matching."""
        if not keywords:
            return 0.0

        matches = 0
        for keyword in keywords:
            if keyword.lower() in message:
                matches += 1

        return min(matches / len(keywords), 1.0)

    def _calculate_pattern_confidence(self, message: str, patterns: List[str]) -> float:
        """Calculate confidence based on regex pattern matching."""
        if not patterns:
            return 0.0

        matches = 0
        for pattern in patterns:
            try:
                if re.search(pattern, message, re.IGNORECASE):
                    matches += 1
            except re.error:
                logger.warning(f"Invalid regex pattern: {pattern}")
                continue

        return min(matches / len(patterns), 1.0) if patterns else 0.0

    def _calculate_contextual_confidence(self, message: str, current_intent: str) -> float:
        """Calculate confidence based on conversation context."""
        # Simple contextual rules - can be enhanced with ML
        contextual_keywords = {
            'complaint_register': ['yes', 'continue', 'proceed', 'next'],
            'complaint_status': ['check', 'status', 'reference', 'number'],
            'feedback_submit': ['feedback', 'comment', 'experience'],
            'document_upload': ['upload', 'file', 'document'],
            'content_generate': ['generate', 'create', 'policy', 'procedure'],
            'audit_questions': ['audit', 'questions', 'compliance']
        }

        keywords = contextual_keywords.get(current_intent, [])
        if not keywords:
            return 0.0

        matches = sum(1 for keyword in keywords if keyword in message)
        return min(matches / len(keywords), 1.0)


class ActionDispatcher:
    """
    Service for dispatching actions based on detected intents.
    """

    def __init__(self):
        self.intent_detector = IntentDetector()

    def dispatch_action(self, intent_type: str, message: str, session_id: str,
                       user: Optional['User'] = None, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Dispatch action based on intent type.

        Args:
            intent_type: Detected intent type
            message: Original user message
            session_id: Conversation session ID
            user: Authenticated user (if any)
            parameters: Additional parameters

        Returns:
            Action result dictionary
        """
        parameters = parameters or {}

        # Get or create conversation
        conversation = self._get_or_create_conversation(session_id, user)

        # Update conversation context
        from ..models import ChatbotIntent
        conversation.current_intent = ChatbotIntent.objects.filter(
            intent_type=intent_type, is_active=True
        ).first()
        conversation.save()

        # Dispatch to specific handler
        handler_map = {
            'greeting': self._handle_greeting,
            'complaint_register': self._handle_complaint_register,
            'complaint_status': self._handle_complaint_status,
            'feedback_submit': self._handle_feedback_submit,
            'document_upload': self._handle_document_upload,
            'content_generate': self._handle_content_generate,
            'audit_questions': self._handle_audit_questions,
            'general_inquiry': self._handle_general_inquiry,
        }

        handler = handler_map.get(intent_type, self._handle_fallback)
        return handler(message, conversation, parameters)

    def _get_or_create_conversation(self, session_id: str, user: Optional['User'] = None) -> 'ChatbotConversation':
        """Get existing conversation or create new one."""
        from ..models import ChatbotConversation
        from django.utils import timezone

        conversation, created = ChatbotConversation.objects.get_or_create(
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

    def _handle_greeting(self, message: str, conversation: 'ChatbotConversation',
                        parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle greeting intent."""
        # Get greeting response
        from ..models import ChatbotResponse
        response = ChatbotResponse.objects.filter(
            response_type='greeting', is_active=True
        ).first()

        if not response:
            response_message = "Hello! I'm here to help you with medical complaints, feedback, and document management. How can I assist you today?"
        else:
            response_message = response.message

        # Get quick actions for main menu
        from ..models import ChatbotQuickAction
        quick_actions = ChatbotQuickAction.objects.filter(
            is_active=True, requires_auth=False
        ).order_by('order')[:6]

        buttons = [
            {
                'text': action.button_text,
                'value': action.intent.intent_type,
                'icon': action.icon
            }
            for action in quick_actions
        ]

        return {
            'message': response_message,
            'response_type': 'greeting',
            'buttons': buttons,
            'quick_replies': [],
            'session_id': conversation.session_id,
            'conversation_id': str(conversation.id)
        }

    def _handle_complaint_register(self, message: str, conversation: 'ChatbotConversation',
                                  parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle complaint registration intent."""
        return {
            'message': "I'll help you register a complaint. Please provide the following information:\n\n1. Brief description of the issue\n2. Date when the incident occurred\n3. Location/practice where it happened\n\nYou can also use our complaint form directly at /api/complaints/",
            'response_type': 'form_guidance',
            'buttons': [
                {'text': 'Start Complaint Form', 'value': 'start_complaint_form', 'action': 'redirect'},
                {'text': 'Get Help', 'value': 'help', 'action': 'intent'}
            ],
            'quick_replies': ['I need help', 'Start over'],
            'session_id': conversation.session_id,
            'conversation_id': str(conversation.id),
            'metadata': {
                'api_endpoint': '/api/complaints/',
                'method': 'POST',
                'required_fields': ['title', 'complaint_details', 'patient_name']
            }
        }

    def _handle_complaint_status(self, message: str, conversation: 'ChatbotConversation',
                                parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle complaint status check intent."""
        return {
            'message': "To check your complaint status, I'll need your complaint reference number. It usually starts with 'COMP-' followed by the year and a number.\n\nPlease provide your reference number, or I can help you find it using other information.",
            'response_type': 'information_request',
            'buttons': [
                {'text': 'I have reference number', 'value': 'provide_reference', 'action': 'input'},
                {'text': 'Find by patient name', 'value': 'find_by_name', 'action': 'input'},
                {'text': 'Get Help', 'value': 'help', 'action': 'intent'}
            ],
            'quick_replies': ['I have the reference', 'Help me find it'],
            'session_id': conversation.session_id,
            'conversation_id': str(conversation.id),
            'metadata': {
                'api_endpoint': '/api/complaints/{id}/',
                'method': 'GET'
            }
        }

    def _handle_feedback_submit(self, message: str, conversation: 'ChatbotConversation',
                               parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle feedback submission intent."""
        return {
            'message': "I'd be happy to help you submit feedback. You can provide feedback about:\n\n• Your experience with our services\n• Suggestions for improvement\n• Compliments for our staff\n• Any concerns you may have\n\nWould you like to start the feedback form?",
            'response_type': 'form_guidance',
            'buttons': [
                {'text': 'Start Feedback Form', 'value': 'start_feedback_form', 'action': 'redirect'},
                {'text': 'Learn More', 'value': 'feedback_info', 'action': 'info'},
                {'text': 'Get Help', 'value': 'help', 'action': 'intent'}
            ],
            'quick_replies': ['Start feedback', 'Tell me more'],
            'session_id': conversation.session_id,
            'conversation_id': str(conversation.id),
            'metadata': {
                'api_endpoint': '/api/feedback/',
                'method': 'POST',
                'required_fields': ['title', 'feedback_details', 'practice', 'submitter']
            }
        }

    def _handle_document_upload(self, message: str, conversation: 'ChatbotConversation',
                               parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle document upload intent."""
        return {
            'message': "I can help you upload medical documents and standards. Supported formats include:\n\n• PDF files\n• DOCX files\n\nYou'll need to specify the document type (Policy, Procedure, Protocol, etc.) when uploading.",
            'response_type': 'upload_guidance',
            'buttons': [
                {'text': 'Upload Document', 'value': 'start_upload', 'action': 'redirect'},
                {'text': 'View Document Types', 'value': 'view_types', 'action': 'info'},
                {'text': 'Get Help', 'value': 'help', 'action': 'intent'}
            ],
            'quick_replies': ['Start upload', 'Show types'],
            'session_id': conversation.session_id,
            'conversation_id': str(conversation.id),
            'metadata': {
                'api_endpoint': '/api/upload/',
                'method': 'POST',
                'supported_formats': ['pdf', 'docx'],
                'required_fields': ['file', 'standard_type_id']
            }
        }

    def _handle_content_generate(self, message: str, conversation: 'ChatbotConversation',
                                parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle content generation intent."""
        return {
            'message': "I can help you generate medical content using AI. Available content types include:\n\n• Policies\n• Procedures\n• Best Practices\n• Standing Orders\n\nWhat type of content would you like to generate?",
            'response_type': 'generation_guidance',
            'buttons': [
                {'text': 'Generate Policy', 'value': 'generate_policy', 'action': 'form'},
                {'text': 'Generate Procedure', 'value': 'generate_procedure', 'action': 'form'},
                {'text': 'View All Types', 'value': 'view_content_types', 'action': 'info'},
                {'text': 'Get Help', 'value': 'help', 'action': 'intent'}
            ],
            'quick_replies': ['Policy', 'Procedure', 'Show all types'],
            'session_id': conversation.session_id,
            'conversation_id': str(conversation.id),
            'metadata': {
                'api_endpoint': '/api/generate/',
                'method': 'POST',
                'required_fields': ['topic', 'content_type', 'model_name']
            }
        }

    def _handle_audit_questions(self, message: str, conversation: 'ChatbotConversation',
                               parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle audit questions intent."""
        return {
            'message': "I can help you create audit questions for compliance checking. You can:\n\n• Generate questions for specific policies\n• Choose from different AI models\n• Specify the number of questions needed\n\nWhat policy would you like to create audit questions for?",
            'response_type': 'audit_guidance',
            'buttons': [
                {'text': 'Generate Questions', 'value': 'start_audit_generation', 'action': 'form'},
                {'text': 'View Existing Questions', 'value': 'view_questions', 'action': 'redirect'},
                {'text': 'Get Help', 'value': 'help', 'action': 'intent'}
            ],
            'quick_replies': ['Generate new', 'View existing'],
            'session_id': conversation.session_id,
            'conversation_id': str(conversation.id),
            'metadata': {
                'api_endpoint': '/api/audit-questions/generate/',
                'method': 'POST',
                'required_fields': ['policy_name', 'ai_model', 'number_of_questions']
            }
        }

    def _handle_general_inquiry(self, message: str, conversation: 'ChatbotConversation',
                               parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general inquiry intent."""
        return {
            'message': "I'm here to help you with:\n\n• Registering complaints\n• Checking complaint status\n• Submitting feedback\n• Uploading documents\n• Generating content\n• Creating audit questions\n\nWhat would you like to do?",
            'response_type': 'menu',
            'buttons': [
                {'text': 'Register Complaint', 'value': 'complaint_register', 'action': 'intent'},
                {'text': 'Check Status', 'value': 'complaint_status', 'action': 'intent'},
                {'text': 'Submit Feedback', 'value': 'feedback_submit', 'action': 'intent'},
                {'text': 'Upload Document', 'value': 'document_upload', 'action': 'intent'},
                {'text': 'Generate Content', 'value': 'content_generate', 'action': 'intent'},
                {'text': 'Audit Questions', 'value': 'audit_questions', 'action': 'intent'}
            ],
            'quick_replies': ['Complaint', 'Feedback', 'Upload', 'Generate'],
            'session_id': conversation.session_id,
            'conversation_id': str(conversation.id)
        }

    def _handle_fallback(self, message: str, conversation: 'ChatbotConversation',
                        parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle fallback when no intent is detected."""
        return {
            'message': "I'm not sure I understand. I can help you with medical complaints, feedback, document uploads, content generation, and audit questions. Could you please clarify what you'd like to do?",
            'response_type': 'fallback',
            'buttons': [
                {'text': 'Show Main Menu', 'value': 'general_inquiry', 'action': 'intent'},
                {'text': 'Get Help', 'value': 'help', 'action': 'intent'}
            ],
            'quick_replies': ['Main menu', 'Help'],
            'session_id': conversation.session_id,
            'conversation_id': str(conversation.id)
        }


class ChatbotEngine:
    """
    Main chatbot engine that coordinates intent detection and action dispatching.
    """

    def __init__(self):
        self.intent_detector = IntentDetector()
        self.action_dispatcher = ActionDispatcher()

    def process_message(self, message: str, session_id: str = None,
                       user: Optional['User'] = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process user message and return chatbot response.

        Args:
            message: User's input message
            session_id: Conversation session ID
            user: Authenticated user (if any)
            context: Additional context

        Returns:
            Chatbot response dictionary
        """
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())

        try:
            # Detect intent
            intent_type, confidence = self.intent_detector.detect_intent(message, context)

            # Dispatch action
            response = self.action_dispatcher.dispatch_action(
                intent_type=intent_type,
                message=message,
                session_id=session_id,
                user=user,
                parameters={'confidence': confidence}
            )

            # Add intent detection info to response
            response.update({
                'intent_detected': intent_type,
                'confidence_score': confidence
            })

            # Log the interaction
            self._log_interaction(session_id, message, response, intent_type, confidence)

            return response

        except Exception as e:
            logger.error(f"Error processing chatbot message: {e}")
            return {
                'message': "I'm experiencing some technical difficulties. Please try again later or contact support.",
                'response_type': 'error',
                'session_id': session_id,
                'error': str(e)
            }

    def _log_interaction(self, session_id: str, user_message: str, bot_response: Dict[str, Any],
                        intent_type: str, confidence: float):
        """Log the chatbot interaction."""
        try:
            from ..models import ChatbotConversation, ChatbotIntent, ChatbotMessage
            conversation = ChatbotConversation.objects.get(session_id=session_id)
            intent = ChatbotIntent.objects.filter(intent_type=intent_type).first()

            # Log user message
            ChatbotMessage.objects.create(
                conversation=conversation,
                message_type='user',
                content=user_message,
                intent_detected=intent,
                confidence_score=confidence
            )

            # Log bot response
            ChatbotMessage.objects.create(
                conversation=conversation,
                message_type='bot',
                content=bot_response.get('message', ''),
                metadata={
                    'response_type': bot_response.get('response_type'),
                    'buttons': bot_response.get('buttons', []),
                    'quick_replies': bot_response.get('quick_replies', [])
                }
            )

        except Exception as e:
            logger.error(f"Error logging chatbot interaction: {e}")

    def get_quick_actions(self, user: Optional['User'] = None) -> List[Dict[str, Any]]:
        """Get available quick actions for the user."""
        from ..models import ChatbotQuickAction
        queryset = ChatbotQuickAction.objects.filter(is_active=True)

        if not user or not user.is_authenticated:
            queryset = queryset.filter(requires_auth=False)

        actions = []
        for action in queryset.order_by('order'):
            actions.append({
                'id': str(action.id),
                'title': action.title,
                'description': action.description,
                'button_text': action.button_text,
                'icon': action.icon,
                'intent_type': action.intent.intent_type,
                'requires_auth': action.requires_auth
            })

        return actions
