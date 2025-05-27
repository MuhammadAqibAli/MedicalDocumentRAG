#!/usr/bin/env python
"""
Quick test for the fixed simple chatbot
"""

import sys
import os
sys.path.append('.')

# Test the updated simple chatbot
from api.services.simple_chatbot import SimpleChatbotService

def test_chatbot():
    chatbot = SimpleChatbotService()

    # Test the specific message that was failing
    test_message = 'Register Complaint'
    print(f'Testing message: "{test_message}"')

    # Test intent detection
    intent, confidence = chatbot.detect_intent(test_message)
    print(f'Intent detected: {intent} (confidence: {confidence})')

    # Test full message processing
    try:
        response = chatbot.process_message(test_message, 'test-session-123')
        print(f'Response generated successfully!')
        print(f'Message: {response["message"][:100]}...')
        print(f'Response type: {response.get("response_type")}')
        print(f'Buttons: {len(response.get("buttons", []))} buttons')
        print(f'Session ID: {response.get("session_id")}')
        print('✅ Chatbot is working correctly!')
        return True
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_chatbot()
    sys.exit(0 if success else 1)
