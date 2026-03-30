# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Tools for querying AWS Amazon Bedrock Knowledge Base"""

import boto3
from typing import Dict, Any, List


class KnowledgeBaseTools:
    """AWS Amazon Bedrock Knowledge Base query tools"""
    
    def __init__(self, knowledge_base_id: str, region: str = "us-east-1"):
        # Use bedrock-agent-runtime for knowledge base operations
        self.kb_client = boto3.client('bedrock-agent-runtime', region_name=region)
        self.knowledge_base_id = knowledge_base_id
        self.region = region
    
    def query_knowledge_base(
        self,
        query: str,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Query the AWS Marketplace documentation knowledge base
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            Dict with search results
        """
        try:
            response = self.kb_client.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={
                    'text': query
                },
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': max_results
                    }
                }
            )
            
            results = []
            for item in response.get('retrievalResults', []):
                results.append({
                    'content': item['content']['text'],
                    'score': item.get('score', 0),
                    'location': item.get('location', {})
                })
            
            return {
                "success": True,
                "results": results,
                "count": len(results)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def get_pricing_guidance(self) -> Dict[str, Any]:
        """Get guidance on AWS Marketplace pricing models"""
        return self.query_knowledge_base(
            "AWS Marketplace SaaS pricing models subscription contract dimensions"
        )
    
    def get_integration_guidance(self) -> Dict[str, Any]:
        """Get guidance on SaaS integration requirements"""
        return self.query_knowledge_base(
            "AWS Marketplace SaaS integration fulfillment redirect URL requirements"
        )
    
    def get_listing_requirements(self) -> Dict[str, Any]:
        """Get requirements for creating a SaaS listing"""
        return self.query_knowledge_base(
            "AWS Marketplace SaaS listing requirements product information categories"
        )
