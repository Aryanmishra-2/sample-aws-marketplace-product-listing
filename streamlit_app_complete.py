#!/usr/bin/env python3
"""
AI-Guided AWS Marketplace Listing Creation

This app uses LLMs to automate listing creation based on product documentation.
Users provide links/docs, and the AI generates all required fields.
"""

import streamlit as st
from agent.orchestrator import ListingOrchestrator, WorkflowStage
from agent.tools.listing_tools import ListingTools
import boto3
import json
import re

# Configure page
st.set_page_config(
    page_title="AI-Guided Marketplace Listing",
    page_icon="🤖",
    layout="wide"
)


def sanitize_text_for_marketplace(text: str) -> str:
    """
    Sanitize text to remove unsupported characters for AWS Marketplace.
    AWS Marketplace only supports basic ASCII characters.
    """
    if not text:
        return text
    
    # Replace common Unicode characters with ASCII equivalents
    replacements = [
        ('•', '-'),          # Bullet point
        ('–', '-'),          # En dash
        ('—', '-'),          # Em dash
        ('"', '"'),          # Left double quote
        ('"', '"'),          # Right double quote
        (''', "'"),          # Left single quote
        (''', "'"),          # Right single quote
        ('…', '...'),        # Ellipsis
        ('®', '(R)'),        # Registered trademark
        ('™', '(TM)'),       # Trademark
        ('©', '(C)'),        # Copyright
        ('°', ' degrees'),   # Degree symbol
        ('×', 'x'),          # Multiplication sign
        ('÷', '/'),          # Division sign
    ]
    
    for unicode_char, ascii_char in replacements:
        text = text.replace(unicode_char, ascii_char)
    
    # Remove any remaining non-ASCII characters (but preserve newlines and tabs)
    # Split by lines to preserve line breaks
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # Remove non-ASCII from each line
        cleaned_line = line.encode('ascii', 'ignore').decode('ascii')
        # Clean up multiple spaces within the line (but not leading/trailing)
        cleaned_line = re.sub(r' +', ' ', cleaned_line)
        cleaned_lines.append(cleaned_line.strip())
    
    # Rejoin with newlines
    text = '\n'.join(cleaned_lines)
    
    return text.strip()


def init_session_state():
    """Initialize session state"""
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    if 'product_context' not in st.session_state:
        st.session_state.product_context = {}
    
    if 'current_step' not in st.session_state:
        st.session_state.current_step = "credentials"
    
    if 'aws_credentials' not in st.session_state:
        st.session_state.aws_credentials = None
    
    if 'credentials_validated' not in st.session_state:
        st.session_state.credentials_validated = False


def init_agents_with_credentials():
    """Initialize agents with user-provided credentials"""
    if 'strands_agent' not in st.session_state and st.session_state.credentials_validated:
        try:
            # Create boto3 session with user credentials
            creds = st.session_state.aws_credentials
            session = boto3.Session(
                aws_access_key_id=creds['access_key'],
                aws_secret_access_key=creds['secret_key'],
                aws_session_token=creds.get('session_token'),
                region_name=creds.get('region', 'us-east-1')
            )
            
            # Use integrated Strands agent with credentials
            from agent.strands_marketplace_agent import StrandsMarketplaceAgent
            from agent.tools.listing_tools import ListingTools
            
            # Create listing tools with session
            listing_tools = ListingTools(region=creds.get('region', 'us-east-1'), session=session)
            
            # Create agent with listing tools
            st.session_state.strands_agent = StrandsMarketplaceAgent()
            st.session_state.strands_agent.listing_tools = listing_tools
            st.session_state.strands_agent.orchestrator.listing_tools = listing_tools
            st.session_state.orchestrator = st.session_state.strands_agent.orchestrator
            
            # Store session for Phase 2
            st.session_state.boto3_session = session
            
        except Exception as e:
            st.error(f"⚠️ Failed to initialize agents: {str(e)}")
            st.session_state.strands_agent = None


def call_bedrock_llm(prompt: str, system_prompt: str = None, model_id: str = None) -> str:
    """Call Amazon Bedrock to generate responses"""
    try:
        # Use user-provided credentials if available
        if st.session_state.get('boto3_session'):
            bedrock = st.session_state.boto3_session.client('bedrock-runtime')
        else:
            bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        messages = [{"role": "user", "content": prompt}]
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "messages": messages,
            "temperature": 0.7
        }
        
        if system_prompt:
            request_body["system"] = system_prompt
        
        # Model priority list (try in order)
        if not model_id:
            model_ids = [
                "us.anthropic.claude-3-5-sonnet-20241022-v2:0",  # Claude 3.5 Sonnet v2 (inference profile)
                "anthropic.claude-3-5-sonnet-20241022-v2:0",     # Claude 3.5 Sonnet v2 (direct)
                "anthropic.claude-3-5-sonnet-20240620-v1:0",     # Claude 3.5 Sonnet v1 (stable)
                "anthropic.claude-3-sonnet-20240229-v1:0"        # Claude 3 Sonnet (fallback)
            ]
        else:
            model_ids = [model_id]
        
        last_error = None
        for mid in model_ids:
            try:
                response = bedrock.invoke_model(
                    modelId=mid,
                    body=json.dumps(request_body)
                )
                response_body = json.loads(response['body'].read())
                return response_body['content'][0]['text']
            except Exception as e:
                last_error = e
                continue
        
        # If all models failed, raise the last error
        raise last_error
    
    except Exception as e:
        st.error(f"Error calling Bedrock: {str(e)}")
        st.info("💡 Tip: Make sure you have requested access to Claude models in the Bedrock console")
        return None


def credentials_screen():
    """AWS Credentials input screen"""
    st.title("🔐 AWS Credentials Setup")
    
    st.markdown("""
    ### Secure Credential Input
    
    Please provide your AWS credentials to access AWS Marketplace and Bedrock services.
    
    **Required Permissions:**
    - AWS Marketplace Catalog API
    - Amazon Bedrock (for AI features)
    - CloudFormation (for infrastructure deployment)
    - DynamoDB, Lambda, API Gateway, SNS (for SaaS integration)
    
    **Security Note:** Credentials are only stored in your browser session and never saved to disk.
    """)
    
    st.divider()
    
    with st.form("credentials_form"):
        access_key = st.text_input(
            "AWS Access Key ID *",
            type="password",
            help="Your AWS access key (e.g., AKIAIOSFODNN7EXAMPLE)"
        )
        
        secret_key = st.text_input(
            "AWS Secret Access Key *",
            type="password",
            help="Your AWS secret access key"
        )
        
        session_token = st.text_input(
            "AWS Session Token (Optional)",
            type="password",
            help="Required only if using temporary credentials"
        )
        
        region = st.selectbox(
            "AWS Region *",
            options=['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1'],
            index=0,
            help="AWS region for Marketplace and Bedrock operations"
        )
        
        submitted = st.form_submit_button("Validate & Continue", type="primary", use_container_width=True)
        
        if submitted:
            if not access_key or not secret_key:
                st.error("❌ Please provide both Access Key and Secret Key")
            else:
                # Validate credentials
                with st.spinner("🔍 Validating AWS credentials..."):
                    try:
                        # Test credentials with STS
                        sts_client = boto3.client(
                            'sts',
                            region_name=region,
                            aws_access_key_id=access_key,
                            aws_secret_access_key=secret_key,
                            aws_session_token=session_token if session_token else None
                        )
                        identity = sts_client.get_caller_identity()
                        
                        # Store credentials in session state
                        st.session_state.aws_credentials = {
                            'access_key': access_key,
                            'secret_key': secret_key,
                            'session_token': session_token if session_token else None,
                            'region': region,
                            'account_id': identity['Account'],
                            'user_arn': identity['Arn']
                        }
                        st.session_state.credentials_validated = True
                        
                        # Initialize agents with credentials
                        init_agents_with_credentials()
                        
                        st.success(f"✅ Credentials validated for account: {identity['Account']}")
                        st.info(f"👤 User: {identity['Arn']}")
                        
                        # Move to welcome screen
                        st.session_state.current_step = "welcome"
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Credential validation failed: {str(e)}")
                        st.info("💡 Please check your credentials and try again")
    
    st.divider()
    st.caption("🔒 Your credentials are encrypted in transit and only stored in your browser session")


def welcome_screen():
    """Welcome screen with workflow selection"""
    st.title("🤖 AI-Guided AWS Marketplace Listing Creation")
    
    # Show credential status
    if st.session_state.credentials_validated:
        creds = st.session_state.aws_credentials
        st.success(f"✅ Connected to AWS Account: {creds['account_id']} ({creds['region']})")
    
    st.markdown("""
    ### Welcome! Let's create your AWS Marketplace listing together.
    
    This AI-powered workflow will:
    - 📄 Analyze your product documentation
    - 💡 Suggest the best pricing model
    - ✍️ Generate all required text fields automatically
    - 🎯 Select appropriate categories and keywords
    - 🚀 Create your listing in minutes
    
    **No AWS Marketplace expertise required!**
    """)
    
    st.divider()
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← Change Credentials"):
            st.session_state.current_step = "credentials"
            st.session_state.credentials_validated = False
            st.rerun()
    
    with col2:
        if st.button("Start AI-Guided Creation", type="primary", use_container_width=True):
            st.session_state.current_step = "gather_context"
            st.rerun()


def gather_context_screen():
    """Gather product context from user"""
    st.title("📄 Tell Us About Your Product")
    
    st.markdown("""
    Provide URLs to your product information so our AI can analyze it and create your marketplace listing.
    """)
    
    st.write("**Product URLs:**")
    website_url = st.text_input(
        "Product Website *", 
        placeholder="https://yourproduct.com",
        help="Main product website or landing page"
    )
    docs_url = st.text_input(
        "Documentation URL (optional)", 
        placeholder="https://docs.yourproduct.com",
        help="Technical documentation or user guides"
    )
    pricing_url = st.text_input(
        "Pricing Page (optional)", 
        placeholder="https://yourproduct.com/pricing",
        help="Your existing pricing page if available"
    )
    
    st.divider()
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Back"):
            st.session_state.current_step = "welcome"
            st.rerun()
    
    with col2:
        if st.button("Continue →", type="primary", use_container_width=True):
            # Validate at least website URL is provided
            if not website_url:
                st.error("Please provide at least your product website URL")
                return
            
            # Store context
            context = {
                "website_url": website_url,
                "docs_url": docs_url,
                "pricing_url": pricing_url,
                "product_description": "",
                "uploaded_file": None
            }
            
            st.session_state.product_context = context
            st.session_state.current_step = "analyze_product"
            st.rerun()


