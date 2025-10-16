from strands import Agent, tool
import boto3
import time
from create_saas import CreateSaasAgent
from metering import MeteringAgent

class ServerlessSaasIntegrationAgent(Agent):
    def __init__(self):
        super().__init__(name="ServerlessSaasIntegration")
        self.create_saas_agent = CreateSaasAgent()
        self.metering_agent = MeteringAgent()
    
    @tool
    def deploy_integration(self, access_key, secret_key, session_token=None):
        """Deploy integration using customer's temporary AWS credentials"""
        # Get data from create_saas agent
        product_id = self.create_saas_agent.get_product_id()
        pricing_model = self.create_saas_agent.get_pricing_model_dimension()
        email_id = self.create_saas_agent.get_email_dimension()
        
        # Create CloudFormation client with customer credentials
        cf_client = boto3.client(
            'cloudformation',
            region_name='us-east-1',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token
        )
        
        # Read and deploy template
        with open('Integration.yaml', 'r') as f:
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
        
        # Wait 15 minutes before invoking metering for pricing models that require it
        if pricing_model in ["Contract-with-consumption", "Usage-based-pricing"]:
            print(f"Stack deployed: {stack_id}")
            print("Waiting 15 minutes before setting up metering...")
            time.sleep(900)  # 15 minutes = 900 seconds
            
            metering_result = self.metering_agent.check_entitlement_and_add_metering(
                access_key, secret_key, session_token
            )
            return {
                'stack_id': stack_id,
                'metering_result': metering_result
            }
        
        return stack_id

if __name__ == "__main__":
    agent = ServerlessSaasIntegrationAgent()
    
    # Customer provides temporary credentials
    access_key = input("Enter AWS Access Key: ")
    secret_key = input("Enter AWS Secret Key: ")
    session_token = input("Enter Session Token (optional): ") or None
    
    stack_id = agent.deploy_integration(access_key, secret_key, session_token)
    print(f"Deployed stack: {stack_id}")