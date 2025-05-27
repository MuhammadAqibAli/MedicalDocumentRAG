# Modular Intent-Based Chatbot System Documentation

## Overview

This document provides comprehensive documentation for the modular, intent-based chatbot system that integrates seamlessly with your existing Django backend APIs. The chatbot acts as a smart interface layer over your existing functionality without requiring any changes to your current APIs.

## Architecture

### Core Components

1. **Intent Detection Engine** (`IntentDetector`)
   - Analyzes user messages to determine intent
   - Uses keyword matching and regex patterns
   - Supports contextual intent detection

2. **Action Dispatcher** (`ActionDispatcher`)
   - Routes detected intents to appropriate handlers
   - Manages conversation state and context
   - Integrates with existing API endpoints

3. **Conversation Manager**
   - Tracks conversation sessions
   - Maintains conversation context and state
   - Logs all interactions for analytics

4. **Response Generator**
   - Provides predefined responses for each intent
   - Supports dynamic button generation
   - Manages quick reply options

## Database Models

### ChatbotIntent
Stores intent configurations and mappings to API endpoints.

```python
class ChatbotIntent(models.Model):
    name = models.CharField(max_length=100, unique=True)
    intent_type = models.CharField(max_length=50, choices=INTENT_TYPES)
    description = models.TextField()
    keywords = models.JSONField(default=list)
    patterns = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    requires_auth = models.BooleanField(default=False)
    api_endpoint = models.CharField(max_length=255, null=True, blank=True)
```

### ChatbotResponse
Stores predefined responses for different scenarios.

```python
class ChatbotResponse(models.Model):
    intent = models.ForeignKey(ChatbotIntent, on_delete=models.CASCADE)
    response_type = models.CharField(max_length=50, choices=RESPONSE_TYPES)
    message = models.TextField()
    buttons = models.JSONField(default=list)
    quick_replies = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)
```

### ChatbotConversation
Tracks conversation sessions and state.

```python
class ChatbotConversation(models.Model):
    session_id = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    current_intent = models.ForeignKey(ChatbotIntent, on_delete=models.SET_NULL)
    context = models.JSONField(default=dict)
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
```

### ChatbotMessage
Logs individual messages in conversations.

```python
class ChatbotMessage(models.Model):
    conversation = models.ForeignKey(ChatbotConversation, on_delete=models.CASCADE)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    content = models.TextField()
    intent_detected = models.ForeignKey(ChatbotIntent, on_delete=models.SET_NULL)
    confidence_score = models.FloatField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
```

### ChatbotQuickAction
Defines quick action buttons for the interface.

```python
class ChatbotQuickAction(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    intent = models.ForeignKey(ChatbotIntent, on_delete=models.CASCADE)
    button_text = models.CharField(max_length=50)
    icon = models.CharField(max_length=50, null=True, blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    requires_auth = models.BooleanField(default=False)
```

## Intent Types and Mappings

### Supported Intents

| Intent Type | Description | Existing API Endpoint | Method |
|-------------|-------------|----------------------|---------|
| `greeting` | User greets the chatbot | N/A | N/A |
| `complaint_register` | Register new complaint | `/api/complaints/` | POST |
| `complaint_status` | Check complaint status | `/api/complaints/{id}/` | GET |
| `feedback_submit` | Submit feedback | `/api/feedback/` | POST |
| `document_upload` | Upload document | `/api/upload/` | POST |
| `content_generate` | Generate content | `/api/generate/` | POST |
| `audit_questions` | Create audit questions | `/api/audit-questions/generate/` | POST |
| `general_inquiry` | General help/menu | N/A | N/A |

### Intent Detection Logic

1. **Keyword Matching**: Exact keyword matches in user message
2. **Pattern Matching**: Regex patterns for complex intent detection
3. **Contextual Detection**: Based on conversation history and current state
4. **Confidence Scoring**: Each detection method provides a confidence score

## API Endpoints

### Core Chatbot Endpoints

#### Process Message
- **URL**: `POST /api/chatbot/message/`
- **Purpose**: Main chatbot interaction endpoint
- **Input**: User message, optional session ID, user context
- **Output**: Chatbot response with buttons, quick replies, and metadata

#### Intent Detection
- **URL**: `POST /api/chatbot/intent-detect/`
- **Purpose**: Detect intent without full conversation processing
- **Input**: User message
- **Output**: Detected intent, confidence score, and API mapping

#### Handle Intent Action
- **URL**: `POST /api/chatbot/handle-intent/`
- **Purpose**: Execute specific action for detected intent
- **Input**: Intent type, session ID, parameters
- **Output**: Action-specific response

#### Quick Actions
- **URL**: `GET /api/chatbot/quick-actions/`
- **Purpose**: Get available quick action buttons
- **Input**: None (user context from authentication)
- **Output**: List of available quick actions

#### Health Check
- **URL**: `GET /api/chatbot/health/`
- **Purpose**: Check chatbot service health
- **Input**: None
- **Output**: Service status and statistics

### Management Endpoints

#### Conversations
- **List**: `GET /api/chatbot/conversations/`
- **Detail**: `GET /api/chatbot/conversations/{id}/`
- **Complete**: `POST /api/chatbot/conversations/{id}/complete/`

#### Intents (Admin)
- **List**: `GET /api/chatbot/intents/`
- **Detail**: `GET /api/chatbot/intents/{id}/`

## Integration with Existing APIs

### How It Works

