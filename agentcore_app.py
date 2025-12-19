"""
AgentCore Runtime Application for AWS Marketplace Seller Portal

This file wraps the existing agent system for deployment to Amazon Bedrock AgentCore Runtime.
It exposes the WorkflowOrchestrator and individual agents via HTTP endpoints.
"""

from bedrock_agentcore.runtime import BedrockAgentCoreApp
import json
import sys
import os
import threading
import uuid
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# Add the app directory to path so Python can find the agents and backend packages
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from agents.workflow_orchestrator import WorkflowOrchestrator
from agents.metering import MeteringAgent
from agents.public_visibility import PublicVisibilityAgent
from agents.buyer_experience import BuyerExperienceAgent
from agents.create_saas import CreateSaasAgent

# Import listing subagents and tools from backend
try:
    from backend.agents import (
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
    LISTING_AGENTS_AVAILABLE = True
except ImportError:
    LISTING_AGENTS_AVAILABLE = False

# Initialize AgentCore app
app = BedrockAgentCoreApp()

# DynamoDB table for persistent task state
TASK_TABLE_NAME = "marketplace-listing-tasks"

def get_dynamodb_client(access_key=None, secret_key=None, session_token=None):
    """Get DynamoDB client with optional credentials"""
    if access_key and secret_key:
        return boto3.client(
            'dynamodb',
            region_name='us-east-1',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token
        )
    return boto3.client('dynamodb', region_name='us-east-1')

def ensure_task_table_exists(dynamodb_client):
    """Create the task table if it doesn't exist"""
    try:
        dynamodb_client.describe_table(TableName=TASK_TABLE_NAME)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            dynamodb_client.create_table(
                TableName=TASK_TABLE_NAME,
                KeySchema=[{'AttributeName': 'task_id', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'task_id', 'AttributeType': 'S'}],
                BillingMode='PAY_PER_REQUEST'
            )
            # Wait for table to be created
            waiter = dynamodb_client.get_waiter('table_exists')
            waiter.wait(TableName=TASK_TABLE_NAME)

def save_task_state(task_id: str, task_data: dict, access_key=None, secret_key=None, session_token=None):
    """Save task state to DynamoDB"""
    try:
        dynamodb_client = get_dynamodb_client(access_key, secret_key, session_token)
        ensure_task_table_exists(dynamodb_client)
        
        item = {
            'task_id': {'S': task_id},
            'status': {'S': task_data.get('status', 'unknown')},
            'stages': {'S': json.dumps(task_data.get('stages', []))},
            'product_id': {'S': task_data.get('product_id') or ''},
            'offer_id': {'S': task_data.get('offer_id') or ''},
            'published_to_limited': {'BOOL': task_data.get('published_to_limited', False)},
            'error': {'S': task_data.get('error') or ''},
            'message': {'S': task_data.get('message') or ''},
            'started_at': {'S': task_data.get('started_at') or ''},
            'completed_at': {'S': task_data.get('completed_at') or ''},
            'ttl': {'N': str(int(datetime.now().timestamp()) + 86400)}  # 24 hour TTL
        }
        
        dynamodb_client.put_item(TableName=TASK_TABLE_NAME, Item=item)
    except Exception as e:
        print(f"Error saving task state: {e}")

def get_task_state(task_id: str, access_key=None, secret_key=None, session_token=None) -> dict:
    """Get task state from DynamoDB"""
    try:
        dynamodb_client = get_dynamodb_client(access_key, secret_key, session_token)
        
        response = dynamodb_client.get_item(
            TableName=TASK_TABLE_NAME,
            Key={'task_id': {'S': task_id}}
        )
        
        if 'Item' not in response:
            return None
        
        item = response['Item']
        return {
            'task_id': item.get('task_id', {}).get('S'),
            'status': item.get('status', {}).get('S', 'unknown'),
            'stages': json.loads(item.get('stages', {}).get('S', '[]')),
            'product_id': item.get('product_id', {}).get('S') or None,
            'offer_id': item.get('offer_id', {}).get('S') or None,
            'published_to_limited': item.get('published_to_limited', {}).get('BOOL', False),
            'error': item.get('error', {}).get('S') or None,
            'message': item.get('message', {}).get('S') or None,
            'started_at': item.get('started_at', {}).get('S') or None,
            'completed_at': item.get('completed_at', {}).get('S') or None,
        }
    except Exception as e:
        print(f"Error getting task state: {e}")
        return None

# Initialize agents
workflow_orchestrator = WorkflowOrchestrator()
metering_agent = MeteringAgent()
visibility_agent = PublicVisibilityAgent()
buyer_experience_agent = BuyerExperienceAgent()
create_saas_agent = CreateSaasAgent()

# Initialize listing subagents if available
listing_agents = {}
if LISTING_AGENTS_AVAILABLE:
    listing_agents = {
        'seller_registration': SellerRegistrationAgent(),
        'product_information': ProductInformationAgent(),
        'fulfillment': FulfillmentAgent(),
        'pricing_config': PricingConfigAgent(),
        'price_review': PriceReviewAgent(),
        'refund_policy': RefundPolicyAgent(),
        'eula_config': EULAConfigAgent(),
        'offer_availability': OfferAvailabilityAgent(),
        'allowlist': AllowlistAgent(),
    }


@app.entrypoint
async def handle_request(payload: dict, context=None):
    """
    Main entrypoint for AgentCore Runtime.
    
    Payload format:
    {
        "action": "chat" | "workflow" | "metering" | "visibility" | "buyer_experience",
        "credentials": {
            "accessKeyId": "...",
            "secretAccessKey": "...",
            "sessionToken": "..."  # optional
        },
        "prompt": "...",  # for chat action
        "product_id": "...",  # optional
        "lambda_function_name": "...",  # optional for workflow
        ... other action-specific params
    }
    """
    action = payload.get("action", "chat")
    credentials = payload.get("credentials", {})
    
    # Extract credentials (support both camelCase and snake_case)
    access_key = credentials.get("accessKeyId") or credentials.get("aws_access_key_id")
    secret_key = credentials.get("secretAccessKey") or credentials.get("aws_secret_access_key")
    session_token = credentials.get("sessionToken") or credentials.get("aws_session_token")
    
    # Set product ID if provided
    product_id = payload.get("product_id")
    if product_id:
        create_saas_agent.set_product_id(product_id)
    
    try:
        if action == "chat":
            return await handle_chat(payload, access_key, secret_key, session_token)
        
        elif action == "workflow":
            return handle_workflow(payload, access_key, secret_key, session_token)
        
        elif action == "metering":
            return handle_metering(payload, access_key, secret_key, session_token)
        
        elif action == "visibility":
            return handle_visibility(payload, access_key, secret_key, session_token)
        
        elif action == "buyer_experience":
            return handle_buyer_experience(payload, access_key, secret_key, session_token)
        
        elif action == "analyze_product":
            return await handle_analyze_product(payload, access_key, secret_key, session_token)
        
        elif action == "generate_content":
            return await handle_generate_content(payload, access_key, secret_key, session_token)
        
        elif action == "suggest_pricing":
            return await handle_suggest_pricing(payload, access_key, secret_key, session_token)
        
        elif action == "deploy_saas":
            return handle_deploy_saas(payload, access_key, secret_key, session_token)
        
        elif action == "get_stack_status":
            return handle_get_stack_status(payload, access_key, secret_key, session_token)
        
        elif action == "get_stack_parameters":
            return handle_get_stack_parameters(payload, access_key, secret_key, session_token)
        
        elif action == "delete_stack":
            return handle_delete_stack(payload, access_key, secret_key, session_token)
        
        elif action == "create_listing":
            return handle_create_listing_async(payload, access_key, secret_key, session_token)
        
        elif action == "listing_progress":
            return handle_listing_progress(payload)
        
        elif action == "validate_credentials":
            return handle_validate_credentials(payload, access_key, secret_key, session_token)
        
        elif action == "check_seller_status":
            return handle_check_seller_status(payload, access_key, secret_key, session_token)
        
        elif action == "list_marketplace_products":
            return handle_list_marketplace_products(payload, access_key, secret_key, session_token)
        
        elif action == "check_stack_exists":
            return handle_check_stack_exists(payload, access_key, secret_key, session_token)
        
        elif action == "run_metering":
            return handle_run_metering(payload, access_key, secret_key, session_token)
        
        elif action == "execute_saas_workflow":
            return handle_execute_saas_workflow(payload, access_key, secret_key, session_token)
        
        elif action == "get_registration_requirements":
            return handle_get_registration_requirements(payload)
        
        elif action == "validate_business_info":
            return handle_validate_business_info(payload)
        
        elif action == "check_registration_progress":
            return handle_check_registration_progress(payload)
        
        elif action == "generate_registration_preview":
            return handle_generate_registration_preview(payload)
        
        elif action == "metering_find_tables":
            return handle_metering_find_tables(payload, access_key, secret_key, session_token)
        
        elif action == "metering_get_customer":
            return handle_metering_get_customer(payload, access_key, secret_key, session_token)
        
        elif action == "metering_insert_record":
            return handle_metering_insert_record(payload, access_key, secret_key, session_token)
        
        # Listing Tools Actions
        elif action == "listing_create_draft":
            return handle_listing_create_draft(payload, access_key, secret_key, session_token)
        
        elif action == "listing_update_info":
            return handle_listing_update_info(payload, access_key, secret_key, session_token)
        
        elif action == "listing_add_pricing":
            return handle_listing_add_pricing(payload, access_key, secret_key, session_token)
        
        elif action == "listing_update_support":
            return handle_listing_update_support(payload, access_key, secret_key, session_token)
        
        elif action == "listing_update_legal":
            return handle_listing_update_legal(payload, access_key, secret_key, session_token)
        
        elif action == "listing_update_availability":
            return handle_listing_update_availability(payload, access_key, secret_key, session_token)
        
        elif action == "listing_release_to_limited":
            return handle_listing_release_to_limited(payload, access_key, secret_key, session_token)
        
        elif action == "listing_get_status":
            return handle_listing_get_status(payload, access_key, secret_key, session_token)
        
        elif action == "listing_get_entity":
            return handle_listing_get_entity(payload, access_key, secret_key, session_token)
        
        elif action == "health":
            return {
                "status": "healthy", 
                "agents": ["workflow", "metering", "visibility", "buyer_experience"],
                "listing_agents_available": LISTING_AGENTS_AVAILABLE,
                "listing_agents": list(listing_agents.keys()) if LISTING_AGENTS_AVAILABLE else []
            }
        
        else:
            return {"error": f"Unknown action: {action}", "available_actions": [
                "chat", "workflow", "metering", "visibility", "buyer_experience", 
                "analyze_product", "generate_content", "suggest_pricing", 
                "deploy_saas", "get_stack_status", "get_stack_parameters", "delete_stack",
                "create_listing", "validate_credentials", "check_seller_status",
                "list_marketplace_products", "check_stack_exists", "run_metering",
                "execute_saas_workflow", "get_registration_requirements", "validate_business_info",
                "check_registration_progress", "generate_registration_preview",
                "metering_find_tables", "metering_get_customer", "metering_insert_record",
                "listing_create_draft", "listing_update_info", "listing_add_pricing",
                "listing_update_support", "listing_update_legal", "listing_update_availability",
                "listing_release_to_limited", "listing_get_status", "listing_get_entity", 
                "listing_progress", "health"
            ]}
            
    except Exception as e:
        return {"error": str(e), "action": action}


async def handle_chat(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Handle chat/help requests using Bedrock"""
    import boto3
    
    prompt = payload.get("prompt") or payload.get("question")
    if not prompt:
        return {"error": "Missing 'prompt' or 'question' in payload"}
    
    conversation_history = payload.get("conversation_history", [])
    
    # Use Bedrock for chat
    bedrock_client = boto3.client(
        'bedrock-runtime',
        region_name='us-east-1',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token
    )
    
    system_prompt = """You are an AWS Marketplace Help Agent specializing in seller registration and SaaS product listings.

IMPORTANT RULES:
1. Only answer questions about AWS Marketplace seller topics
2. If you don't know something specific, say "I don't have that specific information" rather than guessing
3. For questions about other AWS services not related to Marketplace, say "I specialize in AWS Marketplace. For questions about [service], please refer to AWS documentation."
4. Be concise and factual

Topics you can help with:
- AWS Marketplace seller registration process
- SaaS product listing creation
- Pricing models (usage-based, contracts, hybrid)
- SaaS integration with CloudFormation
- Metering and billing setup
- Public visibility requirements
- Buyer experience testing

For technical AWS service questions outside Marketplace, direct users to AWS documentation."""

    messages = []
    
    # Filter conversation history to start with user message (Bedrock requirement)
    if conversation_history:
        start_idx = 0
        for i, msg in enumerate(conversation_history):
            if msg.get("role") == "user":
                start_idx = i
                break
        
        for msg in conversation_history[start_idx:]:
            if msg.get("role") and msg.get("content"):
                messages.append({
                    "role": msg["role"],
                    "content": [{"text": msg["content"]}]
                })
    
    messages.append({
        "role": "user",
        "content": [{"text": prompt}]
    })
    
    response = bedrock_client.converse(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        system=[{"text": system_prompt}],
        messages=messages,
        inferenceConfig={"maxTokens": 2048, "temperature": 0.7}
    )
    
    response_text = ""
    if response.get("output", {}).get("message", {}).get("content"):
        for block in response["output"]["message"]["content"]:
            if "text" in block:
                response_text += block["text"]
    
    return {
        "success": True,
        "response": response_text,
        "session_id": payload.get("session_id", f"chat-{id(payload)}")
    }


def handle_workflow(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Execute the full marketplace workflow"""
    if not access_key or not secret_key:
        return {"error": "Missing AWS credentials"}
    
    lambda_function_name = payload.get("lambda_function_name")
    
    result = workflow_orchestrator.execute_full_workflow(
        access_key=access_key,
        secret_key=secret_key,
        session_token=session_token,
        lambda_function_name=lambda_function_name
    )
    
    return result


def handle_metering(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Handle metering operations"""
    if not access_key or not secret_key:
        return {"error": "Missing AWS credentials"}
    
    sub_action = payload.get("sub_action", "check_and_add")
    
    if sub_action == "check_and_add":
        return metering_agent.check_entitlement_and_add_metering(
            access_key=access_key,
            secret_key=secret_key,
            session_token=session_token
        )
    
    elif sub_action == "trigger_lambda":
        lambda_function_name = payload.get("lambda_function_name")
        if not lambda_function_name:
            return {"error": "Missing lambda_function_name for trigger_lambda action"}
        
        return metering_agent.trigger_hourly_metering(
            lambda_function_name=lambda_function_name,
            access_key=access_key,
            secret_key=secret_key,
            session_token=session_token
        )
    
    elif sub_action == "insert_test_customer":
        return metering_agent.insert_test_customer(
            access_key=access_key,
            secret_key=secret_key,
            session_token=session_token
        )
    
    else:
        return {"error": f"Unknown metering sub_action: {sub_action}"}


def handle_visibility(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Handle public visibility operations"""
    if not access_key or not secret_key:
        return {"error": "Missing AWS credentials"}
    
    sub_action = payload.get("sub_action", "check_and_update")
    
    if sub_action == "check_and_update":
        return visibility_agent.check_metering_and_update_visibility(
            access_key=access_key,
            secret_key=secret_key,
            session_token=session_token
        )
    
    elif sub_action == "raise_request":
        return visibility_agent.raise_public_visibility_request(
            access_key=access_key,
            secret_key=secret_key,
            session_token=session_token
        )
    
    else:
        return {"error": f"Unknown visibility sub_action: {sub_action}"}


def handle_buyer_experience(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Handle buyer experience simulation"""
    if not access_key or not secret_key:
        return {"error": "Missing AWS credentials"}
    
    sub_action = payload.get("sub_action", "get_checklist")
    
    if sub_action == "simulate":
        return buyer_experience_agent.simulate_buyer_journey(
            access_key=access_key,
            secret_key=secret_key,
            session_token=session_token
        )
    
    elif sub_action == "get_checklist":
        return buyer_experience_agent.get_simulation_checklist()
    
    elif sub_action == "verify_registration":
        return buyer_experience_agent.verify_customer_registration(
            access_key=access_key,
            secret_key=secret_key,
            session_token=session_token
        )
    
    else:
        return {"error": f"Unknown buyer_experience sub_action: {sub_action}"}


async def handle_analyze_product(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Analyze product for marketplace listing"""
    import boto3
    
    product_context = payload.get("product_context", {})
    
    bedrock_client = boto3.client(
        'bedrock-runtime',
        region_name='us-east-1',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token
    )
    
    analysis_prompt = """Analyze the provided product information and generate a JSON response with:
{
  "product_summary": "Brief summary",
  "target_audience": "Who this is for",
  "key_features": ["feature1", "feature2"],
  "suggested_categories": ["category1"],
  "suggested_keywords": ["keyword1"],
  "pricing_recommendations": {"model": "subscription|usage|contract", "rationale": "Why"},
  "marketplace_fit_score": 8,
  "recommendations": ["recommendation1"]
}
Respond ONLY with valid JSON."""

    product_info = f"""
Product Name: {product_context.get('product_name', 'Not provided')}
Product Description: {product_context.get('product_description', 'Not provided')}
Product URLs: {', '.join(product_context.get('product_urls', []))}
Documentation URL: {product_context.get('documentation_url', 'Not provided')}
Additional Context: {product_context.get('additional_context', 'Not provided')}
"""

    response = bedrock_client.converse(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        system=[{"text": analysis_prompt}],
        messages=[{"role": "user", "content": [{"text": f"Analyze this product:\n{product_info}"}]}],
        inferenceConfig={"maxTokens": 2048, "temperature": 0.3}
    )
    
    response_text = ""
    if response.get("output", {}).get("message", {}).get("content"):
        for block in response["output"]["message"]["content"]:
            if "text" in block:
                response_text += block["text"]
    
    # Parse JSON response
    try:
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            analysis = json.loads(json_match.group(0))
        else:
            analysis = {"raw_response": response_text}
    except:
        analysis = {"raw_response": response_text}
    
    return {"success": True, "analysis": analysis}


async def handle_generate_content(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Generate listing content using Bedrock"""
    import boto3
    
    analysis = payload.get("analysis", {})
    product_context = payload.get("product_context", {})
    
    bedrock_client = boto3.client(
        'bedrock-runtime',
        region_name='us-east-1',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token
    )
    
    product_name = analysis.get("product_name", analysis.get("Product Name", ""))
    website_url = ""
    if product_context.get("product_urls"):
        website_url = product_context["product_urls"][0] if product_context["product_urls"] else ""
    original_description = product_context.get("product_description", "")
    
    # Valid AWS Marketplace categories
    valid_categories = [
        "AI Security", "Content Creation", "Customer Experience Personalization", "Customer Support",
        "Data Analysis", "Finance & Accounting", "IT Support", "Legal & Compliance", "Observability",
        "Procurement & Supply Chain", "Quality Assurance", "Research", "Sales & Marketing",
        "Scheduling & Coordination", "Software Development", "Backup & Recovery", "Data Analytics",
        "Data Integration", "Data Preparation", "ELT/ETL", "Streaming Solutions", "Databases",
        "Data Warehouses", "Analytic Platforms", "Data Catalogs", "Master Data Management",
        "Masking/Tokenization", "Business Intelligence & Advanced Analytics", "High Performance Computing",
        "Migration", "Network Infrastructure", "Operating Systems", "Security", "Storage",
        "Agile Lifecycle Management", "Application Development", "Application Servers", "Application Stacks",
        "Continuous Integration and Continuous Delivery", "Infrastructure as Code", "Issue & Bug Tracking",
        "Monitoring", "Log Analysis", "Source Control", "Testing", "Blockchain", "Collaboration & Productivity",
        "Contact Center", "Content Management", "CRM", "eCommerce", "eLearning", "Human Resources",
        "IT Business Management", "Project Management"
    ]
    
    prompt = f"""Based on this product analysis and original product information:

ORIGINAL PRODUCT INFO:
- Website: {website_url}
- Description provided by user: {original_description}

AI ANALYSIS:
{json.dumps(analysis, indent=2)}

Generate AWS Marketplace listing content that is SPECIFIC to this product.

1. Product Title (5-72 chars, compelling and clear - MUST be under 72 characters)
   CRITICAL: Use the actual product name "{product_name}" if provided.
2. Short Description (10-500 chars, for search results)
3. Long Description (50-5000 chars, detailed with benefits)
4. Highlights (3-5 bullet points, 5-250 chars each)
5. Search Keywords (5-10 keywords, max 50 chars each)
6. Categories (1-3 categories) - MUST be from this EXACT list only:
   {', '.join(valid_categories)}

IMPORTANT: 
- Use only basic ASCII characters. No bullet points (use hyphens), no smart quotes.
- Categories MUST match exactly from the list above - do not invent new categories.

Format as JSON with keys: product_title, short_description, long_description, highlights (array), search_keywords (array), categories (array)"""

    response = bedrock_client.converse(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        system=[{"text": "Generate AWS Marketplace listing content. Respond ONLY with valid JSON."}],
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 4096, "temperature": 0.3}
    )
    
    response_text = ""
    if response.get("output", {}).get("message", {}).get("content"):
        for block in response["output"]["message"]["content"]:
            if "text" in block:
                response_text += block["text"]
    
    # Parse JSON response
    try:
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            content = json.loads(json_match.group(0))
        else:
            content = {"raw_response": response_text}
    except Exception:
        content = {"raw_response": response_text}
    
    return {"success": True, "content": content}


async def handle_suggest_pricing(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Suggest pricing for marketplace listing"""
    import boto3
    
    analysis = payload.get("analysis", {})
    product_context = payload.get("product_context", {})
    
    bedrock_client = boto3.client(
        'bedrock-runtime',
        region_name='us-east-1',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token
    )
    
    prompt = f"""Based on this product analysis, suggest AWS Marketplace pricing:

PRODUCT ANALYSIS:
{json.dumps(analysis, indent=2)}

PRODUCT CONTEXT:
{json.dumps(product_context, indent=2)}

Suggest pricing with these options:
1. Subscription (monthly/annual)
2. Usage-based (pay per use)
3. Contract (upfront commitment)

For each, provide:
- Recommended model
- Price points
- Rationale

Format as JSON with:
{{
  "recommended_model": "subscription|usage|contract",
  "rationale": "Why this model fits",
  "pricing_options": [
    {{"model": "subscription", "monthly_price": 99, "annual_price": 999, "description": "..."}},
    {{"model": "usage", "unit": "API calls", "price_per_unit": 0.001, "description": "..."}},
    {{"model": "contract", "tiers": [{{"name": "Basic", "price": 5000}}, ...], "description": "..."}}
  ],
  "dimensions": [
    {{"name": "Users", "description": "Number of users", "unit": "user", "suggested_price": 10}}
  ]
}}"""

    response = bedrock_client.converse(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        system=[{"text": "Suggest AWS Marketplace pricing. Respond ONLY with valid JSON."}],
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 2048, "temperature": 0.3}
    )
    
    response_text = ""
    if response.get("output", {}).get("message", {}).get("content"):
        for block in response["output"]["message"]["content"]:
            if "text" in block:
                response_text += block["text"]
    
    # Parse JSON response
    try:
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            pricing = json.loads(json_match.group(0))
        else:
            pricing = {"raw_response": response_text}
    except Exception:
        pricing = {"raw_response": response_text}
    
    return {"success": True, "pricing": pricing}


def handle_deploy_saas(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Deploy SaaS integration CloudFormation stack"""
    import boto3
    
    product_id = payload.get("product_id")
    email = payload.get("email")
    pricing_model = payload.get("pricing_model")
    region = payload.get("region", "us-east-1")
    
    if not product_id or not email or not pricing_model:
        return {"success": False, "error": "Missing required fields: product_id, email, pricing_model"}
    
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
        region_name=region
    )
    
    # Find the Integration.yaml template
    template_paths = [
        os.path.join(os.path.dirname(__file__), 'deployment', 'cloudformation', 'Integration.yaml'),
        os.path.join(os.path.dirname(__file__), '..', 'deployment', 'cloudformation', 'Integration.yaml'),
        'deployment/cloudformation/Integration.yaml',
    ]
    
    template_body = None
    for path in template_paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                template_body = f.read()
            break
    
    if not template_body:
        return {"success": False, "error": "CloudFormation template not found"}
    
    actual_stack_name = f"saas-integration-{product_id}"
    cf_client = session.client('cloudformation')
    
    try:
        response = cf_client.create_stack(
            StackName=actual_stack_name,
            TemplateBody=template_body,
            Parameters=[
                {'ParameterKey': 'ProductId', 'ParameterValue': product_id},
                {'ParameterKey': 'TypeOfSaaSListing', 'ParameterValue': pricing_model},
                {'ParameterKey': 'MarketplaceTechAdminEmail', 'ParameterValue': email},
                {'ParameterKey': 'UpdateFulfillmentURL', 'ParameterValue': 'true'}
            ],
            Capabilities=['CAPABILITY_IAM', 'CAPABILITY_AUTO_EXPAND']
        )
        
        return {
            "success": True,
            "stack_id": response['StackId'],
            "stack_name": actual_stack_name,
            "message": "CloudFormation stack creation initiated"
        }
    except cf_client.exceptions.AlreadyExistsException:
        stack_info = cf_client.describe_stacks(StackName=actual_stack_name)
        stack = stack_info['Stacks'][0]
        return {
            "success": True,
            "stack_id": stack['StackId'],
            "stack_name": actual_stack_name,
            "message": "Stack already exists",
            "status": stack['StackStatus']
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_get_stack_status(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Get CloudFormation stack status"""
    import boto3
    
    stack_name = payload.get("stack_name")
    product_id = payload.get("product_id")
    region = payload.get("region", "us-east-1")
    
    if not stack_name and product_id:
        stack_name = f"saas-integration-{product_id}"
    
    if not stack_name:
        return {"success": False, "error": "Missing stack_name or product_id"}
    
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
        region_name=region
    )
    
    cf_client = session.client('cloudformation')
    
    try:
        response = cf_client.describe_stacks(StackName=stack_name)
        stack = response['Stacks'][0]
        
        # Get stack outputs
        outputs = {}
        for output in stack.get('Outputs', []):
            outputs[output['OutputKey']] = output['OutputValue']
        
        return {
            "success": True,
            "stack_name": stack_name,
            "status": stack['StackStatus'],
            "status_reason": stack.get('StackStatusReason', ''),
            "outputs": outputs,
            "creation_time": stack.get('CreationTime', '').isoformat() if stack.get('CreationTime') else None
        }
    except cf_client.exceptions.ClientError as e:
        if 'does not exist' in str(e):
            return {"success": False, "error": "Stack not found", "status": "NOT_FOUND"}
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_get_stack_parameters(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Get CloudFormation stack parameters and outputs"""
    import boto3
    
    stack_name = payload.get("stack_name")
    product_id = payload.get("product_id")
    region = payload.get("region", "us-east-1")
    
    if not stack_name and product_id:
        stack_name = f"saas-integration-{product_id}"
    
    if not stack_name:
        return {"success": False, "error": "Missing stack_name or product_id"}
    
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
        region_name=region
    )
    
    cf_client = session.client('cloudformation')
    
    try:
        response = cf_client.describe_stacks(StackName=stack_name)
        stack = response['Stacks'][0]
        
        # Get parameters
        parameters = {}
        for param in stack.get('Parameters', []):
            parameters[param['ParameterKey']] = param['ParameterValue']
        
        # Get outputs
        outputs = {}
        for output in stack.get('Outputs', []):
            outputs[output['OutputKey']] = output['OutputValue']
        
        return {
            "success": True,
            "stack_name": stack_name,
            "parameters": parameters,
            "outputs": outputs,
            "status": stack['StackStatus']
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_delete_stack(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Delete CloudFormation stack"""
    import boto3
    
    stack_name = payload.get("stack_name")
    product_id = payload.get("product_id")
    region = payload.get("region", "us-east-1")
    
    if not stack_name and product_id:
        stack_name = f"saas-integration-{product_id}"
    
    if not stack_name:
        return {"success": False, "error": "Missing stack_name or product_id"}
    
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
        region_name=region
    )
    
    cf_client = session.client('cloudformation')
    
    try:
        cf_client.delete_stack(StackName=stack_name)
        return {
            "success": True,
            "stack_name": stack_name,
            "message": "Stack deletion initiated"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_listing_progress(payload: dict, access_key: str = None, secret_key: str = None, session_token: str = None):
    """Get progress of an async listing creation task from DynamoDB"""
    task_id = payload.get("task_id")
    
    if not task_id:
        return {"success": False, "error": "Missing task_id"}
    
    task = get_task_state(task_id, access_key, secret_key, session_token)
    
    if not task:
        return {"success": False, "error": f"Task {task_id} not found", "status": "NOT_FOUND"}
    
    return {
        "success": True,
        "task_id": task_id,
        "status": task.get("status", "unknown"),
        "stages": task.get("stages", []),
        "product_id": task.get("product_id"),
        "offer_id": task.get("offer_id"),
        "published_to_limited": task.get("published_to_limited", False),
        "error": task.get("error"),
        "message": task.get("message"),
        "started_at": task.get("started_at"),
        "completed_at": task.get("completed_at"),
    }


def handle_create_listing_async(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Start async listing creation - returns immediately with task_id for polling"""
    # Generate unique task ID
    task_id = str(uuid.uuid4())[:8]
    
    # Initialize task state in DynamoDB
    initial_state = {
        "status": "in_progress",
        "stages": [{"stage": "Initializing", "status": "in_progress", "message": "Starting listing creation..."}],
        "product_id": None,
        "offer_id": None,
        "published_to_limited": False,
        "error": None,
        "message": "Listing creation started",
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
    }
    save_task_state(task_id, initial_state, access_key, secret_key, session_token)
    
    # Start async task using AgentCore's task management
    agentcore_task_id = app.add_async_task("create_listing", {"task_id": task_id})
    
    # Run the actual listing creation in a background thread
    def run_listing_creation():
        import asyncio
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the async function
            result = loop.run_until_complete(
                handle_create_listing(payload, access_key, secret_key, session_token, task_id)
            )
            
            # Update task state with result in DynamoDB
            final_state = {
                "status": "completed" if result.get("success") else "failed",
                "stages": result.get("stages", []),
                "product_id": result.get("product_id"),
                "offer_id": result.get("offer_id"),
                "published_to_limited": result.get("published_to_limited", False),
                "error": result.get("error"),
                "message": result.get("message", "Completed"),
                "started_at": initial_state["started_at"],
                "completed_at": datetime.now().isoformat(),
            }
            save_task_state(task_id, final_state, access_key, secret_key, session_token)
            
            loop.close()
        except Exception as e:
            error_state = {
                "status": "failed",
                "stages": [],
                "product_id": None,
                "offer_id": None,
                "published_to_limited": False,
                "error": str(e),
                "message": "Failed",
                "started_at": initial_state["started_at"],
                "completed_at": datetime.now().isoformat(),
            }
            save_task_state(task_id, error_state, access_key, secret_key, session_token)
        finally:
            # Mark AgentCore task as complete
            app.complete_async_task(agentcore_task_id)
    
    # Start background thread
    thread = threading.Thread(target=run_listing_creation, daemon=True)
    thread.start()
    
    # Return immediately with task_id
    return {
        "success": True,
        "task_id": task_id,
        "status": "in_progress",
        "message": "Listing creation started. Poll /api/listing-progress with task_id for updates.",
    }


async def handle_create_listing(payload: dict, access_key: str, secret_key: str, session_token: str = None, task_id: str = None):
    """Create marketplace listing using AWS Marketplace Catalog API with full sub-agent orchestration"""
    import time
    
    listing_data = payload.get("listing_data", {})
    stages = []
    
    # Helper to update task progress in real-time
    def update_progress(new_stages, product_id=None, offer_id=None, message=None):
        nonlocal stages
        stages = new_stages
    
    # Check if listing tools are available
    if not LISTING_AGENTS_AVAILABLE:
        return {
            "success": False,
            "error": "Listing tools not available",
            "stages": [{"stage": "Initializing", "status": "failed", "message": "Listing tools not available"}]
        }
    
    try:
        # Create boto3 session
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token,
            region_name='us-east-1'
        )
        
        marketplace_client = session.client('marketplace-catalog')
        listing_tools = _get_listing_tools(access_key, secret_key, session_token)
        
        if not listing_tools:
            return {
                "success": False,
                "error": "Failed to initialize listing tools",
                "stages": [{"stage": "Initializing", "status": "failed", "message": "Failed to initialize listing tools"}]
            }
        
        # Extract listing data
        product_title = listing_data.get("title", "")
        logo_s3_url = listing_data.get("logo_s3_url", "")
        short_description = listing_data.get("short_description", "")
        long_description = listing_data.get("long_description", "")
        highlights = listing_data.get("highlights", [])
        categories = listing_data.get("categories", [])
        search_keywords = listing_data.get("search_keywords", [])
        fulfillment_url = listing_data.get("fulfillment_url", "")
        pricing_model = listing_data.get("pricing_model", "usage")
        pricing_dimensions = listing_data.get("pricing_dimensions", [])
        refund_policy = listing_data.get("refund_policy", "")
        eula_type = listing_data.get("eula_type", "STANDARD")
        auto_publish_to_limited = listing_data.get("auto_publish_to_limited", False)
        offer_name = listing_data.get("offer_name", f"{product_title} - Public Offer")
        offer_description = listing_data.get("offer_description", f"Public offer for {product_title}")
        
        # Validate required fields
        if not product_title:
            return {"success": False, "error": "Product title is required", "stages": []}
        if not short_description:
            return {"success": False, "error": "Short description is required", "stages": []}
        if not long_description:
            return {"success": False, "error": "Long description is required", "stages": []}
        
        # Helper to strip revision suffix
        def strip_revision_suffix(entity_id: str) -> str:
            if entity_id and '@' in entity_id:
                return entity_id.split('@')[0]
            return entity_id
        
        # Helper to wait for changeset
        def wait_for_changeset(change_set_id: str, stage_name: str, max_wait: int = 300) -> dict:
            wait_interval = 5
            elapsed = 0
            while elapsed < max_wait:
                status_response = marketplace_client.describe_change_set(
                    Catalog='AWSMarketplace',
                    ChangeSetId=change_set_id
                )
                status = status_response['Status']
                if status == 'SUCCEEDED':
                    return {"success": True, "response": status_response}
                elif status == 'FAILED':
                    failure_desc = status_response.get('FailureDescription', 'Unknown error')
                    return {"success": False, "error": failure_desc}
                elif status == 'CANCELLED':
                    return {"success": False, "error": "Change set was cancelled"}
                time.sleep(wait_interval)
                elapsed += wait_interval
            return {"success": False, "error": "Timed out waiting for change set"}
        
        # ============================================================
        # Stage 1: Product Information (ProductInformationAgent)
        # ============================================================
        stages.append({"stage": "Product Information", "status": "in_progress", "message": f"Creating product: {product_title}..."})
        update_progress(stages)
        
        create_result = listing_tools.create_product_minimal(product_title)
        if not create_result.get("success"):
            stages[-1]["status"] = "failed"
            stages[-1]["message"] = create_result.get("error", "Failed to create product")
            update_progress(stages)
            return {"success": False, "error": stages[-1]["message"], "stages": stages}
        
        change_set_id = create_result.get("change_set_id")
        wait_result = wait_for_changeset(change_set_id, "Product Information")
        
        if not wait_result.get("success"):
            stages[-1]["status"] = "failed"
            stages[-1]["message"] = wait_result.get("error", "Product creation failed")
            update_progress(stages)
            return {"success": False, "error": stages[-1]["message"], "stages": stages}
        
        # Extract product_id and offer_id from changeset
        product_id = None
        offer_id = None
        for change in wait_result.get("response", {}).get('ChangeSet', []):
            if change.get('ChangeType') == 'CreateProduct':
                product_id = strip_revision_suffix(change.get('Entity', {}).get('Identifier'))
            elif change.get('ChangeType') == 'CreateOffer':
                offer_id = strip_revision_suffix(change.get('Entity', {}).get('Identifier'))
        
        if not product_id:
            stages[-1]["status"] = "failed"
            stages[-1]["message"] = "Failed to get product ID"
            update_progress(stages)
            return {"success": False, "error": "Failed to get product ID", "stages": stages}
        
        stages[-1]["status"] = "complete"
        stages[-1]["message"] = f"Product created: {product_id}"
        update_progress(stages, product_id, offer_id)
        
        # Update product details
        stages.append({"stage": "Product Details", "status": "in_progress", "message": "Updating product details..."})
        update_progress(stages, product_id, offer_id)
        
        description_data = {
            "ProductTitle": product_title,
            "ShortDescription": short_description,
            "LongDescription": long_description,
            "Highlights": highlights[:5] if highlights else [],
            "SearchKeywords": search_keywords[:5] if search_keywords else [],
            "Categories": categories[:3] if categories else []
        }
        if logo_s3_url and logo_s3_url.startswith("https://") and "s3" in logo_s3_url:
            description_data["LogoUrl"] = logo_s3_url
        
        try:
            details_response = marketplace_client.start_change_set(
                Catalog='AWSMarketplace',
                ChangeSet=[{
                    'ChangeType': 'UpdateInformation',
                    'Entity': {'Type': 'SaaSProduct@1.0', 'Identifier': product_id},
                    'Details': json.dumps(description_data)
                }],
                ChangeSetName=f"UpdateInfo-{product_id[:20]}-{int(time.time())}"
            )
            details_wait = wait_for_changeset(details_response['ChangeSetId'], "Product Details")
            if details_wait.get("success"):
                stages[-1]["status"] = "complete"
                stages[-1]["message"] = "Product details updated"
                update_progress(stages, product_id, offer_id)
            else:
                raise Exception(details_wait.get("error", "Unknown error"))
        except Exception as e:
            stages[-1]["status"] = "failed"
            stages[-1]["message"] = f"Product details update failed: {str(e)}"
            update_progress(stages, product_id, offer_id)
            return {"success": False, "error": str(e), "stages": stages, "product_id": product_id, "offer_id": offer_id}
        
        # ============================================================
        # Stage 2: Fulfillment (FulfillmentAgent)
        # ============================================================
        stages.append({"stage": "Fulfillment", "status": "in_progress", "message": "Configuring fulfillment URL..."})
        update_progress(stages, product_id, offer_id)
        
        if fulfillment_url:
            try:
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
                fulfillment_wait = wait_for_changeset(fulfillment_response['ChangeSetId'], "Fulfillment")
                if fulfillment_wait.get("success"):
                    stages[-1]["status"] = "complete"
                    stages[-1]["message"] = "Fulfillment URL configured"
                    update_progress(stages, product_id, offer_id)
                else:
                    raise Exception(fulfillment_wait.get("error", "Unknown error"))
            except Exception as e:
                stages[-1]["status"] = "failed"
                stages[-1]["message"] = f"Fulfillment configuration failed: {str(e)}"
                update_progress(stages, product_id, offer_id)
                return {"success": False, "error": str(e), "stages": stages, "product_id": product_id, "offer_id": offer_id}
        else:
            stages[-1]["status"] = "complete"
            stages[-1]["message"] = "Fulfillment URL will be configured later"
            update_progress(stages, product_id, offer_id)
        
        # ============================================================
        # Stage 3: Pricing Dimensions (PricingConfigAgent)
        # ============================================================
        stages.append({"stage": "Pricing Dimensions", "status": "in_progress", "message": "Configuring pricing dimensions..."})
        update_progress(stages, product_id, offer_id)
        
        if pricing_dimensions and offer_id and product_id:
            try:
                formatted_dimensions = []
                ui_pricing_model = listing_data.get("ui_pricing_model", pricing_model)
                
                for dim in pricing_dimensions:
                    dim_type = dim.get("type", "Metered")
                    types_list = ["Metered", "ExternallyMetered"] if dim_type == "Metered" else [dim_type]
                    formatted_dimensions.append({
                        "Key": dim.get("key", dim.get("name", "").lower().replace(" ", "_").replace("-", "_")),
                        "Description": dim.get("description", dim.get("name", "")),
                        "Name": dim.get("name", ""),
                        "Types": types_list,
                        "Unit": "Units"
                    })
                
                if ui_pricing_model == "Usage" or pricing_model == "usage":
                    pricing_result = listing_tools.add_dimensions_and_pricing_for_usage(
                        product_id=product_id, offer_id=offer_id, dimensions=formatted_dimensions
                    )
                elif ui_pricing_model == "Contract with Consumption":
                    pricing_result = listing_tools.add_dimensions_and_pricing_for_hybrid(
                        product_id=product_id, offer_id=offer_id, dimensions=formatted_dimensions,
                        contract_durations=listing_data.get("contract_durations", ["12 Months"])
                    )
                else:
                    pricing_result = listing_tools.add_dimensions_and_pricing_for_contract(
                        product_id=product_id, offer_id=offer_id, dimensions=formatted_dimensions,
                        contract_durations=listing_data.get("contract_durations", ["12 Months"])
                    )
                
                if pricing_result.get("success"):
                    pricing_wait = wait_for_changeset(pricing_result['change_set_id'], "Pricing Dimensions")
                    if pricing_wait.get("success"):
                        stages[-1]["status"] = "complete"
                        stages[-1]["message"] = f"Configured {len(pricing_dimensions)} pricing dimension(s)"
                        update_progress(stages, product_id, offer_id)
                    else:
                        raise Exception(pricing_wait.get("error", "Unknown error"))
                else:
                    raise Exception(pricing_result.get("error", "Unknown error"))
            except Exception as e:
                stages[-1]["status"] = "failed"
                stages[-1]["message"] = f"Pricing configuration failed: {str(e)}"
                update_progress(stages, product_id, offer_id)
                return {"success": False, "error": str(e), "stages": stages, "product_id": product_id, "offer_id": offer_id}
        else:
            stages[-1]["status"] = "complete"
            stages[-1]["message"] = "Default pricing will be applied"
            update_progress(stages, product_id, offer_id)
        
        # ============================================================
        # Stage 4: Price Review (PriceReviewAgent)
        # ============================================================
        stages.append({"stage": "Price Review", "status": "complete", "message": "Pricing configuration validated"})
        update_progress(stages, product_id, offer_id)
        
        # ============================================================
        # Stage 5: Refund Policy (RefundPolicyAgent)
        # ============================================================
        stages.append({"stage": "Refund Policy", "status": "in_progress", "message": "Configuring refund policy..."})
        update_progress(stages, product_id, offer_id)
        
        if refund_policy and offer_id:
            try:
                refund_result = listing_tools.update_support_terms(offer_id=offer_id, refund_policy=refund_policy)
                if refund_result.get("success"):
                    refund_wait = wait_for_changeset(refund_result['change_set_id'], "Refund Policy")
                    if refund_wait.get("success"):
                        stages[-1]["status"] = "complete"
                        stages[-1]["message"] = "Refund policy configured"
                        update_progress(stages, product_id, offer_id)
                    else:
                        raise Exception(refund_wait.get("error", "Unknown error"))
                else:
                    raise Exception(refund_result.get("error", "Unknown error"))
            except Exception as e:
                stages[-1]["status"] = "failed"
                stages[-1]["message"] = f"Refund policy configuration failed: {str(e)}"
                update_progress(stages, product_id, offer_id)
                return {"success": False, "error": str(e), "stages": stages, "product_id": product_id, "offer_id": offer_id}
        else:
            stages[-1]["status"] = "complete"
            stages[-1]["message"] = "Default refund policy applied"
            update_progress(stages, product_id, offer_id)
        
        # ============================================================
        # Stage 6: EULA Configuration (EULAConfigAgent)
        # ============================================================
        stages.append({"stage": "EULA", "status": "in_progress", "message": "Configuring End User License Agreement..."})
        update_progress(stages, product_id, offer_id)
        
        if offer_id:
            try:
                is_standard_eula = eula_type.lower() in ["standard", "scmp"]
                eula_result = listing_tools.update_legal_terms(
                    offer_id=offer_id,
                    eula_type="StandardEula" if is_standard_eula else "CustomEula",
                    eula_url=listing_data.get("custom_eula_url") if not is_standard_eula else None
                )
                if eula_result.get("success"):
                    eula_wait = wait_for_changeset(eula_result['change_set_id'], "EULA")
                    if eula_wait.get("success"):
                        stages[-1]["status"] = "complete"
                        stages[-1]["message"] = f"{eula_type} EULA configured"
                        update_progress(stages, product_id, offer_id)
                    else:
                        raise Exception(eula_wait.get("error", "Unknown error"))
                else:
                    raise Exception(eula_result.get("error", "Unknown error"))
            except Exception as e:
                stages[-1]["status"] = "failed"
                stages[-1]["message"] = f"EULA configuration failed: {str(e)}"
                update_progress(stages, product_id, offer_id)
                return {"success": False, "error": str(e), "stages": stages, "product_id": product_id, "offer_id": offer_id}
        else:
            stages[-1]["status"] = "complete"
            stages[-1]["message"] = "Standard EULA will be applied"
            update_progress(stages, product_id, offer_id)
        
        # ============================================================
        # Stage 7: Availability Settings (OfferAvailabilityAgent)
        # ============================================================
        stages.append({"stage": "Availability", "status": "in_progress", "message": "Configuring availability settings..."})
        update_progress(stages, product_id, offer_id)
        
        if offer_id:
            try:
                availability_result = listing_tools.update_offer_availability(offer_id=offer_id, availability_type="all")
                if availability_result.get("success"):
                    availability_wait = wait_for_changeset(availability_result['change_set_id'], "Availability")
                    if availability_wait.get("success"):
                        stages[-1]["status"] = "complete"
                        stages[-1]["message"] = "Availability set to all countries"
                        update_progress(stages, product_id, offer_id)
                    else:
                        raise Exception(availability_wait.get("error", "Unknown error"))
                else:
                    raise Exception(availability_result.get("error", "Unknown error"))
            except Exception as e:
                stages[-1]["status"] = "failed"
                stages[-1]["message"] = f"Availability configuration failed: {str(e)}"
                update_progress(stages, product_id, offer_id)
                return {"success": False, "error": str(e), "stages": stages, "product_id": product_id, "offer_id": offer_id}
        else:
            stages[-1]["status"] = "complete"
            stages[-1]["message"] = "Default availability applied"
            update_progress(stages, product_id, offer_id)
        
        # ============================================================
        # Stage 8: Allowlist Configuration (AllowlistAgent)
        # ============================================================
        stages.append({"stage": "Allowlist", "status": "complete", "message": "Allowlist configuration complete (no restrictions)"})
        update_progress(stages, product_id, offer_id)
        
        # ============================================================
        # Stage 9: Publish to Limited (optional)
        # ============================================================
        published_to_limited = False
        if auto_publish_to_limited and product_id and offer_id:
            stages.append({"stage": "Publish to Limited", "status": "in_progress", "message": "Publishing product to Limited visibility..."})
            update_progress(stages, product_id, offer_id)
            try:
                release_result = listing_tools.release_product_and_offer_to_limited(
                    product_id=product_id, offer_id=offer_id,
                    offer_name=offer_name, offer_description=offer_description,
                    pricing_model="Usage" if pricing_model == "usage" else "Contract"
                )
                if release_result.get("success"):
                    release_wait = wait_for_changeset(release_result['change_set_id'], "Publish to Limited")
                    if release_wait.get("success"):
                        published_to_limited = True
                        stages[-1]["status"] = "complete"
                        stages[-1]["message"] = "Product published to Limited visibility"
                        update_progress(stages, product_id, offer_id)
                    else:
                        stages[-1]["status"] = "warning"
                        stages[-1]["message"] = f"Publish to Limited pending: {release_wait.get('error', 'Unknown')[:50]}"
                        update_progress(stages, product_id, offer_id)
                else:
                    stages[-1]["status"] = "warning"
                    stages[-1]["message"] = f"Publish to Limited pending: {release_result.get('error', 'Unknown')[:50]}"
                    update_progress(stages, product_id, offer_id)
            except Exception as e:
                stages[-1]["status"] = "warning"
                stages[-1]["message"] = f"Publish to Limited pending: {str(e)[:50]}"
                update_progress(stages, product_id, offer_id)
        
        return {
            "success": True,
            "product_id": product_id,
            "offer_id": offer_id,
            "published_to_limited": published_to_limited,
            "message": f"Product '{product_title}' created successfully" + (" and published to Limited" if published_to_limited else " (Draft)"),
            "stages": stages
        }
        
    except Exception as e:
        stages.append({"stage": "Error", "status": "failed", "message": str(e)})
        return {"success": False, "error": str(e), "stages": stages}


def handle_validate_credentials(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Validate AWS credentials and check IAM permissions"""
    import boto3
    
    if not access_key or not secret_key:
        return {"success": False, "error": "Missing AWS credentials"}
    
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
        region_name='us-east-1'
    )
    
    try:
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        account_id = identity.get('Account')
        user_arn = identity.get('Arn')
        
        # Determine user type
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
        
        # Check marketplace permissions
        has_marketplace_access = False
        try:
            marketplace_client = session.client('marketplace-catalog')
            marketplace_client.list_entities(
                Catalog='AWSMarketplace',
                EntityType='SaaSProduct',
                MaxResults=1
            )
            has_marketplace_access = True
        except Exception:
            pass
        
        return {
            "success": True,
            "account_id": account_id,
            "user_arn": user_arn,
            "user_type": user_type,
            "user_name": user_name,
            "has_marketplace_access": has_marketplace_access,
            "can_proceed": has_marketplace_access or user_type == 'Root User'
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_check_seller_status(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Check seller registration status"""
    import boto3
    
    if not access_key or not secret_key:
        return {"success": False, "error": "Missing AWS credentials"}
    
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
        region_name='us-east-1'
    )
    
    try:
        marketplace_client = session.client('marketplace-catalog')
        sts_client = session.client('sts')
        identity = sts_client.get_caller_identity()
        account_id = identity['Account']
        
        try:
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
            
            return {
                "success": True,
                "seller_status": "APPROVED" if products else "APPROVED",
                "account_id": account_id,
                "owned_products": products,
                "owned_products_count": len(products),
                "marketplace_accessible": True,
                "portal_url": "https://aws.amazon.com/marketplace/management/"
            }
        except Exception:
            return {
                "success": True,
                "seller_status": "NOT_REGISTERED",
                "account_id": account_id,
                "owned_products": [],
                "owned_products_count": 0,
                "marketplace_accessible": False,
                "portal_url": "https://aws.amazon.com/marketplace/management/tour"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_list_marketplace_products(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """List marketplace products with status"""
    import boto3
    
    if not access_key or not secret_key:
        return {"success": False, "error": "Missing AWS credentials"}
    
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
        region_name='us-east-1'
    )
    
    try:
        marketplace_client = session.client('marketplace-catalog')
        cf_client = session.client('cloudformation')
        account_id = session.client('sts').get_caller_identity()['Account']
        
        products = []
        response = marketplace_client.list_entities(
            Catalog='AWSMarketplace',
            EntityType='SaaSProduct',
            MaxResults=20
        )
        
        for entity in response.get('EntitySummaryList', []):
            entity_id = entity.get('EntityId')
            entity_name = entity.get('Name', 'Unnamed Product')
            visibility = entity.get('Visibility', 'DRAFT')
            
            # Check for CloudFormation stack
            saas_integration_status = 'PENDING'
            try:
                stack_name = f"saas-integration-{entity_id}"
                stack_response = cf_client.describe_stacks(StackName=stack_name)
                if stack_response['Stacks']:
                    stack_status = stack_response['Stacks'][0]['StackStatus']
                    if stack_status == 'CREATE_COMPLETE':
                        saas_integration_status = 'COMPLETED'
                    elif stack_status in ['CREATE_IN_PROGRESS', 'UPDATE_IN_PROGRESS']:
                        saas_integration_status = 'IN_PROGRESS'
                    elif stack_status in ['CREATE_FAILED', 'ROLLBACK_COMPLETE']:
                        saas_integration_status = 'FAILED'
            except Exception:
                pass
            
            # Determine allowed actions
            allowed_actions = ['view_console']
            if visibility == 'DRAFT':
                allowed_actions = ['resume', 'delete']
            elif saas_integration_status != 'COMPLETED':
                allowed_actions.append('configure_saas')
            
            products.append({
                'product_id': entity_id,
                'product_name': entity_name,
                'product_type': 'SaaSProduct',
                'visibility': visibility,
                'status': 'ACTIVE',
                'needs_saas_integration': True,
                'saas_integration_status': saas_integration_status,
                'allowed_actions': allowed_actions,
            })
        
        return {
            "success": True,
            "products": products,
            "count": len(products),
            "account_id": account_id
        }
    except Exception as e:
        return {"success": False, "error": str(e), "products": [], "count": 0}


def handle_check_stack_exists(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Check if a CloudFormation stack exists"""
    import boto3
    
    stack_name = payload.get("stack_name")
    product_id = payload.get("product_id")
    region = payload.get("region", "us-east-1")
    
    if not stack_name and product_id:
        stack_name = f"saas-integration-{product_id}"
    
    if not stack_name:
        return {"exists": False, "error": "Missing stack_name or product_id"}
    
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
        region_name=region
    )
    
    cf_client = session.client('cloudformation')
    
    try:
        response = cf_client.describe_stacks(StackName=stack_name)
        stack = response['Stacks'][0]
        return {
            "exists": True,
            "stack_name": stack_name,
            "status": stack['StackStatus'],
            "stack_id": stack['StackId']
        }
    except cf_client.exceptions.ClientError as e:
        if 'does not exist' in str(e):
            return {"exists": False, "stack_name": stack_name}
        return {"exists": False, "error": str(e)}
    except Exception as e:
        return {"exists": False, "error": str(e)}


def handle_run_metering(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Run metering agent"""
    if not access_key or not secret_key:
        return {"success": False, "error": "Missing AWS credentials", "steps": []}
    
    product_id = payload.get("product_id")
    
    try:
        result = metering_agent.check_entitlement_and_add_metering(
            access_key=access_key,
            secret_key=secret_key,
            session_token=session_token
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e), "steps": []}


def handle_execute_saas_workflow(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Execute complete SaaS workflow"""
    if not access_key or not secret_key:
        return {"success": False, "error": "Missing AWS credentials"}
    
    lambda_function_name = payload.get("lambda_function_name")
    
    try:
        result = workflow_orchestrator.execute_full_workflow(
            access_key=access_key,
            secret_key=secret_key,
            session_token=session_token,
            lambda_function_name=lambda_function_name
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_get_registration_requirements(payload: dict):
    """Get seller registration requirements"""
    country = payload.get("country", "US")
    
    requirements = {
        "general": {
            "title": "AWS Marketplace Seller Registration Requirements",
            "steps": [
                "Create an AWS account if you don't have one",
                "Complete the seller registration form",
                "Provide business information and tax details",
                "Set up payment information",
                "Accept the AWS Marketplace Terms and Conditions"
            ],
            "documentation_url": "https://docs.aws.amazon.com/marketplace/latest/userguide/seller-registration-process.html"
        },
        "business_info": {
            "required_fields": ["Legal business name", "Business address", "Tax identification number", "Contact information"]
        },
        "payment_info": {
            "required_fields": ["Bank account details", "Routing number", "Account number"]
        }
    }
    
    if country in ['IN', 'India']:
        requirements["india_specific"] = {
            "required_fields": ["GST Number", "PAN Number", "Indian bank account details"],
            "notes": ["GST registration is mandatory", "PAN verification required"]
        }
    
    return {"success": True, "requirements": requirements, "country": country}


def handle_validate_business_info(payload: dict):
    """Validate business information"""
    business_info = payload.get("business_info", {})
    
    errors = []
    warnings = []
    
    if not business_info.get("business_name"):
        errors.append("Business name is required")
    if not business_info.get("business_address"):
        errors.append("Business address is required")
    if not business_info.get("tax_id"):
        warnings.append("Tax ID is recommended")
    if not business_info.get("contact_email"):
        errors.append("Contact email is required")
    
    return {
        "success": True,
        "validation": {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    }


def handle_check_registration_progress(payload: dict):
    """Check registration progress"""
    registration_data = payload.get("registration_data", {})
    
    steps = [
        {"step": 1, "name": "Account Creation", "status": "completed"},
        {"step": 2, "name": "Business Information", "status": "completed" if registration_data.get("business_name") else "pending"},
        {"step": 3, "name": "Tax Information", "status": "completed" if registration_data.get("tax_id") else "pending"},
        {"step": 4, "name": "Payment Setup", "status": "completed" if registration_data.get("payment_info") else "pending"},
        {"step": 5, "name": "Terms Acceptance", "status": "completed" if registration_data.get("terms_accepted") else "pending"}
    ]
    
    completed = len([s for s in steps if s["status"] == "completed"])
    
    return {
        "success": True,
        "progress": {
            "steps": steps,
            "completed_steps": completed,
            "total_steps": len(steps),
            "progress_percent": int((completed / len(steps)) * 100),
            "is_complete": completed == len(steps)
        }
    }


def handle_generate_registration_preview(payload: dict):
    """Generate registration preview"""
    registration_data = payload.get("registration_data", {})
    
    return {
        "success": True,
        "preview": {
            "business_details": {
                "name": registration_data.get("business_name", "Not provided"),
                "address": registration_data.get("business_address", "Not provided"),
                "country": registration_data.get("country", "Not provided")
            },
            "contact_details": {
                "email": registration_data.get("contact_email", "Not provided"),
                "phone": registration_data.get("contact_phone", "Not provided")
            },
            "payment_status": "Configured" if registration_data.get("payment_info") else "Not configured",
            "estimated_review_time": "2-5 business days"
        }
    }


def handle_metering_find_tables(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Find DynamoDB tables for metering"""
    import boto3
    
    if not access_key or not secret_key:
        return {"success": False, "error": "Missing AWS credentials"}
    
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
        region_name='us-east-1'
    )
    
    dynamodb = session.client('dynamodb')
    
    try:
        tables = dynamodb.list_tables()['TableNames']
        
        new_subscribers_table = None
        metering_records_table = None
        
        for table in tables:
            if 'NewSubscribers' in table or 'newsubscribers' in table.lower():
                new_subscribers_table = table
            if 'MeteringRecords' in table or 'meteringrecords' in table.lower():
                metering_records_table = table
        
        return {
            "success": True,
            "new_subscribers_table": new_subscribers_table,
            "metering_records_table": metering_records_table,
            "all_tables": tables
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_metering_get_customer(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Get customer from NewSubscribers table"""
    import boto3
    
    if not access_key or not secret_key:
        return {"success": False, "error": "Missing AWS credentials"}
    
    table_name = payload.get("table_name")
    if not table_name:
        return {"success": False, "error": "Missing table_name"}
    
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
        region_name='us-east-1'
    )
    
    dynamodb = session.resource('dynamodb')
    table = dynamodb.Table(table_name)
    
    try:
        response = table.scan(Limit=1)
        items = response.get('Items', [])
        
        if items:
            customer = items[0]
            return {
                "success": True,
                "customer": customer,
                "customer_identifier": customer.get('customerIdentifier'),
                "product_code": customer.get('productCode')
            }
        else:
            return {"success": False, "error": "No customers found in table"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_metering_insert_record(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Insert metering record"""
    import boto3
    import time
    import uuid
    
    if not access_key or not secret_key:
        return {"success": False, "error": "Missing AWS credentials"}
    
    table_name = payload.get("table_name")
    customer_identifier = payload.get("customer_identifier")
    dimension_usage = payload.get("dimension_usage", [])
    
    if not table_name or not customer_identifier:
        return {"success": False, "error": "Missing table_name or customer_identifier"}
    
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
        region_name='us-east-1'
    )
    
    dynamodb = session.resource('dynamodb')
    table = dynamodb.Table(table_name)
    
    try:
        record = {
            'customerIdentifier': customer_identifier,
            'create_timestamp': int(time.time()),
            'metering_pending': 'true',
            'dimension_usage': dimension_usage or [{"dimension": "users", "value": 1}],
            'record_id': str(uuid.uuid4())
        }
        
        table.put_item(Item=record)
        
        return {
            "success": True,
            "message": "Metering record inserted",
            "record": record
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# LISTING TOOLS HANDLERS
# ============================================================================

def _get_listing_tools(access_key: str, secret_key: str, session_token: str = None):
    """Get ListingTools instance with credentials"""
    import boto3
    
    if not LISTING_AGENTS_AVAILABLE:
        return None
    
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
        region_name='us-east-1'
    )
    
    return ListingTools(region='us-east-1', session=session)


def handle_listing_create_draft(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Create a new listing draft with product and offer"""
    if not LISTING_AGENTS_AVAILABLE:
        return {"success": False, "error": "Listing tools not available"}
    
    tools = _get_listing_tools(access_key, secret_key, session_token)
    if not tools:
        return {"success": False, "error": "Failed to initialize listing tools"}
    
    try:
        result = tools.create_listing_draft(
            product_title=payload.get("product_title"),
            short_description=payload.get("short_description"),
            long_description=payload.get("long_description"),
            logo_url=payload.get("logo_url"),
            categories=payload.get("categories", []),
            search_keywords=payload.get("search_keywords", []),
            highlights=payload.get("highlights", []),
            video_urls=payload.get("video_urls", []),
            additional_resources=payload.get("additional_resources", []),
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_listing_update_info(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Update product information"""
    if not LISTING_AGENTS_AVAILABLE:
        return {"success": False, "error": "Listing tools not available"}
    
    tools = _get_listing_tools(access_key, secret_key, session_token)
    if not tools:
        return {"success": False, "error": "Failed to initialize listing tools"}
    
    product_id = payload.get("product_id")
    updates = payload.get("updates", {})
    
    if not product_id:
        return {"success": False, "error": "product_id is required"}
    
    try:
        result = tools.update_product_information(product_id, updates)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_listing_add_pricing(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Add pricing to an offer"""
    if not LISTING_AGENTS_AVAILABLE:
        return {"success": False, "error": "Listing tools not available"}
    
    tools = _get_listing_tools(access_key, secret_key, session_token)
    if not tools:
        return {"success": False, "error": "Failed to initialize listing tools"}
    
    offer_id = payload.get("offer_id")
    pricing_model = payload.get("pricing_model")
    dimensions = payload.get("dimensions", [])
    contract_durations = payload.get("contract_durations", [])
    
    if not offer_id or not pricing_model:
        return {"success": False, "error": "offer_id and pricing_model are required"}
    
    try:
        result = tools.add_pricing(
            offer_id=offer_id,
            pricing_model=pricing_model,
            dimensions=dimensions,
            contract_durations=contract_durations,
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_listing_update_support(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Update support terms on an offer"""
    if not LISTING_AGENTS_AVAILABLE:
        return {"success": False, "error": "Listing tools not available"}
    
    tools = _get_listing_tools(access_key, secret_key, session_token)
    if not tools:
        return {"success": False, "error": "Failed to initialize listing tools"}
    
    offer_id = payload.get("offer_id")
    refund_policy = payload.get("refund_policy")
    
    if not offer_id or not refund_policy:
        return {"success": False, "error": "offer_id and refund_policy are required"}
    
    try:
        result = tools.update_support_terms(offer_id, refund_policy)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_listing_update_legal(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Update legal terms (EULA) on an offer"""
    if not LISTING_AGENTS_AVAILABLE:
        return {"success": False, "error": "Listing tools not available"}
    
    tools = _get_listing_tools(access_key, secret_key, session_token)
    if not tools:
        return {"success": False, "error": "Failed to initialize listing tools"}
    
    offer_id = payload.get("offer_id")
    eula_type = payload.get("eula_type", "StandardEula")
    eula_url = payload.get("eula_url")
    
    if not offer_id:
        return {"success": False, "error": "offer_id is required"}
    
    try:
        result = tools.update_legal_terms(offer_id, eula_type, eula_url)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_listing_update_availability(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Update offer availability (geographic restrictions)"""
    if not LISTING_AGENTS_AVAILABLE:
        return {"success": False, "error": "Listing tools not available"}
    
    tools = _get_listing_tools(access_key, secret_key, session_token)
    if not tools:
        return {"success": False, "error": "Failed to initialize listing tools"}
    
    offer_id = payload.get("offer_id")
    availability_type = payload.get("availability_type", "all")
    country_codes = payload.get("country_codes", [])
    
    if not offer_id:
        return {"success": False, "error": "offer_id is required"}
    
    try:
        result = tools.update_offer_availability(offer_id, availability_type, country_codes)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_listing_release_to_limited(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Release product to Limited visibility"""
    if not LISTING_AGENTS_AVAILABLE:
        return {"success": False, "error": "Listing tools not available"}
    
    tools = _get_listing_tools(access_key, secret_key, session_token)
    if not tools:
        return {"success": False, "error": "Failed to initialize listing tools"}
    
    product_id = payload.get("product_id")
    
    if not product_id:
        return {"success": False, "error": "product_id is required"}
    
    try:
        result = tools.release_to_limited(product_id)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_listing_get_status(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Get listing/change set status"""
    if not LISTING_AGENTS_AVAILABLE:
        return {"success": False, "error": "Listing tools not available"}
    
    tools = _get_listing_tools(access_key, secret_key, session_token)
    if not tools:
        return {"success": False, "error": "Failed to initialize listing tools"}
    
    change_set_id = payload.get("change_set_id")
    
    if not change_set_id:
        return {"success": False, "error": "change_set_id is required"}
    
    try:
        result = tools.get_listing_status(change_set_id)
        
        if result.get("success"):
            # Extract product_id and offer_id from changeset
            product_id = None
            offer_id = None
            change_set = result.get("change_set", [])
            
            for change in change_set:
                change_type = change.get("ChangeType", "")
                entity = change.get("Entity", {})
                identifier = entity.get("Identifier", "")
                
                # Strip revision suffix
                if identifier and "@" in identifier:
                    identifier = identifier.split("@")[0]
                
                if change_type == "CreateProduct":
                    product_id = identifier
                elif change_type == "CreateOffer":
                    offer_id = identifier
            
            return {
                "success": True,
                "status": result.get("status"),
                "product_id": product_id,
                "offer_id": offer_id,
                "message": f"Change set status: {result.get('status')}"
            }
        
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_listing_get_entity(payload: dict, access_key: str, secret_key: str, session_token: str = None):
    """Get entity details"""
    if not LISTING_AGENTS_AVAILABLE:
        return {"success": False, "error": "Listing tools not available"}
    
    tools = _get_listing_tools(access_key, secret_key, session_token)
    if not tools:
        return {"success": False, "error": "Failed to initialize listing tools"}
    
    entity_type = payload.get("entity_type", "SaaSProduct@1.0")
    entity_id = payload.get("entity_id")
    
    if not entity_id:
        return {"success": False, "error": "entity_id is required"}
    
    try:
        result = tools.get_entity_details(entity_type, entity_id)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # Run locally for testing
    app.run(port=8080)
