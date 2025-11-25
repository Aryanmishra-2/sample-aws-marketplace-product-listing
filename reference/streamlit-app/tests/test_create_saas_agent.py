#!/usr/bin/env python3
"""
Test script for CreateSaasAgent functionality
Usage: python tests/test_create_saas_agent.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.create_saas import CreateSaasAgent

def test_create_saas_agent():
    """Test CreateSaasAgent functionality"""
    
    print("=== Testing CreateSaasAgent ===")
    
    # Create agent
    agent = CreateSaasAgent()
    
    print("\n=== Test 1: Get Product Configuration ===")
    product_id = agent.get_product_id()
    pricing_model = agent.get_pricing_model_dimension()
    email = agent.get_email_dimension()
    
    print(f"Product ID: {product_id}")
    print(f"Pricing Model: {pricing_model}")
    print(f"Email: {email}")
    
    print("\n=== Test 2: Validate Configuration ===")
    if product_id and pricing_model and email:
        print("✓ All configuration values are set")
    else:
        print("✗ Some configuration values are missing")
    
    print("\n=== Test 3: Configuration Details ===")
    print(f"Product ID valid format: {'✓' if product_id.startswith('prod-') else '✗'}")
    print(f"Email valid format: {'✓' if '@' in email else '✗'}")
    print(f"Pricing model: {pricing_model}")

if __name__ == "__main__":
    test_create_saas_agent()