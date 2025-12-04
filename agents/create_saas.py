from strands import Agent

class CreateSaasAgent(Agent):
    def __init__(self):
        super().__init__(name="CreateSaas")
    
    def get_product_id(self):
        return "prod-ebsllm6bj3ccm" \
        ""
    
    def get_aws_account_id(self):
        return "605345174368"
    
    def get_pricing_model_dimension(self):
        return "Usage-based-pricing"
    
    def get_email_dimension(self):
        return "jain.manasvi1999@gmail.com"
    
    def get_usage_dimensions(self):
        return ["dimension_1_id"]