1. **No API Changes Required**: The chatbot acts as a smart interface layer
2. **Intent Mapping**: Each intent maps to existing API endpoints
3. **Parameter Extraction**: Chatbot guides users to provide required parameters
4. **API Calls**: Backend makes calls to existing APIs on behalf of users
5. **Response Formatting**: API responses are formatted for chatbot presentation

### Example Integration Flow

```
User: "I want to register a complaint"
↓
Intent Detection: complaint_register (confidence: 0.95)
↓
Action Dispatcher: Provides guidance for complaint form
↓
User provides details → API call to POST /api/complaints/
↓
Response: Confirmation with complaint reference number
```

## Setup and Configuration

### 1. Run Migrations

```bash
python manage.py migrate
```

### 2. Setup Initial Data

```bash
python manage.py setup_chatbot
```

This command creates:
- 8 predefined intents
- 5 response templates
- 6 quick action buttons

### 3. Customize Intents (Optional)

Access Django Admin to:
- Modify intent keywords and patterns
- Add new intents
- Configure API endpoint mappings
- Adjust response templates

## Frontend Integration

### Basic Chat Interface

```javascript
// Send message to chatbot
const sendMessage = async (message, sessionId = null) => {
  const response = await fetch('/api/chatbot/message/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: message,
      session_id: sessionId,
      user_context: {
        user_id: currentUser?.id
      }
    })
  });
  
  return await response.json();
};

// Get quick actions for initial display
const getQuickActions = async () => {
  const response = await fetch('/api/chatbot/quick-actions/');
  return await response.json();
};
```

### Response Handling

```javascript
const handleChatbotResponse = (response) => {
  // Display message
  displayMessage(response.message, 'bot');
  
  // Show buttons if available
  if (response.buttons && response.buttons.length > 0) {
    displayButtons(response.buttons);
  }
  
  // Show quick replies
  if (response.quick_replies && response.quick_replies.length > 0) {
    displayQuickReplies(response.quick_replies);
  }
  
  // Handle metadata (API endpoint info, etc.)
  if (response.metadata) {
    handleMetadata(response.metadata);
  }
};
```

## Extending the System

### Adding New Intents

1. **Create Intent in Database**:
```python
intent = ChatbotIntent.objects.create(
    name='Appointment Booking',
    intent_type='appointment_book',
    description='User wants to book an appointment',
    keywords=['appointment', 'book', 'schedule', 'meeting'],
    patterns=[r'\b(book|schedule)\s+(appointment|meeting)\b'],
    api_endpoint='/api/appointments/',
    requires_auth=True
)
```

2. **Add Handler in ActionDispatcher**:
```python
def _handle_appointment_book(self, message, conversation, parameters):
    return {
        'message': 'I can help you book an appointment...',
        'response_type': 'appointment_guidance',
        'buttons': [...],
        'metadata': {
            'api_endpoint': '/api/appointments/',
            'method': 'POST'
        }
    }
```

3. **Update Handler Map**:
```python
handler_map = {
    # ... existing handlers
    'appointment_book': self._handle_appointment_book,
}
```

### Adding AI Integration

For more sophisticated intent detection, you can integrate AI models:

```python
def _detect_intent_with_ai(self, message):
    # Call to OpenAI, Claude, or other AI service
    response = ai_service.analyze_intent(message)
    return response.intent_type, response.confidence
```

## Monitoring and Analytics

### Conversation Analytics

```python
# Get conversation statistics
from django.db.models import Count, Avg
from api.models import ChatbotConversation, ChatbotMessage

# Most common intents
intent_stats = ChatbotMessage.objects.filter(
    intent_detected__isnull=False
).values('intent_detected__intent_type').annotate(
    count=Count('id')
).order_by('-count')

# Average conversation length
avg_length = ChatbotConversation.objects.annotate(
    message_count=Count('messages')
).aggregate(avg_messages=Avg('message_count'))

# Completion rate
completion_rate = ChatbotConversation.objects.filter(
    status='completed'
).count() / ChatbotConversation.objects.count()
```

### Performance Monitoring

- Monitor intent detection accuracy
- Track conversation completion rates
- Analyze user satisfaction through feedback
- Monitor API integration success rates

## Security Considerations

1. **Authentication**: Some intents require user authentication
2. **Authorization**: Role-based access to certain features
3. **Input Validation**: All user inputs are validated
4. **Rate Limiting**: Implement rate limiting for API endpoints
5. **Data Privacy**: Conversation logs follow data retention policies

## Troubleshooting

### Common Issues

1. **Intent Not Detected**: Check keywords and patterns in ChatbotIntent
2. **API Integration Fails**: Verify endpoint URLs and authentication
3. **Conversation State Lost**: Check session management and storage
4. **Performance Issues**: Monitor database queries and optimize as needed

### Debug Mode

Enable debug logging to trace intent detection and action dispatching:

```python
import logging
logging.getLogger('api.services.chatbot_engine').setLevel(logging.DEBUG)
```

## Future Enhancements

1. **Machine Learning**: Implement ML-based intent detection
2. **Multi-language Support**: Add support for multiple languages
3. **Voice Integration**: Add voice input/output capabilities
4. **Advanced Analytics**: Implement conversation flow analysis
5. **A/B Testing**: Test different response strategies
6. **Integration Expansion**: Add more API integrations as needed

This modular design ensures the chatbot can grow with your application while maintaining clean separation of concerns and easy maintainability.
