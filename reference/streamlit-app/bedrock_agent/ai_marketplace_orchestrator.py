from strands import Agent, tool
import boto3
import json
try:
    from ..agents.serverless_saas_integration import ServerlessSaasIntegrationAgent
    from ..agents.metering import MeteringAgent
    from ..agents.public_visibility import PublicVisibilityAgent
    from ..agents.validation_helper import ValidationHelperAgent
except ImportError:
    from serverless_saas_integration import ServerlessSaasIntegrationAgent
    from metering import MeteringAgent
    from public_visibility import PublicVisibilityAgent
    from validation_helper import ValidationHelperAgent

class AIMarketplaceOrchestrator(Agent):
    def __init__(self, strands_agent=None):
        super().__init__(name="AIMarketplaceOrchestrator")
        self.bedrock_client = boto3.client('bedrock-runtime')
        self.bedrock_agent_client = boto3.client('bedrock-agent-runtime')
        self.knowledge_base_id = "marketplace-kb-id"  # Replace with actual KB ID
        self.strands_agent = strands_agent
        
        # Initialize all available agents
        self.agents = {
            'deployment': ServerlessSaasIntegrationAgent(strands_agent=strands_agent),
            'metering': MeteringAgent(),
            'visibility': PublicVisibilityAgent(),
            'validation': ValidationHelperAgent()
        }
        
        # Workflow state tracking
        self.workflow_state = {
            'current_step': 'start',
            'completed_steps': [],
            'user_credentials': None,
            'errors': []
        }
    
    @tool
    def guide_user_workflow(self, user_input, access_key=None, secret_key=None, session_token=None):
        """Main orchestrator that guides users through complete marketplace integration"""
        
        # Store credentials for agent operations
        if access_key and secret_key:
            self.workflow_state['user_credentials'] = {
                'access_key': access_key,
                'secret_key': secret_key,
                'session_token': session_token
            }
        
        # Use LLM to understand user intent
        intent = self._analyze_user_intent(user_input)
        
        # Query Knowledge Base for relevant guidance
        guidance = self._get_contextual_guidance(user_input, intent)
        
        # Coordinate appropriate agents based on intent
        result = self._execute_workflow_step(intent)
        
        # Provide natural language response
        response = self._generate_natural_response(intent, result, guidance)
        
        return {
            'response': response,
            'current_step': self.workflow_state['current_step'],
            'completed_steps': self.workflow_state['completed_steps'],
            'next_actions': self._get_next_actions(),
            'result': result
        }
    
    def _analyze_user_intent(self, user_input):
        """Use Bedrock LLM to understand what the user wants to do"""
        prompt = f"""
        Analyze this user input for AWS Marketplace SaaS integration intent:
        "{user_input}"
        
        Classify the intent as one of:
        - start_deployment: User wants to deploy SaaS integration
        - check_metering: User wants to test metering functionality  
        - update_visibility: User wants to make product public
        - troubleshoot: User has an error or issue
        - get_status: User wants to check current progress
        - help: User needs general guidance
        
        Respond with just the classification.
        """
        
        try:
            response = self.bedrock_client.converse(
                modelId="us.amazon.nova-pro-v1:0",
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={"maxTokens": 50, "temperature": 0.1}
            )
            return response['output']['message']['content'][0]['text'].strip()
        except:
            return "help"  # Default fallback
    
    def _get_contextual_guidance(self, user_input, intent):
        """Query Knowledge Base for relevant guidance"""
        query = f"AWS Marketplace SaaS integration guidance for: {intent}. User question: {user_input}"
        
        try:
            response = self.bedrock_agent_client.retrieve_and_generate(
                input={'text': query},
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': self.knowledge_base_id,
                        'modelArn': 'arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0'
                    }
                }
            )
            return response['output']['text']
        except:
            return "No specific guidance available."
    
    def _execute_workflow_step(self, intent):
        """Execute the appropriate workflow step based on intent"""
        creds = self.workflow_state.get('user_credentials')
        
        try:
            if intent == "start_deployment":
                if not creds:
                    return {"error": "AWS credentials required for deployment"}
                result = self.agents['deployment'].deploy_integration(
                    creds['access_key'], creds['secret_key'], creds['session_token']
                )
                if 'error' not in result:
                    self.workflow_state['completed_steps'].append('deployment')
                    self.workflow_state['current_step'] = 'metering'
                return result
                
            elif intent == "check_metering":
                if not creds:
                    return {"error": "AWS credentials required for metering check"}
                result = self.agents['metering'].check_entitlement_and_add_metering(
                    creds['access_key'], creds['secret_key'], creds['session_token']
                )
                if result.get('status') == 'success':
                    self.workflow_state['completed_steps'].append('metering')
                    self.workflow_state['current_step'] = 'visibility'
                return result
                
            elif intent == "update_visibility":
                if not creds:
                    return {"error": "AWS credentials required for visibility update"}
                result = self.agents['visibility'].check_metering_and_update_visibility(
                    creds['access_key'], creds['secret_key'], creds['session_token']
                )
                if result.get('status') == 'success':
                    self.workflow_state['completed_steps'].append('visibility')
                    self.workflow_state['current_step'] = 'complete'
                return result
                
            elif intent == "get_status":
                status = {
                    'current_step': self.workflow_state['current_step'],
                    'completed_steps': self.workflow_state['completed_steps']
                }
                
                if self.strands_agent:
                    status['product_id'] = self.strands_agent.orchestrator.product_id
                    pricing_data = self.strands_agent.orchestrator.all_data.get('PRICING_CONFIG', {})
                    status['pricing_model'] = pricing_data.get('pricing_model', 'Usage-based-pricing')
                    status['listing_complete'] = self.strands_agent.orchestrator.current_stage.value > 8
                
                return status
                
            else:  # help, troubleshoot, or unknown
                return {"message": "I can help you with AWS Marketplace SaaS integration. What would you like to do?"}
                
        except Exception as e:
            error_msg = str(e)
            self.workflow_state['errors'].append(error_msg)
            return {"error": error_msg}
    
    def _generate_natural_response(self, intent, result, guidance):
        """Generate natural language response using LLM"""
        prompt = f"""
        Generate a helpful response for AWS Marketplace SaaS integration:
        
        User Intent: {intent}
        Operation Result: {json.dumps(result, default=str)[:500]}
        Knowledge Base Guidance: {guidance[:300]}
        
        Provide a clear, helpful response that:
        1. Explains what happened
        2. Gives next steps if successful
        3. Provides troubleshooting if there was an error
        4. Uses friendly, professional tone
        
        Keep response under 200 words.
        """
        
        try:
            response = self.bedrock_client.converse(
                modelId="us.amazon.nova-pro-v1:0",
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={"maxTokens": 300, "temperature": 0.3}
            )
            return response['output']['message']['content'][0]['text']
        except:
            return f"Operation completed with result: {result.get('status', 'unknown')}"
    
    def _get_next_actions(self):
        """Suggest next actions based on current workflow state"""
        current_step = self.workflow_state['current_step']
        
        actions = {
            'start': ['Deploy SaaS integration template'],
            'deployment': ['Confirm SNS subscription', 'Test metering functionality'],
            'metering': ['Check metering records', 'Update product visibility'],
            'visibility': ['Monitor visibility request status'],
            'complete': ['Integration complete - monitor marketplace notifications']
        }
        
        return actions.get(current_step, ['Ask for help if needed'])

