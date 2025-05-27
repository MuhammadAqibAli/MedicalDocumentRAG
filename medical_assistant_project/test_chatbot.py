#!/usr/bin/env python
"""
Test script to verify chatbot functionality.
Run this script to test the chatbot without relying on terminal output.
"""

import os
import sys
import django
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical_assistant_project.settings')
django.setup()

def log_result(test_name, success, message="", data=None):
    """Log test results to a file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "✅ PASS" if success else "❌ FAIL"
    
    result = f"[{timestamp}] {status} {test_name}"
    if message:
        result += f" - {message}"
    if data:
        result += f"\nData: {json.dumps(data, indent=2)}"
    result += "\n" + "="*50 + "\n"
    
    # Write to file
    with open("chatbot_test_results.txt", "a", encoding="utf-8") as f:
        f.write(result)
    
    # Also print to console (might work)
    print(result)

def test_imports():
    """Test if all chatbot components can be imported."""
    try:
        from api.services.chatbot_engine import ChatbotEngine
        log_result("Import ChatbotEngine", True)
        return True
    except Exception as e:
        log_result("Import ChatbotEngine", False, str(e))
        return False

def test_database_models():
    """Test if chatbot models are accessible."""
    try:
        from api.models import ChatbotIntent, ChatbotResponse, ChatbotQuickAction
        
        intent_count = ChatbotIntent.objects.count()
        response_count = ChatbotResponse.objects.count()
        action_count = ChatbotQuickAction.objects.count()
        
        data = {
            "intents": intent_count,
            "responses": response_count,
            "quick_actions": action_count
        }
        
        log_result("Database Models", True, f"Found {intent_count} intents, {response_count} responses, {action_count} actions", data)
        return True
    except Exception as e:
        log_result("Database Models", False, str(e))
        return False

def test_chatbot_engine():
    """Test chatbot engine functionality."""
    try:
        from api.services.chatbot_engine import ChatbotEngine
        
        engine = ChatbotEngine()
        
        # Test message processing
        response = engine.process_message("Hello", "test-session-123")
        
        log_result("ChatbotEngine Process Message", True, "Message processed successfully", {
            "input": "Hello",
            "response_type": response.get("response_type"),
            "intent_detected": response.get("intent_detected"),
            "confidence_score": response.get("confidence_score")
        })
        
        # Test quick actions
        quick_actions = engine.get_quick_actions()
        log_result("ChatbotEngine Quick Actions", True, f"Retrieved {len(quick_actions)} quick actions", {
            "count": len(quick_actions),
            "actions": [action.get("title") for action in quick_actions[:3]]  # First 3 titles
        })
        
        return True
    except Exception as e:
        log_result("ChatbotEngine Functionality", False, str(e))
        return False

def test_api_views():
    """Test if chatbot views can be imported."""
    try:
        from api.views import (
            ChatbotMessageView, ChatbotHealthView, ChatbotQuickActionsView,
            ChatbotIntentDetectionView, ChatbotActionView
        )
        log_result("Import API Views", True, "All chatbot views imported successfully")
        return True
    except Exception as e:
        log_result("Import API Views", False, str(e))
        return False

def test_serializers():
    """Test if chatbot serializers work."""
    try:
        from api.serializers import (
            ChatbotMessageRequestSerializer, ChatbotResponseDataSerializer,
            ChatbotQuickActionSerializer
        )
        
        # Test message request serializer
        data = {"message": "Hello, I want to register a complaint"}
        serializer = ChatbotMessageRequestSerializer(data=data)
        is_valid = serializer.is_valid()
        
        log_result("Serializers", is_valid, "Message request serializer validation", {
            "input_data": data,
            "is_valid": is_valid,
            "errors": serializer.errors if not is_valid else None
        })
        
        return is_valid
    except Exception as e:
        log_result("Serializers", False, str(e))
        return False

def main():
    """Run all tests."""
    # Clear previous results
    with open("chatbot_test_results.txt", "w", encoding="utf-8") as f:
        f.write(f"Chatbot Test Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*60 + "\n\n")
    
    tests = [
        ("Imports", test_imports),
        ("Database Models", test_database_models),
        ("API Views", test_api_views),
        ("Serializers", test_serializers),
        ("ChatbotEngine", test_chatbot_engine),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            log_result(f"Test {test_name}", False, f"Unexpected error: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    summary = f"\nTEST SUMMARY: {passed}/{total} tests passed"
    if passed == total:
        summary += " 🎉 ALL TESTS PASSED!"
    else:
        summary += f" ⚠️  {total - passed} tests failed"
    
    log_result("FINAL SUMMARY", passed == total, summary)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
