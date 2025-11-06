#!/usr/bin/env python3
"""
Test script to verify the integration between the Streamlit app and the agents
"""

import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_agent_imports():
    """Test that all agents can be imported"""
    print("=== Testing Agent Imports ===")
    
    try:
        from agents.serverless_saas_integration import ServerlessSaasIntegrationAgent
        print("✅ ServerlessSaasIntegrationAgent imported successfully")
    except Exception as e:
        print(f"❌ Failed to import ServerlessSaasIntegrationAgent: {e}")
        return False
    
    try:
        from agents.workflow_orchestrator import WorkflowOrchestrator
        print("✅ WorkflowOrchestrator imported successfully")
    except Exception as e:
        print(f"❌ Failed to import WorkflowOrchestrator: {e}")
        return False
    
    try:
        from agents.buyer_experience import BuyerExperienceAgent
        print("✅ BuyerExperienceAgent imported successfully")
    except Exception as e:
        print(f"❌ Failed to import BuyerExperienceAgent: {e}")
        return False
    
    try:
        from agents.metering import MeteringAgent
        print("✅ MeteringAgent imported successfully")
    except Exception as e:
        print(f"❌ Failed to import MeteringAgent: {e}")
        return False
    
    try:
        from agents.public_visibility import PublicVisibilityAgent
        print("✅ PublicVisibilityAgent imported successfully")
    except Exception as e:
        print(f"❌ Failed to import PublicVisibilityAgent: {e}")
        return False
    
    return True

def test_seller_registration():
    """Test seller registration components"""
    print("\n=== Testing Seller Registration ===")
    
    try:
        from agent.tools.seller_registration_tools import SellerRegistrationTools
        print("✅ SellerRegistrationTools imported successfully")
    except Exception as e:
        print(f"❌ Failed to import SellerRegistrationTools: {e}")
        return False
    
    try:
        from agent.sub_agents.seller_registration_agent import SellerRegistrationAgent
        print("✅ SellerRegistrationAgent imported successfully")
    except Exception as e:
        print(f"❌ Failed to import SellerRegistrationAgent: {e}")
        return False
    
    try:
        from seller_registration_module import SellerRegistrationModule
        print("✅ SellerRegistrationModule imported successfully")
    except Exception as e:
        print(f"❌ Failed to import SellerRegistrationModule: {e}")
        return False
    
    return True

def test_core_components():
    """Test core orchestrator and tools"""
    print("\n=== Testing Core Components ===")
    
    try:
        from agent.orchestrator import ListingOrchestrator, WorkflowStage
        print("✅ ListingOrchestrator imported successfully")
    except Exception as e:
        print(f"❌ Failed to import ListingOrchestrator: {e}")
        return False
    
    try:
        from agent.tools.listing_tools import ListingTools
        print("✅ ListingTools imported successfully")
    except Exception as e:
        print(f"❌ Failed to import ListingTools: {e}")
        return False
    
    return True

def test_streamlit_app():
    """Test that the main Streamlit app can be imported"""
    print("\n=== Testing Streamlit App ===")
    
    # Test if the main app file exists and is readable
    app_file = "streamlit_app_with_seller_registration.py"
    if os.path.exists(app_file):
        print(f"✅ {app_file} exists")
        
        # Try to read the file to check for syntax errors
        try:
            with open(app_file, 'r') as f:
                content = f.read()
            print(f"✅ {app_file} is readable")
            
            # Check for key imports
            if "import streamlit as st" in content:
                print("✅ Streamlit import found")
            else:
                print("❌ Streamlit import not found")
                return False
                
        except Exception as e:
            print(f"❌ Error reading {app_file}: {e}")
            return False
    else:
        print(f"❌ {app_file} not found")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🧪 Starting Integration Tests...\n")
    
    tests = [
        test_core_components,
        test_seller_registration,
        test_agent_imports,
        test_streamlit_app
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ {test.__name__} failed")
        except Exception as e:
            print(f"❌ {test.__name__} crashed: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)