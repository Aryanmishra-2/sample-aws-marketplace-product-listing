#!/usr/bin/env python3
"""
AWS Marketplace SaaS Integration - Complete Workflow Demo
Demonstrates the integrated workflow from limited listing creation to AWS deployment
"""

import sys
import os
import json

# Add agent paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

from agent.strands_marketplace_agent import StrandsMarketplaceAgent

def main():
    print("🚀 AWS Marketplace SaaS Integration - Complete Workflow")
    print("=" * 60)
    print()
    
    # Initialize the integrated agent
    config = {
        'region': 'us-east-1',
        'model_id': 'us.anthropic.claude-3-7-sonnet-20250219-v1:0'
    }
    
    agent = StrandsMarketplaceAgent(config=config)
    
    print("✅ Integrated Strands Marketplace Agent initialized")
    print()
    
    # Show current status
    status = agent.get_workflow_status()
    print(f"📊 Current Status:")
    print(f"   Phase: {status['phase']}")
    print(f"   Stage: {status['current_stage']}/8")
    print(f"   Progress: {status['progress']}%")
    print(f"   Listing Complete: {status['listing_complete']}")
    print(f"   Ready for Integration: {status['ready_for_integration']}")
    print()
    
    if not status['listing_complete']:
        print("📝 PHASE 1: Limited Listing Creation")
        print("   Complete all 8 stages to create your AWS Marketplace listing:")
        print("   1. Product Information")
        print("   2. Fulfillment Configuration") 
        print("   3. Pricing Configuration")
        print("   4. Price Review")
        print("   5. Refund Policy")
        print("   6. EULA Configuration")
        print("   7. Offer Availability")
        print("   8. Allowlist Configuration")
        print()
        print("💡 Start by providing your product information...")
        
        # Interactive listing creation
        while not agent.get_workflow_status()['listing_complete']:
            user_input = input("\n💬 Enter information (or 'help' for guidance): ")
            
            if user_input.lower() in ['quit', 'exit']:
                break
            
            response = agent.process_message(user_input)
            print(f"\n🤖 {response}")
            
            # Show progress
            current_status = agent.get_workflow_status()
            if current_status['current_stage'] <= 8:
                print(f"\n📊 Progress: Stage {current_status['current_stage']}/8 ({current_status['progress']}%)")
    
    # Check if ready for integration phase
    final_status = agent.get_workflow_status()
    if final_status['listing_complete']:
        print("\n🎉 PHASE 1 COMPLETE: Limited Listing Created!")
        print(f"   ✅ Product ID: {final_status['product_id']}")
        print(f"   ✅ Offer ID: {final_status['offer_id']}")
        print()
        
        print("🔧 PHASE 2: AWS Integration & Deployment")
        print("   Now you can deploy the AWS infrastructure and complete the workflow:")
        print("   • Deploy CloudFormation stack (DynamoDB, Lambda, API Gateway, SNS)")
        print("   • Execute metering workflow")
        print("   • Submit public visibility request")
        print()
        
        # Ask if user wants to proceed with integration
        proceed = input("Would you like to proceed with AWS integration? (y/n): ").strip().lower()
        
        if proceed == 'y':
            print("\n📋 AWS Integration Phase")
            print("You'll need AWS credentials to proceed...")
            
            # Interactive integration phase
            while True:
                user_input = input("\n💬 Enter command or AWS credentials (or 'help' for options): ")
                
                if user_input.lower() in ['quit', 'exit']:
                    break
                
                response = agent.process_message(user_input)
                print(f"\n🤖 {response}")
        else:
            print("\n💡 You can return anytime to complete the AWS integration phase.")
            print("   Use the same agent and your progress will be preserved.")
    
    print("\n" + "=" * 60)
    print("🏁 Workflow Demo Complete")
    print("   Your AWS Marketplace SaaS integration is ready!")

def demo_api_usage():
    """Demonstrate programmatic API usage"""
    print("\n" + "=" * 60)
    print("🔧 API Usage Demo")
    print("=" * 60)
    
    agent = StrandsMarketplaceAgent()
    
    # Example: Check status
    status = agent.get_workflow_status()
    print(f"Status: {json.dumps(status, indent=2)}")
    
    # Example: Process message
    response = agent.process_message("What's my current progress?")
    print(f"Response: {response}")
    
    # Example: Export data
    data = agent.export_workflow_data()
    print(f"Exported data keys: {list(data.keys())}")

if __name__ == "__main__":
    try:
        main()
        
        # Optionally show API demo
        show_api = input("\nWould you like to see the API usage demo? (y/n): ").strip().lower()
        if show_api == 'y':
            demo_api_usage()
            
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Your progress is saved!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Please check your configuration and try again.")