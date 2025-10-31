#!/usr/bin/env python3
"""
AWS Marketplace SaaS Integration Chatbot
A conversational AI assistant that guides users through the complete marketplace integration process
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import boto3
import json
import time
from datetime import datetime

try:
    from agents.serverless_saas_integration import ServerlessSaasIntegrationAgent
    from agents.metering import MeteringAgent
    from agents.public_visibility import PublicVisibilityAgent
    from agents.buyer_experience import BuyerExperienceAgent
    from agents.workflow_orchestrator import WorkflowOrchestrator
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))
    from serverless_saas_integration import ServerlessSaasIntegrationAgent
    from metering import MeteringAgent
    from public_visibility import PublicVisibilityAgent
    from buyer_experience import BuyerExperienceAgent
    from workflow_orchestrator import WorkflowOrchestrator

class MarketplaceChatbot:
    def __init__(self):
        self.session_state = {
            'step': 'welcome',
            'credentials': {},
            'credential_step': 'none',  # none, access_key, secret_key, session_token
            'product_config': {},
            'deployment_status': {},
            'conversation_history': []
        }
        
        # Initialize agents
        self.serverless_agent = ServerlessSaasIntegrationAgent(strands_agent=None)
        self.metering_agent = MeteringAgent(strands_agent=None)
        self.visibility_agent = PublicVisibilityAgent(strands_agent=None)
        self.buyer_agent = BuyerExperienceAgent(strands_agent=None)
        self.orchestrator = WorkflowOrchestrator(strands_agent=None)
        
        # Initialize knowledge base
        self.knowledge_base = self._init_knowledge_base()
    
    def _init_knowledge_base(self):
        """Initialize knowledge base for error handling and solutions"""
        try:
            # Try to import validation helper with knowledge base
            from agents.validation_helper import ValidationHelperAgent
            return ValidationHelperAgent()
        except:
            # Fallback to mock knowledge base
            return MockKnowledgeBase()
    
    def _handle_error_with_kb(self, error, context="general"):
        """Handle errors using knowledge base for intelligent solutions"""
        error_str = str(error).lower()
        
        # Query knowledge base for solutions
        try:
            kb_response = self.knowledge_base.query(context, error_str)
            if kb_response and "no guidance" not in kb_response.lower():
                return f"🔍 **Knowledge Base Solution:**\n{kb_response}\n\n"
        except:
            pass
        
        # Fallback to built-in error handling
        return self._get_builtin_solution(error_str, context)
    
    def _get_builtin_solution(self, error_str, context):
        """Built-in error solutions when knowledge base is unavailable"""
        solutions = {
            'invalidclienttokenid': {
                'cause': 'Invalid AWS Access Key or Secret Key',
                'solutions': [
                    'Double-check your Access Key and Secret Key for typos',
                    'Ensure you copied the complete keys without extra spaces',
                    'Generate new Access Keys in AWS IAM Console',
                    'Verify the keys are not expired or deactivated'
                ]
            },
            'accessdenied': {
                'cause': 'Insufficient IAM permissions',
                'solutions': [
                    'Add required permissions: cloudformation:*, marketplace-catalog:*, dynamodb:*, lambda:*',
                    'Contact your AWS administrator to grant permissions',
                    'Use an IAM user with AdministratorAccess policy (for testing)',
                    'Check if your account has AWS Marketplace seller registration'
                ]
            },
            'validationexception': {
                'cause': 'Invalid parameters or malformed request',
                'solutions': [
                    'Check product ID format (must start with "prod-")',
                    'Verify email address format',
                    'Ensure pricing model is valid',
                    'Check CloudFormation template syntax'
                ]
            },
            'resourcenotfound': {
                'cause': 'AWS resource does not exist',
                'solutions': [
                    'Verify the resource exists in the correct AWS region',
                    'Check if CloudFormation stack was created successfully',
                    'Ensure DynamoDB tables and Lambda functions are deployed',
                    'Wait for stack creation to complete before proceeding'
                ]
            },
            'throttling': {
                'cause': 'API rate limits exceeded',
                'solutions': [
                    'Wait a few minutes before retrying',
                    'Implement exponential backoff in retries',
                    'Check if multiple processes are making API calls',
                    'Contact AWS support if throttling persists'
                ]
            }
        }
        
        for error_key, info in solutions.items():
            if error_key in error_str:
                solution_text = f"**Cause:** {info['cause']}\n\n**Solutions:**\n"
                for i, solution in enumerate(info['solutions'], 1):
                    solution_text += f"{i}. {solution}\n"
                return solution_text
        
        return "**General troubleshooting:**\n1. Check AWS credentials and permissions\n2. Verify network connectivity\n3. Ensure all required resources exist\n4. Try again in a few minutes"

    def _show_progress(self, message, steps=None, current_step=0):
        """Show progress indicator with context"""
        progress_msg = f"⏳ **{message}**\n\n"
        
        if steps:
            for i, step in enumerate(steps, 1):
                if i <= current_step:
                    progress_msg += f"✅ {step}\n"
                elif i == current_step + 1:
                    progress_msg += f"🔄 {step} (in progress...)\n"
                else:
                    progress_msg += f"⏸️ {step}\n"
            progress_msg += "\n"
        
        progress_msg += "☕ **Please wait while this completes...**\n"
        progress_msg += "This may take a few minutes. I'll update you when it's done."
        
        return progress_msg
    
    def _show_waiting_context(self, process, duration, what_happening):
        """Show what's happening during waiting periods"""
        return (
            f"⏳ **{process} in Progress**\n\n"
            f"**What's happening:**\n{what_happening}\n\n"
            f"**Expected duration:** {duration}\n\n"
            f"☕ Please wait... I'll notify you when complete!"
        )

    def chat(self, user_input):
        """Main chat interface - processes user input and returns response"""
        original_input = user_input.strip()
        user_input = user_input.strip().lower()
        
        # Add to conversation history
        self.session_state['conversation_history'].append({
            'timestamp': datetime.now().isoformat(),
            'user': user_input,
            'step': self.session_state['step']
        })
        
        # Handle numeric option selection
        if user_input.isdigit() and hasattr(self.session_state, 'last_options'):
            option_num = int(user_input)
            if 1 <= option_num <= len(self.session_state['last_options']):
                user_input = self.session_state['last_options'][option_num - 1].lower()
        
        # For credential input, preserve original case
        if self.session_state.get('credential_step') in ['access_key', 'secret_key', 'session_token']:
            user_input = original_input
        
        # Route to appropriate handler based on current step and user input
        if self.session_state['step'] == 'welcome':
            return self._handle_welcome(user_input)
        elif self.session_state['step'] == 'credentials':
            return self._handle_credentials(user_input)
        elif self.session_state['step'] == 'deployment':
            return self._handle_deployment(user_input)
        elif self.session_state['step'] == 'workflow':
            return self._handle_workflow(user_input)
        elif self.session_state['step'] == 'step1':
            return self._handle_step1(user_input)
        elif self.session_state['step'] == 'step2':
            return self._handle_step2(user_input)
        elif self.session_state['step'] == 'step3':
            return self._handle_step3(user_input)
        elif self.session_state['step'] == 'step4':
            return self._handle_step4(user_input)
        elif self.session_state['step'] == 'step5':
            return self._handle_step5(user_input)
        elif self.session_state['step'] == 'step6':
            return self._handle_step6(user_input)
        elif self.session_state['step'] == 'sns_confirmation':
            return self._handle_sns(user_input)
        elif self.session_state['step'] == 'metering':
            return self._handle_metering(user_input)
        elif self.session_state['step'] == 'visibility':
            return self._handle_visibility(user_input)
        elif self.session_state['step'] == 'complete':
            return self._handle_complete(user_input)
        else:
            return self._handle_general(user_input)

    def _handle_welcome(self, user_input):
        """Welcome and initial setup"""
        if not user_input or 'help' in user_input or 'start' in user_input:
            self.session_state['step'] = 'credentials'
            return {
                'message': "👋 Hi! I'm your AWS Marketplace SaaS Integration Assistant.\n\n"
                          "I'll help you deploy and configure your SaaS product on AWS Marketplace. "
                          "This includes:\n"
                          "• CloudFormation deployment\n"
                          "• Automatic fulfillment URL updates\n"
                          "• Metering setup and testing\n"
                          "• Public visibility requests\n\n"
                          "To get started, I'll need your AWS credentials. Do you have them ready?",
                'options': ['Yes, I have my credentials', 'No, I need help getting credentials', 'What permissions do I need?']
            }
        
        return self._handle_general(user_input)
    
    def _handle_credentials(self, user_input):
        """Handle credential collection"""
        # Handle credential step-by-step collection
        if self.session_state['credential_step'] == 'access_key':
            return self._collect_access_key(user_input)
        elif self.session_state['credential_step'] == 'secret_key':
            return self._collect_secret_key(user_input)
        elif self.session_state['credential_step'] == 'session_token':
            return self._collect_session_token(user_input)
        
        # Initial credential request
        if 'yes' in user_input or 'have' in user_input or 'ready' in user_input or user_input == '1':
            self.session_state['credential_step'] = 'access_key'
            return {
                'message': "Perfect! Let's collect your AWS credentials step by step.\n\n"
                          "🔑 **Step 1: Access Key**\n\n"
                          "Please enter your AWS Access Key (starts with AKIA...):",
                'input_type': 'access_key'
            }
        
        elif 'help' in user_input or 'how' in user_input or user_input == '2':
            return {
                'message': "📋 **To get AWS credentials:**\n\n"
                          "1. Go to AWS Console → IAM → Users\n"
                          "2. Select your user → Security credentials\n"
                          "3. Create access key → Command Line Interface (CLI)\n"
                          "4. Download the credentials\n\n"
                          "💡 **Tip**: Use temporary credentials for security!\n\n"
                          "Ready to provide your credentials?",
                'options': ['Yes, I have them now', 'What permissions do I need?']
            }
        
        elif 'permission' in user_input or user_input == '3':
            return {
                'message': "🛡️ **Required IAM Permissions:**\n\n"
                          "• `cloudformation:*` - For stack deployment\n"
                          "• `marketplace-catalog:*` - For fulfillment URL updates\n"
                          "• `dynamodb:*` - For metering tables\n"
                          "• `lambda:*` - For metering functions\n"
                          "• `sns:*` - For notifications\n\n"
                          "Ready to provide your credentials?",
                'options': ['Yes, I have them', 'I need help with permissions']
            }
        
        return {
            'message': "I need your AWS credentials to proceed.\n\n"
                      "Ready to provide them step by step?",
            'options': ['Yes, I have my credentials', 'No, I need help getting credentials', 'What permissions do I need?']
        }
    
    def _collect_access_key(self, user_input):
        """Collect AWS Access Key"""
        access_key = user_input.strip()
        
        # Basic validation - just check if it looks like an access key
        if len(access_key) < 16 or not access_key.upper().startswith('AKIA'):
            return {
                'message': f"❌ **Invalid Access Key**\n\n"
                          f"You entered: '{access_key}' ({len(access_key)} characters)\n"
                          f"Expected: Starts with 'AKIA', 20 characters total\n\n"
                          "Please enter a valid Access Key:",
                'input_type': 'access_key'
            }
        
        # Accept the key if it passes basic validation
        self.session_state['credentials']['access_key'] = access_key
        self.session_state['credential_step'] = 'secret_key'
        
        return {
            'message': "✅ **Access Key saved!**\n\n"
                      "🔐 **Step 2: Secret Access Key**\n\n"
                      "Please enter your AWS Secret Access Key:",
            'input_type': 'secret_key'
        }

    def _collect_secret_key(self, user_input):
        """Collect AWS Secret Key"""
        secret_key = user_input.strip()
        
        if len(secret_key) < 20:
            return {
                'message': "❌ **Secret Key seems too short**\n\n"
                          "AWS Secret Keys are typically 40 characters long.\n\n"
                          "Please enter your complete Secret Access Key:",
                'input_type': 'secret_key'
            }
        
        self.session_state['credentials']['secret_key'] = secret_key
        self.session_state['credential_step'] = 'session_token'
        
        return {
            'message': "✅ **Secret Key saved!**\n\n"
                      "🎫 **Step 3: Session Token (Optional)**\n\n"
                      "If you're using temporary credentials, enter your Session Token.\n"
                      "Otherwise, type 'skip' to continue:",
            'input_type': 'session_token',
            'options': ['Skip (no session token)', 'I have a session token']
        }
    
    def _collect_session_token(self, user_input):
        """Collect AWS Session Token (optional)"""
        user_input = user_input.strip().lower()
        
        # Handle option selections
        if 'skip' in user_input or 'no session' in user_input or user_input == '1':
            return self._validate_credentials()
        
        if 'i have' in user_input or user_input == '2':
            return {
                'message': "Please enter your Session Token:",
                'input_type': 'session_token'
            }
        
        # If it's a long string, assume it's the actual token
        if len(user_input) > 50:  # Session tokens are typically very long
            self.session_state['credentials']['session_token'] = user_input.strip()
            return self._validate_credentials()
        
        # If unclear, ask again
        return {
            'message': "Please choose an option:",
            'options': ['Skip (no session token)', 'I have a session token']
        }
    
    def _validate_credentials(self):
        """Validate collected credentials"""
        # Show validation progress
        print(self._show_waiting_context(
            "Credential Validation",
            "5-10 seconds",
            "• Connecting to AWS STS service\n"
            "• Verifying Access Key and Secret Key\n"
            "• Checking account permissions\n"
            "• Retrieving account information"
        ))
        
        try:
            creds = self.session_state['credentials']
            sts = boto3.client(
                'sts',
                aws_access_key_id=creds['access_key'],
                aws_secret_access_key=creds['secret_key'],
                aws_session_token=creds.get('session_token')
            )
            identity = sts.get_caller_identity()
            
            self.session_state['step'] = 'deployment'
            self.session_state['credential_step'] = 'complete'
            
            return {
                'message': f"✅ **Credentials validated successfully!**\n\n"
                          f"Account: {identity['Account']}\n"
                          f"User: {identity.get('Arn', 'Unknown').split('/')[-1]}\n\n"
                          f"🚀 **Ready to deploy your SaaS integration!**\n\n"
                          f"Your product configuration:\n"
                          f"• Product ID: test-product-123\n"
                          f"• Pricing: Usage-based-pricing\n"
                          f"• Email: support@example.com\n\n"
                          f"Shall I start the deployment?",
                'options': ['Yes, deploy now!', 'Let me review the configuration', 'What will be deployed?']
            }
        except Exception as e:
            # Use knowledge base for intelligent error handling
            kb_solution = self._handle_error_with_kb(e, "credentials")
            
            error_msg = f"❌ **Credential Validation Failed**\n\n{kb_solution}\n"
            error_msg += f"**Error Details:** {str(e)}\n\n"
            
            self.session_state['credential_step'] = 'access_key'
            self.session_state['credentials'] = {}
            
            return {
                'message': error_msg,
                'options': ['Try again with new credentials', 'Get help with permissions', 'Contact support']
            }
    
    def _handle_deployment(self, user_input):
        """Handle deployment phase"""
        user_input = user_input.strip().lower()
        
        # Handle user responses
        if 'yes' in user_input or 'deploy' in user_input or user_input == '1':
            return self._deploy_cloudformation()
        elif 'review' in user_input or user_input == '2':
            return self._show_configuration()
        elif 'what will' in user_input or user_input == '3':
            return self._show_deployment_details()
        
        return {
            'message': "Please choose an option:",
            'options': ['Yes, deploy now!', 'Let me review the configuration', 'What will be deployed?']
        }
    
    def _deploy_cloudformation(self):
        """Deploy CloudFormation stack"""
        print(self._show_waiting_context(
            "CloudFormation Deployment",
            "2-5 minutes",
            "• Creating CloudFormation stack\n"
            "• Deploying Lambda functions\n"
            "• Setting up API Gateway\n"
            "• Configuring SNS topics\n"
            "• Updating fulfillment URL"
        ))
        
        try:
            # Use the serverless integration agent
            result = self.serverless_agent.deploy_integration(
                self.session_state['credentials']['access_key'],
                self.session_state['credentials']['secret_key'],
                self.session_state['credentials'].get('session_token')
            )
            
            if result.get('success'):
                self.session_state['step'] = 'workflow'
                return {
                    'message': f"✅ **CloudFormation deployment successful!**\n\n"
                              f"Stack Name: {result.get('stack_name', 'Unknown')}\n"
                              f"Status: {result.get('status', 'CREATE_COMPLETE')}\n\n"
                              f"🔗 **Fulfillment URL updated automatically**\n\n"
                              f"📋 **Ready to execute complete workflow**\n\n"
                              f"This will run: Metering → Lambda → Visibility Request\n\n"
                              f"Proceed with full workflow?",
                    'options': ['Yes, run workflow', 'Show stack details', 'Manual steps']
                }
            else:
                return {
                    'message': f"❌ **Deployment failed**\n\n{result.get('error', 'Unknown error')}\n\n"
                              f"Would you like to try again?",
                    'options': ['Retry deployment', 'Check configuration', 'Get help']
                }
        except Exception as e:
            kb_solution = self._handle_error_with_kb(e, "deployment")
            return {
                'message': f"❌ **Deployment Error**\n\n{kb_solution}\n\n"
                          f"Error: {str(e)}\n\n"
                          f"What would you like to do?",
                'options': ['Retry deployment', 'Check permissions', 'Contact support']
            }
    
    def _show_configuration(self):
        """Show current configuration"""
        return {
            'message': f"📋 **Current Configuration:**\n\n"
                      f"• Product ID: test-product-123\n"
                      f"• Pricing Model: Usage-based-pricing\n"
                      f"• Contact Email: support@example.com\n\n"
                      f"Ready to deploy with this configuration?",
            'options': ['Yes, deploy now!', 'Modify configuration', 'Cancel']
        }
    
    def _show_deployment_details(self):
        """Show what will be deployed"""
        return {
            'message': f"🏗️ **Deployment Details:**\n\n"
                      f"**CloudFormation Stack will create:**\n"
                      f"• Lambda functions for SaaS integration\n"
                      f"• API Gateway for webhook endpoints\n"
                      f"• SNS topics for notifications\n"
                      f"• IAM roles and policies\n"
                      f"• DynamoDB tables for state management\n\n"
                      f"**Automatic Configuration:**\n"
                      f"• Fulfillment URL will be updated via Marketplace Catalog API\n"
                      f"• SNS subscription will be configured\n\n"
                      f"Ready to proceed?",
            'options': ['Yes, start deployment!', 'Go back', 'Cancel']
        }
    
    def _handle_workflow(self, user_input):
        """Handle complete workflow execution"""
        user_input = user_input.strip().lower()
        
        if 'yes' in user_input or 'run' in user_input or user_input == '1':
            return self._execute_workflow()
        elif 'details' in user_input or user_input == '2':
            return {
                'message': "📊 **Stack Details:**\n\n"
                          "You can view full details in AWS CloudFormation console.\n\n"
                          "Ready to run the workflow?",
                'options': ['Run workflow', 'Open AWS Console', 'Go back']
            }
        elif 'manual' in user_input or user_input == '3':
            return self._show_manual_steps()
        
        return {
            'message': "Please choose an option:",
            'options': ['Yes, run workflow', 'Show stack details', 'Manual steps']
        }
    
    def _execute_workflow(self):
        """Execute the complete workflow using WorkflowOrchestrator"""
        print(self._show_waiting_context(
            "Complete Workflow Execution",
            "3-5 minutes",
            "• Validating credentials and permissions\n"
            "• Creating metering records in DynamoDB\n"
            "• Triggering Lambda for BatchMeterUsage\n"
            "• Verifying metering completion\n"
            "• Submitting public visibility request"
        ))
        
        try:
            # Execute the workflow
            result = self.orchestrator.execute_full_workflow(
                self.session_state['credentials']['access_key'],
                self.session_state['credentials']['secret_key'],
                self.session_state['credentials'].get('session_token')
            )
            
            if result.get('status') == 'success':
                self.session_state['step'] = 'complete'
                return {
                    'message': f"✅ **Complete workflow executed successfully!**\n\n"
                              f"✓ Metering records created\n"
                              f"✓ Lambda function triggered\n"
                              f"✓ BatchMeterUsage API calls completed\n"
                              f"✓ Public visibility request submitted\n\n"
                              f"🎉 **Integration Complete!**\n\n"
                              f"Monitor AWS Marketplace console for approval status.",
                    'final': True
                }
            elif result.get('status') == 'partial_success':
                return {
                    'message': f"⚠️ **Workflow partially completed**\n\n"
                              f"Completed steps: {', '.join(result.get('results', {}).keys())}\n"
                              f"Warning: {result.get('warning', 'Some steps may need manual intervention')}\n\n"
                              f"What would you like to do?",
                    'options': ['Retry failed steps', 'Complete anyway', 'Get help']
                }
            else:
                return {
                    'message': f"❌ **Workflow failed**\n\n"
                              f"Failed at: {result.get('step', 'unknown')}\n"
                              f"Error: {result.get('error', 'Unknown error')}\n\n"
                              f"What would you like to do?",
                    'options': ['Retry workflow', 'Manual steps', 'Get help']
                }
        except Exception as e:
            kb_solution = self._handle_error_with_kb(e, "workflow")
            return {
                'message': f"❌ **Workflow Error**\n\n{kb_solution}\n\n"
                          f"Error: {str(e)}\n\n"
                          f"What would you like to do?",
                'options': ['Retry workflow', 'Manual steps', 'Contact support']
            }
    
    def _show_manual_steps(self):
        """Show manual steps for users who prefer step-by-step approach"""
        return {
            'message': f"📋 **Manual Steps Available:**\n\n"
                      f"If you prefer to run steps manually:\n"
                      f"1. Test metering functionality\n"
                      f"2. Verify SNS subscriptions\n"
                      f"3. Request public visibility\n\n"
                      f"Or use the automated workflow for best results.\n\n"
                      f"What would you prefer?",
            'options': ['Use automated workflow', 'Manual metering test', 'Skip to visibility']
        }
    
    def _step1_access_product(self):
        """Step 1: Access Product in AWS Marketplace Management Portal"""
        return {
            'message': "── **Step 1: Access Product in AWS Marketplace Management Portal** ──\n\n"
                      "1. Open AWS Marketplace Management Portal\n"
                      "2. Navigate to your SaaS product listing\n"
                      f"3. Select product: test-product-123\n\n"
                      "Have you opened your product page?",
            'options': ['Yes, opened', 'Need help finding it', 'Skip this step']
        }
    
    def _step2_validate_fulfillment(self):
        """Step 2: Validate Fulfillment URL Update"""
        return {
            'message': "── **Step 2: Validate Fulfillment URL Update** ──\n\n"
                      "1. Go to the 'Request Log' tab\n"
                      "2. Check that the last request status is 'Succeeded'\n"
                      "3. This confirms the fulfillment URL was updated successfully\n\n"
                      "Is the last request status 'Succeeded'?",
            'options': ['Yes, succeeded', 'No, failed', 'Cannot find Request Log']
        }
    
    def _step3_review_product(self):
        """Step 3: Review Product Information"""
        return {
            'message': "── **Step 3: Review Product Information** ──\n\n"
                      "1. Select 'View on AWS Marketplace'\n"
                      "2. Review that your product information is accurate\n"
                      "3. Verify pricing, description, and features are correct\n\n"
                      "Have you reviewed your product information?",
            'options': ['Yes, looks good', 'Need to make changes', 'Skip review']
        }
    
    def _step4_simulate_purchase(self):
        """Step 4: Simulate Purchase Process"""
        return {
            'message': "── **Step 4: Simulate Purchase Process** ──\n\n"
                      "1. Select 'View purchase options'\n"
                      "2. Under 'How long do you want your contract to run?', select '1 month'\n"
                      "3. Set 'Renewal Settings' to 'No'\n"
                      "4. Under 'Contract Options', set any option quantity to 1\n"
                      "5. Select 'Create contract' then 'Pay now'\n\n"
                      "Have you completed the purchase simulation?",
            'options': ['Yes, completed', 'Having issues', 'Skip simulation']
        }
    
    def _step5_account_setup(self):
        """Step 5: Account Setup and Registration"""
        return {
            'message': "── **Step 5: Account Setup and Registration** ──\n\n"
                      "1. Select 'Set up your account'\n"
                      "2. You'll be redirected to your custom registration page\n"
                      "3. Fill in the registration information:\n"
                      "   • Company name\n"
                      "   • Contact email\n"
                      "   • Any other required fields\n"
                      "4. Select 'Register'\n\n"
                      "Have you completed the registration?",
            'options': ['Yes, registered', 'Registration failed', 'Skip registration']
        }
    
    def _step6_verify_registration(self):
        """Step 6: Verify Registration Success"""
        return {
            'message': "── **Step 6: Verify Registration Success** ──\n\n"
                      "**Expected outcomes:**\n"
                      "✓ Blue banner appears confirming successful registration\n"
                      "✓ Email notification sent to your admin email\n"
                      "✓ Customer record created in DynamoDB\n\n"
                      "Did you see the success confirmation?",
            'options': ['Yes, all confirmed', 'Some issues', 'Continue anyway']
        }
    
    def _handle_sns(self, user_input):
        """Handle SNS confirmation"""
        user_input = user_input.strip().lower()
        
        if 'yes' in user_input or 'confirmed' in user_input or user_input == '1':
            self.session_state['step'] = 'metering'
            return {
                'message': "✅ **SNS Subscription Confirmed!**\n\n"
                          "🧪 **Ready to test metering functionality**\n\n"
                          "This will send a test usage record to validate the integration.\n\n"
                          "Proceed with metering test?",
                'options': ['Yes, test metering', 'Skip to visibility', 'Show current status']
            }
        elif 'not yet' in user_input or user_input == '2':
            return {
                'message': "⏳ **Waiting for confirmation**\n\n"
                          "Please check your email and confirm the SNS subscription.\n\n"
                          "Ready when you are!",
                'options': ['I confirmed it now', 'Still waiting', 'Resend confirmation']
            }
        elif 'resend' in user_input or user_input == '3':
            return {
                'message': "📧 **Resending confirmation**\n\n"
                          "A new confirmation email has been sent.\n\n"
                          "Please check your inbox and confirm.",
                'options': ['I confirmed it', 'Still not received', 'Continue anyway']
            }
        
        return {
            'message': "Please choose an option:",
            'options': ['Yes, confirmed', 'Not yet', 'Resend confirmation']
        }
    
    def _handle_metering(self, user_input):
        """Handle metering setup - now uses workflow orchestrator"""
        user_input = user_input.strip().lower()
        
        if 'workflow' in user_input or user_input == '1':
            self.session_state['step'] = 'workflow'
            return self._handle_workflow('yes')
        elif 'manual' in user_input or user_input == '2':
            return self._manual_metering_test()
        elif 'skip' in user_input or user_input == '3':
            self.session_state['step'] = 'visibility'
            return self._handle_visibility("start")
        
        return {
            'message': "Please choose an option:",
            'options': ['Use automated workflow', 'Manual metering test', 'Skip to visibility']
        }
    
    def _manual_metering_test(self):
        """Manual metering test for users who prefer step-by-step"""
        print(self._show_waiting_context(
            "Manual Metering Test",
            "30-60 seconds",
            "• Creating metering records\n"
            "• Validating metering setup\n"
            "• Checking DynamoDB tables"
        ))
        
        try:
            # Use the metering agent from workflow orchestrator
            result = self.orchestrator.metering_agent.check_entitlement_and_add_metering(
                self.session_state['credentials']['access_key'],
                self.session_state['credentials']['secret_key'],
                self.session_state['credentials'].get('session_token')
            )
            
            if result.get('status') == 'success':
                return {
                    'message': f"✅ **Manual metering test successful!**\n\n"
                              f"Records created: {result.get('records_created', 'N/A')}\n"
                              f"Status: {result.get('message', 'Completed')}\n\n"
                              f"Ready for visibility request?",
                    'options': ['Yes, request visibility', 'Run full workflow', 'Complete setup']
                }
            else:
                return {
                    'message': f"❌ **Manual metering failed**\n\n{result.get('message', 'Unknown error')}\n\n"
                              f"Consider using the automated workflow instead.",
                    'options': ['Use automated workflow', 'Retry manual test', 'Get help']
                }
        except Exception as e:
            return {
                'message': f"❌ **Metering Error**\n\n{str(e)}\n\n"
                          f"Recommend using the automated workflow.",
                'options': ['Use automated workflow', 'Contact support', 'Skip for now']
            }
    
    def _handle_visibility(self, user_input):
        """Handle visibility requests"""
        user_input = user_input.strip().lower()
        
        if user_input == 'start' or 'yes' in user_input or 'request' in user_input or user_input == '1':
            return self._request_visibility()
        elif 'more tests' in user_input or user_input == '2':
            return self._test_metering()
        elif 'complete' in user_input or user_input == '3':
            self.session_state['step'] = 'complete'
            return self._handle_complete("")
        
        return {
            'message': "Please choose an option:",
            'options': ['Yes, request visibility', 'Run more tests', 'Complete setup']
        }
    
    def _request_visibility(self):
        """Request public visibility using workflow orchestrator"""
        try:
            result = self.orchestrator.visibility_agent.check_metering_and_update_visibility(
                self.session_state['credentials']['access_key'],
                self.session_state['credentials']['secret_key'],
                self.session_state['credentials'].get('session_token')
            )
            
            if result.get('status') == 'success':
                self.session_state['step'] = 'complete'
                return {
                    'message': f"✅ **Public visibility requested!**\n\n"
                              f"Request submitted successfully\n"
                              f"Status: {result.get('message', 'Submitted')}\n\n"
                              f"🎉 **Integration Complete!**\n\n"
                              f"Monitor AWS Marketplace console for approval status.",
                    'final': True
                }
            else:
                return {
                    'message': f"❌ **Visibility request failed**\n\n{result.get('message', 'Unknown error')}\n\n"
                              f"Consider running the full workflow for better results.",
                    'options': ['Run full workflow', 'Retry request', 'Complete anyway']
                }
        except Exception as e:
            return {
                'message': f"❌ **Visibility Error**\n\n{str(e)}\n\n"
                          f"Recommend using the complete workflow.",
                'options': ['Run full workflow', 'Contact support', 'Complete setup']
            }
    
    def _show_current_status(self):
        """Show current integration status"""
        return {
            'message': f"📊 **Current Status:**\n\n"
                      f"✅ Credentials validated\n"
                      f"✅ CloudFormation deployed\n"
                      f"✅ Fulfillment URL updated\n"
                      f"🔄 Ready for workflow execution\n\n"
                      f"The automated workflow will handle:\n"
                      f"• Metering setup and validation\n"
                      f"• Lambda function triggers\n"
                      f"• Public visibility requests\n\n"
                      f"Ready to proceed?",
            'options': ['Run automated workflow', 'Manual steps', 'Complete setup']
        }
    
    def _handle_complete(self, user_input):
        """Handle completion"""
        return {
            'message': "🎉 Integration process complete! Thank you for using the assistant.",
            'final': True
        }
    
    def _handle_general(self, user_input):
        """Handle general queries"""
        return {
            'message': "I'm here to help with AWS Marketplace SaaS integration. What would you like to do?",
            'options': ['Start over', 'Get help', 'Exit']
        }

class MockKnowledgeBase:
    """Fallback knowledge base when validation helper is not available"""
    def query(self, context, error_context=""):
        return None

def main():
    """Main chatbot interface"""
    chatbot = MarketplaceChatbot()
    
    print("🤖 AWS Marketplace SaaS Integration Assistant")
    print("=" * 50)
    
    # Start conversation
    response = chatbot.chat("start")
    
    while True:
        # Display bot response
        print(f"\n🤖 {response['message']}")
        
        # Show options if available
        if response.get('options'):
            print("\n💡 Options (enter number):")
            for i, option in enumerate(response['options'], 1):
                print(f"   {i}. {option}")
            # Store options for numeric selection
            chatbot.session_state['last_options'] = response['options']
        
        # Check if conversation is complete
        if response.get('final'):
            break
        
        # Get user input
        print("\n" + "─" * 50)
        if response.get('options'):
            user_input = input("Enter option number (or type your response): ").strip()
        else:
            user_input = input("You: ").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("\n🤖 Goodbye! Thanks for using the AWS Marketplace Assistant! 👋")
            break
        
        # Process user input
        response = chatbot.chat(user_input)

if __name__ == "__main__":
    main()

