"""
FastAPI Backend for AWS Marketplace Seller Portal
Integrates with existing agent system for complete functionality
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import boto3
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Add reference folder to path for legacy agents
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'reference', 'streamlit-app'))

# Import existing agents and tools
from agent.strands_marketplace_agent import StrandsMarketplaceAgent
from agent.tools.seller_registration_tools import SellerRegistrationTools
from agents.serverless_saas_integration import ServerlessSaasIntegrationAgent
from agents.workflow_orchestrator import WorkflowOrchestrator

app = FastAPI(title="AWS Marketplace Seller Portal API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
            'has_admin_access': user_type == 'Root User',
            'has_iam_read_access': False,
            'missing_permissions': [],
            'warnings': [],
            'recommendations': []
        }
        
        print("[DEBUG] Checking marketplace permissions...")
        
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
        # Initialize seller registration tools
        seller_tools = SellerRegistrationTools(
            region='us-east-1',
            aws_access_key_id=credentials.aws_access_key_id,
            aws_secret_access_key=credentials.aws_secret_access_key,
            aws_session_token=credentials.aws_session_token
        )
        
        # Check seller status
        status_result = seller_tools.check_seller_status()
        
        if status_result.get('success'):
            # Get account details
            account_details = seller_tools.get_seller_account_details()
            
            # Format products with more details
            products = []
            if status_result.get('owned_products'):
                for prod_id in status_result.get('owned_products', []):
                    products.append({
                        'product_id': prod_id,
                        'product_name': f'Product {prod_id[:8]}...',
                        'product_type': 'SaaS',
                        'status': 'ACTIVE',
                    })
            
            return {
                "success": True,
                "seller_status": status_result.get('seller_status', 'UNKNOWN'),
                "account_id": status_result.get('account_id'),
                "owned_products": products,
                "owned_products_count": status_result.get('owned_products_count', 0),
                "verification_status": status_result.get('verification_status', {}),
                "required_steps": status_result.get('required_steps', []),
                "marketplace_accessible": status_result.get('marketplace_accessible', False),
                "portal_url": status_result.get('portal_url'),
                "message": status_result.get('message', '')
            }
        else:
            return {
                "success": False,
                "seller_status": "UNKNOWN",
                "error": status_result.get('error', 'Failed to check seller status')
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})

# Get registration requirements
@app.post("/get-registration-requirements")
async def get_registration_requirements(data: Dict[str, Any]):
    """Get seller registration requirements based on country/region"""
    try:
        credentials = data.get("credentials", {})
        country = data.get("country", "US")
        
        seller_tools = SellerRegistrationTools(
            region='us-east-1',
            aws_access_key_id=credentials.get("aws_access_key_id"),
            aws_secret_access_key=credentials.get("aws_secret_access_key"),
            aws_session_token=credentials.get("aws_session_token")
        )
        
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
                    
                    # Determine allowed actions based on status
                    allowed_actions = []
                    recommendations = []
                    
                    if visibility == 'DRAFT':
                        allowed_actions = ['edit', 'continue_listing', 'delete']
                        recommendations.append('Continue with listing creation to publish')
                    elif visibility == 'LIMITED' or visibility == 'Restricted':
                        allowed_actions = ['view', 'manage_saas']
                        if needs_saas_integration:
                            recommendations.append('Complete SaaS integration before going public')
                            allowed_actions.append('deploy_saas')
                            saas_integration_status = 'REQUIRED'
                    elif visibility == 'PUBLIC' or visibility == 'Public':
                        allowed_actions = ['view', 'manage']
                        recommendations.append('Product is live on AWS Marketplace')
                        saas_integration_status = 'COMPLETED'
                    else:
                        # Unknown visibility
                        allowed_actions = ['view']
                        recommendations.append('Check product status in AWS Console')
                    
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
        
        # Build analysis prompt
        urls = product_context.get("product_urls", [])
        docs_url = product_context.get("documentation_url", "")
        description = product_context.get("product_description", "")
        
        prompt = f"""
        Analyze this product information and provide a structured analysis:
        
        Website: {urls[0] if urls else 'Not provided'}
        Documentation: {docs_url or 'Not provided'}
        Description: {description or 'Not provided'}
        
        Provide:
        1. Product Type (SaaS, API, Platform, etc.)
        2. Target Audience
        3. Key Features (list 5-10)
        4. Value Proposition
        5. Use Cases
        6. Competitive Advantages
        
        Format as JSON.
        """
        
        # Call Bedrock
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
        
        prompt = f"""
        Based on this product analysis:
        {json.dumps(analysis, indent=2)}
        
        Generate AWS Marketplace listing content:
        
        1. Product Title (5-72 chars, compelling and clear - MUST be under 72 characters)
        2. Short Description (10-500 chars, for search results)
        3. Long Description (50-5000 chars, detailed with benefits)
        4. Highlights (3-5 bullet points, 5-250 chars each)
        5. Search Keywords (5-10 keywords, max 50 chars each)
        6. Suggested Categories (from AWS Marketplace categories)
        
        IMPORTANT: Use only basic ASCII characters. Do NOT use:
        - Bullet points (•) - use hyphens (-) instead
        - Smart quotes (" ") - use straight quotes (")
        - Em/en dashes (— –) - use hyphens (-)
        
        Format as JSON with these exact keys: product_title, short_description, long_description, highlights (array), search_keywords (array), categories (array)
        """
        
        # Call Bedrock
        bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
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
        
        # Call Bedrock
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
        
        strands_agent = StrandsMarketplaceAgent()
        strands_agent.orchestrator.listing_tools.update_credentials(session)
        
        orchestrator = strands_agent.orchestrator
        
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

# Deploy SaaS
@app.post("/deploy-saas")
async def deploy_saas(data: Dict[str, Any]):
    """Deploy SaaS integration using existing agent system"""
    import traceback
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
        
        print("[DEBUG] Session created, initializing agents...")
        
        # Initialize SaaS integration agent
        strands_agent = StrandsMarketplaceAgent()
        saas_agent = ServerlessSaasIntegrationAgent(strands_agent=strands_agent)
        
        print("[DEBUG] Agents initialized, starting deployment...")
        
        # Deploy integration
        result = saas_agent.deploy_integration_with_session(
            session=session,
            product_id=product_id,
            email=email,
            pricing_dimensions=[]
        )
        
        print(f"[DEBUG] Deployment result: {result}")
        
        if result.get('stack_id') or result.get('success'):
            return {
                "success": True,
                "stack_id": result.get('stack_id'),
                "stack_name": result.get('stack_name', stack_name),
                "message": "SaaS integration deployed successfully"
            }
        else:
            error_msg = result.get('error', 'Deployment failed')
            print(f"[ERROR] Deployment failed: {error_msg}")
            raise Exception(error_msg)
            
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
