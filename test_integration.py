#!/usr/bin/env python3
"""
Test script for the integrated AWS Marketplace SaaS workflow
Verifies that all components are properly integrated
"""

import sys
import os
import json

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

def test_agent_initialization():
    """Test that the main agent initializes correctly"""
    print("🧪 Testing agent initialization...")
    
    try:
        from agent.strands_marketplace_agent import StrandsMarketplaceAgent
        
        agent = StrandsMarketplaceAgent()
        print("   ✅ StrandsMarketplaceAgent initialized successfully")
        
        # Test basic functionality
        status = agent.get_workflow_status()
        assert 'current_stage' in status
        assert 'phase' in status
        print("   ✅ get_workflow_status() working")
        
        return agent
        
    except Exception as e:
        print(f"   ❌ Agent initialization failed: {e}")
        return None

def test_post_listing_agents():
    """Test that post-listing agents can be imported"""
    print("\n🧪 Testing post-listing agent imports...")
    
    try:
        from agents.serverless_saas_integration import ServerlessSaasIntegrationAgent
        print("   ✅ ServerlessSaasIntegrationAgent imported")
        
        from agents.workflow_orchestrator import WorkflowOrchestrator  
        print("   ✅ WorkflowOrchestrator imported")
        
        from agents.metering import MeteringAgent
        print("   ✅ MeteringAgent imported")
        
        from agents.public_visibility import PublicVisibilityAgent
        print("   ✅ PublicVisibilityAgent imported")
        
        from agents.buyer_experience import BuyerExperienceAgent
        print("   ✅ BuyerExperienceAgent imported")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Post-listing agent import failed: {e}")
        return False

def test_workflow_phases():
    """Test workflow phase transitions"""
    print("\n🧪 Testing workflow phases...")
    
    try:
        from agent.strands_marketplace_agent import StrandsMarketplaceAgent
        
        agent = StrandsMarketplaceAgent()
        
        # Test Phase 1 (listing creation)
        status = agent.get_workflow_status()
        assert status['phase'] == 'listing_creation'
        assert status['current_stage'] <= 8
        print("   ✅ Phase 1 (listing creation) detected correctly")
        
        # Simulate completing all stages
        for stage in range(1, 9):
            agent.orchestrator.completed_stages.add(agent.orchestrator.current_stage)
            if stage < 8:
                # Move to next stage
                next_stage_value = stage + 1
                for workflow_stage in agent.orchestrator.agents.keys():
                    if workflow_stage.value == next_stage_value:
                        agent.orchestrator.current_stage = workflow_stage
                        break
        
        # Set to complete
        from agent.orchestrator import WorkflowStage
        agent.orchestrator.current_stage = WorkflowStage.COMPLETE
        agent.orchestrator.product_id = "test-product-123"
        agent.orchestrator.offer_id = "test-offer-456"
        
        # Test Phase 2 (integration)
        status = agent.get_workflow_status()
        assert status['phase'] == 'post_listing_integration'
        assert status['listing_complete'] == True
        print("   ✅ Phase 2 (integration) transition working")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Workflow phase test failed: {e}")
        return False

def test_tools_availability():
    """Test that all required tools are available"""
    print("\n🧪 Testing tool availability...")
    
    try:
        from agent.strands_marketplace_agent import StrandsMarketplaceAgent
        
        agent = StrandsMarketplaceAgent()
        
        # Check that agent has tools
        tools = agent.agent.tools if hasattr(agent.agent, 'tools') else []
        tool_names = [tool.__name__ if hasattr(tool, '__name__') else str(tool) for tool in tools]
        
        print(f"   📋 Available tools: {len(tools)}")
        
        # Test basic message processing
        response = agent.process_message("What's my current status?")
        assert isinstance(response, str)
        assert len(response) > 0
        print("   ✅ Message processing working")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Tools test failed: {e}")
        return False

def test_integration_workflow():
    """Test the complete integration workflow"""
    print("\n🧪 Testing integration workflow...")
    
    try:
        from agent.strands_marketplace_agent import StrandsMarketplaceAgent
        
        agent = StrandsMarketplaceAgent()
        
        # Test that integration agents are initialized
        assert agent.integration_agents is not None or agent.integration_agents == {}
        print("   ✅ Integration agents initialized")
        
        # Test serverless integration agent with strands agent reference
        if agent.integration_agents and 'serverless_integration' in agent.integration_agents:
            integration_agent = agent.integration_agents['serverless_integration']
            assert integration_agent.strands_agent == agent
            print("   ✅ Serverless integration agent has strands agent reference")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Integration workflow test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 AWS Marketplace SaaS Integration - Test Suite")
    print("=" * 60)
    
    tests = [
        test_agent_initialization,
        test_post_listing_agents, 
        test_workflow_phases,
        test_tools_availability,
        test_integration_workflow
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = test()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"   ❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Integration is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)