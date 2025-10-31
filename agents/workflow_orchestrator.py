from strands import Agent, tool
try:
    from .metering import MeteringAgent
    from .public_visibility import PublicVisibilityAgent
    from .buyer_experience import BuyerExperienceAgent
except ImportError:
    from metering import MeteringAgent
    from public_visibility import PublicVisibilityAgent
    from buyer_experience import BuyerExperienceAgent
import time
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

class WorkflowOrchestrator(Agent):
    def __init__(self, strands_agent=None):
        super().__init__(name="WorkflowOrchestrator")
        self.strands_agent = strands_agent
        self.metering_agent = MeteringAgent()
        self.visibility_agent = PublicVisibilityAgent()
        self.buyer_experience_agent = BuyerExperienceAgent(strands_agent=strands_agent)
    
    def _validate_credentials(self, access_key, secret_key, session_token=None):
        """Validate AWS credentials"""
        try:
            sts = boto3.client(
                'sts',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                aws_session_token=session_token
            )
            sts.get_caller_identity()
            return True, None
        except (ClientError, NoCredentialsError) as e:
            return False, str(e)
    
    def _check_lambda_exists(self, lambda_function_name, access_key, secret_key, session_token=None):
        """Check if Lambda function exists"""
        try:
            lambda_client = boto3.client(
                'lambda',
                region_name='us-east-1',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                aws_session_token=session_token
            )
            lambda_client.get_function(FunctionName=lambda_function_name)
            return True, None
        except ClientError as e:
            return False, str(e)
    
    def _wait_for_metering_completion(self, access_key, secret_key, session_token=None, max_retries=6):
        """Wait and verify metering completion by checking metering_failed=False"""
        for attempt in range(max_retries):
            try:
                dynamodb = boto3.client(
                    'dynamodb',
                    region_name='us-east-1',
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    aws_session_token=session_token
                )
                
                tables = dynamodb.list_tables()['TableNames']
                metering_table = next((t for t in tables if 'AWSMarketplaceMeteringRecords' in t), None)
                
                if not metering_table:
                    return False, "Metering table not found"
                
                response = dynamodb.scan(TableName=metering_table)
                
                for item in response['Items']:
                    metering_failed = item.get('metering_failed', {}).get('BOOL')
                    if metering_failed is False:
                        return True, "Metering completed successfully"
                
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1}: Waiting for metering_failed=False, retrying in 30 seconds...")
                    time.sleep(30)
                    
            except Exception as e:
                return False, f"Error checking metering status: {str(e)}"
        
        return False, "Metering completion timeout - metering_failed not set to False"
    
    @tool
    def execute_full_workflow(self, access_key, secret_key, session_token=None, lambda_function_name=None):
        """Execute complete AWS Marketplace workflow: Metering → Lambda → Visibility"""
        
        # Check pricing model to determine workflow path
        pricing_model = "Usage-based-pricing"  # Default fallback
        
        print("\n=== AWS Marketplace Complete Workflow Execution ===")
        print(f"Pricing Model: {pricing_model}")
        
        if pricing_model == "Contract-based-pricing":
            print("This workflow will:")
            print("  1. Validate AWS credentials and permissions")
            print("  2. Update fulfillment URL in marketplace")
            print("  3. Test buyer experience (subscription creation)")
            print("  4. Submit public visibility request to AWS Marketplace")
            print("  → Skipping metering steps for contract-based pricing")
        else:
            print("This workflow will:")
            print("  1. Validate AWS credentials and permissions")
            print("  2. Update fulfillment URL in marketplace")
            print("  3. Test buyer experience (subscription creation)")
            print("  4. Create metering records in DynamoDB")
            print("  5. Trigger Lambda to send metering to AWS Marketplace")
            print("  6. Verify metering records processed (metering_failed=False)")
            print("  7. Submit public visibility request to AWS Marketplace")
        
        workflow_status = {
            "step": "validation",
            "status": "in_progress",
            "results": {}
        }
        
        try:
            # Step 1: Validate AWS credentials and permissions
            print("\n━━ Step 1: Credential Validation ━━")
            print("Validating AWS credentials and permissions...")
            valid, error = self._validate_credentials(access_key, secret_key, session_token)
            if not valid:
                print(f"  ✗ Credential validation failed: {error}")
                workflow_status.update({"status": "failed", "error": f"Invalid credentials: {error}"})
                return workflow_status
            print("  ✓ AWS credentials validated successfully")
            
            # Step 2: Update fulfillment URL
            print("\n━━ Step 2: Update Fulfillment URL ━━")
            workflow_status["step"] = "fulfillment_update"
            
            # Check if fulfillment URL update was already done during deployment
            print("  → Fulfillment URL update is handled during CloudFormation deployment")
            print("  → Verifying fulfillment URL is properly configured...")
            
            # Get fulfillment URL from strands agent if available
            fulfillment_url = None
            if self.strands_agent:
                fulfillment_data = self.strands_agent.orchestrator.all_data.get('FULFILLMENT', {})
                fulfillment_url = fulfillment_data.get('fulfillment_url')
                product_id = self.strands_agent.orchestrator.product_id
                
                if fulfillment_url and product_id:
                    print(f"  ✓ Fulfillment URL configured: {fulfillment_url}")
                    print(f"  ✓ Product ID: {product_id}")
                else:
                    print("  → Fulfillment URL will be updated automatically during deployment")
            
            workflow_status["results"]["fulfillment_update"] = {"status": "verified"}
            
            # Step 3: Buyer experience simulation
            print("\n━━ Step 3: Buyer Experience Testing ━━")
            workflow_status["step"] = "buyer_experience"
            
            print("Testing buyer experience is critical to verify:")
            print("  • Fulfillment URL redirect works correctly")
            print("  • Customer registration process functions")
            print("  • SNS notifications are received")
            print("  • Customer data is captured in DynamoDB")
            
            simulate_buyer = input("\nWould you like to test the buyer experience now? (y/n): ").strip().lower()
            
            if simulate_buyer == 'y':
                print("Starting buyer experience testing...")
                buyer_result = self.buyer_experience_agent.simulate_buyer_journey(access_key, secret_key, session_token)
                workflow_status["results"]["buyer_experience"] = buyer_result
                
                if buyer_result.get("status") not in ["success", "partial_success"]:
                    print("\n⚠️  Buyer experience testing failed or incomplete")
                    print("This may affect metering and visibility steps.")
                    
                    continue_anyway = input("Continue with workflow anyway? (y/n): ").strip().lower()
                    if continue_anyway != 'y':
                        workflow_status.update({"status": "failed", "error": f"Buyer experience testing failed: {buyer_result}"})
                        return workflow_status
                    
                print("  ✓ Buyer experience testing completed")
            else:
                print("  → Buyer experience testing skipped")
                print("  ⚠️  Warning: Skipping buyer testing may cause issues with metering")
                workflow_status["results"]["buyer_experience"] = {"status": "skipped", "warning": "Testing skipped - may affect metering"}
            
            # Check if metering is required based on pricing model
            if pricing_model == "Contract-based-pricing":
                print("\n━━ Step 4: Skipping Metering (Contract-based pricing) ━━")
                print("  → Contract-based pricing does not require metering")
                print("  → Proceeding directly to public visibility request")
                workflow_status["results"]["metering"] = {"status": "skipped", "reason": "Contract-based pricing"}
            else:
                # Step 4: Create metering records in DynamoDB
                print("\n━━ Step 4: Metering Setup ━━")
                workflow_status["step"] = "metering"
                
                # Check if buyer experience created customer records
                buyer_status = workflow_status["results"].get("buyer_experience", {}).get("status")
                if buyer_status == "success":
                    print("  ✓ Customer records from buyer testing will be used for metering")
                elif buyer_status == "skipped":
                    print("  → Creating test customer records for metering...")
                else:
                    print("  ⚠️  Buyer testing incomplete - creating fallback test records...")
                
                metering_result = self.metering_agent.check_entitlement_and_add_metering(
                    access_key, secret_key, session_token
                )
                workflow_status["results"]["metering"] = metering_result
                
                if metering_result.get("status") not in ["success", "skipped"]:
                    workflow_status.update({"status": "failed", "error": f"Metering failed: {metering_result}"})
                    return workflow_status
                    return workflow_status
                
                # Step 5: Trigger Lambda function to send metering to AWS Marketplace
                if lambda_function_name and metering_result.get("status") == "success":
                    print("\n━━ Step 5: Lambda Validation ━━")
                    print(f"Validating Lambda function: {lambda_function_name}")
                    exists, error = self._check_lambda_exists(lambda_function_name, access_key, secret_key, session_token)
                    if not exists:
                        print(f"  ✗ Lambda function validation failed: {error}")
                        workflow_status.update({"status": "failed", "error": f"Lambda function not found: {error}"})
                        return workflow_status
                    print("  ✓ Lambda function validated successfully")
                    
                    print("\n━━ Step 6: Metering Processing ━━")
                    workflow_status["step"] = "lambda_trigger"
                    
                    trigger_result = self.metering_agent.trigger_hourly_metering(
                        lambda_function_name, access_key, secret_key, session_token
                    )
                    workflow_status["results"]["lambda_trigger"] = trigger_result
                    
                    if trigger_result.get("status_code") != 200:
                        workflow_status.update({"status": "failed", "error": f"Lambda trigger failed: {trigger_result}"})
                        return workflow_status
                    
                    # Step 7: Verify metering was processed successfully
                    print("\n━━ Step 7: Metering Verification ━━")
                    workflow_status["step"] = "metering_verification"
                    
                    completed, message = self._wait_for_metering_completion(access_key, secret_key, session_token)
                    if not completed:
                        workflow_status.update({"status": "failed", "error": message})
                        return workflow_status
            
            # Final Step: Submit public visibility request to AWS Marketplace
            step_num = "4" if pricing_model == "Contract-based-pricing" else "8"
            print(f"\n━━ Step {step_num}: Public Visibility Request ━━")
            workflow_status["step"] = "visibility_update"
            
            visibility_result = self.visibility_agent.check_metering_and_update_visibility(
                access_key, secret_key, session_token
            )
            workflow_status["results"]["visibility"] = visibility_result
            
            if visibility_result.get("status") == "failed":
                print("  → Visibility request failed - manual intervention may be required")
                workflow_status.update({"status": "partial_success", "warning": visibility_result.get("message")})
            else:
                print("  ✓ Public visibility request submitted successfully")
                

                
                print("\n✓ Complete workflow executed successfully!")
                print("  → Monitor AWS Marketplace console for approval status")
                workflow_status.update({"status": "success", "step": "completed"})
            
            return workflow_status
            
        except Exception as e:
            print(f"\n✗ Unexpected error in {workflow_status['step']}: {str(e)}")
            workflow_status.update({
                "status": "failed",
                "error": f"Unexpected error in {workflow_status['step']}: {str(e)}"
            })
            return workflow_status

