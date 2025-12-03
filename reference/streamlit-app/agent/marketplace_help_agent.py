"""
AWS Marketplace Help Agent - Strands SDK Implementation
Provides contextual help and guidance for AWS Marketplace sellers
"""

import json
import os
from typing import Dict, Any, Optional, List
from strands import Agent, tool


class MarketplaceHelpAgent:
    """
    AWS Marketplace Help Agent using Strands SDK
    
    Provides:
    - AWS Marketplace documentation search
    - Seller registration guidance
    - Product listing help
    - SaaS integration support
    - Pricing model explanations
    - Troubleshooting assistance
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the help agent"""
        self.config = config or {}
        
        # Get model configuration
        model_id = self.config.get('model_id', 'us.anthropic.claude-3-5-sonnet-20241022-v2:0')
        
        # Knowledge base for AWS Marketplace topics
        self.knowledge_base = self._load_knowledge_base()
        
        # Create Strands agent with tools
        self.agent = Agent(
            tools=[
                self._create_search_docs_tool(),
                self._create_get_seller_guide_tool(),
                self._create_get_saas_guide_tool(),
                self._create_get_pricing_guide_tool(),
                self._create_get_troubleshooting_tool(),
            ],
            model=model_id,
            system_prompt=self._get_system_prompt()
        )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the help agent"""
        return """You are an AWS Marketplace Help Assistant. Your role is to help sellers navigate the AWS Marketplace seller journey.

You have access to comprehensive AWS Marketplace documentation and can provide:
- Step-by-step guidance for seller registration
- Product listing creation help
- SaaS integration instructions
- Pricing model explanations
- Troubleshooting assistance

Always:
- Be concise and actionable
- Provide specific steps when possible
- Include relevant documentation links
- Use examples to clarify concepts
- Be encouraging and supportive

