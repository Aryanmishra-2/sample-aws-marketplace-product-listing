# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from strands import Agent, tool
import boto3
import uuid
import time
try:
    from .create_saas import CreateSaasAgent
except ImportError:
    from create_saas import CreateSaasAgent

class BuyerExperienceAgent(Agent):
    def __init__(self):
        super().__init__(name="BuyerExperience")
        self.create_saas_agent = CreateSaasAgent()
    
    @tool
    def simulate_buyer_journey(self, access_key, secret_key, session_token=None):
        """Guide customer through buyer experience with step-by-step verification"""
        
        product_id = self.create_saas_agent.get_product_id()
        
        print("=== AWS Marketplace Buyer Experience Simulation ===")
        print("Follow these steps to test your SaaS product as a buyer would:")
        
        # Step 1: Access Management Portal
        print("\n── Step 1: Access Product in AWS Marketplace Management Portal ──")
        print("1. Open AWS Marketplace Management Portal:")
        print("   https://aws.amazon.com/marketplace/management/products")
        print("2. Navigate to your SaaS product listing")
        print(f"3. Select product: {product_id}")
        
        step1_done = input("Have you opened your product page? (y/n): ").strip().lower()
        if step1_done != 'y':
            return {"error": "Step 1 not completed - please access your product page first"}
        
        # Step 2: Validate fulfillment URL
        print("\n── Step 2: Validate Fulfillment URL Update ──")
        print("1. Go to the 'Request Log' tab")
        print("2. Check that the last request status is 'Succeeded'")
        print("3. This confirms the fulfillment URL was updated successfully")
        
        fulfillment_ready = input("Is the last request status 'Succeeded'? (y/n): ").strip().lower()
        if fulfillment_ready != 'y':
            print("⚠️  Please wait for the fulfillment URL update to complete")
            return {"error": "Fulfillment URL update not completed"}
        
        # Step 3: Review product
        print("\n── Step 3: Review Product Information ──")
        print("1. Select 'View on AWS Marketplace'")
        print("2. Review that your product information is accurate")
        print("3. Verify pricing, description, and features are correct")
        
        product_reviewed = input("Have you reviewed your product information? (y/n): ").strip().lower()
        if product_reviewed != 'y':
            return {"error": "Step 3 not completed - please review product information"}
        
        # Step 4: Purchase simulation
        print("\n── Step 4: Simulate Purchase Process ──")
        print("1. Select 'View purchase options'")
        print("2. Under 'How long do you want your contract to run?', select '1 month'")
        print("3. Set 'Renewal Settings' to 'No'")
        print("4. Under 'Contract Options', set any option quantity to 1")
        print("5. Select 'Create contract' then 'Pay now'")
        
        purchase_completed = input("Have you completed the purchase simulation? (y/n): ").strip().lower()
        if purchase_completed != 'y':
            return {"error": "Step 4 not completed - please complete purchase simulation"}
        
        # Step 5: Account setup
        print("\n── Step 5: Account Setup and Registration ──")
        print("1. Select 'Set up your account'")
        print("2. You'll be redirected to your custom registration page")
        print("3. Fill in the registration information:")
        print("   • Company name")
        print("   • Contact email")
        print("   • Any other required fields")
        print("4. Select 'Register'")
        
        registration_completed = input("Have you completed the registration? (y/n): ").strip().lower()
        if registration_completed != 'y':
            return {"error": "Step 5 not completed - please complete registration"}
        
        # Step 6: Verify success
        print("\n── Step 6: Verify Registration Success ──")
        print("Expected outcomes:")
        print("✓ Blue banner appears confirming successful registration")
        print("✓ Email notification sent to your admin email")
        print("✓ Customer record created in DynamoDB")
        
        success_verified = input("Did you see the success banner and receive email notification? (y/n): ").strip().lower()
        
        # Verify customer record in DynamoDB
        print("\n── Verifying Customer Record in DynamoDB ──")
        try:
            dynamodb = boto3.client(
                'dynamodb',
                region_name='us-east-1',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                aws_session_token=session_token
            )
            
            tables = dynamodb.list_tables()['TableNames']
            subscribers_table = None
            
            for table in tables:
                if 'AWSMarketplaceSubscribers' in table or 'NewSubscribers' in table:
                    subscribers_table = table
                    break
            
            if subscribers_table:
                response = dynamodb.scan(TableName=subscribers_table)
                customer_count = len(response['Items'])
                print(f"  ✓ Found {customer_count} customer record(s) in DynamoDB")
                
                if customer_count > 0:
                    latest_customer = response['Items'][-1]
                    customer_id = latest_customer.get('customerIdentifier', {}).get('S', 'Unknown')
                    print(f"  ✓ Latest customer ID: {customer_id}")
                else:
                    print("  ⚠️  No customer records found - registration may not have completed")
            else:
                print("  ⚠️  Subscribers table not found")
                
        except Exception as e:
            print(f"  ✗ Error checking DynamoDB: {str(e)}")
        
        if success_verified == 'y':
            print("\n🎉 Buyer experience simulation completed successfully!")
            print("Your SaaS integration is working correctly:")
            print("  • AWS Marketplace purchase flow ✓")
            print("  • Registration page redirect ✓")
            print("  • SNS notifications ✓")
            print("  • Customer data capture ✓")
            
            return {
                "status": "success",
                "message": "Buyer experience simulation completed successfully",
                "steps_completed": [
                    "Product page access",
                    "Request log validation",
                    "Product information review", 
                    "Purchase simulation",
                    "Account setup",
                    "Registration verification"
                ]
            }
        else:
            print("\n⚠️  Registration may not have completed successfully")
            print("Troubleshooting steps:")
            print("  • Check SNS subscription confirmation")
            print("  • Verify fulfillment URL is correct")
            print("  • Check CloudFormation stack status")
            print("  • Review registration page configuration")
            
            return {
                "status": "partial_success",
                "message": "Buyer experience simulation completed with issues",
                "recommendation": "Check SNS and registration page configuration"
            }
    
    @tool
    def get_simulation_checklist(self):
        """Provide a checklist for buyer experience simulation"""
        
        checklist = {
            "pre_simulation": [
                "CloudFormation stack deployed successfully",
                "SNS subscription confirmed",
                "Fulfillment URL updated",
                "Product listing is active"
            ],
            "simulation_steps": [
                "Access product in Management Portal",
                "Validate request log shows 'Succeeded'",
                "Review product information accuracy",
                "Complete purchase simulation (1 month contract)",
                "Set up account and complete registration",
                "Verify success banner and email notification"
            ],
            "expected_outcomes": [
                "Successful redirect to registration page",
                "Registration completion confirmation",
                "Email notification received",
                "Customer record in DynamoDB",
                "No errors in CloudWatch logs"
            ]
        }
        
        return checklist
    
    @tool
    def verify_customer_registration(self, access_key, secret_key, session_token=None):
        """Verify if customer registration was successful in DynamoDB"""
        try:
            dynamodb = boto3.client(
                'dynamodb',
                region_name='us-east-1',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                aws_session_token=session_token
            )
            
            tables = dynamodb.list_tables()['TableNames']
            subscribers_table = None
            
            for table in tables:
                if 'AWSMarketplaceSubscribers' in table or 'NewSubscribers' in table:
                    subscribers_table = table
                    break
            
            if not subscribers_table:
                return {"error": "Subscribers table not found"}
            
            response = dynamodb.scan(TableName=subscribers_table)
            customers = response['Items']
            
            return {
                "status": "success",
                "customer_count": len(customers),
                "customers": [{
                    "customer_id": item.get('customerIdentifier', {}).get('S', 'Unknown'),
                    "product_code": item.get('productCode', {}).get('S', 'Unknown'),
                    "status": item.get('subscriptionStatus', {}).get('S', 'Unknown')
                } for item in customers]
            }
            
        except Exception as e:
            return {"error": f"Failed to verify registration: {str(e)}"}

if __name__ == "__main__":
    agent = BuyerExperienceAgent()
    
    print("Choose an option:")
    print("1. Run buyer experience simulation")
    print("2. Get simulation checklist")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        result = agent.simulate_buyer_journey()
        print(f"\nSimulation result: {result}")
    elif choice == "2":
        checklist = agent.get_simulation_checklist()
        print("\n=== Buyer Experience Simulation Checklist ===")
        for category, items in checklist.items():
            print(f"\n{category.replace('_', ' ').title()}:")
            for item in items:
                print(f"  □ {item}")
    else:
        print("Invalid choice")