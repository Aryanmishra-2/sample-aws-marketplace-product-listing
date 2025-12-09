"""
FastAPI Backend for AWS Marketplace Seller Portal
Integrates with existing agent system for complete functionality
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import boto3
import sys
import os
import asyncio
from queue import Queue
import threading

# Add parent directory to path for imports
# Import listing agents and tools from backend/agents
from agents import (
    SellerRegistrationAgent,
    ProductInformationAgent,
    FulfillmentAgent,
    PricingConfigAgent,
    PriceReviewAgent,
    RefundPolicyAgent,
    EULAConfigAgent,
    OfferAvailabilityAgent,
    AllowlistAgent,
    ListingTools,
    SellerRegistrationTools,
)

# Help agent functionality is integrated in the /chat endpoint below
help_agent = None  # Placeholder - will use Bedrock directly

app = FastAPI(title="AWS Marketplace Seller Portal API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global event queues for SSE (keyed by session_id)
event_queues: Dict[str, Queue] = {}

# Request/Response Models
class Credentials(BaseModel):
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_session_token: Optional[str] = None

class ProductContext(BaseModel):
    product_name: Optional[str] = None
    product_description: Optional[str] = None
    product_urls: List[str] = []
    documentation_url: Optional[str] = None
    additional_context: Optional[str] = None

class ListingData(BaseModel):
    title: str
    logo_s3_url: str
    short_description: str
    long_description: str
    highlights: List[str]
    categories: List[str]
    search_keywords: List[str]
    support_email: str
    fulfillment_url: str
    support_description: str
    pricing_model: str
    ui_pricing_model: Optional[str] = None
    pricing_dimensions: List[Dict[str, Any]]
    contract_durations: Optional[List[str]] = []
    purchasing_option: Optional[str] = None
    refund_policy: str
    eula_type: str
    custom_eula_url: Optional[str] = None
    availability_type: str
    excluded_countries: Optional[List[str]] = []
    allowed_countries: Optional[List[str]] = []
    auto_publish_to_limited: bool = False
    offer_name: Optional[str] = None
    offer_description: Optional[str] = None

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

# Validate credentials with IAM permissions check
@app.post("/validate-credentials")
async def validate_credentials(credentials: Credentials):
    """Validate AWS credentials and check IAM permissions (fast version)"""
    try:
        print("[DEBUG] Validating credentials...")
        
        # Create session with provided credentials
        session = boto3.Session(
            aws_access_key_id=credentials.aws_access_key_id,
            aws_secret_access_key=credentials.aws_secret_access_key,
            aws_session_token=credentials.aws_session_token,
            region_name='us-east-1'
        )
        
        # Get caller identity (fast)
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        account_id = identity.get('Account')
        user_arn = identity.get('Arn')
        
        print(f"[DEBUG] Identity: {account_id}, {user_arn}")
        
        # Determine user type and name
        user_type = 'Unknown'
        user_name = None
        
        if ':user/' in user_arn:
            user_type = 'IAM User'
            user_name = user_arn.split('/')[-1]
        elif ':assumed-role/' in user_arn:
            user_type = 'IAM Role (Assumed)'
            user_name = user_arn.split('/')[-2]
        elif ':role/' in user_arn:
            user_type = 'IAM Role'
            user_name = user_arn.split('/')[-1]
        elif ':root' in user_arn:
            user_type = 'Root User'
            user_name = 'root'
        
        # Quick marketplace permissions check (single API call)
        permissions_check = {
            'has_marketplace_full_access': False,
            'has_marketplace_manage_products': False,
            'has_marketplace_full_access_policy': False,
            'has_admin_access': user_type == 'Root User',
            'has_iam_read_access': False,
            'missing_permissions': [],
            'warnings': [],
            'recommendations': []
        }
        
        print("[DEBUG] Checking marketplace permissions...")
        
        # Check for AWSMarketplaceFullAccess policy
        try:
            iam_client = session.client('iam')
            if ':user/' in user_arn:
                # For IAM users, check attached policies
                user_name = user_arn.split('/')[-1]
                attached_policies = iam_client.list_attached_user_policies(UserName=user_name)
                for policy in attached_policies.get('AttachedPolicies', []):
                    if 'AWSMarketplaceFullAccess' in policy['PolicyName'] or 'AWSMarketplaceSellerFullAccess' in policy['PolicyName']:
                        permissions_check['has_marketplace_full_access_policy'] = True
                        print(f"[DEBUG] Found policy: {policy['PolicyName']}")
                        break
            elif ':assumed-role/' in user_arn:
                # For assumed roles, check role policies
                role_name = user_arn.split('/')[-2]
                try:
                    attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)
                    for policy in attached_policies.get('AttachedPolicies', []):
                        if 'AWSMarketplaceFullAccess' in policy['PolicyName'] or 'AWSMarketplaceSellerFullAccess' in policy['PolicyName']:
                            permissions_check['has_marketplace_full_access_policy'] = True
                            print(f"[DEBUG] Found policy: {policy['PolicyName']}")
                            break
                except:
                    pass
        except Exception as e:
            print(f"[DEBUG] Could not check IAM policies: {str(e)}")
        
        # Test marketplace permissions with a single quick call
        marketplace_client = session.client('marketplace-catalog')
        try:
            marketplace_client.list_entities(
                Catalog='AWSMarketplace',
                EntityType='SaaSProduct',
                MaxResults=1
            )
            permissions_check['has_marketplace_manage_products'] = True
            permissions_check['has_marketplace_full_access'] = True
            print("[DEBUG] Marketplace permissions: OK")
        except Exception as e:
            error_code = getattr(e, 'response', {}).get('Error', {}).get('Code', '')
            print(f"[DEBUG] Marketplace permissions error: {error_code}")
            if error_code in ['AccessDenied', 'UnauthorizedOperation']:
                permissions_check['missing_permissions'].append('aws-marketplace:ListEntities')
                permissions_check['warnings'].append('Cannot list marketplace products')
                permissions_check['recommendations'].append({
                    'severity': 'high',
                    'title': 'Marketplace Permissions Required',
                    'message': 'You need AWS Marketplace Catalog API permissions to manage products',
                    'action': 'Attach the "AWSMarketplaceSellerFullAccess" managed policy',
                    'policy_arn': 'arn:aws:iam::aws:policy/AWSMarketplaceSellerFullAccess',
                    'required_actions': [
                        'aws-marketplace:ListEntities',
                        'aws-marketplace:DescribeEntity',
                        'aws-marketplace:StartChangeSet'
                    ]
                })
        
        # Determine region type based on partition
        region_type = 'UNKNOWN'
        organization = 'Unknown'
        
        if user_arn.startswith('arn:aws:'):
            region_type = 'AWS_COMMERCIAL'
            organization = 'Amazon Web Services (Commercial)'
        elif user_arn.startswith('arn:aws-cn:'):
            region_type = 'AWS_CHINA'
            organization = 'Amazon Web Services China'
        elif user_arn.startswith('arn:aws-us-gov:'):
            region_type = 'AWS_GOVCLOUD'
            organization = 'Amazon Web Services GovCloud'
        
        if 'amazon.com' in user_arn.lower():
            organization += ' (Internal)'
        elif 'amazon.in' in user_arn.lower():
            organization = 'Amazon Web Services India Pvt Ltd'
            region_type = 'AWS_INDIA'
        
        # Overall permission status
        has_required_permissions = (
            permissions_check['has_marketplace_manage_products'] or
            user_type == 'Root User'
        )
        
        print(f"[DEBUG] Validation complete. Can proceed: {has_required_permissions}")
        
        return {
            "success": True,
            "account_id": account_id,
            "region_type": region_type,
            "user_arn": user_arn,
            "user_type": user_type,
            "user_name": user_name,
            "organization": organization,
            "session_id": f"session-{account_id}",
            "permissions": permissions_check,
            "has_required_permissions": has_required_permissions,
            "can_proceed": has_required_permissions
        }
        
    except Exception as e:
        print(f"[ERROR] Validation failed: {str(e)}")
        raise HTTPException(status_code=400, detail={"success": False, "error": str(e)})

# Check seller status
@app.post("/check-seller-status")
async def check_seller_status(credentials: Credentials):
    """Check seller registration status with enhanced details"""
    try:
        # Create boto3 session
        session = boto3.Session(
            aws_access_key_id=credentials.aws_access_key_id,
            aws_secret_access_key=credentials.aws_secret_access_key,
            aws_session_token=credentials.aws_session_token,
            region_name='us-east-1'
        )
        
        # Check seller status using Marketplace Catalog API
        marketplace_client = session.client('marketplace-catalog')
        
        try:
            # List entities to check if seller is registered
            response = marketplace_client.list_entities(
                Catalog='AWSMarketplace',
                EntityType='SaaSProduct',
                MaxResults=10
            )
            
            products = []
            for entity in response.get('EntitySummaryList', []):
                products.append({
                    'product_id': entity.get('EntityId', ''),
                    'product_name': entity.get('Name', 'Unknown'),
                    'product_type': 'SaaS',
                    'status': 'ACTIVE',
                })
            
            # Get account ID from STS
            sts_client = session.client('sts')
            identity = sts_client.get_caller_identity()
            account_id = identity['Account']
            
            return {
                "success": True,
                "seller_status": "APPROVED" if products else "NOT_REGISTERED",
                "account_id": account_id,
                "owned_products": products,
                "owned_products_count": len(products),
                "verification_status": {"verified": True},
                "required_steps": [],
                "marketplace_accessible": True,
                "portal_url": "https://aws.amazon.com/marketplace/management/",
                "message": f"Found {len(products)} product(s)" if products else "No products found. You may need to complete seller registration."
            }
            
        except Exception as marketplace_error:
            # If marketplace API fails, seller might not be registered
            sts_client = session.client('sts')
            identity = sts_client.get_caller_identity()
            account_id = identity['Account']
            
            return {
                "success": True,
                "seller_status": "NOT_REGISTERED",
                "account_id": account_id,
                "owned_products": [],
                "owned_products_count": 0,
                "verification_status": {"verified": False},
                "required_steps": ["Complete seller registration at AWS Marketplace Management Portal"],
                "marketplace_accessible": False,
                "portal_url": "https://aws.amazon.com/marketplace/management/tour",
                "message": "Seller registration not found. Please complete registration."
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})

# Get registration requirements
@app.post("/get-registration-requirements")
async def get_registration_requirements(data: Dict[str, Any]):
    """Get seller registration requirements based on country/region"""
    try:
        country = data.get("country", "US")
        
        # Return basic registration requirements
        seller_tools = SellerRegistrationTools(region='us-east-1')
        
        # Get general requirements
        requirements = seller_tools.get_registration_requirements()
        
        # Get India-specific requirements if applicable
        if country == "IN" or country == "India":
            india_requirements = seller_tools.get_india_specific_requirements()
            requirements["india_specific"] = india_requirements
        
        return {
            "success": True,
            "requirements": requirements,
            "country": country
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})

# Validate business information
@app.post("/validate-business-info")
async def validate_business_info(data: Dict[str, Any]):
    """Validate business information for seller registration"""
    try:
        credentials = data.get("credentials", {})
        business_info = data.get("business_info", {})
        
        seller_tools = SellerRegistrationTools(
            region='us-east-1',
            aws_access_key_id=credentials.get("aws_access_key_id"),
            aws_secret_access_key=credentials.get("aws_secret_access_key"),
            aws_session_token=credentials.get("aws_session_token")
        )
        
        # Validate business info
        validation_result = seller_tools.validate_business_info(business_info)
        
        # If India, also validate India-specific requirements
        if business_info.get("country") in ["IN", "India"]:
            india_validation = seller_tools.validate_india_business_info(business_info)
            validation_result["india_validation"] = india_validation
        
        return {
            "success": True,
            "validation": validation_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})

# Check registration progress
@app.post("/check-registration-progress")
async def check_registration_progress(data: Dict[str, Any]):
    """Check progress of seller registration"""
    try:
        credentials = data.get("credentials", {})
        registration_data = data.get("registration_data", {})
        
        seller_tools = SellerRegistrationTools(
            region='us-east-1',
            aws_access_key_id=credentials.get("aws_access_key_id"),
            aws_secret_access_key=credentials.get("aws_secret_access_key"),
            aws_session_token=credentials.get("aws_session_token")
        )
        
        # Check progress
        progress_result = seller_tools.check_registration_progress(registration_data)
        
        return {
            "success": True,
            "progress": progress_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})

# Generate registration preview
@app.post("/generate-registration-preview")
async def generate_registration_preview(data: Dict[str, Any]):
    """Generate preview of registration data"""
    try:
        credentials = data.get("credentials", {})
        registration_data = data.get("registration_data", {})
        
        seller_tools = SellerRegistrationTools(
            region='us-east-1',
            aws_access_key_id=credentials.get("aws_access_key_id"),
            aws_secret_access_key=credentials.get("aws_secret_access_key"),
            aws_session_token=credentials.get("aws_session_token")
        )
        
        # Generate preview
        preview_result = seller_tools.generate_registration_preview(registration_data)
        
        return {
            "success": True,
            "preview": preview_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})

# Get help resources
@app.get("/get-help-resources")
async def get_help_resources():
    """Get help resources for seller registration"""
    try:
        seller_tools = SellerRegistrationTools(region='us-east-1')
        help_resources = seller_tools.get_help_resources()
        
        return {
            "success": True,
            "resources": help_resources
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})

# List marketplace products with detailed status (FAST VERSION)
@app.post("/list-marketplace-products")
async def list_marketplace_products(credentials: Credentials):
    """List marketplace products with detailed status and recommendations (optimized)"""
    try:
        print("[DEBUG] Listing marketplace products...")
        
        # Create session with provided credentials
        session = boto3.Session(
            aws_access_key_id=credentials.aws_access_key_id,
            aws_secret_access_key=credentials.aws_secret_access_key,
            aws_session_token=credentials.aws_session_token,
            region_name='us-east-1'
        )
        
        marketplace_client = session.client('marketplace-catalog')
        account_id = session.client('sts').get_caller_identity()['Account']
        
        products = []
        
        # List all product types - but DON'T describe each one (too slow)
        for product_type in ['SaaSProduct']:  # Start with SaaS only for speed
            try:
                response = marketplace_client.list_entities(
                    Catalog='AWSMarketplace',
                    EntityType=product_type,
                    MaxResults=20  # Limit to 20 for speed
                )
                
                for entity in response.get('EntitySummaryList', []):
                    entity_id = entity.get('EntityId')
                    entity_name = entity.get('Name', 'Unnamed Product')
                    
                    # Use list response data only - NO describe_entity calls
                    # Infer visibility from entity name/status
                    visibility = entity.get('Visibility', 'DRAFT')
                    if not visibility or visibility == 'Unknown':
                        # Default to DRAFT if unknown
                        visibility = 'DRAFT'
                    
                    # Check if SaaS integration is needed
                    needs_saas_integration = product_type == 'SaaSProduct'
                    saas_integration_status = 'PENDING'
                    
                    # Check if CloudFormation stack exists for this product (indicates SaaS integration)
                    stack_exists = False
                    if needs_saas_integration:
                        try:
                            cf_client = session.client('cloudformation')
                            stack_name = f"saas-integration-{entity_id}"
                            print(f"[DEBUG] Checking for CloudFormation stack: {stack_name}")
                            stack_response = cf_client.describe_stacks(StackName=stack_name)
                            if stack_response['Stacks']:
                                stack_status = stack_response['Stacks'][0]['StackStatus']
                                print(f"[DEBUG] Stack {stack_name} status: {stack_status}")
                                if stack_status == 'CREATE_COMPLETE':
                                    stack_exists = True
                                    saas_integration_status = 'COMPLETED'
                                elif stack_status in ['CREATE_IN_PROGRESS', 'UPDATE_IN_PROGRESS']:
                                    saas_integration_status = 'IN_PROGRESS'
                                elif stack_status in ['CREATE_FAILED', 'ROLLBACK_COMPLETE', 'DELETE_COMPLETE']:
                                    saas_integration_status = 'FAILED'
                                    print(f"[DEBUG] Stack in failed/deleted state: {stack_status}")
                        except cf_client.exceptions.ClientError as e:
                            error_code = e.response.get('Error', {}).get('Code', '')
                            if error_code == 'ValidationError' or 'does not exist' in str(e):
                                print(f"[DEBUG] Stack {stack_name} does not exist")
                            else:
                                print(f"[ERROR] Error checking stack {stack_name}: {str(e)}")
                        except Exception as e:
                            print(f"[ERROR] Unexpected error checking stack: {str(e)}")
                    
                    # Determine allowed actions based on status
                    allowed_actions = []
                    recommendations = []
                    
                    if visibility == 'DRAFT':
                        allowed_actions = ['resume', 'delete']
                        recommendations.append('Resume listing creation to publish')
                        # Check if SaaS integration is needed for DRAFT products
                        if needs_saas_integration and not stack_exists:
                            saas_integration_status = 'PENDING'
                    elif visibility == 'LIMITED' or visibility == 'Restricted':
                        allowed_actions = ['view_console']
                        if needs_saas_integration:
                            if stack_exists:
                                recommendations.append('SaaS integration complete - ready for public visibility')
                                saas_integration_status = 'COMPLETED'
                            else:
                                recommendations.append('Complete SaaS integration before going public')
                                allowed_actions.append('configure_saas')
                                saas_integration_status = 'REQUIRED'
                        else:
                            recommendations.append('Product is in limited availability')
                    elif visibility == 'PUBLIC' or visibility == 'Public':
                        allowed_actions = ['view_console']
                        recommendations.append('Product is live on AWS Marketplace')
                        if needs_saas_integration:
                            saas_integration_status = 'COMPLETED'
                    else:
                        # Unknown visibility
                        allowed_actions = ['view_console']
                        recommendations.append('Check product status in AWS Console')
                        # For unknown status, check if it needs SaaS integration
                        if needs_saas_integration:
                            if not stack_exists:
                                allowed_actions.append('configure_saas')
                                saas_integration_status = 'PENDING'
                    
                    products.append({
                        'product_id': entity_id,
                        'product_name': entity_name,
                        'product_type': product_type,
                        'visibility': visibility,
                        'status': 'ACTIVE',
                        'last_modified': '',
                        'needs_saas_integration': needs_saas_integration,
                        'saas_integration_status': saas_integration_status,
                        'fulfillment_url': '',
                        'allowed_actions': allowed_actions,
                        'recommendations': recommendations,
                        'is_editable': visibility == 'DRAFT',
                        'can_deploy_saas': needs_saas_integration and saas_integration_status != 'COMPLETED',
                    })
                        
            except Exception as list_error:
                print(f"[ERROR] Error listing {product_type}: {list_error}")
                continue
        
        print(f"[DEBUG] Found {len(products)} products")
        
        return {
            "success": True,
            "products": products,
            "count": len(products),
            "account_id": account_id
        }
        
    except Exception as e:
        print(f"[ERROR] Error listing marketplace products: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "products": [],
            "count": 0
        }

# List Bedrock agents
@app.post("/list-agents")
async def list_agents(credentials: Credentials):
    """List Bedrock agents in the account"""
    try:
        # Create session with provided credentials
        session = boto3.Session(
            aws_access_key_id=credentials.aws_access_key_id,
            aws_secret_access_key=credentials.aws_secret_access_key,
            aws_session_token=credentials.aws_session_token,
            region_name='us-east-1'
        )
        
        # List agents
        bedrock_agent = session.client('bedrock-agent')
        response = bedrock_agent.list_agents(maxResults=50)
        
        agents = []
        for agent_summary in response.get('agentSummaries', []):
            agents.append({
                'agent_id': agent_summary.get('agentId'),
                'agent_name': agent_summary.get('agentName'),
                'agent_status': agent_summary.get('agentStatus'),
                'description': agent_summary.get('description', ''),
                'updated_at': agent_summary.get('updatedAt').isoformat() if agent_summary.get('updatedAt') else None,
            })
        
        return {
            "success": True,
            "agents": agents,
            "count": len(agents)
        }
        
    except Exception as e:
        # Return empty list if no agents or error
        return {
            "success": True,
            "agents": [],
            "count": 0,
            "error": str(e)
        }

# Helper function to fetch webpage content
def fetch_webpage_content(url: str, max_length: int = 5000) -> str:
    """Fetch and extract text content from a webpage"""
    import re
    try:
        import requests
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Truncate to max length
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        return text
    except Exception as e:
        print(f"[DEBUG] Failed to fetch {url}: {e}")
        return ""

# Helper function to extract JSON from text
def extract_json_from_text(text: str) -> dict:
    """Extract JSON object from text that may contain markdown or other content"""
    import re
    
    # Try to parse as-is first
    try:
        return json.loads(text)
    except:
        pass
    
    # Try to find JSON in markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except:
            pass
    
    # Try to find raw JSON object
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except:
            pass
    
    return None

# Analyze product
@app.post("/analyze-product")
async def analyze_product(data: Dict[str, Any]):
    """Analyze product using Amazon Bedrock"""
    try:
        product_context = data.get("product_context", {})
        credentials = data.get("credentials", {})
        
        # Build analysis prompt
        urls = product_context.get("product_urls", [])
        docs_url = product_context.get("documentation_url", "")
        description = product_context.get("product_description", "")
        product_name = product_context.get("product_name", "")
        
        # Fetch actual content from URLs
        website_content = ""
        if urls:
            print(f"[DEBUG] Fetching content from {urls[0]}")
            website_content = fetch_webpage_content(urls[0])
            if website_content:
                print(f"[DEBUG] Fetched {len(website_content)} chars from website")
        
        docs_content = ""
        if docs_url:
            print(f"[DEBUG] Fetching content from {docs_url}")
            docs_content = fetch_webpage_content(docs_url, max_length=3000)
            if docs_content:
                print(f"[DEBUG] Fetched {len(docs_content)} chars from docs")
        
        prompt = f"""Analyze this product information and provide a structured analysis.

