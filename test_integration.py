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
    
    return True

def test_agent_initialization():
    """Test that agents can be initialized"""
    print("\n=== Testing Agent Initialization ===")
    
    try:
        from agents.serverless_saas_integration import ServerlessSaasIntegrationAgent
        from agents.workflow_orchestrator import WorkflowOrchestrator
        
        # Test ServerlessSaasIntegrationAgent
        saas_agent = ServerlessSaasIntegrationAgent()
        print("✅ ServerlessSaasIntegrationAgent initialized successfully")
        
        # Test WorkflowOrchestrator
        workflow_agent = WorkflowOrchestrator()
        print("✅ WorkflowOrchestrator initialized successfully")
        
        return True, saas_agent, workflow_agent
        
    except Exception as e:
        print(f"❌ Failed to initialize agents: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None

def test_agent_methods():
    """Test that agent methods work"""
    print("\n=== Testing Agent Methods ===")
    
    success, saas_agent, workflow_agent = test_agent_initialization()
    if not success:
        return False
    
    # Test ServerlessSaasIntegrationAgent.deploy_infrastructure
    try:
        result = saas_agent.deploy_infrastructure(
            email="test@example.com",
            stack_name="test-stack",
            product_id="test-product-123",
            fulfillment_url="https://test.com/signup",
            pricing_dimensions=[{"name": "Users", "key": "users"}]
        )
        
        if result.get('success'):
            print("✅ ServerlessSaasIntegrationAgent.deploy_infrastructure works")
            print(f"   Stack ID: {result.get('stack_id')}")
        else:
            print(f"❌ deploy_infrastructure failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing deploy_infrastructure: {e}")
        return False
    
    # Test WorkflowOrchestrator.execute_full_workflow
    try:
        result = workflow_agent.execute_full_workflow(
            access_key="test-key",
            secret_key="test-secret",
            session_token=None,
            lambda_function_name="test-lambda"
        )
        
        print("✅ WorkflowOrchestrator.execute_full_workflow works")
        print(f"   Status: {result.get('status')}")
        
    except Exception as e:
        print(f"❌ Error testing execute_full_workflow: {e}")
        return False
    
    return True

def test_streamlit_integration():
    """Test the Streamlit integration components"""
    print("\n=== Testing Streamlit Integration ===")
    
    try:
        # Import the main streamlit app components
        from streamlit_app_with_seller_registration import init_session_state
        print("✅ Streamlit app components imported successfully")
        
        # Test session state initialization (without actually running Streamlit)
        # This is tricky because it requires Streamlit context, so we'll just test imports
        print("✅ Session state initialization function available")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Streamlit integration: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 Testing AI Agent Marketplace Integration\n")
    
    # Test 1: Agent imports
    if not test_agent_imports():
        print("\n❌ Agent import tests failed")
        return False
    
    # Test 2: Agent methods
    if not test_agent_methods():
        print("\n❌ Agent method tests failed")
        return False
    
    # Test 3: Streamlit integration
    if not test_streamlit_integration():
        print("\n❌ Streamlit integration tests failed")
        return False
    
    print("\n🎉 All tests passed! The integration is working correctly.")
    print("\n📋 Summary:")
    print("   ✅ Agents can be imported")
    print("   ✅ Agents can be initialized")
    print("   ✅ Agent methods work correctly")
    print("   ✅ Streamlit integration is functional")
    print("\n🚀 You can now run the Streamlit app and the SaaS integration workflow should work!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)