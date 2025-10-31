#!/usr/bin/env python3
"""
Test script for PublicVisibilityAgent functionality
Usage: python tests/test_public_visibility_agent.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.public_visibility import PublicVisibilityAgent

def test_public_visibility_agent():
    """Test PublicVisibilityAgent functionality"""
    
    print("=== Testing PublicVisibilityAgent ===")
    
    # Get credentials
    access_key = input("Enter AWS Access Key: ")
    secret_key = input("Enter AWS Secret Key: ")
    session_token = input("Enter Session Token (optional): ") or None
    
    # Create agent
    agent = PublicVisibilityAgent()
    
    print("\n=== Test 1: Check Metering Prerequisites ===")
    result = agent.check_metering_prerequisites(access_key, secret_key, session_token)
    print(f"Result: {result}")
    
    print("\n=== Test 2: Submit Public Visibility Request ===")
    result = agent.submit_public_visibility_request(access_key, secret_key, session_token)
    print(f"Result: {result}")

if __name__ == "__main__":
    test_public_visibility_agent()