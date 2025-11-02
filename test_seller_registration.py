#!/usr/bin/env python3
"""
Test script for Seller Registration Agent and Tools

This script tests the seller registration functionality to ensure
everything is working correctly.
"""

import sys
import json
from typing import Dict, Any

# Add the current directory to Python path
sys.path.append('.')

from agent.tools.seller_registration_tools import SellerRegistrationTools
from agent.sub_agents.seller_registration_agent import SellerRegistrationAgent


def test_seller_registration_tools():
    """Test the SellerRegistrationTools class"""
    print("🧪 Testing SellerRegistrationTools...")
    print("=" * 50)
    
    try:
        # Initialize tools
        tools = SellerRegistrationTools()
        print("✅ SellerRegistrationTools initialized successfully")
        
        # Test 1: Get account info
        print("\n📋 Test 1: Get Account Info")
        account_info = tools.get_account_info()
        print(f"Result: {json.dumps(account_info, indent=2)}")
        
        # Test 2: Check seller status
        print("\n📋 Test 2: Check Seller Status")
        status = tools.check_seller_status()
        print(f"Result: {json.dumps(status, indent=2)}")
        
        # Test 3: Get registration requirements
        print("\n📋 Test 3: Get Registration Requirements")
        requirements = tools.get_registration_requirements()
        print(f"Workflow steps: {len(requirements['workflow_steps'])} steps")
        for step_key, step_info in requirements['workflow_steps'].items():
            print(f"  - {step_info['title']}: {step_info['estimated_time']}")
        
        # Test 4: Get workflow status
        print("\n📋 Test 4: Get Workflow Status")
        workflow_status = tools.get_registration_workflow_status()
        print(f"Current step: {workflow_status.get('current_step')}")
        print(f"Progress: {workflow_status.get('progress_percentage', 0)}%")
        
        # Test 5: Initiate registration process
        print("\n📋 Test 5: Initiate Registration Process")
        initiation = tools.initiate_registration_process()
        print(f"Status: {initiation.get('status')}")
        print(f"Message: {initiation.get('message')}")
        
        # Test 6: Validate business info
        print("\n📋 Test 6: Validate Business Info")
        test_business_info = {
            "business_name": "Test Company Pvt Ltd",
            "business_type": "Private Limited Company",
            "business_address": "123 Test Street, Mumbai, Maharashtra 400001",
            "business_phone": "+91-9876543210",
            "business_email": "test@testcompany.com",
            "tax_id": "ABCDE1234F",
            "primary_contact_name": "John Doe",
            "primary_contact_email": "john@testcompany.com",
            "primary_contact_phone": "+91-9876543210"
        }
        
        validation = tools.validate_business_info(test_business_info)
        print(f"Validation success: {validation['success']}")
        if validation.get('errors'):
            print(f"Errors: {validation['errors']}")
        if validation.get('warnings'):
            print(f"Warnings: {validation['warnings']}")
        
        # Test 7: India-specific requirements
        print("\n📋 Test 7: India-Specific Requirements")
        india_req = tools.get_india_specific_requirements()
        print(f"Country: {india_req['country']}")
        print(f"Mandatory documents: {len(india_req['business_requirements']['mandatory_documents'])}")
        
        # Test 8: Validate India business info
        print("\n📋 Test 8: Validate India Business Info")
        india_business_info = {
            "business_name": "Test India Pvt Ltd",
            "business_type": "Private Limited Company",
            "business_address": "123 Test Street, Mumbai, Maharashtra 400001",
            "business_phone": "9876543210",
            "business_email": "test@testindia.com",
            "pan_number": "ABCDE1234F",
            "gst_number": "27ABCDE1234F1Z5",
            "primary_contact_name": "Raj Sharma",
            "primary_contact_email": "raj@testindia.com",
            "primary_contact_phone": "9876543210"
        }
        
        india_validation = tools.validate_india_business_info(india_business_info)
        print(f"India validation success: {india_validation['success']}")
        if india_validation.get('errors'):
            print(f"Errors: {india_validation['errors']}")
        if india_validation.get('warnings'):
            print(f"Warnings: {india_validation['warnings']}")
        
        # Test 9: Get help resources
        print("\n📋 Test 9: Get Help Resources")
        help_resources = tools.get_help_resources()
        print(f"Documentation links: {len(help_resources['official_documentation'])}")
        print(f"Support channels: {len(help_resources['support_channels'])}")
        print(f"India-specific resources: {len(help_resources['india_specific_resources'])}")
        
        print("\n✅ All SellerRegistrationTools tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ SellerRegistrationTools test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_seller_registration_agent():
    """Test the SellerRegistrationAgent class"""
    print("\n🧪 Testing SellerRegistrationAgent...")
    print("=" * 50)
    
    try:
        # Initialize agent
        agent = SellerRegistrationAgent()
        print("✅ SellerRegistrationAgent initialized successfully")
        
        # Test 1: Get required fields
        print("\n📋 Test 1: Get Required Fields")
        required_fields = agent.get_required_fields()
        print(f"Required fields ({len(required_fields)}): {required_fields}")
        
        # Test 2: Get optional fields
        print("\n📋 Test 2: Get Optional Fields")
        optional_fields = agent.get_optional_fields()
        print(f"Optional fields ({len(optional_fields)}): {optional_fields}")
        
        # Test 3: Get field validations
        print("\n📋 Test 3: Get Field Validations")
        validations = agent.get_field_validations()
        print(f"Validation rules for {len(validations)} fields")
        
        # Test 4: Get stage instructions
        print("\n📋 Test 4: Get Stage Instructions")
        instructions = agent.get_stage_instructions()
        print(f"Instructions length: {len(instructions)} characters")
        print(f"Instructions preview: {instructions[:200]}...")
        
        # Test 5: Check if stage is complete (should be False initially)
        print("\n📋 Test 5: Check Stage Completion")
        is_complete = agent.is_stage_complete()
        print(f"Stage complete: {is_complete}")
        
        # Test 6: Process stage with user input
        print("\n📋 Test 6: Process Stage with User Input")
        user_input = """
        I want to register my company for AWS Marketplace.
        Business name: Tech Solutions India Pvt Ltd
        Business type: Private Limited Company
        Business email: contact@techsolutions.in
        """
        
        context = {"conversation_history": []}
        result = agent.process_stage(user_input, context)
        print(f"Process result status: {result.get('status')}")
        print(f"Message: {result.get('message', '')[:200]}...")
        
        # Test 7: Get registration requirements
        print("\n📋 Test 7: Get Registration Requirements")
        requirements = agent.get_registration_requirements()
        print(f"Requirements available: {requirements.get('success', False)}")
        
        # Test 8: Check seller status
        print("\n📋 Test 8: Check Seller Status")
        status = agent.check_seller_status()
        print(f"Status check success: {status.get('success', False)}")
        print(f"Seller status: {status.get('seller_status', 'Unknown')}")
        
        # Test 9: Get help resources
        print("\n📋 Test 9: Get Help Resources")
        help_resources = agent.get_help_resources()
        print(f"Help resources available: {help_resources.get('success', False) if isinstance(help_resources, dict) else True}")
        
        print("\n✅ All SellerRegistrationAgent tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ SellerRegistrationAgent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test integration between tools and agent"""
    print("\n🧪 Testing Integration...")
    print("=" * 50)
    
    try:
        # Test that agent uses tools correctly
        agent = SellerRegistrationAgent()
        tools = agent.seller_tools
        
        # Verify tools are properly initialized
        assert tools is not None, "Agent should have seller_tools initialized"
        assert hasattr(tools, 'check_seller_status'), "Tools should have check_seller_status method"
        assert hasattr(tools, 'get_registration_requirements'), "Tools should have get_registration_requirements method"
        
        # Test that agent methods delegate to tools
        agent_status = agent.check_seller_status()
        tools_status = tools.check_seller_status()
        
        # Both should return similar structure
        assert isinstance(agent_status, dict), "Agent status should return dict"
        assert isinstance(tools_status, dict), "Tools status should return dict"
        
        print("✅ Integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("🚀 Starting Seller Registration Tests")
    print("=" * 60)
    
    results = []
    
    # Test 1: SellerRegistrationTools
    results.append(test_seller_registration_tools())
    
    # Test 2: SellerRegistrationAgent
    results.append(test_seller_registration_agent())
    
    # Test 3: Integration
    results.append(test_integration())
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Seller registration system is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)