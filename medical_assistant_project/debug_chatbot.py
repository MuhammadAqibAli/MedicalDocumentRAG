#!/usr/bin/env python
"""
Debug script to identify chatbot 500 errors.
"""

import os
import sys
import django
import traceback
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical_assistant_project.settings')
django.setup()

def log_debug(message, error=None):
    """Log debug information."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    if error:
        log_entry += f"\nError: {error}\nTraceback:\n{traceback.format_exc()}"
    log_entry += "\n" + "="*50 + "\n"
    
    with open("chatbot_debug.txt", "a", encoding="utf-8") as f:
        f.write(log_entry)
    print(log_entry)

def test_chatbot_engine():
    """Test ChatbotEngine directly."""
    try:
        from api.services.chatbot_engine import ChatbotEngine
        log_debug("✅ ChatbotEngine imported successfully")
        
        engine = ChatbotEngine()
        log_debug("✅ ChatbotEngine instantiated successfully")
        
        # Test message processing
        response = engine.process_message("Hello", "test-session")
        log_debug("✅ Message processed successfully", response)
        
        return True
    except Exception as e:
        log_debug("❌ ChatbotEngine test failed", e)
        return False

def test_chatbot_view():
    """Test ChatbotMessageView."""
    try:
        from api.views import ChatbotMessageView
        from django.test import RequestFactory
        import json
        
        log_debug("✅ ChatbotMessageView imported successfully")
        
        # Create test request
        factory = RequestFactory()
        request = factory.post('/api/chatbot/message/', 
                              data=json.dumps({'message': 'Hello'}),
                              content_type='application/json')
        
        log_debug("✅ Test request created")
        
        # Test view
        view = ChatbotMessageView()
        log_debug("✅ View instantiated")
        
        response = view.post(request)
        log_debug(f"✅ View response: Status {response.status_code}")
        
        return True
    except Exception as e:
        log_debug("❌ ChatbotMessageView test failed", e)
        return False

def test_serializers():
    """Test chatbot serializers."""
    try:
        from api.serializers import ChatbotMessageRequestSerializer
        
        # Test serializer
        data = {'message': 'Hello'}
        serializer = ChatbotMessageRequestSerializer(data=data)
        is_valid = serializer.is_valid()
        
        log_debug(f"✅ Serializer test: Valid={is_valid}, Errors={serializer.errors}")
        
        return is_valid
    except Exception as e:
        log_debug("❌ Serializer test failed", e)
        return False

def test_database_connection():
    """Test database connection."""
    try:
        from api.models import ChatbotIntent
        count = ChatbotIntent.objects.count()
        log_debug(f"✅ Database connection: Found {count} intents")
        return True
    except Exception as e:
        log_debug("❌ Database connection failed", e)
        return False

def main():
    """Run all debug tests."""
    # Clear previous results
    with open("chatbot_debug.txt", "w", encoding="utf-8") as f:
        f.write(f"Chatbot Debug Session - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*60 + "\n\n")
    
    log_debug("Starting chatbot debug session...")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Serializers", test_serializers),
        ("ChatbotEngine", test_chatbot_engine),
        ("ChatbotView", test_chatbot_view),
    ]
    
    results = []
    for test_name, test_func in tests:
        log_debug(f"Running test: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            log_debug(f"Test {test_name} crashed", e)
            results.append((test_name, False))
    
    # Summary
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    summary = f"DEBUG SUMMARY: {passed}/{total} tests passed"
    if passed == total:
        summary += " 🎉 All tests passed - issue might be elsewhere"
    else:
        summary += f" ⚠️ {total - passed} tests failed - found the issue!"
    
    log_debug(summary)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