def analyze_product_screen():
    """AI analyzes product and generates suggestions"""
    st.title("🔍 Analyzing Your Product...")
    
    context = st.session_state.product_context
    
    # Show what we're analyzing
    with st.expander("📋 Product Information Provided", expanded=False):
        if context.get("website_url"):
            st.write(f"🔗 Website: {context['website_url']}")
        if context.get("docs_url"):
            st.write(f"📄 Documentation: {context['docs_url']}")
        if context.get("product_description"):
            st.write(f"📝 Description: {context['product_description'][:200]}...")
    
    # Check if analysis already exists (avoid re-analysis)
    if ('product_analysis' in st.session_state and 
        'generated_content' in st.session_state and 
        'pricing_suggestion' in st.session_state):
        st.success("✅ Analysis already complete! Proceeding to review...")
        if st.button("Review Suggestions →", type="primary"):
            st.session_state.current_step = "review_suggestions"
            st.rerun()
        
        if st.button("← Back to Re-analyze"):
            # Clear existing analysis to force re-analysis
            del st.session_state.product_analysis
            del st.session_state.generated_content
            del st.session_state.pricing_suggestion
            st.rerun()
        return
    
    # Analysis progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Step 1: Analyze product
    status_text.text("🔍 Understanding your product...")
    progress_bar.progress(20)
    
    analysis_prompt = f"""
    Analyze this product information and provide a structured analysis:
    
    Website: {context.get('website_url', 'Not provided')}
    Documentation: {context.get('docs_url', 'Not provided')}
    Description: {context.get('product_description', 'Not provided')}
    
    Provide:
    1. Product Type (SaaS, API, Platform, etc.)
    2. Target Audience
    3. Key Features (list 5-10)
    4. Value Proposition
    5. Use Cases
    6. Competitive Advantages
    
    Format as JSON.
    """
    
    system_prompt = "You are an AWS Marketplace expert analyzing products for listing creation."
    
    with st.spinner("Analyzing product..."):
        model_id = st.session_state.get('selected_model', None)
        analysis = call_bedrock_llm(analysis_prompt, system_prompt, model_id)
    
    if analysis:
        st.session_state.product_analysis = analysis
        progress_bar.progress(40)
        
        # Step 2: Generate listing content
        status_text.text("✍️ Generating listing content...")
        
        content_prompt = f"""
        Based on this product analysis:
        {analysis}
        
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
        - Any Unicode symbols
        
        Format as JSON with these exact keys: product_title, short_description, long_description, highlights (array), search_keywords (array), categories (array)
        """
        
        with st.spinner("Generating content..."):
            model_id = st.session_state.get('selected_model', None)
            content = call_bedrock_llm(content_prompt, system_prompt, model_id)
        
        if content and content.strip():
            st.session_state.generated_content = content
            progress_bar.progress(60)
        else:
            st.error("❌ Failed to generate content. Using fallback template.")
            # Fallback content based on context
            fallback_content = {
                "product_title": context.get('product_description', 'Your Product')[:100],
                "short_description": context.get('product_description', 'Product description')[:200],
                "long_description": context.get('product_description', 'Detailed product description')[:1000],
                "highlights": [
                    "Key feature 1",
                    "Key feature 2",
                    "Key feature 3"
                ],
                "search_keywords": ["saas", "cloud", "software"],
                "categories": ["Application Development"]
            }
            st.session_state.generated_content = json.dumps(fallback_content)
            progress_bar.progress(60)
        
        # Step 3: Suggest pricing model (moved outside the else block)
        status_text.text("💰 Analyzing pricing model...")
        
        pricing_prompt = f"""
        Based on this product:
        {analysis}
        
        Suggest the best AWS Marketplace pricing model:
        
        Options:
        1. "Contract" - One-time fee with allotted units (e.g., buy 100 users for 12 months upfront)
        2. "Usage" - Purely subscription/consumption based (e.g., pay per API call, pay per GB used)
        3. "Contract with Consumption" - One-time fee plus additional charges for excess usage (e.g., buy 100 users upfront + pay extra for additional users beyond that)
        
        Return ONLY a valid JSON object with these exact keys (no other text):
        {{
            "recommended_model": "Contract" | "Usage" | "Contract with Consumption",
            "reasoning": "Brief explanation of why this model fits the product",
            "suggested_dimensions": ["dimension1", "dimension2"],
            "contract_durations": ["12 Months", "24 Months"]
        }}
        
        Choose the model that best fits the product's business model. Return only the JSON, nothing else.
        """
        
        with st.spinner("Analyzing pricing..."):
            model_id = st.session_state.get('selected_model', None)
            pricing = call_bedrock_llm(pricing_prompt, system_prompt, model_id)
        
        if pricing and pricing.strip():
            # Try to extract JSON from the response
            try:
                # Look for JSON in the response
                import re
                json_match = re.search(r'\{.*\}', pricing, re.DOTALL)
                if json_match:
                    pricing_json = json_match.group()
                    # Validate it's valid JSON
                    json.loads(pricing_json)
                    st.session_state.pricing_suggestion = pricing_json
                else:
                    # If no JSON found, store as-is and let review screen handle it
                    st.session_state.pricing_suggestion = pricing
            except (json.JSONDecodeError, AttributeError):
                # Store as-is if we can't parse it
                st.session_state.pricing_suggestion = pricing
        else:
            st.warning("⚠️ Could not generate pricing suggestion. Using default.")
            # Fallback pricing suggestion
            fallback_pricing = {
                "recommended_model": "Contract",
                "reasoning": "Contract-based pricing is recommended for most SaaS products as it provides predictable revenue.",
                "suggested_dimensions": ["Users", "Features"],
                "contract_durations": ["12 Months", "24 Months"]
            }
            st.session_state.pricing_suggestion = json.dumps(fallback_pricing)
        
        progress_bar.progress(100)
        status_text.text("✅ Analysis complete!")
        
        st.success("🎉 Analysis complete! Review the suggestions on the next screen.")
        
        if st.button("Review Suggestions →", type="primary"):
            st.session_state.current_step = "review_suggestions"
            st.rerun()


