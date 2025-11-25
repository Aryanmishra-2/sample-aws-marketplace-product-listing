#!/usr/bin/env python3
"""
Test script for MeteringAgent functionality
Usage: python tests/test_metering_agent.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.metering import MeteringAgent

def test_metering_agent():
    """Test MeteringAgent functionality"""
    
    print("=== Testing MeteringAgent ===")
    
    # Get credentials
    access_key = input("Enter AWS Access Key: ")
    secret_key = input("Enter AWS Secret Key: ")
    session_token = input("Enter Session Token (optional): ") or None
    
    # Create agent
    agent = MeteringAgent()
    
    print("\n=== Test 1: Insert Test Customer ===")
    result = agent.insert_test_customer(access_key, secret_key, session_token)
    print(f"Result: {result}")
    
    print("\n=== Test 2: Create Metering Records ===")
    result = agent.create_metering_records(access_key, secret_key, session_token)
    print(f"Result: {result}")
    
    print("\n=== Test 3: Check Metering Status ===")
    result = agent.check_metering_status(access_key, secret_key, session_token)
    print(f"Result: {result}")

if __name__ == "__main__":
    test_metering_agent()