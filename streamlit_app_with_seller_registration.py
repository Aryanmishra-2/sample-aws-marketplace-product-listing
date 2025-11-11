#!/usr/bin/env python3
"""
AI-Guided AWS Marketplace Listing Creation

This app uses LLMs to automate listing creation based on product documentation.
Users provide links/docs, and the AI generates all required fields.
"""

import streamlit as st
from agent.orchestrator import ListingOrchestrator, WorkflowStage
from agent.tools.listing_tools import ListingTools
from agent.tools.seller_registration_tools import SellerRegistrationTools
from agent.sub_agents.seller_registration_agent import SellerRegistrationAgent
# Import agents from agents folder
try:
    from agents.serverless_saas_integration import ServerlessSaasIntegrationAgent
    from agents.buyer_experience import BuyerExperienceAgent
    from agents.metering import MeteringAgent
    from agents.public_visibility import PublicVisibilityAgent
    from agents.workflow_orchestrator import WorkflowOrchestrator
    print("[DEBUG] Successfully imported all agents from agents folder")
except ImportError as e:
    print(f"[DEBUG] ImportError when importing agents: {e}")
    # Fallback if agents not available
    ServerlessSaasIntegrationAgent = None
    BuyerExperienceAgent = None
    MeteringAgent = None
    PublicVisibilityAgent = None
    WorkflowOrchestrator = None
    print("[DEBUG] Set all agents to None due to import error")

import boto3
import json
import re

# Configure page
st.set_page_config(
    page_title="AI-Guided Marketplace Listing",
    page_icon="🤖",
    layout="wide"
)

# Amazon Professional Styling
st.markdown("""
<style>
    /* Import Amazon's Ember font family */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styling with Amazon design system */
    .main .block-container {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        background-color: #fafafa !important;
        padding-top: 2rem !important;
    }
    
    /* Amazon-style form containers */
    .stForm {
        border: 1px solid #d5d9d9 !important;
        border-radius: 8px !important;
        padding: 24px !important;
        background-color: #ffffff !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        margin: 16px 0 !important;
    }
    
    /* Amazon-style input fields */
    .stTextInput > div > div > input {
        border: 1px solid #d5d9d9 !important;
        border-radius: 4px !important;
        padding: 8px 12px !important;
        font-size: 14px !important;
        font-family: 'Inter', sans-serif !important;
        background-color: #ffffff !important;
        transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #007eb9 !important;
        box-shadow: 0 0 0 2px rgba(0, 126, 185, 0.2) !important;
        outline: none !important;
    }
    
    .stTextArea > div > div > textarea {
        border: 1px solid #d5d9d9 !important;
        border-radius: 4px !important;
        padding: 8px 12px !important;
        font-size: 14px !important;
        font-family: 'Inter', sans-serif !important;
        background-color: #ffffff !important;
        transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out !important;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #007eb9 !important;
        box-shadow: 0 0 0 2px rgba(0, 126, 185, 0.2) !important;
        outline: none !important;
    }
    
    .stSelectbox > div > div > div {
        border: 1px solid #d5d9d9 !important;
        border-radius: 4px !important;
        background-color: #ffffff !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Amazon-style buttons */
    .stButton > button {
        border: 1px solid #d5d9d9 !important;
        border-radius: 4px !important;
        padding: 8px 16px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        font-family: 'Inter', sans-serif !important;
        background-color: #ffffff !important;
        color: #0f1111 !important;
        transition: all 0.15s ease !important;
        cursor: pointer !important;
    }
    
    .stButton > button:hover {
        background-color: #f7f8f8 !important;
        border-color: #c7c7c7 !important;
    }
    
    /* Amazon primary button (orange) */
    .stButton > button[kind="primary"] {
        background-color: #ff9900 !important;
        border-color: #ff9900 !important;
        color: #0f1111 !important;
        font-weight: 600 !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #fa8900 !important;
        border-color: #fa8900 !important;
    }
    
    /* Amazon-style section containers */
    .credentials-section {
        border: 1px solid #d5d9d9 !important;
        border-radius: 8px !important;
        padding: 24px !important;
        background-color: #ffffff !important;
        margin: 16px 0 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    .registration-section {
        border: 1px solid #d5d9d9 !important;
        border-radius: 8px !important;
        padding: 24px !important;
        background-color: #ffffff !important;
        margin: 16px 0 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    .product-section {
        border: 1px solid #d5d9d9 !important;
        border-radius: 8px !important;
        padding: 24px !important;
        background-color: #ffffff !important;
        margin: 16px 0 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    /* Amazon-style headers */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif !important;
        color: #0f1111 !important;
        font-weight: 600 !important;
    }
    
    h1 {
        font-size: 28px !important;
        line-height: 36px !important;
        margin-bottom: 16px !important;
    }
    
    h2 {
        font-size: 24px !important;
        line-height: 32px !important;
        margin-bottom: 12px !important;
    }
    
    h3 {
        font-size: 18px !important;
        line-height: 24px !important;
        margin-bottom: 8px !important;
    }
    
    /* Amazon-style labels */
    .stTextInput > label, .stTextArea > label, .stSelectbox > label {
        font-family: 'Inter', sans-serif !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        color: #0f1111 !important;
        margin-bottom: 4px !important;
    }
    
    /* Amazon-style alerts */
    .stAlert {
        border-radius: 4px !important;
        border: 1px solid !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 14px !important;
    }
    
    .stSuccess {
        background-color: #dff0d8 !important;
        border-color: #d6e9c6 !important;
        color: #3c763d !important;
    }
    
    .stError {
        background-color: #f2dede !important;
        border-color: #ebccd1 !important;
        color: #a94442 !important;
    }
    
    .stInfo {
        background-color: #d9edf7 !important;
        border-color: #bce8f1 !important;
        color: #31708f !important;
    }
    
    .stWarning {
        background-color: #fcf8e3 !important;
        border-color: #faebcc !important;
        color: #8a6d3b !important;
    }
    
    /* Amazon-style sidebar */
    .css-1d391kg {
        background-color: #ffffff !important;
        border-right: 1px solid #d5d9d9 !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Amazon-style form submit buttons */
    .stForm > div:last-child button {
        background-color: #ff9900 !important;
        border: 1px solid #ff9900 !important;
        color: #0f1111 !important;
        border-radius: 4px !important;
        padding: 12px 24px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        transition: all 0.15s ease !important;
    }
    
    .stForm > div:last-child button:hover {
        background-color: #fa8900 !important;
        border-color: #fa8900 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
    }
    
    /* Amazon-style navigation buttons */
    .nav-buttons {
        border: 1px solid #d5d9d9;
        border-radius: 4px;
        padding: 16px;
        background-color: #ffffff;
        margin: 16px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Amazon-style dividers */
    hr {
        border: none !important;
        height: 1px !important;
        background-color: #d5d9d9 !important;
        margin: 16px 0 !important;
    }
    
    /* Amazon-style expandable sections */
    .streamlit-expanderHeader {
        background-color: #f7f8f8 !important;
        border: 1px solid #d5d9d9 !important;
        border-radius: 4px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
    }
    
    /* Amazon-style required field indicators */
    .stTextInput label:after, .stTextArea label:after, .stSelectbox label:after {
        content: " *" !important;
        color: #cc0c39 !important;
        font-weight: bold !important;
    }
    
    /* Amazon-style help text */
    .stTextInput small, .stTextArea small, .stSelectbox small {
        font-family: 'Inter', sans-serif !important;
        font-size: 12px !important;
        color: #565959 !important;
    }
    
    /* Amazon-style progress indicators */
    .stProgress > div > div {
        background-color: #ff9900 !important;
    }
    
    /* Amazon-style metrics */
    .metric-container {
        background-color: #ffffff !important;
        border: 1px solid #d5d9d9 !important;
        border-radius: 4px !important;
        padding: 16px !important;
        font-family: 'Inter', sans-serif !important;
    }
</style>
""", unsafe_allow_html=True)


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