def review_suggestions_screen():
    """Review and edit AI-generated suggestions"""
    st.title("📝 Review AI-Generated Content")
    
    st.markdown("""
    Review the AI-generated content below. You can edit any field before creating your listing.
    """)
    
    # Parse generated content
    try:
        content = json.loads(st.session_state.generated_content)
        
        # Check if content is empty or has blank values
        if not content or all(not v for v in content.values()):
            raise ValueError("Empty content")
            
    except (json.JSONDecodeError, KeyError, AttributeError, ValueError) as e:
        st.warning("⚠️ AI-generated content was incomplete. Using template. Please fill in your product details.")
        # Fallback if JSON parsing fails or content is empty
        context = st.session_state.get('product_context', {})
        content = {
            "product_title": context.get('product_description', 'Your Product Name')[:72] or "Your Product Name",
            "short_description": context.get('product_description', 'Brief description')[:200] or "Brief description of your product",
            "long_description": context.get('product_description', 'Detailed description')[:1000] or "Detailed description of your product with features and benefits",
            "highlights": ["Key feature 1", "Key feature 2", "Key feature 3"],
            "search_keywords": ["saas", "cloud", "software"],
            "categories": ["Application Development"]
        }
    
    # Truncate product title if AI generated one that's too long
    ai_title = content.get("product_title", "")
    if len(ai_title) > 72:
        st.warning(f"⚠️ AI generated a title that's too long ({len(ai_title)} chars). Truncated to 72 characters.")
        ai_title = ai_title[:69] + "..."  # Truncate and add ellipsis
    
    st.subheader("📦 Product Information")
    
    product_title = st.text_input(
        "Product Title *",
        value=ai_title,
        max_chars=72,
        help="Maximum 72 characters (AWS Marketplace limit)"
    )
    
    # Validate title length
    if product_title and len(product_title) > 72:
        st.error(f"⚠️ Product title is too long ({len(product_title)} chars). Maximum is 72 characters.")
    elif product_title and len(product_title) < 5:
        st.warning(f"⚠️ Product title is too short ({len(product_title)} chars). Minimum is 5 characters.")
    
    logo_s3_url = st.text_input(
        "Logo S3 URL *",
        placeholder="https://your-bucket.s3.amazonaws.com/logo.png",
        help="S3 URL to your product logo (PNG/JPG, min 110x110px, max 5MB)"
    )
    
    short_description = st.text_area(
        "Short Description *",
        value=content.get("short_description", ""),
        max_chars=500,
        height=100
    )
    
    long_description = st.text_area(
        "Long Description *",
        value=content.get("long_description", ""),
        max_chars=5000,
        height=200
    )
    
    st.write("**Highlights (1-3 maximum) ***")
    st.caption("1 mandatory, 2 optional - Key features or benefits")
    highlights = []
    
    # Get AI-generated highlights or use defaults
    ai_highlights = content.get("highlights", ["", "", ""])
    
    # Highlight 1 (mandatory)
    h1 = st.text_input("Highlight 1 *", value=ai_highlights[0] if len(ai_highlights) > 0 else "", max_chars=250, key="highlight_0")
    if h1:
        highlights.append(h1)
    
    # Highlight 2 (optional)
    h2 = st.text_input("Highlight 2 (optional)", value=ai_highlights[1] if len(ai_highlights) > 1 else "", max_chars=250, key="highlight_1")
    if h2:
        highlights.append(h2)
    
    # Highlight 3 (optional)
    h3 = st.text_input("Highlight 3 (optional)", value=ai_highlights[2] if len(ai_highlights) > 2 else "", max_chars=250, key="highlight_2")
    if h3:
        highlights.append(h3)
    
    col1, col2 = st.columns(2)
    
    # Complete AWS Marketplace categories list
    all_categories = [
        # Infrastructure Software
        "Backup & Recovery", "Data Analytics", "High Performance Computing", "Migration",
        "Network Infrastructure", "Operating Systems", "Security", "Storage",
        # DevOps
        "Agile Lifecycle Management", "Application Development", "Application Servers",
        "Application Stacks", "Continuous Integration & Continuous Delivery",
        "Infrastructure as Code", "Issues & Bug Tracking", "Monitoring", "Log Analysis",
        "Source Control", "Testing",
        # Business Applications
        "Blockchain", "Collaboration & Productivity", "Contact Center", "Content Management",
        "CRM", "eCommerce", "eLearning", "Human Resources", "IT Business Management",
        "Business Intelligence", "Project Management",
        # Machine Learning
        "ML Solutions", "Data Labeling Services", "Computer Vision",
        "Natural Language Processing", "Speech Recognition", "Text", "Image", "Video",
        "Audio", "Structured",
        # IoT
        "IoT Analytics", "IoT Applications", "Device Connectivity", "Device Management",
        "Device Security", "Industrial IoT", "Smart Home & City",
        # Professional Services
        "Assessments", "Implementation", "Managed Services", "Premium Support", "Training",
        # Desktop Applications
        "Desktop Applications", "AP and Billing", "Application and the Web", "Development",
        "CAD and CAM", "GIS and Mapping", "Illustration and Design", "Media and Encoding",
        "Productivity and Collaboration", "Security/Storage/Archiving", "Utilities",
        # Industries
        "Education & Research", "Financial Services", "Healthcare & Life Sciences",
        "Media & Entertainment", "Industrial", "Energy"
    ]
    
    with col1:
        # Use AI suggestions if available, otherwise show all categories
        ai_categories = content.get("categories", [])
        default_categories = [cat for cat in ai_categories if cat in all_categories][:3]
        
        categories = st.multiselect(
            "Categories (1-3) *",
            options=sorted(all_categories),
            default=default_categories,
            max_selections=3,
            help="AI suggested categories are pre-selected. You can change them."
        )
    
    with col2:
        keywords_str = ", ".join(content.get("search_keywords", []))
        keywords_input = st.text_input(
            "Search Keywords *",
            value=keywords_str,
            help="Comma-separated"
        )
        keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
    
    st.divider()
    
    # Support information
    st.subheader("📞 Support Information")
    
    col1, col2 = st.columns(2)
    with col1:
        support_email = st.text_input("Support Email *", placeholder="support@example.com")
    with col2:
        fulfillment_url = st.text_input("Fulfillment URL *", placeholder="https://yourapp.com/signup")
    
    support_description = st.text_area(
        "Support Description *",
        placeholder="Describe your support offerings...",
        max_chars=2000
    )
    
    st.divider()
    
    # Pricing review
    st.subheader("💰 Pricing Configuration")
    
    # Parse pricing suggestion
    pricing_suggestion = {}
    recommended_model_display = "Contract"
    
    if 'pricing_suggestion' in st.session_state:
        try:
            # Try to parse as JSON if it's a string
            if isinstance(st.session_state.pricing_suggestion, str):
                pricing_suggestion = json.loads(st.session_state.pricing_suggestion)
            else:
                pricing_suggestion = st.session_state.pricing_suggestion
            
            recommended_model = pricing_suggestion.get('recommended_model', 'Contract')
            
            # Show AI recommendation
            st.info(f"💡 **AI Recommendation:** {recommended_model}")
            if pricing_suggestion.get('reasoning'):
                st.write(pricing_suggestion.get('reasoning'))
            
            # Map AI recommendation to dropdown options
            model_mapping = {
                "Contract": "Contract",
                "Usage": "Usage",
                "Contract with Consumption": "Contract with Consumption",
                "contract": "Contract",
                "usage": "Usage",
                "contract_consumption": "Contract with Consumption",
                "hybrid": "Contract with Consumption"
            }
            recommended_model_display = model_mapping.get(recommended_model, "Contract")
            
        except (json.JSONDecodeError, KeyError, AttributeError, TypeError) as e:
            # Show debug info in expander
            with st.expander("🔍 Debug: Pricing Suggestion Issue"):
                st.error(f"Error parsing pricing suggestion: {str(e)}")
                st.write("Raw pricing suggestion:")
                st.code(str(st.session_state.get('pricing_suggestion', 'None')))
            pricing_suggestion = {}
            recommended_model_display = "Contract"
    else:
        st.warning("⚠️ No pricing suggestion found. Using default Contract model.")
    
    # Pricing model options (including hybrid)
    pricing_options = ["Contract", "Usage", "Contract with Consumption"]
    
    default_index = pricing_options.index(recommended_model_display) if recommended_model_display in pricing_options else 0
    
    pricing_model = st.selectbox(
        "Pricing Model *",
        options=pricing_options,
        index=default_index,
        help="AI recommended model is pre-selected. You can change it if needed."
    )
    
    # Show pricing model explanation
    if pricing_model == "Usage":
        st.info("💡 **Usage-based**: Customers pay for what they use (metered dimensions)")
    elif pricing_model == "Contract":
        st.info("💡 **Contract-based**: Customers pay upfront for entitled dimensions")
    else:  # Contract with Consumption
        st.info("💡 **Contract with Consumption**: Customers commit to a contract with entitled dimensions, plus pay for additional usage beyond their entitlement (metered dimensions)")
    
    st.write("**Pricing Dimensions ***")
    st.caption("Define what customers will be charged for")
    
    # Show AI suggested dimensions
    if pricing_suggestion and 'suggested_dimensions' in pricing_suggestion:
        suggested_dims = pricing_suggestion.get('suggested_dimensions', [])
        if suggested_dims:
            st.info(f"💡 **AI Suggested Dimensions:** {', '.join(suggested_dims)}")
    
    # Initialize dimensions in session state
    if 'dimensions' not in st.session_state:
        st.session_state.dimensions = []
    
    # Dimension type based on pricing model
    if pricing_model == "Usage":
        dim_type = "Metered"
        allow_type_selection = False
    elif pricing_model == "Contract":
        dim_type = "Entitled"
        allow_type_selection = False
    else:  # Contract with Consumption
        dim_type = "Entitled"  # Default for hybrid
        allow_type_selection = True
        st.info("ℹ️ For hybrid pricing, add both **Entitled** dimensions (included in contract) and **Metered** dimensions (pay-per-use overages)")
    
    # Add dimension
    with st.expander("➕ Add Dimension", expanded=len(st.session_state.dimensions) == 0):
        dim_name = st.text_input("Dimension Name", placeholder="e.g., Active Users", key="dim_name")
        dim_key = st.text_input("Dimension Key", placeholder="e.g., users", key="dim_key")
        dim_description = st.text_input("Description", placeholder="e.g., Number of active users per month", key="dim_desc")
        
        # For hybrid pricing, allow selecting dimension type
        if allow_type_selection:
            selected_dim_type = st.radio(
                "Dimension Type",
                options=["Entitled", "Metered"],
                help="Entitled: Included in contract. Metered: Pay-per-use overages.",
                key="dim_type_select"
            )
        else:
            selected_dim_type = dim_type
        
        if st.button("Add Dimension"):
            if dim_name and dim_key and dim_description:
                st.session_state.dimensions.append({
                    "name": dim_name,
                    "key": dim_key,
                    "description": dim_description,
                    "type": selected_dim_type
                })
                st.rerun()
    
    # Show added dimensions
    if st.session_state.dimensions:
        st.write(f"**Added Dimensions ({dim_type}):**")
        for i, dim in enumerate(st.session_state.dimensions):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"{i+1}. {dim['name']} ({dim['key']}) - {dim['type']}")
            with col2:
                if st.button("Remove", key=f"remove_{i}"):
                    st.session_state.dimensions.pop(i)
                    st.rerun()
    
    all_dimensions = st.session_state.dimensions
    
    st.divider()
    
    # Contract Durations (for Contract and hybrid pricing)
    if pricing_model in ["Contract", "Contract with Consumption"]:
        st.subheader("📅 Contract Durations")
        st.caption("Select which contract lengths to offer")
        
        contract_durations = st.multiselect(
            "Available Contract Durations *",
            options=["1 Month", "3 Months", "6 Months", "12 Months", "24 Months", "36 Months"],
            default=["12 Months"],
            help="AI recommends 12 and 24 months for most SaaS products"
        )
        
        st.subheader("🛒 Purchasing Options")
        purchasing_option = st.radio(
            "How can customers purchase dimensions?",
            options=[
                "Multiple dimensions per contract",
                "Single dimension per contract"
            ],
            index=0,
            help="AI recommends allowing multiple dimensions for flexibility"
        )
    else:
        contract_durations = []
        purchasing_option = "Multiple dimensions per contract"
    
    st.divider()
    
    # Refund Policy
    st.subheader("↩️ Refund Policy")
    st.caption("AI-generated template - please review and customize")
    
    # AI-generated refund policy template
    refund_template = f"""We offer a 30-day money-back guarantee for {product_title}. If you're not satisfied with the product, please contact {support_email} within 30 days of purchase to request a full refund. Refunds are processed within 5-7 business days to the original payment method."""
    
    refund_policy = st.text_area(
        "Refund Policy *",
        value=refund_template,
        max_chars=5000,
        height=150,
        help="50-5000 characters - Edit the AI-generated template as needed"
    )
    
    st.divider()
    
    # EULA Configuration
    st.subheader("📄 EULA Configuration")
    st.caption("AI recommends SCMP for most SaaS products")
    
    eula_type = st.radio(
        "EULA Type *",
        options=["SCMP (Standard Contract for AWS Marketplace)", "Custom EULA"],
        index=0,
        help="SCMP is pre-approved by AWS and recommended for most products"
    )
    
    custom_eula_url = None
    if eula_type == "Custom EULA":
        custom_eula_url = st.text_input(
            "Custom EULA S3 URL *",
            placeholder="https://your-bucket.s3.amazonaws.com/eula.pdf",
            help="S3 URL to your custom EULA PDF file"
        )
    
    st.divider()
    
    # Geographic Availability
    st.subheader("🌍 Geographic Availability")
    st.caption("AI recommends worldwide availability for most products")
    
    availability_type = st.radio(
        "Where should your offer be available? *",
        options=[
            "All countries (worldwide)",
            "All countries except specific ones",
            "Only specific countries"
        ],
        index=0,
        help="Most SaaS products are available worldwide"
    )
    
    excluded_countries = []
    allowed_countries = []
    
    if availability_type == "All countries except specific ones":
        excluded_input = st.text_input(
            "Excluded Country Codes",
            placeholder="US, GB, DE (comma-separated ISO codes)",
            help="ISO 3166-1 alpha-2 country codes to exclude"
        )
        if excluded_input:
            excluded_countries = [c.strip().upper() for c in excluded_input.split(",")]
    
    elif availability_type == "Only specific countries":
        allowed_input = st.text_input(
            "Allowed Country Codes *",
            placeholder="US, GB, DE (comma-separated ISO codes)",
            help="ISO 3166-1 alpha-2 country codes to allow"
        )
        if allowed_input:
            allowed_countries = [c.strip().upper() for c in allowed_input.split(",")]
    
    st.divider()
    
    # Account Allowlist (Optional)
    st.subheader("🔐 Account Allowlist (Optional)")
    st.caption("AI recommends public offer for maximum reach")
    
    offer_type = st.radio(
        "Offer Type",
        options=["Public Offer (Recommended)", "Private Offer (Specific AWS Accounts)"],
        index=0,
        help="Public offers are visible to all AWS Marketplace customers"
    )
    
    buyer_accounts = []
    if offer_type == "Private Offer (Specific AWS Accounts)":
        accounts_input = st.text_area(
            "AWS Account IDs",
            placeholder="123456789012, 987654321098 (comma-separated 12-digit account IDs)",
            help="Enter AWS account IDs that can access this offer"
        )
        if accounts_input:
            buyer_accounts = [a.strip() for a in accounts_input.split(",") if a.strip()]
    
    st.divider()
    
    # Auto-publish to Limited option
    st.subheader("🚀 Publishing Options")
    
    auto_publish = st.checkbox(
        "Automatically publish to Limited stage after creation",
        value=True,
        help="Publishes product and offer to Limited stage for testing. You can test with your AWS account immediately."
    )
    
    if auto_publish:
        st.info("✅ Your listing will be published to Limited stage automatically. You can test it immediately with your AWS account.")
        
        # Offer information (required for Limited)
        col_a, col_b = st.columns(2)
        with col_a:
            offer_name = st.text_input(
                "Offer Name",
                value=product_title,
                help="Name for your offer (defaults to product title)"
            )
        with col_b:
            offer_description = st.text_input(
                "Offer Description",
                value=short_description[:200] if len(short_description) <= 200 else short_description[:197] + "...",
                help="Brief description of your offer"
            )
        
        # Optional: Buyer accounts for Limited testing
        with st.expander("🔐 Add Buyer Accounts for Limited Testing (Optional)"):
            st.caption("Add AWS account IDs that can access your Limited listing for testing")
            buyer_accounts_limited = st.text_area(
                "AWS Account IDs",
                placeholder="123456789012, 987654321098 (comma-separated)",
                help="Leave empty to test with only your account"
            )
            buyer_accounts_for_limited = []
            if buyer_accounts_limited:
                buyer_accounts_for_limited = [a.strip() for a in buyer_accounts_limited.split(",") if a.strip()]
    else:
        st.info("ℹ️ Your listing will be created in Draft state. You'll need to publish manually through AWS Marketplace Management Portal.")
        offer_name = product_title
        offer_description = short_description
        buyer_accounts_for_limited = []
    
    st.divider()
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("← Back"):
            st.session_state.current_step = "analyze_product"
            st.rerun()
    
    with col3:
        if st.button("Create Listing 🚀", type="primary", use_container_width=True):
            # Validate product title length (AWS limit)
            if len(product_title) > 72:
                st.error(f"❌ Product title is too long ({len(product_title)} characters). Maximum is 72 characters.")
                return
            
            if len(product_title) < 5:
                st.error(f"❌ Product title is too short ({len(product_title)} characters). Minimum is 5 characters.")
                return
            
            # Validate required fields
            if not all([product_title, logo_s3_url, short_description, long_description, highlights, 
                       categories, keywords, support_email, fulfillment_url, support_description,
                       refund_policy]):
                st.error("Please fill in all required fields")
                return
            
            # Validate logo URL format
            if not logo_s3_url.startswith("https://") or ".s3" not in logo_s3_url:
                st.error("Logo S3 URL must be a valid HTTPS S3 URL")
                return
            
            # Validate dimensions
            if not all_dimensions or len(all_dimensions) == 0:
                st.error("Please add at least one pricing dimension")
                return
            
            # Validate contract durations for contract and hybrid pricing
            if pricing_model in ["Contract", "Contract with Consumption"] and not contract_durations:
                st.error("Please select at least one contract duration")
                return
            
            # Validate hybrid pricing has both dimension types
            if pricing_model == "Contract with Consumption":
                dim_types = set(dim["type"] for dim in all_dimensions)
                if "Entitled" not in dim_types or "Metered" not in dim_types:
                    st.error("Contract with Consumption requires at least one Entitled dimension and one Metered dimension")
                    return
            
            # Validate custom EULA URL if custom chosen
            if eula_type == "Custom EULA" and not custom_eula_url:
                st.error("Please provide Custom EULA S3 URL")
                return
            
            # Validate country codes for restricted availability
            if availability_type == "Only specific countries" and not allowed_countries:
                st.error("Please provide at least one allowed country code")
                return
            
            # Map pricing model to API format
            # API only accepts: "Usage", "Contract", or "Free"
            # "Contract with Consumption" uses "Contract" with both Entitled and Metered dimensions
            if pricing_model == "Usage":
                api_pricing_model = "Usage"
            else:  # Contract or Contract with Consumption
                api_pricing_model = "Contract"
            
            # Sanitize text fields to remove unsupported characters
            sanitized_product_title = sanitize_text_for_marketplace(product_title)
            sanitized_short_description = sanitize_text_for_marketplace(short_description)
            sanitized_long_description = sanitize_text_for_marketplace(long_description)
            sanitized_highlights = [sanitize_text_for_marketplace(h) for h in highlights]
            sanitized_support_description = sanitize_text_for_marketplace(support_description)
            sanitized_refund_policy = sanitize_text_for_marketplace(refund_policy)
            
            # Check if any sanitization occurred
            sanitization_occurred = (
                sanitized_product_title != product_title or
                sanitized_short_description != short_description or
                sanitized_long_description != long_description or
                any(sanitized_highlights[i] != highlights[i] for i in range(len(highlights))) or
                sanitized_support_description != support_description or
                sanitized_refund_policy != refund_policy
            )
            
            if sanitization_occurred:
                st.info("ℹ️ Special characters (like • – " ") were converted to ASCII equivalents for AWS Marketplace compatibility.")
            
            # Store all data and proceed to creation
            listing_data = {
                "product_title": sanitized_product_title,
                "logo_s3_url": logo_s3_url,
                "short_description": sanitized_short_description,
                "long_description": sanitized_long_description,
                "highlights": sanitized_highlights,
                "categories": categories,
                "search_keywords": keywords,
                "support_email": support_email,
                "fulfillment_url": fulfillment_url,
                "support_description": sanitized_support_description,
                "pricing_model": api_pricing_model,
                "ui_pricing_model": pricing_model,  # Keep original for display
                "dimensions": all_dimensions,
                "contract_durations": contract_durations,
                "purchasing_option": purchasing_option,
                "refund_policy": sanitized_refund_policy,
                "eula_type": "scmp" if "SCMP" in eula_type else "custom",
                "custom_eula_url": custom_eula_url,
                "availability_type": availability_type,
                "excluded_countries": excluded_countries,
                "allowed_countries": allowed_countries,
                "buyer_accounts": buyer_accounts,
                "auto_publish_to_limited": auto_publish,
                "offer_name": offer_name,
                "offer_description": offer_description,
                "buyer_accounts_for_limited": buyer_accounts_for_limited
            }
            
            st.session_state.listing_data = listing_data
            st.session_state.current_step = "create_listing"
            st.rerun()


