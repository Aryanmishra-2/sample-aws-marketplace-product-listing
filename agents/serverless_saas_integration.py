from strands import Agent, tool
import boto3
import time
import json
try:
    from .create_saas import CreateSaasAgent
    from .workflow_orchestrator import WorkflowOrchestrator
except ImportError:
    from create_saas import CreateSaasAgent
    from workflow_orchestrator import WorkflowOrchestrator

class ServerlessSaasIntegrationAgent(Agent):
    def __init__(self):
        super().__init__(name="ServerlessSaasIntegration")
        self.create_saas_agent = CreateSaasAgent()
        self.workflow_orchestrator = WorkflowOrchestrator()
    
    @tool
    def deploy_integration(self, access_key, secret_key, session_token=None, product_id=None):
        """Deploy AWS Marketplace SaaS integration with complete automated workflow"""
        
        print("=== Starting AWS Marketplace SaaS Integration Deployment ===")
        
        # Set credentials and product ID in create_saas agent
        self.create_saas_agent.set_credentials(access_key, secret_key, session_token)
        if product_id:
            self.create_saas_agent.set_product_id(product_id)
        
        # Get configuration from create_saas agent (will fetch from marketplace)
        product_id = self.create_saas_agent.get_product_id()
        
        print(f"\n=== Fetching Pricing Model from AWS Marketplace ===")
        print(f"Product ID: {product_id}")
        pricing_model = self.create_saas_agent.get_pricing_model_dimension()
        
        if not pricing_model:
            print(f"  ✗ Failed to fetch pricing model from marketplace")
            print(f"  → Using default: Usage-based-pricing")
            pricing_model = "Usage-based-pricing"
        
        email_id = self.create_saas_agent.get_email_dimension()
        
        print(f"\n=== Configuration Summary ===")
        print(f"Product ID: {product_id}")
        print(f"Pricing Model: {pricing_model}")
        print(f"TypeOfSaaSListing will be: {self._get_saas_listing_type(pricing_model)}")
        print(f"Admin Email: {email_id}")
        
        # Validate credentials before deployment
        print("\nValidating AWS credentials...")
        try:
            sts_client = boto3.client(
                'sts',
                region_name='us-east-1',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                aws_session_token=session_token
            )
            identity = sts_client.get_caller_identity()
            print(f"  ✓ Credentials valid for account: {identity['Account']}")
        except Exception as e:
            print(f"  ✗ Invalid credentials: {str(e)}")
            return {"error": f"Invalid AWS credentials: {str(e)}"}
        
        # Connect to CloudFormation
        print("Connecting to AWS CloudFormation...")
        cf_client = boto3.client(
            'cloudformation',
            region_name='us-east-1',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token
        )
        
        # Check if stack already exists and delete it if needed
        stack_name = f"saas-integration-{product_id}"
        print(f"\nChecking if stack '{stack_name}' already exists...")
        
        if self._stack_exists(cf_client, stack_name):
            print(f"  ⚠️  Stack '{stack_name}' already exists")
            print("  → Deleting existing stack before redeployment...")
            
            try:
                cf_client.delete_stack(StackName=stack_name)
                print("  → Waiting for stack deletion to complete...")
                
                deletion_status = self._wait_for_stack_deletion(cf_client, stack_name)
                if deletion_status == 'DELETED':
                    print("  ✓ Existing stack deleted successfully")
                else:
                    print(f"  ✗ Stack deletion failed with status: {deletion_status}")
                    return {"error": f"Failed to delete existing stack: {deletion_status}"}
            except Exception as e:
                print(f"  ✗ Error deleting stack: {str(e)}")
                return {"error": f"Failed to delete existing stack: {str(e)}"}
        else:
            print("  ✓ No existing stack found, proceeding with deployment")
        
        # Deploy AWS Marketplace SaaS integration CloudFormation template
        print("\nDeploying CloudFormation stack...")
        print("  → Creating DynamoDB tables for subscribers and metering")
        print("  → Setting up Lambda functions for metering processing")
        print("  → Configuring API Gateway for customer registration")
        print("  → Setting up SNS topics for marketplace notifications")
        
        with open('bedrock_agent/Integration.yaml', 'r') as f:
            template = f.read()
        
        response = cf_client.create_stack(
            StackName=stack_name,
            TemplateBody=template,
            Parameters=[
                {'ParameterKey': 'ProductId', 'ParameterValue': product_id},
                {'ParameterKey': 'PricingModel', 'ParameterValue': pricing_model},
                {'ParameterKey': 'MarketplaceTechAdminEmail', 'ParameterValue': email_id},
                {'ParameterKey': 'UpdateFulfillmentURL', 'ParameterValue': 'true'}
            ],
            Capabilities=['CAPABILITY_IAM', 'CAPABILITY_AUTO_EXPAND']
        )
        
        stack_id = response['StackId']
        print(f"  ✓ CloudFormation stack created: {stack_id}")
        
        # Wait for stack completion to get outputs
        print("\nWaiting for CloudFormation deployment to complete...")
        stack_status = self._wait_for_stack_completion(cf_client, stack_id)
        if stack_status != 'CREATE_COMPLETE':
            return {"error": f"Stack deployment failed with status: {stack_status}"}
        
        # Get fulfillment URL from stack outputs
        fulfillment_url = self._get_fulfillment_url(cf_client, stack_id)
        
        if fulfillment_url:
            print(f"\n=== Updating Fulfillment URL Automatically ===")
            print(f"MarketplaceFulfillmentURL: {fulfillment_url}")
            
            # Update fulfillment URL programmatically using AWS Marketplace Catalog API
            update_result = self._update_fulfillment_url_api(access_key, secret_key, session_token, product_id, fulfillment_url)
            
            if update_result.get('success'):
                print("  ✓ Fulfillment URL update request submitted successfully")
                print(f"  → ChangeSet ID: {update_result.get('changeset_id')}")
                print("  → AWS Marketplace will process this change (typically takes a few minutes)")
            else:
                print(f"  ✗ Failed to update fulfillment URL: {update_result.get('error')}")
                print("  → Falling back to manual process - please update via AWS Marketplace Management Portal")
        else:
            print("  ⚠️  Could not retrieve fulfillment URL from stack outputs")
        
        # Check SNS subscription confirmation
        print("\n=== SNS Subscription Confirmation ===")
        print(f"An SNS subscription email has been sent to: {email_id}")
        print("This email is required to receive notifications for:")
        print("  • New buyer registrations")
        print("  • Entitlement changes")
        print("  • Subscription events")
        
        sns_confirmed = input("\nHave you confirmed the SNS subscription email? (y/n): ").strip().lower()
        
        if sns_confirmed != 'y':
            print("\n⚠️  Please check your email and confirm the SNS subscription before proceeding.")
            print("Without SNS confirmation, you won't receive important marketplace notifications.")
            confirm_proceed = input("Do you want to proceed anyway? (y/n): ").strip().lower()
            if confirm_proceed != 'y':
                return {"error": "SNS subscription not confirmed. Please confirm and retry."}
        else:
            print("  ✓ SNS subscription confirmed")
        
        # Execute complete metering and visibility workflow for usage-based pricing
        if pricing_model in ["Contract-with-consumption", "Usage-based-pricing"]:
            print(f"\n=== Pricing model requires metering - starting automated workflow ===")
            
            # Locate the metering Lambda function from CloudFormation outputs
            print("\nLocating Lambda function for metering...")
            stack_name = f"saas-integration-{product_id}"
            lambda_function_name = self._get_lambda_function_name(cf_client, stack_id, stack_name)
            
            if lambda_function_name:
                print(f"  ✓ Found Lambda function: {lambda_function_name}")
            else:
                print("  → Lambda function not found in outputs - will proceed without it")
            
            # Execute complete workflow: Metering → Lambda → Public Visibility
            print("\n=== Executing Complete Workflow ===")
            print("Step 1: Create metering records")
            print("Step 2: Trigger Lambda to send to AWS Marketplace")
            print("Step 3: Verify metering success")
            print("Step 4: Submit public visibility request")
            
            workflow_result = self.workflow_orchestrator.execute_full_workflow(
                access_key, secret_key, session_token, lambda_function_name
            )
            
            print("\n=== Workflow Complete ===")
            
            # Simulate buyer experience
            print("\n=== Simulating Buyer Experience ===")
            print("Next step: Simulate a customer purchasing and using your SaaS product")
            print("This will test the complete integration workflow")
            
            return {
                'stack_id': stack_id,
                'workflow_result': workflow_result,
                'sns_confirmed': sns_confirmed == 'y'
            }
        
        print(f"\n=== Deployment Complete ===")
        print(f"Stack ID: {stack_id}")
        print(f"Pricing model {pricing_model} does not require metering workflow")
        return {'stack_id': stack_id}
    
    def _get_lambda_function_name(self, cf_client, stack_id, stack_name):
        """Find Lambda function that contains product_id and Hourly"""
        try:
            product_id = self.create_saas_agent.get_product_id()
            print(f"  → Looking for Lambda function with: {product_id} and Hourly")
            
            # Search Lambda functions by name pattern
            lambda_client = boto3.client('lambda', region_name='us-east-1')
            functions = lambda_client.list_functions()['Functions']
            
            print(f"  → Checking {len(functions)} Lambda functions...")
            
            for func in functions:
                func_name = func['FunctionName']
                
                # Check if function name contains product_id and Hourly
                if product_id in func_name and 'Hourly' in func_name:
                    print(f"  ✓ Found matching Lambda function: {func_name}")
                    return func_name
                    
        except Exception as e:
            print(f"  ✗ Error finding Lambda function: {e}")
        
        print(f"  → No Lambda function found with: {product_id} and Hourly")
        return None
    
    def _update_fulfillment_url_api(self, access_key, secret_key, session_token, product_id, fulfillment_url):
        """Update fulfillment URL using AWS Marketplace Catalog API"""
        try:
            print("  → Connecting to AWS Marketplace Catalog API...")
            
            # Create marketplace catalog client
            catalog_client = boto3.client(
                'marketplace-catalog',
                region_name='us-east-1',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                aws_session_token=session_token
            )
            
            # Get the correct entity identifier with current revision
            print("  → Finding current product revision...")
            entity_id = self._get_current_entity_id(catalog_client, product_id)
            
            if not entity_id:
                return {'success': False, 'error': 'Could not find product entity'}
            
            print(f"  → Using entity ID: {entity_id}")
            
            # Get current product details to find delivery option ID
            print("  → Retrieving current product configuration...")
            
            try:
                describe_response = catalog_client.describe_entity(
                    Catalog='AWSMarketplace',
                    EntityId=entity_id
                )
                
                product_details = describe_response.get('Details', '{}')
                if isinstance(product_details, str):
                    product_details = json.loads(product_details)
                
                print(f"  → Full product details keys: {list(product_details.keys())}")
                
                # Find existing delivery option ID
                delivery_options = product_details.get('DeliveryOptions', [])
                print(f"  → Found {len(delivery_options)} delivery options")
                
                if not delivery_options:
                    print("  → No delivery options exist - using AddDeliveryOptions")
                    return self._add_fulfillment_url_api(catalog_client, entity_id, fulfillment_url)
                
                delivery_option_id = None
                for i, option in enumerate(delivery_options):
                    print(f"  → Option {i+1}: {option}")
                    if 'SaaSUrlDeliveryOptionDetails' in option.get('Details', {}):
                        delivery_option_id = option.get('Id')
                        print(f"  → Found SaaS delivery option with ID: {delivery_option_id}")
                        break
                
                if not delivery_option_id and delivery_options:
                    # Use the first delivery option ID if no SaaS-specific one found
                    delivery_option_id = delivery_options[0].get('Id')
                    print(f"  → Using first delivery option ID: {delivery_option_id}")
                
                if not delivery_option_id:
                    print("  → No valid delivery option ID found - using AddDeliveryOptions")
                    return self._add_fulfillment_url_api(catalog_client, entity_id, fulfillment_url)
                
                print(f"  → Found delivery option ID: {delivery_option_id}")
                
                # Update the fulfillment URL
                print("  → Submitting fulfillment URL update...")
                
                changeset_response = catalog_client.start_change_set(
                    Catalog='AWSMarketplace',
                    ChangeSet=[
                        {
                            'ChangeType': 'UpdateDeliveryOptions',
                            'Entity': {
                                'Identifier': entity_id,
                                'Type': 'SaaSProduct@1.0'
                            },
                            'DetailsDocument': {
                                'DeliveryOptions': [
                                    {
                                        'Id': delivery_option_id,
                                        'Details': {
                                            'SaaSUrlDeliveryOptionDetails': {
                                                'FulfillmentUrl': fulfillment_url
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                )
                
                return {
                    'success': True,
                    'changeset_id': changeset_response['ChangeSetId']
                }
                
            except Exception as describe_error:
                print(f"  → Could not retrieve product details: {describe_error}")
                print("  → Attempting to add delivery option instead...")
                return self._add_fulfillment_url_api(catalog_client, entity_id, fulfillment_url)
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_current_entity_id(self, catalog_client, product_id):
        """Get the current entity ID with correct revision number"""
        try:
            print(f"  → Searching for product: {product_id}")
            
            # List entities to find the current revision
            response = catalog_client.list_entities(
                Catalog='AWSMarketplace',
                EntityType='SaaSProduct',
                MaxResults=50
            )
            
            entities = response.get('EntitySummaryList', [])
            print(f"  → Found {len(entities)} SaaS products")
            
            # Debug: print first few entity IDs
            for i, entity in enumerate(entities[:3]):
                print(f"  → Entity {i+1}: {entity.get('EntityId', 'N/A')}")
            
            for entity in entities:
                entity_id = entity.get('EntityId', '')
                entity_product_id = entity_id.split('@')[0] if '@' in entity_id else entity_id
                print(f"  → Checking: {entity_product_id} vs {product_id}")
                if entity_product_id == product_id:
                    print(f"  → Found exact match: {entity_id}")
                    return entity_id
            
            # Try with pagination if not found
            next_token = response.get('NextToken')
            while next_token:
                print(f"  → Checking next page of entities...")
                response = catalog_client.list_entities(
                    Catalog='AWSMarketplace',
                    EntityType='SaaSProduct',
                    MaxResults=50,
                    NextToken=next_token
                )
                
                entities = response.get('EntitySummaryList', [])
                for entity in entities:
                    entity_id = entity.get('EntityId', '')
                    entity_product_id = entity_id.split('@')[0] if '@' in entity_id else entity_id
                    if entity_product_id == product_id:
                        print(f"  → Found exact match: {entity_id}")
                        return entity_id
                
                next_token = response.get('NextToken')
            
            print(f"  → Product {product_id} not found in marketplace catalog")
            print(f"  → Trying direct entity access with common revision numbers...")
            
            # Try common revision numbers as fallback
            for revision in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
                try:
                    test_entity_id = f"{product_id}@{revision}"
                    catalog_client.describe_entity(
                        Catalog='AWSMarketplace',
                        EntityId=test_entity_id
                    )
                    print(f"  → Found working entity ID: {test_entity_id}")
                    return test_entity_id
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"  → Error finding entity: {e}")
            print(f"  → Trying direct entity access as fallback...")
            
            # Try direct access as fallback
            for revision in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
                try:
                    test_entity_id = f"{product_id}@{revision}"
                    catalog_client.describe_entity(
                        Catalog='AWSMarketplace',
                        EntityId=test_entity_id
                    )
                    print(f"  → Found working entity ID: {test_entity_id}")
                    return test_entity_id
                except:
                    continue
            
            return None
    

    
    def _add_fulfillment_url_api(self, catalog_client, entity_id, fulfillment_url):
        """Add fulfillment URL using AWS Marketplace Catalog API"""
        try:
            print("  → Adding new delivery option with fulfillment URL...")
            
            changeset_response = catalog_client.start_change_set(
                Catalog='AWSMarketplace',
                ChangeSet=[
                    {
                        'ChangeType': 'AddDeliveryOptions',
                        'Entity': {
                            'Identifier': entity_id,
                            'Type': 'SaaSProduct@1.0'
                        },
                        'DetailsDocument': {
                            'DeliveryOptions': [
                                {
                                    'Details': {
                                        'SaaSUrlDeliveryOptionDetails': {
                                            'FulfillmentUrl': fulfillment_url
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            )
            
            return {
                'success': True,
                'changeset_id': changeset_response['ChangeSetId']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_saas_listing_type(self, pricing_model):
        """Map pricing model to TypeOfSaaSListing value"""
        mapping = {
            'Usage-based-pricing': 'subscriptions',
            'Contract-based-pricing': 'contracts',
            'Contract-with-consumption': 'contracts_with_subscription'
        }
        return mapping.get(pricing_model, 'subscriptions')
    
    def _stack_exists(self, cf_client, stack_name):
        """Check if a CloudFormation stack exists"""
        try:
            response = cf_client.describe_stacks(StackName=stack_name)
            stacks = response.get('Stacks', [])
            if stacks:
                status = stacks[0]['StackStatus']
                # Consider stack as existing if it's not in a deleted state
                if status not in ['DELETE_COMPLETE', 'DELETE_FAILED']:
                    return True
            return False
        except cf_client.exceptions.ClientError as e:
            # Stack doesn't exist
            if 'does not exist' in str(e):
                return False
            raise
    
    def _wait_for_stack_deletion(self, cf_client, stack_name, max_wait_minutes=20):
        """Wait for CloudFormation stack deletion to complete"""
        print("  → Monitoring stack deletion progress...")
        
        for attempt in range(max_wait_minutes * 2):  # Check every 30 seconds
            try:
                response = cf_client.describe_stacks(StackName=stack_name)
                status = response['Stacks'][0]['StackStatus']
                
                if status == 'DELETE_COMPLETE':
                    print(f"  ✓ Stack deletion completed successfully")
                    return 'DELETED'
                elif status == 'DELETE_FAILED':
                    print(f"  ✗ Stack deletion failed")
                    return status
                elif status == 'DELETE_IN_PROGRESS':
                    print(f"  → Stack deletion in progress (attempt {attempt + 1}/{max_wait_minutes * 2})")
                    time.sleep(30)
                else:
                    print(f"  → Unexpected status during deletion: {status}")
                    time.sleep(30)
                    
            except cf_client.exceptions.ClientError as e:
                # Stack no longer exists - deletion complete
                if 'does not exist' in str(e):
                    print(f"  ✓ Stack successfully deleted")
                    return 'DELETED'
                print(f"  ✗ Error checking stack status: {e}")
                return 'ERROR'
        
        print(f"  ✗ Stack deletion timeout after {max_wait_minutes} minutes")
        return 'TIMEOUT'
    
    def _get_fulfillment_url(self, cf_client, stack_id):
        """Extract MarketplaceFulfillmentURL from CloudFormation stack outputs"""
        try:
            print("  → Retrieving fulfillment URL from stack outputs...")
            
            # Check main stack outputs
            response = cf_client.describe_stacks(StackName=stack_id)
            main_outputs = response['Stacks'][0].get('Outputs', [])
            
            # Look for nested stack first
            nested_stack_id = None
            for output in main_outputs:
                if 'SampleApp' in output.get('OutputKey', ''):
                    nested_stack_id = output['OutputValue']
                    break
            
            # Check nested stack outputs for fulfillment URL
            if nested_stack_id:
                nested_response = cf_client.describe_stacks(StackName=nested_stack_id)
                nested_outputs = nested_response['Stacks'][0].get('Outputs', [])
                
                for output in nested_outputs:
                    if output.get('OutputKey') == 'AWSMarketplaceFulfillmentURL':
                        print(f"  ✓ Found fulfillment URL in nested stack")
                        return output['OutputValue']
            
            # Check main stack outputs as fallback
            for output in main_outputs:
                if 'FulfillmentURL' in output.get('OutputKey', ''):
                    print(f"  ✓ Found fulfillment URL in main stack")
                    return output['OutputValue']
                    
        except Exception as e:
            print(f"  ✗ Error retrieving fulfillment URL: {e}")
        
        return None
    
    def _wait_for_stack_completion(self, cf_client, stack_id, max_wait_minutes=20):
        """Wait for CloudFormation stack to complete deployment"""
        print("  → Monitoring stack deployment progress...")
        
        for attempt in range(max_wait_minutes * 2):  # Check every 30 seconds
            try:
                response = cf_client.describe_stacks(StackName=stack_id)
                status = response['Stacks'][0]['StackStatus']
                
                if status == 'CREATE_COMPLETE':
                    print(f"  ✓ Stack deployment completed successfully")
                    return status
                elif status in ['CREATE_FAILED', 'ROLLBACK_COMPLETE', 'ROLLBACK_FAILED']:
                    print(f"  ✗ Stack deployment failed: {status}")
                    return status
                elif status in ['CREATE_IN_PROGRESS', 'ROLLBACK_IN_PROGRESS']:
                    print(f"  → Stack status: {status} (attempt {attempt + 1}/{max_wait_minutes * 2})")
                    time.sleep(30)
                else:
                    print(f"  → Unexpected status: {status}")
                    time.sleep(30)
                    
            except Exception as e:
                print(f"  ✗ Error checking stack status: {e}")
                return 'ERROR'
        
        print(f"  ✗ Stack deployment timeout after {max_wait_minutes} minutes")
        return 'TIMEOUT'

if __name__ == "__main__":
    agent = ServerlessSaasIntegrationAgent()
    
    # Customer provides temporary credentials
    access_key = input("Enter AWS Access Key: ")
    secret_key = input("Enter AWS Secret Key: ")
    session_token = input("Enter Session Token (optional): ") or None
    
    stack_id = agent.deploy_integration(access_key, secret_key, session_token)
    print(f"Deployed stack: {stack_id}")