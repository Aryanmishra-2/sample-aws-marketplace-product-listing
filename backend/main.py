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

# Validate credentials
@app.post("/validate-credentials")
async def validate_credentials(credentials: Credentials):
    """Validate AWS credentials using STS"""
    try:
        # Create session with provided credentials
        session = boto3.Session(
            aws_access_key_id=credentials.aws_access_key_id,
            aws_secret_access_key=credentials.aws_secret_access_key,
            aws_session_token=credentials.aws_session_token,
            region_name='us-east-1'
        )
        
        # Get caller identity
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        account_id = identity.get('Account')
        user_arn = identity.get('Arn')
        
        # Determine region type based on partition and account patterns
        region_type = 'UNKNOWN'
        organization = 'Unknown'
        
        # Check ARN partition
        if user_arn.startswith('arn:aws:'):
            # Standard AWS partition (US commercial)
            region_type = 'AWS_COMMERCIAL'
            organization = 'Amazon Web Services (Commercial)'
        elif user_arn.startswith('arn:aws-cn:'):
            # China partition
            region_type = 'AWS_CHINA'
            organization = 'Amazon Web Services China'
        elif user_arn.startswith('arn:aws-us-gov:'):
            # GovCloud partition
            region_type = 'AWS_GOVCLOUD'
            organization = 'Amazon Web Services GovCloud'
        
        # Additional check for internal AWS accounts (if email domain is available)
        # This is a best-effort detection
        if 'amazon.com' in user_arn.lower():
            organization += ' (Internal)'
        elif 'amazon.in' in user_arn.lower():
            organization = 'Amazon Web Services India Pvt Ltd'
            region_type = 'AWS_INDIA'
        
        return {
            "success": True,
            "account_id": account_id,
            "region_type": region_type,
            "user_arn": user_arn,
            "organization": organization,
            "session_id": f"session-{account_id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail={"success": False, "error": str(e)})

# Check seller status
@app.post("/check-seller-status")
async def check_seller_status(credentials: Credentials):
    """Check seller registration status"""
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
            if account_details.get('success') and account_details.get('owned_products'):
                for prod in account_details.get('owned_products', []):
                    if isinstance(prod, dict):
                        products.append({
                            'product_id': prod.get('Id', prod.get('product_id', '')),
                            'product_name': prod.get('Name', prod.get('product_name', 'Unnamed Product')),
                            'product_type': prod.get('ProductType', prod.get('product_type', 'SaaS')),
                            'status': prod.get('Status', prod.get('status', 'UNKNOWN')),
                        })
                    else:
                        # If it's just a string ID
                        products.append({
                            'product_id': str(prod),
                            'product_name': 'Product ' + str(prod)[:8],
                            'product_type': 'SaaS',
                            'status': 'UNKNOWN',
                        })
            
            return {
                "success": True,
                "seller_status": status_result.get('seller_status', 'UNKNOWN'),
                "account_id": status_result.get('account_id'),
                "owned_products": products,
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
        
        return {
            "success": True,
            "product_id": product_id,
            "offer_id": offer_id,
            "published_to_limited": published_to_limited,
            "message": "Listing created successfully"
        }
        
    except Exception as e:
        print(f"[ERROR] create_listing failed: {str(e)}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})

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