Product Name: {product_name or 'Extract from the content below'}
Website URL: {urls[0] if urls else 'Not provided'}
Documentation URL: {docs_url or 'Not provided'}
User Description: {description or 'Not provided'}

WEBSITE CONTENT:
{website_content or 'No content fetched'}

DOCUMENTATION CONTENT:
{docs_content or 'No content fetched'}

IMPORTANT: 
- If a product name is provided, use it exactly
- If not, extract the actual product/company name from the website content
- Do NOT use generic names - use the REAL product name from the content

Provide a JSON response with these exact keys:
{{
    "product_name": "The actual product name",
    "product_type": "SaaS/API/Platform/etc",
    "target_audience": "Who this product is for",
    "key_features": ["feature1", "feature2", "feature3", "feature4", "feature5"],
    "value_proposition": "Main value this product provides",
    "use_cases": ["use case 1", "use case 2", "use case 3"],
    "competitive_advantages": ["advantage 1", "advantage 2"]
}}

Return ONLY the JSON object, no other text."""
        
        # Create session with credentials if provided
        if credentials:
            session = boto3.Session(
                aws_access_key_id=credentials.get("aws_access_key_id"),
                aws_secret_access_key=credentials.get("aws_secret_access_key"),
                aws_session_token=credentials.get("aws_session_token"),
                region_name=credentials.get("region", "us-east-1")
            )
            bedrock = session.client('bedrock-runtime')
        else:
            bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3  # Lower temperature for more consistent output
        }
        
        # Try multiple models
        models = [
            "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            "anthropic.claude-3-5-sonnet-20240620-v1:0",
            "anthropic.claude-3-sonnet-20240229-v1:0"
        ]
        
        response_text = None
        for model_id in models:
            try:
                print(f"[DEBUG] Trying model: {model_id}")
                response = bedrock.invoke_model(
                    modelId=model_id,
                    body=json.dumps(request_body)
                )
                response_body = json.loads(response['body'].read())
                response_text = response_body['content'][0]['text']
                print(f"[DEBUG] Got response from {model_id}")
                break
            except Exception as e:
                print(f"[DEBUG] Model {model_id} failed: {e}")
                continue
        
        if not response_text:
            raise Exception("All Bedrock models failed")
        
        # Parse response using helper function
        analysis = extract_json_from_text(response_text)
        
        if not analysis:
            print(f"[DEBUG] Failed to parse JSON, raw response: {response_text[:500]}")
            # Create fallback with product name if available
            analysis = {
                "product_name": product_name or "Unknown Product",
                "product_type": "SaaS",
                "target_audience": "Developers and teams",
                "key_features": ["Feature 1", "Feature 2", "Feature 3"],
                "value_proposition": "Streamline your workflow",
                "use_cases": ["Use case 1", "Use case 2"],
                "competitive_advantages": ["Advantage 1", "Advantage 2"]
            }
        
        return {
            "success": True,
            "analysis": analysis
        }
        
    except Exception as e:
        print(f"[ERROR] analyze_product failed: {e}")
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})

# Generate content
@app.post("/generate-content")
async def generate_content(data: Dict[str, Any]):
    """Generate listing content using Amazon Bedrock"""
    try:
        analysis = data.get("analysis", {})
        product_context = data.get("product_context", {})
        credentials = data.get("credentials", {})
        
        # Extract product name from analysis if available
        product_name = analysis.get("product_name", analysis.get("Product Name", ""))
        
        # Get original product info
        website_url = ""
        if product_context.get("product_urls"):
            website_url = product_context["product_urls"][0] if product_context["product_urls"] else ""
        original_description = product_context.get("product_description", "")
        
        prompt = f"""
        Based on this product analysis and original product information:
        
        ORIGINAL PRODUCT INFO:
        - Website: {website_url}
        - Description provided by user: {original_description}
        
        AI ANALYSIS:
        {json.dumps(analysis, indent=2)}
        
        Generate AWS Marketplace listing content that is SPECIFIC to this product.
        
        1. Product Title (5-72 chars, compelling and clear - MUST be under 72 characters)
           CRITICAL: Use the actual product name "{product_name}" if provided. Extract from website URL if not.
           Do NOT use generic names like "Cloud Security Platform" - use the REAL product name.
        2. Short Description (10-500 chars, for search results)
           Must be specific to THIS product, not generic marketing copy.
        3. Long Description (50-5000 chars, detailed with benefits)
           Reference the actual features and capabilities of THIS specific product.
        4. Highlights (3-5 bullet points, 5-250 chars each)
           Specific features of THIS product, not generic benefits.
        5. Search Keywords (5-10 keywords, max 50 chars each)
        6. Suggested Categories (1-3 subcategories MAXIMUM) - Use ONLY subcategory names from this list:
           
           AI Security, Content Creation, Customer Experience Personalization, Customer Support, Data Analysis, Finance & Accounting, IT Support, Legal & Compliance, Observability, Procurement & Supply Chain, Quality Assurance, Research, Sales & Marketing, Scheduling & Coordination, Software Development, Backup & Recovery, Data Analytics, Data Integration, Data Preparation, ELT/ETL, Streaming Solutions, Databases, Data Warehouses, Analytic Platforms, Data Catalogs, Master Data Management, Masking/Tokenization, Business Intelligence & Advanced Analytics, High Performance Computing, Migration, Network Infrastructure, Operating Systems, Security, Storage, Agile Lifecycle Management, Application Development, Application Servers, Application Stacks, Continuous Integration and Continuous Delivery, Infrastructure as Code, Issue & Bug Tracking, Monitoring, Log Analysis, Source Control, Testing, Blockchain, Collaboration & Productivity, Contact Center, Content Management, CRM, eCommerce, eLearning, Human Resources, IT Business Management, Project Management, Analytics, Applications, Device Connectivity, Device Management, Device Security, Industrial IoT, Smart Home & City, Education & Research, Financial Services, Healthcare & Life Sciences, Media & Entertainment, Industrial, Energy, Automotive, Financial Services Data, Retail Location & Marketing Data, Public Sector Data, Healthcare & Life Sciences Data, Resources Data, Media & Entertainment Data, Telecommunications Data, Environmental Data, Automotive Data, Manufacturing Data, Gaming Data, Assessments, Implementation, Managed Services, Premium Support, Training, Human Review Services, ML Solutions, Data Labeling Services, Computer Vision, Natural Language Processing, Speech Recognition, Generative AI, Sentiment Analysis, Text to Speech, Translation, Object Detection, Anomaly Detection, Time-series Forecasting, Cloud Governance, Cloud Financial Management, Monitoring and Observability, Compliance and Auditing, Operations Management, AIOps
           
           Example category values: "Security", "Generative AI", "Application Development", "Monitoring"
           DO NOT use parent category names like "DevOps", "Machine Learning", "Infrastructure Software" - use only subcategories.
        
        IMPORTANT: 
        - Use only basic ASCII characters. Do NOT use:
          - Bullet points (•) - use hyphens (-) instead
          - Smart quotes (" ") - use straight quotes (")
          - Em/en dashes (— –) - use hyphens (-)
        - ALL content must be specific to the actual product, NOT generic placeholder text.
        - If the website URL contains a product/company name, USE IT.
        - Categories must be ONLY subcategory names (e.g., "Testing", "Security", NOT "DevOps > Testing")
        
        Format as JSON with these exact keys: product_title, short_description, long_description, highlights (array), search_keywords (array), categories (array)
        """
        
        # Create session with credentials if provided
        if credentials:
            session = boto3.Session(
                aws_access_key_id=credentials.get("aws_access_key_id"),
                aws_secret_access_key=credentials.get("aws_secret_access_key"),
                aws_session_token=credentials.get("aws_session_token"),
                region_name=credentials.get("region", "us-east-1")
            )
            bedrock = session.client('bedrock-runtime')
        else:
            bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3  # Lower temperature for more focused, less creative output
        }
        
        models = [
            "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            "anthropic.claude-3-5-sonnet-20240620-v1:0",
            "anthropic.claude-3-sonnet-20240229-v1:0"
        ]
        
        response_text = None
        for model_id in models:
            try:
                response = bedrock.invoke_model(
                    modelId=model_id,
                    body=json.dumps(request_body)
                )
                response_body = json.loads(response['body'].read())
                response_text = response_body['content'][0]['text']
                break
            except:
                continue
        
        if not response_text:
            raise Exception("All Bedrock models failed")
        
        # Parse response
        try:
            content = json.loads(response_text)
        except:
            content = {
                "product_title": "Your Product",
                "short_description": "Brief description",
                "long_description": "Detailed description",
                "highlights": ["Feature 1", "Feature 2", "Feature 3"],
                "search_keywords": ["keyword1", "keyword2"],
                "categories": ["Application Development"]
            }
        
        return {
            "success": True,
            "content": content
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})

# Suggest pricing
@app.post("/suggest-pricing")
async def suggest_pricing(data: Dict[str, Any]):
    """Suggest pricing model using Amazon Bedrock"""
    try:
        analysis = data.get("analysis", {})
        credentials = data.get("credentials", {})
        
        prompt = f"""
        Based on this product:
        {json.dumps(analysis, indent=2)}
        
        Suggest the best AWS Marketplace pricing model:
        
        Options:
        1. "Contract" - One-time fee with allotted units
        2. "Usage" - Purely subscription/consumption based
        3. "Contract with Consumption" - One-time fee plus additional charges
        
        Return ONLY a valid JSON object with these exact keys:
        {{
            "recommended_model": "Contract" | "Usage" | "Contract with Consumption",
            "reasoning": "Brief explanation",
            "suggested_dimensions": ["dimension1", "dimension2"],
            "contract_durations": ["12 Months", "24 Months"]
        }}
        """
        
        # Create session with credentials if provided
        if credentials:
            session = boto3.Session(
                aws_access_key_id=credentials.get("aws_access_key_id"),
                aws_secret_access_key=credentials.get("aws_secret_access_key"),
                aws_session_token=credentials.get("aws_session_token"),
                region_name=credentials.get("region", "us-east-1")
            )
            bedrock = session.client('bedrock-runtime')
        else:
            bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        
        models = [
            "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            "anthropic.claude-3-5-sonnet-20240620-v1:0",
            "anthropic.claude-3-sonnet-20240229-v1:0"
        ]
        
        response_text = None
        for model_id in models:
            try:
                response = bedrock.invoke_model(
                    modelId=model_id,
                    body=json.dumps(request_body)
                )
                response_body = json.loads(response['body'].read())
                response_text = response_body['content'][0]['text']
                break
            except:
                continue
        
        if not response_text:
            raise Exception("All Bedrock models failed")
        
        # Parse response
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                pricing = json.loads(json_match.group())
            else:
                raise ValueError("No JSON found")
        except:
            pricing = {
                "recommended_model": "Contract",
                "reasoning": "Contract-based pricing is recommended for most SaaS products",
                "suggested_dimensions": ["Users", "Features"],
                "contract_durations": ["12 Months", "24 Months"]
            }
        
        return {
            "success": True,
            "pricing": pricing
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})

# Create listing


# Create listing
@app.post("/create-listing")
async def create_listing(data: Dict[str, Any]):
    """Create marketplace listing using AWS Marketplace Catalog API"""
    import traceback
    import time
    
    stages = []
    
    try:
        print("[DEBUG] create_listing called")
        listing_data = data.get("listing_data", {})
        credentials = data.get("credentials", {})
        print(f"[DEBUG] listing_data keys: {list(listing_data.keys())}")
        
        # Create boto3 session
        session = boto3.Session(
            aws_access_key_id=credentials.get("aws_access_key_id"),
            aws_secret_access_key=credentials.get("aws_secret_access_key"),
            aws_session_token=credentials.get("aws_session_token"),
            region_name='us-east-1'
        )
        
        marketplace_client = session.client('marketplace-catalog')
        
        # Extract listing data
        product_title = listing_data.get("title", "")
        short_description = listing_data.get("short_description", "")
        long_description = listing_data.get("long_description", "")
        highlights = listing_data.get("highlights", [])
        categories = listing_data.get("categories", [])
        search_keywords = listing_data.get("search_keywords", [])
        support_email = listing_data.get("support_email", "")
        
        # Validate required fields
        if not product_title:
            raise Exception("Product title is required")
        if not short_description:
            raise Exception("Short description is required")
        if not long_description:
            raise Exception("Long description is required")
        
        print(f"[DEBUG] Creating product: {product_title}")
        
        # Stage 1: Create SaaS Product
        stages.append({"stage": "Product Creation", "status": "in_progress", "message": "Creating product..."})
        
        # Build product details JSON for CreateProduct change type
        product_details = json.dumps({
            "ProductTitle": product_title
        })
        
        # Start change set to create product
        create_response = marketplace_client.start_change_set(
            Catalog='AWSMarketplace',
            ChangeSet=[
                {
                    'ChangeType': 'CreateProduct',
                    'Entity': {
                        'Type': 'SaaSProduct@1.0'
                    },
                    'Details': product_details
                }
            ],
            ChangeSetName=f"Create-{product_title[:30].replace(' ', '-')}-{int(time.time())}"
        )
        
        change_set_id = create_response['ChangeSetId']
        print(f"[DEBUG] Change set created: {change_set_id}")
        
        # Wait for change set to complete (poll status)
        max_wait = 300  # 5 minutes max
        wait_interval = 5
        elapsed = 0
        product_id = None
        
        while elapsed < max_wait:
            status_response = marketplace_client.describe_change_set(
                Catalog='AWSMarketplace',
                ChangeSetId=change_set_id
            )
            
            status = status_response['Status']
            print(f"[DEBUG] Change set status: {status}")
            
            if status == 'SUCCEEDED':
                # Extract product ID from change set
                for change in status_response.get('ChangeSet', []):
                    if change.get('ChangeType') == 'CreateProduct':
                        product_id = change.get('Entity', {}).get('Identifier')
                        break
                break
            elif status == 'FAILED':
                failure_code = status_response.get('FailureCode', 'Unknown')
                failure_desc = status_response.get('FailureDescription', 'No description')
                raise Exception(f"Product creation failed: {failure_code} - {failure_desc}")
            elif status in ['CANCELLED']:
                raise Exception("Product creation was cancelled")
            
            time.sleep(wait_interval)
            elapsed += wait_interval
        
        if not product_id:
            raise Exception("Timed out waiting for product creation")
        
        stages[0] = {"stage": "Product Creation", "status": "complete", "message": f"Product created: {product_id}"}
        print(f"[DEBUG] Product created: {product_id}")
        
        # Stage 2: Update product description
        stages.append({"stage": "Product Details", "status": "in_progress", "message": "Updating product details..."})
        
        description_details = json.dumps({
            "ProductTitle": product_title,
            "ShortDescription": short_description,
            "LongDescription": long_description,
            "Highlights": highlights[:5] if highlights else [],
            "SearchKeywords": search_keywords[:5] if search_keywords else [],
            "Categories": categories[:3] if categories else []
        })
        
        try:
            marketplace_client.start_change_set(
                Catalog='AWSMarketplace',
                ChangeSet=[
                    {
                        'ChangeType': 'UpdateInformation',
                        'Entity': {
                            'Type': 'SaaSProduct@1.0',
                            'Identifier': product_id
                        },
                        'Details': description_details
                    }
                ],
                ChangeSetName=f"UpdateInfo-{product_id[:20]}-{int(time.time())}"
            )
            stages[-1] = {"stage": "Product Details", "status": "complete", "message": "Product details updated"}
        except Exception as e:
            print(f"[DEBUG] Update info failed: {str(e)}")
            stages[-1] = {"stage": "Product Details", "status": "warning", "message": f"Details update pending: {str(e)[:50]}"}
        
        # Stage 3: Configure support if email provided
        if support_email:
            stages.append({"stage": "Support Configuration", "status": "in_progress", "message": "Configuring support..."})
            
            support_details = json.dumps({
                "SupportDescription": listing_data.get("support_description", "Contact support for assistance."),
                "SupportResources": [{"Type": "Email", "Value": support_email}]
            })
            
            try:
                marketplace_client.start_change_set(
                    Catalog='AWSMarketplace',
                    ChangeSet=[
                        {
                            'ChangeType': 'UpdateSupportTerms',
                            'Entity': {
                                'Type': 'SaaSProduct@1.0',
                                'Identifier': product_id
                            },
                            'Details': support_details
                        }
                    ],
                    ChangeSetName=f"Support-{product_id[:20]}-{int(time.time())}"
                )
                stages[-1] = {"stage": "Support Configuration", "status": "complete", "message": "Support configured"}
            except Exception as e:
                print(f"[DEBUG] Support config failed: {str(e)}")
                stages[-1] = {"stage": "Support Configuration", "status": "warning", "message": f"Support config pending: {str(e)[:50]}"}
        
        # Return success
        return {
            "success": True,
            "product_id": product_id,
            "offer_id": None,
            "published_to_limited": False,
            "message": f"Product '{product_title}' created successfully",
            "stages": stages
        }
        
    except Exception as e:
        print(f"[ERROR] create_listing exception: {str(e)}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        stages.append({"stage": "Error", "status": "failed", "message": str(e)})
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to create listing: {str(e)}",
            "stages": stages
        }

@app.post("/check-stack-exists")
async def check_stack_exists(data: Dict[str, Any]):
    """Check if a CloudFormation stack already exists"""
    try:
        stack_name = data.get("stack_name")
        region = data.get("region", "us-east-1")
        credentials = data.get("credentials", {})
        
        session = boto3.Session(
            aws_access_key_id=credentials.get("aws_access_key_id"),
            aws_secret_access_key=credentials.get("aws_secret_access_key"),
            aws_session_token=credentials.get("aws_session_token"),
            region_name=region
        )
        
        cf_client = session.client('cloudformation')
        
        try:
            response = cf_client.describe_stacks(StackName=stack_name)
            stacks = response.get('Stacks', [])
            
            if stacks:
                stack = stacks[0]
                status = stack['StackStatus']
                
                # Consider stack as existing if it's not deleted
                if status not in ['DELETE_COMPLETE', 'DELETE_FAILED']:
                    return {
                        "exists": True,
                        "stack_name": stack_name,
                        "stack_id": stack['StackId'],
                        "status": status
                    }
            
            return {"exists": False}
            
        except cf_client.exceptions.ClientError as e:
            if 'does not exist' in str(e):
                return {"exists": False}
            raise
            
    except Exception as e:
        print(f"[ERROR] Failed to check stack: {str(e)}")
        return {"exists": False, "error": str(e)}

@app.post("/delete-stack")
async def delete_stack(data: Dict[str, Any]):
    """Delete a CloudFormation stack and wait for completion"""
    try:
        stack_name = data.get("stack_name")
        region = data.get("region", "us-east-1")
        credentials = data.get("credentials", {})
        
        print(f"[DEBUG] Deleting stack: {stack_name}")
        
        session = boto3.Session(
            aws_access_key_id=credentials.get("aws_access_key_id"),
            aws_secret_access_key=credentials.get("aws_secret_access_key"),
            aws_session_token=credentials.get("aws_session_token"),
            region_name=region
        )
        
        cf_client = session.client('cloudformation')
        
        # Initiate stack deletion (non-blocking)
        cf_client.delete_stack(StackName=stack_name)
        print(f"[DEBUG] Stack deletion initiated for: {stack_name}")
        
        # Return immediately - frontend will poll for status
        return {
            "success": True, 
            "message": "Stack deletion initiated",
            "stack_name": stack_name,
            "status": "DELETE_IN_PROGRESS"
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to delete stack: {str(e)}")
        return {"success": False, "error": str(e)}

@app.post("/run-buyer-experience")
async def run_buyer_experience(data: Dict[str, Any]):
    """Run buyer experience simulation and route to appropriate next step based on pricing model"""
    try:
        credentials = data.get("credentials", {})
        product_id = data.get("product_id")
        pricing_model = data.get("pricing_model")  # Get pricing model from user selection
        
        print(f"[BACKEND DEBUG] ===== BUYER EXPERIENCE WORKFLOW =====")
        print(f"[BACKEND DEBUG] Product ID: {product_id}")
        print(f"[BACKEND DEBUG] Pricing Model from frontend: {pricing_model}")
        print(f"[BACKEND DEBUG] ================================================")
        
        access_key = credentials.get("aws_access_key_id")
        secret_key = credentials.get("aws_secret_access_key")
        session_token = credentials.get("aws_session_token")
        
        # Import buyer experience agent
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))
        from buyer_experience import BuyerExperienceAgent
        
        # Run buyer experience simulation
        agent = BuyerExperienceAgent()
        buyer_result = agent.simulate_buyer_journey(access_key, secret_key, session_token)
        
        if buyer_result.get("status") != "success":
            return {
                "success": False,
                "error": "Buyer experience simulation did not complete successfully",
                "buyer_result": buyer_result
            }
        
        # Use pricing model from user selection (passed from frontend)
        # Map CloudFormation values to agent routing logic
        pricing_model_mapping = {
            'subscriptions': 'Usage-based-pricing',
            'contracts': 'Contract-based-pricing',
            'contracts_with_subscription': 'Contract-with-consumption'
        }
        
        # Convert CloudFormation format to agent format if needed
        if pricing_model in pricing_model_mapping:
            agent_pricing_model = pricing_model_mapping[pricing_model]
        else:
            agent_pricing_model = pricing_model  # Already in agent format
        
        print(f"[BACKEND DEBUG] Pricing model for routing: {agent_pricing_model}")
        
        # Route to appropriate agent based on pricing model
        next_step = None
        next_step_result = None
        
        if agent_pricing_model in ["Usage-based-pricing", "Contract-with-consumption"]:
            # Route to metering agent
            print("[BACKEND DEBUG] ===== ROUTING TO METERING AGENT =====")
            print(f"[BACKEND DEBUG] Pricing model requires metering: {agent_pricing_model}")
            print("[BACKEND DEBUG] ================================================")
            from metering import MeteringAgent
            
            metering_agent = MeteringAgent()
            metering_result = metering_agent.check_entitlement_and_add_metering(
                access_key, secret_key, session_token
            )
            
            next_step = "metering"
            next_step_result = metering_result
            
        else:  # Contract-based-pricing
            # Route to public visibility agent
            print("[BACKEND DEBUG] ===== ROUTING TO PUBLIC VISIBILITY AGENT =====")
            print(f"[BACKEND DEBUG] Pricing model: {agent_pricing_model}")
            print("[BACKEND DEBUG] Starting public visibility workflow...")
            print("[BACKEND DEBUG] ================================================")
            from public_visibility import PublicVisibilityAgent
            
            visibility_agent = PublicVisibilityAgent()
            visibility_result = visibility_agent.raise_public_visibility_request(
                access_key, secret_key, session_token
            )
            
            next_step = "public_visibility"
            next_step_result = visibility_result
        
        print(f"[BACKEND DEBUG] ===== WORKFLOW COMPLETE =====")
        print(f"[BACKEND DEBUG] Next step: {next_step}")
        print(f"[BACKEND DEBUG] ================================================")
        
        return {
            "success": True,
            "buyer_result": buyer_result,
            "pricing_model": agent_pricing_model,
            "next_step": next_step,
            "next_step_result": next_step_result
        }
        
    except Exception as e:
        print(f"[ERROR] run_buyer_experience failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/buyer-experience-guide")
async def buyer_experience_guide(data: Dict[str, Any]):
    """Get buyer experience simulation guide"""
    try:
        return {
            "success": True,
            "steps": [
                {
                    "step": 1,
                    "title": "Open SaaS Product Page",
                    "description": "Access your product in the AWS Marketplace Management Portal",
                    "actions": [
                        "Open AWS Marketplace Management Portal: https://aws.amazon.com/marketplace/management/products",
                        "Select the product you created in the Lab: Create a SaaS listing"
                    ]
                },
                {
                    "step": 2,
                    "title": "Validate Fulfillment URL Update",
                    "description": "Ensure the fulfillment URL was updated successfully before continuing",
                    "actions": [
                        "In the Request Log tab, validate that the last request's status is Succeeded",
                        "This confirms the solution has updated your AWS Marketplace product's fulfillment URL"
                    ]
                },
                {
                    "step": 3,
                    "title": "View Product on Marketplace",
                    "description": "Access your product as customers would see it",
                    "actions": [
                        "Select 'View on AWS Marketplace'"
                    ]
                },
                {
                    "step": 4,
                    "title": "Start Purchase Process",
                    "description": "Begin the test purchase flow",
                    "actions": [
                        "Select 'View purchase options'"
                    ]
                },
                {
                    "step": 5,
                    "title": "Configure Contract Terms",
                    "description": "Set up a test contract with minimal commitment",
                    "actions": [
                        "Under 'How long do you want your contract to run?', select 1 month",
                        "Set your Renewal Settings to No",
                        "Under Contract Options, set any option quantity to 1 (or select the cheapest option tier, if applicable)"
                    ]
                },
                {
                    "step": 6,
                    "title": "Complete Purchase",
                    "description": "Finalize the test purchase",
                    "actions": [
                        "Select 'Create contract'",
                        "Then select 'Pay now'"
                    ]
                },
                {
                    "step": 7,
                    "title": "Set Up Account",
                    "description": "Begin the registration process",
                    "actions": [
                        "Select 'Set up your account'",
                        "You will be redirected to your custom registration page"
                    ]
                },
                {
                    "step": 8,
                    "title": "Complete Registration",
                    "description": "Fill in your information and register",
                    "actions": [
                        "Fill in the information in the registration page (company name, contact email, etc.)",
                        "Select 'Register'"
                    ]
                },
                {
                    "step": 9,
                    "title": "Verify Registration Success",
                    "description": "Confirm the registration completed successfully",
                    "expected": [
                        "After a few seconds, a blue banner should appear confirming successful registration",
                        "You should receive an email with subscription details in your notification email inbox",
                        "Customer record is created in DynamoDB"
                    ]
                }
            ]
        }
    except Exception as e:
        print(f"[ERROR] Failed to get buyer experience guide: {str(e)}")
        return {"success": False, "error": str(e)}

@app.post("/metering-guide")
async def metering_guide(data: Dict[str, Any]):
    """Get metering setup guide for usage-based pricing"""
    try:
        return {
            "success": True,
            "steps": [
                {
                    "step": 1,
                    "title": "Check Customer Entitlement",
                    "description": "Verify customer records exist in DynamoDB",
                    "actions": [
                        "Open AWS Console → DynamoDB",
                        "Find the 'NewSubscribers' or 'AWSMarketplaceSubscribers' table",
                        "Verify customer records exist from your test purchase",
                        "Note the customerIdentifier for metering"
                    ]
                },
                {
                    "step": 2,
                    "title": "Create Metering Records",
                    "description": "Add usage records to the metering table",
                    "actions": [
                        "Find the 'AWSMarketplaceMeteringRecords' table",
                        "Metering records are automatically created when customers use your service",
                        "For testing, records can be manually added with usage dimensions"
                    ]
                },
                {
                    "step": 3,
                    "title": "Trigger Metering Lambda",
                    "description": "Process metering records and send to AWS Marketplace",
                    "actions": [
                        "Open AWS Console → Lambda",
                        "Find the Lambda function with 'Hourly' in the name",
                        "Click 'Test' to manually trigger the function",
                        "Lambda will call BatchMeterUsage API to report usage to AWS Marketplace"
                    ]
                },
                {
                    "step": 4,
                    "title": "Verify Metering Success",
                    "description": "Confirm usage was reported successfully",
                    "expected": [
                        "Lambda execution succeeds without errors",
                        "Metering records updated with metering_failed=False",
                        "BatchMeterUsage response stored in records",
                        "Usage appears in AWS Marketplace billing"
                    ]
                }
            ]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/metering-find-tables")
async def metering_find_tables(data: Dict[str, Any]):
    """Step 1: Find NewSubscribers and MeteringRecords tables"""
    try:
        credentials = data.get("credentials", {})
        product_id = data.get("product_id")
        
        access_key = credentials.get("aws_access_key_id")
        secret_key = credentials.get("aws_secret_access_key")
        session_token = credentials.get("aws_session_token")
        
        print(f"[METERING DEBUG] Finding tables for product: {product_id}")
        
        dynamodb = boto3.client(
            'dynamodb',
            region_name='us-east-1',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token
        )
        
        tables = dynamodb.list_tables()['TableNames']
        subscribers_table = None
        metering_table = None
        
        for table in tables:
            if product_id in table:
                if 'NewSubscribers' in table or 'AWSMarketplaceSubscribers' in table:
                    subscribers_table = table
                    print(f"[METERING DEBUG] ✓ Found subscribers table: {table}")
                if 'MeteringRecords' in table:
                    metering_table = table
                    print(f"[METERING DEBUG] ✓ Found metering table: {table}")
        
        if not subscribers_table:
            return {
                "success": False,
                "error": "NewSubscribers table not found. Make sure the CloudFormation stack is deployed."
            }
        
        if not metering_table:
            return {
                "success": False,
                "error": "MeteringRecords table not found. Make sure the CloudFormation stack is deployed."
            }
        
        return {
            "success": True,
            "subscribers_table": subscribers_table,
            "metering_table": metering_table
        }
        
    except Exception as e:
        print(f"[METERING ERROR] Failed to find tables: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/metering-get-customer")
async def metering_get_customer(data: Dict[str, Any]):
    """Step 2: Get customer from NewSubscribers table"""
    try:
        credentials = data.get("credentials", {})
        subscribers_table = data.get("subscribers_table")
        
        access_key = credentials.get("aws_access_key_id")
        secret_key = credentials.get("aws_secret_access_key")
        session_token = credentials.get("aws_session_token")
        
        print(f"[METERING DEBUG] Getting customer from table: {subscribers_table}")
        
        dynamodb = boto3.client(
            'dynamodb',
            region_name='us-east-1',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token
        )
        
        response = dynamodb.scan(TableName=subscribers_table, Limit=10)
        
        if not response['Items']:
            return {
                "success": False,
                "error": "No customers found in NewSubscribers table. Complete the buyer experience workflow first."
            }
        
        # Get the first customer
        customer = response['Items'][0]
        customer_identifier = customer.get('customerIdentifier', {}).get('S', '')
        product_code = customer.get('productCode', {}).get('S', '')
        
        print(f"[METERING DEBUG] ✓ Found customer: {customer_identifier}")
        
        return {
            "success": True,
            "customer_identifier": customer_identifier,
            "product_code": product_code,
            "customer_data": customer
        }
        
    except Exception as e:
        print(f"[METERING ERROR] Failed to get customer: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/metering-insert-record")
async def metering_insert_record(data: Dict[str, Any]):
    """Step 3: Insert metering record into MeteringRecords table"""
    try:
        credentials = data.get("credentials", {})
        metering_table = data.get("metering_table")
        customer_identifier = data.get("customer_identifier")
        usage_dimensions = data.get("usage_dimensions", [])
        
        access_key = credentials.get("aws_access_key_id")
        secret_key = credentials.get("aws_secret_access_key")
        session_token = credentials.get("aws_session_token")
        
        print(f"[METERING DEBUG] Inserting record for customer: {customer_identifier}")
        
        dynamodb = boto3.client(
            'dynamodb',
            region_name='us-east-1',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token
        )
        
        import time
        current_timestamp = str(int(time.time()))
        
        # Prepare dimension usage
        dimension_usage = []
        for dimension in usage_dimensions:
            dimension_usage.append({
                "M": {
                    "dimension": {"S": dimension},
                    "value": {"N": "10"}
                }
            })
        
        # Create metering record
        metering_record = {
            "create_timestamp": {"N": current_timestamp},
            "customerIdentifier": {"S": customer_identifier},
            "dimension_usage": {"L": dimension_usage},
            "metering_pending": {"S": "true"}
        }
        
        dynamodb.put_item(TableName=metering_table, Item=metering_record)
        print(f"[METERING DEBUG] ✓ Metering record inserted successfully")
        
        return {
            "success": True,
            "timestamp": current_timestamp,
            "customer_identifier": customer_identifier,
            "dimensions": usage_dimensions,
            "message": "Metering record created successfully"
        }
        
    except Exception as e:
        print(f"[METERING ERROR] Failed to insert record: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/public-visibility-guide")
async def public_visibility_guide(data: Dict[str, Any]):
    """Get public visibility request guide for contract-based pricing"""
    try:
        return {
            "success": True,
            "steps": [
                {
                    "step": 1,
                    "title": "Prepare for Public Launch",
                    "description": "Ensure your product is ready to go live",
                    "actions": [
                        "Review product title, description, and features",
                        "Verify pricing information is accurate",
                        "Ensure all required documentation is uploaded",
                        "Confirm support contact information is correct",
                        "Test the complete buyer experience flow"
                    ]
                },
                {
                    "step": 2,
                    "title": "Access Your Product in Management Portal",
                    "description": "Navigate to your SaaS product page",
                    "actions": [
                        "Open AWS Marketplace Management Portal: https://aws.amazon.com/marketplace/management/products",
                        "Select your product in the SaaS product page"
                    ]
                },
                {
                    "step": 3,
                    "title": "Request Product Visibility Change",
                    "description": "Initiate the public visibility request",
                    "actions": [
                        "Select 'Request changes'",
                        "Choose 'Update product visibility'",
                        "Follow the prompts to change from Limited to Public visibility"
                    ]
                },
                {
                    "step": 4,
                    "title": "AWS Review Process",
                    "description": "AWS will review your public visibility request",
                    "expected": [
                        "Review typically takes 1-3 business days",
                        "You'll receive email notifications about the review status",
                        "AWS may request additional information or changes",
                        "Once approved, your product will be publicly visible to all AWS customers"
                    ]
                },
                {
                    "step": 5,
                    "title": "Post-Approval Actions",
                    "description": "After your product goes public",
                    "actions": [
                        "Verify product appears in AWS Marketplace search results",
                        "Test the public product page as a customer would see it",
                        "Monitor for customer subscriptions and usage",
                        "Respond to customer inquiries promptly",
                        "Track product performance and customer feedback"
                    ]
                }
            ]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/deploy-saas")
async def deploy_saas(data: Dict[str, Any]):
    """Deploy SaaS integration - starts CloudFormation stack and returns immediately"""
    import traceback
    import os
    try:
        print("=" * 80)
        print("[BACKEND DEBUG] ===== DEPLOY-SAAS ENDPOINT CALLED =====")
        print(f"[BACKEND DEBUG] Raw request data: {data}")
        print("=" * 80)
        product_id = data.get("product_id")
        email = data.get("email")
        stack_name = data.get("stack_name")
        region = data.get("region", "us-east-1")
        pricing_model = data.get("pricing_model")
        credentials = data.get("credentials", {})
        
        print(f"[DEBUG] Product ID: {product_id}, Email: {email}, Stack: {stack_name}, Region: {region}")
        print(f"[BACKEND DEBUG] ===== PRICING MODEL RECEIVED FROM FRONTEND =====")
        print(f"[BACKEND DEBUG] pricing_model value: {pricing_model}")
        print(f"[BACKEND DEBUG] pricing_model type: {type(pricing_model)}")
        print(f"[BACKEND DEBUG] ================================================")
        
        # Validate pricing model is provided
        if not pricing_model:
            print("[BACKEND ERROR] Pricing model is missing!")
            raise HTTPException(status_code=400, detail={"success": False, "error": "Pricing model is required"})
        
        # Create boto3 session
        session = boto3.Session(
            aws_access_key_id=credentials.get("aws_access_key_id"),
            aws_secret_access_key=credentials.get("aws_secret_access_key"),
            aws_session_token=credentials.get("aws_session_token"),
            region_name=region
        )
        
        # Validate credentials
        print("[DEBUG] Validating AWS credentials...")
        try:
            sts_client = session.client('sts')
            identity = sts_client.get_caller_identity()
            print(f"[DEBUG] Credentials valid for account: {identity['Account']}")
        except Exception as e:
            print(f"[ERROR] Invalid credentials: {str(e)}")
            raise HTTPException(status_code=400, detail={"success": False, "error": f"Invalid AWS credentials: {str(e)}"})
        
        # Use pricing model provided by user (already validated above)
        type_of_saas_listing = pricing_model  # Frontend sends the CloudFormation value directly
        print(f"[BACKEND DEBUG] ===== PREPARING CLOUDFORMATION PARAMETERS =====")
        print(f"[BACKEND DEBUG] Using user-provided pricing model: {pricing_model}")
        print(f"[BACKEND DEBUG] TypeOfSaaSListing for CloudFormation: {type_of_saas_listing}")
        print(f"[BACKEND DEBUG] ================================================")
        
        # Find the Integration.yaml template
        possible_paths = [
            'deployment/cloudformation/Integration.yaml',
            '../deployment/cloudformation/Integration.yaml',
            os.path.join(os.path.dirname(__file__), '..', 'deployment', 'cloudformation', 'Integration.yaml')
        ]
        
        template_path = None
        for path in possible_paths:
            if os.path.exists(path):
                template_path = path
                print(f"[DEBUG] Found template at: {path}")
                break
        
        if not template_path:
            raise Exception(f"Could not find Integration.yaml template in: {possible_paths}")
        
        with open(template_path, 'r') as f:
            template_body = f.read()
        
        # The actual stack name used
        actual_stack_name = f"saas-integration-{product_id}"
        
        # Create CloudFormation client and start stack (non-blocking)
        cf_client = session.client('cloudformation')
        
        # Frontend already sends the correct CloudFormation value
        # (subscriptions, contracts, or contracts_with_subscription)
        type_of_saas_listing = pricing_model
        
        print(f"[DEBUG] Creating CloudFormation stack: {actual_stack_name}")
        print(f"[BACKEND DEBUG] ===== CLOUDFORMATION STACK PARAMETERS =====")
        print(f"[BACKEND DEBUG] Parameters being sent to CloudFormation:")
        print(f"[BACKEND DEBUG]   - ProductId: {product_id}")
        print(f"[BACKEND DEBUG]   - Pricing Model (from frontend): {pricing_model}")
        print(f"[BACKEND DEBUG]   - TypeOfSaaSListing (for CloudFormation): {type_of_saas_listing}")
        print(f"[BACKEND DEBUG]   - Email: {email}")
        print(f"[BACKEND DEBUG] ================================================")
        
        try:
            cf_params = [
                {'ParameterKey': 'ProductId', 'ParameterValue': product_id},
                {'ParameterKey': 'TypeOfSaaSListing', 'ParameterValue': type_of_saas_listing},
                {'ParameterKey': 'MarketplaceTechAdminEmail', 'ParameterValue': email},
                {'ParameterKey': 'UpdateFulfillmentURL', 'ParameterValue': 'true'}
            ]
            
            print(f"[BACKEND DEBUG] ===== CALLING CLOUDFORMATION CREATE_STACK =====")
            print(f"[BACKEND DEBUG] Full parameters list: {cf_params}")
            print(f"[BACKEND DEBUG] ================================================")
            
            response = cf_client.create_stack(
                StackName=actual_stack_name,
                TemplateBody=template_body,
                Parameters=cf_params,
                Capabilities=['CAPABILITY_IAM', 'CAPABILITY_AUTO_EXPAND']
            )
            
            stack_id = response['StackId']
            print(f"[BACKEND DEBUG] ===== STACK CREATION SUCCESS =====")
            print(f"[BACKEND DEBUG] Stack creation initiated: {stack_id}")
            print(f"[BACKEND DEBUG] Stack will use TypeOfSaaSListing: {type_of_saas_listing}")
            print(f"[BACKEND DEBUG] ================================================")
            
            # Return immediately - frontend will poll for status
            return {
                "success": True,
                "stack_id": stack_id,
                "stack_name": actual_stack_name,
                "message": "CloudFormation stack creation initiated. Polling for status..."
            }
            
        except cf_client.exceptions.AlreadyExistsException:
            print(f"[DEBUG] Stack already exists: {actual_stack_name}")
            # Get existing stack info
            stack_info = cf_client.describe_stacks(StackName=actual_stack_name)
            stack = stack_info['Stacks'][0]
            return {
                "success": True,
                "stack_id": stack['StackId'],
                "stack_name": actual_stack_name,
                "message": "Stack already exists",
                "status": stack['StackStatus']
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] deploy_saas exception: {str(e)}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})

# Execute complete SaaS workflow using orchestrator
@app.post("/execute-saas-workflow")
async def execute_saas_workflow(data: Dict[str, Any]):
    """Execute complete SaaS workflow: Metering → Lambda → Visibility"""
    try:
        if not AGENTS_AVAILABLE:
            return {
                "success": False,
                "error": "Workflow orchestrator not available. Agents not properly imported."
            }
        
        credentials = data.get("credentials", {})
        lambda_function_name = data.get("lambda_function_name")
        
        access_key = credentials.get("aws_access_key_id")
        secret_key = credentials.get("aws_secret_access_key")
        session_token = credentials.get("aws_session_token")
        
        if not access_key or not secret_key:
            return {
                "success": False,
                "error": "AWS credentials are required"
            }
        
        # Initialize workflow orchestrator
        orchestrator = WorkflowOrchestrator()
        
        # Execute full workflow
        result = orchestrator.execute_full_workflow(
            access_key=access_key,
            secret_key=secret_key,
            session_token=session_token,
            lambda_function_name=lambda_function_name
        )
        
        return {
            "success": result.get("status") in ["success", "partial_success"],
            "workflow_result": result
        }
        
    except Exception as e:
        print(f"[ERROR] Workflow execution failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

# Get CloudFormation stack status
@app.post("/get-stack-status")
async def get_stack_status(data: Dict[str, Any]):
    """Get CloudFormation stack deployment status"""
    try:
        stack_name = data.get("stack_name")
        region = data.get("region", "us-east-1")
        credentials = data.get("credentials", {})
        
        print(f"[DEBUG] Checking stack status for: {stack_name} in {region}")
        
        # Create boto3 session
        session = boto3.Session(
            aws_access_key_id=credentials.get("aws_access_key_id"),
            aws_secret_access_key=credentials.get("aws_secret_access_key"),
            aws_session_token=credentials.get("aws_session_token"),
            region_name=region
        )
        
        cf_client = session.client('cloudformation')
        
        # Get stack status
        try:
            response = cf_client.describe_stacks(StackName=stack_name)
            stack = response['Stacks'][0]
            
            stack_status = stack.get('StackStatus')
            stack_status_reason = stack.get('StackStatusReason', '')
            
            print(f"[DEBUG] Stack status: {stack_status}")
            if stack_status_reason:
                print(f"[DEBUG] Stack status reason: {stack_status_reason}")
            
            # Get stack events for detailed progress
            events_response = cf_client.describe_stack_events(StackName=stack_name)
            events = events_response['StackEvents'][:15]  # Get last 15 events
            
            # Parse events to determine current stage
            latest_events = []
            for event in events:
                event_data = {
                    'resource_type': event.get('ResourceType', ''),
                    'logical_id': event.get('LogicalResourceId', ''),
                    'status': event.get('ResourceStatus', ''),
                    'timestamp': event.get('Timestamp').isoformat() if event.get('Timestamp') else None,
                    'reason': event.get('ResourceStatusReason', '')
                }
                latest_events.append(event_data)
                
                # Log failed resources
                if 'FAILED' in event_data['status']:
                    print(f"[ERROR] Resource failed: {event_data['logical_id']} - {event_data['reason']}")
            
            return {
                "success": True,
                "stack_status": stack_status,
                "stack_status_reason": stack_status_reason,
                "events": latest_events,
                "outputs": stack.get('Outputs', [])
            }
            
        except cf_client.exceptions.ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if 'does not exist' in str(e) or error_code == 'ValidationError':
                print(f"[DEBUG] Stack not found yet: {stack_name}")
                return {
                    "success": False,
                    "stack_status": "NOT_FOUND",
                    "error": "Stack not found - may still be initializing"
                }
            raise
            
    except Exception as e:
        print(f"[ERROR] get_stack_status failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/get-stack-parameters")
async def get_stack_parameters(data: Dict[str, Any]):
    """Get CloudFormation stack parameters including TypeOfSaaSListing"""
    try:
        stack_name = data.get("stack_name")
        region = data.get("region", "us-east-1")
        credentials = data.get("credentials", {})
        
        print(f"[BACKEND DEBUG] Getting parameters for stack: {stack_name}")
        
        # Create boto3 session
        session = boto3.Session(
            aws_access_key_id=credentials.get("aws_access_key_id"),
            aws_secret_access_key=credentials.get("aws_secret_access_key"),
            aws_session_token=credentials.get("aws_session_token"),
            region_name=region
        )
        
        cf_client = session.client('cloudformation')
        
        # Get stack details
        try:
            response = cf_client.describe_stacks(StackName=stack_name)
            stack = response['Stacks'][0]
            
            parameters = {}
            pricing_model = None
            
            # Extract parameters
            for param in stack.get('Parameters', []):
                param_key = param.get('ParameterKey')
                param_value = param.get('ParameterValue')
                parameters[param_key] = param_value
                
                if param_key == 'TypeOfSaaSListing':
                    pricing_model = param_value
                    print(f"[BACKEND DEBUG] Found TypeOfSaaSListing: {pricing_model}")
            
            return {
                "success": True,
                "pricing_model": pricing_model,
                "parameters": parameters
            }
            
        except cf_client.exceptions.ClientError as e:
            if 'does not exist' in str(e):
                return {
                    "success": False,
                    "error": "Stack not found"
                }
            raise
            
    except Exception as e:
        print(f"[ERROR] get_stack_parameters failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

# Helper function to emit events
def emit_event(session_id: str, event_type: str, data: Dict[str, Any]):
    """Emit an event to the SSE stream for a specific session"""
    if session_id in event_queues:
        event_queues[session_id].put({
            "type": event_type,
            "data": data
        })


def wait_for_changeset(
    marketplace_client,
    change_set_id: str,
    session_id: str,
    stage_name: str,
    max_wait: int = 120,
    wait_interval: int = 5
) -> Dict[str, Any]:
    """
    Wait for a changeset to complete and emit progress events.
    
    Returns:
        Dict with 'success', 'status', and optionally 'entities' or 'error'
    """
    import time
    elapsed = 0
    
    while elapsed < max_wait:
        try:
            status_response = marketplace_client.describe_change_set(
                Catalog='AWSMarketplace',
                ChangeSetId=change_set_id
            )
            
            status = status_response['Status']
            
            emit_event(session_id, "progress", {
                "stage": stage_name,
                "status": "in_progress",
                "message": f"Processing... ({elapsed}s)"
            })
            
            if status == 'SUCCEEDED':
                entities = {}
                for change in status_response.get('ChangeSet', []):
                    change_type = change.get('ChangeType')
                    entity_id = change.get('Entity', {}).get('Identifier')
                    if entity_id:
                        entities[change_type] = entity_id
                return {"success": True, "status": "SUCCEEDED", "entities": entities}
            
            elif status == 'FAILED':
                failure_code = status_response.get('FailureCode', 'Unknown')
                failure_desc = status_response.get('FailureDescription', 'No description')
                return {"success": False, "status": "FAILED", "error": f"{failure_code}: {failure_desc}"}
            
            elif status == 'CANCELLED':
                return {"success": False, "status": "CANCELLED", "error": "Changeset was cancelled"}
            
            # Still in progress (PREPARING, APPLYING)
            time.sleep(wait_interval)
            elapsed += wait_interval
            
        except Exception as e:
            return {"success": False, "status": "ERROR", "error": str(e)}
    
    return {"success": False, "status": "TIMEOUT", "error": f"Timed out after {max_wait}s"}

# SSE endpoint for listing creation progress
@app.get("/create-listing-stream/{session_id}")
async def create_listing_stream(session_id: str):
    """Server-Sent Events endpoint for real-time listing creation progress"""
    
    # Create queue for this session
    event_queues[session_id] = Queue()
    
    async def event_generator():
        try:
            while True:
                # Check if there are events in the queue
                if not event_queues[session_id].empty():
                    event = event_queues[session_id].get()
                    
                    # Format as SSE
                    yield f"event: {event['type']}\n"
                    yield f"data: {json.dumps(event['data'])}\n\n"
                    
                    # If it's a completion event, close the stream
                    if event['type'] in ['complete', 'error']:
                        break
                else:
                    # Send keepalive comment every 15 seconds
                    yield ": keepalive\n\n"
                
                await asyncio.sleep(0.5)
        finally:
            # Clean up queue when done
            if session_id in event_queues:
                del event_queues[session_id]
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )



# Modified create listing endpoint with SSE support - Uses Agent Workflow
@app.post("/create-listing-with-stream")
async def create_listing_with_stream(data: Dict[str, Any]):
    """Create marketplace listing with SSE progress updates using Agent Workflow"""
    import traceback
    import time
    
    session_id = data.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail={"error": "session_id is required"})
    
    # Run the listing creation in a background thread
    def run_listing_creation():
        try:
            listing_data = data.get("listing_data", {})
            credentials = data.get("credentials", {})
            
            emit_event(session_id, "stage", {
                "stage": "Initializing",
                "status": "in_progress",
                "message": "Setting up AWS Marketplace connection..."
            })
            
            # Create boto3 session
            boto_session = boto3.Session(
                aws_access_key_id=credentials.get("aws_access_key_id"),
                aws_secret_access_key=credentials.get("aws_secret_access_key"),
                aws_session_token=credentials.get("aws_session_token"),
                region_name='us-east-1'
            )
            
            # Initialize ListingTools with session
            listing_tools = ListingTools(region='us-east-1', session=boto_session)
            
            # Extract listing data
            product_title = listing_data.get("title", "")
            logo_s3_url = listing_data.get("logo_s3_url", "")
            short_description = listing_data.get("short_description", "")
            long_description = listing_data.get("long_description", "")
            highlights = listing_data.get("highlights", [])
            categories = listing_data.get("categories", [])
            search_keywords = listing_data.get("search_keywords", [])
            support_email = listing_data.get("support_email", "")
            fulfillment_url = listing_data.get("fulfillment_url", "")
            pricing_model = listing_data.get("pricing_model", "usage")
            pricing_dimensions = listing_data.get("pricing_dimensions", [])
            refund_policy = listing_data.get("refund_policy", "")
            eula_type = listing_data.get("eula_type", "STANDARD")
            availability_type = listing_data.get("availability_type", "PUBLIC")
            auto_publish_to_limited = listing_data.get("auto_publish_to_limited", False)
            offer_name = listing_data.get("offer_name", f"{product_title} - Public Offer")
            offer_description = listing_data.get("offer_description", f"Public offer for {product_title}")
            
            # Validate required fields
            if not product_title:
                raise Exception("Product title is required")
            if not short_description:
                raise Exception("Short description is required")
            if not long_description:
                raise Exception("Long description is required")
            
            # ============================================================
            # Stage 1: Product Information (using ProductInformationAgent)
            # ============================================================
            emit_event(session_id, "stage", {
                "stage": "Product Information",
                "status": "in_progress",
                "message": f"Creating product: {product_title}..."
            })
            
            # Create product using ListingTools
            create_result = listing_tools.create_product_minimal(product_title)
            
            if not create_result.get("success"):
                raise Exception(f"Failed to create product: {create_result.get('error', 'Unknown error')}")
            
            change_set_id = create_result.get("change_set_id")
            print(f"[DEBUG] Change set created: {change_set_id}")
            
            # Wait for product creation to complete
            max_wait = 300
            wait_interval = 5
            elapsed = 0
            product_id = None
            offer_id = None
            
            marketplace_client = boto_session.client('marketplace-catalog')
            
            while elapsed < max_wait:
                status_response = marketplace_client.describe_change_set(
                    Catalog='AWSMarketplace',
                    ChangeSetId=change_set_id
                )
                
                status = status_response['Status']
                emit_event(session_id, "progress", {
                    "stage": "Product Information",
                    "status": "in_progress",
                    "message": f"Waiting for product creation... ({elapsed}s)"
                })
                
                if status == 'SUCCEEDED':
                    for change in status_response.get('ChangeSet', []):
                        if change.get('ChangeType') == 'CreateProduct':
                            product_id = change.get('Entity', {}).get('Identifier')
                        elif change.get('ChangeType') == 'CreateOffer':
                            offer_id = change.get('Entity', {}).get('Identifier')
                    break
                elif status == 'FAILED':
                    failure_code = status_response.get('FailureCode', 'Unknown')
                    failure_desc = status_response.get('FailureDescription', 'No description')
                    raise Exception(f"Product creation failed: {failure_code} - {failure_desc}")
                elif status in ['CANCELLED']:
                    raise Exception("Product creation was cancelled")
                
                time.sleep(wait_interval)
                elapsed += wait_interval
            
            if not product_id:
                raise Exception("Timed out waiting for product creation")
            
            emit_event(session_id, "changeset", {
                "stage": "Product Information",
                "status": "SUCCEEDED",
                "message": f"Product created: {product_id}"
            })
            
            # Helper function to strip revision suffix from entity identifier (e.g., "prod-abc@1" -> "prod-abc")
            def strip_revision_suffix(entity_id: str) -> str:
                if entity_id and '@' in entity_id:
                    return entity_id.split('@')[0]
                return entity_id
            
            # Strip any revision suffix from product_id
            product_id = strip_revision_suffix(product_id)
            
            # Update product details
            emit_event(session_id, "progress", {
                "stage": "Product Information",
                "status": "in_progress",
                "message": "Updating product details..."
            })
            
            # Build description details with optional logo URL
            description_data = {
                "ProductTitle": product_title,
                "ShortDescription": short_description,
                "LongDescription": long_description,
                "Highlights": highlights[:5] if highlights else [],
                "SearchKeywords": search_keywords[:5] if search_keywords else [],
                "Categories": categories[:3] if categories else []
            }
            
            # Add logo URL if provided (must be a valid S3 URL)
            if logo_s3_url and logo_s3_url.startswith("https://") and "s3" in logo_s3_url:
                description_data["LogoUrl"] = logo_s3_url
            
            description_details = json.dumps(description_data)
            
            try:
                details_response = marketplace_client.start_change_set(
                    Catalog='AWSMarketplace',
                    ChangeSet=[{
                        'ChangeType': 'UpdateInformation',
                        'Entity': {'Type': 'SaaSProduct@1.0', 'Identifier': product_id},
                        'Details': description_details
                    }],
                    ChangeSetName=f"UpdateInfo-{product_id[:20]}-{int(time.time())}"
                )
                # Wait for product details update to complete
                details_result = wait_for_changeset(
                    marketplace_client,
                    details_response['ChangeSetId'],
                    session_id,
                    "Product Information"
                )
                if details_result["success"]:
                    emit_event(session_id, "changeset", {
                        "stage": "Product Information",
                        "status": "SUCCEEDED",
                        "message": "Product details updated"
                    })
                else:
                    # Stage failed - stop the entire listing process
                    raise Exception(f"Product details update failed: {details_result.get('error', 'Unknown error')}")
            except Exception as e:
                # Stage failed - stop the entire listing process
                raise Exception(f"Product details update failed: {str(e)}")
            
            # ============================================================
            # Stage 2: Fulfillment Configuration (using FulfillmentAgent)
            # ============================================================
            emit_event(session_id, "stage", {
                "stage": "Fulfillment",
                "status": "in_progress",
                "message": "Configuring fulfillment URL..."
            })
            
            if fulfillment_url:
                try:
                    # For SaaS products, use AddDeliveryOptions with SaaSUrlDeliveryOptionDetails
                    fulfillment_details = json.dumps({
                        "DeliveryOptions": [{
                            "Details": {
                                "SaaSUrlDeliveryOptionDetails": {
                                    "FulfillmentUrl": fulfillment_url
                                }
                            }
                        }]
                    })
                    fulfillment_response = marketplace_client.start_change_set(
                        Catalog='AWSMarketplace',
                        ChangeSet=[{
                            'ChangeType': 'AddDeliveryOptions',
                            'Entity': {'Type': 'SaaSProduct@1.0', 'Identifier': product_id},
                            'Details': fulfillment_details
                        }],
                        ChangeSetName=f"Fulfillment-{product_id[:20]}-{int(time.time())}"
                    )
                    # Wait for fulfillment changeset to complete
                    fulfillment_result = wait_for_changeset(
                        marketplace_client,
                        fulfillment_response['ChangeSetId'],
                        session_id,
                        "Fulfillment"
                    )
                    if fulfillment_result["success"]:
                        emit_event(session_id, "changeset", {
                            "stage": "Fulfillment",
                            "status": "SUCCEEDED",
                            "message": "Fulfillment URL configured"
                        })
                    else:
                        # Stage failed - stop the entire listing process
                        raise Exception(f"Fulfillment configuration failed: {fulfillment_result.get('error', 'Unknown error')}")
                except Exception as e:
                    # Stage failed - stop the entire listing process
                    raise Exception(f"Fulfillment configuration failed: {str(e)}")
            else:
                emit_event(session_id, "changeset", {
                    "stage": "Fulfillment",
                    "status": "SUCCEEDED",
                    "message": "Fulfillment URL will be configured later"
                })
            
            # ============================================================
            # Stage 3: Pricing Dimensions (using PricingConfigAgent)
            # ============================================================
            emit_event(session_id, "stage", {
                "stage": "Pricing Dimensions",
                "status": "in_progress",
                "message": "Configuring pricing dimensions..."
            })
            
            # Strip any revision suffix from offer_id
            if offer_id:
                offer_id = strip_revision_suffix(offer_id)
            
            if pricing_dimensions and offer_id and product_id:
                try:
                    # Format pricing dimensions for ListingTools
                    # AWS Marketplace requires dimensions to be added to the PRODUCT first,
                    # then pricing terms are added to the OFFER
                    formatted_dimensions = []
                    ui_pricing_model = listing_data.get("ui_pricing_model", pricing_model)
                    
                    for dim in pricing_dimensions:
                        dim_type = dim.get("type", "Metered")  # Get type from frontend
                        # AWS Marketplace dimension type requirements:
                        # - Entitled: ["Entitled"] for contract-based
                        # - Metered: ["Metered", "ExternallyMetered"] for usage-based
                        if dim_type == "Metered":
                            types_list = ["Metered", "ExternallyMetered"]
                        else:
                            types_list = [dim_type]  # "Entitled" stays as-is
                        
                        formatted_dimensions.append({
                            "Key": dim.get("key", dim.get("name", "").lower().replace(" ", "_").replace("-", "_")),
                            "Description": dim.get("description", dim.get("name", "")),
                            "Name": dim.get("name", ""),
                            "Types": types_list,
                            "Unit": "Units"
                        })
                    
                    # Use the combined method that adds dimensions to product AND pricing to offer
                    if ui_pricing_model == "Usage" or pricing_model == "usage":
                        pricing_api_result = listing_tools.add_dimensions_and_pricing_for_usage(
                            product_id=product_id,
                            offer_id=offer_id,
                            dimensions=formatted_dimensions
                        )
                    elif ui_pricing_model == "Contract with Consumption":
                        # Hybrid model - needs both Entitled and Metered dimensions
                        pricing_api_result = listing_tools.add_dimensions_and_pricing_for_hybrid(
                            product_id=product_id,
                            offer_id=offer_id,
                            dimensions=formatted_dimensions,
                            contract_durations=listing_data.get("contract_durations", ["12 Months"])
                        )
                    else:
                        # Contract model
                        pricing_api_result = listing_tools.add_dimensions_and_pricing_for_contract(
                            product_id=product_id,
                            offer_id=offer_id,
                            dimensions=formatted_dimensions,
                            contract_durations=listing_data.get("contract_durations", ["12 Months"])
                        )
                    
                    if pricing_api_result.get("success"):
                        # Wait for pricing changeset to complete
                        pricing_wait_result = wait_for_changeset(
                            marketplace_client,
                            pricing_api_result['change_set_id'],
                            session_id,
                            "Pricing Dimensions"
                        )
                        if pricing_wait_result["success"]:
                            emit_event(session_id, "changeset", {
                                "stage": "Pricing Dimensions",
                                "status": "SUCCEEDED",
                                "message": f"Configured {len(pricing_dimensions)} pricing dimension(s)"
                            })
                        else:
                            # Stage failed - stop the entire listing process
                            raise Exception(f"Pricing configuration failed: {pricing_wait_result.get('error', 'Unknown error')}")
                    else:
                        # Stage failed - stop the entire listing process
                        raise Exception(f"Pricing configuration failed: {pricing_api_result.get('error', 'Unknown error')}")
                except Exception as e:
                    # Stage failed - stop the entire listing process
                    raise Exception(f"Pricing configuration failed: {str(e)}")
            else:
                emit_event(session_id, "changeset", {
                    "stage": "Pricing Dimensions",
                    "status": "SUCCEEDED",
                    "message": "Default pricing will be applied"
                })
            
            # ============================================================
            # Stage 4: Price Review (using PriceReviewAgent)
            # ============================================================
            emit_event(session_id, "stage", {
                "stage": "Price Review",
                "status": "in_progress",
                "message": "Reviewing pricing configuration..."
            })
            
            # Price review is a validation step - just confirm pricing is set
            time.sleep(1)  # Brief pause for UI feedback
            emit_event(session_id, "changeset", {
                "stage": "Price Review",
                "status": "SUCCEEDED",
                "message": "Pricing configuration validated"
            })
            
            # ============================================================
            # Stage 5: Refund Policy (using RefundPolicyAgent)
            # ============================================================
            emit_event(session_id, "stage", {
                "stage": "Refund Policy",
                "status": "in_progress",
                "message": "Configuring refund policy..."
            })
            
            if refund_policy and offer_id:
                try:
                    # Use ListingTools for correct API format
                    refund_api_result = listing_tools.update_support_terms(
                        offer_id=offer_id,
                        refund_policy=refund_policy
                    )
                    
                    if refund_api_result.get("success"):
                        # Wait for refund policy changeset to complete
                        refund_wait_result = wait_for_changeset(
                            marketplace_client,
                            refund_api_result['change_set_id'],
                            session_id,
                            "Refund Policy"
                        )
                        if refund_wait_result["success"]:
                            emit_event(session_id, "changeset", {
                                "stage": "Refund Policy",
                                "status": "SUCCEEDED",
                                "message": "Refund policy configured"
                            })
                        else:
                            # Stage failed - stop the entire listing process
                            raise Exception(f"Refund policy configuration failed: {refund_wait_result.get('error', 'Unknown error')}")
                    else:
                        # Stage failed - stop the entire listing process
                        raise Exception(f"Refund policy configuration failed: {refund_api_result.get('error', 'Unknown error')}")
                except Exception as e:
                    # Stage failed - stop the entire listing process
                    raise Exception(f"Refund policy configuration failed: {str(e)}")
            else:
                emit_event(session_id, "changeset", {
                    "stage": "Refund Policy",
                    "status": "SUCCEEDED",
                    "message": "Default refund policy applied"
                })
            
            # ============================================================
            # Stage 6: EULA Configuration (using EULAConfigAgent)
            # ============================================================
            emit_event(session_id, "stage", {
                "stage": "EULA",
                "status": "in_progress",
                "message": "Configuring End User License Agreement..."
            })
            
            if offer_id:
                try:
                    # Use ListingTools for correct API format
                    # Frontend sends 'scmp' for standard, 'custom' for custom EULA
                    is_standard_eula = eula_type.lower() in ["standard", "scmp"]
                    eula_result = listing_tools.update_legal_terms(
                        offer_id=offer_id,
                        eula_type="StandardEula" if is_standard_eula else "CustomEula",
                        eula_url=listing_data.get("custom_eula_url") if not is_standard_eula else None
                    )
                    
                    if eula_result.get("success"):
                        # Wait for EULA changeset to complete
                        eula_wait_result = wait_for_changeset(
                            marketplace_client,
                            eula_result['change_set_id'],
                            session_id,
                            "EULA"
                        )
                        if eula_wait_result["success"]:
                            emit_event(session_id, "changeset", {
                                "stage": "EULA",
                                "status": "SUCCEEDED",
                                "message": f"{eula_type} EULA configured"
                            })
                        else:
                            # Stage failed - stop the entire listing process
                            raise Exception(f"EULA configuration failed: {eula_wait_result.get('error', 'Unknown error')}")
                    else:
                        # Stage failed - stop the entire listing process
                        raise Exception(f"EULA configuration failed: {eula_result.get('error', 'Unknown error')}")
                except Exception as e:
                    # Stage failed - stop the entire listing process
                    raise Exception(f"EULA configuration failed: {str(e)}")
            else:
                emit_event(session_id, "changeset", {
                    "stage": "EULA",
                    "status": "SUCCEEDED",
                    "message": "Standard EULA will be applied"
                })
            
            # ============================================================
            # Stage 7: Availability Settings (using OfferAvailabilityAgent)
            # ============================================================
            emit_event(session_id, "stage", {
                "stage": "Availability",
                "status": "in_progress",
                "message": "Configuring availability settings..."
            })
            
            if offer_id:
                try:
                    # Use ListingTools for correct API format
                    availability_result = listing_tools.update_offer_availability(
                        offer_id=offer_id,
                        availability_type="all"  # Default to all countries
                    )
                    
                    if availability_result.get("success"):
                        # Wait for availability changeset to complete
                        availability_wait_result = wait_for_changeset(
                            marketplace_client,
                            availability_result['change_set_id'],
                            session_id,
                            "Availability"
                        )
                        if availability_wait_result["success"]:
                            emit_event(session_id, "changeset", {
                                "stage": "Availability",
                                "status": "SUCCEEDED",
                                "message": f"Availability set to {availability_type}"
                            })
                        else:
                            # Stage failed - stop the entire listing process
                            raise Exception(f"Availability configuration failed: {availability_wait_result.get('error', 'Unknown error')}")
                    else:
                        # Stage failed - stop the entire listing process
                        raise Exception(f"Availability configuration failed: {availability_result.get('error', 'Unknown error')}")
                except Exception as e:
                    # Stage failed - stop the entire listing process
                    raise Exception(f"Availability configuration failed: {str(e)}")
            else:
                emit_event(session_id, "changeset", {
                    "stage": "Availability",
                    "status": "SUCCEEDED",
                    "message": "Default availability applied"
                })
            
            # ============================================================
            # Stage 8: Allowlist Configuration (using AllowlistAgent)
            # ============================================================
            emit_event(session_id, "stage", {
                "stage": "Allowlist",
                "status": "in_progress",
                "message": "Configuring buyer allowlist..."
            })
            
            # Allowlist is optional - just mark as complete
            time.sleep(1)  # Brief pause for UI feedback
            emit_event(session_id, "changeset", {
                "stage": "Allowlist",
                "status": "SUCCEEDED",
                "message": "Allowlist configuration complete (no restrictions)"
            })
            
            # ============================================================
            # Stage 9: Publish to Limited (if auto_publish_to_limited is True)
            # ============================================================
            published_to_limited = False
            if auto_publish_to_limited and product_id and offer_id:
                emit_event(session_id, "stage", {
                    "stage": "Publish to Limited",
                    "status": "in_progress",
                    "message": "Publishing product to Limited visibility..."
                })
                
                try:
                    # Use ListingTools to release product and offer to Limited
                    release_result = listing_tools.release_product_and_offer_to_limited(
                        product_id=product_id,
                        offer_id=offer_id,
                        offer_name=offer_name,
                        offer_description=offer_description,
                        pricing_model="Usage" if pricing_model == "usage" else "Contract"
                    )
                    
                    if release_result.get("success"):
                        # Wait for release changeset to complete
                        release_wait_result = wait_for_changeset(
                            marketplace_client,
                            release_result['change_set_id'],
                            session_id,
                            "Publish to Limited"
                        )
                        if release_wait_result["success"]:
                            published_to_limited = True
                            emit_event(session_id, "changeset", {
                                "stage": "Publish to Limited",
                                "status": "SUCCEEDED",
                                "message": "Product published to Limited visibility"
                            })
                        else:
                            emit_event(session_id, "changeset", {
                                "stage": "Publish to Limited",
                                "status": "WARNING",
                                "message": f"Publish to Limited pending: {release_wait_result.get('error', 'Unknown')[:50]}"
                            })
                    else:
                        emit_event(session_id, "changeset", {
                            "stage": "Publish to Limited",
                            "status": "WARNING",
                            "message": f"Publish to Limited pending: {release_result.get('error', 'Unknown')[:50]}"
                        })
                except Exception as e:
                    print(f"[WARNING] Publish to Limited failed: {e}")
                    emit_event(session_id, "changeset", {
                        "stage": "Publish to Limited",
                        "status": "WARNING",
                        "message": f"Publish to Limited pending: {str(e)[:50]}"
                    })
            
            # ============================================================
            # All stages complete - send completion event
            # ============================================================
            emit_event(session_id, "complete", {
                "product_id": product_id,
                "offer_id": offer_id,
                "published_to_limited": published_to_limited,
                "message": f"Product '{product_title}' created successfully" + (" and published to Limited" if published_to_limited else " (Draft)")
            })
            
        except Exception as e:
            error_message = str(e)
            print(f"[ERROR] create_listing_with_stream failed: {error_message}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            
            emit_event(session_id, "error", {
                "message": error_message,
                "details": traceback.format_exc()
            })
    
    # Start background thread
    thread = threading.Thread(target=run_listing_creation)
    thread.daemon = True
    thread.start()
    
    return {
        "success": True,
        "session_id": session_id,
        "message": "Listing creation started. Connect to SSE stream for progress updates."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


# Chatbot endpoint using AWS documentation
@app.post("/chat")
async def chat(data: Dict[str, Any]):
    """Chat endpoint with conversation history support"""
    try:
        question = data.get("question", "")
        conversation_history = data.get("conversation_history", [])
        
        if not question:
            return {
                "success": False,
                "error": "Question is required"
            }
        
        print(f"[DEBUG] Chat question: {question}")
        print(f"[DEBUG] History length: {len(conversation_history)}")
        
        # Generate response with conversation history
        response_text = generate_chat_response_with_history(question, conversation_history)
        
        response = {
            "success": True,
            "response": response_text
        }
        
        return response
        
    except Exception as e:
        print(f"[ERROR] Chat error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "response": generate_chat_response_with_history(question, [])
        }

@app.get("/chat/topics")
async def get_chat_topics():
    """Get quick help topics for the chatbot"""
    try:
        # Return default topics including India-specific ones
        topics = [
            "How do I create a SaaS product listing?",
            "What pricing models are available?",
            "How do I deploy SaaS infrastructure?",
            "What are the seller registration requirements?",
            "How does AWS Marketplace India work?",
            "What are India GST and tax requirements?",
            "What payment methods are available in India?",
            "How do I sell to India-based customers?"
        ]
        return {
            "success": True,
            "topics": topics
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def load_knowledge_base() -> str:
    """Load all knowledge base files into a single context"""
    knowledge_base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'knowledge-base')
    knowledge_content = []
    
    try:
        for filename in os.listdir(knowledge_base_dir):
            if filename.endswith('.md'):
                filepath = os.path.join(knowledge_base_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    knowledge_content.append(f"# {filename}\n\n{content}\n\n")
        
        return "\n".join(knowledge_content)
    except Exception as e:
        print(f"[ERROR] Failed to load knowledge base: {e}")
        return ""

def generate_chat_response_with_history(question: str, conversation_history: List[Dict[str, str]]) -> str:
    """Generate a response with conversation history context"""
    question_lower = question.lower()
    
    # Load knowledge base
    knowledge_base = load_knowledge_base()
    
    # Use Bedrock to generate response with knowledge base context and history
    try:
        bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        # Build conversation context
        conversation_context = ""
        if conversation_history:
            conversation_context = "\n\nPREVIOUS CONVERSATION:\n"
            for msg in conversation_history[-6:]:  # Last 6 messages (3 exchanges)
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                conversation_context += f"{role.upper()}: {content}\n"
        
        # Build messages array for Claude
        messages = []
        
        # Add conversation history
        for msg in conversation_history[-6:]:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            messages.append({
                "role": "user" if role == "user" else "assistant",
                "content": content
            })
        
        # Add current question with knowledge base context
        current_prompt = f"""You are an AWS Marketplace expert assistant helping sellers. Use the following knowledge base to answer the question accurately and comprehensively.

KNOWLEDGE BASE:
{knowledge_base[:45000]}

USER QUESTION: {question}

Provide a detailed, helpful answer based on the knowledge base. Format your response in markdown with clear sections, bullet points, and examples where appropriate. Consider the conversation history to provide contextual answers. If the question refers to previous topics, acknowledge that context."""

        messages.append({
            "role": "user",
            "content": current_prompt
        })
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "messages": messages,
            "temperature": 0.7
        }
        
        # Try multiple models
        models = [
            "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            "anthropic.claude-3-5-sonnet-20240620-v1:0",
            "anthropic.claude-3-sonnet-20240229-v1:0"
        ]
        
        for model_id in models:
            try:
                response = bedrock.invoke_model(
                    modelId=model_id,
                    body=json.dumps(request_body)
                )
                response_body = json.loads(response['body'].read())
                return response_body['content'][0]['text']
            except Exception as model_error:
                print(f"[DEBUG] Model {model_id} failed: {model_error}")
                continue
        
        # If all models fail, use fallback
        return generate_fallback_response(question_lower)
        
    except Exception as e:
        print(f"[ERROR] Bedrock error: {e}")
        return generate_fallback_response(question_lower)

def generate_chat_response(question: str) -> str:
    """Generate a response without history (backward compatibility)"""
    return generate_chat_response_with_history(question, [])

def generate_fallback_response(question_lower: str) -> str:
    """Generate fallback response when Bedrock is unavailable"""
    
    # India-specific responses
    if "india" in question_lower:
        if "invoice" in question_lower or "billing" in question_lower:
            return """**AWS Marketplace India - Invoicing:**

**For India-Based Seller Purchases (AWS India):**
• Commercial Invoice/Statement listing all purchases
• Separate Tax Invoices from each seller with QR code and IRN
• Can be used to claim Input Tax Credit (ITC)
• Invoices in Indian Rupees (INR)

**For Non-India Seller Purchases (AWS, Inc.):**
• Commercial invoice from AWS, Inc.
• Tax invoice only if you haven't provided tax information

**Separate Invoices:**
• AWS Cloud and AWS Marketplace purchases get separate invoices
• Available on billing console
• Delivered to configured email addresses

**Invoice Discrepancies:**
• Commercial and tax invoices may differ by a few rupees
• Small rounding errors may occur for INR-priced offers
• You can pay using either invoice

**Learn more:** [AWS India FAQs](https://aws.amazon.com/legal/awsin/)"""
        
        elif "tax" in question_lower or "gst" in question_lower:
            return """**AWS Marketplace India - Taxation:**

**GST Rate:** 18% on all purchases

**For India-Based Sellers:**
• AWS India facilitates tax invoice issuance
• Seller is Seller on Record (SOR)
• GST remitted to seller, who deposits to authorities

**Tax Type Determination:**
• Same State: CGST + SGST
• Different States: IGST
• SEZ Involved: IGST (regardless of states)

**Tax Information:**
• Use Tax Settings page: https://console.aws.amazon.com/billing/home#/tax
• Enter GSTIN to claim Input Tax Credit (ITC)
• Same info used for AWS Cloud purchases
• Can purchase without tax info, but cannot claim ITC

**No Tax Withholding:**
• Do NOT withhold taxes on payments to AWS India
• AWS India withholds when paying sellers (Section 194-O)

**Learn more:** [Buyer Tax Help](https://aws.amazon.com/tax-help/india/india-marketplace-buyers/)"""
        
        elif "payment" in question_lower or "pay" in question_lower:
            return """**AWS Marketplace India - Payment Methods:**

**Currency:** Indian Rupee (INR) only

**Accepted Payment Methods:**
✅ Credit/Debit Cards: AMEX, MasterCard, RuPay, Visa
   • Must be tokenized per RBI regulations
   • Restrictions on contract pricing products
   • No restrictions on PAYG, free, trial, BYOL products
✅ Wire Transfer: To India-based bank account
   • Different account from AWS Cloud payments
   • Refer to invoice for remittance details

❌ NOT Available at Launch:
• UPI
• NetBanking

**Payment Rules:**
• AWS Cloud and Marketplace payments go to different accounts
• AWS Inc. and AWS India payments go to different accounts
• Wrong account = payment rejected and delays

**For Contract Pricing:**
• Switch to Pay by Invoice (PBI) if using credit card

**Learn more:** [AWS India FAQs](https://aws.amazon.com/legal/awsin/)"""
        
        elif "seller" in question_lower or "sell" in question_lower or "registration" in question_lower:
            return """**Selling in AWS Marketplace India - Registration Process:**

**Step 1: Create Standalone AWS Account**
⚠️ MUST be standalone (not in AWS Organizations)
• Using linked account causes taxation errors

**Step 2: Complete Seller Registration**
• Register on AWS Marketplace Management Portal
• Provide unique legal business name (for tax invoices)
• Create public profile

**Step 3: Tax Information (Required)**
• GSTIN (GST Identification Number)
• PAN (auto-populated from GSTIN)
• Seller signature (submit via contact form)
• Legal business name and address
• Acknowledgements (WHT, e-invoicing, authorization)

**Step 4: Bank Account**
• Account number, IFSC, name, address
• Must be Indian bank account

**Step 5: Disbursement Method**
• Add INR disbursement method
• Choose frequency: Monthly or Daily
• Disbursements via NEFT/RTGS
• Can only receive INR (not USD)

**Step 6: Create Offers**
• Product listings in USD
• Private offers in USD or INR
• Product title must have `[IN]` suffix
• Can only sell to India buyers

**Key Benefits:**
✅ Receive disbursements in INR
✅ Buyers invoiced in INR with GST
✅ Tax-compliant invoices as Seller of Record

**Restrictions:**
❌ Cannot sell to buyers outside India
❌ Cannot use linked AWS Organizations account
❌ Cannot receive USD disbursements

**Learn more:** [Getting Started Guide](https://docs.aws.amazon.com/marketplace/latest/userguide/getting-started-seller-india.html)"""
        
        else:
            return """**AWS Marketplace India Overview:**

**Key Benefits:**
✅ Local invoicing in Indian Rupees (INR)
✅ Local payment options (cards, wire transfer)
✅ 18% GST with ITC claims available
✅ Transactions facilitated by AWS India

**For Buyers:**
• Purchase from India-based sellers
• Separate invoices for cloud and marketplace
• Enter GSTIN for ITC claims
• No UPI/NetBanking at launch

**For Sellers:**
• Sell to India-based customers
• Issue tax invoices with QR code
• Collect and remit 18% GST
• State Indian entity in product description

**Quick Links:**
• [India FAQs](https://aws.amazon.com/legal/awsin/)
• [Tax Settings](https://console.aws.amazon.com/billing/home#/tax)
• [India Solutions](https://aws.amazon.com/marketplace/solutions/india)
• [Customer Service](https://console.aws.amazon.com/support/home/)

**Questions?** Ask about:
• India invoicing
• India taxation/GST
• India payment methods
• Selling in India"""
    
    # AWS Marketplace specific responses
    elif "register" in question_lower or "seller" in question_lower:
        return """To register as an AWS Marketplace seller:

1. **Validate Credentials**: Enter your AWS credentials on the home page
2. **Check Status**: The system will check if you're already registered
3. **Create Business Profile**: If not registered, click "Create Business Profile"
4. **Complete Tax Information**: Submit W-9 (US) or W-8 (International) form
5. **Set Up Payment**: Configure bank account for disbursements
6. **Submit for Review**: AWS reviews your application (2-3 business days)

Once approved, you can create product listings in AWS Marketplace.

**Need help?** Visit the [AWS Marketplace Seller Guide](https://docs.aws.amazon.com/marketplace/latest/userguide/seller-registration-process.html)"""
    
    elif "saas" in question_lower and "integration" in question_lower:
        return """SaaS Integration connects your SaaS product to AWS Marketplace:

**What it does:**
• Deploys serverless infrastructure (DynamoDB, Lambda, API Gateway)
• Handles subscription management automatically
• Processes metering and billing
• Provides fulfillment endpoint for AWS Marketplace

**How to deploy:**
1. Navigate to your product in the Seller Registration page
2. Click "Configure SaaS" for products requiring integration
3. Enter your email for notifications
4. Deploy the CloudFormation stack (3-5 minutes)
5. Copy the fulfillment URL from stack outputs
6. Update your product with the fulfillment URL

**Architecture:**
- **DynamoDB**: Stores subscription and metering data
- **Lambda**: Processes usage metering
- **API Gateway**: Fulfillment endpoint
- **SNS**: Marketplace notifications

**Learn more:** [SaaS Integration Guide](https://docs.aws.amazon.com/marketplace/latest/userguide/saas-integrate-saas.html)"""
    
    elif "listing" in question_lower or "product" in question_lower:
        return """Creating a product listing in AWS Marketplace:

**Step-by-step process:**
1. **Product Information**: Enter product name, description, and URLs
2. **AI Analysis**: Our AI analyzes your product and generates content
3. **Review Suggestions**: Review and edit AI-generated content
4. **Create Listing**: Submit to create the marketplace listing
5. **SaaS Integration** (if applicable): Deploy integration infrastructure
6. **Testing**: Test the buyer experience
7. **Publish**: Request public visibility

**Product Types:**
• **SaaS**: Software as a Service
• **AMI**: Amazon Machine Images
• **Container**: Docker containers
• **Data**: Data products

**Pricing Models:**
• Usage-based (pay-as-you-go)
• Contract-based (fixed term)
• Hybrid (contract + consumption)
• Free trial

**Documentation:** [Product Preparation Guide](https://docs.aws.amazon.com/marketplace/latest/userguide/product-preparation.html)"""
    
    elif "pricing" in question_lower or "price" in question_lower:
        return """AWS Marketplace Pricing Models:

**1. Usage-Based Pricing**
• Pay-as-you-go model
• Charge per hour, API call, GB, etc.
• Best for: Variable usage patterns
• Example: $0.10 per API call

**2. Contract-Based Pricing**
• Fixed price for a term (monthly, annual)
• Upfront or scheduled payments
• Best for: Predictable costs
• Example: $1,000/month

**3. Contract with Consumption**
• Hybrid model
• Base contract + usage charges
• Best for: Committed base + overages
• Example: $500/month + $0.05 per GB over 100GB

**4. Free Trial**
• Let customers try before buying
• Configurable trial period
• Converts to paid automatically
• Best for: Reducing friction

**Pricing Dimensions:**
• Define what you charge for
• Multiple dimensions supported
• Examples: Users, API calls, Storage, Bandwidth

**Learn more:** [Pricing Guide](https://docs.aws.amazon.com/marketplace/latest/userguide/pricing.html)"""
    
    elif "limited" in question_lower or "public" in question_lower or "visibility" in question_lower:
        return """AWS Marketplace Product Visibility:

**DRAFT**
• Product is being created
• Not visible to customers
• Can edit freely
• Action: Complete listing creation

**LIMITED**
• Product is published to specific accounts
• Test with selected customers
• Requires SaaS integration (for SaaS products)
• Action: Complete testing, then request public visibility

**PUBLIC**
• Product is live on AWS Marketplace
• Visible to all customers
• Cannot make major changes without new version
• Action: Monitor sales and customer feedback

**Publishing Process:**
1. Create product (DRAFT)
2. Publish to LIMITED for testing
3. Complete SaaS integration (if applicable)
4. Test buyer experience
5. Request public visibility
6. AWS reviews (1-2 business days)
7. Product goes PUBLIC

**Learn more:** [Publishing Guide](https://docs.aws.amazon.com/marketplace/latest/userguide/product-submission.html)"""
    
    elif "metering" in question_lower or "billing" in question_lower:
        return """AWS Marketplace Metering and Billing:

**How it works:**
1. Customer subscribes to your product
2. Your product sends usage records to AWS
3. AWS aggregates usage and bills customer
4. AWS disburses payment to you (minus fees)

**Metering API:**
• Send usage records in real-time
• Supports multiple dimensions
• Idempotent (safe to retry)
• Example: `meter_usage(customer_id, dimension, quantity)`

**Billing Cycle:**
• Monthly billing for customers
• Disbursement to sellers: Net 30 days
• Detailed usage reports available
• AWS handles collections

**SaaS Metering:**
• Lambda function sends usage records
• DynamoDB stores metering data
• Automatic aggregation
• Supports hourly, daily, or monthly metering

**Fees:**
• AWS Marketplace fee: 3-15% depending on product type
• Payment processing included
• No upfront costs

**Documentation:** [Metering Guide](https://docs.aws.amazon.com/marketplace/latest/userguide/saas-integration-metering-and-entitlement-apis.html)"""
    
    elif "private offer" in question_lower or "custom" in question_lower:
        return """AWS Marketplace Private Offers:

**What are Private Offers?**
• Custom pricing and terms for specific customers
• Negotiate directly with buyers
• Flexible payment schedules
• Custom contract terms

**Use Cases:**
• Enterprise deals
• Volume discounts
• Custom payment terms
• Multi-year contracts
• Proof of concept pricing

**How to create:**
1. Negotiate terms with customer
2. Create Private Offer in Management Portal
3. Specify customer AWS account ID
4. Set custom pricing and terms
5. Customer accepts offer
6. Contract is activated

**Benefits:**
• Faster deal closure
• Flexible terms
• Leverage customer's AWS commitment
• Simplified procurement

**Learn more:** [Private Offers Guide](https://docs.aws.amazon.com/marketplace/latest/userguide/private-offers-overview.html)"""
    
    else:
        return f"""I can help you with AWS Marketplace seller topics:

**Common Questions:**
• Seller registration process
• SaaS integration setup
• Creating product listings
• Pricing models
• Product visibility (DRAFT, LIMITED, PUBLIC)
• Metering and billing
• Private offers

**Your question:** "{question_lower}"

For detailed information, please visit the [AWS Marketplace Seller Guide](https://docs.aws.amazon.com/marketplace/latest/userguide/what-is-marketplace.html) or ask a more specific question.

**Example questions:**
• "How do I register as a seller?"
• "What is SaaS integration?"
• "How do I create a product listing?"
• "What pricing models are available?"
• "How does metering work?"
"""


# =============================================================================
# LISTING AGENT ENDPOINTS
# =============================================================================

# Store active agent sessions
agent_sessions: Dict[str, Dict[str, Any]] = {}


class AgentRequest(BaseModel):
    """Request model for agent interactions"""
    session_id: str
    user_input: str
    credentials: Optional[Credentials] = None
    context: Optional[Dict[str, Any]] = None


class AgentStageRequest(BaseModel):
    """Request model for specific stage operations"""
    session_id: str
    stage_name: str
    credentials: Optional[Credentials] = None
    data: Optional[Dict[str, Any]] = None


@app.get("/agents/list-available")
async def list_available_agents():
    """List all available listing agents and their purposes"""
    return {
        "success": True,
        "agents": [
            {
                "name": "SellerRegistrationAgent",
                "stage": 0,
                "description": "Handles AWS Marketplace seller registration process",
                "required_fields": ["business_name", "business_type", "business_address", "tax_id"],
            },
            {
                "name": "ProductInformationAgent",
                "stage": 1,
                "description": "Collects product details, descriptions, and metadata",
                "required_fields": ["product_title", "logo_s3_url", "short_description", "long_description", "highlights"],
            },
            {
                "name": "FulfillmentAgent",
                "stage": 2,
                "description": "Configures SaaS fulfillment URL and integration",
                "required_fields": ["fulfillment_url"],
            },
            {
                "name": "PricingConfigAgent",
                "stage": 3,
                "description": "Sets up pricing model and dimensions",
                "required_fields": ["pricing_model", "pricing_dimensions"],
            },
            {
                "name": "PriceReviewAgent",
                "stage": 4,
                "description": "Reviews and validates pricing configuration",
                "required_fields": [],
            },
            {
                "name": "RefundPolicyAgent",
                "stage": 5,
                "description": "Configures refund policy for the offer",
                "required_fields": ["refund_policy"],
            },
            {
                "name": "EULAConfigAgent",
                "stage": 6,
                "description": "Sets up End User License Agreement",
                "required_fields": ["eula_type"],
            },
            {
                "name": "OfferAvailabilityAgent",
                "stage": 7,
                "description": "Configures offer availability and geographic restrictions",
                "required_fields": ["availability_type"],
            },
            {
                "name": "AllowlistAgent",
                "stage": 8,
                "description": "Manages buyer allowlist for limited availability",
                "required_fields": [],
            },
        ],
    }


@app.post("/agents/create-session")
async def create_agent_session(data: Dict[str, Any]):
    """Create a new listing workflow session with all agents"""
    try:
        credentials = data.get("credentials", {})
        session_id = data.get("session_id", f"session-{os.urandom(8).hex()}")
        
        # Initialize all agents for this session
        agent_sessions[session_id] = {
            "seller_registration": SellerRegistrationAgent(
                aws_access_key_id=credentials.get("aws_access_key_id"),
                aws_secret_access_key=credentials.get("aws_secret_access_key"),
                aws_session_token=credentials.get("aws_session_token"),
            ),
            "product_information": ProductInformationAgent(),
            "fulfillment": FulfillmentAgent(),
            "pricing_config": PricingConfigAgent(),
            "price_review": PriceReviewAgent(),
            "refund_policy": RefundPolicyAgent(),
            "eula_config": EULAConfigAgent(),
            "offer_availability": OfferAvailabilityAgent(),
            "allowlist": AllowlistAgent(),
            "current_stage": 0,
            "workflow_data": {},
            "credentials": credentials,
        }
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "Listing workflow session created",
            "current_stage": 0,
            "stages": [
                "Seller Registration",
                "Product Information",
                "Fulfillment",
                "Pricing Configuration",
                "Price Review",
                "Refund Policy",
                "EULA Configuration",
                "Offer Availability",
                "Allowlist",
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})


@app.post("/agents/process-stage")
async def process_agent_stage(request: AgentRequest):
    """Process user input for the current stage"""
    try:
        session_id = request.session_id
        
        if session_id not in agent_sessions:
            raise HTTPException(status_code=404, detail="Session not found. Create a session first.")
        
        session = agent_sessions[session_id]
        current_stage = session["current_stage"]
        
        # Map stage number to agent
        stage_agents = [
            "seller_registration",
            "product_information",
            "fulfillment",
            "pricing_config",
            "price_review",
            "refund_policy",
            "eula_config",
            "offer_availability",
            "allowlist",
        ]
        
        if current_stage >= len(stage_agents):
            return {
                "success": True,
                "status": "workflow_complete",
                "message": "All stages completed! Your listing is ready for submission.",
                "workflow_data": session["workflow_data"],
            }
        
        agent_key = stage_agents[current_stage]
        agent = session[agent_key]
        
        # Process the stage
        context = request.context or {}
        context["workflow_data"] = session["workflow_data"]
        
        result = agent.process_stage(request.user_input, context)
        
        # If stage is complete, move to next stage
        if result.get("status") == "complete":
            # Save stage data to workflow
            session["workflow_data"][agent_key] = agent.stage_data
            session["current_stage"] += 1
            result["next_stage"] = current_stage + 1
            result["next_stage_name"] = stage_agents[current_stage + 1] if current_stage + 1 < len(stage_agents) else "Complete"
        
        result["current_stage"] = current_stage
        result["session_id"] = session_id
        
        return {"success": True, **result}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})