def chat_mode_screen():
    """Interactive chat with the Strands agent"""
    st.title("💬 Chat with AWS Marketplace Agent")
    
    strands_agent = st.session_state.strands_agent
    
    if not strands_agent:
        st.error("❌ Chat mode is not available. Advanced agent features are disabled.")
        st.info("💡 You can still use the guided creation workflow.")
        if st.button("← Back to Guided Creation"):
            st.session_state.current_step = "welcome"
            st.rerun()
        return
    
    # Show current status
    status = strands_agent.get_workflow_status()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Stage", f"{status['current_stage']}/8")
    with col2:
        st.metric("Progress", f"{status['progress']}%")
    with col3:
        st.metric("Phase", status['phase'].replace('_', ' ').title())
    
    if status['listing_complete']:
        st.success("✅ Limited listing creation complete! Ready for AWS integration.")
        if status['product_id']:
            st.info(f"🆔 Product ID: {status['product_id']}")
        if status['offer_id']:
            st.info(f"🆔 Offer ID: {status['offer_id']}")
    else:
        st.info(f"📝 Currently in: {status['stage_name']}")
    
    st.divider()
    
    # Chat interface
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about your marketplace listing..."):
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                if strands_agent:
                    response = strands_agent.process_message(prompt)
                else:
                    response = "Sorry, the advanced chat agent is not available. Please use the guided creation workflow."
                st.write(response)
        
        # Add assistant response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": response})
    
    # Quick actions
    st.divider()
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 Check Status"):
            if strands_agent:
                response = strands_agent.process_message("What's my current status?")
                st.session_state.chat_history.append({"role": "user", "content": "What's my current status?"})
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()
            else:
                st.error("Chat agent not available")
    
    with col2:
        if st.button("🚀 Deploy Integration") and status['listing_complete']:
            st.session_state.show_aws_form = True
            st.rerun()
    
    with col3:
        if st.button("⚙️ Execute Workflow") and status['listing_complete']:
            st.session_state.show_workflow_form = True
            st.rerun()
    
    # AWS Integration Form
    if st.session_state.get('show_aws_form'):
        with st.form("aws_integration_form"):
            st.subheader("🔧 Deploy AWS Integration")
            aws_access_key = st.text_input("AWS Access Key", type="password")
            aws_secret_key = st.text_input("AWS Secret Key", type="password")
            aws_session_token = st.text_input("AWS Session Token (optional)", type="password")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("🚀 Deploy", type="primary"):
                    if aws_access_key and aws_secret_key:
                        deploy_message = f"Deploy AWS integration with credentials: Access Key: {aws_access_key[:8]}..., Secret Key: {aws_secret_key[:8]}..."
                        if aws_session_token:
                            deploy_message += f", Session Token: {aws_session_token[:8]}..."
                        
                        st.session_state.chat_history.append({"role": "user", "content": deploy_message})
                        
                        with st.spinner("Deploying..."):
                            if strands_agent:
                                response = strands_agent.process_message(deploy_message)
                            else:
                                response = "Chat agent not available for deployment."
                        
                        st.session_state.chat_history.append({"role": "assistant", "content": response})
                        st.session_state.show_aws_form = False
                        st.rerun()
                    else:
                        st.error("Please provide AWS credentials")
            
            with col2:
                if st.form_submit_button("Cancel"):
                    st.session_state.show_aws_form = False
                    st.rerun()
    
    # Workflow Execution Form
    if st.session_state.get('show_workflow_form'):
        with st.form("workflow_form"):
            st.subheader("⚡ Execute Marketplace Workflow")
            aws_access_key = st.text_input("AWS Access Key", type="password")
            aws_secret_key = st.text_input("AWS Secret Key", type="password")
            aws_session_token = st.text_input("AWS Session Token (optional)", type="password")
            lambda_function = st.text_input("Lambda Function Name (optional)")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("⚡ Execute", type="primary"):
                    if aws_access_key and aws_secret_key:
                        workflow_message = f"Execute marketplace workflow with: Access Key: {aws_access_key[:8]}..., Secret Key: {aws_secret_key[:8]}..."
                        if aws_session_token:
                            workflow_message += f", Session Token: {aws_session_token[:8]}..."
                        if lambda_function:
                            workflow_message += f", Lambda Function: {lambda_function}"
                        
                        st.session_state.chat_history.append({"role": "user", "content": workflow_message})
                        
                        with st.spinner("Executing workflow..."):
                            if strands_agent:
                                response = strands_agent.process_message(workflow_message)
                            else:
                                response = "Chat agent not available for workflow execution."
                        
                        st.session_state.chat_history.append({"role": "assistant", "content": response})
                        st.session_state.show_workflow_form = False
                        st.rerun()
                    else:
                        st.error("Please provide AWS credentials")
            
            with col2:
                if st.form_submit_button("Cancel"):
                    st.session_state.show_workflow_form = False
                    st.rerun()
    
    # Navigation
    st.divider()
    if st.button("← Back to Guided Creation"):
        st.session_state.current_step = "welcome"
        st.rerun()


