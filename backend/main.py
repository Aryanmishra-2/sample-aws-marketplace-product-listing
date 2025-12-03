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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Note: Legacy agent imports removed - agent logic is now integrated directly in endpoints
# Tools are available in the tools/ directory
# from agent.strands_marketplace_agent import StrandsMarketplaceAgent
# from agent.marketplace_help_agent import MarketplaceHelpAgent
# from agent.tools.seller_registration_tools import SellerRegistrationTools
# from agents.serverless_saas_integration import ServerlessSaasIntegrationAgent
# from agents.workflow_orchestrator import WorkflowOrchestrator

# Temporary mock class to replace removed SellerRegistrationTools
class SellerRegistrationTools:
    def __init__(self, region='us-east-1', **kwargs):
        self.region = region
        
    def get_registration_requirements(self):
        return {"requirements": ["Business information", "Tax information", "Bank account"]}
    
    def get_help_resources(self):
        return {"resources": ["AWS Marketplace Seller Guide", "Registration FAQ"]}
    
    def validate_business_info(self, business_info):
        return {"valid": True, "message": "Business information validated"}
    
    def check_registration_progress(self, registration_data):
        return {"progress": 50, "status": "in_progress"}
    
    def generate_registration_preview(self, registration_data):
        return {"preview": "Registration preview data"}

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
                            stack_response = cf_client.describe_stacks(StackName=stack_name)
                            if stack_response['Stacks']:
                                stack_status = stack_response['Stacks'][0]['StackStatus']
                                if stack_status == 'CREATE_COMPLETE':
                                    stack_exists = True
                                    saas_integration_status = 'COMPLETED'
                                elif stack_status in ['CREATE_IN_PROGRESS', 'UPDATE_IN_PROGRESS']:
                                    saas_integration_status = 'IN_PROGRESS'
                                elif stack_status in ['CREATE_FAILED', 'ROLLBACK_COMPLETE']:
                                    saas_integration_status = 'FAILED'
                        except:
                            # Stack doesn't exist or error checking
                            pass
                    
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
        
        prompt = f"""
        Analyze this product information and provide a structured analysis:
        
        Product Name: {product_name or 'Not provided - extract from website/description'}
        Website: {urls[0] if urls else 'Not provided'}
        Documentation: {docs_url or 'Not provided'}
        Description: {description or 'Not provided'}
        
        IMPORTANT: If a product name is provided, use it exactly. Do NOT invent or change the product name.
        If no product name is provided, try to extract it from the website URL or description.
        
        Provide:
        1. Product Type (SaaS, API, Platform, etc.)
        2. Target Audience
        3. Key Features (list 5-10)
        4. Value Proposition
        5. Use Cases
        6. Competitive Advantages
        7. Product Name (use the exact name provided, or extract from URL/description)
        
        Format as JSON.
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
            "temperature": 0.7
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
            analysis = json.loads(response_text)
        except:
            # If not valid JSON, create structured response
            analysis = {
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
@app.post("/create-listing")
async def create_listing(data: Dict[str, Any]):
    """Create marketplace listing using existing agent system"""
    import traceback
    try:
        print("[DEBUG] create_listing called")
        listing_data = data.get("listing_data", {})
        credentials = data.get("credentials", {})
        print(f"[DEBUG] listing_data keys: {list(listing_data.keys())}")
        print(f"[DEBUG] credentials keys: {list(credentials.keys())}")
        
        # Initialize Strands agent with credentials
        # Create boto3 session
        session = boto3.Session(
            aws_access_key_id=credentials.get("aws_access_key_id"),
            aws_secret_access_key=credentials.get("aws_secret_access_key"),
            aws_session_token=credentials.get("aws_session_token"),
            region_name='us-east-1'
        )
        
        # Note: Direct Marketplace API integration (agent removed)
        # strands_agent = StrandsMarketplaceAgent()
        # strands_agent.orchestrator.listing_tools.update_credentials(session)
        # orchestrator = strands_agent.orchestrator
        
        # Use direct AWS SDK calls instead
        marketplace_client = session.client('marketplace-catalog')
        
        # Stage 1: Product Information
        product_title = listing_data.get("title")
        logo_s3_url = listing_data.get("logo_s3_url")
        short_description = listing_data.get("short_description")
        long_description = listing_data.get("long_description")
        
        print(f"[DEBUG] Product title: {product_title}")
        print(f"[DEBUG] Short description: {short_description[:50] if short_description else 'MISSING'}")
        print(f"[DEBUG] Long description: {long_description[:50] if long_description else 'MISSING'}")
        
        # Validate required fields
        if not long_description or len(long_description.strip()) == 0:
            raise Exception("Long description is required but missing or empty")
        
        orchestrator.set_stage_data("product_title", product_title)
        orchestrator.set_stage_data("logo_s3_url", logo_s3_url)
        orchestrator.set_stage_data("short_description", short_description)
        orchestrator.set_stage_data("long_description", long_description)
        orchestrator.set_stage_data("highlights", listing_data.get("highlights"))
        orchestrator.set_stage_data("support_email", listing_data.get("support_email"))
        orchestrator.set_stage_data("support_description", listing_data.get("support_description"))
        orchestrator.set_stage_data("categories", listing_data.get("categories"))
        orchestrator.set_stage_data("search_keywords", listing_data.get("search_keywords"))
        
        result1 = orchestrator.complete_current_stage()
        
        if result1.get("status") != "complete":
            raise Exception(f"Stage 1 failed: {result1.get('message')}")
        
        # Stage 2: Fulfillment
        orchestrator.set_stage_data("fulfillment_url", listing_data.get("fulfillment_url"))
        orchestrator.set_stage_data("quick_launch_enabled", False)
        result2 = orchestrator.complete_current_stage()
        
        # Stage 3: Pricing Dimensions
        dimensions = listing_data.get("pricing_dimensions", [])
        api_dimensions = []
        for dim in dimensions:
            types = ["Metered", "ExternallyMetered"] if dim.get("type") == "Metered" else [dim.get("type")]
            api_dimensions.append({
                "Key": dim.get("key"),
                "Name": dim.get("name"),
                "Description": dim.get("description"),
                "Types": types,
                "Unit": "Units"
            })
        
        orchestrator.set_stage_data("pricing_model", listing_data.get("pricing_model"))
        orchestrator.set_stage_data("dimensions", api_dimensions)
        result3 = orchestrator.complete_current_stage()
        
        # Stage 4: Price Review
        if listing_data.get("pricing_model") == "Usage":
            orchestrator.set_stage_data("contract_durations", ["12 Months"])
            orchestrator.set_stage_data("multiple_dimension_selection", "Allowed")
            orchestrator.set_stage_data("quantity_configuration", "Allowed")
        else:
            orchestrator.set_stage_data("contract_durations", listing_data.get("contract_durations", ["12 Months"]))
            if listing_data.get("purchasing_option") == "multiple":
                orchestrator.set_stage_data("multiple_dimension_selection", "Allowed")
                orchestrator.set_stage_data("quantity_configuration", "Allowed")
            else:
                orchestrator.set_stage_data("multiple_dimension_selection", "Disallowed")
                orchestrator.set_stage_data("quantity_configuration", "Disallowed")
        
        result4 = orchestrator.complete_current_stage()
        
        # Stage 5: Refund Policy
        orchestrator.set_stage_data("refund_policy", listing_data.get("refund_policy"))
        result5 = orchestrator.complete_current_stage()
        
        # Stage 6: EULA
        orchestrator.set_stage_data("eula_type", listing_data.get("eula_type"))
        if listing_data.get("custom_eula_url"):
            orchestrator.set_stage_data("custom_eula_s3_url", listing_data.get("custom_eula_url"))
        result6 = orchestrator.complete_current_stage()
        
        # Stage 7: Availability
        if listing_data.get("availability_type") == "all":
            orchestrator.set_stage_data("availability_type", "all_countries")
        elif listing_data.get("availability_type") == "exclude":
            orchestrator.set_stage_data("availability_type", "all_with_exclusions")
            orchestrator.set_stage_data("excluded_countries", listing_data.get("excluded_countries", []))
        else:
            orchestrator.set_stage_data("availability_type", "allowlist_only")
            orchestrator.set_stage_data("allowed_countries", listing_data.get("allowed_countries", []))
        
        result7 = orchestrator.complete_current_stage()
        
        # Stage 8: Allowlist
        buyer_accounts = listing_data.get("buyer_accounts", [])
        if buyer_accounts:
            orchestrator.set_stage_data("allowlist_account_ids", buyer_accounts)
        result8 = orchestrator.complete_current_stage()
        
        # Get product and offer IDs
        api_result = result1.get("api_result", {})
        product_id = api_result.get("product_id")
        offer_id = api_result.get("offer_id")
        
        # Auto-publish to Limited if requested
        published_to_limited = False
        if listing_data.get("auto_publish_to_limited") and product_id and offer_id:
            tools = orchestrator.listing_tools
            release_result = tools.release_product_and_offer_to_limited(
                product_id=product_id,
                offer_id=offer_id,
                offer_name=listing_data.get("offer_name", listing_data.get("title")),
                offer_description=listing_data.get("offer_description", listing_data.get("short_description")),
                pricing_model=listing_data.get("pricing_model"),
                buyer_accounts=listing_data.get("buyer_accounts_for_limited") or None
            )
            published_to_limited = release_result.get("success", False)
        
        # Collect all stage results
        stage_results = [
            {"stage": "Product Information", "status": result1.get("status"), "message": result1.get("message", "")},
            {"stage": "Fulfillment", "status": result2.get("status"), "message": result2.get("message", "")},
            {"stage": "Pricing Dimensions", "status": result3.get("status"), "message": result3.get("message", "")},
            {"stage": "Price Review", "status": result4.get("status"), "message": result4.get("message", "")},
            {"stage": "Refund Policy", "status": result5.get("status"), "message": result5.get("message", "")},
            {"stage": "EULA", "status": result6.get("status"), "message": result6.get("message", "")},
            {"stage": "Availability", "status": result7.get("status"), "message": result7.get("message", "")},
            {"stage": "Allowlist", "status": result8.get("status"), "message": result8.get("message", "")},
        ]
        
        return {
            "success": True,
            "product_id": product_id,
            "offer_id": offer_id,
            "published_to_limited": published_to_limited,
            "message": "Listing created successfully",
            "stages": stage_results
        }
        
    except Exception as e:
        error_message = str(e)
        print(f"[ERROR] create_listing failed: {error_message}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        
        # Return detailed error
        return {
            "success": False,
            "error": error_message,
            "message": f"Listing creation failed: {error_message}",
            "stages": []
        }

# Deploy SaaS - Non-blocking version that starts stack and returns immediately
@app.post("/deploy-saas")
async def deploy_saas(data: Dict[str, Any]):
    """Deploy SaaS integration - starts CloudFormation stack and returns immediately"""
    import traceback
    import os
    try:
        print("[DEBUG] deploy_saas called")
        product_id = data.get("product_id")
        email = data.get("email")
        stack_name = data.get("stack_name")
        region = data.get("region", "us-east-1")
        credentials = data.get("credentials", {})
        
        print(f"[DEBUG] Product ID: {product_id}, Email: {email}, Stack: {stack_name}, Region: {region}")
        
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
        
        print(f"[DEBUG] Creating CloudFormation stack: {actual_stack_name}")
        
        try:
            response = cf_client.create_stack(
                StackName=actual_stack_name,
                TemplateBody=template_body,
                Parameters=[
                    {'ParameterKey': 'ProductId', 'ParameterValue': product_id},
                    {'ParameterKey': 'PricingModel', 'ParameterValue': 'Usage-based-pricing'},
                    {'ParameterKey': 'MarketplaceTechAdminEmail', 'ParameterValue': email}
                ],
                Capabilities=['CAPABILITY_IAM', 'CAPABILITY_AUTO_EXPAND']
            )
            
            stack_id = response['StackId']
            print(f"[DEBUG] Stack creation initiated: {stack_id}")
            
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

# Helper function to emit events
def emit_event(session_id: str, event_type: str, data: Dict[str, Any]):
    """Emit an event to the SSE stream for a specific session"""
    if session_id in event_queues:
        event_queues[session_id].put({
            "type": event_type,
            "data": data
        })

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

# Modified create listing endpoint with SSE support
@app.post("/create-listing-with-stream")
async def create_listing_with_stream(data: Dict[str, Any]):
    """Create marketplace listing with SSE progress updates"""
    import traceback
    
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
                "message": "Setting up AWS Marketplace agent..."
            })
            
            # Create boto3 session
            session = boto3.Session(
                aws_access_key_id=credentials.get("aws_access_key_id"),
                aws_secret_access_key=credentials.get("aws_secret_access_key"),
                aws_session_token=credentials.get("aws_session_token"),
                region_name='us-east-1'
            )
            
            # Note: Direct Marketplace API integration (agent removed)
            # strands_agent = StrandsMarketplaceAgent()
            # strands_agent.orchestrator.listing_tools.update_credentials(session)
            # orchestrator = strands_agent.orchestrator
            
            # Use direct AWS SDK calls instead
            marketplace_client = session.client('marketplace-catalog')
            
            # Stage 1: Product Information
            emit_event(session_id, "stage", {
                "stage": "Product Information",
                "status": "in_progress",
                "message": "Creating product and updating details..."
            })
            
            orchestrator.set_stage_data("product_title", listing_data.get("title"))
            orchestrator.set_stage_data("logo_s3_url", listing_data.get("logo_s3_url"))
            orchestrator.set_stage_data("short_description", listing_data.get("short_description"))
            orchestrator.set_stage_data("long_description", listing_data.get("long_description"))
            orchestrator.set_stage_data("highlights", listing_data.get("highlights"))
            orchestrator.set_stage_data("support_email", listing_data.get("support_email"))
            orchestrator.set_stage_data("support_description", listing_data.get("support_description"))
            orchestrator.set_stage_data("categories", listing_data.get("categories"))
            orchestrator.set_stage_data("search_keywords", listing_data.get("search_keywords"))
            
            result1 = orchestrator.complete_current_stage()
            
            if result1.get("status") != "complete":
                emit_event(session_id, "error", {
                    "stage": "Product Information",
                    "message": result1.get("message", "Failed to create product")
                })
                return
            
            emit_event(session_id, "changeset", {
                "stage": "Product Information",
                "changeset_id": result1.get("api_result", {}).get("change_set_id"),
                "status": "SUCCEEDED",
                "message": "Product information updated successfully"
            })
            
            # Stage 2: Fulfillment
            emit_event(session_id, "stage", {
                "stage": "Fulfillment",
                "status": "in_progress",
                "message": "Configuring fulfillment options..."
            })
            
            orchestrator.set_stage_data("fulfillment_url", listing_data.get("fulfillment_url"))
            orchestrator.set_stage_data("quick_launch_enabled", False)
            result2 = orchestrator.complete_current_stage()
            
            emit_event(session_id, "changeset", {
                "stage": "Fulfillment",
                "changeset_id": result2.get("api_result", {}).get("change_set_id"),
                "status": "SUCCEEDED",
                "message": "Fulfillment options configured"
            })
            
            # Stage 3: Pricing Dimensions
            emit_event(session_id, "stage", {
                "stage": "Pricing Dimensions",
                "status": "in_progress",
                "message": "Setting up pricing dimensions..."
            })
            
            dimensions = listing_data.get("pricing_dimensions", [])
            api_dimensions = []
            for dim in dimensions:
                types = ["Metered", "ExternallyMetered"] if dim.get("type") == "Metered" else [dim.get("type")]
                api_dimensions.append({
                    "Key": dim.get("key"),
                    "Name": dim.get("name"),
                    "Description": dim.get("description"),
                    "Types": types,
                    "Unit": "Units"
                })
            
            orchestrator.set_stage_data("pricing_model", listing_data.get("pricing_model"))
            orchestrator.set_stage_data("dimensions", api_dimensions)
            result3 = orchestrator.complete_current_stage()
            
            emit_event(session_id, "changeset", {
                "stage": "Pricing Dimensions",
                "status": "SUCCEEDED",
                "message": result3.get("message", "Pricing dimensions configured")
            })
            
            # Stage 4: Price Review
            emit_event(session_id, "stage", {
                "stage": "Price Review",
                "status": "in_progress",
                "message": "Configuring pricing terms..."
            })
            
            if listing_data.get("pricing_model") == "Usage":
                orchestrator.set_stage_data("contract_durations", ["12 Months"])
                orchestrator.set_stage_data("multiple_dimension_selection", "Allowed")
                orchestrator.set_stage_data("quantity_configuration", "Allowed")
            else:
                orchestrator.set_stage_data("contract_durations", listing_data.get("contract_durations", ["12 Months"]))
                if listing_data.get("purchasing_option") == "multiple":
                    orchestrator.set_stage_data("multiple_dimension_selection", "Allowed")
                    orchestrator.set_stage_data("quantity_configuration", "Allowed")
                else:
                    orchestrator.set_stage_data("multiple_dimension_selection", "Disallowed")
                    orchestrator.set_stage_data("quantity_configuration", "Disallowed")
            
            result4 = orchestrator.complete_current_stage()
            
            emit_event(session_id, "changeset", {
                "stage": "Price Review",
                "changeset_id": result4.get("api_result", {}).get("change_set_id"),
                "status": "SUCCEEDED",
                "message": "Pricing terms configured"
            })
            
            # Stage 5: Refund Policy
            emit_event(session_id, "stage", {
                "stage": "Refund Policy",
                "status": "in_progress",
                "message": "Setting refund policy..."
            })
            
            orchestrator.set_stage_data("refund_policy", listing_data.get("refund_policy"))
            result5 = orchestrator.complete_current_stage()
            
            emit_event(session_id, "changeset", {
                "stage": "Refund Policy",
                "changeset_id": result5.get("api_result", {}).get("change_set_id"),
                "status": "SUCCEEDED",
                "message": "Refund policy set"
            })
            
            # Stage 6: EULA
            emit_event(session_id, "stage", {
                "stage": "EULA",
                "status": "in_progress",
                "message": "Configuring legal terms..."
            })
            
            orchestrator.set_stage_data("eula_type", listing_data.get("eula_type"))
            if listing_data.get("custom_eula_url"):
                orchestrator.set_stage_data("custom_eula_s3_url", listing_data.get("custom_eula_url"))
            result6 = orchestrator.complete_current_stage()
            
            emit_event(session_id, "changeset", {
                "stage": "EULA",
                "changeset_id": result6.get("api_result", {}).get("change_set_id"),
                "status": "SUCCEEDED",
                "message": "Legal terms configured"
            })
            
            # Stage 7: Availability
            emit_event(session_id, "stage", {
                "stage": "Availability",
                "status": "in_progress",
                "message": "Setting geographic availability..."
            })
            
            if listing_data.get("availability_type") == "all":
                orchestrator.set_stage_data("availability_type", "all_countries")
            elif listing_data.get("availability_type") == "exclude":
                orchestrator.set_stage_data("availability_type", "all_with_exclusions")
                orchestrator.set_stage_data("excluded_countries", listing_data.get("excluded_countries", []))
            else:
                orchestrator.set_stage_data("availability_type", "allowlist_only")
                orchestrator.set_stage_data("allowed_countries", listing_data.get("allowed_countries", []))
            
            result7 = orchestrator.complete_current_stage()
            
            emit_event(session_id, "changeset", {
                "stage": "Availability",
                "changeset_id": result7.get("api_result", {}).get("change_set_id"),
                "status": "SUCCEEDED",
                "message": "Geographic availability set"
            })
            
            # Stage 8: Allowlist
            emit_event(session_id, "stage", {
                "stage": "Allowlist",
                "status": "in_progress",
                "message": "Configuring buyer allowlist..."
            })
            
            buyer_accounts = listing_data.get("buyer_accounts", [])
            if buyer_accounts:
                orchestrator.set_stage_data("allowlist_account_ids", buyer_accounts)
            result8 = orchestrator.complete_current_stage()
            
            emit_event(session_id, "changeset", {
                "stage": "Allowlist",
                "status": "SUCCEEDED",
                "message": result8.get("message", "Allowlist configured")
            })
            
            # Get product and offer IDs
            api_result = result1.get("api_result", {})
            product_id = api_result.get("product_id")
            offer_id = api_result.get("offer_id")
            
            # Auto-publish to Limited if requested
            published_to_limited = False
            if listing_data.get("auto_publish_to_limited") and product_id and offer_id:
                emit_event(session_id, "stage", {
                    "stage": "Publishing",
                    "status": "in_progress",
                    "message": "Publishing to Limited audience..."
                })
                
                tools = orchestrator.listing_tools
                release_result = tools.release_product_and_offer_to_limited(
                    product_id=product_id,
                    offer_id=offer_id,
                    offer_name=listing_data.get("offer_name", listing_data.get("title")),
                    offer_description=listing_data.get("offer_description", listing_data.get("short_description")),
                    pricing_model=listing_data.get("pricing_model"),
                    buyer_accounts=listing_data.get("buyer_accounts_for_limited") or None
                )
                published_to_limited = release_result.get("success", False)
                
                emit_event(session_id, "changeset", {
                    "stage": "Publishing",
                    "status": "SUCCEEDED" if published_to_limited else "FAILED",
                    "message": "Published to Limited" if published_to_limited else "Publishing failed"
                })
            
            # Send completion event
            emit_event(session_id, "complete", {
                "product_id": product_id,
                "offer_id": offer_id,
                "published_to_limited": published_to_limited,
                "message": "Listing created successfully"
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

**Your question:** "{question}"

For detailed information, please visit the [AWS Marketplace Seller Guide](https://docs.aws.amazon.com/marketplace/latest/userguide/what-is-marketplace.html) or ask a more specific question.

**Example questions:**
• "How do I register as a seller?"
• "What is SaaS integration?"
• "How do I create a product listing?"
• "What pricing models are available?"
• "How does metering work?"
"""