When users ask questions:
1. Search the documentation for relevant information
2. Provide clear, structured answers
3. Include links to official AWS documentation
4. Offer next steps or related topics"""
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load AWS Marketplace knowledge base"""
        return {
            "seller_registration": {
                "title": "Seller Registration Process",
                "steps": [
                    "Validate AWS credentials",
                    "Create business profile in AWS Marketplace Management Portal",
                    "Complete tax information (W-9 for US, W-8 for international)",
                    "Set up payment and banking information",
                    "Submit for AWS review (2-3 business days)",
                    "Receive approval notification"
                ],
                "requirements": [
                    "Valid AWS account",
                    "Business information (name, address, EIN/Tax ID)",
                    "Bank account for disbursements",
                    "Tax documentation"
                ],
                "docs_url": "https://docs.aws.amazon.com/marketplace/latest/userguide/seller-registration-process.html"
            },
            "saas_integration": {
                "title": "SaaS Product Integration",
                "overview": "Connect your SaaS product to AWS Marketplace for subscription management and metering",
                "components": [
                    "DynamoDB table for subscription data",
                    "Lambda functions for metering",
                    "API Gateway for fulfillment endpoint",
                    "SNS topics for marketplace notifications"
                ],
                "deployment_steps": [
                    "Deploy CloudFormation stack",
                    "Configure fulfillment URL in product listing",
                    "Implement subscription webhook handler",
                    "Set up usage metering",
                    "Test buyer experience"
                ],
                "docs_url": "https://docs.aws.amazon.com/marketplace/latest/userguide/saas-integrate-saas.html"
            },
            "pricing_models": {
                "title": "AWS Marketplace Pricing Models",
                "models": {
                    "usage_based": {
                        "description": "Pay-as-you-go pricing based on consumption",
                        "best_for": "Variable usage patterns",
                        "examples": ["Per API call", "Per GB", "Per hour"]
                    },
                    "contract": {
                        "description": "Fixed price for a specific term",
                        "best_for": "Predictable costs and commitments",
                        "examples": ["Monthly subscription", "Annual license"]
                    },
                    "hybrid": {
                        "description": "Contract with consumption pricing",
                        "best_for": "Base commitment with overage charges",
                        "examples": ["$500/month + $0.05 per GB over 100GB"]
                    }
                },
                "docs_url": "https://docs.aws.amazon.com/marketplace/latest/userguide/pricing.html"
            },
            "product_listing": {
                "title": "Creating Product Listings",
                "workflow": [
                    "Gather product information",
                    "AI-assisted content generation",
                    "Review and edit suggestions",
                    "Create listing in AWS Marketplace",
                    "Configure SaaS integration (if applicable)",
                    "Test buyer experience",
                    "Request public visibility"
                ],
                "required_info": [
                    "Product name and description",
                    "Product logo (PNG, 110x110px minimum)",
                    "Product URLs (website, documentation)",
                    "Pricing dimensions",
                    "Support information",
                    "EULA or terms of service"
                ],
                "docs_url": "https://docs.aws.amazon.com/marketplace/latest/userguide/product-preparation.html"
            }
        }
    
    def _create_search_docs_tool(self):
        """Create tool for searching AWS Marketplace documentation"""
        knowledge_base = self.knowledge_base
        
        @tool
        def search_documentation(query: str) -> dict:
            """
            Search AWS Marketplace documentation for relevant information.
            
            Args:
                query: Search query or topic (e.g., "seller registration", "saas integration")
            
            Returns:
                Dictionary with relevant documentation and links
            """
            query_lower = query.lower()
            results = []
            
            # Search knowledge base
            for topic_key, topic_data in knowledge_base.items():
                if any(keyword in query_lower for keyword in topic_key.split('_')):
                    results.append({
                        "topic": topic_data.get("title", topic_key),
                        "content": topic_data,
                        "relevance": "high"
                    })
            
            if not results:
                # Return general help
                results.append({
                    "topic": "General AWS Marketplace Help",
                    "content": {
                        "message": "I can help with seller registration, product listings, SaaS integration, and pricing models.",
                        "docs_url": "https://docs.aws.amazon.com/marketplace/latest/userguide/"
                    },
                    "relevance": "medium"
                })
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results)
            }
        
        return search_documentation
    
    def _create_get_seller_guide_tool(self):
        """Create tool for getting seller registration guide"""
        knowledge_base = self.knowledge_base
        
        @tool
        def get_seller_registration_guide() -> dict:
            """
            Get comprehensive guide for AWS Marketplace seller registration.
            
            Returns:
                Dictionary with registration steps, requirements, and documentation links
            """
            return {
                "success": True,
                "guide": knowledge_base["seller_registration"]
            }
        
        return get_seller_registration_guide
    
    def _create_get_saas_guide_tool(self):
        """Create tool for getting SaaS integration guide"""
        knowledge_base = self.knowledge_base
        
        @tool
        def get_saas_integration_guide() -> dict:
            """
            Get comprehensive guide for SaaS product integration with AWS Marketplace.
            
            Returns:
                Dictionary with integration steps, architecture, and documentation links
            """
            return {
                "success": True,
                "guide": knowledge_base["saas_integration"]
            }
        
        return get_saas_integration_guide
    
    def _create_get_pricing_guide_tool(self):
        """Create tool for getting pricing models guide"""
        knowledge_base = self.knowledge_base
        
        @tool
        def get_pricing_models_guide() -> dict:
            """
            Get comprehensive guide for AWS Marketplace pricing models.
            
            Returns:
                Dictionary with pricing model descriptions and examples
            """
            return {
                "success": True,
                "guide": knowledge_base["pricing_models"]
            }
        
        return get_pricing_models_guide
    
    def _create_get_troubleshooting_tool(self):
        """Create tool for troubleshooting common issues"""
        
        @tool
        def get_troubleshooting_help(issue: str) -> dict:
            """
            Get troubleshooting help for common AWS Marketplace issues.
            
            Args:
                issue: Description of the issue or error
            
            Returns:
                Dictionary with troubleshooting steps and solutions
            """
            issue_lower = issue.lower()
            
            troubleshooting = {
                "issue": issue,
                "solutions": []
            }
            
            # Common issues and solutions
            if "credential" in issue_lower or "access" in issue_lower:
                troubleshooting["solutions"].append({
                    "problem": "Credential or Access Issues",
                    "steps": [
                        "Verify AWS credentials are valid and not expired",
                        "Check IAM permissions include AWSMarketplaceFullAccess",
                        "Ensure session token is included if using temporary credentials",
                        "Try re-validating credentials on the home page"
                    ]
                })
            
            if "seller" in issue_lower and ("not registered" in issue_lower or "registration" in issue_lower):
                troubleshooting["solutions"].append({
                    "problem": "Seller Not Registered",
                    "steps": [
                        "Complete seller registration in AWS Marketplace Management Portal",
                        "Submit tax information (W-9 or W-8)",
                        "Configure banking information",
                        "Wait for AWS approval (2-3 business days)",
                        "Re-validate credentials after approval"
                    ]
                })
            
            if "saas" in issue_lower or "integration" in issue_lower:
                troubleshooting["solutions"].append({
                    "problem": "SaaS Integration Issues",
                    "steps": [
                        "Verify CloudFormation stack deployed successfully",
                        "Check fulfillment URL is correctly configured",
                        "Ensure Lambda functions have proper IAM permissions",
                        "Test subscription webhook endpoint",
                        "Review CloudWatch logs for errors"
                    ]
                })
            
            if "listing" in issue_lower or "product" in issue_lower:
                troubleshooting["solutions"].append({
                    "problem": "Product Listing Issues",
                    "steps": [
                        "Verify all required fields are completed",
                        "Check product logo meets size requirements (110x110px minimum)",
                        "Ensure pricing dimensions are properly configured",
                        "Validate EULA URL is accessible",
                        "Review product for AWS Marketplace policy compliance"
                    ]
                })
            
            if not troubleshooting["solutions"]:
                troubleshooting["solutions"].append({
                    "problem": "General Troubleshooting",
                    "steps": [
                        "Check AWS Service Health Dashboard for outages",
                        "Review CloudWatch logs for detailed error messages",
                        "Verify all AWS services are available in your region",
                        "Contact AWS Marketplace Seller Support if issue persists"
                    ],
                    "support_url": "https://aws.amazon.com/marketplace/management/contact-us"
                })
            
            return {
                "success": True,
                "troubleshooting": troubleshooting
            }
        
        return get_troubleshooting_help
    
    async def chat(self, message: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Process a chat message and return a response.
        
        Args:
            message: User's message
            conversation_history: Optional conversation history
        
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Build conversation context
            messages = conversation_history or []
            messages.append({"role": "user", "content": message})
            
            # Get response from Strands agent
            response = await self.agent.run(message)
            
            return {
                "success": True,
                "response": response.content if hasattr(response, 'content') else str(response),
                "sources": [],
                "conversation_id": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I encountered an error processing your request. Please try rephrasing your question."
            }
    
    def get_quick_help_topics(self) -> List[Dict[str, str]]:
        """Get list of quick help topics"""
        return [
            {
                "title": "Seller Registration",
                "description": "How to register as an AWS Marketplace seller",
                "query": "How do I register as a seller?"
            },
            {
                "title": "Create Product Listing",
                "description": "Steps to create a product listing",
                "query": "How do I create a product listing?"
            },
            {
                "title": "SaaS Integration",
                "description": "Integrate SaaS product with AWS Marketplace",
                "query": "How do I integrate my SaaS product?"
            },
            {
                "title": "Pricing Models",
                "description": "Understanding AWS Marketplace pricing",
                "query": "What pricing models are available?"
            },
            {
                "title": "Troubleshooting",
                "description": "Common issues and solutions",
                "query": "Help me troubleshoot an issue"
            }
        ]
