#!/usr/bin/env python3
"""
Simple test script to verify backend API is working correctly
Run this after starting the backend server
"""

import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000"

def test_health_check():
    """Test if API is running"""
    print("Testing health check...")
    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"✓ Health check passed: {response.json()}")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_create_task():
    """Test creating a task"""
    print("\nTesting task creation...")
    try:
        task_data = {
            "title": "Test Task",
            "description": "This is a test task",
            "priority": "medium"
        }
        response = requests.post(f"{API_BASE}/api/tasks", json=task_data)
        if response.status_code == 201:
            print(f"✓ Task created: {response.json()}")
            return response.json()["id"]
        else:
            print(f"✗ Task creation failed: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Task creation failed: {e}")
        return None

def test_get_tasks():
    """Test retrieving tasks"""
    print("\nTesting task retrieval...")
    try:
        response = requests.get(f"{API_BASE}/api/tasks")
        if response.status_code == 200:
            tasks = response.json()
            print(f"✓ Retrieved {len(tasks)} tasks")
            return True
        else:
            print(f"✗ Task retrieval failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Task retrieval failed: {e}")
        return False

def test_weather():
    """Test weather API"""
    print("\nTesting weather API...")
    try:
        response = requests.get(f"{API_BASE}/api/weather", params={"location": "London"})
        if response.status_code == 200:
            weather = response.json()
            print(f"✓ Weather retrieved: {weather['location']} - {weather['temperature']}°C")
            return True
        else:
            print(f"✗ Weather retrieval failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Weather retrieval failed: {e}")
        return False

def test_chat():
    """Test chat API"""
    print("\nTesting chat API...")
    try:
        chat_data = {
            "message": "What is 2+2?"
        }
        response = requests.post(f"{API_BASE}/api/chat", json=chat_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Chat response: {result['response'][:100]}...")
            return True
        else:
            print(f"✗ Chat failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Chat failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Voice AI Assistant - Backend API Test Suite")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health_check),
        ("Task Creation", test_create_task),
        ("Task Retrieval", test_get_tasks),
        ("Weather API", test_weather),
        ("Chat API", test_chat),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            if name == "Task Creation":
                result = test_func() is not None
            else:
                result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} crashed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{name:.<40} {status}")
    
    print("=" * 60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Backend is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the logs above.")

if __name__ == "__main__":
    main()
