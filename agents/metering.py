from strands import Agent, tool
import boto3
import time
import json
try:
    from .create_saas import CreateSaasAgent
except ImportError:
    from create_saas import CreateSaasAgent

class MeteringAgent(Agent):
    def __init__(self):
        super().__init__(name="Metering")
        self.create_saas_agent = CreateSaasAgent()
        self.dynamodb = boto3.client('dynamodb')
        self.lambda_client = boto3.client('lambda')
    
    @tool
    def insert_test_customer(self, access_key, secret_key, session_token=None):
        """Insert a test customer record into subscribers table if empty"""
        print("  → Creating test customer for metering simulation...")
        
        dynamodb = boto3.client(
            'dynamodb',
            region_name='us-east-1',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token
        )
        
        try:
            # Find the subscribers table created by CloudFormation
            tables = dynamodb.list_tables()['TableNames']
            subscribers_table = None
            
            for table in tables:
                if 'AWSMarketplaceSubscribers' in table or 'NewSubscribers' in table:
                    subscribers_table = table
                    break
            
            if not subscribers_table:
                return {"error": "Subscribers table not found"}
            
            # Insert test customer record for metering purposes
            test_customer = {
                "customerIdentifier": {"S": "test-customer-123"},
                "productCode": {"S": self.create_saas_agent.get_product_id()},
                "subscriptionStatus": {"S": "ACTIVE"}
            }
            
            dynamodb.put_item(TableName=subscribers_table, Item=test_customer)
            print("  ✓ Test customer created successfully")
            return {"status": "success", "customer_id": "test-customer-123"}
            
        except Exception as e:
            return {"error": f"Failed to insert test customer: {str(e)}"}
    
    @tool
    def check_entitlement_and_add_metering(self, access_key, secret_key, session_token=None):
        """Step 1: Check customer entitlement and create metering records for usage tracking"""
        
        pricing_model = self.create_saas_agent.get_pricing_model_dimension()
        print(f"Checking pricing model: {pricing_model}")
        
        if pricing_model in ["Contract-with-consumption", "Usage-based-pricing"]:
            print("  → Pricing model requires metering - proceeding with setup...")
            
            # Connect to customer's DynamoDB tables created by CloudFormation
            dynamodb = boto3.client(
                'dynamodb',
                region_name='us-east-1',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                aws_session_token=session_token
            )
            
            try:
                # Locate the DynamoDB tables created by the CloudFormation stack
                tables = dynamodb.list_tables()['TableNames']
                subscribers_table = None
                metering_table = None
                
                for table in tables:
                    if 'AWSMarketplaceSubscribers' in table or 'NewSubscribers' in table:
                        subscribers_table = table
                        print(f"  ✓ Found subscribers table: {table}")
                    if 'AWSMarketplaceMeteringRecords' in table:
                        metering_table = table
                        print(f"  ✓ Found metering table: {table}")
                
                if not subscribers_table:
                    return {"error": "Subscribers table not found - CloudFormation may not be complete"}
                
                # Check for existing customers or create test customer
                response = dynamodb.scan(TableName=subscribers_table)
                
                if not response['Items']:
                    print("  → No customers found - creating test customer for metering...")
                    test_result = self.insert_test_customer(access_key, secret_key, session_token)
                    if test_result.get("status") != "success":
                        return test_result
                    customer_identifier = "test-customer-123"
                else:
                    # Use existing customer for metering
                    customer_identifier = response['Items'][0].get('customerIdentifier', {}).get('S')
                    print(f"  ✓ Using existing customer: {customer_identifier}")
                    if not customer_identifier:
                        return {"error": "Customer identifier not found in table"}

            except Exception as e:
                return {"error": f"Failed to access DynamoDB tables: {str(e)}"}
            
            # Create metering record with usage dimensions
            usage_dimensions = self.create_saas_agent.get_usage_dimensions()
            print(f"  → Creating metering record for dimensions: {usage_dimensions}")
            
            current_timestamp = str(int(time.time()))
            dimension_usage = []
            for dimension in usage_dimensions:
                dimension_usage.append({
                    "M": {
                        "dimension": {"S": dimension},
                        "value": {"N": "10"}  # Sample usage value
                    }
                })
            
            # Prepare metering record for Lambda processing
            metering_record = {
                "create_timestamp": {"N": current_timestamp},
                "customerIdentifier": {"S": customer_identifier},
                "dimension_usage": {"L": dimension_usage},
                "metering_pending": {"S": "true"}  # Will be processed by Lambda
            }
            
            if not metering_table:
                return {"error": "Metering table not found - CloudFormation may not be complete"}
            
            # Insert metering record - Lambda will process and send to AWS Marketplace
            dynamodb.put_item(TableName=metering_table, Item=metering_record)
            print("  ✓ Metering record created - ready for Lambda processing")
            
            return {
                "status": "success",
                "customer_identifier": customer_identifier,
                "timestamp": current_timestamp,
                "pricing_model": pricing_model
            }
        else:
            print(f"  ✓ Pricing model {pricing_model} does not require metering - skipping")
            return {"status": "skipped", "reason": f"Pricing model {pricing_model} does not require metering"}
    
    @tool
    def trigger_hourly_metering(self, lambda_function_name, access_key, secret_key, session_token=None, trigger_visibility=False):
        """Step 2: Trigger Lambda to process metering records and send to AWS Marketplace"""
        
        print(f"Triggering Lambda function: {lambda_function_name}")
        print("  → Lambda will process pending metering records...")
        print("  → Lambda will call BatchMeterUsage API to AWS Marketplace...")
        print("  → Lambda will update records with metering_failed=False on success...")
        
        lambda_client = boto3.client(
            'lambda',
            region_name='us-east-1',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token
        )
        
        # Invoke the hourly metering Lambda function
        try:
            response = lambda_client.invoke(
                FunctionName=lambda_function_name,
                InvocationType='RequestResponse'
            )
            
            # Check response payload for errors
            payload = response.get('Payload')
            if payload:
                payload_content = payload.read().decode('utf-8')
                print(f"  → Lambda response payload: {payload_content[:200]}...")
            
            if response['StatusCode'] == 200:
                print("  ✓ Lambda executed successfully")
                print("  → Metering data should now be sent to AWS Marketplace")
                print("  → Records should be updated with BatchMeterUsage response")
            else:
                print(f"  ✗ Lambda execution failed with status: {response['StatusCode']}")
                
        except Exception as e:
            print(f"  ✗ Failed to invoke Lambda function: {str(e)}")
            response = {'StatusCode': 500, 'Error': str(e)}
        
        result = {
            "status": "triggered" if response.get('StatusCode') == 200 else "failed",
            "status_code": response.get('StatusCode', 500),
            "function_name": lambda_function_name,
            "error": response.get('Error') if 'Error' in response else None
        }
        
        # Optionally trigger public visibility workflow after successful metering
        if trigger_visibility and response['StatusCode'] == 200:
            print("  → Triggering public visibility workflow...")
            try:
                from .public_visibility import PublicVisibilityAgent
            except ImportError:
                from public_visibility import PublicVisibilityAgent
            visibility_agent = PublicVisibilityAgent()
            
            # Wait for metering to process and update DynamoDB
            print("  → Waiting 30 seconds for metering to complete...")
            time.sleep(30)
            
            visibility_result = visibility_agent.check_metering_and_update_visibility(
                access_key, secret_key, session_token
            )
            result["visibility_result"] = visibility_result
        
        return result

if __name__ == "__main__":
    agent = MeteringAgent()
    
    # Customer provides credentials
    access_key = input("Enter AWS Access Key: ")
    secret_key = input("Enter AWS Secret Key: ")
    session_token = input("Enter Session Token (optional): ") or None
    
    # Check entitlement and add metering
    result = agent.check_entitlement_and_add_metering(access_key, secret_key, session_token)
    print(f"Metering result: {result}")
    
    # Trigger hourly function if needed
    if result.get("status") == "success":
        lambda_name = input("Enter Hourly Lambda Function Name: ")
        trigger_result = agent.trigger_hourly_metering(lambda_name, access_key, secret_key, session_token)
        print(f"Trigger result: {trigger_result}")