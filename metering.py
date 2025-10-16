from strands import Agent, tool
import boto3
import time
import json
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
        dynamodb = boto3.client(
            'dynamodb',
            region_name='us-east-1',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token
        )
        
        try:
            tables = dynamodb.list_tables()['TableNames']
            subscribers_table = None
            
            for table in tables:
                if 'AWSMarketplaceSubscribers' in table or 'NewSubscribers' in table:
                    subscribers_table = table
                    break
            
            if not subscribers_table:
                return {"error": "Subscribers table not found"}
            
            # Insert test customer record
            test_customer = {
                "customerIdentifier": {"S": "test-customer-123"},
                "productCode": {"S": self.create_saas_agent.get_product_id()},
                "subscriptionStatus": {"S": "ACTIVE"}
            }
            
            dynamodb.put_item(TableName=subscribers_table, Item=test_customer)
            return {"status": "success", "customer_id": "test-customer-123"}
            
        except Exception as e:
            return {"error": f"Failed to insert test customer: {str(e)}"}
    
    @tool
    def check_entitlement_and_add_metering(self, access_key, secret_key, session_token=None):
        """Check entitlement and add metering records for Contract-with-consumption and usage-based-pricing"""
        
        pricing_model = self.create_saas_agent.get_pricing_model_dimension()
        
        if pricing_model in ["Contract-with-consumption", "Usage-based-pricing"]:
            # Create DynamoDB client with customer credentials
            dynamodb = boto3.client(
                'dynamodb',
                region_name='us-east-1',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                aws_session_token=session_token
            )
            
            # Find subscriber table with prefix
            try:
                tables = dynamodb.list_tables()['TableNames']
                subscribers_table = None
                metering_table = None
                
                for table in tables:
                    if 'AWSMarketplaceSubscribers' in table or 'NewSubscribers' in table:
                        subscribers_table = table
                    if 'AWSMarketplaceMeteringRecords' in table:
                        metering_table = table
                
                if not subscribers_table:
                    return {"error": "Subscribers table not found"}
                
                response = dynamodb.scan(TableName=subscribers_table)
                
                if not response['Items']:
                    # Insert test customer if table is empty
                    test_result = self.insert_test_customer(access_key, secret_key, session_token)
                    if test_result.get("status") != "success":
                        return test_result
                    customer_identifier = "test-customer-123"
                else:
                    # Get first customer identifier from table
                    customer_identifier = response['Items'][0].get('customerIdentifier', {}).get('S')
                    if not customer_identifier:
                        return {"error": "Customer identifier not found in table"}
                

            except Exception as e:
                return {"error": f"Failed to access tables: {str(e)}"}
            
            # Get usage dimensions from create_saas agent
            usage_dimensions = self.create_saas_agent.get_usage_dimensions()
            
            # Add metering record
            current_timestamp = str(int(time.time()))
            dimension_usage = []
            for dimension in usage_dimensions:
                dimension_usage.append({
                    "M": {
                        "dimension": {"S": dimension},
                        "value": {"N": "10"}
                    }
                })
            
            metering_record = {
                "create_timestamp": {"N": current_timestamp},
                "customerIdentifier": {"S": customer_identifier},
                "dimension_usage": {"L": dimension_usage},
                "metering_pending": {"S": "true"}
            }
            
            # Insert into metering table
            if not metering_table:
                return {"error": "Metering table not found"}
            
            dynamodb.put_item(
                TableName=metering_table,
                Item=metering_record
            )
            
            return {
                "status": "success",
                "customer_identifier": customer_identifier,
                "timestamp": current_timestamp,
                "pricing_model": pricing_model
            }
        else:
            return {"status": "skipped", "reason": f"Pricing model {pricing_model} does not require metering"}
    
    @tool
    def trigger_hourly_metering(self, lambda_function_name, access_key, secret_key, session_token=None):
        """Trigger the hourly Lambda function to report metering to AWS Marketplace"""
        
        lambda_client = boto3.client(
            'lambda',
            region_name='us-east-1',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token
        )
        
        response = lambda_client.invoke(
            FunctionName=lambda_function_name,
            InvocationType='RequestResponse'
        )
        
        return {
            "status": "triggered",
            "status_code": response['StatusCode'],
            "function_name": lambda_function_name
        }

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