def create_listing_screen():
    """Create the listing using the orchestrator"""
    st.title("🚀 Creating Your Listing...")
    
    # Debug info
    with st.expander("🔍 Debug Info", expanded=False):
        st.write(f"Current step: {st.session_state.current_step}")
        st.write(f"Orchestrator available: {st.session_state.orchestrator is not None}")
        if st.session_state.orchestrator:
            st.write(f"Current stage: {st.session_state.orchestrator.current_stage}")
        st.write(f"Listing data keys: {list(st.session_state.listing_data.keys()) if 'listing_data' in st.session_state else 'None'}")
    
    if 'listing_data' not in st.session_state:
        st.error("❌ No listing data found. Please go back and complete the form.")
        if st.button("← Back to Review"):
            st.session_state.current_step = "review_suggestions"
            st.rerun()
        return
    
    if 'aws_credentials' not in st.session_state or not st.session_state.credentials_validated:
        st.error("❌ No AWS credentials found. Please provide credentials first.")
        if st.button("← Back to Credentials"):
            st.session_state.current_step = "credentials"
            st.rerun()
        return
    
    listing_data = st.session_state.listing_data
    orchestrator = st.session_state.orchestrator
    
    if not orchestrator:
        st.error("❌ Orchestrator not available. Please restart the app.")
        return
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    error_container = st.container()
    
    # Add cancel and test mode options
    col1, col2 = st.columns(2)
    with col1:
        if st.button("❌ Cancel Creation"):
            st.session_state.current_step = "review_suggestions"
            st.rerun()
    with col2:
        test_mode = st.checkbox("🧪 Test Mode (Skip AWS API calls)", 
                               value=st.session_state.get('force_test_mode', False),
                               help="For debugging - simulates successful API responses")
        if st.session_state.get('force_test_mode'):
            st.warning("⚠️ Test mode enabled due to API errors")
    
    # Stage 1: Product Information
    status_text.text("📦 Creating product...")
    progress_bar.progress(10)
    
    # Show what we're about to do
    credentials = st.session_state.aws_credentials
    st.info(f"📝 Creating product: {listing_data['product_title']}")
    st.info(f"🌍 Using AWS Account: {credentials['account_id']} in {credentials['region']}")
    
    # Set Stage 1 data
    print(f"[DEBUG] Starting Stage 1. Current stage: {orchestrator.current_stage}")
    print(f"[DEBUG] Current agent: {orchestrator.get_current_agent().stage_name}")
    
    # Ensure we're on the correct stage (Stage 1 = PRODUCT_INFO)
    if orchestrator.current_stage != WorkflowStage.PRODUCT_INFO:
        print(f"[DEBUG] WARNING: Expected Stage 1 (PRODUCT_INFO) but on {orchestrator.current_stage}")
        print(f"[DEBUG] Forcing stage to PRODUCT_INFO")
        orchestrator.current_stage = WorkflowStage.PRODUCT_INFO
        print(f"[DEBUG] Stage corrected to: {orchestrator.current_stage}")
        print(f"[DEBUG] Agent after correction: {orchestrator.get_current_agent().stage_name}")
    
    orchestrator.set_stage_data("product_title", listing_data["product_title"])
    orchestrator.set_stage_data("logo_s3_url", listing_data["logo_s3_url"])
    orchestrator.set_stage_data("short_description", listing_data["short_description"])
    orchestrator.set_stage_data("long_description", listing_data["long_description"])
    orchestrator.set_stage_data("highlights", listing_data["highlights"])
    orchestrator.set_stage_data("support_email", listing_data["support_email"])
    orchestrator.set_stage_data("support_description", listing_data["support_description"])
    orchestrator.set_stage_data("categories", listing_data["categories"])
    orchestrator.set_stage_data("search_keywords", listing_data["search_keywords"])
    print(f"[DEBUG] Stage 1 data set. Current agent data: {orchestrator.get_current_agent().stage_data}")
    
    try:
        if test_mode:
            result1 = {"status": "complete", "api_result": {"success": True, "product_id": "prod-test123", "offer_id": "offer-test123"}}
            st.write("🧪 Test mode: Simulated Stage 1 success")
        else:
            # Show what API call we're about to make
            st.info("🔄 Calling AWS Marketplace Catalog API: CreateProduct + CreateOffer")
            with st.expander("🔍 API Call Details", expanded=False):
                st.write(f"Product Title: {listing_data['product_title']}")
                st.write(f"AWS Account: {credentials['account_id']}")
                st.write(f"Region: {credentials['region']}")
            
            result1 = orchestrator.complete_current_stage()
        st.write(f"Stage 1 result: {result1}")
    except Exception as e:
        error_container.error(f"❌ Stage 1 failed: {str(e)}")
        
        # Enhanced error analysis
        error_str = str(e).lower()
        if "accessdenied" in error_str:
            st.error("🚫 **AWS Marketplace Access Denied**")
            st.info("💡 Your AWS credentials need marketplace-catalog permissions")
            st.code("Required IAM Policy:\n{\n  \"Version\": \"2012-10-17\",\n  \"Statement\": [{\n    \"Effect\": \"Allow\",\n    \"Action\": [\"marketplace-catalog:*\"],\n    \"Resource\": \"*\"\n  }]\n}")
        elif "invalidparameter" in error_str or "validationexception" in error_str:
            st.error("📝 **Invalid Parameters**")
            st.info("💡 Check product title, descriptions, and other fields for AWS requirements")
        elif "throttling" in error_str:
            st.error("⏱️ **API Rate Limited**")
            st.info("💡 Wait a few minutes before retrying")
        
        with st.expander("🔍 Full Error Details"):
            st.code(f"Error Type: {type(e).__name__}")
            st.code(f"Error Message: {str(e)}")
            st.code(f"AWS Account: {credentials.get('account_id', 'Unknown')}")
            st.code(f"Region: {credentials.get('region', 'Unknown')}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Retry Stage 1"):
                st.rerun()
        with col2:
            if st.button("🧪 Enable Test Mode"):
                st.session_state.force_test_mode = True
                st.rerun()
        return
    
    if result1.get("status") != "complete":
        error_container.error(f"Failed to create product: {result1.get('message')}")
        st.write(f"Debug - Stage 1 full result: {result1}")
        return
    
    progress_bar.progress(25)
    
    # Stage 2: Fulfillment
    status_text.text("🔗 Adding fulfillment options...")
    print(f"[DEBUG] Starting Stage 2. Current stage: {orchestrator.current_stage}")
    print(f"[DEBUG] Current agent: {orchestrator.get_current_agent().stage_name}")
    
    # Ensure we're on the correct stage (Stage 2 = FULFILLMENT)
    if orchestrator.current_stage != WorkflowStage.FULFILLMENT:
        print(f"[DEBUG] WARNING: Expected Stage 2 (FULFILLMENT) but on {orchestrator.current_stage}")
        print(f"[DEBUG] Forcing stage to FULFILLMENT")
        orchestrator.current_stage = WorkflowStage.FULFILLMENT
        print(f"[DEBUG] Stage corrected to: {orchestrator.current_stage}")
        print(f"[DEBUG] Agent after correction: {orchestrator.get_current_agent().stage_name}")
    
    orchestrator.set_stage_data("fulfillment_url", listing_data["fulfillment_url"])
    orchestrator.set_stage_data("quick_launch_enabled", False)
    
    try:
        if test_mode:
            result2 = {"status": "complete", "api_result": {"success": True}}
            st.write("🧪 Test mode: Simulated Stage 2 success")
        else:
            st.info("🔄 Calling AWS API: AddDeliveryOptions")
            result2 = orchestrator.complete_current_stage()
        st.write(f"Stage 2 result: {result2}")
    except Exception as e:
        error_container.error(f"❌ Stage 2 failed: {str(e)}")
        st.info("💡 **Tip:** Stage 2 adds fulfillment URL to your product")
        if st.button("🧪 Enable Test Mode for Remaining Stages"):
            st.session_state.force_test_mode = True
            st.rerun()
        return
    progress_bar.progress(40)
    
    # Stage 3: Pricing Dimensions
    status_text.text("💰 Configuring pricing...")
    print(f"[DEBUG] Starting Stage 3. Current stage: {orchestrator.current_stage}")
    print(f"[DEBUG] Current agent: {orchestrator.get_current_agent().stage_name}")
    
    # Ensure we're on the correct stage (Stage 3 = PRICING_CONFIG)
    if orchestrator.current_stage != WorkflowStage.PRICING_CONFIG:
        print(f"[DEBUG] WARNING: Expected Stage 3 (PRICING_CONFIG) but on {orchestrator.current_stage}")
        print(f"[DEBUG] Forcing stage to PRICING_CONFIG")
        orchestrator.current_stage = WorkflowStage.PRICING_CONFIG
        print(f"[DEBUG] Stage corrected to: {orchestrator.current_stage}")
        print(f"[DEBUG] Agent after correction: {orchestrator.get_current_agent().stage_name}")
    
    dimensions = listing_data["dimensions"]
    
    # Convert dimensions to API format
    api_dimensions = []
    for dim in dimensions:
        # AWS Marketplace requires specific dimension type combinations:
        # - Entitled: ["Entitled"]
        # - Metered: ["Metered", "ExternallyMetered"] (both required!)
        if dim["type"] == "Metered":
            types = ["Metered", "ExternallyMetered"]
        else:
            types = [dim["type"]]
        
        api_dimensions.append({
            "Key": dim["key"],
            "Name": dim["name"],
            "Description": dim["description"],
            "Types": types,
            "Unit": "Units"
        })
    
    # Set pricing model (API accepts "Usage" or "Contract")
    # For "Contract with Consumption", we use "Contract" with both Entitled and Metered dimensions
    orchestrator.set_stage_data("pricing_model", listing_data["pricing_model"])
    orchestrator.set_stage_data("dimensions", api_dimensions)
    
    try:
        if test_mode:
            result3 = {"status": "complete", "api_result": {"success": True}}
            st.write("🧪 Test mode: Simulated Stage 3 success")
        else:
            st.info("🔄 Calling AWS API: AddDimensions")
            result3 = orchestrator.complete_current_stage()
        st.write(f"Stage 3 result: {result3}")
        if not test_mode:
            st.write(f"Current stage after Stage 3: {orchestrator.current_stage}")
    except Exception as e:
        error_container.error(f"❌ Stage 3 failed: {str(e)}")
        st.info("💡 **Tip:** Stage 3 adds pricing dimensions to your product")
        if st.button("🧪 Enable Test Mode for Remaining Stages"):
            st.session_state.force_test_mode = True
            st.rerun()
        return
    progress_bar.progress(55)
    
    # Stage 4: Price Review
    status_text.text("💵 Applying pricing terms...")
    print(f"[DEBUG] Setting Stage 4 data...")
    print(f"[DEBUG] Current stage before Stage 4: {orchestrator.current_stage}")
    print(f"[DEBUG] Current agent before Stage 4: {orchestrator.get_current_agent().stage_name}")
    
    # Ensure we're on the correct stage (Stage 4 = PRICE_REVIEW)
    if orchestrator.current_stage != WorkflowStage.PRICE_REVIEW:
        print(f"[DEBUG] WARNING: Expected Stage 4 (PRICE_REVIEW) but on {orchestrator.current_stage}")
        print(f"[DEBUG] Forcing stage to PRICE_REVIEW")
        orchestrator.current_stage = WorkflowStage.PRICE_REVIEW
        print(f"[DEBUG] Stage corrected to: {orchestrator.current_stage}")
        print(f"[DEBUG] Agent after correction: {orchestrator.get_current_agent().stage_name}")
    
    # For Usage pricing, these fields are not applicable but required by the agent
    # Set dummy values that won't be used by the API
    if listing_data["pricing_model"] == "Usage":
        orchestrator.set_stage_data("contract_durations", ["12 Months"])  # Dummy value, not used for Usage
        orchestrator.set_stage_data("multiple_dimension_selection", "Allowed")
        orchestrator.set_stage_data("quantity_configuration", "Allowed")
    else:
        # For Contract pricing
        orchestrator.set_stage_data("contract_durations", listing_data.get("contract_durations", ["12 Months"]))
        
        # Set purchasing options based on user selection
        if listing_data.get("purchasing_option") == "Multiple dimensions per contract":
            orchestrator.set_stage_data("multiple_dimension_selection", "Allowed")
            orchestrator.set_stage_data("quantity_configuration", "Allowed")
        else:
            orchestrator.set_stage_data("multiple_dimension_selection", "Disallowed")
            orchestrator.set_stage_data("quantity_configuration", "Disallowed")
    
    print(f"[DEBUG] Stage 4 data set complete. Current agent data: {orchestrator.get_current_agent().stage_data}")
    
    print(f"[DEBUG] About to complete Stage 4...")
    current_agent = orchestrator.get_current_agent()
    print(f"[DEBUG] Stage 4 agent: {current_agent}")
    print(f"[DEBUG] Stage 4 required fields: {current_agent.get_required_fields()}")
    print(f"[DEBUG] Stage 4 collected data: {current_agent.stage_data}")
    print(f"[DEBUG] Stage 4 is complete: {orchestrator.check_stage_completion()}")
    
    # Check what's missing
    missing_fields = [f for f in current_agent.get_required_fields() if f not in current_agent.stage_data or not current_agent.stage_data[f]]
    if missing_fields:
        print(f"[DEBUG] Missing required fields: {missing_fields}")
    
    # Check validation errors
    validation_errors = current_agent.validate_all_fields(current_agent.stage_data)
    if validation_errors:
        print(f"[DEBUG] Validation errors: {validation_errors}")
    try:
        if test_mode:
            result4 = {"status": "complete", "api_result": {"success": True}}
            st.write("🧪 Test mode: Simulated Stage 4 success")
        else:
            st.info("🔄 Calling AWS API: UpdatePricingTerms")
            result4 = orchestrator.complete_current_stage()
        st.write(f"Stage 4 result: {result4}")
        print(f"[DEBUG] Stage 4 completed. Current stage now: {orchestrator.current_stage}")
    except Exception as e:
        error_container.error(f"❌ Stage 4 failed: {str(e)}")
        st.info("💡 **Tip:** Stage 4 configures pricing terms on your offer")
        
        # Enhanced debug info for Stage 4
        print(f"[DEBUG] Stage 4 exception: {str(e)}")
        print(f"[DEBUG] Exception type: {type(e).__name__}")
        
        # Show debug info for Stage 4 failure
        with st.expander("🔍 Stage 4 Debug Info", expanded=True):
            current_agent = orchestrator.get_current_agent()
            st.write(f"**Current Stage:** {orchestrator.current_stage}")
            st.write(f"**Agent:** {current_agent.stage_name}")
            st.write(f"**Required Fields:** {current_agent.get_required_fields()}")
            st.write(f"**Collected Data:** {current_agent.stage_data}")
            
            missing_fields = [f for f in current_agent.get_required_fields() if f not in current_agent.stage_data or not current_agent.stage_data[f]]
            if missing_fields:
                st.error(f"**Missing Required Fields:** {missing_fields}")
            
            validation_errors = current_agent.validate_all_fields(current_agent.stage_data)
            if validation_errors:
                st.error(f"**Validation Errors:** {validation_errors}")
        
        if st.button("🧪 Enable Test Mode for Remaining Stages"):
            st.session_state.force_test_mode = True
            st.rerun()
        return
    progress_bar.progress(70)
    
    # Stage 5: Refund Policy
    status_text.text("↩️ Setting refund policy...")
    print(f"[DEBUG] Starting Stage 5. Current stage: {orchestrator.current_stage}")
    print(f"[DEBUG] Current agent: {orchestrator.get_current_agent().stage_name}")
    
    # Ensure we're on the correct stage (Stage 5 = REFUND_POLICY)
    if orchestrator.current_stage != WorkflowStage.REFUND_POLICY:
        print(f"[DEBUG] WARNING: Expected Stage 5 (REFUND_POLICY) but on {orchestrator.current_stage}")
        print(f"[DEBUG] Forcing stage to REFUND_POLICY")
        orchestrator.current_stage = WorkflowStage.REFUND_POLICY
        print(f"[DEBUG] Stage corrected to: {orchestrator.current_stage}")
        print(f"[DEBUG] Agent after correction: {orchestrator.get_current_agent().stage_name}")
    
    orchestrator.set_stage_data("refund_policy", listing_data["refund_policy"])
    
    try:
        if test_mode:
            result5 = {"status": "complete", "api_result": {"success": True}}
            st.write("🧪 Test mode: Simulated Stage 5 success")
        else:
            st.info("🔄 Calling AWS API: UpdateSupportTerms")
            result5 = orchestrator.complete_current_stage()
        st.write(f"Stage 5 result: {result5}")
    except Exception as e:
        error_container.error(f"❌ Stage 5 failed: {str(e)}")
        st.info("💡 **Tip:** Stage 5 adds refund policy to your offer")
        if st.button("🧪 Enable Test Mode for Remaining Stages"):
            st.session_state.force_test_mode = True
            st.rerun()
        return
    progress_bar.progress(80)
    
    # Stage 6: EULA
    status_text.text("📄 Configuring EULA...")
    print(f"[DEBUG] Starting Stage 6. Current stage: {orchestrator.current_stage}")
    print(f"[DEBUG] Current agent: {orchestrator.get_current_agent().stage_name}")
    
    # Ensure we're on the correct stage (Stage 6 = EULA_CONFIG)
    if orchestrator.current_stage != WorkflowStage.EULA_CONFIG:
        print(f"[DEBUG] WARNING: Expected Stage 6 (EULA_CONFIG) but on {orchestrator.current_stage}")
        print(f"[DEBUG] Forcing stage to EULA_CONFIG")
        orchestrator.current_stage = WorkflowStage.EULA_CONFIG
        print(f"[DEBUG] Stage corrected to: {orchestrator.current_stage}")
        print(f"[DEBUG] Agent after correction: {orchestrator.get_current_agent().stage_name}")
    
    orchestrator.set_stage_data("eula_type", listing_data["eula_type"])
    if listing_data.get("custom_eula_url"):
        orchestrator.set_stage_data("custom_eula_s3_url", listing_data["custom_eula_url"])
    
    try:
        if test_mode:
            result6 = {"status": "complete", "api_result": {"success": True}}
            st.write("🧪 Test mode: Simulated Stage 6 success")
        else:
            st.info("🔄 Calling AWS API: UpdateLegalTerms")
            result6 = orchestrator.complete_current_stage()
        st.write(f"Stage 6 result: {result6}")
    except Exception as e:
        error_container.error(f"❌ Stage 6 failed: {str(e)}")
        st.info("💡 **Tip:** Stage 6 configures EULA (legal terms) on your offer")
        if st.button("🧪 Enable Test Mode for Remaining Stages"):
            st.session_state.force_test_mode = True
            st.rerun()
        return
    progress_bar.progress(90)
    
    # Stage 7: Availability
    status_text.text("🌍 Setting availability...")
    print(f"[DEBUG] Starting Stage 7. Current stage: {orchestrator.current_stage}")
    print(f"[DEBUG] Current agent: {orchestrator.get_current_agent().stage_name}")
    
    # Ensure we're on the correct stage (Stage 7 = OFFER_AVAILABILITY)
    if orchestrator.current_stage != WorkflowStage.OFFER_AVAILABILITY:
        print(f"[DEBUG] WARNING: Expected Stage 7 (OFFER_AVAILABILITY) but on {orchestrator.current_stage}")
        print(f"[DEBUG] Forcing stage to OFFER_AVAILABILITY")
        orchestrator.current_stage = WorkflowStage.OFFER_AVAILABILITY
        print(f"[DEBUG] Stage corrected to: {orchestrator.current_stage}")
        print(f"[DEBUG] Agent after correction: {orchestrator.get_current_agent().stage_name}")
    
    # Map availability type to orchestrator format
    if listing_data["availability_type"] == "All countries (worldwide)":
        orchestrator.set_stage_data("availability_type", "all_countries")
    elif listing_data["availability_type"] == "All countries except specific ones":
        orchestrator.set_stage_data("availability_type", "all_with_exclusions")
        orchestrator.set_stage_data("excluded_countries", listing_data.get("excluded_countries", []))
    else:  # Only specific countries
        orchestrator.set_stage_data("availability_type", "allowlist_only")
        orchestrator.set_stage_data("allowed_countries", listing_data.get("allowed_countries", []))
    
    try:
        if test_mode:
            result7 = {"status": "complete", "api_result": {"success": True}}
            st.write("🧪 Test mode: Simulated Stage 7 success")
        else:
            st.info("🔄 Calling AWS API: UpdateAvailability")
            result7 = orchestrator.complete_current_stage()
        st.write(f"Stage 7 result: {result7}")
    except Exception as e:
        error_container.error(f"❌ Stage 7 failed: {str(e)}")
        st.info("💡 **Tip:** Stage 7 sets geographic availability for your offer")
        if st.button("🧪 Enable Test Mode for Remaining Stages"):
            st.session_state.force_test_mode = True
            st.rerun()
        return
    progress_bar.progress(95)
    
    # Stage 8: Allowlist
    status_text.text("✅ Finalizing...")
    print(f"[DEBUG] Starting Stage 8. Current stage: {orchestrator.current_stage}")
    print(f"[DEBUG] Current agent: {orchestrator.get_current_agent().stage_name}")
    
    # Ensure we're on the correct stage (Stage 8 = ALLOWLIST)
    if orchestrator.current_stage != WorkflowStage.ALLOWLIST:
        print(f"[DEBUG] WARNING: Expected Stage 8 (ALLOWLIST) but on {orchestrator.current_stage}")
        print(f"[DEBUG] Forcing stage to ALLOWLIST")
        orchestrator.current_stage = WorkflowStage.ALLOWLIST
        print(f"[DEBUG] Stage corrected to: {orchestrator.current_stage}")
        print(f"[DEBUG] Agent after correction: {orchestrator.get_current_agent().stage_name}")
    
    buyer_accounts = listing_data.get("buyer_accounts", [])
    if buyer_accounts:
        orchestrator.set_stage_data("allowlist_account_ids", buyer_accounts)
    
    try:
        if test_mode:
            result8 = {"status": "complete", "api_result": {"success": True}}
            st.write("🧪 Test mode: Simulated Stage 8 success")
        else:
            st.info("🔄 Calling AWS API: UpdateTargeting")
            result8 = orchestrator.complete_current_stage()
        st.write(f"Stage 8 result: {result8}")
    except Exception as e:
        error_container.error(f"❌ Stage 8 failed: {str(e)}")
        st.info("💡 **Tip:** Stage 8 configures account targeting (allowlist) for your offer")
        return
    
    progress_bar.progress(95)
    
    # Check if all stages completed successfully
    # Each result has api_result nested inside
    all_stages_successful = all([
        result1.get("api_result", {}).get("success", False),
        result2.get("api_result", {}).get("success", False),
        result3.get("api_result", {}).get("success", False),
        result4.get("api_result", {}).get("success", False),
        result5.get("api_result", {}).get("success", False),
        result6.get("api_result", {}).get("success", False),
        result7.get("api_result", {}).get("success", False),
        result8.get("api_result", {}).get("success", False)
    ])
    
    # Get IDs for display
    api_result = result1.get("api_result", {})
    offer_id = api_result.get("offer_id")
    product_id = api_result.get("product_id")
    
    # Auto-publish to Limited if requested
    published_to_limited = False
    if all_stages_successful and product_id and offer_id and listing_data.get("auto_publish_to_limited"):
        status_text.text("📤 Publishing to Limited stage...")
        progress_bar.progress(97)
        
        tools = st.session_state.orchestrator.listing_tools
        
        # Prepare offer information
        offer_name = listing_data.get("offer_name", listing_data["product_title"])
        offer_description = listing_data.get("offer_description", listing_data["short_description"])
        buyer_accounts = listing_data.get("buyer_accounts_for_limited", [])
        pricing_model = listing_data.get("pricing_model", "Usage")
        
        release_result = tools.release_product_and_offer_to_limited(
            product_id=product_id,
            offer_id=offer_id,
            offer_name=offer_name,
            offer_description=offer_description,
            pricing_model=pricing_model,
            buyer_accounts=buyer_accounts if buyer_accounts else None
        )
        
        if release_result.get("success"):
            # Wait for release changeset to complete
            change_set_id = release_result.get("change_set_id")
            if change_set_id:
                import time
                max_attempts = 15
                for attempt in range(1, max_attempts + 1):
                    time.sleep(3)
                    status_result = tools.get_listing_status(change_set_id)
                    status = status_result.get("status", "UNKNOWN")
                    
                    if status == "SUCCEEDED":
                        published_to_limited = True
                        break
                    elif status == "FAILED":
                        st.warning(f"⚠️ Release to Limited failed: {status_result.get('error', 'Unknown error')}")
                        break
                    elif attempt == max_attempts:
                        st.info("ℹ️ Release to Limited is in progress. Check AWS Marketplace Management Portal for status.")
        else:
            st.warning(f"⚠️ Could not publish to Limited: {release_result.get('error', 'Unknown error')}")
    
    progress_bar.progress(100)
    status_text.text("🎉 Listing creation process completed!")
    
    # Show final status
    if all_stages_successful:
        st.success("✅ All stages completed successfully!")
    else:
        st.warning("⚠️ Some stages had issues but process completed.")
    
    # Show results
    if all_stages_successful:
        st.success("🎉 Your AWS Marketplace listing has been created!")
    else:
        st.warning("⚠️ Listing creation completed with some issues.")
    
    if product_id:
        st.info(f"🆔 **Product ID:** `{product_id}`")
    else:
        st.warning("⚠️ Product ID not found - check AWS Marketplace console")
        
    if offer_id:
        st.info(f"🆔 **Offer ID:** `{offer_id}`")
    else:
        st.warning("⚠️ Offer ID not found - check AWS Marketplace console")
    
    # Always show next steps, regardless of success status
    if all_stages_successful and product_id and offer_id:
        if published_to_limited:
            st.success("📋 **Status:** Limited (published and ready for testing!)")
            
            # Show AWS Integration option
            st.markdown("""
            ### 🎉 Your listing is now LIVE in Limited stage!
            
            Your product and offer have been successfully published to Limited stage:
            - ✅ Product information
            - ✅ Fulfillment configuration
            - ✅ Pricing and dimensions
            - ✅ Support terms
            - ✅ EULA
            - ✅ Geographic availability
            - ✅ **Published to Limited stage**
            
            ---
            
            ### 🚀 Next Phase: AWS Integration & Deployment
            
            Now you can deploy the complete AWS infrastructure for your SaaS integration:
            """)
            
            # AWS Integration Section
            with st.expander("🔧 Deploy AWS Integration Infrastructure", expanded=True):
                st.markdown("""
                Deploy CloudFormation stack with:
                - DynamoDB tables for subscribers and metering
                - Lambda functions for hourly metering processing  
                - API Gateway for customer registration
                - SNS topics for marketplace notifications
                """)
                
                col1, col2 = st.columns(2)
                with col1:
                    aws_access_key = st.text_input("AWS Access Key", type="password")
                    aws_secret_key = st.text_input("AWS Secret Key", type="password")
                with col2:
                    aws_session_token = st.text_input("AWS Session Token (optional)", type="password")
                
                if st.button("🚀 Deploy AWS Integration", type="primary"):
                    if aws_access_key and aws_secret_key:
                        with st.spinner("Deploying AWS infrastructure..."):
                            # Use the integrated Strands agent
                            strands_agent = st.session_state.strands_agent
                            
                            # Deploy integration
                            deploy_message = f"Deploy AWS integration with credentials: Access Key: {aws_access_key[:8]}..., Secret Key: {aws_secret_key[:8]}..."
                            if aws_session_token:
                                deploy_message += f", Session Token: {aws_session_token[:8]}..."
                            
                            response = strands_agent.process_message(deploy_message)
                            st.success("✅ AWS Integration deployment initiated!")
                            st.write(response)
                            
                            # Show next step
                            st.info("💡 **Next:** Execute the complete marketplace workflow (metering, buyer experience, visibility)")
                    else:
                        st.error("Please provide AWS Access Key and Secret Key")
            
            # Workflow Execution Section  
            with st.expander("⚡ Execute Complete Marketplace Workflow"):
                st.markdown("""
                Execute the complete workflow:
                1. Update fulfillment URL in marketplace
                2. Test buyer experience (purchase & registration)
                3. Create metering records
                4. Trigger Lambda processing
                5. Submit public visibility request
                """)
                
                lambda_function = st.text_input("Lambda Function Name (optional)", placeholder="marketplace-metering-hourly-{ProductId}")
                
                if st.button("⚡ Execute Workflow"):
                    if aws_access_key and aws_secret_key:
                        with st.spinner("Executing marketplace workflow..."):
                            strands_agent = st.session_state.strands_agent
                            
                            workflow_message = f"Execute marketplace workflow with: Access Key: {aws_access_key[:8]}..., Secret Key: {aws_secret_key[:8]}..."
                            if aws_session_token:
                                workflow_message += f", Session Token: {aws_session_token[:8]}..."
                            if lambda_function:
                                workflow_message += f", Lambda Function: {lambda_function}"
                            
                            response = strands_agent.process_message(workflow_message)
                            st.success("✅ Marketplace workflow executed!")
                            st.write(response)
                    else:
                        st.error("Please provide AWS credentials above first")
            
            st.markdown("""
            ---
            
            ### 🧪 Test Your Listing
            
            1. **Find your product:**
               - Go to [AWS Marketplace](https://aws.amazon.com/marketplace)
               - Search for your product title
               - Or use the Product ID above
            
            2. **Subscribe and test:**
               - Click "Continue to Subscribe"
               - Accept terms
               - Click "Set Up Your Account"
               - You'll be redirected to your fulfillment URL
            
            3. **Verify integration:**
               - Test the subscription flow
               - Verify fulfillment URL works
               - Check metering/entitlement (if applicable)
            
            ---
            
            ### 📈 Next Steps: Go Public
            
            When you're ready to make your listing public:
            
            1. **Update pricing** from test values ($0.001) to production prices
            2. **Go to** [AWS Marketplace Management Portal](https://aws.amazon.com/marketplace/management/products)
            3. **Find your product** and click "Update visibility"
            4. **Select "Public"** and submit for AWS review
            5. **AWS reviews** your listing (typically 1-2 weeks)
            6. **Once approved**, your listing is publicly available!
            
            ---
            
            ### 📚 Resources
            - [SaaS Product Guidelines](https://docs.aws.amazon.com/marketplace/latest/userguide/saas-guidelines.html)
            - [Testing Your Product](https://docs.aws.amazon.com/marketplace/latest/userguide/saas-prepare.html)
            - [Seller Support](https://aws.amazon.com/marketplace/management/contact-us/)
            """)
        else:
            st.info("📋 **Status:** Draft (ready to publish)")
            st.markdown("""
            ### ✅ Your listing is ready!
            
            The listing has been created in **Draft** state with all configurations complete:
            - ✅ Product information
        - ✅ Fulfillment configuration
        - ✅ Pricing and dimensions
        - ✅ Support terms
        - ✅ EULA
        - ✅ Geographic availability
        
        ---
        
        ### 📋 Next Steps: Publish to Limited Stage
        
        Follow these steps to publish your listing to Limited stage for testing:
        
        #### Step 1: Open AWS Marketplace Management Portal
        1. Go to [AWS Marketplace Management Portal](https://aws.amazon.com/marketplace/management/products)
        2. Sign in with your AWS seller account
        
        #### Step 2: Find Your Product
        1. In the left sidebar, click **"Products"**
        2. Find your product by searching for the Product ID above
        3. Click on the product name to open it
        
        #### Step 3: Add Offer Description (Required)
        1. Navigate to the **"Offers"** tab
        2. Click on your offer
        3. Click **"Edit offer information"**
        4. Add a description (e.g., your product's short description)
        5. Click **"Save"**
        
        #### Step 4: Publish Product to Limited
        1. Go back to the product overview page
        2. Click **"Request changes"** → **"Publish product"**
        3. Select **"Limited"** as the target audience
        4. Review and submit the request
        5. Wait for the changeset to complete (usually 5-10 minutes)
        
        #### Step 5: Publish Offer to Limited
        1. Once the product is in Limited stage, go to the **"Offers"** tab
        2. Click on your offer
        3. Click **"Request changes"** → **"Publish offer"**
        4. Select **"Limited"** as the target audience
        5. Review and submit the request
        
        #### Step 6: Test Your Listing
        - Your listing is now visible to your AWS account
        - Test the subscription flow
        - Verify fulfillment URL integration
        - Check metering/entitlement (if applicable)
        
        #### Step 7: Publish to Public (When Ready)
        1. Update pricing to production values (currently set to $0.001 for testing)
        2. Submit for AWS Marketplace review
        3. Once approved, your listing will be publicly available
        
        ---
        
        ### 📚 Additional Resources
        - [AWS Marketplace Seller Guide](https://docs.aws.amazon.com/marketplace/latest/userguide/what-is-marketplace.html)
        - [SaaS Product Guidelines](https://docs.aws.amazon.com/marketplace/latest/userguide/saas-guidelines.html)
        - [Testing Your SaaS Product](https://docs.aws.amazon.com/marketplace/latest/userguide/saas-prepare.html)
        """)
    else:
        st.warning("⚠️ Some stages may have failed. Please check the logs above.")
        st.markdown("""
        ### Next Steps:
        1. Review any errors in the terminal output
        2. Check your listing in the AWS Marketplace Management Portal
        3. Complete any missing configurations manually
        4. Publish to Limited stage for testing
        """)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create Another Listing"):
            # Reset
            st.session_state.clear()
            st.rerun()
    
    with col2:
        if st.button("💬 Chat with Agent", type="secondary"):
            st.session_state.current_step = "chat_mode"
            st.rerun()


