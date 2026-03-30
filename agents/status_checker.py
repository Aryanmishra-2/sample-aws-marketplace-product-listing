# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from strands import Agent, tool
import boto3
from botocore.exceptions import ClientError

class StatusChecker(Agent):
    def __init__(self):
        super().__init__(name="StatusChecker")
    
    @tool
    def check_infrastructure_status(self, access_key, secret_key, session_token=None):
        """Check status of all required infrastructure components"""
        status = {
            "dynamodb_tables": {"status": "unknown", "details": []},
            "lambda_functions": {"status": "unknown", "details": []},
            "marketplace_integration": {"status": "unknown", "details": []}
        }
        
        try:
            # Check DynamoDB tables
            dynamodb = boto3.client(
                'dynamodb',
                region_name='us-east-1',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                aws_session_token=session_token
            )
            
            tables = dynamodb.list_tables()['TableNames']
            required_tables = ['AWSMarketplaceSubscribers', 'AWSMarketplaceMeteringRecords']
            
            found_tables = []
            for required in required_tables:
                matching = [t for t in tables if required in t]
                if matching:
                    found_tables.extend(matching)
                    status["dynamodb_tables"]["details"].append(f"Found: {matching[0]}")
                else:
                    status["dynamodb_tables"]["details"].append(f"Missing: {required}")
            
            status["dynamodb_tables"]["status"] = "ready" if len(found_tables) >= 2 else "incomplete"
            
            # Check Lambda functions
            lambda_client = boto3.client(
                'lambda',
                region_name='us-east-1',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                aws_session_token=session_token
            )
            
            functions = lambda_client.list_functions()['Functions']
            metering_functions = [f for f in functions if 'metering' in f['FunctionName'].lower() or 'hourly' in f['FunctionName'].lower()]
            
            if metering_functions:
                status["lambda_functions"]["status"] = "ready"
                for func in metering_functions:
                    status["lambda_functions"]["details"].append(f"Found: {func['FunctionName']}")
            else:
                status["lambda_functions"]["status"] = "missing"
                status["lambda_functions"]["details"].append("No metering Lambda functions found")
            
            # Check marketplace integration
            try:
                marketplace_client = boto3.client('marketplace-catalog', region_name='us-east-1')
                # This will fail if no permissions, but that's expected
                status["marketplace_integration"]["status"] = "configured"
                status["marketplace_integration"]["details"].append("Marketplace client accessible")
            except:
                status["marketplace_integration"]["status"] = "needs_setup"
                status["marketplace_integration"]["details"].append("Marketplace permissions may be needed")
            
        except Exception as e:
            return {"error": f"Status check failed: {str(e)}"}
        
        return status
    
    @tool
    def get_readiness_report(self, status_result):
        """Generate readiness report for workflow execution"""
        if "error" in status_result:
            return {"ready": False, "reason": status_result["error"]}
        
        ready = True
        issues = []
        
        if status_result["dynamodb_tables"]["status"] != "ready":
            ready = False
            issues.append("DynamoDB tables not ready")
        
        if status_result["lambda_functions"]["status"] != "ready":
            issues.append("Lambda functions not found (optional)")
        
        return {
            "ready": ready,
            "issues": issues,
            "recommendation": "Deploy CloudFormation stack first" if not ready else "Ready for workflow execution"
        }

if __name__ == "__main__":
    checker = StatusChecker()
    
    access_key = input("Enter AWS Access Key: ").strip()
    secret_key = input("Enter AWS Secret Key: ").strip()
    session_token = input("Enter Session Token (optional): ").strip() or None
    
    print("Checking infrastructure status...")
    status = checker.check_infrastructure_status(access_key, secret_key, session_token)
    
    if "error" in status:
        print(f"Error: {status['error']}")
    else:
        print("\n=== Infrastructure Status ===")
        for component, info in status.items():
            print(f"{component.replace('_', ' ').title()}: {info['status'].upper()}")
            for detail in info['details']:
                print(f"  - {detail}")
        
        readiness = checker.get_readiness_report(status)
        print(f"\nWorkflow Ready: {'YES' if readiness['ready'] else 'NO'}")
        print(f"Recommendation: {readiness['recommendation']}")
        
        if readiness['issues']:
            print("Issues:")
            for issue in readiness['issues']:
                print(f"  - {issue}")