def validate_aws_account_region(access_key, secret_key, session_token=None):
    """
    Validate AWS account and determine if it belongs to AWS Inc or AWS India
    
    Returns:
        dict: {
            'success': bool,
            'account_id': str,
            'region_type': 'AWS_INC' | 'AWS_INDIA' | 'UNKNOWN',
            'user_arn': str,
            'organization': str,
            'error': str (if failed)
        }
    """
    try:
        # Create session with provided credentials
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token,
            region_name='us-east-1'
        )
        
        # Get caller identity
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        account_id = identity.get('Account')
        user_arn = identity.get('Arn')
        
        # Determine region type based on account patterns and ARN
        region_type = 'UNKNOWN'
        organization = 'Unknown'
        
        # Check for AWS Inc patterns
        if (account_id.startswith(('123456789', '533719170361', '518237894409')) or 
            'aws.amazon.com' in user_arn.lower() or
            'amazon.com' in user_arn.lower()):
            region_type = 'AWS_INC'
            organization = 'Amazon Web Services Inc.'
        
        # Check for AWS India patterns
        elif (account_id.startswith(('797583073197', '999999999')) or
              'aws.amazon.in' in user_arn.lower() or
              'amazon.in' in user_arn.lower()):
            region_type = 'AWS_INDIA'
            organization = 'Amazon Web Services India Pvt Ltd'
        
        # Try to get more information from organizations API
        try:
            orgs = session.client('organizations')
            org_info = orgs.describe_organization()
            
            # Check master account email domain
            master_email = org_info.get('Organization', {}).get('MasterAccountEmail', '')
            if 'amazon.com' in master_email:
                region_type = 'AWS_INC'
                organization = 'Amazon Web Services Inc.'
            elif 'amazon.in' in master_email:
                region_type = 'AWS_INDIA'
                organization = 'Amazon Web Services India Pvt Ltd'
                
        except Exception:
            # Organizations API might not be accessible
            pass
        
        # Additional heuristics based on account ID ranges
        if region_type == 'UNKNOWN':
            account_num = int(account_id)
            if account_num < 600000000000:  # Older AWS Inc accounts
                region_type = 'AWS_INC'
                organization = 'Amazon Web Services Inc.'
            else:  # Newer accounts, could be either
                region_type = 'UNKNOWN'
                organization = 'Unknown Organization'
        
        return {
            'success': True,
            'account_id': account_id,
            'region_type': region_type,
            'user_arn': user_arn,
            'organization': organization,
            'session': session
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def credentials_input_screen():
    """AWS Credentials input and validation screen"""
    st.title("🔐 AWS Marketplace Seller Registration")
    st.markdown("### Step 1: AWS Credentials & Account Validation")
    
    # Amazon-style breadcrumb
    st.markdown('<div style="color: #565959; font-size: 12px; margin-bottom: 16px;">AWS Marketplace > Seller Registration > Credentials</div>', unsafe_allow_html=True)
    
    # Show that this is the home screen
    st.caption("🏠 This is the home screen - all navigation leads back here")
    
    st.info("""
    **Enter your AWS credentials to:**
    - Validate your AWS account
    - Determine organization (AWS Inc vs AWS India)
    - Check current seller registration status
    - Proceed with appropriate registration process
    """)
    
    # Check if credentials are already validated
    if 'aws_credentials' in st.session_state and 'account_validation' in st.session_state:
        # Show validation results in styled container
        st.markdown('<div class="credentials-section">', unsafe_allow_html=True)
        validation_result = st.session_state.account_validation
        
        st.success("✅ AWS Credentials Validated Successfully!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"""
            **Account Details:**
            - **Account ID**: {validation_result['account_id']}
            - **Organization**: {validation_result['organization']}
            - **Region Type**: {validation_result['region_type']}
            """)
        
        with col2:
            if validation_result['region_type'] == 'AWS_INC':
                st.success("""
                **🇺🇸 AWS Inc Account Detected**
                - US-based registration process
                - Standard AWS Marketplace requirements
                - USD currency and US tax forms
                """)
            elif validation_result['region_type'] == 'AWS_INDIA':
                st.info("""
                **🇮🇳 AWS India Account Detected**
                - India-specific registration process
                - Additional compliance requirements
                - INR currency and Indian tax forms
                """)
            else:
                st.warning("""
                **❓ Unknown Organization**
                - Will use standard registration process
                - Manual verification may be required
                """)
        
        # Check seller registration status
        st.markdown("### Current Seller Registration Status")
        seller_status = check_seller_registration_status()
        
        # Navigation buttons (outside form)
        col3, col4, col5, col6 = st.columns(4)
        
        with col3:
            if st.button("🔄 Re-validate Credentials"):
                # Clear credentials to re-enter
                if 'aws_credentials' in st.session_state:
                    del st.session_state.aws_credentials
                if 'account_validation' in st.session_state:
                    del st.session_state.account_validation
                st.rerun()
        
        with col6:
            if st.button("🗑️ Clear All Data", help="Clear all stored data and start fresh"):
                # Clear all session state data
                keys_to_clear = [
                    'aws_credentials', 
                    'account_validation', 
                    'seller_status',
                    'product_context',
                    'ai_suggestions',
                    'listing_data',
                    'workflow_data',
                    'registration_completed'
                ]
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                
                # Reset to credentials step
                st.session_state.current_step = "credentials"
                st.success("🗑️ All data cleared! You can now enter new AWS credentials.")
                st.rerun()
        
        with col4:
            if seller_status == 'APPROVED':
                if st.button("🚀 Create Product Listing"):
                    st.session_state.current_step = "gather_context"
                    st.rerun()
            elif seller_status == 'NOT_REGISTERED':
                if st.button("🚀 Register via API"):
                    st.session_state.current_step = "registration_details"
                    st.rerun()
        
        with col5:
            if st.button("ℹ️ View Portal"):
                st.markdown("[AWS Marketplace Management Portal](https://aws.amazon.com/marketplace/management/seller-registration)")
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close credentials-section container
        return True
    
    # Clear data section with info
    with st.expander("🗑️ Clear All Data", expanded=False):
        st.info("""
        **What gets cleared:**
        - AWS credentials and account validation
        - Seller registration status
        - Product information and AI suggestions
        - Listing data and workflow progress
        
        **Use this to:**
        - Switch to different AWS credentials
        - Start fresh with a new product
        - Reset after completing a workflow
        """)
        
        if st.button("🗑️ Clear All Data", help="Clear all stored data and start fresh", key="clear_data_main"):
            st.session_state.show_clear_confirmation = True
    
    # Show confirmation dialog if requested
    if st.session_state.get('show_clear_confirmation', False):
        with col_clear2:
            st.warning("⚠️ This will clear ALL stored data including credentials, registration info, and product data.")
            col_confirm1, col_confirm2 = st.columns(2)
            
            with col_confirm1:
                if st.button("✅ Yes, Clear All", key="confirm_clear_main"):
                    # Clear all session state data
                    keys_to_clear = [
                        'aws_credentials', 
                        'account_validation', 
                        'seller_status',
                        'product_context',
                        'ai_suggestions',
                        'listing_data',
                        'workflow_data',
                        'registration_completed',
                        'show_clear_confirmation'
                    ]
                    for key in keys_to_clear:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    # Reset to credentials step
                    st.session_state.current_step = "credentials"
                    st.success("🗑️ All data cleared! You can now enter new AWS credentials.")
                    st.rerun()
            
            with col_confirm2:
                if st.button("❌ Cancel", key="cancel_clear_main"):
                    st.session_state.show_clear_confirmation = False
                    st.rerun()
    
    st.divider()
    
    # Show credentials input form in styled container
    st.markdown('<div class="credentials-section">', unsafe_allow_html=True)
    with st.form("aws_credentials_form"):
        st.markdown('<h3 style="color: #0f1111; font-weight: 600; margin-bottom: 16px;">🔐 AWS Credentials</h3>', unsafe_allow_html=True)
        st.markdown('<hr style="margin: 16px 0; border: none; height: 1px; background-color: #d5d9d9;">', unsafe_allow_html=True)
        
        access_key = st.text_input(
            "AWS Access Key ID *",
            placeholder="AKIA...",
            help="Your AWS Access Key ID (starts with AKIA)"
        )
        
        secret_key = st.text_input(
            "AWS Secret Access Key *",
            type="password",
            help="Your AWS Secret Access Key"
        )
        
        session_token = st.text_input(
            "AWS Session Token (Optional)",
            type="password",
            help="Required only for temporary credentials"
        )
        
        submitted = st.form_submit_button("🔍 Validate Credentials & Check Status")
        
        if submitted:
            if not access_key or not secret_key:
                st.error("❌ Please provide both Access Key ID and Secret Access Key")
                return False
            
            # Validate credentials and determine organization
            with st.spinner("🔍 Validating AWS credentials and checking account..."):
                validation_result = validate_aws_account_region(
                    access_key, 
                    secret_key, 
                    session_token if session_token else None
                )
            
            if validation_result['success']:
                # Store credentials and validation results in session state
                st.session_state.aws_credentials = {
                    'access_key': access_key,
                    'secret_key': secret_key,
                    'session_token': session_token if session_token else None,
                    'session': validation_result['session']
                }
                st.session_state.account_validation = validation_result
                
                # Update seller registration agent with credentials
                if 'seller_registration_agent' in st.session_state:
                    st.session_state.seller_registration_agent.update_credentials(
                        aws_access_key_id=access_key,
                        aws_secret_access_key=secret_key,
                        aws_session_token=session_token if session_token else None,
                        region='us-east-1'
                    )
                    print("[DEBUG] Updated seller registration agent credentials")
                
                st.success("✅ Credentials validated! Refreshing page...")
                st.rerun()
                
            else:
                st.error(f"❌ Credential validation failed: {validation_result['error']}")
                return False
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close credentials-section container
    return False

def check_seller_registration_status():
    """Check and display current seller registration status"""
    if 'aws_credentials' not in st.session_state:
        st.error("❌ AWS credentials not available")
        return 'UNKNOWN'
    
    try:
        # Initialize seller registration tools
        seller_tools = SellerRegistrationTools(
            region='us-east-1',
            aws_access_key_id=st.session_state.aws_credentials['access_key'],
            aws_secret_access_key=st.session_state.aws_credentials['secret_key'],
            aws_session_token=st.session_state.aws_credentials['session_token']
        )
        
        # Check seller status
        status_result = seller_tools.check_seller_status()
        
        if status_result.get('success'):
            seller_status = status_result.get('seller_status', 'UNKNOWN')
            
            if seller_status == 'APPROVED':
                st.success("""
                🎉 **Seller Registration: APPROVED**
                
                Your account is registered as an AWS Marketplace seller!
                """)
                
                # Get detailed account information
                account_details = seller_tools.get_seller_account_details()
                
                if account_details.get('success'):
                    products_count = account_details.get('owned_products_count', 0)
                    
                    # Show products count if any
                    if products_count > 0:
                        st.write(f"� **Arctive Products:** {products_count}")
                    
                    st.divider()
                    
                    # Manual verification section
                    st.write("**📋 Seller Profile Validation Required**")
                    st.warning("""
                    ⚠️ **Before creating products, you must validate your seller profile.**
                    
                    AWS Marketplace requires complete tax and payment information before you can list products.
                    """)
                    
                    st.info("""
                    **Please complete these steps:**
                    
                    1. 🔗 **Open the AWS Marketplace Seller Settings portal:**
                       👉 [AWS Marketplace Seller Settings](https://aws.amazon.com/marketplace/management/seller-settings/account)
                    
                    2. 📋 **Verify Tax Information:**
                       - Check that your W-9 (US) or W-8 (International) form is submitted
                       - Ensure your business name and EIN/Tax ID are correct
                       - Verify your business address is up to date
                    
                    3. 💳 **Verify Payment Information:**
                       - Confirm your bank account details are configured
                       - Check that your routing number and account number are correct
                       - Ensure disbursement method is selected
                    
                    4. ✅ **Return here and confirm completion below**
                    """)
                    
                    # Initialize session state for manual verification
                    if 'tax_verified' not in st.session_state:
                        st.session_state.tax_verified = False
                    if 'banking_verified' not in st.session_state:
                        st.session_state.banking_verified = False
                    if 'tax_details' not in st.session_state:
                        st.session_state.tax_details = {}
                    
                    st.divider()
                    st.write("**Validation Checklist:**")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**📋 Tax Information**")
                        tax_verified = st.checkbox(
                            "I have verified my tax information is complete in the AWS portal",
                            value=st.session_state.tax_verified,
                            key="tax_checkbox",
                            help="Check this ONLY after verifying your tax information in the AWS Marketplace Seller Settings"
                        )
                        st.session_state.tax_verified = tax_verified
                        
                        if tax_verified:
                            with st.expander("📋 Enter Tax Details (Optional)", expanded=False):
                                st.write("Enter your tax information for reference:")
                                
                                tax_classification = st.selectbox(
                                    "Tax Classification",
                                    ["", "Individual/Sole Proprietor", "C Corporation", "S Corporation", 
                                     "Partnership", "Trust/Estate", "LLC", "Other"],
                                    index=0 if not st.session_state.tax_details.get('classification') else 
                                          ["", "Individual/Sole Proprietor", "C Corporation", "S Corporation", 
                                           "Partnership", "Trust/Estate", "LLC", "Other"].index(
                                               st.session_state.tax_details.get('classification', ''))
                                )
                                
                                business_name = st.text_input(
                                    "Business Name",
                                    value=st.session_state.tax_details.get('business_name', ''),
                                    placeholder="Your legal business name"
                                )
                                
                                ein = st.text_input(
                                    "EIN/Tax ID",
                                    value=st.session_state.tax_details.get('ein', ''),
                                    placeholder="XX-XXXXXXX",
                                    help="Your Employer Identification Number"
                                )
                                
                                address = st.text_area(
                                    "Business Address",
                                    value=st.session_state.tax_details.get('address', ''),
                                    placeholder="Street, City, State, ZIP",
                                    height=80
                                )
                                
                                if st.button("Save Tax Details"):
                                    st.session_state.tax_details = {
                                        'classification': tax_classification,
                                        'business_name': business_name,
                                        'ein': ein,
                                        'address': address
                                    }
                                    st.success("Tax details saved!")
                                    st.rerun()
                    
                    with col2:
                        st.write("**💳 Payment Information**")
                        banking_verified = st.checkbox(
                            "I have verified my payment information is complete in the AWS portal",
                            value=st.session_state.banking_verified,
                            key="banking_checkbox",
                            help="Check this ONLY after verifying your banking/payment information in the AWS Marketplace Seller Settings"
                        )
                        st.session_state.banking_verified = banking_verified
                    
                    st.divider()
                    
                    # Show tax details if saved
                    if st.session_state.tax_verified and st.session_state.tax_details:
                        st.write("**📋 Tax Information Summary:**")
                        with st.expander("View Tax Details", expanded=True):
                            details = st.session_state.tax_details
                            if details.get('classification'):
                                st.write(f"**Tax Classification:** {details['classification']}")
                            if details.get('business_name'):
                                st.write(f"**Business Name:** {details['business_name']}")
                            if details.get('ein'):
                                # Mask EIN for security
                                ein_masked = details['ein'][:3] + "****" + details['ein'][-2:] if len(details['ein']) > 5 else "***"
                                st.write(f"**EIN:** {ein_masked}")
                            if details.get('address'):
                                st.write(f"**Address:** {details['address']}")
                    
                    st.divider()
                    
                    # Show appropriate message and actions based on verification status
                    if st.session_state.tax_verified and st.session_state.banking_verified:
                        st.success("""
                        ✅ **Validation Complete! Your seller profile is ready.**
                        
                        You have confirmed that both tax and payment information are configured in AWS.
                        """)
                        
                        st.info("""
                        **You can now proceed to:**
                        - Create new product listings
                        - Manage existing products
                        - View sales and reports
                        """)
                        
                        # Offer to proceed to product creation
                        st.divider()
                        st.write("**🚀 Ready to Create Your First Product?**")
                        
                        col_a, col_b, col_c = st.columns([1, 1, 1])
                        
                        with col_b:
                            if st.button("📦 Create Product Listing", type="primary", use_container_width=True):
                                st.session_state.current_step = "welcome"
                                st.session_state.seller_profile_validated = True
                                st.rerun()
                        
                    else:
                        missing_items = []
                        if not st.session_state.tax_verified:
                            missing_items.append("Tax Information")
                        if not st.session_state.banking_verified:
                            missing_items.append("Payment Information")
                        
                        st.error(f"""
                        ❌ **Validation Incomplete**
                        
                        Please complete validation for: {', '.join(missing_items)}
                        """)
                        
                        st.warning("""
                        **You must validate both tax and payment information before creating products.**
                        
                        1. Click the link above to open AWS Marketplace Seller Settings
                        2. Verify your tax and payment information are complete
                        3. Return here and check both boxes
                        4. Then you can proceed to create products
                        """)
                else:
                    # Fallback if we can't get account details
                    st.info("""
                    ✅ **Your seller account is approved.**
                    
                    Please verify your tax and banking information at:
                    👉 [AWS Marketplace Seller Settings](https://aws.amazon.com/marketplace/management/seller-settings/account)
                    """)
                    
            elif seller_status == 'PENDING':
                st.warning("""
                ⏳ **Seller Registration: PENDING**
                
                Your seller registration is currently under review by AWS.
                Estimated completion: 2-3 business days.
                """)
                
            elif seller_status == 'NOT_REGISTERED':
                st.info("""
                📝 **Seller Registration: NOT REGISTERED**
                
                Your account is not yet registered as an AWS Marketplace seller.
                
                **We'll help you register using AWS APIs directly through this application.**
                
                ✨ **What we'll do:**
                - Create your business profile via AWS API
                - Set up your public seller profile
                - Configure tax and banking information
                - Submit everything to AWS for approval
                
                **Estimated time:** 10-15 minutes to complete the forms
                **AWS Review:** 2-3 business days for approval
                """)
                
                # Check if there's any registration data in progress
                if 'registration_data' in st.session_state and st.session_state.registration_data:
                    st.write("---")
                    st.write("**📊 Current Registration Progress:**")
                    
                    # Use the new check_registration_progress method
                    progress_result = seller_tools.check_registration_progress(st.session_state.registration_data)
                    
                    if progress_result.get("success"):
                        # Show progress bar
                        progress_pct = progress_result.get("progress_percentage", 0)
                        st.progress(progress_pct / 100)
                        st.write(f"**{progress_pct}% Complete**")
                        
                        # Show status by section
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**Completed:**")
                            for step in progress_result.get("completed_steps", []):
                                st.write(f"✅ {step}")
                        
                        with col2:
                            st.write("**Still Required:**")
                            for step in progress_result.get("required_steps", []):
                                st.write(f"❌ {step}")
                else:
                    st.write("---")
                    st.write("**📋 Registration Status:**")
                    st.write("❌ Business Profile: Not started")
                    st.write("❌ Tax Information: Not started")
                    st.write("❌ Banking Information: Not started")
                    st.write("❌ Disbursement Method: Not started")
                
            else:
                st.warning(f"❓ **Seller Registration: {seller_status}**")
                st.write("Status unclear. Manual verification may be required.")
            
            return seller_status
        
        else:
            st.error(f"❌ Failed to check seller status: {status_result.get('error', 'Unknown error')}")
            return 'ERROR'
    
    except Exception as e:
        st.error(f"❌ Error checking seller status: {str(e)}")
        return 'ERROR'

def registration_details_screen():
    """Collect seller registration details based on organization type"""
    st.title("🚀 AWS Marketplace Seller Registration via API")
    
    # Add navigation buttons at the top
    show_navigation_buttons(show_back=True, show_home=True, back_step="credentials")
    st.divider()
    
    if 'account_validation' not in st.session_state:
        st.error("❌ Account validation required. Please go back to credentials step.")
        return
    
    account_info = st.session_state.account_validation
    region_type = account_info.get('region_type', 'UNKNOWN')
    
    st.success("""
    **🎯 API-Driven Registration Process**
    
    We'll register your account as an AWS Marketplace seller using direct AWS API calls.
    This ensures faster processing and immediate submission to AWS for review.
    """)
    
    st.info(f"""
    **Account**: {account_info.get('account_id')}  
    **Organization**: {account_info.get('organization')}  
    **Registration Type**: {region_type}
    """)
    
    # Show appropriate registration form based on region type
    if region_type == 'AWS_INDIA':
        show_india_registration_form()
    else:
        show_standard_registration_form()

def show_india_registration_form():
    """Show India-specific registration form"""
    st.markdown("### 🇮🇳 AWS India Seller Registration via API")
    st.info("📡 **API-Driven Process**: Your information will be submitted directly to AWS via official APIs for immediate processing.")
    
    with st.form("india_registration_form"):
        st.subheader("Business Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            business_name = st.text_input("Legal Business Name *")
            business_type = st.selectbox(
                "Business Type *",
                ["Private Limited Company", "Public Limited Company", "Partnership", "LLP", "Sole Proprietorship", "Other"]
            )
            pan_number = st.text_input("PAN Number *", placeholder="AAAAA9999A")
            gstin = st.text_input("GSTIN (if applicable)", placeholder="22AAAAA0000A1Z5")
            
        with col2:
            business_address = st.text_area("Business Address *")
            business_phone = st.text_input("Business Phone *", placeholder="+91-XXXXXXXXXX")
            business_email = st.text_input("Business Email *")
            website_url = st.text_input("Website URL")
        
        st.subheader("Contact Information")
        
        col3, col4 = st.columns(2)
        
        with col3:
            primary_contact_name = st.text_input("Primary Contact Name *")
            primary_contact_email = st.text_input("Primary Contact Email *")
            primary_contact_phone = st.text_input("Primary Contact Phone *")
            
        with col4:
            secondary_contact_name = st.text_input("Secondary Contact Name")
            secondary_contact_email = st.text_input("Secondary Contact Email")
            secondary_contact_phone = st.text_input("Secondary Contact Phone")
        
        st.subheader("Banking Information")
        
        col5, col6 = st.columns(2)
        
        with col5:
            bank_name = st.text_input("Bank Name *")
            account_number = st.text_input("Account Number *", type="password")
            ifsc_code = st.text_input("IFSC Code *")
            
        with col6:
            account_holder_name = st.text_input("Account Holder Name *")
            account_type = st.selectbox("Account Type *", ["Current", "Savings"])
            swift_code = st.text_input("SWIFT Code (for international transfers)")
        
        st.subheader("Compliance & Documentation")
        
        st.checkbox("I confirm that all provided information is accurate and complete")
        st.checkbox("I agree to comply with AWS Marketplace policies and Indian regulations")
        st.checkbox("I understand that false information may result in account suspension")
        
        submitted = st.form_submit_button("🚀 Submit India Registration")
        
        if submitted:
            # Validate and process India registration
            registration_data = {
                "business_info": {
                    "business_name": business_name,
                    "business_type": business_type,
                    "business_address": business_address,
                    "business_phone": business_phone,
                    "business_email": business_email,
                    "website_url": website_url,
                    "pan_number": pan_number,
                    "gstin": gstin
                },
                "contact_info": {
                    "primary_contact_name": primary_contact_name,
                    "primary_contact_email": primary_contact_email,
                    "primary_contact_phone": primary_contact_phone,
                    "secondary_contact_name": secondary_contact_name,
                    "secondary_contact_email": secondary_contact_email,
                    "secondary_contact_phone": secondary_contact_phone
                },
                "banking_info": {
                    "bank_name": bank_name,
                    "account_number": account_number,
                    "ifsc_code": ifsc_code,
                    "account_holder_name": account_holder_name,
                    "account_type": account_type,
                    "swift_code": swift_code
                },
                "region_type": "AWS_INDIA"
            }
            
            process_seller_registration(registration_data)

def show_standard_registration_form():
    """Show standard (AWS Inc) registration form"""
    st.markdown('<div class="registration-section">', unsafe_allow_html=True)
    st.markdown("### 🇺🇸 AWS Marketplace Seller Registration")
    
    # Amazon-style breadcrumb
    st.markdown('<div style="color: #565959; font-size: 12px; margin-bottom: 16px;">AWS Marketplace > Seller Registration > Business Information</div>', unsafe_allow_html=True)
    
    st.info("📡 **Secure API Integration**: Your information will be submitted directly to AWS via official APIs for immediate processing and enhanced security.")
    
    # Show validation requirements
    with st.expander("📋 Field Requirements & Validation Rules", expanded=False):
        st.markdown("""
        **Required Fields (marked with *):**
        - All business information fields
        - Primary contact information
        - Banking information
        - Tax classification
        
        **Validation Rules:**
        - **Email**: Must be valid format (contains @ and .)
        - **Tax ID**: Must be 9 digits (EIN/SSN format)
        - **Phone Numbers**: Must be 10 digits
        - **Business Address**: Complete address required
        
        **Tips:**
        - Use format XX-XXXXXXX for Tax ID
        - Use format +1-XXX-XXX-XXXX for phone numbers
        - Ensure all required fields are filled before submitting
        """)
    
    with st.form("standard_registration_form"):
        st.markdown('<h3 style="color: #0f1111; font-weight: 600; margin-bottom: 16px;">🏢 Business Information</h3>', unsafe_allow_html=True)
        st.markdown('<hr style="margin: 16px 0; border: none; height: 1px; background-color: #d5d9d9;">', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            business_name = st.text_input("Legal Business Name *")
            business_type = st.selectbox(
                "Business Type *",
                ["Corporation", "LLC", "Partnership", "Sole Proprietorship", "Other"]
            )
            tax_id = st.text_input("Tax ID (EIN/SSN) *", placeholder="XX-XXXXXXX", help="9-digit Employer Identification Number or Social Security Number")
            
        with col2:
            business_address = st.text_area("Business Address *")
            business_phone = st.text_input("Business Phone *", placeholder="+1-XXX-XXX-XXXX", help="10-digit US phone number")
            business_email = st.text_input("Business Email *", help="Valid business email address")
            website_url = st.text_input("Website URL")
        
        st.subheader("Contact Information")
        
        col3, col4 = st.columns(2)
        
        with col3:
            primary_contact_name = st.text_input("Primary Contact Name *")
            primary_contact_email = st.text_input("Primary Contact Email *")
            primary_contact_phone = st.text_input("Primary Contact Phone *")
            
        with col4:
            secondary_contact_name = st.text_input("Secondary Contact Name")
            secondary_contact_email = st.text_input("Secondary Contact Email")
            secondary_contact_phone = st.text_input("Secondary Contact Phone")
        
        st.subheader("Banking Information")
        
        col5, col6 = st.columns(2)
        
        with col5:
            bank_name = st.text_input("Bank Name *")
            routing_number = st.text_input("Routing Number *")
            account_number = st.text_input("Account Number *", type="password")
            
        with col6:
            account_holder_name = st.text_input("Account Holder Name *")
            account_type = st.selectbox("Account Type *", ["Checking", "Savings"])
        
        st.subheader("Tax Information")
        
        tax_classification = st.selectbox(
            "Tax Classification *",
            ["Individual/Sole Proprietor", "C Corporation", "S Corporation", "Partnership", "LLC", "Other"]
        )
        
        st.subheader("Compliance")
        
        st.checkbox("I confirm that all provided information is accurate and complete")
        st.checkbox("I agree to comply with AWS Marketplace policies and US regulations")
        st.checkbox("I understand that false information may result in account suspension")
        
        submitted = st.form_submit_button("🚀 Submit Standard Registration")
        
        if submitted:
            # Client-side validation before submission
            validation_errors = []
            
            # Required field validation
            required_fields = {
                "Legal Business Name": business_name,
                "Business Address": business_address,
                "Business Phone": business_phone,
                "Business Email": business_email,
                "Tax ID": tax_id,
                "Primary Contact Name": primary_contact_name,
                "Primary Contact Email": primary_contact_email,
                "Primary Contact Phone": primary_contact_phone,
                "Bank Name": bank_name,
                "Routing Number": routing_number,
                "Account Number": account_number,
                "Account Holder Name": account_holder_name
            }
            
            for field_name, field_value in required_fields.items():
                if not field_value or not field_value.strip():
                    validation_errors.append(f"Required field missing: {field_name}")
            
            # Email format validation
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            
            if business_email and not re.match(email_pattern, business_email):
                validation_errors.append("Invalid business email format")
            
            if primary_contact_email and not re.match(email_pattern, primary_contact_email):
                validation_errors.append("Invalid primary contact email format")
            
            # Tax ID validation
            if tax_id:
                tax_id_clean = tax_id.replace("-", "").replace(" ", "")
                if not (len(tax_id_clean) == 9 and tax_id_clean.isdigit()):
                    validation_errors.append("Tax ID should be 9 digits (EIN/SSN format: XX-XXXXXXX)")
            
            # Phone validation
            def validate_phone(phone, field_name):
                if phone:
                    phone_clean = re.sub(r'[^\d]', '', phone)
                    if len(phone_clean) != 10:
                        validation_errors.append(f"{field_name} should be 10 digits")
            
            validate_phone(business_phone, "Business Phone")
            validate_phone(primary_contact_phone, "Primary Contact Phone")
            
            # Show validation errors if any
            if validation_errors:
                st.error("❌ Please fix the following issues before submitting:")
                for error in validation_errors:
                    st.markdown(f"🔴 {error}")
                return
            # Validate and process standard registration
            registration_data = {
                "business_info": {
                    "business_name": business_name,
                    "business_type": business_type,
                    "business_address": business_address,
                    "business_phone": business_phone,
                    "business_email": business_email,
                    "website_url": website_url,
                    "tax_id": tax_id
                },
                "contact_info": {
                    "primary_contact_name": primary_contact_name,
                    "primary_contact_email": primary_contact_email,
                    "primary_contact_phone": primary_contact_phone,
                    "secondary_contact_name": secondary_contact_name,
                    "secondary_contact_email": secondary_contact_email,
                    "secondary_contact_phone": secondary_contact_phone
                },
                "banking_info": {
                    "bank_name": bank_name,
                    "routing_number": routing_number,
                    "account_number": account_number,
                    "account_holder_name": account_holder_name,
                    "account_type": account_type
                },
                "tax_info": {
                    "tax_classification": tax_classification
                },
                "region_type": "AWS_INC"
            }
            
            process_seller_registration(registration_data)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close registration-section container

def process_seller_registration(registration_data):
    """Process seller registration using AWS APIs"""
    if 'aws_credentials' not in st.session_state:
        st.error("❌ AWS credentials not available")
        return
    
    try:
        # Initialize seller registration tools
        seller_tools = SellerRegistrationTools(
            region='us-east-1',
            aws_access_key_id=st.session_state.aws_credentials['access_key'],
            aws_secret_access_key=st.session_state.aws_credentials['secret_key'],
            aws_session_token=st.session_state.aws_credentials['session_token']
        )
        
        # Pre-validation: Check all required sections are present
        st.write("🔍 Pre-validating registration data...")
        
        required_sections = {
            "business_info": "Business Information",
            "contact_info": "Contact Information",
            "tax_info": "Tax Information",
            "banking_info": "Banking Information"
        }
        
        missing_sections = []
        for section_key, section_name in required_sections.items():
            if section_key not in registration_data or not registration_data[section_key]:
                missing_sections.append(section_name)
        
        if missing_sections:
            st.error(f"❌ Missing required sections: {', '.join(missing_sections)}")
            st.info("Please ensure all sections are filled out before submitting.")
            return
        
        # Validate each section has required data
        if not registration_data["business_info"].get("business_name"):
            st.error("❌ Business name is required")
            return
        
        if not registration_data["tax_info"].get("tax_classification"):
            st.error("❌ Tax classification is required")
            return
        
        if not registration_data["banking_info"].get("bank_name"):
            st.error("❌ Banking information is incomplete")
            return
        
        st.success("✅ Pre-validation passed")
        
        with st.spinner("🚀 Processing seller registration..."):
            # Step 1: Create business profile
            st.write("📝 Creating business profile...")
            # Merge business_info and contact_info for validation
            business_profile_data = {
                **registration_data["business_info"],
                **registration_data["contact_info"]
            }
            business_result = seller_tools.create_business_profile(business_profile_data)
            
            if business_result.get("success"):
                st.success(f"✅ Business profile created: {business_result.get('message', 'Successfully created')}")
            else:
                st.error("❌ Business profile creation failed:")
                
                # Show specific validation errors if available
                if business_result.get("errors"):
                    st.markdown("**Please fix the following issues:**")
                    for error in business_result["errors"]:
                        st.markdown(f"🔴 {error}")
                
                # Show warnings if available
                if business_result.get("warnings"):
                    st.markdown("**Warnings:**")
                    for warning in business_result["warnings"]:
                        st.markdown(f"🟡 {warning}")
                
                # Show general error message if no specific errors
                if not business_result.get("errors") and not business_result.get("warnings"):
                    error_msg = business_result.get('error') or business_result.get('message') or 'Unknown error occurred'
                    st.markdown(f"🔴 {error_msg}")
                
                return
            
            # Step 2: Create public profile
            st.write("🌐 Creating public profile...")
            public_profile_data = {
                "company_name": registration_data["business_info"]["business_name"],
                "company_description": f"AWS Marketplace seller - {registration_data['business_info']['business_name']}",
                "website_url": registration_data["business_info"].get("website_url", ""),
                "support_email": registration_data["contact_info"]["primary_contact_email"],
                "support_phone": registration_data["contact_info"]["primary_contact_phone"]
            }
            
            public_result = seller_tools.create_public_profile(public_profile_data)
            
            if public_result.get("success"):
                st.success(f"✅ Public profile created: {public_result.get('message', 'Successfully created')}")
            else:
                error_msg = public_result.get('error') or public_result.get('message') or 'Unknown error occurred'
                st.error(f"❌ Public profile creation failed: {error_msg}")
                return
            
            # Step 3: Validate tax information
            st.write("� UValidating tax information...")
            tax_validation = seller_tools._validate_tax_info(registration_data.get("tax_info", {}))
            
            if not tax_validation.get("success"):
                st.error("❌ Tax information validation failed:")
                for error in tax_validation.get("errors", []):
                    st.markdown(f"🔴 {error}")
                return
            
            if tax_validation.get("warnings"):
                st.warning("⚠️ Tax information warnings:")
                for warning in tax_validation.get("warnings", []):
                    st.markdown(f"🟡 {warning}")
            
            # Step 4: Validate banking information
            st.write("🏦 Validating banking information...")
            banking_validation = seller_tools._validate_banking_info(registration_data["banking_info"])
            
            if not banking_validation.get("success"):
                st.error("❌ Banking information validation failed:")
                for error in banking_validation.get("errors", []):
                    st.markdown(f"🔴 {error}")
                return
            
            if banking_validation.get("warnings"):
                st.warning("⚠️ Banking information warnings:")
                for warning in banking_validation.get("warnings", []):
                    st.markdown(f"🟡 {warning}")
            
            # Step 5: Update tax and banking information
            st.write("💰 Updating tax and banking information...")
            tax_banking_data = {
                "tax_info": registration_data.get("tax_info", {}),
                "banking_info": registration_data["banking_info"]
            }
            
            tax_banking_result = seller_tools.update_tax_banking_info(tax_banking_data)
            
            if tax_banking_result.get("success"):
                st.success(f"✅ Tax and banking info updated: {tax_banking_result.get('message', 'Successfully updated')}")
            else:
                error_msg = tax_banking_result.get('error') or tax_banking_result.get('message') or 'Unknown error occurred'
                st.error(f"❌ Tax and banking update failed: {error_msg}")
                return
            
            # Step 4: Validate information
            st.write("🔍 Validating information...")
            validation_result = seller_tools.validate_information()
            
            if validation_result.get("success"):
                st.success(f"✅ Information validation initiated: {validation_result.get('message', 'Validation started')}")
            else:
                warning_msg = validation_result.get('message') or validation_result.get('error') or 'Validation status unclear'
                st.warning(f"⚠️ Validation status: {warning_msg}")
            
            # Step 7: Validate and setup disbursement method
            st.write("💳 Validating disbursement method...")
            disbursement_data = {
                "method": "ACH_DIRECT_DEPOSIT",
                "account_details": registration_data["banking_info"]
            }
            
            disbursement_validation = seller_tools._validate_disbursement_info(disbursement_data)
            
            if not disbursement_validation.get("success"):
                st.error("❌ Disbursement method validation failed:")
                for error in disbursement_validation.get("errors", []):
                    st.markdown(f"🔴 {error}")
                return
            
            if disbursement_validation.get("warnings"):
                st.warning("⚠️ Disbursement method warnings:")
                for warning in disbursement_validation.get("warnings", []):
                    st.markdown(f"🟡 {warning}")
            
            st.write("💳 Setting up disbursement method...")
            disbursement_result = seller_tools.select_disbursement_method(disbursement_data)
            
            if disbursement_result.get("success"):
                st.success(f"✅ Disbursement method configured: {disbursement_result.get('message', 'Successfully configured')}")
            else:
                error_msg = disbursement_result.get('error') or disbursement_result.get('message') or 'Unknown error occurred'
                st.error(f"❌ Disbursement setup failed: {error_msg}")
                return
            
            # Display comprehensive registration summary
            st.success("✅ All validation checks passed!")
            
            st.markdown("---")
            st.subheader("📋 Registration Summary")
            
            # Business Information
            with st.expander("🏢 Business Information", expanded=True):
                business = registration_data["business_info"]
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Business Name:** {business.get('business_name', 'N/A')}")
                    st.write(f"**Business Type:** {business.get('business_type', 'N/A')}")
                    st.write(f"**Email:** {business.get('business_email', 'N/A')}")
                    st.write(f"**Phone:** {business.get('business_phone', 'N/A')}")
                with col2:
                    st.write(f"**Address:** {business.get('business_address', 'N/A')}")
                    st.write(f"**Website:** {business.get('website_url', 'N/A')}")
                    st.write(f"**Tax ID:** {business.get('tax_id', 'N/A')}")
            
            # Contact Information
            with st.expander("👤 Contact Information"):
                contact = registration_data["contact_info"]
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Primary Contact:**")
                    st.write(f"Name: {contact.get('primary_contact_name', 'N/A')}")
                    st.write(f"Email: {contact.get('primary_contact_email', 'N/A')}")
                    st.write(f"Phone: {contact.get('primary_contact_phone', 'N/A')}")
                with col2:
                    if contact.get('secondary_contact_name'):
                        st.write("**Secondary Contact:**")
                        st.write(f"Name: {contact.get('secondary_contact_name', 'N/A')}")
                        st.write(f"Email: {contact.get('secondary_contact_email', 'N/A')}")
                        st.write(f"Phone: {contact.get('secondary_contact_phone', 'N/A')}")
            
            # Tax Information
            with st.expander("📋 Tax Information", expanded=True):
                tax = registration_data["tax_info"]
                st.write(f"**Tax Classification:** {tax.get('tax_classification', 'N/A')}")
                if tax.get('w9_form_url'):
                    st.write(f"**W-9 Form:** Provided")
                else:
                    st.warning("⚠️ W-9 form not provided - will be required during AWS review")
            
            # Banking Information
            with st.expander("🏦 Banking Information", expanded=True):
                banking = registration_data["banking_info"]
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Bank Name:** {banking.get('bank_name', 'N/A')}")
                    st.write(f"**Account Type:** {banking.get('account_type', 'N/A')}")
                    st.write(f"**Account Holder:** {banking.get('account_holder_name', 'N/A')}")
                with col2:
                    # Mask sensitive information
                    routing = banking.get('routing_number', 'N/A')
                    if routing and routing != 'N/A':
                        routing_masked = f"****{routing[-4:]}"
                    else:
                        routing_masked = 'N/A'
                    
                    account = banking.get('account_number', 'N/A')
                    if account and account != 'N/A':
                        account_masked = f"****{account[-4:]}"
                    else:
                        account_masked = 'N/A'
                    
                    st.write(f"**Routing Number:** {routing_masked}")
                    st.write(f"**Account Number:** {account_masked}")
            
            # Disbursement Method
            with st.expander("💳 Disbursement Method"):
                st.write(f"**Method:** ACH Direct Deposit")
                st.write(f"**Status:** Configured")
            
            st.markdown("---")
            
            # Final success message
            st.balloons()
            st.success("""
            🎉 **Seller Registration Completed Successfully!**
            
            Your seller registration has been submitted to AWS for review.
            
            **Next Steps:**
            1. AWS will review your information (2-3 business days)
            2. You'll receive email updates on the status
            3. Once approved, you can create product listings
            
            **What happens now:**
            - Identity verification process will begin
            - Banking information will be verified
            - You'll receive confirmation emails
            """)
            
            # Store registration completion and data in session state
            st.session_state.registration_completed = True
            st.session_state.registration_data = registration_data  # Store the registration data
            st.session_state.current_step = "registration_complete"
            
            if st.button("📧 Check Registration Status"):
                st.rerun()
    
    except Exception as e:
        st.error(f"❌ Registration processing failed: {str(e)}")

def init_session_state():
    """Initialize session state"""
    print("[DEBUG] Initializing session state...")
    
    if 'current_step' not in st.session_state:
        st.session_state.current_step = "credentials"
    
    if 'orchestrator' not in st.session_state:
        # Use Strands agent
        from agent.strands_marketplace_agent import StrandsMarketplaceAgent
        strands_agent = StrandsMarketplaceAgent()
        st.session_state.orchestrator = strands_agent.orchestrator
        print("[DEBUG] Orchestrator initialized")
    
    # Add seller registration components
    if 'seller_registration_tools' not in st.session_state:
        st.session_state.seller_registration_tools = SellerRegistrationTools()
        print("[DEBUG] Seller registration tools initialized")
    
    if 'seller_registration_agent' not in st.session_state:
        # Initialize without credentials - will be updated when credentials are provided
        st.session_state.seller_registration_agent = SellerRegistrationAgent()
        print("[DEBUG] Seller registration agent initialized")
    
    # Initialize agents from agents folder
    print(f"[DEBUG] ServerlessSaasIntegrationAgent available: {ServerlessSaasIntegrationAgent is not None}")
    if ServerlessSaasIntegrationAgent and 'serverless_saas_integration_agent' not in st.session_state:
        try:
            # Pass the entire strands agent, not just the orchestrator
            from agent.strands_marketplace_agent import StrandsMarketplaceAgent
            strands_agent = StrandsMarketplaceAgent()
            st.session_state.serverless_saas_integration_agent = ServerlessSaasIntegrationAgent(strands_agent=strands_agent)
            print("[DEBUG] Serverless SaaS Integration agent initialized successfully")
        except Exception as e:
            print(f"[DEBUG] Error initializing ServerlessSaasIntegrationAgent: {e}")
            st.session_state.serverless_saas_integration_agent = None
    
    print(f"[DEBUG] BuyerExperienceAgent available: {BuyerExperienceAgent is not None}")
    if BuyerExperienceAgent and 'buyer_experience_agent' not in st.session_state:
        try:
            st.session_state.buyer_experience_agent = BuyerExperienceAgent(strands_agent=st.session_state.orchestrator)
            print("[DEBUG] Buyer Experience agent initialized successfully")
        except Exception as e:
            print(f"[DEBUG] Error initializing BuyerExperienceAgent: {e}")
            st.session_state.buyer_experience_agent = None
    
    print(f"[DEBUG] MeteringAgent available: {MeteringAgent is not None}")
    if MeteringAgent and 'metering_agent' not in st.session_state:
        try:
            st.session_state.metering_agent = MeteringAgent(strands_agent=st.session_state.orchestrator)
            print("[DEBUG] Metering agent initialized successfully")
        except Exception as e:
            print(f"[DEBUG] Error initializing MeteringAgent: {e}")
            st.session_state.metering_agent = None
    
    print(f"[DEBUG] PublicVisibilityAgent available: {PublicVisibilityAgent is not None}")
    if PublicVisibilityAgent and 'public_visibility_agent' not in st.session_state:
        try:
            st.session_state.public_visibility_agent = PublicVisibilityAgent(strands_agent=st.session_state.orchestrator)
            print("[DEBUG] Public Visibility agent initialized successfully")
        except Exception as e:
            print(f"[DEBUG] Error initializing PublicVisibilityAgent: {e}")
            st.session_state.public_visibility_agent = None
    
    print(f"[DEBUG] WorkflowOrchestrator available: {WorkflowOrchestrator is not None}")
    if WorkflowOrchestrator and 'workflow_orchestrator_agent' not in st.session_state:
        try:
            # Pass the entire strands agent, not just the orchestrator
            from agent.strands_marketplace_agent import StrandsMarketplaceAgent
            strands_agent = StrandsMarketplaceAgent()
            st.session_state.workflow_orchestrator_agent = WorkflowOrchestrator(strands_agent=strands_agent)
            print("[DEBUG] Workflow Orchestrator agent initialized successfully")
        except Exception as e:
            print(f"[DEBUG] Error initializing WorkflowOrchestrator: {e}")
            st.session_state.workflow_orchestrator_agent = None
    
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    if 'product_context' not in st.session_state:
        st.session_state.product_context = {}
    
    if 'current_step' not in st.session_state:
        st.session_state.current_step = "welcome"
        print("[DEBUG] Set current_step to welcome")
    else:
        print(f"[DEBUG] Existing current_step: {st.session_state.current_step}")
    
    # Add seller registration state
    if 'seller_status' not in st.session_state:
        st.session_state.seller_status = None
    
    if 'registration_data' not in st.session_state:
        st.session_state.registration_data = {}
    
    # Workflow state tracking for agents
    if 'workflow_data' not in st.session_state:
        st.session_state.workflow_data = {
            'product_id': None,
            'pricing_dimensions': None,
            'email': None,
            'stack_id': None,
            'fulfillment_url': None,
            'lambda_function_name': None
        }
        print("[DEBUG] Initialized workflow_data")
    else:
        print(f"[DEBUG] Existing workflow_data: {st.session_state.workflow_data}")


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


def welcome_screen():
    """Welcome screen with seller status check and workflow selection"""
    st.title("🚀 AWS Marketplace Seller Registration & Listing Creation")
    
    st.markdown("""
    ### Welcome! Let's get you set up on AWS Marketplace.
    
    This comprehensive workflow will:
    
    **Step 1: Seller Registration** 🏢
    - Check your current seller status
    - Guide you through AWS Marketplace seller registration
    - Handle business profile, tax information, and banking setup
    
    **Step 2: Listing Creation** 🛍️
    - Analyze your product documentation
    - Generate all required listing content automatically
    - Select optimal pricing models and dimensions
    - Create and publish your marketplace listing
    
    **Complete end-to-end solution!**
    """)
    
    st.divider()
    
    # Check if seller profile has been validated
    if not st.session_state.get('seller_profile_validated', False):
        st.warning("""
        ⚠️ **Seller Profile Validation Required**
        
        Before creating products, you must validate your tax and payment information.
        """)
        
        st.info("""
        **Please complete these steps:**
        
        1. Go back to the credentials screen
        2. Verify your tax and payment information in the AWS portal
        3. Confirm validation by checking both boxes
        4. Return here to create products
        """)
        
        if st.button("← Back to Credentials", type="primary", use_container_width=True):
            st.session_state.current_step = "credentials"
            st.rerun()
        
        return
    
    # Seller profile is validated - proceed
    st.success("✅ **Seller Status: APPROVED & VALIDATED**")
    st.info("Your tax and payment information are confirmed. You can now create product listings!")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Back to Credentials", use_container_width=True):
            st.session_state.current_step = "credentials"
            st.rerun()
    
    with col2:
        if st.button("Start AI-Guided Creation →", type="primary", use_container_width=True):
            st.session_state.current_step = "gather_context"
            st.rerun()
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Re-check Status", use_container_width=True):
                    st.session_state.seller_status = None
                    st.rerun()
            
            with col2:
                if st.button("View Management Console", use_container_width=True):
                    st.markdown("[Open AWS Marketplace Management Console](https://console.aws.amazon.com/marketplace/management/)")
        



def gather_context_screen():
    """Gather product context from user"""
    st.title("📄 Product Information")
    
    # Amazon-style breadcrumb
    st.markdown('<div style="color: #565959; font-size: 12px; margin-bottom: 16px;">AWS Marketplace > Listing Creation > Product Information</div>', unsafe_allow_html=True)
    
    # Add navigation buttons at the top
    show_navigation_buttons(show_back=True, show_home=True, back_step="credentials")
    st.divider()
    
    st.markdown("""
    **Provide your product information** so our AI can analyze it and create your marketplace listing with accurate details and compelling descriptions.
    """)
    
    st.markdown('<div class="product-section">', unsafe_allow_html=True)
    st.write("**📋 Product URLs:**")
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
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close product-section container


def analyze_product_screen():
    """AI analyzes product and generates suggestions"""
    st.title("🔍 Analyzing Your Product...")
    
    # Add navigation buttons at the top
    show_navigation_buttons(show_back=True, show_home=True, back_step="gather_context")
    st.divider()
    
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
    
    # Add navigation buttons at the top
    show_navigation_buttons(show_back=True, show_home=True, back_step="analyze_product")
    st.divider()
    
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
            if not dim_name or not dim_key or not dim_description:
                st.error("All three fields (Dimension Name, Dimension Key, and Description) are mandatory")
            else:
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
            
            # Validate dimensions based on pricing model
            dim_types = set(dim["type"] for dim in all_dimensions)
            
            if pricing_model == "Contract":
                # Contract model: at least one Entitled dimension is mandatory
                if "Entitled" not in dim_types:
                    st.error("Contract model requires at least one Entitled dimension")
                    return
                # Contract model: should not have Metered dimensions
                if "Metered" in dim_types:
                    st.error("Contract model should only have Entitled dimensions, not Metered dimensions")
                    return
            
            elif pricing_model == "Usage":
                # Usage model: only Metered dimensions allowed, at least one is mandatory
                if "Metered" not in dim_types:
                    st.error("Usage model requires at least one Metered dimension")
                    return
                if "Entitled" in dim_types:
                    st.error("Usage model should only have Metered dimensions, not Entitled dimensions")
                    return
            
            elif pricing_model == "Contract with Consumption":
                # Hybrid model: one Entitled and one Metered dimension are mandatory
                if "Entitled" not in dim_types or "Metered" not in dim_types:
                    st.error("Contract with Consumption requires at least one Entitled dimension and one Metered dimension")
                    return
            
            # Validate contract durations for contract and hybrid pricing
            if pricing_model in ["Contract", "Contract with Consumption"] and not contract_durations:
                st.error("Please select at least one contract duration")
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


def create_listing_screen():
    """Create the listing using the orchestrator"""
    
    # Add navigation buttons at the top
    show_navigation_buttons(show_back=True, show_home=True, back_step="review_suggestions")
    st.divider()
    
    # Check if listing is already created to avoid re-execution
    if 'listing_created' in st.session_state and st.session_state.listing_created:
        show_listing_success()
        return
    
    st.title("🚀 Creating Your Listing...")
    
    listing_data = st.session_state.listing_data
    orchestrator = st.session_state.orchestrator
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Stage 1: Product Information
    status_text.text("📦 Creating product...")
    progress_bar.progress(10)
    
    # Set Stage 1 data
    orchestrator.set_stage_data("product_title", listing_data["product_title"])
    orchestrator.set_stage_data("logo_s3_url", listing_data["logo_s3_url"])
    orchestrator.set_stage_data("short_description", listing_data["short_description"])
    orchestrator.set_stage_data("long_description", listing_data["long_description"])
    orchestrator.set_stage_data("highlights", listing_data["highlights"])
    orchestrator.set_stage_data("support_email", listing_data["support_email"])
    orchestrator.set_stage_data("support_description", listing_data["support_description"])
    orchestrator.set_stage_data("categories", listing_data["categories"])
    orchestrator.set_stage_data("search_keywords", listing_data["search_keywords"])
    
    result1 = orchestrator.complete_current_stage()
    
    if result1.get("status") != "complete":
        st.error(f"Failed to create product: {result1.get('message')}")
        return
    
    progress_bar.progress(25)
    
    # Stage 2: Fulfillment
    status_text.text("🔗 Adding fulfillment options...")
    orchestrator.set_stage_data("fulfillment_url", listing_data["fulfillment_url"])
    orchestrator.set_stage_data("quick_launch_enabled", False)
    
    result2 = orchestrator.complete_current_stage()
    progress_bar.progress(40)
    
    # Stage 3: Pricing Dimensions
    status_text.text("💰 Configuring pricing...")
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
    
    result3 = orchestrator.complete_current_stage()
    print(f"[DEBUG] Stage 3 result: {result3}")
    print(f"[DEBUG] Current stage after Stage 3: {orchestrator.current_stage}")
    progress_bar.progress(55)
    
    # Stage 4: Price Review
    status_text.text("💵 Applying pricing terms...")
    print(f"[DEBUG] Setting Stage 4 data...")
    
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
    
    print(f"[DEBUG] About to complete Stage 4...")
    print(f"[DEBUG] Stage 4 agent: {orchestrator.get_current_agent()}")
    print(f"[DEBUG] Stage 4 is complete: {orchestrator.check_stage_completion()}")
    result4 = orchestrator.complete_current_stage()
    print(f"[DEBUG] Stage 4 result: {result4}")
    progress_bar.progress(70)
    
    # Stage 5: Refund Policy
    status_text.text("↩️ Setting refund policy...")
    orchestrator.set_stage_data("refund_policy", listing_data["refund_policy"])
    
    result5 = orchestrator.complete_current_stage()
    progress_bar.progress(80)
    
    # Stage 6: EULA
    status_text.text("📄 Configuring EULA...")
    orchestrator.set_stage_data("eula_type", listing_data["eula_type"])
    if listing_data.get("custom_eula_url"):
        orchestrator.set_stage_data("custom_eula_s3_url", listing_data["custom_eula_url"])
    
    result6 = orchestrator.complete_current_stage()
    progress_bar.progress(90)
    
    # Stage 7: Availability
    status_text.text("🌍 Setting availability...")
    
    # Map availability type to orchestrator format
    if listing_data["availability_type"] == "All countries (worldwide)":
        orchestrator.set_stage_data("availability_type", "all_countries")
    elif listing_data["availability_type"] == "All countries except specific ones":
        orchestrator.set_stage_data("availability_type", "all_with_exclusions")
        orchestrator.set_stage_data("excluded_countries", listing_data.get("excluded_countries", []))
    else:  # Only specific countries
        orchestrator.set_stage_data("availability_type", "allowlist_only")
        orchestrator.set_stage_data("allowed_countries", listing_data.get("allowed_countries", []))
    
    result7 = orchestrator.complete_current_stage()
    progress_bar.progress(95)
    
    # Stage 8: Allowlist
    status_text.text("✅ Finalizing...")
    buyer_accounts = listing_data.get("buyer_accounts", [])
    if buyer_accounts:
        orchestrator.set_stage_data("allowlist_account_ids", buyer_accounts)
    
    result8 = orchestrator.complete_current_stage()
    
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
    status_text.text("🎉 Listing created successfully!")
    
    # Mark listing as created to prevent re-execution
    st.session_state.listing_created = True
    st.session_state.created_product_id = product_id
    st.session_state.created_offer_id = offer_id
    st.session_state.created_listing_data = listing_data
    st.session_state.all_stages_successful = all_stages_successful
    st.session_state.published_to_limited = published_to_limited
    
    show_listing_success()

def show_listing_success():
    """Show listing success screen with deployment options"""
    # Get stored data
    product_id = st.session_state.get('created_product_id')
    offer_id = st.session_state.get('created_offer_id')
    listing_data = st.session_state.get('created_listing_data', {})
    all_stages_successful = st.session_state.get('all_stages_successful', False)
    published_to_limited = st.session_state.get('published_to_limited', False)
    
    # Show results
    st.success("🎉 Your AWS Marketplace listing has been created!")
    
    if product_id:
        st.info(f"🆔 **Product ID:** `{product_id}`")
    if offer_id:
        st.info(f"🆔 **Offer ID:** `{offer_id}`")
    
    if all_stages_successful:
        if published_to_limited:
            st.success("📋 **Status:** Limited (published and ready for testing!)")
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
    
    # Add workflow continuation buttons
    st.divider()
    st.subheader("🔧 Continue with SaaS Integration Workflow")
    st.markdown("""
    Your listing is created! Now continue with the complete SaaS integration workflow:
    
    **Next Steps:**
    - **Step 3:** Deploy Serverless SaaS Integration
    - **Step 4:** Update Fulfillment URL
    - **Step 5:** Test Buyer Experience
    - **Step 6:** Configure Usage Metering
    - **Step 7:** Submit for Public Visibility
    """)
    
    st.write(f"[DEBUG] About to render workflow continuation buttons")
    st.write(f"[DEBUG] product_id: {product_id}")
    st.write(f"[DEBUG] offer_id: {offer_id}")
    st.write(f"[DEBUG] listing_data keys: {list(listing_data.keys()) if listing_data else 'None'}")
    
    # Simple navigation to SaaS deployment
    deploy_saas = st.checkbox("🔧 Deploy SaaS Integration", help="Check this to go to SaaS deployment screen")
    
    if deploy_saas:
        # Store workflow data
        st.session_state.workflow_data.update({
            'product_id': product_id,
            'offer_id': offer_id,
            'fulfillment_url': listing_data.get('fulfillment_url'),
            'pricing_model': listing_data.get('ui_pricing_model', 'Contract'),
            'dimensions': listing_data.get('dimensions', [])
        })
        
        # Navigate to SaaS deployment screen
        st.session_state.current_step = "saas_deployment"
        st.rerun()
    
    st.divider()
    if st.button("Create Another Listing", use_container_width=True):
        # Clear listing creation flags
        if 'listing_created' in st.session_state:
            del st.session_state.listing_created
        if 'created_product_id' in st.session_state:
            del st.session_state.created_product_id
        if 'created_offer_id' in st.session_state:
            del st.session_state.created_offer_id
        if 'created_listing_data' in st.session_state:
            del st.session_state.created_listing_data
        st.session_state.current_step = "gather_context"
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
                value=data.get("pan_number", tax_id),
                placeholder="ABCDE1234F",
                help="Permanent Account Number (PAN)"
            )
        
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
    
    # Action buttons
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
    
    **2. Complete the registration process in the portal**
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


def saas_deployment_screen():
    """Simple SaaS deployment screen with email input"""
    st.title("🚀 Deploy SaaS Integration")
    
    # Add navigation buttons at the top
    show_navigation_buttons(show_back=True, show_home=True, back_step="create_listing")
    st.divider()
    
    workflow_data = st.session_state.workflow_data
    
    # Show product information
    with st.expander("📋 Product Information", expanded=True):
        st.write(f"**Product ID:** {workflow_data.get('product_id', 'N/A')}")
        st.write(f"**Pricing Model:** {workflow_data.get('pricing_model', 'N/A')}")
        st.write(f"**Fulfillment URL:** {workflow_data.get('fulfillment_url', 'N/A')}")
    
    st.markdown("""
    Deploy the serverless infrastructure for your AWS Marketplace SaaS integration.
    This will create all necessary AWS resources using CloudFormation.
    """)
    
    # Email input
    st.subheader("📧 Configuration")
    email = st.text_input(
        "Email for SNS Notifications *",
        placeholder="admin@yourcompany.com",
        help="This email will receive AWS Marketplace subscription notifications"
    )
    
    # AWS Credentials
    st.subheader("🔑 AWS Credentials")
    col1, col2 = st.columns(2)
    with col1:
        aws_access_key = st.text_input("AWS Access Key ID *", type="password")
        aws_secret_key = st.text_input("AWS Secret Access Key *", type="password")
    with col2:
        aws_session_token = st.text_input("AWS Session Token (optional)", type="password")
        st.caption("Optional for temporary credentials")
    
    st.divider()
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← Back", key="saas_back_btn"):
            st.session_state.current_step = "create_listing"
            st.rerun()
    
    with col2:
        if st.button("🚀 Deploy CloudFormation Template", type="primary", use_container_width=True):
            if not email or not aws_access_key or not aws_secret_key:
                st.error("Please provide email and AWS credentials")
                return
            
            # Deploy using agent
            with st.spinner("Deploying CloudFormation template... This may take 5-10 minutes."):
                agent = st.session_state.serverless_saas_integration_agent
                
                try:
                    # Create boto3 session
                    session = boto3.Session(
                        aws_access_key_id=aws_access_key,
                        aws_secret_access_key=aws_secret_key,
                        aws_session_token=aws_session_token if aws_session_token else None,
                        region_name='us-east-1'
                    )
                    
                    # Deploy with product data
                    result = agent.deploy_integration_with_session(
                        session=session,
                        product_id=workflow_data.get('product_id'),
                        email=email,
                        pricing_dimensions=workflow_data.get('dimensions', [])
                    )
                    
                    if result.get('success') or result.get('stack_id'):
                        st.success("✅ SaaS Integration deployed successfully!")
                        st.info(f"**Stack ID:** {result.get('stack_id', 'N/A')}")
                        st.info("📧 Check your email to confirm SNS subscription")
                        
                        if st.button("Continue to Full Workflow →", type="primary"):
                            st.session_state.current_step = "workflow_orchestrator"
                            st.rerun()
                    else:
                        st.error(f"❌ Deployment failed: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ Deployment error: {str(e)}")


def serverless_integration_screen():
    """Serverless SaaS Integration workflow"""
    print(f"[DEBUG] Entering serverless_integration_screen")
    print(f"[DEBUG] Current step: {st.session_state.current_step}")
    print(f"[DEBUG] Workflow data: {st.session_state.workflow_data}")
    
    st.title("🔧 Serverless SaaS Integration")
    
    st.markdown("""
    Deploy the complete serverless infrastructure for your AWS Marketplace SaaS integration using CloudFormation.
    """)
    
    workflow_data = st.session_state.workflow_data
    print(f"[DEBUG] Retrieved workflow_data: {workflow_data}")
    
    # Show current product info
    with st.expander("📋 Product Information", expanded=True):
        st.write(f"**Product ID:** {workflow_data.get('product_id', 'N/A')}")
        st.write(f"**Offer ID:** {workflow_data.get('offer_id', 'N/A')}")
        st.write(f"**Fulfillment URL:** {workflow_data.get('fulfillment_url', 'N/A')}")
        st.write(f"**Pricing Model:** {workflow_data.get('pricing_model', 'N/A')}")
        if workflow_data.get('dimensions'):
            st.write(f"**Pricing Dimensions:** {len(workflow_data.get('dimensions', []))} configured")
            for i, dim in enumerate(workflow_data.get('dimensions', [])):
                st.write(f"  - {dim.get('name', 'Unknown')} ({dim.get('key', 'unknown')})")
    
    # AWS Credentials
    st.subheader("🔑 AWS Credentials")
    st.caption("Required for CloudFormation deployment")
    
    col1, col2 = st.columns(2)
    with col1:
        aws_access_key = st.text_input("AWS Access Key ID *", type="password")
        aws_secret_key = st.text_input("AWS Secret Access Key *", type="password")
    with col2:
        aws_session_token = st.text_input("AWS Session Token (optional)", type="password")
        st.write("")
        st.caption("Session token is optional for temporary credentials")
    
    # Integration form
    st.subheader("⚙️ Configuration")
    
    col1, col2 = st.columns(2)
    with col1:
        email = st.text_input("Email for SNS notifications *", placeholder="admin@yourcompany.com", help="This email will receive AWS Marketplace notifications")
        stack_name = st.text_input("CloudFormation Stack Name *", value=f"marketplace-saas-{workflow_data.get('product_id', 'integration')[:8]}")
    
    with col2:
        aws_region = st.selectbox("AWS Region *", options=["us-east-1", "us-west-2", "eu-west-1"], index=0)
        st.write("")
        st.caption("Infrastructure will be deployed in the selected region")
    
    # Show what will be deployed
    with st.expander("🛠️ Infrastructure Components", expanded=False):
        st.markdown("""
        **CloudFormation will deploy:**
        - 🗄 DynamoDB tables for subscriptions and metering
        - λ Lambda function for usage metering
        - 🔗 API Gateway for fulfillment
        - 📧 SNS topic for notifications
        - 🔐 IAM roles and policies
        """)
    
    st.divider()
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Back"):
            print(f"[DEBUG] Back button clicked in serverless_integration_screen")
            st.session_state.current_step = "create_listing"
            st.rerun()
    
    with col2:
        if st.button("Deploy CloudFormation Stack 🚀", type="primary", use_container_width=True):
            if not all([email, stack_name, aws_access_key, aws_secret_key]):
                st.error("Please fill in all required fields including AWS credentials")
                return
            
            # Store configuration
            st.session_state.workflow_data.update({
                'email': email,
                'stack_name': stack_name,
                'aws_region': aws_region
            })
            
            # Deploy using agent
            print(f"[DEBUG] About to deploy CloudFormation infrastructure...")
            print(f"[DEBUG] Agent available: {st.session_state.get('serverless_saas_integration_agent') is not None}")
            
            with st.spinner("Deploying CloudFormation stack... This may take 5-10 minutes."):
                agent = st.session_state.serverless_saas_integration_agent
                print(f"[DEBUG] Agent: {agent}")
                
                print(f"[DEBUG] Deploy parameters:")
                print(f"  email: {email}")
                print(f"  stack_name: {stack_name}")
                print(f"  product_id: {workflow_data.get('product_id')}")
                print(f"  pricing_dimensions: {workflow_data.get('dimensions', [])}")
                
                try:
                    # CRITICAL: Make sure the agent has access to the product data
                    if agent.strands_agent and agent.strands_agent.orchestrator:
                        agent.strands_agent.orchestrator.product_id = workflow_data.get('product_id')
                        print(f"[DEBUG] Updated agent product_id: {workflow_data.get('product_id')}")
                    
                    # Create boto3 session and call existing deploy method
                    session = boto3.Session(
                        aws_access_key_id=aws_access_key,
                        aws_secret_access_key=aws_secret_key,
                        aws_session_token=aws_session_token,
                        region_name='us-east-1'
                    )
                    
                    # Pass the actual product data from listing creation
                    result = agent.deploy_integration_with_session(
                        session=session,
                        product_id=workflow_data.get('product_id'),
                        email=email,
                        pricing_dimensions=workflow_data.get('dimensions', [])
                    )
                    print(f"[DEBUG] Deploy result: {result}")
                except Exception as e:
                    print(f"[DEBUG] Deploy error: {e}")
                    import traceback
                    print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
                    result = {'success': False, 'error': str(e)}
            
            if result.get('stack_id') or not result.get('error'):
                st.success("✅ AWS Marketplace SaaS Integration deployed successfully!")
                
                # Show deployment results
                with st.expander("📋 Deployment Results", expanded=True):
                    if result.get('stack_id'):
                        st.write(f"**Stack ID:** {result.get('stack_id')}")
                    if result.get('workflow_result'):
                        st.write(f"**Workflow Status:** {result.get('workflow_result', {}).get('status', 'Unknown')}")
                    st.write(f"**SNS Confirmed:** {'Yes' if result.get('sns_confirmed') else 'No'}")
                
                # Update workflow data with deployment results
                st.session_state.workflow_data.update({
                    'stack_id': result.get('stack_id'),
                    'deployment_complete': True,
                    'sns_confirmed': result.get('sns_confirmed', False)
                })
                
                st.info("📧 **Next Step:** Check your email to confirm the SNS subscription for marketplace notifications.")
                
                if st.button("Continue to Full Workflow →", type="primary"):
                    st.session_state.current_step = "workflow_orchestrator"
                    st.rerun()
            else:
                st.error(f"❌ SaaS Integration deployment failed: {result.get('error', 'Unknown error')}")
                
                # Show troubleshooting tips
                with st.expander("🔧 Troubleshooting", expanded=True):
                    st.markdown("""
                    **Common issues:**
                    - Check AWS credentials have CloudFormation permissions
                    - Ensure stack name is unique in your account
                    - Verify you have IAM permissions to create roles
                    - Check AWS service limits in your region
                    """)


def workflow_orchestrator_screen():
    """Complete workflow orchestrator"""
    print(f"[DEBUG] Entering workflow_orchestrator_screen")
    print(f"[DEBUG] Current step: {st.session_state.current_step}")
    print(f"[DEBUG] Workflow data: {st.session_state.workflow_data}")
    
    st.title("🌐 Complete Workflow Orchestrator")
    
    st.markdown("""
    Execute the complete AWS Marketplace workflow:
    1. ✅ Seller Registration (Complete)
    2. ✅ Listing Creation (Complete)
    3. ✅ Serverless SaaS Integration (Complete)
    4. 🔄 Fulfillment URL Update
    5. 🧪 Buyer Experience Testing
    6. 📈 Usage Metering Configuration
    7. 🌍 Public Visibility Request
    """)
    
    workflow_data = st.session_state.workflow_data
    
    # Show current status
    with st.expander("📋 Workflow Status", expanded=True):
        st.write(f"**Product ID:** {workflow_data.get('product_id', 'N/A')}")
        st.write(f"**Stack Name:** {workflow_data.get('stack_name', 'N/A')}")
        st.write(f"**Email:** {workflow_data.get('email', 'N/A')}")
        st.write(f"**Lambda Function:** {workflow_data.get('lambda_function_name', 'N/A')}")
    
    # AWS Credentials
    st.subheader("🔑 AWS Credentials")
    st.caption("Required for workflow execution")
    
    col1, col2 = st.columns(2)
    with col1:
        access_key = st.text_input("AWS Access Key ID *", type="password")
        secret_key = st.text_input("AWS Secret Access Key *", type="password")
    with col2:
        session_token = st.text_input("AWS Session Token (optional)", type="password")
        st.write("")
        st.caption("Session token is optional for temporary credentials")
    
    st.divider()
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Back"):
            print(f"[DEBUG] Back button clicked in workflow_orchestrator_screen")
            st.session_state.current_step = "serverless_integration"
            st.rerun()
    
    with col2:
        if st.button("Execute Complete Workflow 🎆", type="primary", use_container_width=True):
            if not all([access_key, secret_key]):
                st.error("Please provide AWS credentials")
                return
            
            # Execute workflow using orchestrator agent
            print(f"[DEBUG] About to execute full workflow...")
            print(f"[DEBUG] Agent available: {st.session_state.get('workflow_orchestrator_agent') is not None}")
            
            with st.spinner("Executing complete workflow..."):
                agent = st.session_state.workflow_orchestrator_agent
                print(f"[DEBUG] Agent: {agent}")
                
                workflow_params = {
                    'access_key': access_key,
                    'secret_key': secret_key,
                    'session_token': session_token if session_token else None,
                    'lambda_function_name': workflow_data.get('lambda_function_name')
                }
                print(f"[DEBUG] Workflow parameters: {workflow_params}")
                
                try:
                    # CRITICAL: Make sure the agent has access to the product data
                    if agent.strands_agent and agent.strands_agent.orchestrator:
                        agent.strands_agent.orchestrator.product_id = workflow_data.get('product_id')
                        print(f"[DEBUG] Updated agent product_id: {workflow_data.get('product_id')}")
                    
                    result = agent.execute_full_workflow(**workflow_params)
                    print(f"[DEBUG] Workflow result: {result}")
                except Exception as e:
                    print(f"[DEBUG] Workflow error: {e}")
                    result = {'status': 'error', 'error': str(e)}
            
            if result.get('status') == 'success':
                st.success("🎉 Complete workflow executed successfully!")
                st.balloons()
                
                st.markdown("""
                ### ✅ Workflow Complete!
                
                Your AWS Marketplace SaaS integration is now fully configured:
                
                - ✅ **Seller Registration:** Approved
                - ✅ **Product Listing:** Created and published
                - ✅ **Infrastructure:** Deployed
                - ✅ **Fulfillment URL:** Updated
                - ✅ **Buyer Experience:** Tested
                - ✅ **Usage Metering:** Configured
                - ✅ **Public Visibility:** Submitted
                
                Your product is now ready for customers!
                """)
                
                if st.button("Start New Workflow"):
                    st.session_state.clear()
                    st.rerun()
            else:
                st.error(f"❌ Workflow failed: {result.get('error', 'Unknown error')}")
                st.write("**Details:**")
                st.json(result)


def show_navigation_buttons(show_back=True, show_home=True, back_step=None):
    """
    Show navigation buttons (Back and Home)
    
    Args:
        show_back: Whether to show the back button
        show_home: Whether to show the home button
        back_step: The step to go back to (if None, goes to previous step in sequence)
    """
    col1, col2, col3 = st.columns([1, 1, 4])
    
    with col1:
        if show_home:
            if st.button("🏠 Home", help="Go to AWS Credentials page"):
                st.session_state.current_step = "credentials"
                st.rerun()
    
    with col2:
        if show_back:
            # Define step sequence for back navigation
            step_sequence = [
                "credentials",
                "registration_details", 
                "registration_complete",
                "welcome",
                "seller_registration",
                "registration_portal",
                "gather_context",
                "analyze_product",
                "review_suggestions",
                "create_listing",
                "saas_deployment"
            ]
            
            current_step = st.session_state.current_step
            
            if back_step:
                previous_step = back_step
            else:
                # Find previous step in sequence
                try:
                    current_index = step_sequence.index(current_step)
                    previous_step = step_sequence[current_index - 1] if current_index > 0 else "credentials"
                except ValueError:
                    previous_step = "credentials"
            
            if st.button("⬅️ Back", help=f"Go back to previous step"):
                st.session_state.current_step = previous_step
                st.rerun()


def main():
    """Main app logic"""
    print(f"[DEBUG] Main function called")
    print(f"[DEBUG] Current step at start: {st.session_state.get('current_step', 'None')}")
    
    init_session_state()
    
    print(f"[DEBUG] After init_session_state, current step: {st.session_state.get('current_step', 'None')}")
    
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
            "registration_details": "📝 Registration",
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
        
        st.divider()
        
        # Global clear data button
        if st.button("🗑️ Clear All Data", help="Clear all stored data and start fresh", key="sidebar_clear_data"):
            st.session_state.show_sidebar_clear_confirmation = True
        
        # Show confirmation in sidebar if requested
        if st.session_state.get('show_sidebar_clear_confirmation', False):
            st.warning("⚠️ Clear ALL data?")
            col_s1, col_s2 = st.columns(2)
            
            with col_s1:
                if st.button("✅ Yes", key="confirm_sidebar_clear"):
                    # Clear all session state data
                    keys_to_clear = [
                        'aws_credentials', 
                        'account_validation', 
                        'seller_status',
                        'product_context',
                        'ai_suggestions',
                        'listing_data',
                        'workflow_data',
                        'registration_completed',
                        'show_sidebar_clear_confirmation'
                    ]
                    for key in keys_to_clear:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    # Reset to credentials step
                    st.session_state.current_step = "credentials"
                    st.success("🗑️ Cleared!")
                    st.rerun()
            
            with col_s2:
                if st.button("❌ No", key="cancel_sidebar_clear"):
                    st.session_state.show_sidebar_clear_confirmation = False
                    st.rerun()
        
        st.markdown('<hr style="margin: 16px 0; border: none; height: 1px; background-color: #d5d9d9;">', unsafe_allow_html=True)
        st.markdown('<div style="text-align: center; color: #565959; font-size: 12px; font-family: Inter, sans-serif;">Powered by Amazon Bedrock | AWS Marketplace</div>', unsafe_allow_html=True)
    
    # Main content
    current_step = st.session_state.current_step
    print(f"[DEBUG] About to render screen for step: {current_step}")
    
    if current_step == "credentials":
        print(f"[DEBUG] Rendering credentials_input_screen")
        credentials_input_screen()
    elif current_step == "registration_details":
        print(f"[DEBUG] Rendering registration_details_screen")
        registration_details_screen()
    elif current_step == "registration_complete":
        st.title("✅ Registration Complete!")
        
        # Add navigation buttons at the top
        show_navigation_buttons(show_back=True, show_home=True, back_step="registration_details")
        st.divider()
        
        st.success("🎉 Your seller registration has been submitted successfully!")
        st.info("📧 AWS will review your information within 2-3 business days.")
        
        # Display comprehensive registration summary
        st.markdown("---")
        st.subheader("� Submiteted Registration Details")
        
        # Check if we have registration data in session state
        if 'registration_data' in st.session_state and st.session_state.registration_data:
            registration_data = st.session_state.registration_data
            
            # Business Information
            with st.expander("🏢 Business Information", expanded=True):
                business = registration_data.get("business_info", {})
                if business:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Business Name:** {business.get('business_name', 'Not provided')}")
                        st.write(f"**Business Type:** {business.get('business_type', 'Not provided')}")
                        st.write(f"**Email:** {business.get('business_email', 'Not provided')}")
                        st.write(f"**Phone:** {business.get('business_phone', 'Not provided')}")
                    with col2:
                        st.write(f"**Address:** {business.get('business_address', 'Not provided')}")
                        st.write(f"**Website:** {business.get('website_url', 'Not provided')}")
                        st.write(f"**Tax ID:** {business.get('tax_id', 'Not provided')}")
                else:
                    st.warning("⚠️ Business information not found in session")
            
            # Contact Information
            with st.expander("👤 Contact Information"):
                contact = registration_data.get("contact_info", {})
                if contact:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Primary Contact:**")
                        st.write(f"• Name: {contact.get('primary_contact_name', 'Not provided')}")
                        st.write(f"• Email: {contact.get('primary_contact_email', 'Not provided')}")
                        st.write(f"• Phone: {contact.get('primary_contact_phone', 'Not provided')}")
                    with col2:
                        if contact.get('secondary_contact_name'):
                            st.write("**Secondary Contact:**")
                            st.write(f"• Name: {contact.get('secondary_contact_name', 'Not provided')}")
                            st.write(f"• Email: {contact.get('secondary_contact_email', 'Not provided')}")
                            st.write(f"• Phone: {contact.get('secondary_contact_phone', 'Not provided')}")
                        else:
                            st.info("No secondary contact provided")
                else:
                    st.warning("⚠️ Contact information not found in session")
            
            # Tax Information
            with st.expander("📋 Tax Information", expanded=True):
                tax = registration_data.get("tax_info", {})
                business = registration_data.get("business_info", {})
                
                if tax or business:
                    # Show business name and address for tax purposes
                    if business.get('business_name'):
                        st.write(f"**Name:** {business.get('business_name')}")
                    if business.get('business_address'):
                        st.write(f"**Address:** {business.get('business_address')}")
                    
                    # Show EIN/Tax ID
                    if business.get('tax_id'):
                        st.write(f"**EIN:** {business.get('tax_id')}")
                    
                    # Show tax classification
                    if tax.get('tax_classification'):
                        st.write(f"**Tax Classification:** {tax.get('tax_classification')}")
                    
                    # Show W-9 status
                    if tax.get('w9_form_url'):
                        st.write(f"**W-9 Form:** ✅ Provided")
                    else:
                        st.warning("⚠️ W-9 form not provided - will be required during AWS review")
                else:
                    st.error("❌ Tax information not found - Registration may be incomplete!")
            
            # Banking Information
            with st.expander("🏦 Banking Information", expanded=True):
                banking = registration_data.get("banking_info", {})
                if banking:
                    # Account holder and bank name
                    st.write(f"**Account Name:** {banking.get('account_holder_name', 'Not provided')}")
                    st.write(f"**Bank Name:** {banking.get('bank_name', 'Not provided')}")
                    
                    # Account details
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Account Type:** {banking.get('account_type', 'Not provided')}")
                        
                        # Mask account number
                        account = banking.get('account_number', '')
                        if account:
                            account_masked = f"****{account[-4:]}" if len(account) >= 4 else "****"
                        else:
                            account_masked = 'Not provided'
                        st.write(f"**Account Number:** {account_masked}")
                        
                    with col2:
                        # Mask routing numbers
                        routing = banking.get('routing_number', '')
                        if routing:
                            routing_masked = f"****{routing[-4:]}" if len(routing) >= 4 else "****"
                        else:
                            routing_masked = 'Not provided'
                        st.write(f"**ABA Routing Number:** {routing_masked}")
                        
                        wire_routing = banking.get('wire_routing_number', routing)
                        if wire_routing and wire_routing != routing:
                            wire_masked = f"****{wire_routing[-4:]}" if len(wire_routing) >= 4 else "****"
                            st.write(f"**Wire Routing Number:** {wire_masked}")
                    
                    # Bank address
                    if banking.get('bank_address'):
                        st.write(f"**Bank Address:** {banking.get('bank_address')}")
                    
                    # SWIFT code for international
                    if banking.get('swift_code'):
                        st.write(f"**SWIFT Code:** {banking.get('swift_code')}")
                    
                    # EIN if provided in banking
                    business = registration_data.get("business_info", {})
                    if business.get('tax_id'):
                        st.write(f"**EIN:** {business.get('tax_id')}")
                else:
                    st.error("❌ Banking information not found - Registration may be incomplete!")
            
            # Disbursement Method
            with st.expander("💳 Disbursement Method"):
                st.write(f"**Method:** ACH Direct Deposit")
                st.write(f"**Status:** ✅ Configured")
                st.info("Payments will be deposited directly to your bank account")
        else:
            st.error("❌ Registration data not found in session. The registration may not have been completed properly.")
            st.info("Please go back and complete the registration form again.")
        
        st.markdown("---")
        
        # Next steps information
        st.subheader("📌 Next Steps")
        st.markdown("""
        **What happens now:**
        1. ✅ Your registration has been submitted to AWS
        2. 🔍 AWS will verify your business information
        3. 🏦 Banking details will be validated
        4. 📧 You'll receive email updates on verification status
        5. ⏱️ Approval typically takes 2-3 business days
        6. 🎉 Once approved, you can create product listings
        
        **Important:**
        - Check your email regularly for updates from AWS
        - Respond promptly to any verification requests
        - Keep your contact information up to date
        """)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Check Status Again", use_container_width=True):
                st.session_state.current_step = "credentials"
                st.rerun()
        with col2:
            if st.button("📄 Create Product Listing", type="primary", use_container_width=True):
                st.session_state.current_step = "gather_context"
                st.rerun()

    elif current_step == "welcome":
        print(f"[DEBUG] Rendering welcome_screen")
        welcome_screen()
    elif current_step == "seller_registration":
        print(f"[DEBUG] Rendering seller_registration_screen")
        seller_registration_screen()
    elif current_step == "registration_portal":
        print(f"[DEBUG] Rendering registration_portal_screen")
        registration_portal_screen()
    elif current_step == "gather_context":
        print(f"[DEBUG] Rendering gather_context_screen")
        gather_context_screen()
    elif current_step == "analyze_product":
        print(f"[DEBUG] Rendering analyze_product_screen")
        analyze_product_screen()
    elif current_step == "review_suggestions":
        print(f"[DEBUG] Rendering review_suggestions_screen")
        review_suggestions_screen()
    elif current_step == "create_listing":
        print(f"[DEBUG] Rendering create_listing_screen")
        create_listing_screen()
    elif current_step == "saas_deployment":
        print(f"[DEBUG] Rendering saas_deployment_screen")
        saas_deployment_screen()
    else:
        print(f"[DEBUG] Unknown step: {current_step}")
        st.error(f"Unknown step: {current_step}")


if __name__ == "__main__":
    main()
