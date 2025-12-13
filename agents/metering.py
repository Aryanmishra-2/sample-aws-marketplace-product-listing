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
        """Insert a test customer record into NewSubscribers table if empty"""
        print("  → Creating test customer for metering simulation...")
        
        dynamodb = boto3.client(
            'dynamodb',
            region_name='us-east-1',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token
        )
        
        try:
            # Get product ID to search for stacks
            product_id = self.create_saas_agent.get_product_id()
            print(f"  → Product ID: {product_id}")
            
            # Create CloudFormation client
            cfn_client = boto3.client(
                'cloudformation',
                region_name='us-east-1',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                aws_session_token=session_token
            )
            
            # Search for CloudFormation stack containing product ID
            print(f"  → Searching for CloudFormation stack...")
            stack_name = None
            try:
                stacks_response = cfn_client.list_stacks(
                    StackStatusFilter=[
                        'CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE'
                    ]
                )
                
                for stack in stacks_response.get('StackSummaries', []):
                    stack_name_candidate = stack.get('StackName', '')
                    if product_id in stack_name_candidate:
                        stack_name = stack_name_candidate
                        print(f"  ✓ Found stack: {stack_name}")
                        break
                
                if not stack_name:
                    print(f"  ✗ No stack found for product: {product_id}")
                    return {"error": f"No CloudFormation stack found for product {product_id}"}
            except Exception as list_error:
                print(f"  ✗ Failed to list stacks: {str(list_error)}")
                return {"error": f"Failed to list CloudFormation stacks: {str(list_error)}"}
            
            # List stack resources to find NewSubscribers table
            subscribers_table = None
            try:
                stack_resources = cfn_client.list_stack_resources(StackName=stack_name)
                resources = stack_resources.get('StackResourceSummaries', [])
                print(f"  → Found {len(resources)} resources in stack")
                
                for resource in resources:
                    resource_type = resource.get('ResourceType')
                    logical_id = resource.get('LogicalResourceId', '')
                    physical_id = resource.get('PhysicalResourceId', '')
                    
                    if resource_type == 'AWS::DynamoDB::Table':
                        print(f"  [DEBUG] DynamoDB table - Physical ID: {physical_id}")
                        # Check ONLY in PhysicalResourceId
                        if 'NewSubscribers' in physical_id:
                            subscribers_table = physical_id
                            print(f"  ✓ Found NewSubscribers table: {physical_id}")
                            break
            except Exception as cfn_error:
                print(f"  ✗ Failed to list stack resources: {str(cfn_error)}")
                return {"error": f"Failed to list stack resources: {str(cfn_error)}"}
            
            if not subscribers_table:
                print(f"  ✗ NewSubscribers table not found in stack")
                return {"error": f"NewSubscribers table not found in stack '{stack_name}'"}
            
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
        
        print("\n[METERING AGENT] ===== Starting Entitlement Check =====")
        
        # Sub-step 1: Check pricing model
        print("[METERING AGENT] Sub-step 1: Checking pricing model...")
        pricing_model = self.create_saas_agent.get_pricing_model_dimension()
        print(f"[METERING AGENT] ✓ Pricing model: {pricing_model}")
        
        if pricing_model in ["Contract-with-consumption", "Usage-based-pricing"]:
            print("[METERING AGENT] → Pricing model requires metering - proceeding with setup...")
            
            # Sub-step 2: Connect to DynamoDB
            print("\n[METERING AGENT] Sub-step 2: Connecting to DynamoDB...")
            dynamodb = boto3.client(
                'dynamodb',
                region_name='us-east-1',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                aws_session_token=session_token
            )
            print("[METERING AGENT] ✓ Connected to DynamoDB")
            
            try:
                # Sub-step 3: Locate DynamoDB tables using CloudFormation stack resources
                print("\n[METERING AGENT] Sub-step 3: Locating DynamoDB tables from CloudFormation stack...")
                
                # Get product ID to search for stacks
                product_id = self.create_saas_agent.get_product_id()
                print(f"[METERING AGENT] → Product ID: {product_id}")
                
                # Create CloudFormation client
                cfn_client = boto3.client(
                    'cloudformation',
                    region_name='us-east-1',
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    aws_session_token=session_token
                )
                
                # Step 3a: List all CloudFormation stacks and find the one containing product ID
                print(f"[METERING AGENT] → Searching for CloudFormation stack containing product ID...")
                print(f"[METERING AGENT] [DEBUG] Product ID to search: '{product_id}'")
                stack_name = None
                try:
                    stacks_response = cfn_client.list_stacks(
                        StackStatusFilter=[
                            'CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE'
                        ]
                    )
                    
                    all_stacks = stacks_response.get('StackSummaries', [])
                    print(f"[METERING AGENT] [DEBUG] Total stacks found: {len(all_stacks)}")
                    
                    for idx, stack in enumerate(all_stacks):
                        stack_name_candidate = stack.get('StackName', '')
                        stack_status = stack.get('StackStatus', '')
                        print(f"[METERING AGENT] [DEBUG] Stack {idx + 1}: '{stack_name_candidate}' (Status: {stack_status})")
                        print(f"[METERING AGENT] [DEBUG] Checking if '{product_id}' in '{stack_name_candidate}': {product_id in stack_name_candidate}")
                        
                        if product_id in stack_name_candidate:
                            stack_name = stack_name_candidate
                            print(f"[METERING AGENT] ✓ Found matching stack: {stack_name}")
                            break
                    
                    if not stack_name:
                        print(f"[METERING AGENT] ✗ No stack found containing product ID: '{product_id}'")
                        print(f"[METERING AGENT] [DEBUG] Available stack names:")
                        for stack in all_stacks:
                            print(f"[METERING AGENT] [DEBUG]   - {stack.get('StackName')}")
                        return {"error": f"No CloudFormation stack found for product '{product_id}'. Make sure the stack is deployed."}
                        
                except Exception as list_error:
                    print(f"[METERING AGENT] ✗ Failed to list stacks: {str(list_error)}")
                    print(f"[METERING AGENT] [DEBUG] Exception type: {type(list_error).__name__}")
                    import traceback
                    print(f"[METERING AGENT] [DEBUG] Traceback: {traceback.format_exc()}")
                    return {"error": f"Failed to list CloudFormation stacks: {str(list_error)}"}
                
                # Step 3b: List stack resources to find DynamoDB tables
                print(f"[METERING AGENT] → Listing resources in stack: {stack_name}")
                print(f"[METERING AGENT] [DEBUG] Calling list_stack_resources for: '{stack_name}'")
                subscribers_table = None
                metering_table = None
                
                try:
                    stack_resources = cfn_client.list_stack_resources(StackName=stack_name)
                    resources = stack_resources.get('StackResourceSummaries', [])
                    print(f"[METERING AGENT] → Found {len(resources)} resources in stack")
                    print(f"[METERING AGENT] [DEBUG] Total resources: {len(resources)}")
                    
                    # Count resource types
                    resource_types = {}
                    for r in resources:
                        rt = r.get('ResourceType', 'Unknown')
                        resource_types[rt] = resource_types.get(rt, 0) + 1
                    print(f"[METERING AGENT] [DEBUG] Resource types: {resource_types}")
                    
                    # Search for DynamoDB tables in stack resources
                    dynamodb_tables_found = []
                    for resource in resources:
                        resource_type = resource.get('ResourceType')
                        logical_id = resource.get('LogicalResourceId', '')
                        physical_id = resource.get('PhysicalResourceId', '')
                        resource_status = resource.get('ResourceStatus', '')
                        
                        # Look for DynamoDB tables
                        if resource_type == 'AWS::DynamoDB::Table':
                            dynamodb_tables_found.append({
                                'logical_id': logical_id,
                                'physical_id': physical_id,
                                'status': resource_status
                            })
                            print(f"[METERING AGENT] → Found DynamoDB table:")
                            print(f"[METERING AGENT] [DEBUG]   Logical ID: {logical_id}")
                            print(f"[METERING AGENT] [DEBUG]   Physical ID: {physical_id}")
                            print(f"[METERING AGENT] [DEBUG]   Status: {resource_status}")
                            
                            # Check for NewSubscribers table - ONLY in PhysicalResourceId
                            has_new_subscribers = 'NewSubscribers' in physical_id
                            print(f"[METERING AGENT] [DEBUG]   PhysicalResourceId contains 'NewSubscribers': {has_new_subscribers}")
                            if has_new_subscribers:
                                subscribers_table = physical_id
                                print(f"[METERING AGENT] ✓ Found NewSubscribers table: {physical_id}")
                            
                            # Check for MeteringRecords table - ONLY in PhysicalResourceId
                            has_metering = 'AWSMarketplaceMeteringRecords' in physical_id
                            print(f"[METERING AGENT] [DEBUG]   PhysicalResourceId contains 'AWSMarketplaceMeteringRecords': {has_metering}")
                            if has_metering:
                                metering_table = physical_id
                                print(f"[METERING AGENT] ✓ Found metering table: {physical_id}")
                    
                    print(f"[METERING AGENT] [DEBUG] Total DynamoDB tables found: {len(dynamodb_tables_found)}")
                    if dynamodb_tables_found:
                        print(f"[METERING AGENT] [DEBUG] DynamoDB tables:")
                        for table in dynamodb_tables_found:
                            print(f"[METERING AGENT] [DEBUG]   - {table['logical_id']} -> {table['physical_id']}")
                    
                except Exception as cfn_error:
                    print(f"[METERING AGENT] ✗ Failed to list stack resources: {str(cfn_error)}")
                    print(f"[METERING AGENT] [DEBUG] Exception type: {type(cfn_error).__name__}")
                    import traceback
                    print(f"[METERING AGENT] [DEBUG] Traceback: {traceback.format_exc()}")
                    return {"error": f"Failed to list stack resources: {str(cfn_error)}"}
                
                # Verify both tables were found
                if not subscribers_table:
                    print("[METERING AGENT] ✗ NewSubscribers table not found in stack resources")
                    print(f"[METERING AGENT] → Stack: {stack_name}")
                    print(f"[METERING AGENT] → Resources checked: {len(resources)}")
                    return {"error": f"NewSubscribers table not found in stack '{stack_name}'. Make sure the CloudFormation stack is fully deployed."}
                
                if not metering_table:
                    print("[METERING AGENT] ✗ AWSMarketplaceMeteringRecords table not found in stack resources")
                    print(f"[METERING AGENT] → Stack: {stack_name}")
                    print(f"[METERING AGENT] → Resources checked: {len(resources)}")
                    return {"error": f"AWSMarketplaceMeteringRecords table not found in stack '{stack_name}'. Make sure the CloudFormation stack is fully deployed."}
                
                # Sub-step 4: Get customer from subscribers table
                print("\n[METERING AGENT] Sub-step 4: Retrieving customer from subscribers table...")
                response = dynamodb.scan(TableName=subscribers_table, Limit=10)
                print(f"[METERING AGENT] → Found {len(response['Items'])} customer(s)")
                
                if not response['Items']:
                    print("[METERING AGENT] → No customers found - creating test customer...")
                    test_result = self.insert_test_customer(access_key, secret_key, session_token)
                    if test_result.get("status") != "success":
                        return test_result
                    customer_identifier = "test-customer-123"
                else:
                    customer_identifier = response['Items'][0].get('customerIdentifier', {}).get('S')
                    print(f"[METERING AGENT] ✓ Using existing customer: {customer_identifier}")
                    if not customer_identifier:
                        print("[METERING AGENT] ✗ Customer identifier not found in record")
                        return {"error": "Customer identifier not found in table"}

            except Exception as e:
                print(f"[METERING AGENT] ✗ Failed to access DynamoDB: {str(e)}")
                return {"error": f"Failed to access DynamoDB tables: {str(e)}"}
            
            # Sub-step 5: Get usage dimensions
            print("\n[METERING AGENT] Sub-step 5: Getting usage dimensions...")
            # Set credentials in create_saas_agent so it can fetch dimensions from marketplace
            self.create_saas_agent.set_credentials(access_key, secret_key, session_token)
            
            # Try to load stored dimensions if not already set
            if not self.create_saas_agent._pricing_dimensions:
                print("[METERING AGENT] → No pricing dimensions set, trying to load from storage...")
                stored_dimensions = self._load_stored_dimensions_for_stack(stack_name)
                if stored_dimensions:
                    print(f"[METERING AGENT] → Found {len(stored_dimensions)} stored dimensions")
                    self.create_saas_agent.set_pricing_dimensions(stored_dimensions)
                else:
                    print("[METERING AGENT] → No stored dimensions found")
            
            usage_dimensions = self.create_saas_agent.get_usage_dimensions()
            print(f"[METERING AGENT] ✓ Usage dimensions retrieved: {usage_dimensions}")
            
            # Check if we have any dimensions to work with
            if not usage_dimensions:
                print("[METERING AGENT] ✗ No usage dimensions available - cannot create metering record")
                print("[METERING AGENT] → This means no user-entered dimensions were found during listing creation")
                print("[METERING AGENT] → Metering will be skipped for this product")
                return {
                    "status": "skipped", 
                    "reason": "No usage dimensions found - user must enter pricing dimensions during listing creation"
                }
            
            # Debug: Show detailed information about dimension source
            print(f"\n[METERING AGENT] ===== DIMENSION DEBUGGING =====")
            print(f"[METERING AGENT] → Total dimensions found: {len(usage_dimensions)}")
            
            # Check if dimensions came from user input during listing creation
            if self.create_saas_agent._pricing_dimensions:
                print(f"[METERING AGENT] → ✓ Dimensions source: USER-ENTERED during listing creation")
                print(f"[METERING AGENT] → Original user dimensions:")
                for i, dim in enumerate(self.create_saas_agent._pricing_dimensions, 1):
                    dim_key = dim.get("key") or (dim.get("name", "").lower().replace(" ", "_").replace("-", "_") if dim.get("name") else "unknown")
                    print(f"[METERING AGENT]     {i}. Name: '{dim.get('name', 'N/A')}' → Key: '{dim_key}'")
            else:
                print(f"[METERING AGENT] → ⚠ Dimensions source: MARKETPLACE API or STORAGE")
            
            print(f"[METERING AGENT] → Final dimension keys for DynamoDB:")
            for i, dimension in enumerate(usage_dimensions, 1):
                print(f"[METERING AGENT]     {i}. '{dimension}' (will be stored in DynamoDB)")
            print(f"[METERING AGENT] ===== END DIMENSION DEBUGGING =====\n")
            
            # Sub-step 6: Prepare metering record
            print("\n[METERING AGENT] Sub-step 6: Preparing metering record...")
            current_timestamp = str(int(time.time()))
            print(f"[METERING AGENT] → Timestamp: {current_timestamp}")
            print(f"[METERING AGENT] → Customer: {customer_identifier}")
            print(f"[METERING AGENT] → Creating dimension structure for DynamoDB with sample usage values...")
            print(f"[METERING AGENT] → Sample usage: 10 units per dimension")
            
            # Create dimension usage structure with hardcoded sample values
            dimension_usage = []
            for i, dimension in enumerate(usage_dimensions, 1):
                print(f"[METERING AGENT]   Adding dimension {i}: '{dimension}' with value 10 to DynamoDB record")
                dimension_usage.append({
                    "M": {
                        "dimension": {"S": dimension},
                        "value": {"N": "10"}  # Sample usage value for testing
                    }
                })
            
            # Determine record source based on dimension origin
            record_source = "user_entered_dimensions" if self.create_saas_agent._pricing_dimensions else "marketplace_api_or_storage"
            
            metering_record = {
                "create_timestamp": {"N": current_timestamp},
                "customerIdentifier": {"S": customer_identifier},
                "dimension_usage": {"L": dimension_usage},
                "metering_pending": {"S": "true"},  # Will be processed by Lambda
                "dimension_keys": {"SS": usage_dimensions},  # Store the exact dimension keys used
                "record_source": {"S": record_source}  # Track source of dimensions
            }
            
            # Final verification log
            print(f"[METERING AGENT] → ✓ DynamoDB record prepared with {len(usage_dimensions)} user-entered dimensions")
            print(f"[METERING AGENT] → Record source: {record_source}")
            print(f"[METERING AGENT] → Dimension keys in record: {usage_dimensions}")
            print("[METERING AGENT] ✓ Metering record prepared")
            
            # Sub-step 7: Insert metering record
            print("\n[METERING AGENT] Sub-step 7: Inserting metering record into table...")
            print(f"[METERING AGENT] → Target table: {metering_table}")
            dynamodb.put_item(TableName=metering_table, Item=metering_record)
            print("[METERING AGENT] ✓ Metering record inserted successfully")
            
            # Sub-step 8: Verify metering record and check metering_pending flag
            print("\n[METERING AGENT] Sub-step 8: Verifying metering record in table...")
            try:
                # Scan the table to find the record we just inserted
                verify_response = dynamodb.scan(
                    TableName=metering_table,
                    FilterExpression="customerIdentifier = :customer AND create_timestamp = :timestamp",
                    ExpressionAttributeValues={
                        ":customer": {"S": customer_identifier},
                        ":timestamp": {"N": current_timestamp}
                    },
                    Limit=1
                )
                
                if verify_response['Items']:
                    inserted_record = verify_response['Items'][0]
                    metering_pending_value = inserted_record.get('metering_pending', {}).get('S')
                    stored_dimension_keys = inserted_record.get('dimension_keys', {}).get('SS', [])
                    record_source = inserted_record.get('record_source', {}).get('S', 'unknown')
                    
                    print(f"[METERING AGENT] ✓ Record found in table")
                    print(f"[METERING AGENT] → metering_pending value: {metering_pending_value}")
                    print(f"[METERING AGENT] → record_source: {record_source}")
                    print(f"[METERING AGENT] → VERIFICATION: Dimension keys stored in DynamoDB:")
                    
                    for i, key in enumerate(stored_dimension_keys, 1):
                        print(f"[METERING AGENT]     {i}. '{key}' ✓ CONFIRMED in DynamoDB")
                    
                    # Verify dimension usage structure
                    dimension_usage_list = inserted_record.get('dimension_usage', {}).get('L', [])
                    print(f"[METERING AGENT] → VERIFICATION: Dimension usage entries in DynamoDB:")
                    for i, usage_entry in enumerate(dimension_usage_list, 1):
                        dimension_name = usage_entry.get('M', {}).get('dimension', {}).get('S', 'unknown')
                        print(f"[METERING AGENT]     {i}. Dimension: '{dimension_name}' ✓ CONFIRMED in DynamoDB")
                    
                    if metering_pending_value == "true":
                        print("[METERING AGENT] ✓ metering_pending is set to 'true' - ready for Lambda processing")
                        print(f"[METERING AGENT] ✓ SUCCESS: User-entered dimension keys are properly stored in DynamoDB!")
                    else:
                        print(f"[METERING AGENT] ⚠ metering_pending is '{metering_pending_value}' (expected 'true')")
                else:
                    print("[METERING AGENT] ⚠ Could not verify record (may take a moment to appear)")
            except Exception as verify_error:
                print(f"[METERING AGENT] ⚠ Verification failed: {str(verify_error)}")
                print("[METERING AGENT] → Record was inserted but verification skipped")
            
            print("\n[METERING AGENT] ===== Entitlement Check Complete =====\n")
            
            return {
                "status": "success",
                "customer_identifier": customer_identifier,
                "timestamp": current_timestamp,
                "pricing_model": pricing_model,
                "subscribers_table": subscribers_table,
                "metering_table": metering_table,
                "usage_dimensions": usage_dimensions
            }
        else:
            print(f"[METERING AGENT] ✓ Pricing model {pricing_model} does not require metering - skipping")
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

    def _load_stored_dimensions_for_stack(self, stack_name):
        """Load stored pricing dimensions for a given stack"""
        try:
            # Extract product ID from stack name (format: saas-integration-{product_id})
            if stack_name.startswith('saas-integration-'):
                product_id = stack_name.replace('saas-integration-', '')
                print(f"[METERING AGENT] → Extracted product ID from stack: {product_id}")
                
                import os
                import json
                
                # Look for stored dimensions file
                backend_dir = os.path.dirname(os.path.dirname(__file__))  # Go up from agents/ to project root
                storage_dir = os.path.join(backend_dir, 'backend', 'storage')
                dimensions_file = os.path.join(storage_dir, f'pricing_dimensions_{product_id}.json')
                
                print(f"[METERING AGENT] → Looking for stored dimensions: {dimensions_file}")
                
                if os.path.exists(dimensions_file):
                    with open(dimensions_file, 'r') as f:
                        dimension_data = json.load(f)
                    
                    all_stored_dimensions = dimension_data.get('pricing_dimensions', [])
                    print(f"[METERING AGENT] → Found stored file with {len(all_stored_dimensions)} total dimensions")
                    
                    # Filter to only include METERED dimensions
                    metered_dimensions = []
                    for dim in all_stored_dimensions:
                        dim_type = dim.get("type", "").lower()
                        print(f"[METERING AGENT] → Checking stored dimension: {dim.get('name', 'N/A')} (type: {dim.get('type', 'N/A')})")
                        
                        if dim_type == "metered":
                            metered_dimensions.append(dim)
                            print(f"[METERING AGENT] → ✓ Including METERED dimension: {dim.get('name', 'N/A')}")
                        else:
                            print(f"[METERING AGENT] → ✗ Skipping NON-METERED dimension: {dim.get('name', 'N/A')} (type: {dim.get('type', 'N/A')})")
                    
                    print(f"[METERING AGENT] → Filtered to {len(metered_dimensions)} METERED dimensions")
                    return metered_dimensions if metered_dimensions else None
                else:
                    print(f"[METERING AGENT] → No stored dimensions file found")
                    return None
            else:
                print(f"[METERING AGENT] → Stack name doesn't match expected format: {stack_name}")
                return None
                
        except Exception as e:
            print(f"[METERING AGENT] → Error loading stored dimensions: {e}")
            return None

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