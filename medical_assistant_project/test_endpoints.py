#!/usr/bin/env python
"""
Test script to verify chatbot endpoints are working.
"""

import os
import sys
import django
import requests
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
    with open("endpoint_test_results.txt", "a", encoding="utf-8") as f:
        f.write(result)
    
    # Also print to console
    print(result)

def test_health_endpoint():
    """Test health endpoint."""
    try:
        response = requests.get('http://localhost:8000/api/chatbot/health/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            log_result("Health Endpoint", True, f"Status: {response.status_code}", data)
            return True
        else:
            log_result("Health Endpoint", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_result("Health Endpoint", False, str(e))
        return False

def test_quick_actions():
    """Test quick actions endpoint."""
    try:
        response = requests.get('http://localhost:8000/api/chatbot/quick-actions/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            actions = [action.get('title') for action in data.get('quick_actions', [])[:3]]
            log_result("Quick Actions", True, f"Found {count} actions", {
                'count': count,
                'sample_actions': actions
            })
            return True
        else:
            log_result("Quick Actions", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_result("Quick Actions", False, str(e))
        return False

def test_message_processing():
    """Test message processing endpoint."""
    try:
        test_message = "Hello, I want to register a complaint"
        response = requests.post('http://localhost:8000/api/chatbot/message/', 
                               json={'message': test_message},
                               timeout=10)
        if response.status_code == 200:
            data = response.json()
            log_result("Message Processing", True, "Message processed successfully", {
                'input': test_message,
                'intent_detected': data.get('intent_detected'),
                'confidence_score': data.get('confidence_score'),
                'response_type': data.get('response_type'),
                'message_preview': data.get('message', '')[:100] + '...'
            })
            return True
        else:
            log_result("Message Processing", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_result("Message Processing", False, str(e))
        return False

def test_intent_detection():
    """Test intent detection endpoint."""
    try:
        test_message = "I need to check my complaint status"
        response = requests.post('http://localhost:8000/api/chatbot/intent-detect/', 
                               json={'message': test_message},
                               timeout=5)
        if response.status_code == 200:
            data = response.json()
            log_result("Intent Detection", True, "Intent detected successfully", {
                'input': test_message,
                'intent_type': data.get('intent_type'),
                'confidence_score': data.get('confidence_score'),
                'intent_name': data.get('intent_name')
            })
            return True
        else:
            log_result("Intent Detection", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_result("Intent Detection", False, str(e))
        return False

def main():
    """Run all endpoint tests."""
    # Clear previous results
    with open("endpoint_test_results.txt", "w", encoding="utf-8") as f:
        f.write(f"Chatbot Endpoint Test Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*60 + "\n\n")
    
    tests = [
        ("Health Endpoint", test_health_endpoint),
        ("Quick Actions", test_quick_actions),
        ("Message Processing", test_message_processing),
        ("Intent Detection", test_intent_detection),
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
    
    summary = f"\nENDPOINT TEST SUMMARY: {passed}/{total} tests passed"
    if passed == total:
        summary += " 🎉 ALL ENDPOINTS WORKING!"
    else:
        summary += f" ⚠️  {total - passed} endpoints failed"
    
    log_result("FINAL SUMMARY", passed == total, summary)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
