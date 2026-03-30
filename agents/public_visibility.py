# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from strands import Agent, tool
import boto3
import json
try:
    from .create_saas import CreateSaasAgent
    from .validation_helper import ValidationHelperAgent
except ImportError:
    from create_saas import CreateSaasAgent
    from validation_helper import ValidationHelperAgent

class PublicVisibilityAgent(Agent):
    def __init__(self):
        super().__init__(name="PublicVisibility")
        self.create_saas_agent = CreateSaasAgent()
        self.validator = ValidationHelperAgent()
    
    @tool
    def raise_public_visibility_request(self, access_key, secret_key, session_token=None):
        """Step 3: Submit public visibility request to AWS Marketplace after successful metering"""
        print("Preparing public visibility request...")
        
        product_id = self.create_saas_agent.get_product_id()
        pricing_model = self.create_saas_agent.get_pricing_model_dimension()
        usage_dimensions = self.create_saas_agent.get_usage_dimensions()
        
        print(f"  → Product ID: {product_id}")
        print(f"  → Pricing Model: {pricing_model}")
        print(f"  → Usage Dimensions: {usage_dimensions}")
        
        # Collect pricing dimension values from user with validation
        print("  → Collecting pricing information for dimensions...")
        dimension_values = {}
        for dimension in usage_dimensions:
            while True:
                value = input(f"Enter price for {dimension}: $")
                validation = self.validator.validate_and_guide("pricing", value)
                
                if validation["valid"]:
                    dimension_values[dimension] = value
                    print(f"    ✓ Set {dimension} = ${value}")
                    break
                else:
                    print(f"    ✗ Invalid input. {validation['guidance']}")
                    print(f"    Example format: {validation['suggested_format']}")
                    retry = input("    Try again? (y/n): ")
                    if retry.lower() != 'y':
                        return {"error": "User cancelled input"}
        
        # Create marketplace catalog client for visibility update
        print("  → Connecting to AWS Marketplace Catalog API...")
        marketplace_client = boto3.client(
            'marketplace-catalog',
            region_name='us-east-1',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token
        )
        
        try:
            # Submit change set to make product publicly visible
            print("  → Submitting change set to AWS Marketplace...")
            print("  → Requesting visibility change from Limited to Public...")
            
            response = marketplace_client.start_change_set(
                Catalog='AWSMarketplace',
                ChangeSet=[{
                    'ChangeType': 'UpdateInformation',
                    'Entity': {
                        'Type': 'SaaSProduct',
                        'Identifier': product_id
                    },
                    'Details': json.dumps({
                        'ProductTitle': f'Public SaaS Product {product_id}',
                        'ShortDescription': 'Public SaaS offering',
                        'LongDescription': 'Publicly available SaaS product',
                        'Visibility': 'Public',
                        'PricingModel': pricing_model,
                        'Dimensions': dimension_values
                    })
                }]
            )
            
            print(f"  ✓ Change set submitted successfully: {response['ChangeSetId']}")
            print("  → AWS will review the request (typically 1-3 business days)")
            print("  → You will receive email notifications about the status")
            
            return {
                "status": "success",
                "message": "Public visibility request submitted successfully",
                "change_set_id": response['ChangeSetId'],
                "product_id": product_id,
                "dimension_values": dimension_values
            }
            
        except Exception as e:
            print(f"  ✗ Failed to submit visibility request: {str(e)}")
            return {"error": f"Failed to update visibility: {str(e)}"}
    
    @tool
    def check_metering_and_update_visibility(self, access_key, secret_key, session_token=None):
        """Verify metering success and automatically trigger public visibility request"""
        
        print("Checking metering records for successful BatchMeterUsage calls...")
        print("  → Looking for metering_failed=False and BatchMeterUsage response...")
        
        # Connect to DynamoDB to verify metering completion
        dynamodb = boto3.client(
            'dynamodb',
            region_name='us-east-1',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token
        )
        
        try:
            # Locate the metering records table
            tables = dynamodb.list_tables()['TableNames']
            metering_table = None
            
            for table in tables:
                if 'AWSMarketplaceMeteringRecords' in table:
                    metering_table = table
                    print(f"  ✓ Found metering table: {table}")
                    break
            
            if not metering_table:
                print("  ✗ Metering table not found")
                return {"error": "Metering table not found"}
            
            # Scan all metering records to check for successful processing
            print("  → Scanning metering records...")
            response = dynamodb.scan(TableName=metering_table)
            
            if not response['Items']:
                print("  ✗ No metering records found")
                return {
                    "status": "failed",
                    "message": "No metering records found. Please troubleshoot metering manually."
                }
            
            # Verify successful metering: metering_failed=False AND BatchMeterUsage response exists
            print("  → Checking for successful metering records...")
            for item in response['Items']:
                metering_failed = item.get('metering_failed', {}).get('BOOL')
                metering_response = item.get('metering_response', {}).get('S')
                
                print(f"    • Record: metering_failed={metering_failed}")
                if metering_response:
                    has_batch_meter = 'BatchMeterUsage' in metering_response
                    print(f"    • BatchMeterUsage response: {'Yes' if has_batch_meter else 'No'}")
                
                # Success criteria: metering_failed=False AND BatchMeterUsage response present
                if metering_failed is False and metering_response and 'BatchMeterUsage' in metering_response:
                    print("  ✓ Successful metering found - proceeding with visibility request")
                    return self.raise_public_visibility_request(access_key, secret_key, session_token)
            
            print("  ✗ No successful metering records found")
            print("  → Required: metering_failed=False AND BatchMeterUsage response")
            return {
                "status": "failed", 
                "message": "Metering validation failed. Please troubleshoot metering manually."
            }
            
        except Exception as e:
            print(f"  ✗ Error checking metering records: {str(e)}")
            return {"error": f"Failed to check metering records: {str(e)}"}

if __name__ == "__main__":
    agent = PublicVisibilityAgent()
    
    # Customer provides credentials
    access_key = input("Enter AWS Access Key: ")
    secret_key = input("Enter AWS Secret Key: ")
    session_token = input("Enter Session Token (optional): ") or None
    
    result = agent.check_metering_and_update_visibility(access_key, secret_key, session_token)
    print(f"Visibility update result: {result}")