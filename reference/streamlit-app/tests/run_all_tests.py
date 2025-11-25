#!/usr/bin/env python3
"""
Master test runner for all agents
Usage: python tests/run_all_tests.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    """Run all available tests"""
    
    print("=== AWS Marketplace SaaS Integration Test Suite ===")
    print()
    
    tests = {
        "1": ("Fulfillment URL Update", "test_fulfillment_url_update"),
        "2": ("MeteringAgent", "test_metering_agent"),
        "3": ("PublicVisibilityAgent", "test_public_visibility_agent"),
        "4": ("BuyerExperienceAgent", "test_buyer_experience_agent"),
        "5": ("WorkflowOrchestrator", "test_workflow_orchestrator"),
        "6": ("All Tests", "all")
    }
    
    print("Available Tests:")
    for key, (name, _) in tests.items():
        print(f"  {key}. {name}")
    
    choice = input("\nSelect test to run (1-6): ").strip()
    
    if choice in tests:
        name, module = tests[choice]
        
        if module == "all":
            print("\n=== Running All Tests ===")
            for test_key, (test_name, test_module) in tests.items():
                if test_module != "all":
                    print(f"\n--- Running {test_name} ---")
                    try:
                        exec(f"from {test_module} import *")
                        exec(f"{test_module.replace('test_', 'test_').replace('_agent', '_agent')}()")
                    except Exception as e:
                        print(f"Error running {test_name}: {e}")
        else:
            print(f"\n=== Running {name} Test ===")
            try:
                exec(f"from {module} import *")
                if module == "test_fulfillment_url_update":
                    from test_fulfillment_url_update import test_fulfillment_url_update
                    test_fulfillment_url_update()
                elif module == "test_metering_agent":
                    from test_metering_agent import test_metering_agent
                    test_metering_agent()
                elif module == "test_public_visibility_agent":
                    from test_public_visibility_agent import test_public_visibility_agent
                    test_public_visibility_agent()
                elif module == "test_buyer_experience_agent":
                    from test_buyer_experience_agent import test_buyer_experience_agent
                    test_buyer_experience_agent()
                elif module == "test_workflow_orchestrator":
                    from test_workflow_orchestrator import test_workflow_orchestrator
                    test_workflow_orchestrator()
            except Exception as e:
                print(f"Error running test: {e}")
    else:
        print("Invalid choice. Please select 1-6.")

if __name__ == "__main__":
    main()