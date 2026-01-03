#!/usr/bin/env python3
"""Test script for Bob Voice Assistant API"""

import requests
import json

API_BASE = "http://localhost:8000"

def test_health():
    print("Testing health check...")
    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"✓ Health: {response.json()}")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_create_task():
    print("\nTesting task creation...")
    try:
        task_data = {
            "title": "Test Task",
            "description": "This is a test",
            "priority": "medium"
        }
        response = requests.post(f"{API_BASE}/api/tasks", json=task_data)
        if response.status_code == 201:
            print(f"✓ Task created: {response.json()}")
            return response.json()["id"]
        else:
            print(f"✗ Failed: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def test_get_tasks():
    print("\nTesting get tasks...")
    try:
        response = requests.get(f"{API_BASE}/api/tasks")
        if response.status_code == 200:
            tasks = response.json()
            print(f"✓ Retrieved {len(tasks)} tasks")
            return True
        else:
            print(f"✗ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_weather():
    print("\nTesting weather API...")
    try:
        response = requests.get(f"{API_BASE}/api/weather", params={"location": "London"})
        if response.status_code == 200:
            weather = response.json()
            print(f"✓ Weather: {weather['location']} - {weather['temperature']}°C")
            return True
        else:
            print(f"✗ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_chat():
    print("\nTesting chat API...")
    try:
        chat_data = {"message": "What is 2+2?"}
        response = requests.post(f"{API_BASE}/api/chat", json=chat_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Chat response: {result['response'][:100]}...")
            return True
        else:
            print(f"✗ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Bob Voice Assistant - API Test Suite")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health),
        ("Task Creation", test_create_task),
        ("Get Tasks", test_get_tasks),
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
    print("Results")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{name:.<40} {status}")
    
    print(f"\nTotal: {passed}/{len(results)} passed")