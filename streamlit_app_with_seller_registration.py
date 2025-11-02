#!/usr/bin/env python3
"""
AI-Guided AWS Marketplace Seller Registration and Listing Creation

This app provides a complete workflow:
1. Seller Registration (NEW)
2. Listing Creation (Existing)

Users can register as AWS Marketplace sellers and then create product listings.
"""

import streamlit as st
from agent.orchestrator import ListingOrchestrator, WorkflowStage
from agent.tools.listing_tools import ListingTools
from agent.tools.seller_registration_tools import SellerRegistrationTools
from agent.sub_agents.seller_registration_agent import SellerRegistrationAgent
import boto3
import json
import re

# Configure page
st.set_page_config(
    page_title="AWS Marketplace Seller Registration & Listing",
    page_icon="🚀",
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
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        cleaned_line = line.encode('ascii', 'ignore').decode('ascii')
        cleaned_line = re.sub(r' +', ' ', cleaned_line)
        cleaned_lines.append(cleaned_line.strip())
    
    text = '\n'.join(cleaned_lines)
    return text.strip()


def init_session_state():
    """Initialize session state"""
    if 'orchestrator' not in st.session_state:
        # Use Strands agent
        from agent.strands_marketplace_agent import StrandsMarketplaceAgent
        strands_agent = StrandsMarketplaceAgent()
        st.session_state.orchestrator = strands_agent.orchestrator
    
    if 'seller_registration_tools' not in st.session_state:
        st.session_state.seller_registration_tools = SellerRegistrationTools()
    
    if 'seller_registration_agent' not in st.session_state:
        st.session_state.seller_registration_agent = SellerRegistrationAgent()
    
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    if 'product_context' not in st.session_state:
        st.session_state.product_context = {}
    
    if 'current_step' not in st.session_state:
        st.session_state.current_step = "welcome"
    
    if 'seller_status' not in st.session_state:
        st.session_state.seller_status = None
    
    if 'registration_data' not in st.session_state:
        st.session_state.registration_data = {}


def call_bedrock_llm(prompt: str, system_prompt: str = None, model_id: str = None) -> str:
    """Call Amazon Bedrock to generate responses"""
    try:
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
                "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                "anthropic.claude-3-5-sonnet-20241022-v2:0",
                "anthropic.claude-3-5-sonnet-20240620-v1:0",
                "anthropic.claude-3-sonnet-20240229-v1:0"
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
        
        raise last_error
    
    except Exception as e:
        st.error(f"Error calling Bedrock: {str(e)}")
        st.info("💡 Tip: Make sure you have requested access to Claude models in the Bedrock console")
        return None


def welcome_screen():
    """Welcome screen with workflow selection"""
    st.title("🚀 AWS Marketplace Seller Registration & Listing Creation")
    
    st.markdown("""
    ### Welcome! Let's get you set up on AWS Marketplace.
    
    This comprehensive workflow will:
    
    **Step 1: Seller Registration** 🏢
    - Check your current seller status
    - Guide you through AWS Marketplace seller registration
    - Handle business profile, tax information, and banking setup
    - Support for US, India, and other countries
    
    **Step 2: Listing Creation** 🛍️
    - Analyze your product documentation
    - Generate all required listing content automatically
    - Select optimal pricing models and dimensions
    - Create and publish your marketplace listing
    
    **Complete end-to-end solution - no AWS Marketplace expertise required!**
    """)
    
    st.divider()
    
    # Check seller status first
    if st.session_state.seller_status is None:
        with st.spinner("Checking your AWS Marketplace seller status..."):
            status = st.session_state.seller_registration_tools.check_seller_status()
            st.session_state.seller_status = status
    
    status = st.session_state.seller_status
    
    if status and status.get("success"):
        seller_status = status.get("seller_status", "UNKNOWN")
        
        if seller_status == "APPROVED":
            st.success("✅ **You're already registered as an AWS Marketplace seller!**")
            st.info("You can proceed directly to creating product listings.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Re-check Seller Status", use_container_width=True):
                    st.session_state.seller_status = None
                    st.rerun()
            
            with col2:
                if st.button("Create Product Listing →", type="primary", use_container_width=True):
                    st.session_state.current_step = "gather_context"
                    st.rerun()
        
        elif seller_status == "PENDING":
            st.warning("⏳ **Your seller registration is under review by AWS**")
            st.info("This typically takes 2-3 business days. You can check the status in your AWS Marketplace Management Console.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Re-check Status", use_container_width=True):
                    st.session_state.seller_status = None
                    st.rerun()
            
            with col2:
                if st.button("View Management Console", use_container_width=True):
                    st.markdown("[Open AWS Marketplace Management Console](https://console.aws.amazon.com/marketplace/management/)")
        
        else:  # NOT_REGISTERED or other status
            st.info("📋 **You need to register as an AWS Marketplace seller first**")
            st.markdown("Don't worry - we'll guide you through the entire process step by step.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Re-check Status", use_container_width=True):
                    st.session_state.seller_status = None
                    st.rerun()
            
            with col2:
                if st.button("Start Seller Registration →", type="primary", use_container_width=True):
                    st.session_state.current_step = "seller_registration"
                    st.rerun()
    
    else:
        st.error("❌ Unable to check seller status. Please check your AWS credentials and try again.")
        if st.button("Retry", type="primary"):
            st.session_state.seller_status = None
            st.rerun()


def seller_registration_screen():
    """Seller registration workflow"""
    st.title("🏢 AWS Marketplace Seller Registration")
    
    st.markdown("""
    Let's get you registered as an AWS Marketplace seller. This process involves:
    
    1. **Business Profile** - Legal business information
    2. **Public Profile** - Customer-facing company profile  
    3. **Tax Information** - Tax forms and identification
    4. **Banking Information** - Payment account setup
    5. **Verification** - AWS review process (2-3 business days)
    6. **Disbursement** - Payment method selection
    """)
    
    # Show current registration status
    agent = st.session_state.seller_registration_agent
    
    with st.expander("📊 Registration Progress", expanded=True):
        workflow_status = st.session_state.seller_registration_tools.get_registration_workflow_status()
        if workflow_status.get("success"):
            progress = workflow_status.get("progress_percentage", 0)
            st.progress(progress / 100)
            st.write(f"**Progress:** {progress}% complete")
            st.write(f"**Current Step:** {workflow_status.get('current_step', 'Unknown').replace('_', ' ').title()}")
            st.write(f"**Next Action:** {workflow_status.get('next_action', 'Continue with registration')}")
        else:
            st.progress(0)
            st.write("**Progress:** Starting registration process")
    
    st.divider()
    
    # Interactive registration form
    st.subheader("📝 Business Information")
    
    # Check if we already have some data
    if not st.session_state.registration_data:
        st.session_state.registration_data = {}
    
    data = st.session_state.registration_data
    
    # Business Information Form
    col1, col2 = st.columns(2)
    
    with col1:
        business_name = st.text_input(
            "Business Name *",
            value=data.get("business_name", ""),
            placeholder="Your legal business name",
            help="Enter the legal name of your business as registered"
        )
        
        business_type = st.selectbox(
            "Business Type *",
            options=["", "Corporation", "LLC", "Partnership", "Sole Proprietorship", "Private Limited Company", "Public Limited Company"],
            index=0 if not data.get("business_type") else ["", "Corporation", "LLC", "Partnership", "Sole Proprietorship", "Private Limited Company", "Public Limited Company"].index(data.get("business_type", "")),
            help="Select your business entity type"
        )
        
        business_email = st.text_input(
            "Business Email *",
            value=data.get("business_email", ""),
            placeholder="contact@yourcompany.com",
            help="Primary business email address"
        )
        
        tax_id = st.text_input(
            "Tax ID *",
            value=data.get("tax_id", ""),
            placeholder="EIN (US), PAN (India), or equivalent",
            help="Tax identification number (EIN for US, PAN for India)"
        )
        
        primary_contact_name = st.text_input(
            "Primary Contact Name *",
            value=data.get("primary_contact_name", ""),
            placeholder="John Doe",
            help="Name of the primary business contact"
        )
    
    with col2:
        business_address = st.text_area(
            "Business Address *",
            value=data.get("business_address", ""),
            placeholder="123 Business St, City, State/Province, Country, ZIP",
            help="Complete business address",
            height=100
        )
        
        business_phone = st.text_input(
            "Business Phone *",
            value=data.get("business_phone", ""),
            placeholder="+1-555-123-4567 or +91-9876543210",
            help="Business phone number with country code"
        )
        
        primary_contact_email = st.text_input(
            "Primary Contact Email *",
            value=data.get("primary_contact_email", ""),
            placeholder="john@yourcompany.com",
            help="Email of the primary contact person"
        )
        
        primary_contact_phone = st.text_input(
            "Primary Contact Phone *",
            value=data.get("primary_contact_phone", ""),
            placeholder="+1-555-123-4567",
            help="Phone number of the primary contact"
        )
        
        website_url = st.text_input(
            "Website URL (Optional)",
            value=data.get("website_url", ""),
            placeholder="https://www.yourcompany.com",
            help="Your company website"
        )
    
    # Country-specific information
    st.subheader("🌍 Country-Specific Information")
    
    country = st.selectbox(
        "Country/Region",
        options=["United States", "India", "Other"],
        help="Select your country for specific requirements"
    )
    
    if country == "India":
        st.info("🇮🇳 **India-Specific Requirements**")
        col_a, col_b = st.columns(2)
        with col_a:
            gst_number = st.text_input(
                "GST Number (if applicable)",
                value=data.get("gst_number", ""),
                placeholder="27ABCDE1234F1Z5",
                help="GST registration number if your turnover exceeds ₹20 lakhs"
            )
        with col_b:
            pan_number = st.text_input(
                "PAN Number",
                value=data.get("pan_number", tax_id),  # Use tax_id as PAN for India
                placeholder="ABCDE1234F",
                help="Permanent Account Number (PAN)"
            )
        
        # Update tax_id with PAN for India
        if pan_number:
            tax_id = pan_number
        
        with st.expander("📋 India Registration Requirements", expanded=False):
            india_req = st.session_state.seller_registration_tools.get_india_specific_requirements()
            if india_req.get("success"):
                st.write("**Required Documents:**")
                for doc in india_req["business_requirements"]["mandatory_documents"]:
                    st.write(f"• {doc}")
                
                st.write("**Tax Benefits:**")
                st.write(f"• US withholding tax reduced from 30% to 10% with W-8BEN-E form")
                st.write(f"• Form renewal required every 3 years")
    
    elif country == "United States":
        st.info("🇺🇸 **US-Specific Requirements**")
        st.write("• EIN (Employer Identification Number) or SSN required")
        st.write("• W-9 tax form will be required during registration")
        st.write("• US bank account recommended for ACH payments")
    
    # Update registration data
    st.session_state.registration_data.update({
        "business_name": business_name,
        "business_type": business_type,
        "business_address": business_address,
        "business_phone": business_phone,
        "business_email": business_email,
        "tax_id": tax_id,
        "primary_contact_name": primary_contact_name,
        "primary_contact_email": primary_contact_email,
        "primary_contact_phone": primary_contact_phone,
        "website_url": website_url,
        "country": country
    })
    
    if country == "India":
        st.session_state.registration_data.update({
            "gst_number": gst_number,
            "pan_number": pan_number
        })
    
    st.divider()
    
    # Validation and next steps
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("← Back"):
            st.session_state.current_step = "welcome"
            st.rerun()
    
    with col2:
        if st.button("Validate Info"):
            # Validate the information
            if country == "India":
                validation = st.session_state.seller_registration_tools.validate_india_business_info(st.session_state.registration_data)
            else:
                validation = st.session_state.seller_registration_tools.validate_business_info(st.session_state.registration_data)
            
            if validation["success"]:
                st.success("✅ All information is valid!")
            else:
                st.error("❌ Validation errors:")
                for error in validation.get("errors", []):
                    st.error(f"• {error}")
                if validation.get("warnings"):
                    for warning in validation.get("warnings", []):
                        st.warning(f"• {warning}")
    
    with col3:
        if st.button("Continue to AWS Portal →", type="primary", use_container_width=True):
            # Validate required fields
            required_fields = ["business_name", "business_type", "business_address", "business_phone", 
                             "business_email", "tax_id", "primary_contact_name", "primary_contact_email", 
                             "primary_contact_phone"]
            
            missing_fields = [field for field in required_fields if not st.session_state.registration_data.get(field)]
            
            if missing_fields:
                st.error(f"Please fill in all required fields: {', '.join(missing_fields)}")
            else:
                # Validate the information
                if country == "India":
                    validation = st.session_state.seller_registration_tools.validate_india_business_info(st.session_state.registration_data)
                else:
                    validation = st.session_state.seller_registration_tools.validate_business_info(st.session_state.registration_data)
                
                if validation["success"]:
                    st.session_state.current_step = "registration_portal"
                    st.rerun()
                else:
                    st.error("Please fix validation errors before continuing")


def registration_portal_screen():
    """Guide user to AWS Marketplace Management Portal"""
    st.title("🌐 AWS Marketplace Management Portal")
    
    st.markdown("""
    Great! Your business information is ready. Now you need to complete the registration 
    in the AWS Marketplace Management Portal.
    """)
    
    # Show collected information summary
    with st.expander("📋 Your Business Information Summary", expanded=True):
        data = st.session_state.registration_data
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Business Name:** {data.get('business_name', 'N/A')}")
            st.write(f"**Business Type:** {data.get('business_type', 'N/A')}")
            st.write(f"**Email:** {data.get('business_email', 'N/A')}")
            st.write(f"**Phone:** {data.get('business_phone', 'N/A')}")
            st.write(f"**Tax ID:** {data.get('tax_id', 'N/A')}")
        
        with col2:
            st.write(f"**Address:** {data.get('business_address', 'N/A')}")
            st.write(f"**Contact Person:** {data.get('primary_contact_name', 'N/A')}")
            st.write(f"**Contact Email:** {data.get('primary_contact_email', 'N/A')}")
            st.write(f"**Contact Phone:** {data.get('primary_contact_phone', 'N/A')}")
            if data.get('website_url'):
                st.write(f"**Website:** {data.get('website_url')}")
    
    st.divider()
    
    # Portal access instructions
    portal_info = st.session_state.seller_registration_tools.get_marketplace_portal_url()
    
    st.subheader("🚀 Next Steps")
    
    st.markdown(f"""
    **1. Access the AWS Marketplace Management Portal:**
    
    👉 **[Open AWS Marketplace Management Portal]({portal_info.get('portal_url', '#')})**
    
    **2. Complete the registration process:**
    """)
    
    # Show step-by-step instructions
    requirements = st.session_state.seller_registration_tools.get_registration_requirements()
    if requirements.get("success"):
        workflow_steps = requirements["workflow_steps"]
        
        for step_key, step_info in workflow_steps.items():
            step_num = step_key.split('_')[0]
            st.markdown(f"""
            **Step {step_num}: {step_info['title']}**
            - Estimated time: {step_info['estimated_time']}
            """)
            
            if step_key == "4_update_tax_banking":
                st.markdown("  - Complete tax forms (W-9 for US, W-8BEN-E for international)")
                st.markdown("  - Provide banking information for payments")
            elif step_key == "5_validate_information":
                st.markdown("  - AWS will review your information (2-3 business days)")
                st.markdown("  - You may be contacted for additional documentation")
    
    st.divider()
    
    # Country-specific guidance
    country = st.session_state.registration_data.get("country", "Other")
    if country == "India":
        st.subheader("🇮🇳 India-Specific Guidance")
        st.markdown("""
        **Additional documents you may need:**
        - PAN Card copy
        - GST Registration Certificate (if applicable)
        - Bank account details with IFSC code
        - W-8BEN-E form for tax treaty benefits
        
        **Banking Setup:**
        - Use Indian bank account for wire transfers
        - Payments will be in USD, converted by your bank
        - Processing time: 3-5 business days
        """)
    
    elif country == "United States":
        st.subheader("🇺🇸 US-Specific Guidance")
        st.markdown("""
        **Documents needed:**
        - W-9 tax form
        - EIN verification
        - US bank account for ACH (recommended)
        
        **Payment Options:**
        - ACH Direct Deposit (fastest, 2-3 days)
        - Wire Transfer (3-5 days)
        - Check (7-10 days)
        """)
    
    st.divider()
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("← Back to Edit Info"):
            st.session_state.current_step = "seller_registration"
            st.rerun()
    
    with col2:
        if st.button("Check Status"):
            # Re-check seller status
            st.session_state.seller_status = None
            with st.spinner("Checking registration status..."):
                status = st.session_state.seller_registration_tools.check_seller_status()
                st.session_state.seller_status = status
            
            if status.get("seller_status") == "APPROVED":
                st.success("🎉 Registration approved! You can now create listings.")
                st.session_state.current_step = "welcome"
                st.rerun()
            elif status.get("seller_status") == "PENDING":
                st.info("⏳ Registration is still under review.")
            else:
                st.info("📋 Registration not yet submitted or approved.")
    
    with col3:
        if st.button("I've Completed Registration →", type="primary", use_container_width=True):
            # Check status and proceed
            st.session_state.seller_status = None
            with st.spinner("Verifying registration..."):
                status = st.session_state.seller_registration_tools.check_seller_status()
                st.session_state.seller_status = status
            
            if status.get("seller_status") == "APPROVED":
                st.success("🎉 Registration verified! Proceeding to listing creation.")
                st.session_state.current_step = "gather_context"
                st.rerun()
            else:
                st.warning("Registration not yet approved. Please complete the process in the AWS Portal first.")


# Import the existing listing creation screens from the original app
def gather_context_screen():
    """Gather product context from user - same as original"""
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
    """Placeholder for product analysis - would need full implementation"""
    st.title("🔍 Analyzing Your Product...")
    
    st.info("This screen would contain the full product analysis logic from the original app.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back"):
            st.session_state.current_step = "gather_context"
            st.rerun()
    
    with col2:
        if st.button("Continue to Review →", type="primary"):
            st.session_state.current_step = "review_suggestions"
            st.rerun()


def review_suggestions_screen():
    """Placeholder for review suggestions - would need full implementation"""
    st.title("📝 Review AI Suggestions")
    
    st.info("This screen would contain the full review and editing interface from the original app.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back"):
            st.session_state.current_step = "analyze_product"
            st.rerun()
    
    with col2:
        if st.button("Create Listing →", type="primary"):
            st.session_state.current_step = "create_listing"
            st.rerun()


def create_listing_screen():
    """Placeholder for listing creation - would need full implementation"""
    st.title("🚀 Create Your Listing")
    
    st.info("This screen would contain the full listing creation logic from the original app.")
    
    if st.button("← Back"):
        st.session_state.current_step = "review_suggestions"
        st.rerun()


def main():
    """Main app logic"""
    init_session_state()
    
    # Sidebar
    with st.sidebar:
        st.title("🚀 AWS Marketplace")
        st.caption("Seller Registration & Listing Creation")
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
                help="Select which Claude model to use for AI analysis"
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
            "welcome": "🏠 Welcome",
            "seller_registration": "🏢 Seller Registration", 
            "registration_portal": "🌐 AWS Portal",
            "gather_context": "📄 Product Info",
            "analyze_product": "🔍 AI Analysis",
            "review_suggestions": "📝 Review",
            "create_listing": "🚀 Create"
        }
        
        current = st.session_state.current_step
        for key, label in steps.items():
            if key == current:
                st.markdown(f"**→ {label}**")
            else:
                st.markdown(f"   {label}")
        
        st.divider()
        
        # Show seller status
        if st.session_state.seller_status:
            status = st.session_state.seller_status.get("seller_status", "UNKNOWN")
            if status == "APPROVED":
                st.success("✅ Seller Registered")
            elif status == "PENDING":
                st.warning("⏳ Registration Pending")
            else:
                st.info("📋 Registration Needed")
        
        st.caption("Powered by Amazon Bedrock")
    
    # Main content
    if st.session_state.current_step == "welcome":
        welcome_screen()
    elif st.session_state.current_step == "seller_registration":
        seller_registration_screen()
    elif st.session_state.current_step == "registration_portal":
        registration_portal_screen()
    elif st.session_state.current_step == "gather_context":
        gather_context_screen()
    elif st.session_state.current_step == "analyze_product":
        analyze_product_screen()
    elif st.session_state.current_step == "review_suggestions":
        review_suggestions_screen()
    elif st.session_state.current_step == "create_listing":
        create_listing_screen()


if __name__ == "__main__":
    main()