"""
Amazon Bedrock AI tools for product analysis and content generation
"""

import boto3
import json
from typing import Dict, Any

def analyze_product(
    session: boto3.Session,
    product_name: str,
    product_website: str,
    product_description: str,
    documentation_url: str = None
) -> Dict[str, Any]:
    """
    Analyze product using Amazon Bedrock Claude 3.5 Sonnet
    
    Args:
        session: Boto3 session with valid credentials
        product_name: Name of the product
        product_website: Product website URL
        product_description: Brief product description
        documentation_url: Optional documentation URL
    
    Returns:
        Dict with AI-generated product analysis
    """
    try:
        bedrock = session.client('bedrock-runtime')
        
        prompt = f"""Analyze this product for AWS Marketplace listing:

Product Name: {product_name}
Website: {product_website}
Description: {product_description}
{f'Documentation: {documentation_url}' if documentation_url else ''}

Provide a comprehensive analysis including:
1. Key features and capabilities
2. Target audience and use cases
3. Competitive advantages
4. Technical requirements
5. Integration points with AWS services

Format the response as JSON with these keys: features, target_audience, advantages, requirements, aws_integrations"""

        response = bedrock.invoke_model(
            modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )
        
        result = json.loads(response['body'].read())
        analysis_text = result['content'][0]['text']
        
        # Try to parse as JSON, fallback to text
        try:
            analysis = json.loads(analysis_text)
        except:
            analysis = {"raw_analysis": analysis_text}
        
        return {
            "success": True,
            "analysis": analysis
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def generate_listing_content(
    session: boto3.Session,
    product_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate listing content (title, description, highlights) using AI
    
    Args:
        session: Boto3 session with valid credentials
        product_analysis: Product analysis from analyze_product()
    
    Returns:
        Dict with generated listing content
    """
    try:
        bedrock = session.client('bedrock-runtime')
        
        prompt = f"""Based on this product analysis, generate AWS Marketplace listing content:

{json.dumps(product_analysis, indent=2)}

Generate:
1. A compelling product title (max 50 characters)
2. A short description (max 200 characters)
3. A long description (max 5000 characters)
4. 3-5 key highlights/bullet points

Format as JSON with keys: title, short_description, long_description, highlights"""

        response = bedrock.invoke_model(
            modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 3000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )
        
        result = json.loads(response['body'].read())
        content_text = result['content'][0]['text']
        
        try:
            content = json.loads(content_text)
        except:
            content = {"raw_content": content_text}
        
        return {
            "success": True,
            "content": content
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def suggest_pricing_model(
    session: boto3.Session,
    product_type: str,
    product_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Suggest pricing model and dimensions using AI
    
    Args:
        session: Boto3 session with valid credentials
        product_type: Type of product (SaaS, AMI, Container, etc.)
        product_analysis: Product analysis data
    
    Returns:
        Dict with pricing recommendations
    """
    try:
        bedrock = session.client('bedrock-runtime')
        
        prompt = f"""Suggest a pricing model for this AWS Marketplace {product_type} product:

{json.dumps(product_analysis, indent=2)}

Recommend:
1. Pricing model (subscription, usage-based, contract, etc.)
2. Pricing dimensions (users, API calls, data processed, etc.)
3. Suggested price points
4. Contract durations (if applicable)

Format as JSON with keys: model, dimensions, price_points, contract_durations"""

        response = bedrock.invoke_model(
            modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )
        
        result = json.loads(response['body'].read())
        pricing_text = result['content'][0]['text']
        
        try:
            pricing = json.loads(pricing_text)
        except:
            pricing = {"raw_pricing": pricing_text}
        
        return {
            "success": True,
            "pricing": pricing
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def optimize_content(
    session: boto3.Session,
    content: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Optimize listing content for SEO and marketplace best practices
    
    Args:
        session: Boto3 session with valid credentials
        content: Listing content to optimize
    
    Returns:
        Dict with optimized content
    """
    try:
        bedrock = session.client('bedrock-runtime')
        
        prompt = f"""Optimize this AWS Marketplace listing content for SEO and best practices:

{json.dumps(content, indent=2)}

Improve:
1. Keyword optimization
2. Clarity and readability
3. Call-to-action effectiveness
4. Compliance with AWS Marketplace guidelines

Return the optimized version in the same JSON format."""

        response = bedrock.invoke_model(
            modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 3000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )
        
        result = json.loads(response['body'].read())
        optimized_text = result['content'][0]['text']
        
        try:
            optimized = json.loads(optimized_text)
        except:
            optimized = {"raw_optimized": optimized_text}
        
        return {
            "success": True,
            "optimized_content": optimized
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