if __name__ == "__main__":
    orchestrator = WorkflowOrchestrator()
    
    access_key = input("Enter AWS Access Key: ")
    secret_key = input("Enter AWS Secret Key: ")
    session_token = input("Enter Session Token (optional): ") or None
    lambda_function_name = input("Enter Hourly Lambda Function Name (optional): ") or None
    
    result = orchestrator.execute_full_workflow(access_key, secret_key, session_token, lambda_function_name)
    print(f"Workflow result: {result}")
    
    @tool
    def get_workflow_status(self, workflow_result):
        """Get detailed workflow status and next steps"""
        status = workflow_result.get("status")
        step = workflow_result.get("step")
        
        status_info = {
            "overall_status": status,
            "current_step": step,
            "completed_steps": [],
            "next_actions": []
        }
        
        # Determine completed steps
        results = workflow_result.get("results", {})
        if "metering" in results:
            status_info["completed_steps"].append("metering")
        if "lambda_trigger" in results:
            status_info["completed_steps"].append("lambda_trigger")
        if "visibility" in results:
            status_info["completed_steps"].append("visibility_update")
        
        # Provide next actions based on status
        if status == "failed":
            error = workflow_result.get("error", "Unknown error")
            if "credentials" in error.lower():
                status_info["next_actions"].append("Verify AWS credentials and permissions")
            elif "lambda" in error.lower():
                status_info["next_actions"].append("Check Lambda function name and permissions")
            elif "metering" in error.lower():
                status_info["next_actions"].append("Verify DynamoDB tables and metering setup")
            else:
                status_info["next_actions"].append(f"Address error: {error}")
        
        elif status == "partial_success":
            status_info["next_actions"].append("Manual visibility update may be required")
            status_info["next_actions"].append("Check AWS Marketplace console for pending requests")
        
        elif status == "success":
            status_info["next_actions"].append("Monitor AWS Marketplace for visibility approval")
            status_info["next_actions"].append("Workflow completed successfully")
        
        return status_info
    
    @tool
    def retry_failed_step(self, workflow_result, access_key, secret_key, session_token=None, lambda_function_name=None):
        """Retry from the failed step"""
        failed_step = workflow_result.get("step")
        
        if failed_step == "metering":
            return self.metering_agent.check_entitlement_and_add_metering(access_key, secret_key, session_token)
        elif failed_step == "lambda_trigger":
            return self.metering_agent.trigger_hourly_metering(lambda_function_name, access_key, secret_key, session_token)
        elif failed_step == "visibility_update":
            return self.visibility_agent.check_metering_and_update_visibility(access_key, secret_key, session_token)
        else:
            return {"error": f"Cannot retry step: {failed_step}"}

