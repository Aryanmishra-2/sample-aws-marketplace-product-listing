#!/usr/bin/env python3
"""
Test script for WorkflowOrchestrator functionality
Usage: python tests/test_workflow_orchestrator.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.workflow_orchestrator import WorkflowOrchestrator

def test_workflow_orchestrator():
    """Test WorkflowOrchestrator functionality"""
    
    print("=== Testing WorkflowOrchestrator ===")
    
    # Get credentials
    access_key = input("Enter AWS Access Key: ")
    secret_key = input("Enter AWS Secret Key: ")
    session_token = input("Enter Session Token (optional): ") or None
    lambda_function = input("Enter Lambda Function Name (optional): ") or None
    
    # Create orchestrator
    orchestrator = WorkflowOrchestrator()
    
    print("\n=== Test 1: Validate Credentials ===")
    result = orchestrator.validate_credentials(access_key, secret_key, session_token)
    print(f"Result: {result}")
    
    print("\n=== Test 2: Execute Full Workflow ===")
    print("Note: This will execute the complete metering and visibility workflow")
    proceed = input("Do you want to proceed? (y/n): ").strip().lower()
    
    if proceed == 'y':
        result = orchestrator.execute_full_workflow(access_key, secret_key, session_token, lambda_function)
        print(f"Result: {result}")
    else:
        print("Skipped full workflow execution")

if __name__ == "__main__":
    test_workflow_orchestrator()