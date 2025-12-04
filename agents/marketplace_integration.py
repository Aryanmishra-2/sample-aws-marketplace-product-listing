from strands import Agent, tool
import boto3
import json

class MarketplaceIntegrationAgent(Agent):
    def __init__(self):
        super().__init__(name="MarketplaceIntegration")
        self.marketplace_client = boto3.client('meteringmarketplace')
    
    @tool
    def resolve_customer_token(self, registration_token):
        """Resolve customer information from marketplace token"""
        response = self.marketplace_client.resolve_customer(
            RegistrationToken=registration_token
        )
        return {
            'customer_identifier': response['CustomerIdentifier'],
            'product_code': response['ProductCode'],
            'customer_aws_account_id': response.get('CustomerAWSAccountId')
        }
    
    @tool
    def get_entitlements(self, customer_identifier, product_code):
        """Get customer entitlements from marketplace"""
        entitlement_client = boto3.client('marketplaceentitlement')
        response = entitlement_client.get_entitlements(
            ProductCode=product_code,
            Filter={
                'CUSTOMER_IDENTIFIER': [customer_identifier]
            }
        )
        return response['Entitlements']
    
    @tool
    def deploy_for_marketplace_customer(self, registration_token):
        """Deploy infrastructure after marketplace authentication"""
        # Resolve customer from token
        customer_info = self.resolve_customer_token(registration_token)
        
        # Get entitlements
        entitlements = self.get_entitlements(
            customer_info['customer_identifier'],
            customer_info['product_code']
        )
        
        # Deploy CloudFormation in customer account
        # Customer grants permissions through marketplace subscription
        cf_client = boto3.client('cloudformation', region_name='us-east-1')
        
        with open('../bedrock_agent/Integration.yaml', 'r') as f:
            template = f.read()
        
        response = cf_client.create_stack(
            StackName=f"marketplace-saas-{customer_info['customer_identifier']}",
            TemplateBody=template,
            Parameters=[
                {'ParameterKey': 'ProductId', 'ParameterValue': customer_info['product_code']},
                {'ParameterKey': 'AWSAccountId', 'ParameterValue': customer_info['customer_aws_account_id']},
                {'ParameterKey': 'PricingModel', 'ParameterValue': 'Contract-based-pricing'},
                {'ParameterKey': 'MarketplaceTechAdminEmail', 'ParameterValue': 'admin@example.com'}
            ],
            Capabilities=['CAPABILITY_IAM']
        )
        
        return {
            'stack_id': response['StackId'],
            'customer_id': customer_info['customer_identifier'],
            'entitlements': entitlements
        }