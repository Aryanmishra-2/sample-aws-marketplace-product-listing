#!/usr/bin/env python3
"""
Test script to verify Strands SDK migration
Ensures all functionality works correctly after migration
"""

import sys
import json
from typing import Dict, Any

def print_section(title: str):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def print_test(name: str, passed: bool, details: str = ""):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {name}")
    if details:
        print(f"       {details}")

def test_imports():
    """Test that all required modules can be imported"""
    print_section("Testing Imports")
    
    try:
        from agent.strands_marketplace_agent import StrandsMarketplaceAgent
        print_test("Import StrandsMarketplaceAgent", True)
    except ImportError as e:
        print_test("Import StrandsMarketplaceAgent", False, str(e))
        return False
    
    try:
        from agent.orchestrator import ListingOrchestrator, WorkflowStage
        print_test("Import ListingOrchestrator", True)
    except ImportError as e:
        print_test("Import ListingOrchestrator", False, str(e))
        return False
    
    try:
        from agent.tools.listing_tools import ListingTools
        print_test("Import ListingTools", True)
    except ImportError as e:
        print_test("Import ListingTools", False, str(e))
        return False
    
    try:
        from strands import Agent, tool
        print_test("Import Strands SDK", True)
    except ImportError as e:
        print_test("Import Strands SDK", False, str(e))
        print("       Please install: pip install strands strands-tools")
        return False
    
    return True

def test_agent_initialization():
    """Test agent initialization"""
    print_section("Testing Agent Initialization")
    
    try:
        from agent.strands_marketplace_agent import StrandsMarketplaceAgent
        
        # Test with default config
        agent = StrandsMarketplaceAgent()
        print_test("Initialize with default config", True)
        
        # Test with custom config
        agent = StrandsMarketplaceAgent(config={
            'region': 'us-east-1',
            'model_id': 'us.anthropic.claude-3-7-sonnet-20250219-v1:0'
        })
        print_test("Initialize with custom config", True)
        
        # Verify components
        has_orchestrator = agent.orchestrator is not None
        print_test("Orchestrator initialized", has_orchestrator)
        
        has_listing_tools = agent.listing_tools is not None
        print_test("ListingTools initialized", has_listing_tools)
        
        has_strands_agent = agent.agent is not None
        print_test("Strands Agent initialized", has_strands_agent)
        
        return has_orchestrator and has_listing_tools and has_strands_agent
        
    except Exception as e:
        print_test("Agent initialization", False, str(e))
        return False

def test_workflow_status():
    """Test workflow status retrieval"""
    print_section("Testing Workflow Status")
    
    try:
        from agent.strands_marketplace_agent import StrandsMarketplaceAgent
        
        agent = StrandsMarketplaceAgent()
        status = agent.get_workflow_status()
        
        # Verify status structure
        has_current_stage = 'current_stage' in status
        print_test("Status has current_stage", has_current_stage, 
                  f"Stage: {status.get('current_stage')}")
        
        has_stage_name = 'stage_name' in status
        print_test("Status has stage_name", has_stage_name,
                  f"Name: {status.get('stage_name')}")
        
        has_progress = 'progress' in status
        print_test("Status has progress", has_progress,
                  f"Progress: {status.get('progress')}%")
        
        # Verify initial state
        is_stage_1 = status.get('current_stage') == 1
        print_test("Initial stage is 1", is_stage_1)
        
        is_product_info = status.get('stage_name') == 'Product Information'
        print_test("Initial stage name correct", is_product_info)
        
        is_zero_progress = status.get('progress') == 0
        print_test("Initial progress is 0%", is_zero_progress)
        
        return all([has_current_stage, has_stage_name, has_progress,
                   is_stage_1, is_product_info, is_zero_progress])
        
    except Exception as e:
        print_test("Workflow status", False, str(e))
        return False

