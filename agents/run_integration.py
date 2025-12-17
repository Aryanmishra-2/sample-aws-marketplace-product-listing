#!/usr/bin/env python3

from serverless_saas_integration import ServerlessSaasIntegrationAgent

if __name__ == "__main__":
    agent = ServerlessSaasIntegrationAgent()
    
    print("=== AWS Marketplace SaaS Integration with Complete Workflow ===")
    print("This will: Deploy Stack -> Wait 15min -> Metering -> Public Visibility")
    
    access_key = input("Enter AWS Access Key: ").strip()
    secret_key = input("Enter AWS Secret Key: ").strip() 
    session_token = input("Enter Session Token (optional): ").strip() or None
    
    if not access_key or not secret_key:
        print("Error: Access key and secret key are required")
        exit(1)
    
    print("\nStarting deployment with complete workflow...")
    result = agent.deploy_integration(access_key, secret_key, session_token)
    
    print(f"\nDeployment Result:")
    print(f"Stack ID: {result.get('stack_id', 'Unknown')}")
    
    if 'workflow_result' in result:
        workflow = result['workflow_result']
        print(f"Workflow Status: {workflow.get('status', 'unknown').upper()}")
        print(f"Current Step: {workflow.get('step', 'unknown')}")
        
        if workflow.get('error'):
            print(f"Error: {workflow['error']}")
        elif workflow.get('status') == 'success':
            print("✅ Complete workflow executed successfully!")
            print("✅ Public visibility request has been submitted!")
    else:
        print("ℹ️  Stack deployed (Contract-based-pricing - no metering required)")