# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from strands import Agent, tool
import boto3
import json

class ValidationHelperAgent(Agent):
    def __init__(self):
        super().__init__(name="ValidationHelper")
        self.bedrock = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        self.knowledge_base_id = "YOUR_KB_ID"  # Replace with actual KB ID
    
    @tool
    def validate_and_guide(self, field_name, user_input, error_message=None):
        """Validate input and provide guidance using Knowledge Base"""
        
        # Query Knowledge Base for guidance
        query = f"What are the valid values and requirements for {field_name} in AWS Marketplace? Error: {error_message}"
        
        response = self.bedrock.retrieve_and_generate(
            input={'text': query},
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': self.knowledge_base_id,
                    'modelArn': 'arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0'
                }
            }
        )
        
        guidance = response['output']['text']
        
        return {
            "valid": self._validate_input(field_name, user_input),
            "guidance": guidance,
            "suggested_format": self._get_format_example(field_name)
        }
    
    def _validate_input(self, field_name, value):
        """Basic validation rules"""
        validations = {
            "product_id": lambda x: x.startswith("prod-") and len(x) > 10,
            "pricing": lambda x: x.replace(".", "").isdigit() and float(x) > 0,
            "email": lambda x: "@" in x and "." in x
        }
        return validations.get(field_name, lambda x: True)(value)
    
    def _get_format_example(self, field_name):
        """Provide format examples"""
        examples = {
            "product_id": "prod-a2lcytlwv2acq",
            "pricing": "10.00",
            "email": "admin@example.com"
        }
        return examples.get(field_name, "No example available")