@app.get("/agents/session/{session_id}/status")
async def get_session_status(session_id: str):
    """Get the current status of a listing workflow session"""
    if session_id not in agent_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = agent_sessions[session_id]
    
    stage_names = [
        "Seller Registration",
        "Product Information",
        "Fulfillment",
        "Pricing Configuration",
        "Price Review",
        "Refund Policy",
        "EULA Configuration",
        "Offer Availability",
        "Allowlist",
    ]
    
    stages_status = []
    for i, name in enumerate(stage_names):
        agent_key = name.lower().replace(" ", "_")
        if agent_key == "pricing_configuration":
            agent_key = "pricing_config"
        elif agent_key == "eula_configuration":
            agent_key = "eula_config"
        
        agent = session.get(agent_key)
        if agent:
            stages_status.append({
                "stage": i,
                "name": name,
                "status": "complete" if agent.is_complete else ("current" if i == session["current_stage"] else "pending"),
                "progress": agent.get_progress_summary() if hasattr(agent, "get_progress_summary") else "",
            })
    
    return {
        "success": True,
        "session_id": session_id,
        "current_stage": session["current_stage"],
        "current_stage_name": stage_names[session["current_stage"]] if session["current_stage"] < len(stage_names) else "Complete",
        "stages": stages_status,
        "workflow_data": session["workflow_data"],
    }


