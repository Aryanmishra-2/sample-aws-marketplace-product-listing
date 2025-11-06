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
        text = text.replace(unicode_char, ascii_char)    # R
emove any remaining non-ASCII characters (but preserve newlines and tabs)
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
    """Initialize session state variables"""
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 'gather_context'
    
    if 'product_context' not in st.session_state:
        st.session_state.product_context = {}
    
    if 'ai_suggestions' not in st.session_state:
        st.session_state.ai_suggestions = {}
    
    if 'listing_data' not in st.session_state:
        st.session_state.listing_data = {}


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
        help="Pricing information page"
    )
    
    st.write("**Additional Information:**")
    product_description = st.text_area(
        "Brief Product Description *",
        placeholder="Describe what your product does in 2-3 sentences...",
        help="This helps our AI understand your product better"
    )
    
    target_audience = st.text_input(
        "Target Audience *",
        placeholder="e.g., Software developers, Data scientists, DevOps teams",
        help="Who is your primary customer?"
    )
    
    key_features = st.text_area(
        "Key Features (optional)",
        placeholder="List your main features, one per line...",
        help="What makes your product unique?"
    )
    
    if st.button("🔍 Analyze Product", type="primary"):
        if not website_url or not product_description or not target_audience:
            st.error("❌ Please fill in all required fields (marked with *)")
            return
        
        context = {
            "website_url": website_url,
            "docs_url": docs_url,
            "pricing_url": pricing_url,
            "product_description": product_description,
            "target_audience": target_audience,
            "key_features": key_features
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
            st.write(f"📚 Documentation: {context['docs_url']}")
        if context.get("pricing_url"):
            st.write(f"💰 Pricing: {context['pricing_url']}")
        st.write(f"📝 Description: {context['product_description']}")
        st.write(f"🎯 Target Audience: {context['target_audience']}")
        if context.get("key_features"):
            st.write(f"⭐ Key Features: {context['key_features']}")
    
    # Initialize orchestrator
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = ListingOrchestrator()
    
    orchestrator = st.session_state.orchestrator
    
    # Run AI analysis
    with st.spinner("🤖 AI is analyzing your product and generating marketplace content..."):
        try:
            # Analyze the product
            analysis_result = orchestrator.analyze_product_from_context(context)
            
            if analysis_result.get('success'):
                st.session_state.ai_suggestions = analysis_result.get('suggestions', {})
                
                st.success("🎉 Analysis complete! Review the suggestions on the next screen.")
                
                if st.button("Review Suggestions →", type="primary"):
                    st.session_state.current_step = "review_suggestions"
                    st.rerun()
            else:
                st.error(f"❌ Analysis failed: {analysis_result.get('error', 'Unknown error')}")
                if st.button("← Back to Product Info"):
                    st.session_state.current_step = "gather_context"
                    st.rerun()
                    
        except Exception as e:
            st.error(f"❌ Error during analysis: {str(e)}")
            if st.button("← Back to Product Info"):
                st.session_state.current_step = "gather_context"
                st.rerun()


def review_suggestions_screen():
    """Review and edit AI-generated suggestions"""
    st.title("📝 Review AI-Generated Content")
    
    st.markdown("""
    Review the AI-generated content below. You can edit any field before creating your listing.
    """)
    
    suggestions = st.session_state.ai_suggestions
    
    if not suggestions:
        st.error("❌ No suggestions found. Please go back and analyze your product first.")
        if st.button("← Back to Analysis"):
            st.session_state.current_step = "analyze_product"
            st.rerun()
        return
    
    # Product Title
    st.subheader("📝 Product Title")
    product_title = st.text_input(
        "Product Title",
        value=suggestions.get('product_title', ''),
        help="Keep it concise and descriptive (max 120 characters)"
    )
    
    # Short Description
    st.subheader("📄 Short Description")
    short_description = st.text_area(
        "Short Description",
        value=suggestions.get('short_description', ''),
        help="Brief overview for search results (max 120 characters)",
        max_chars=120
    )
    
    # Long Description
    st.subheader("📖 Long Description")
    long_description = st.text_area(
        "Long Description",
        value=suggestions.get('long_description', ''),
        help="Detailed product description (max 2000 characters)",
        height=200,
        max_chars=2000
    )
    
    # Categories
    st.subheader("🏷️ Categories")
    col1, col2 = st.columns(2)
    
    with col1:
        primary_category = st.selectbox(
            "Primary Category",
            options=[
                "Application Development",
                "Business Applications", 
                "Data & Analytics",
                "DevOps",
                "Infrastructure Software",
                "IoT",
                "Machine Learning",
                "Migration",
                "Monitoring & Logging",
                "Networking",
                "Operating Systems",
                "Security",
                "Storage"
            ],
            index=0 if not suggestions.get('primary_category') else None
        )
    
    with col2:
        secondary_category = st.selectbox(
            "Secondary Category (optional)",
            options=["None"] + [
                "Application Development",
                "Business Applications", 
                "Data & Analytics",
                "DevOps",
                "Infrastructure Software",
                "IoT",
                "Machine Learning",
                "Migration",
                "Monitoring & Logging",
                "Networking",
                "Operating Systems",
                "Security",
                "Storage"
            ],
            index=0
        )
    
    # Keywords
    st.subheader("🔍 Search Keywords")
    keywords = st.text_area(
        "Keywords (comma-separated)",
        value=suggestions.get('keywords', ''),
        help="Keywords that customers might use to find your product"
    )
    
    # Highlights
    st.subheader("⭐ Product Highlights")
    highlights = st.text_area(
        "Key Features/Benefits (one per line)",
        value=suggestions.get('highlights', ''),
        help="Up to 3 key selling points",
        height=100
    )
    
    # Support Information
    st.subheader("🛠️ Support Information")
    col3, col4 = st.columns(2)
    
    with col3:
        support_description = st.text_area(
            "Support Description",
            value=suggestions.get('support_description', ''),
            help="Describe the support you provide"
        )
    
    with col4:
        support_email = st.text_input(
            "Support Email",
            value=suggestions.get('support_email', ''),
            help="Email for customer support"
        )
        
        support_url = st.text_input(
            "Support URL (optional)",
            value=suggestions.get('support_url', ''),
            help="Link to support documentation or portal"
        )
    
    # Pricing Model
    st.subheader("💰 Pricing Model")
    pricing_model = st.selectbox(
        "Pricing Model",
        options=[
            "Free",
            "Paid",
            "Free Trial",
            "Freemium",
            "Bring Your Own License (BYOL)"
        ],
        index=1  # Default to "Paid"
    )
    
    # Usage Instructions
    st.subheader("📋 Usage Instructions")
    usage_instructions = st.text_area(
        "Usage Instructions",
        value=suggestions.get('usage_instructions', ''),
        help="Brief instructions on how to get started",
        height=150
    )
    
    # Action buttons
    col5, col6 = st.columns(2)
    
    with col5:
        if st.button("← Back to Analysis"):
            st.session_state.current_step = "analyze_product"
            st.rerun()
    
    with col6:
        if st.button("Create Listing →", type="primary"):
            # Validate required fields
            if not product_title or not short_description or not long_description:
                st.error("❌ Please fill in all required fields")
                return
            
            # Store the final listing data
            listing_data = {
                "product_title": sanitize_text_for_marketplace(product_title),
                "short_description": sanitize_text_for_marketplace(short_description),
                "long_description": sanitize_text_for_marketplace(long_description),
                "primary_category": primary_category,
                "secondary_category": secondary_category if secondary_category != "None" else "",
                "keywords": sanitize_text_for_marketplace(keywords),
                "highlights": sanitize_text_for_marketplace(highlights),
                "support_description": sanitize_text_for_marketplace(support_description),
                "support_email": support_email,
                "support_url": support_url,
                "pricing_model": pricing_model,
                "usage_instructions": sanitize_text_for_marketplace(usage_instructions)
            }
            
            st.session_state.listing_data = listing_data
            st.session_state.current_step = "create_listing"
            st.rerun()


def create_listing_screen():
    """Create the listing using the orchestrator"""
    st.title("🚀 Creating Your Marketplace Listing")
    
    listing_data = st.session_state.listing_data
    
    # Show summary of what will be created
    with st.expander("📋 Listing Summary", expanded=True):
        st.write(f"**Title:** {listing_data['product_title']}")
        st.write(f"**Category:** {listing_data['primary_category']}")
        st.write(f"**Pricing:** {listing_data['pricing_model']}")
        st.write(f"**Short Description:** {listing_data['short_description']}")
    
    if 'listing_created' not in st.session_state:
        st.session_state.listing_created = False
    
    if not st.session_state.listing_created:
        if st.button("🚀 Create Listing Now", type="primary"):
            with st.spinner("Creating your marketplace listing..."):
                try:
                    orchestrator = st.session_state.orchestrator
                    
                    # Create the listing
                    result = orchestrator.create_marketplace_listing(listing_data)
                    
                    if result.get('success'):
                        st.session_state.listing_created = True
                        st.session_state.listing_result = result
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to create listing: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ Error creating listing: {str(e)}")
    else:
        # Show success message
        result = st.session_state.listing_result
        
        st.success("🎉 Listing Created Successfully!")
        
        if result.get('listing_id'):
            st.info(f"**Listing ID:** {result['listing_id']}")
        
        if result.get('status'):
            st.info(f"**Status:** {result['status']}")
        
        st.markdown("""
        ### ✅ Next Steps:
        1. **Review** your listing in the AWS Marketplace Management Portal
        2. **Upload** product images and additional assets
        3. **Submit** for AWS review (typically takes 2-3 business days)
        4. **Monitor** your listing performance once live
        """)
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Create Another Listing"):
                # Reset session state for new listing
                st.session_state.current_step = 'gather_context'
                st.session_state.product_context = {}
                st.session_state.ai_suggestions = {}
                st.session_state.listing_data = {}
                st.session_state.listing_created = False
                if 'listing_result' in st.session_state:
                    del st.session_state.listing_result
                st.rerun()
        
        with col2:
            st.markdown("[📊 View in AWS Portal](https://aws.amazon.com/marketplace/management/)")
        
        with col3:
            if st.button("📝 Edit This Listing"):
                st.session_state.current_step = "review_suggestions"
                st.session_state.listing_created = False
                st.rerun()


def main():
    """Main app logic"""
    init_session_state()
    
    # Sidebar
    with st.sidebar:
        st.title("🤖 AI-Guided Listing")
        st.divider()
        
        # Show progress
        steps = {
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
        st.caption("Powered by Amazon Bedrock")
    
    # Main content
    current_step = st.session_state.current_step
    
    if current_step == "gather_context":
        gather_context_screen()
    elif current_step == "analyze_product":
        analyze_product_screen()
    elif current_step == "review_suggestions":
        review_suggestions_screen()
    elif current_step == "create_listing":
        create_listing_screen()
    else:
        st.error(f"Unknown step: {current_step}")


if __name__ == "__main__":
    main()