if __name__ == "__main__":
    orchestrator = AIMarketplaceOrchestrator()
    
    print("🤖 AWS Marketplace SaaS Integration Assistant")
    print("I can help you deploy, test, and publish your SaaS integration.")
    print("=" * 60)
    
    # Get credentials once
    access_key = input("Enter AWS Access Key: ")
    secret_key = input("Enter AWS Secret Key: ")
    session_token = input("Enter Session Token (optional): ") or None
    
    print("\n✅ Credentials stored. You can now ask me anything!")
    print("Examples:")
    print("- 'Deploy my SaaS integration'")
    print("- 'Test metering functionality'") 
    print("- 'Make my product public'")
    print("- 'What's my current status?'")
    
    while True:
        user_input = input("\n💬 What would you like to do? (or 'quit' to exit): ")
        if user_input.lower() == 'quit':
            break
            
        result = orchestrator.guide_user_workflow(
            user_input, access_key, secret_key, session_token
        )
        
        print(f"\n🤖 {result['response']}")
        
        if result.get('next_actions'):
            print(f"\n📋 Suggested next actions:")
            for action in result['next_actions']:
                print(f"   • {action}")
        
        if result.get('current_step'):
            print(f"\n📍 Current step: {result['current_step']}")
            print(f"✅ Completed: {', '.join(result['completed_steps']) if result['completed_steps'] else 'None'}")