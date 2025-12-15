#!/usr/bin/env python3
"""
Check SaaS Integration Status
Verifies CloudFormation stack status and infrastructure components
"""

import boto3
import sys
from botocore.exceptions import ClientError

def check_saas_integration_status(product_id, region='us-east-1', credentials=None):
    """Check the status of SaaS integration for a product"""
    
    print(f"\n{'='*60}")
    print(f"SaaS Integration Status Check")
    print(f"{'='*60}")
    print(f"Product ID: {product_id}")
    print(f"Region: {region}")
    print(f"{'='*60}\n")
    
    # Create session
    if credentials:
        session = boto3.Session(
            aws_access_key_id=credentials.get('access_key'),
            aws_secret_access_key=credentials.get('secret_key'),
            aws_session_token=credentials.get('session_token'),
            region_name=region
        )
    else:
        session = boto3.Session(region_name=region)
    
    # Check CloudFormation stack
    stack_name = f"saas-integration-{product_id}"
    print(f"1. Checking CloudFormation Stack: {stack_name}")
    print("-" * 60)
    
    cf_client = session.client('cloudformation')
    stack_exists = False
    stack_status = None
    
    try:
        response = cf_client.describe_stacks(StackName=stack_name)
        if response['Stacks']:
            stack = response['Stacks'][0]
            stack_status = stack['StackStatus']
            stack_exists = True
            
            print(f"   ✓ Stack found")
            print(f"   Status: {stack_status}")
            print(f"   Stack ID: {stack['StackId']}")
            
            if 'StackStatusReason' in stack:
                print(f"   Reason: {stack['StackStatusReason']}")
            
            # Show outputs if available
            if 'Outputs' in stack and stack['Outputs']:
                print(f"\n   Outputs:")
                for output in stack['Outputs']:
                    print(f"      {output['OutputKey']}: {output.get('OutputValue', 'N/A')}")
    
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'ValidationError' or 'does not exist' in str(e):
            print(f"   ✗ Stack does not exist")
        else:
            print(f"   ✗ Error: {str(e)}")
    
    # Check DynamoDB tables
    print(f"\n2. Checking DynamoDB Tables")
    print("-" * 60)
    
    dynamodb = session.client('dynamodb')
    required_tables = ['AWSMarketplaceSubscribers', 'AWSMarketplaceMeteringRecords']
    found_tables = []
    
    try:
        tables = dynamodb.list_tables()['TableNames']
        for required in required_tables:
            matching = [t for t in tables if required in t and product_id in t]
            if matching:
                found_tables.append(matching[0])
                print(f"   ✓ Found: {matching[0]}")
            else:
                print(f"   ✗ Missing: {required} (with {product_id})")
    except Exception as e:
        print(f"   ✗ Error checking tables: {str(e)}")
    
    # Check Lambda functions
    print(f"\n3. Checking Lambda Functions")
    print("-" * 60)
    
    lambda_client = session.client('lambda')
    found_functions = []
    
    try:
        functions = lambda_client.list_functions()['Functions']
        metering_functions = [f for f in functions if product_id in f['FunctionName'] and ('metering' in f['FunctionName'].lower() or 'hourly' in f['FunctionName'].lower())]
        
        if metering_functions:
            for func in metering_functions:
                found_functions.append(func['FunctionName'])
                print(f"   ✓ Found: {func['FunctionName']}")
        else:
            print(f"   ✗ No metering Lambda functions found for {product_id}")
    except Exception as e:
        print(f"   ✗ Error checking Lambda functions: {str(e)}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Summary")
    print(f"{'='*60}")
    
    if stack_exists and stack_status == 'CREATE_COMPLETE':
        print(f"   ✓ SaaS Integration: COMPLETED")
        print(f"   ✓ CloudFormation Stack: {stack_status}")
        print(f"   ✓ DynamoDB Tables: {len(found_tables)}/2 found")
        print(f"   ✓ Lambda Functions: {len(found_functions)} found")
        print(f"\n   Status: READY")
    elif stack_exists and stack_status in ['CREATE_IN_PROGRESS', 'UPDATE_IN_PROGRESS']:
        print(f"   ⏳ SaaS Integration: IN PROGRESS")
        print(f"   ⏳ CloudFormation Stack: {stack_status}")
        print(f"\n   Status: DEPLOYING")
    elif stack_exists and stack_status in ['CREATE_FAILED', 'ROLLBACK_COMPLETE', 'DELETE_COMPLETE']:
        print(f"   ✗ SaaS Integration: FAILED")
        print(f"   ✗ CloudFormation Stack: {stack_status}")
        print(f"\n   Status: FAILED - Needs redeployment")
        print(f"\n   Action Required:")
        print(f"      1. Delete the failed stack if it still exists")
        print(f"      2. Redeploy using the SaaS Integration page in the UI")
    else:
        print(f"   ✗ SaaS Integration: NOT DEPLOYED")
        print(f"   ✗ CloudFormation Stack: Not found")
        print(f"\n   Status: PENDING")
        print(f"\n   Action Required:")
        print(f"      Deploy SaaS integration using the UI or run:")
        print(f"      ./deploy_saas_integration.sh")
    
    print(f"{'='*60}\n")
    
    return {
        'stack_exists': stack_exists,
        'stack_status': stack_status,
        'tables_found': len(found_tables),
        'functions_found': len(found_functions),
        'ready': stack_exists and stack_status == 'CREATE_COMPLETE'
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_saas_status.py <product_id> [region]")
        print("Example: python check_saas_status.py prod-cyxse6dkyvfo4 us-east-1")
        sys.exit(1)
    
    product_id = sys.argv[1]
    region = sys.argv[2] if len(sys.argv) > 2 else 'us-east-1'
    
    # Check if credentials are needed
    use_credentials = input("Use specific AWS credentials? (y/n, default: use default profile): ").strip().lower()
    
    credentials = None
    if use_credentials == 'y':
        access_key = input("AWS Access Key ID: ").strip()
        secret_key = input("AWS Secret Access Key: ").strip()
        session_token = input("AWS Session Token (optional): ").strip() or None
        
        credentials = {
            'access_key': access_key,
            'secret_key': secret_key,
            'session_token': session_token
        }
    
    result = check_saas_integration_status(product_id, region, credentials)
    
    sys.exit(0 if result['ready'] else 1)
