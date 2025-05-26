# Frontend Chatbot Integration Guide

## Overview

This guide provides everything you need to integrate the modular intent-based chatbot into your React frontend. The chatbot system is designed to work seamlessly with your existing APIs while providing a conversational interface for users.

## Quick Start

### 1. Basic Chat Component Structure

```jsx
import React, { useState, useEffect } from 'react';

const Chatbot = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [quickActions, setQuickActions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    initializeChatbot();
  }, []);

  const initializeChatbot = async () => {
    // Get quick actions and send initial greeting
    await loadQuickActions();
    await sendMessage('hello');
  };

  // Component implementation...
};
```

### 2. Core API Functions

```javascript
// Base API configuration
const API_BASE = '/api';

// Send message to chatbot
const sendMessage = async (message, sessionId = null) => {
  const response = await fetch(`${API_BASE}/chatbot/message/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getAuthToken()}`, // If user is authenticated
    },
    body: JSON.stringify({
      message: message,
      session_id: sessionId,
      user_context: {
        user_id: getCurrentUser()?.id
      }
    })
  });
  
  if (!response.ok) {
    throw new Error('Failed to send message');
  }
  
  return await response.json();
};

// Get quick actions
const getQuickActions = async () => {
  const response = await fetch(`${API_BASE}/chatbot/quick-actions/`, {
    headers: {
      'Authorization': `Bearer ${getAuthToken()}`,
    }
  });
  
  return await response.json();
};

// Detect intent (optional - for advanced features)
const detectIntent = async (message) => {
  const response = await fetch(`${API_BASE}/chatbot/intent-detect/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message })
  });
  
  return await response.json();
};
```

## Response Handling

### Message Response Structure

```javascript
const handleChatbotResponse = (response) => {
  // Add bot message to chat
  const botMessage = {
    id: Date.now(),
    type: 'bot',
    content: response.message,
    timestamp: new Date(),
    buttons: response.buttons || [],
    quickReplies: response.quick_replies || [],
    metadata: response.metadata || {}
  };
  
  setMessages(prev => [...prev, botMessage]);
  
  // Update session ID if provided
  if (response.session_id) {
    setSessionId(response.session_id);
  }
  
  // Handle specific response types
  switch (response.response_type) {
    case 'greeting':
      handleGreeting(response);
      break;
    case 'form_guidance':
      handleFormGuidance(response);
      break;
    case 'error':
      handleError(response);
      break;
    default:
      // Standard message handling
      break;
  }
};
```

### Button Handling

```javascript
const handleButtonClick = async (button) => {
  // Add user action to chat
  const userMessage = {
    id: Date.now(),
    type: 'user',
    content: button.text,
    timestamp: new Date(),
    isButton: true
  };
  
  setMessages(prev => [...prev, userMessage]);
  
  // Handle different button actions
  switch (button.action) {
    case 'intent':
      // Trigger specific intent
      await handleIntentAction(button.value);
      break;
    case 'redirect':
      // Redirect to form or page
      handleRedirect(button.value);
      break;
    case 'input':
      // Request user input
      handleInputRequest(button.value);
      break;
    default:
      // Send as regular message
      await sendMessage(button.value, sessionId);
      break;
  }
};

