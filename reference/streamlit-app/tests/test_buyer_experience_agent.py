#!/usr/bin/env python3
"""
Test script for BuyerExperienceAgent functionality
Usage: python tests/test_buyer_experience_agent.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.buyer_experience import BuyerExperienceAgent

def test_buyer_experience_agent():
    """Test BuyerExperienceAgent functionality"""
    
    print("=== Testing BuyerExperienceAgent ===")
    
    # Get credentials
    access_key = input("Enter AWS Access Key: ")
    secret_key = input("Enter AWS Secret Key: ")
    session_token = input("Enter Session Token (optional): ") or None
    
    # Create agent
    agent = BuyerExperienceAgent()
    
    print("\n=== Test 1: Simulate Buyer Registration ===")
    result = agent.simulate_buyer_registration(access_key, secret_key, session_token)
    print(f"Result: {result}")
    
    print("\n=== Test 2: Check Registration Status ===")
    result = agent.check_registration_status(access_key, secret_key, session_token)
    print(f"Result: {result}")

if __name__ == "__main__":
    test_buyer_experience_agent()