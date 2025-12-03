#!/usr/bin/env python3
"""
Test script for Listing Products in AWS Marketplace Agent
Tests the agent's functionality with sample inputs
"""

import sys
import json
import requests
from typing import Dict, Any

# Backend API endpoint
API_BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test backend health endpoint"""
    print("\n🏥 Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Backend is healthy")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Is it running?")
        print("   Start backend: cd backend && uvicorn main:app --reload")
        return False

def test_validate_credentials():
    """Test credential validation"""
    print("\n🔐 Testing credential validation...")
    
    # Note: These are dummy credentials for testing
    payload = {
        "access_key": "AKIAIOSFODNN7EXAMPLE",
        "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "region": "us-east-1"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/validate-credentials",
            json=payload
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code in [200, 400]  # 400 is expected for invalid creds
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_analyze_product():
    """Test product analysis"""
    print("\n🔍 Testing product analysis...")
    
    payload = {
        "product_name": "CloudWatch Monitoring Tool",
        "product_website": "https://example.com/product",
        "product_description": "Advanced monitoring and observability platform for AWS",
        "documentation_url": "https://example.com/docs"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/analyze-product",
            json=payload
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Analysis: {json.dumps(result, indent=2)[:200]}...")
            return True
        else:
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_chat():
    """Test help agent chat"""
    print("\n💬 Testing help agent chat...")
    
    payload = {
        "message": "How do I create a SaaS product listing?",
        "session_id": "test-session-123"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json=payload
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Response: {result.get('response', '')[:200]}...")
            return True
        else:
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("=" * 80)
    print("  Listing Products in AWS Marketplace - Agent Tests")
    print("=" * 80)
    
    tests = [
        ("Health Check", test_health_check),
        ("Credential Validation", test_validate_credentials),
        ("Product Analysis", test_analyze_product),
        ("Help Agent Chat", test_chat),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("  Test Summary")
    print("=" * 80)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