const handleIntentAction = async (intentType) => {
  const response = await fetch(`${API_BASE}/chatbot/handle-intent/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      intent_type: intentType,
      session_id: sessionId,
      parameters: {}
    })
  });
  
  const result = await response.json();
  handleChatbotResponse(result);
};
```

## UI Components

### 1. Chat Message Component

```jsx
const ChatMessage = ({ message, onButtonClick, onQuickReplyClick }) => {
  return (
    <div className={`message ${message.type}`}>
      <div className="message-content">
        {message.content}
      </div>
      
      {message.buttons && message.buttons.length > 0 && (
        <div className="message-buttons">
          {message.buttons.map((button, index) => (
            <button
              key={index}
              className="chat-button"
              onClick={() => onButtonClick(button)}
            >
              {button.icon && <span className="button-icon">{button.icon}</span>}
              {button.text}
            </button>
          ))}
        </div>
      )}
      
      {message.quickReplies && message.quickReplies.length > 0 && (
        <div className="quick-replies">
          {message.quickReplies.map((reply, index) => (
            <button
              key={index}
              className="quick-reply"
              onClick={() => onQuickReplyClick(reply)}
            >
              {reply}
            </button>
          ))}
        </div>
      )}
      
      <div className="message-timestamp">
        {message.timestamp.toLocaleTimeString()}
      </div>
    </div>
  );
};
```

### 2. Quick Actions Panel

```jsx
const QuickActionsPanel = ({ quickActions, onActionClick }) => {
  return (
    <div className="quick-actions-panel">
      <h3>Quick Actions</h3>
      <div className="quick-actions-grid">
        {quickActions.map((action) => (
          <button
            key={action.id}
            className="quick-action-card"
            onClick={() => onActionClick(action)}
            disabled={action.requires_auth && !isAuthenticated()}
          >
            <div className="action-icon">{action.icon}</div>
            <div className="action-title">{action.title}</div>
            <div className="action-description">{action.description}</div>
          </button>
        ))}
      </div>
    </div>
  );
};
```

### 3. Chat Input Component

```jsx
const ChatInput = ({ onSendMessage, isLoading }) => {
  const [inputValue, setInputValue] = useState('');
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading) {
      onSendMessage(inputValue.trim());
      setInputValue('');
    }
  };
  
  return (
    <form className="chat-input-form" onSubmit={handleSubmit}>
      <input
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        placeholder="Type your message..."
        disabled={isLoading}
        className="chat-input"
      />
      <button
        type="submit"
        disabled={!inputValue.trim() || isLoading}
        className="send-button"
      >
        {isLoading ? 'Sending...' : 'Send'}
      </button>
    </form>
  );
};
```

## Integration with Existing Forms

### Complaint Registration Integration

```javascript
const handleComplaintFormRedirect = (metadata) => {
  // Pre-fill form with chatbot context
  const formData = {
    title: metadata.extracted_title || '',
    complaint_details: metadata.extracted_details || '',
    // ... other fields
  };
  
  // Navigate to complaint form with pre-filled data
  navigate('/complaints/new', { state: { formData } });
};

// In your complaint form component
const ComplaintForm = () => {
  const location = useLocation();
  const [formData, setFormData] = useState(
    location.state?.formData || {}
  );
  
  // Form implementation...
};
```

### Feedback Form Integration

```javascript
const handleFeedbackFormRedirect = (metadata) => {
  // Similar to complaint form
  const formData = {
    title: metadata.extracted_title || '',
    feedback_details: metadata.extracted_details || '',
  };
  
  navigate('/feedback/new', { state: { formData } });
};
```

## State Management

### Using React Context

```jsx
// ChatbotContext.js
const ChatbotContext = createContext();

export const ChatbotProvider = ({ children }) => {
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [quickActions, setQuickActions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  
  const sendMessage = async (message) => {
    setIsLoading(true);
    try {
      // Add user message
      const userMessage = {
        id: Date.now(),
        type: 'user',
        content: message,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, userMessage]);
      
      // Send to API
      const response = await sendMessageToAPI(message, sessionId);
      
      // Handle response
      handleChatbotResponse(response);
      
      // Update session ID
      if (response.session_id) {
        setSessionId(response.session_id);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      // Handle error
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <ChatbotContext.Provider value={{
      messages,
      sessionId,
      quickActions,
      isLoading,
      sendMessage,
      // ... other methods
    }}>
      {children}
    </ChatbotContext.Provider>
  );
};
```

## Styling Examples

### CSS for Chat Interface

```css
.chatbot-container {
  display: flex;
  flex-direction: column;
  height: 600px;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background-color: #f9f9f9;
}

.message {
  margin-bottom: 16px;
  max-width: 80%;
}

.message.user {
  margin-left: auto;
  text-align: right;
}

.message.bot {
  margin-right: auto;
}

.message-content {
  padding: 12px 16px;
  border-radius: 18px;
  background-color: white;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.message.user .message-content {
  background-color: #007bff;
  color: white;
}

.message-buttons {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chat-button {
  padding: 8px 16px;
  border: 1px solid #007bff;
  background-color: white;
  color: #007bff;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.chat-button:hover {
  background-color: #007bff;
  color: white;
}

.quick-replies {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.quick-reply {
  padding: 4px 12px;
  border: 1px solid #ddd;
  background-color: #f8f9fa;
  border-radius: 12px;
  font-size: 14px;
  cursor: pointer;
}

.chat-input-form {
  display: flex;
  padding: 16px;
  border-top: 1px solid #ddd;
  background-color: white;
}

.chat-input {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 20px;
  outline: none;
}

.send-button {
  margin-left: 8px;
  padding: 12px 24px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
}

.quick-actions-panel {
  padding: 16px;
  background-color: #f8f9fa;
  border-bottom: 1px solid #ddd;
}

.quick-actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.quick-action-card {
  padding: 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: white;
  cursor: pointer;
  text-align: center;
  transition: all 0.2s;
}

.quick-action-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.action-icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.action-title {
  font-weight: bold;
  margin-bottom: 4px;
}

.action-description {
  font-size: 14px;
  color: #666;
}
```

## Error Handling

```javascript
const handleChatbotError = (error) => {
  console.error('Chatbot error:', error);
  
  const errorMessage = {
    id: Date.now(),
    type: 'bot',
    content: 'I apologize, but I encountered an error. Please try again or contact support.',
    timestamp: new Date(),
    isError: true
  };
  
  setMessages(prev => [...prev, errorMessage]);
};

// Retry mechanism
const retryLastMessage = async () => {
  const lastUserMessage = messages
    .filter(m => m.type === 'user')
    .pop();
    
  if (lastUserMessage) {
    await sendMessage(lastUserMessage.content);
  }
};
```

## Testing

### Unit Tests Example

```javascript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Chatbot from './Chatbot';

// Mock API calls
jest.mock('./api', () => ({
  sendMessage: jest.fn(),
  getQuickActions: jest.fn(),
}));

describe('Chatbot', () => {
  test('sends message when form is submitted', async () => {
    const mockResponse = {
      message: 'Hello! How can I help you?',
      response_type: 'greeting',
      session_id: 'test-session'
    };
    
    require('./api').sendMessage.mockResolvedValue(mockResponse);
    
    render(<Chatbot />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByText('Send');
    
    fireEvent.change(input, { target: { value: 'Hello' } });
    fireEvent.click(sendButton);
    
    await waitFor(() => {
      expect(screen.getByText('Hello! How can I help you?')).toBeInTheDocument();
    });
  });
});
```

This guide provides a comprehensive foundation for integrating the chatbot into your React frontend. The modular design allows you to customize and extend the functionality as needed while maintaining clean separation between the chatbot interface and your existing application logic.