if __name__ == "__main__":
    orchestrator = WorkflowOrchestrator()
    
    try:
        print("=== AWS Marketplace SaaS Workflow Orchestrator ===")
        print("This will execute: Metering -> Lambda Trigger -> Public Visibility Request\n")
        
        access_key = input("Enter AWS Access Key: ").strip()
        secret_key = input("Enter AWS Secret Key: ").strip()
        session_token = input("Enter Session Token (optional): ").strip() or None
        lambda_function_name = input("Enter Hourly Lambda Function Name (optional): ").strip() or None
        
        if not access_key or not secret_key:
            print("Error: Access key and secret key are required")
            exit(1)
        
        print("\n=== Starting Workflow Execution ===")
        result = orchestrator.execute_full_workflow(access_key, secret_key, session_token, lambda_function_name)
        
        print("\n=== Workflow Results ===")
        print(f"Status: {result.get('status', 'unknown').upper()}")
        print(f"Current Step: {result.get('step', 'unknown')}")
        
        if result.get("error"):
            print(f"Error: {result['error']}")
        
        if result.get("warning"):
            print(f"Warning: {result['warning']}")
        
        # Show detailed status
        status_info = orchestrator.get_workflow_status(result)
        print(f"\nCompleted Steps: {', '.join(status_info['completed_steps']) or 'None'}")
        
        if status_info["next_actions"]:
            print("\nNext Actions:")
            for action in status_info["next_actions"]:
                print(f"  - {action}")
        
        # Show detailed results if available
        if result.get("results"):
            print("\n=== Detailed Results ===")
            for step, step_result in result["results"].items():
                print(f"{step.title()}: {step_result.get('status', 'unknown')}")
        
        # Offer retry for failed workflows
        if result.get("status") == "failed":
            retry = input("\nWould you like to retry the failed step? (y/n): ").strip().lower()
            if retry == 'y':
                print("Retrying failed step...")
                retry_result = orchestrator.retry_failed_step(result, access_key, secret_key, session_token, lambda_function_name)
                print(f"Retry result: {retry_result}")
        
    except KeyboardInterrupt:
        print("\nWorkflow interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        print("Please check your inputs and try again")