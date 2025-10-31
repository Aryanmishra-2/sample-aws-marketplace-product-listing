#!/usr/bin/env python3
"""
Test script for automated fulfillment URL update functionality
Usage: python tests/test_fulfillment_url_update.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.serverless_saas_integration import ServerlessSaasIntegrationAgent

def test_fulfillment_url_update():
    """Test the automated fulfillment URL update process"""
    
    print("=== Testing Automated Fulfillment URL Update ===")
    
    # Get credentials from user
    access_key = input("Enter AWS Access Key: ")
    secret_key = input("Enter AWS Secret Key: ")
    session_token = input("Enter Session Token (optional): ") or None
    
    # Test parameters
    product_id = input("Enter Product ID (default: prod-dpihhj5madfda): ") or "prod-dpihhj5madfda"
    fulfillment_url = input("Enter Test Fulfillment URL (default: https://example.com/test): ") or "https://example.com/test"
    
    print(f"\nTesting with:")
    print(f"Product ID: {product_id}")
    print(f"Fulfillment URL: {fulfillment_url}")
    
    # Create agent and test
    agent = ServerlessSaasIntegrationAgent()
    
    print("\n=== Starting Test ===")
    result = agent._update_fulfillment_url_api(access_key, secret_key, session_token, product_id, fulfillment_url)
    
    print("\n=== Test Results ===")
    if result.get('success'):
        print("✓ SUCCESS: Fulfillment URL update request submitted")
        print(f"ChangeSet ID: {result.get('changeset_id')}")
    else:
        print("✗ FAILED: Could not update fulfillment URL")
        print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    test_fulfillment_url_update()