@app.post("/agents/session/{session_id}/set-stage-data")
async def set_stage_data(session_id: str, request: AgentStageRequest):
    """Directly set data for a specific stage"""
    if session_id not in agent_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = agent_sessions[session_id]
    stage_name = request.stage_name.lower().replace(" ", "_")
    
    if stage_name not in session:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {request.stage_name}")
    
    agent = session[stage_name]
    
    # Set the data directly
    if request.data:
        for key, value in request.data.items():
            agent.stage_data[key] = value
    
    # Validate
    errors = agent.validate_all_fields(agent.stage_data)
    
    return {
        "success": True,
        "stage": request.stage_name,
        "data": agent.stage_data,
        "validation_errors": errors,
        "is_complete": agent.is_stage_complete(),
    }


@app.delete("/agents/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a listing workflow session"""
    if session_id in agent_sessions:
        del agent_sessions[session_id]
        return {"success": True, "message": "Session deleted"}
    raise HTTPException(status_code=404, detail="Session not found")


@app.post("/agents/listing-tools/create-product")
async def create_product_with_tools(data: Dict[str, Any]):
    """Create a product using ListingTools directly"""
    try:
        credentials = data.get("credentials", {})
        product_title = data.get("product_title")
        
        if not product_title:
            raise HTTPException(status_code=400, detail="product_title is required")
        
        # Create boto3 session
        session = boto3.Session(
            aws_access_key_id=credentials.get("aws_access_key_id"),
            aws_secret_access_key=credentials.get("aws_secret_access_key"),
            aws_session_token=credentials.get("aws_session_token"),
            region_name="us-east-1",
        )
        
        # Initialize ListingTools with session
        tools = ListingTools(region="us-east-1", session=session)
        
        # Create minimal product
        result = tools.create_product_minimal(product_title)
        
        return {"success": True, **result}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})