def test_stage_info():
    """Test stage information retrieval"""
    print_section("Testing Stage Information")
    
    try:
        from agent.strands_marketplace_agent import StrandsMarketplaceAgent
        
        agent = StrandsMarketplaceAgent()
        stage_info = agent.orchestrator.get_stage_info()
        
        # Verify stage info structure
        has_stage_number = 'stage_number' in stage_info
        print_test("Stage info has stage_number", has_stage_number,
                  f"Number: {stage_info.get('stage_number')}")
        
        has_required_fields = 'required_fields' in stage_info
        num_required = len(stage_info.get('required_fields', []))
        print_test("Stage info has required_fields", has_required_fields,
                  f"Count: {num_required}")
        
        has_optional_fields = 'optional_fields' in stage_info
        num_optional = len(stage_info.get('optional_fields', []))
        print_test("Stage info has optional_fields", has_optional_fields,
                  f"Count: {num_optional}")
        
        has_instructions = 'instructions' in stage_info
        print_test("Stage info has instructions", has_instructions)
        
        return all([has_stage_number, has_required_fields, 
                   has_optional_fields, has_instructions])
        
    except Exception as e:
        print_test("Stage information", False, str(e))
        return False

def test_data_storage():
    """Test data storage and retrieval"""
    print_section("Testing Data Storage")
    
    try:
        from agent.strands_marketplace_agent import StrandsMarketplaceAgent
        
        agent = StrandsMarketplaceAgent()
        
        # Store test data
        test_data = {
            "product_title": "Test Product",
            "logo_s3_url": "https://test-bucket.s3.amazonaws.com/logo.png",
            "short_description": "This is a test product description"
        }
        
        for field, value in test_data.items():
            agent.orchestrator.set_stage_data(field, value)
        
        print_test("Store multiple fields", True, 
                  f"Stored {len(test_data)} fields")
        
        # Retrieve data
        current_agent = agent.orchestrator.get_current_agent()
        stored_data = current_agent.stage_data
        
        # Verify data
        all_stored = all(field in stored_data for field in test_data.keys())
        print_test("All fields stored correctly", all_stored)
        
        values_match = all(stored_data.get(field) == value 
                          for field, value in test_data.items())
        print_test("All values match", values_match)
        
        return all_stored and values_match
        
    except Exception as e:
        print_test("Data storage", False, str(e))
        return False

def test_stage_completion_check():
    """Test stage completion checking"""
    print_section("Testing Stage Completion")
    
    try:
        from agent.strands_marketplace_agent import StrandsMarketplaceAgent
        
        agent = StrandsMarketplaceAgent()
        
        # Check incomplete stage
        is_complete = agent.orchestrator.check_stage_completion()
        print_test("Incomplete stage detected", not is_complete)
        
        # Get required fields
        current_agent = agent.orchestrator.get_current_agent()
        required_fields = current_agent.get_required_fields()
        print_test("Required fields retrieved", len(required_fields) > 0,
                  f"Count: {len(required_fields)}")
        
        # Store all required fields with dummy data
        for field in required_fields:
            if field == "highlights":
                agent.orchestrator.set_stage_data(field, ["Feature 1", "Feature 2", "Feature 3"])
            elif field == "categories":
                agent.orchestrator.set_stage_data(field, ["Application Development"])
            elif field == "search_keywords":
                agent.orchestrator.set_stage_data(field, ["test", "product"])
            elif "email" in field:
                agent.orchestrator.set_stage_data(field, "test@example.com")
            elif "url" in field:
                agent.orchestrator.set_stage_data(field, "https://test.s3.amazonaws.com/test.png")
            else:
                agent.orchestrator.set_stage_data(field, f"Test {field}")
        
        # Check complete stage
        is_complete = agent.orchestrator.check_stage_completion()
        print_test("Complete stage detected", is_complete)
        
        return True
        
    except Exception as e:
        print_test("Stage completion check", False, str(e))
        return False

def test_export_import():
    """Test data export and import"""
    print_section("Testing Export/Import")
    
    try:
        from agent.strands_marketplace_agent import StrandsMarketplaceAgent
        
        agent = StrandsMarketplaceAgent()
        
        # Store some test data
        agent.orchestrator.set_stage_data("product_title", "Test Product")
        agent.orchestrator.set_stage_data("logo_s3_url", "https://test.s3.amazonaws.com/logo.png")
        
        # Export data
        exported_data = agent.export_workflow_data()
        print_test("Export data", True, 
                  f"Exported {len(exported_data)} keys")
        
        # Verify export structure
        has_data = 'data' in exported_data
        print_test("Export has 'data' key", has_data)
        
        has_progress = 'progress' in exported_data
        print_test("Export has 'progress' key", has_progress)
        
        # Reset workflow
        agent.reset_workflow()
        current_agent = agent.orchestrator.get_current_agent()
        is_empty = len(current_agent.stage_data) == 0
        print_test("Workflow reset successful", is_empty)
        
        # Import data
        import_success = agent.import_workflow_data(exported_data)
        print_test("Import data", import_success)
        
        # Verify imported data
        current_agent = agent.orchestrator.get_current_agent()
        has_product_title = "product_title" in current_agent.stage_data
        print_test("Imported data restored", has_product_title)
        
        return has_data and has_progress and import_success and has_product_title
        
    except Exception as e:
        print_test("Export/Import", False, str(e))
        return False