def main():
    """Main app logic"""
    init_session_state()
    
    # Sidebar
    with st.sidebar:
        st.title("🤖 AI-Guided Listing")
        st.divider()
        
        # Model selection
        with st.expander("⚙️ Settings", expanded=False):
            model_choice = st.selectbox(
                "AI Model",
                options=[
                    "Auto (Try all models)",
                    "Claude 3.5 Sonnet v2 (Latest)",
                    "Claude 3.5 Sonnet v1 (Stable)",
                    "Claude 3 Sonnet (Fallback)"
                ],
                index=0,
                help="Select which Claude model to use. Auto will try models in order until one works."
            )
            
            model_map = {
                "Auto (Try all models)": None,
                "Claude 3.5 Sonnet v2 (Latest)": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                "Claude 3.5 Sonnet v1 (Stable)": "anthropic.claude-3-5-sonnet-20240620-v1:0",
                "Claude 3 Sonnet (Fallback)": "anthropic.claude-3-sonnet-20240229-v1:0"
            }
            
            st.session_state.selected_model = model_map[model_choice]
        
        st.divider()
        
        # Show progress
        steps = {
            "credentials": "🔐 Credentials",
            "welcome": "Welcome",
            "gather_context": "Product Info",
            "analyze_product": "AI Analysis",
            "review_suggestions": "Review",
            "create_listing": "Create",
            "chat_mode": "💬 Chat Mode"
        }
        
        current = st.session_state.current_step
        for key, label in steps.items():
            if key == current:
                st.markdown(f"**→ {label}**")
            else:
                st.markdown(f"   {label}")
        
        st.divider()
        
        # Show credential status in sidebar
        if st.session_state.credentials_validated:
            creds = st.session_state.aws_credentials
            st.success(f"✅ AWS: {creds['account_id']}")
        else:
            st.warning("⚠️ Credentials needed")
        
        st.caption("Powered by Amazon Bedrock")
    
    # Main content
    if st.session_state.current_step == "credentials":
        credentials_screen()
    elif st.session_state.current_step == "welcome":
        welcome_screen()
    elif st.session_state.current_step == "gather_context":
        gather_context_screen()
    elif st.session_state.current_step == "analyze_product":
        analyze_product_screen()
    elif st.session_state.current_step == "review_suggestions":
        review_suggestions_screen()
    elif st.session_state.current_step == "create_listing":
        create_listing_screen()
    elif st.session_state.current_step == "chat_mode":
        chat_mode_screen()


if __name__ == "__main__":
    main()