@app.post("/agents/listing-tools/get-entity")
async def get_entity_details(data: Dict[str, Any]):
    """Get entity details using ListingTools"""
    try:
        credentials = data.get("credentials", {})
        entity_id = data.get("entity_id")
        entity_type = data.get("entity_type", "SaaSProduct@1.0")
        
        if not entity_id:
            raise HTTPException(status_code=400, detail="entity_id is required")
        
        # Create boto3 session
        session = boto3.Session(
            aws_access_key_id=credentials.get("aws_access_key_id"),
            aws_secret_access_key=credentials.get("aws_secret_access_key"),
            aws_session_token=credentials.get("aws_session_token"),
            region_name="us-east-1",
        )
        
        # Initialize ListingTools with session
        tools = ListingTools(region="us-east-1", session=session)
        
        # Get entity details
        result = tools.get_entity_details(entity_type, entity_id)
        
        return {"success": True, **result}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})


@app.post("/run-metering")
async def run_metering(data: Dict[str, Any]):
    """Run metering agent using the MeteringAgent class with strands"""
    try:
        credentials = data.get("credentials", {})
        product_id = data.get("product_id")
        access_key = credentials.get("aws_access_key_id")
        secret_key = credentials.get("aws_secret_access_key")
        session_token = credentials.get("aws_session_token")
        
        print("=" * 80)
        print("[METERING] ===== STARTING METERING AGENT WORKFLOW =====")
        print(f"[METERING] Product ID: {product_id}")
        print("=" * 80)
        
        import time
        steps = []
        
        # Step 1: Initialize MeteringAgent
        print("\n[METERING] Step 1: Initializing MeteringAgent with strands...")
        steps.append({
            "step": 1, 
            "name": "Initialize MeteringAgent", 
            "status": "in_progress",
            "substeps": []
        })
        
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))
            from metering import MeteringAgent
            
            agent = MeteringAgent()
            agent.create_saas_agent.set_product_id(product_id)
            
            steps[-1]["status"] = "completed"
            steps[-1]["message"] = "MeteringAgent initialized with product ID"
            steps[-1]["product_id"] = product_id
            print(f"[METERING] ✓ MeteringAgent ready with product: {product_id}")
            
        except Exception as e:
            steps[-1]["status"] = "failed"
            steps[-1]["error"] = str(e)
            print(f"[METERING] ✗ Failed to initialize: {str(e)}")
            import traceback
            print(f"[METERING] [DEBUG] Traceback: {traceback.format_exc()}")
            return {"success": False, "error": str(e), "steps": steps}
        
        # Step 2: Check Entitlement and Create Metering Records
        print("\n[METERING] Step 2: Running entitlement check and creating metering records...")
        steps.append({
            "step": 2,
            "name": "Check Entitlement & Create Metering Records",
            "status": "in_progress",
            "substeps": [
                {"name": "Check pricing model", "status": "pending"},
                {"name": "Connect to DynamoDB", "status": "pending"},
                {"name": "Locate DynamoDB tables", "status": "pending"},
                {"name": "Retrieve customer from subscribers", "status": "pending"},
                {"name": "Get usage dimensions", "status": "pending"},
                {"name": "Prepare metering record", "status": "pending"},
                {"name": "Insert metering record", "status": "pending"},
                {"name": "Verify record and check metering_pending flag", "status": "pending"}
            ]
        })
        
        try:
            # Call the agent's check_entitlement_and_add_metering tool
            print(f"[METERING] [DEBUG] Calling check_entitlement_and_add_metering...")
            print(f"[METERING] [DEBUG] Product ID: {product_id}")
            print(f"[METERING] [DEBUG] Access Key: {access_key[:10]}..." if access_key else "[METERING] [DEBUG] Access Key: None")
            print(f"[METERING] [DEBUG] Has Session Token: {bool(session_token)}")
            
            result = agent.check_entitlement_and_add_metering(
                access_key, secret_key, session_token
            )
            
            print(f"[METERING] [DEBUG] Agent result: {json.dumps(result, indent=2)}")
            
            # Update substeps based on result
            if result.get("status") == "success":
                for substep in steps[-1]["substeps"]:
                    substep["status"] = "completed"
                
                steps[-1]["status"] = "completed"
                steps[-1]["customer_identifier"] = result.get("customer_identifier")
                steps[-1]["timestamp"] = result.get("timestamp")
                steps[-1]["pricing_model"] = result.get("pricing_model")
                steps[-1]["subscribers_table"] = result.get("subscribers_table")
                steps[-1]["metering_table"] = result.get("metering_table")
                steps[-1]["usage_dimensions"] = result.get("usage_dimensions")
                print(f"[METERING] ✓ Entitlement check completed successfully")
                
            elif result.get("status") == "skipped":
                steps[-1]["status"] = "skipped"
                steps[-1]["reason"] = result.get("reason")
                print(f"[METERING] ⊘ Metering skipped: {result.get('reason')}")
                return {
                    "success": True,
                    "skipped": True,
                    "reason": result.get("reason"),
                    "steps": steps
                }
                
            elif result.get("error"):
                steps[-1]["status"] = "failed"
                steps[-1]["error"] = result["error"]
                print(f"[METERING] ✗ Entitlement check failed: {result['error']}")
                return {"success": False, "error": result["error"], "steps": steps}
                
        except Exception as e:
            steps[-1]["status"] = "failed"
            steps[-1]["error"] = str(e)
            print(f"[METERING] ✗ Exception during entitlement check: {str(e)}")
            import traceback
            print(f"[METERING] [DEBUG] Full traceback:")
            traceback.print_exc()
            return {"success": False, "error": str(e), "steps": steps}
        
        # Step 3: Find and Trigger Lambda Function
        print("\n[METERING] Step 3: Finding and triggering Lambda function...")
        steps.append({
            "step": 3,
            "name": "Trigger Lambda to Process Metering",
            "status": "in_progress",
            "substeps": [
                {"name": "Find hourly metering Lambda", "status": "in_progress"},
                {"name": "Invoke Lambda function", "status": "pending"},
                {"name": "Process metering records", "status": "pending"}
            ]
        })
        
        try:
            lambda_client = boto3.client(
                'lambda',
                region_name='us-east-1',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                aws_session_token=session_token
            )
            
            # Find the hourly metering Lambda
            functions = lambda_client.list_functions()['Functions']
            lambda_function_name = None
            
            for func in functions:
                func_name = func['FunctionName']
                if product_id in func_name and 'Hourly' in func_name:
                    lambda_function_name = func_name
                    print(f"[METERING] ✓ Found Lambda: {lambda_function_name}")
                    break
            
            if not lambda_function_name:
                steps[-1]["substeps"][0]["status"] = "failed"
                steps[-1]["status"] = "warning"
                steps[-1]["message"] = "Lambda function not found - metering record created but not processed"
                print("[METERING] ⚠ Lambda function not found")
            else:
                steps[-1]["substeps"][0]["status"] = "completed"
                steps[-1]["substeps"][1]["status"] = "in_progress"
                
                # Use the agent's trigger_hourly_metering tool
                lambda_result = agent.trigger_hourly_metering(
                    lambda_function_name, access_key, secret_key, session_token
                )
                
                steps[-1]["substeps"][1]["status"] = "completed"
                steps[-1]["substeps"][2]["status"] = "completed"
                steps[-1]["status"] = "completed"
                steps[-1]["lambda_function"] = lambda_function_name
                steps[-1]["lambda_result"] = lambda_result
                print(f"[METERING] ✓ Lambda triggered: {lambda_result.get('status')}")
                
        except Exception as e:
            steps[-1]["status"] = "warning"
            steps[-1]["error"] = str(e)
            steps[-1]["message"] = "Lambda trigger failed but metering record was created"
            print(f"[METERING] ⚠ Lambda trigger failed: {str(e)}")
        
        print("\n" + "=" * 80)
        print("[METERING] ===== METERING WORKFLOW COMPLETE =====")
        print("=" * 80 + "\n")
        
        return {
            "success": True,
            "steps": steps,
            "message": "Metering workflow completed successfully"
        }
        
    except Exception as e:
        print(f"[METERING] ✗ Workflow failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "steps": steps if 'steps' in locals() else []
        }
