from strands import Agent, tool
import boto3
import time
import json
import traceback
try:
    from .workflow_orchestrator import WorkflowOrchestrator
except ImportError:
    from workflow_orchestrator import WorkflowOrchestrator

class ServerlessSaasIntegrationAgent(Agent):
    def __init__(self, strands_agent=None):
        super().__init__(name="ServerlessSaasIntegration")
        self.strands_agent = strands_agent
        print(f"[DEBUG] ServerlessSaasIntegrationAgent initialized with strands_agent: {strands_agent is not None}")
        try:
            self.workflow_orchestrator = WorkflowOrchestrator(strands_agent=strands_agent)
            print(f"[DEBUG] WorkflowOrchestrator initialized successfully")
        except Exception as e:
            print(f"[DEBUG] Error initializing WorkflowOrchestrator: {e}")
            self.workflow_orchestrator = None
    
    @tool
    def deploy_integration(self, access_key, secret_key, session_token=None):
        """
        Deploy AWS Marketplace SaaS integration with complete automated workflow
        DEPRECATED: Use deploy_integration_with_session instead
        """
        # Create session from credentials
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token,
            region_name='us-east-1'
        )
        return self.deploy_integration_with_session(session)
    
    @tool
    def deploy_infrastructure(self, email, stack_name, product_id=None, fulfillment_url=None, pricing_dimensions=None, aws_access_key=None, aws_secret_key=None, aws_session_token=None):
        """
        Deploy serverless infrastructure for AWS Marketplace SaaS integration using CloudFormation
        This is the method called by the Streamlit frontend
        """
        print(f"[DEBUG] deploy_infrastructure called with:")
        print(f"  email: {email}")
        print(f"  stack_name: {stack_name}")
        print(f"  product_id: {product_id}")
        print(f"  fulfillment_url: {fulfillment_url}")
        print(f"  pricing_dimensions: {pricing_dimensions}")
        
        # Check if we have access to strands agent data
        if self.strands_agent:
            print(f"[DEBUG] Strands agent available: {self.strands_agent is not None}")
            if hasattr(self.strands_agent, 'orchestrator') and self.strands_agent.orchestrator:
                print(f"[DEBUG] Orchestrator available: {self.strands_agent.orchestrator is not None}")
                print(f"[DEBUG] Orchestrator product_id: {getattr(self.strands_agent.orchestrator, 'product_id', 'Not set')}")
        
        try:
            # Use product_id from parameter or from strands agent
            final_product_id = product_id
            if not final_product_id and self.strands_agent and hasattr(self.strands_agent, 'orchestrator'):
                final_product_id = getattr(self.strands_agent.orchestrator, 'product_id', None)
            
            print(f"[DEBUG] Final product_id for deployment: {final_product_id}")
            
            # Validate required parameters
            if not email:
                return {'success': False, 'error': 'Email is required for SNS notifications'}
            if not final_product_id:
                return {'success': False, 'error': 'Product ID is required for deployment'}
            
            # Create CloudFormation client
            if aws_access_key and aws_secret_key:
                print("[DEBUG] Using provided AWS credentials")
                cf_client = boto3.client(
                    'cloudformation',
                    region_name='us-east-1',
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key,
                    aws_session_token=aws_session_token
                )
            else:
                print("[DEBUG] Using default AWS credentials")
                cf_client = boto3.client('cloudformation', region_name='us-east-1')
            
            # Validate credentials
            try:
                sts_client = boto3.client('sts', region_name='us-east-1')
                identity = sts_client.get_caller_identity()
                print(f"[DEBUG] ✅ AWS credentials validated for account: {identity['Account']}")
            except Exception as e:
                return {'success': False, 'error': f'Invalid AWS credentials: {str(e)}'}
            
            # Load existing Integration.yaml template
            import os
            template_path = os.path.join(os.path.dirname(__file__), '..', 'bedrock_agent', 'Integration.yaml')
            
            if not os.path.exists(template_path):
                return {'success': False, 'error': f'Integration.yaml template not found at {template_path}'}
            
            print(f"[DEBUG] → Loading CloudFormation template from: {template_path}")
            
            with open(template_path, 'r') as f:
                template_body = f.read()
            
            # Determine pricing model from pricing_dimensions
            pricing_model = "Usage-based-pricing"  # Default
            if pricing_dimensions:
                # Check if we have both entitled and metered dimensions (hybrid)
                dim_types = set(dim.get('type', 'Metered') for dim in pricing_dimensions)
                if 'Entitled' in dim_types and 'Metered' in dim_types:
                    pricing_model = "Contract-with-consumption"
                elif 'Entitled' in dim_types:
                    pricing_model = "Contract-based-pricing"
                else:
                    pricing_model = "Usage-based-pricing"
            
            print("[DEBUG] → Deploying CloudFormation stack...")
            print(f"[DEBUG] → Stack Name: {stack_name}")
            print(f"[DEBUG] → Product ID: {final_product_id}")
            print(f"[DEBUG] → Email: {email}")
            print(f"[DEBUG] → Pricing Model: {pricing_model}")
            
            # Deploy CloudFormation stack
            try:
                response = cf_client.create_stack(
                    StackName=stack_name,
                    TemplateBody=template_body,
                    Parameters=[
                        {'ParameterKey': 'ProductId', 'ParameterValue': final_product_id},
                        {'ParameterKey': 'MarketplaceTechAdminEmail', 'ParameterValue': email},
                        {'ParameterKey': 'PricingModel', 'ParameterValue': pricing_model},
                        {'ParameterKey': 'UpdateFulfillmentURL', 'ParameterValue': 'true'}
                    ],
                    Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM']
                )
                
                stack_id = response['StackId']
                print(f"[DEBUG] ✅ CloudFormation stack created: {stack_id}")
                
                # Wait for stack creation to complete
                print("[DEBUG] → Waiting for stack deployment to complete...")
                print("[DEBUG] → This may take 5-10 minutes. Monitoring progress...")
                
                # Monitor stack progress
                for i in range(40):  # 20 minutes max
                    try:
                        stack_info = cf_client.describe_stacks(StackName=stack_name)
                        status = stack_info['Stacks'][0]['StackStatus']
                        print(f"[DEBUG] → Stack status: {status} (check {i+1}/40)")
                        
                        if status == 'CREATE_COMPLETE':
                            print("[DEBUG] ✅ Stack creation completed successfully")
                            break
                        elif status in ['CREATE_FAILED', 'ROLLBACK_COMPLETE', 'ROLLBACK_FAILED']:
                            print(f"[DEBUG] ❌ Stack creation failed with status: {status}")
                            
                            # Get failure details
                            stack_events = cf_client.describe_stack_events(StackName=stack_name)
                            failed_events = [event for event in stack_events['StackEvents'] 
                                           if event.get('ResourceStatus', '').endswith('_FAILED')]
                            
                            for event in failed_events[-3:]:  # Last 3 failures
                                print(f"[DEBUG] Failed resource: {event.get('LogicalResourceId')} - {event.get('ResourceStatusReason')}")
                            
                            raise Exception(f"Stack creation failed: {status}")
                        
                        time.sleep(30)
                    except Exception as e:
                        if 'does not exist' in str(e):
                            print(f"[DEBUG] ❌ Stack was deleted or rolled back")
                            raise Exception("Stack creation failed and was rolled back")
                        raise e
                
                # Get stack outputs
                stack_info = cf_client.describe_stacks(StackName=stack_name)
                outputs = stack_info['Stacks'][0].get('Outputs', [])
                
                # Extract important outputs from Integration.yaml
                fulfillment_url_output = None
                lambda_function_name = None
                website_bucket = None
                landing_page_url = None
                
                for output in outputs:
                    if output['OutputKey'] == 'AWSMarketplaceFulfillmentURL':
                        fulfillment_url_output = output['OutputValue']
                    elif output['OutputKey'] == 'WebsiteS3Bucket':
                        website_bucket = output['OutputValue']
                    elif output['OutputKey'] == 'LandingPagePreviewURL':
                        landing_page_url = output['OutputValue']
                
                # Try to get Lambda function name from nested stack
                try:
                    nested_stacks = cf_client.list_stack_resources(StackName=stack_name)
                    for resource in nested_stacks['StackResourceSummaries']:
                        if resource['ResourceType'] == 'AWS::CloudFormation::Stack':
                            nested_stack_name = resource['PhysicalResourceId']
                            nested_outputs = cf_client.describe_stacks(StackName=nested_stack_name)
                            for nested_output in nested_outputs['Stacks'][0].get('Outputs', []):
                                if 'Lambda' in nested_output.get('OutputKey', '') and 'Hourly' in nested_output.get('OutputKey', ''):
                                    lambda_function_name = nested_output['OutputValue']
                                    break
                except Exception as e:
                    print(f"[DEBUG] Could not get nested stack outputs: {e}")
                
                print(f"[DEBUG] ✅ Stack deployment completed successfully!")
                print(f"[DEBUG] Stack ID: {stack_id}")
                print(f"[DEBUG] Fulfillment URL: {fulfillment_url_output}")
                print(f"[DEBUG] Lambda Function: {lambda_function_name}")
                
                return {
                    'success': True,
                    'stack_id': stack_id,
                    'stack_name': stack_name,
                    'message': 'AWS Marketplace SaaS Integration deployed successfully',
                    'fulfillment_url': fulfillment_url_output,
                    'lambda_function': lambda_function_name,
                    'website_bucket': website_bucket,
                    'landing_page_url': landing_page_url,
                    'product_id': final_product_id,
                    'pricing_model': pricing_model,
                    'outputs': {output['OutputKey']: output['OutputValue'] for output in outputs}
                }
                
            except Exception as cf_error:
                print(f"[DEBUG] ❌ CloudFormation deployment failed: {cf_error}")
                
                # Get detailed error information
                try:
                    stack_events = cf_client.describe_stack_events(StackName=stack_name)
                    failed_events = [event for event in stack_events['StackEvents'] 
                                   if event.get('ResourceStatus', '').endswith('_FAILED')]
                    
                    error_details = []
                    for event in failed_events[-3:]:  # Last 3 failed events
                        error_details.append({
                            'resource': event.get('LogicalResourceId', 'Unknown'),
                            'type': event.get('ResourceType', 'Unknown'),
                            'status': event.get('ResourceStatus', 'Unknown'),
                            'reason': event.get('ResourceStatusReason', 'No reason provided')
                        })
                    
                    print(f"[DEBUG] Failed resource details: {error_details}")
                    
                    return {
                        'success': False,
                        'error': f'CloudFormation deployment failed: {str(cf_error)}',
                        'failed_resources': error_details
                    }
                except:
                    return {
                        'success': False,
                        'error': f'CloudFormation deployment failed: {str(cf_error)}'
                    }
            
        except Exception as e:
            print(f"[DEBUG] Error in deploy_infrastructure: {e}")
            import traceback
            print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def deploy_integration_with_session(self, session, product_id=None, email=None, pricing_dimensions=None):
        """Deploy AWS Marketplace SaaS integration using boto3 session"""
        
        print("=== Starting AWS Marketplace SaaS Integration Deployment ===")
        
        # Use provided parameters first, then fall back to strands agent data
        if not product_id and self.strands_agent:
            product_id = self.strands_agent.orchestrator.product_id
        
        if not product_id:
            return {"error": "Product ID not available. Please provide product_id parameter or complete the limited listing creation first."}
        
        # Use provided email or get from strands agent
        if not email and self.strands_agent:
            product_data = self.strands_agent.orchestrator.all_data.get('PRODUCT_INFO', {})
            email = product_data.get('support_email', 'admin@example.com')
        
        if not email:
            email = 'admin@example.com'
        
        # Determine pricing model from pricing_dimensions or strands agent data
        pricing_model = "Usage-based-pricing"  # Default
        if pricing_dimensions:
            # Check if we have both entitled and metered dimensions (hybrid)
            dim_types = set(dim.get('type', 'Metered') for dim in pricing_dimensions)
            if 'Entitled' in dim_types and 'Metered' in dim_types:
                pricing_model = "Contract-with-consumption"
            elif 'Entitled' in dim_types:
                pricing_model = "Contract-based-pricing"
            else:
                pricing_model = "Usage-based-pricing"
        elif self.strands_agent:
            pricing_data = self.strands_agent.orchestrator.all_data.get('PRICING_CONFIG', {})
            pricing_model = pricing_data.get('pricing_model', 'Usage-based-pricing')
        
        email_id = email
        
        print(f"Product ID: {product_id}")
        print(f"Pricing Model: {pricing_model}")
        print(f"Admin Email: {email_id}")
        
        # Validate credentials before deployment
        print("\nValidating AWS credentials...")
        try:
            sts_client = session.client('sts')
            identity = sts_client.get_caller_identity()
            print(f"  ✓ Credentials valid for account: {identity['Account']}")
        except Exception as e:
            print(f"  ✗ Invalid credentials: {str(e)}")
            return {"error": f"Invalid AWS credentials: {str(e)}"}
        
        # Connect to CloudFormation
        print("Connecting to AWS CloudFormation...")
        cf_client = session.client('cloudformation')
        
        # Deploy AWS Marketplace SaaS integration CloudFormation template
        print("\nDeploying CloudFormation stack...")
        print("  → Creating DynamoDB tables for subscribers and metering")
        print("  → Setting up Lambda functions for metering processing")
        print("  → Configuring API Gateway for customer registration")
        print("  → Setting up SNS topics for marketplace notifications")
        
        # Find the Integration.yaml file - check multiple possible locations
        import os
        possible_paths = [
            'bedrock_agent/Integration.yaml',
            'reference/streamlit-app/bedrock_agent/Integration.yaml',
            os.path.join(os.path.dirname(__file__), '..', 'bedrock_agent', 'Integration.yaml')
        ]
        
        template_path = None
        for path in possible_paths:
            if os.path.exists(path):
                template_path = path
                break
        
        if not template_path:
            raise FileNotFoundError(f"Could not find Integration.yaml in any of: {possible_paths}")
        
        with open(template_path, 'r') as f:
            template = f.read()
        
        response = cf_client.create_stack(
            StackName=f"saas-integration-{product_id}",
            TemplateBody=template,
            Parameters=[
                {'ParameterKey': 'ProductId', 'ParameterValue': product_id},
                {'ParameterKey': 'PricingModel', 'ParameterValue': pricing_model},
                {'ParameterKey': 'MarketplaceTechAdminEmail', 'ParameterValue': email_id}
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
            
            # Execute complete workflow: Update Fulfillment URL → Buyer Experience → Metering → Lambda → Public Visibility
            print("\n=== Executing Complete Workflow ===")
            print("Step 1: Update fulfillment URL in marketplace")
            print("Step 2: Test buyer experience")
            print("Step 3: Create metering records")
            print("Step 4: Trigger Lambda to send to AWS Marketplace")
            print("Step 5: Verify metering success")
            print("Step 6: Submit public visibility request")
            
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
            product_id = self.strands_agent.orchestrator.product_id if self.strands_agent else None
            if not product_id:
                return None
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
    print("ServerlessSaasIntegrationAgent - Use this agent through the Streamlit app or import it in your code.")
    print("This agent requires actual product data from the listing creation workflow.")
    print("Run the Streamlit app to use this agent with real product data.")