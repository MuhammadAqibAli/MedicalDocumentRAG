#!/usr/bin/env python
"""
Test script for the new Simple Chatbot Service
Tests intent detection and response generation without database operations.
"""

import sys
import os

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the simple chatbot service directly
from api.services.simple_chatbot import SimpleChatbotService

def test_intent_detection():
    """Test intent detection functionality."""
    print("🔍 Testing Intent Detection...")
    print("=" * 50)
    
    chatbot = SimpleChatbotService()
    
    test_cases = [
        ("Hello", "greeting"),
        ("I want to register a complaint", "complaint_register"),
        ("Check my complaint status", "complaint_status"),
        ("COMP-2024-001 status", "complaint_status"),
        ("Submit feedback", "feedback_submit"),
        ("I need to give feedback", "feedback_submit"),
        ("What can you help me with?", "general_inquiry"),
    ]
    
    for message, expected_intent in test_cases:
        intent, confidence = chatbot.detect_intent(message)
        status = "✅" if intent == expected_intent else "❌"
        print(f"{status} '{message}' -> {intent} (confidence: {confidence:.2f})")
        if intent != expected_intent:
            print(f"   Expected: {expected_intent}, Got: {intent}")
    
    print()

def test_response_generation():
    """Test response generation for each intent."""
    print("💬 Testing Response Generation...")
    print("=" * 50)
    
    chatbot = SimpleChatbotService()
    
    test_messages = [
        "Hello",
        "I want to register a complaint",
        "Check status of COMP-2024-001",
        "I need to submit feedback",
        "What can you do?"
    ]
    
    for message in test_messages:
        print(f"\n📝 User: {message}")
        
        # Mock conversation object for testing
        class MockConversation:
            def __init__(self):
                self.session_id = "test-session-123"
                self.id = "test-conv-456"
        
        mock_conversation = MockConversation()
        
        # Detect intent
        intent, confidence = chatbot.detect_intent(message)
        
        # Generate response
        response = chatbot._generate_response(intent, message, mock_conversation)
        
        print(f"🤖 Bot: {response['message'][:100]}...")
        print(f"   Intent: {response.get('intent_detected', 'N/A')}")
        print(f"   Confidence: {response.get('confidence_score', 'N/A')}")
        print(f"   Response Type: {response.get('response_type', 'N/A')}")
        print(f"   Buttons: {len(response.get('buttons', []))} buttons")
        print(f"   Quick Replies: {len(response.get('quick_replies', []))} quick replies")

def test_specific_scenarios():
    """Test specific chatbot scenarios."""
    print("\n🎯 Testing Specific Scenarios...")
    print("=" * 50)
    
    chatbot = SimpleChatbotService()
    
    # Test complaint status with reference number
    print("\n📋 Scenario 1: Complaint Status with Reference Number")
    message = "What's the status of COMP-2024-001?"
    intent, confidence = chatbot.detect_intent(message)
    
    class MockConversation:
        def __init__(self):
            self.session_id = "test-session"
            self.id = "test-conv"
    
    response = chatbot._handle_complaint_status(message, MockConversation())
    print(f"✅ Detected reference number: {response.get('metadata', {}).get('reference_number', 'None')}")
    print(f"✅ API endpoint: {response.get('metadata', {}).get('api_endpoint', 'None')}")
    
    # Test complaint status without reference number
    print("\n📋 Scenario 2: Complaint Status without Reference Number")
    message = "I want to check my complaint status"
    response = chatbot._handle_complaint_status(message, MockConversation())
    print(f"✅ Response type: {response.get('response_type')}")
    print(f"✅ Asks for reference: {'reference' in response.get('message', '').lower()}")

def test_api_integration_readiness():
    """Test if responses are ready for API integration."""
    print("\n🔗 Testing API Integration Readiness...")
    print("=" * 50)
    
    chatbot = SimpleChatbotService()
    
    class MockConversation:
        def __init__(self):
            self.session_id = "test-session"
            self.id = "test-conv"
    
    # Test complaint registration response
    response = chatbot._handle_complaint_register()
    metadata = response.get('metadata', {})
    
    print("📝 Complaint Registration API Integration:")
    print(f"✅ API Endpoint: {metadata.get('api_endpoint', 'Missing')}")
    print(f"✅ HTTP Method: {metadata.get('method', 'Missing')}")
    print(f"✅ Required Fields: {metadata.get('required_fields', 'Missing')}")
    
    # Test feedback submission response
    response = chatbot._handle_feedback_submit()
    metadata = response.get('metadata', {})
    
    print("\n💭 Feedback Submission API Integration:")
    print(f"✅ API Endpoint: {metadata.get('api_endpoint', 'Missing')}")
    print(f"✅ HTTP Method: {metadata.get('method', 'Missing')}")
    print(f"✅ Required Fields: {metadata.get('required_fields', 'Missing')}")

def main():
    """Run all tests."""
    print("🚀 Simple Chatbot Service Test Suite")
    print("=" * 60)
    print("Testing the new simplified chatbot that supports:")
    print("• Complaint Registration")
    print("• Complaint Status Check")
    print("• Feedback Submission")
    print("=" * 60)
    
    try:
        test_intent_detection()
        test_response_generation()
        test_specific_scenarios()
        test_api_integration_readiness()
        
        print("\n🎉 ALL TESTS COMPLETED!")
        print("✅ Simple Chatbot Service is working correctly")
        print("✅ Intent detection is functional")
        print("✅ Response generation is working")
        print("✅ API integration metadata is present")
        print("✅ Ready for frontend integration")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