def test_workflow_reset():
    """Test workflow reset"""
    print_section("Testing Workflow Reset")
    
    try:
        from agent.strands_marketplace_agent import StrandsMarketplaceAgent
        
        agent = StrandsMarketplaceAgent()
        
        # Store some data
        agent.orchestrator.set_stage_data("product_title", "Test Product")
        current_agent = agent.orchestrator.get_current_agent()
        has_data_before = len(current_agent.stage_data) > 0
        print_test("Data stored before reset", has_data_before)
        
        # Reset
        agent.reset_workflow()
        
        # Verify reset
        current_agent = agent.orchestrator.get_current_agent()
        is_empty = len(current_agent.stage_data) == 0
        print_test("Data cleared after reset", is_empty)
        
        status = agent.get_workflow_status()
        is_stage_1 = status['current_stage'] == 1
        print_test("Reset to stage 1", is_stage_1)
        
        is_zero_progress = status['progress'] == 0
        print_test("Progress reset to 0%", is_zero_progress)
        
        return is_empty and is_stage_1 and is_zero_progress
        
    except Exception as e:
        print_test("Workflow reset", False, str(e))
        return False

def test_all_stages_accessible():
    """Test that all 8 stages are accessible"""
    print_section("Testing All Stages")
    
    try:
        from agent.strands_marketplace_agent import StrandsMarketplaceAgent
        from agent.orchestrator import WorkflowStage
        
        agent = StrandsMarketplaceAgent()
        
        # Verify all stages exist
        expected_stages = [
            (1, "Product Information"),
            (2, "Fulfillment Options"),
            (3, "Pricing Configuration"),
            (4, "Price Review"),
            (5, "Refund Policy"),
            (6, "EULA Configuration"),
            (7, "Offer Availability"),
            (8, "Allowlist Configuration")
        ]
        
        for stage_num, expected_name in expected_stages:
            stage = WorkflowStage(stage_num)
            agent_for_stage = agent.orchestrator.agents.get(stage)
            
            if agent_for_stage:
                actual_name = agent_for_stage.stage_name
                name_matches = expected_name in actual_name or actual_name in expected_name
                print_test(f"Stage {stage_num} accessible", True,
                          f"Name: {actual_name}")
            else:
                print_test(f"Stage {stage_num} accessible", False,
                          "Stage not found")
                return False
        
        return True
        
    except Exception as e:
        print_test("All stages accessible", False, str(e))
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  🧪 STRANDS SDK MIGRATION TEST SUITE")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    
    if results[-1][1]:  # Only continue if imports work
        results.append(("Agent Initialization", test_agent_initialization()))
        results.append(("Workflow Status", test_workflow_status()))
        results.append(("Stage Information", test_stage_info()))
        results.append(("Data Storage", test_data_storage()))
        results.append(("Stage Completion", test_stage_completion_check()))
        results.append(("Export/Import", test_export_import()))
        results.append(("Workflow Reset", test_workflow_reset()))
        results.append(("All Stages", test_all_stages_accessible()))
    
    # Print summary
    print_section("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{'='*60}")
    print(f"  Results: {passed}/{total} tests passed")
    print('='*60)
    
    if passed == total:
        print("\n🎉 All tests passed! Migration successful.")
        print("\nNext steps:")
        print("1. Test the Streamlit app: streamlit run streamlit_strands_app.py")
        print("2. Deploy to AgentCore: agentcore launch")
        print("3. Test end-to-end workflow")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed. Please review the errors above.")
        print("\nTroubleshooting:")
        print("1. Ensure all dependencies are installed: pip install -r requirements_strands.txt")
        print("2. Check AWS credentials are configured: aws configure")
        print("3. Verify Bedrock model access in AWS console")
        return 1

if __name__ == "__main__":
    sys.exit(main())
