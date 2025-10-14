#!/usr/bin/env python3
"""
Streamlit Form-Based UI for AWS Marketplace Listing Creation

This bypasses LLM data extraction and uses direct form input.
"""

import streamlit as st
from agent.orchestrator import ListingOrchestrator, WorkflowStage
from agent.tools.listing_tools import ListingTools


def init_session_state():
    """Initialize session state"""
    if "orchestrator" not in st.session_state:
        tools = ListingTools()
        st.session_state.orchestrator = ListingOrchestrator(listing_tools=tools)


def complete_stage_with_feedback(orchestrator, stage_name: str, spinner_message: str):
    """Helper function to complete stage and show feedback"""
    with st.spinner(spinner_message):
        result = orchestrator.complete_current_stage()

        if result.get("status") == "complete":
            st.success(f"✅ {stage_name} Complete!")

            # Show API result
            api_result = result.get("api_result", {})
            if api_result:
                if api_result.get("success"):
                    st.success(api_result.get("message", "Changes applied!"))

                    if api_result.get("product_id"):
                        st.info(f"🆔 Product ID: `{api_result['product_id']}`")

                    if api_result.get("offer_id"):
                        st.info(f"🆔 Offer ID: `{api_result['offer_id']}`")

                    if api_result.get("change_set_id"):
                        st.caption(f"Change Set ID: {api_result['change_set_id']}")
                else:
                    st.error(
                        f"❌ API Error: {api_result.get('error', 'Unknown error')}"
                    )
                    st.error(f"Message: {api_result.get('message', 'No message')}")
                    st.json(api_result)  # Debug: show full API result

            st.rerun()
        else:
            st.error(f"❌ Stage Error: {result.get('message')}")
            st.json(result)  # Debug: show full result
            return False

    return True


def stage1_form():
    """Stage 1: Product Information Form"""
    st.header("📦 Stage 1: Product Information")
    st.write("Provide all required information for your SaaS product.")

    with st.form("stage1_form"):
        st.subheader("Required Information")

        # Product Title
        product_title = st.text_input(
            "Product Title *",
            help="5-255 characters",
            placeholder="e.g., CloudSync Pro",
        )

        # Logo S3 URL
        logo_s3_url = st.text_input(
            "Logo S3 URL *",
            help="S3 URL to PNG/JPG image (e.g., https://bucket.s3.amazonaws.com/logo.png)",
            placeholder="https://your-bucket.s3.amazonaws.com/logo.png",
        )

        # Short Description
        short_description = st.text_area(
            "Short Description *",
            help="10-500 characters - Brief description for search results",
            placeholder="Brief description of your product...",
            max_chars=500,
        )

        # Long Description
        long_description = st.text_area(
            "Long Description *",
            help="50-5000 characters - Detailed product description",
            placeholder="Detailed description with features and benefits...",
            max_chars=5000,
            height=150,
        )

        # Highlights
        st.write("**Highlights (1-3 maximum) ***")
        st.caption("Key features or benefits, 5-250 characters each")
        highlight_1 = st.text_input(
            "Highlight 1 *",
            placeholder="e.g., Real-time synchronization",
            max_chars=250,
        )
        highlight_2 = st.text_input(
            "Highlight 2 (optional)",
            placeholder="e.g., Enterprise-grade security",
            max_chars=250,
        )
        highlight_3 = st.text_input(
            "Highlight 3 (optional)",
            placeholder="e.g., 99.99% uptime SLA",
            max_chars=250,
        )

        # Support Information
        col1, col2 = st.columns(2)
        with col1:
            support_email = st.text_input(
                "Support Email *",
                help="Valid email address",
                placeholder="support@example.com",
            )

        with col2:
            pass  # Spacing

        support_description = st.text_area(
            "Support Description *",
            help="20-2000 characters - How you provide support",
            placeholder="We provide 24/7 support via email and phone...",
            max_chars=2000,
        )

        # Categories
        st.write("**Categories (1-3) ***")
        st.caption("Select AWS Marketplace categories")
        category_options = [
            # Infrastructure Software
            "Backup & Recovery",
            "Data Analytics",
            "High Performance Computing",
            "Migration",
            "Network Infrastructure",
            "Operating Systems",
            "Security",
            "Storage",
            # DevOps
            "Agile Lifecycle Management",
            "Application Development",
            "Application Servers",
            "Application Stacks",
            "Continuous Integration & Continuous Delivery",
            "Infrastructure as Code",
            "Issues & Bug Tracking",
            "Monitoring",
            "Log Analysis",
            "Source Control",
            "Testing",
            # Business Applications
            "Blockchain",
            "Collaboration & Productivity",
            "Contact Center",
            "Content Management",
            "CRM",
            "eCommerce",
            "eLearning",
            "Human Resources",
            "IT Business Management",
            "Business Intelligence",
            "Project Management",
            # Machine Learning
            "ML Solutions",
            "Data Labeling Services",
            "Computer Vision",
            "Natural Language Processing",
            "Speech Recognition",
            "Text",
            "Image",
            "Video",
            "Audio",
            "Structured",
            # IoT
            "IoT Analytics",
            "IoT Applications",
            "Device Connectivity",
            "Device Management",
            "Device Security",
            "Industrial IoT",
            "Smart Home & City",
            # Professional Services
            "Assessments",
            "Implementation",
            "Managed Services",
            "Premium Support",
            "Training",
            # Desktop Applications
            "Desktop Applications",
            "AP and Billing",
            "Application and the Web",
            "Development",
            "CAD and CAM",
            "GIS and Mapping",
            "Illustration and Design",
            "Media and Encoding",
            "Productivity and Collaboration",
            "Security/Storage/Archiving",
            "Utilities",
            # Industries
            "Education & Research",
            "Financial Services",
            "Healthcare & Life Sciences",
            "Media & Entertainment",
            "Industrial",
            "Energy",
        ]
        categories = st.multiselect(
            "Select categories",
            options=sorted(category_options),  # Sort alphabetically
            max_selections=3,
            help="Choose up to 3 categories that best describe your product",
        )

        # Search Keywords
        st.write("**Search Keywords (1-10) ***")
        st.caption("Keywords for marketplace search, max 50 characters each")
        keywords_input = st.text_input(
            "Keywords (comma-separated)",
            placeholder="sync, cloud, integration, backup",
            help="Enter keywords separated by commas",
        )

        # Optional Fields
        st.subheader("Optional Information")

        sku = st.text_input(
            "SKU (optional)", help="Stock Keeping Unit", placeholder="PROD-001"
        )

        video_url = st.text_input(
            "Video URL (optional)",
            help="URL to product demo video",
            placeholder="https://www.youtube.com/watch?v=...",
        )

        # Submit button
        submitted = st.form_submit_button(
            "🚀 Create Product", type="primary", use_container_width=True
        )

        if submitted:
            # Validate required fields
            errors = []

            if not product_title or len(product_title) < 5:
                errors.append("Product Title must be at least 5 characters")

            if not logo_s3_url:
                errors.append("Logo S3 URL is required")

            if not short_description or len(short_description) < 10:
                errors.append("Short Description must be at least 10 characters")

            if not long_description or len(long_description) < 50:
                errors.append("Long Description must be at least 50 characters")

            if not highlight_1:
                errors.append("At least 1 highlight is required")

            if not support_email:
                errors.append("Support Email is required")

            if not support_description or len(support_description) < 20:
                errors.append("Support Description must be at least 20 characters")

            if not categories or len(categories) < 1:
                errors.append("At least 1 category is required")

            if not keywords_input:
                errors.append("At least 1 keyword is required")

            if errors:
                st.error("Please fix the following errors:")
                for error in errors:
                    st.write(f"- {error}")
                return

            # Build highlights array (1-3 highlights)
            highlights = [highlight_1]
            if highlight_2:
                highlights.append(highlight_2)
            if highlight_3:
                highlights.append(highlight_3)

            # Parse keywords
            keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
            if len(keywords) > 10:
                st.error("Maximum 10 keywords allowed")
                return

            # Set all data in orchestrator
            orchestrator = st.session_state.orchestrator

            orchestrator.set_stage_data("product_title", product_title)
            orchestrator.set_stage_data("logo_s3_url", logo_s3_url)
            orchestrator.set_stage_data("short_description", short_description)
            orchestrator.set_stage_data("long_description", long_description)
            orchestrator.set_stage_data("highlights", highlights)
            orchestrator.set_stage_data("support_email", support_email)
            orchestrator.set_stage_data("support_description", support_description)
            orchestrator.set_stage_data("categories", categories)
            orchestrator.set_stage_data("search_keywords", keywords)

            if sku:
                orchestrator.set_stage_data("sku", sku)

            if video_url:
                orchestrator.set_stage_data("video_urls", [video_url])

            # Show progress
            with st.spinner("Creating product in AWS Marketplace..."):
                # Complete the stage
                result = orchestrator.complete_current_stage()

                if result.get("status") == "complete":
                    st.success("✅ Stage 1 Complete!")

                    # Show API result
                    api_result = result.get("api_result", {})
                    if api_result.get("success"):
                        st.success(api_result.get("message", "Product created!"))

                        if api_result.get("product_id"):
                            st.info(f"🆔 Product ID: `{api_result['product_id']}`")

                        if api_result.get("offer_id"):
                            st.info(f"🆔 Offer ID: `{api_result['offer_id']}`")

                        if api_result.get("change_set_id"):
                            st.caption(f"Change Set ID: {api_result['change_set_id']}")

                        # Orchestrator automatically advances to next stage
                        st.rerun()
                    else:
                        st.error(
                            f"❌ Error: {api_result.get('error', 'Unknown error')}"
                        )
                else:
                    st.error(f"❌ {result.get('message', 'Failed to complete stage')}")


def stage2_form():
    """Stage 2: Fulfillment Options Form"""
    st.header("🔗 Stage 2: Fulfillment Options")
    st.write("Configure how customers will access your SaaS product.")

    orchestrator = st.session_state.orchestrator

    # Show product info
    if orchestrator.product_id:
        st.success(f"✅ Product ID: `{orchestrator.product_id}`")

    with st.form("stage2_form"):
        fulfillment_url = st.text_input(
            "Fulfillment URL *",
            help="HTTPS URL where customers will register/login",
            placeholder="https://app.example.com/signup",
        )

        quick_launch = st.checkbox("Enable Quick Launch")

        launch_url = None
        if quick_launch:
            launch_url = st.text_input(
                "Launch URL *",
                help="URL for Quick Launch feature",
                placeholder="https://app.example.com/quicklaunch",
            )

        submitted = st.form_submit_button("Continue to Stage 3", type="primary")

        if submitted:
            if not fulfillment_url or not fulfillment_url.startswith("https://"):
                st.error("Fulfillment URL must start with https://")
                return

            if quick_launch and not launch_url:
                st.error("Launch URL is required when Quick Launch is enabled")
                return

            # Set data
            orchestrator.set_stage_data("fulfillment_url", fulfillment_url)
            orchestrator.set_stage_data("quick_launch_enabled", quick_launch)
            if launch_url:
                orchestrator.set_stage_data("launch_url", launch_url)

            # Complete stage
            complete_stage_with_feedback(
                orchestrator, "Stage 2", "Adding delivery options..."
            )


def stage3_form():
    """Stage 3: Pricing Configuration Form"""
    st.header("💰 Stage 3: Pricing Configuration")
    st.write("Configure your pricing model and dimensions.")

    orchestrator = st.session_state.orchestrator

    with st.form("stage3_form"):
        pricing_model = st.selectbox(
            "Pricing Model *",
            options=["Usage", "Contract", "Contract with Consumption"],
            help="How customers will be charged",
        )

        # Show pricing model explanation
        if pricing_model == "Usage":
            st.info("💡 **Usage-based**: Customers pay for what they use (metered dimensions)")
        elif pricing_model == "Contract":
            st.info("💡 **Contract-based**: Customers pay upfront for entitled dimensions")
        else:
            st.info("💡 **Contract with Consumption**: Customers pay upfront for contract dimensions + usage for metered dimensions")

        st.write("**Pricing Dimensions (1-24) ***")
        st.caption("Define the units customers will be charged for")

        # For Contract with Consumption, separate contract and usage dimensions
        if pricing_model == "Contract with Consumption":
            st.subheader("Contract Dimensions (Entitled)")
            num_contract_dims = st.number_input(
                "Number of contract dimensions", min_value=1, max_value=10, value=1, key="num_contract"
            )
            
            contract_dimensions = []
            for i in range(num_contract_dims):
                st.write(f"**Contract Dimension {i + 1}**")
                col1, col2 = st.columns(2)

                with col1:
                    dim_key = st.text_input(
                        "API ID *",
                        key=f"contract_dim_key_{i}",
                        help="Lowercase, alphanumeric, underscores only",
                        placeholder="e.g., basic_users",
                    )

                with col2:
                    dim_name = st.text_input(
                        "Display Name *",
                        key=f"contract_dim_name_{i}",
                        placeholder="e.g., Basic Users",
                    )

                dim_desc = st.text_input(
                    "Description *",
                    key=f"contract_dim_desc_{i}",
                    placeholder="e.g., Number of basic user seats included in contract",
                )

                if dim_key and dim_name and dim_desc:
                    contract_dimensions.append({
                        "Key": dim_key,
                        "Name": dim_name,
                        "Description": dim_desc,
                        "Types": ["Entitled"],
                        "Unit": "Units",
                    })
            
            st.divider()
            st.subheader("Usage Dimensions (Metered)")
            num_usage_dims = st.number_input(
                "Number of usage dimensions", min_value=1, max_value=10, value=1, key="num_usage"
            )
            
            usage_dimensions = []
            for i in range(num_usage_dims):
                st.write(f"**Usage Dimension {i + 1}**")
                col1, col2 = st.columns(2)

                with col1:
                    dim_key = st.text_input(
                        "API ID *",
                        key=f"usage_dim_key_{i}",
                        help="Lowercase, alphanumeric, underscores only",
                        placeholder="e.g., api_calls",
                    )

                with col2:
                    dim_name = st.text_input(
                        "Display Name *",
                        key=f"usage_dim_name_{i}",
                        placeholder="e.g., API Calls",
                    )

                dim_desc = st.text_input(
                    "Description *",
                    key=f"usage_dim_desc_{i}",
                    placeholder="e.g., Number of API calls beyond contract limit",
                )

                if dim_key and dim_name and dim_desc:
                    usage_dimensions.append({
                        "Key": dim_key,
                        "Name": dim_name,
                        "Description": dim_desc,
                        "Types": ["Metered"],
                        "Unit": "Units",
                    })
            
            dimensions = contract_dimensions + usage_dimensions
        
        else:
            # For Usage or Contract, single dimension type
            dim_type = "Metered" if pricing_model == "Usage" else "Entitled"
            
            num_dimensions = st.number_input(
                "Number of dimensions", min_value=1, max_value=10, value=1
            )

            dimensions = []
            for i in range(num_dimensions):
                st.write(f"**Dimension {i + 1}**")
                col1, col2 = st.columns(2)

                with col1:
                    dim_key = st.text_input(
                        f"API ID {i + 1} *",
                        key=f"dim_key_{i}",
                        help="Lowercase, alphanumeric, underscores only",
                        placeholder="e.g., users",
                    )

                with col2:
                    dim_name = st.text_input(
                        f"Display Name {i + 1} *",
                        key=f"dim_name_{i}",
                        placeholder="e.g., Active Users",
                    )

                dim_desc = st.text_input(
                    f"Description {i + 1} *",
                    key=f"dim_desc_{i}",
                    placeholder="e.g., Number of active users per month",
                )

                if dim_key and dim_name and dim_desc:
                    dimensions.append({
                        "Key": dim_key,
                        "Name": dim_name,
                        "Description": dim_desc,
                        "Types": [dim_type],
                        "Unit": "Units",
                    })

        submitted = st.form_submit_button("Continue to Stage 4", type="primary")

        if submitted:
            if not dimensions:
                st.error("At least 1 dimension is required")
                return

            # Set data
            orchestrator.set_stage_data("pricing_model", pricing_model.lower())
            orchestrator.set_stage_data("dimensions", dimensions)

            # Complete stage
            complete_stage_with_feedback(
                orchestrator, "Stage 3", "Adding pricing dimensions to product..."
            )


def stage4_form():
    """Stage 4: Price Review Form"""
    st.header("💵 Stage 4: Price Review")
    st.write("Configure contract pricing terms for your offer.")

    orchestrator = st.session_state.orchestrator

    # Show configured dimensions
    pricing_config = orchestrator.all_data.get("PRICING_CONFIG", {})
    dimensions = pricing_config.get("dimensions", []) if pricing_config else []

    if not dimensions:
        st.error("No dimensions configured. Please complete Stage 3 first.")
        return

    st.info(f"Pricing Model: {pricing_config.get('pricing_model', 'N/A').upper()}")
    st.write("**Configured Dimensions:**")
    for dim in dimensions:
        st.write(f"- {dim.get('Name')} ({dim.get('Key')})")

    with st.form("stage4_form"):
        st.subheader("Contract Durations")
        st.write("Select which contract durations to offer:")

        durations = st.multiselect(
            "Available contract durations *",
            options=[
                "1 Month",
                "12 Months",
                "24 Months",
                "36 Months",
            ],
            default=["12 Months"],
            help="Customers can choose from these contract lengths",
        )

        st.subheader("Purchasing Options")
        st.write("Configure how customers can purchase dimensions:")

        purchasing_option = st.radio(
            "Dimension Selection",
            options=[
                "Multiple dimensions per contract",
                "Single dimension per contract",
            ],
            index=0,
            help="Choose whether customers can purchase multiple dimensions in one contract or must purchase each dimension separately",
        )

        # Automatically set constraints based on selection
        if purchasing_option == "Multiple dimensions per contract":
            multiple_dimensions = "Allowed"
            quantity_config = "Allowed"
            st.info(
                "✓ Customers can purchase multiple dimensions and configure quantities"
            )
        else:
            multiple_dimensions = "Disallowed"
            quantity_config = "Disallowed"
            st.info(
                "✓ Customers must purchase each dimension separately with fixed quantities"
            )

        st.info(
            "💡 **Note:** Prices are set to $0.001 USD for testing. Update prices before going live."
        )

        submitted = st.form_submit_button("Continue to Stage 5", type="primary")

        if submitted:
            if not durations:
                st.error("At least one contract duration is required")
                return

            # Set data
            orchestrator.set_stage_data("contract_durations", durations)
            orchestrator.set_stage_data(
                "multiple_dimension_selection", multiple_dimensions
            )
            orchestrator.set_stage_data("quantity_configuration", quantity_config)

            # Complete stage
            complete_stage_with_feedback(
                orchestrator, "Stage 4", "Applying pricing to offer..."
            )


def stage5_form():
    """Stage 5: Refund Policy Form"""
    st.header("↩️ Stage 5: Refund Policy")
    st.write("Specify your refund policy for customers.")

    orchestrator = st.session_state.orchestrator

    with st.form("stage5_form"):
        refund_policy = st.text_area(
            "Refund Policy *",
            help="50-5000 characters - Clear statement of refund terms",
            placeholder="We offer a 30-day money-back guarantee. If you're not satisfied, contact support within 30 days of purchase for a full refund. Refunds are processed within 5-7 business days.",
            max_chars=5000,
            height=150,
        )

        # Quick templates
        st.write("**Quick Templates:**")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.form_submit_button("30-Day Refund", use_container_width=True):
                st.session_state.refund_template = "We offer a 30-day money-back guarantee. If you're not satisfied with our service, contact support@example.com within 30 days of purchase for a full refund. Refunds are processed within 5-7 business days."

        with col2:
            if st.form_submit_button("No Refund", use_container_width=True):
                st.session_state.refund_template = "All sales are final. We do not offer refunds for this service. Please ensure you understand the product features and pricing before purchasing."

        with col3:
            if st.form_submit_button("Pro-rated", use_container_width=True):
                st.session_state.refund_template = "We offer pro-rated refunds for annual subscriptions. If you cancel within the first year, you will receive a refund for the unused portion of your subscription, minus a processing fee."

        submitted = st.form_submit_button("Continue to Stage 6", type="primary")

        if submitted:
            if not refund_policy or len(refund_policy) < 50:
                st.error("Refund policy must be at least 50 characters")
                return

            # Set data
            orchestrator.set_stage_data("refund_policy", refund_policy)

            # Complete stage
            complete_stage_with_feedback(
                orchestrator, "Stage 5", "Updating support terms on offer..."
            )


def stage6_form():
    """Stage 6: EULA Configuration Form"""
    st.header("📄 Stage 6: EULA Configuration")
    st.write("Configure your End User License Agreement.")

    orchestrator = st.session_state.orchestrator

    with st.form("stage6_form"):
        eula_type = st.radio(
            "EULA Type *",
            options=["scmp", "custom"],
            format_func=lambda x: "Standard Contract for AWS Marketplace (SCMP)"
            if x == "scmp"
            else "Custom EULA",
            help="SCMP is recommended for most sellers",
        )

        st.info(
            "**SCMP (Recommended):** AWS's standard terms - quick and easy, no additional setup needed."
        )
        st.info(
            "**Custom EULA:** Your own license agreement - requires S3 URL to PDF document and AWS review."
        )

        custom_eula_url = None
        if eula_type == "custom":
            custom_eula_url = st.text_input(
                "Custom EULA S3 URL *",
                help="S3 URL to your custom EULA PDF",
                placeholder="https://your-bucket.s3.amazonaws.com/eula.pdf",
            )

        submitted = st.form_submit_button("Continue to Stage 7", type="primary")

        if submitted:
            if eula_type == "custom" and not custom_eula_url:
                st.error("Custom EULA URL is required when using Custom EULA")
                return

            # Set data
            orchestrator.set_stage_data("eula_type", eula_type)
            if custom_eula_url:
                orchestrator.set_stage_data("custom_eula_s3_url", custom_eula_url)

            # Complete stage
            complete_stage_with_feedback(
                orchestrator, "Stage 6", "Updating legal terms on offer..."
            )


def stage7_form():
    """Stage 7: Offer Availability Form"""
    st.header("🌍 Stage 7: Offer Availability")
    st.write("Configure geographic availability for your offer.")

    orchestrator = st.session_state.orchestrator

    with st.form("stage7_form"):
        availability_type = st.radio(
            "Availability Type *",
            options=["all_countries", "all_with_exclusions", "allowlist_only"],
            format_func=lambda x: {
                "all_countries": "All Countries (Worldwide)",
                "all_with_exclusions": "All Countries with Exclusions",
                "allowlist_only": "Specific Countries Only (Allowlist)",
            }[x],
            help="Most sellers choose 'All Countries'",
        )

        excluded_countries = None
        allowed_countries = None

        if availability_type == "all_with_exclusions":
            st.write("**Excluded Countries**")
            excluded_countries = st.text_input(
                "Country codes to exclude (comma-separated)",
                help="ISO 3166-1 alpha-2 codes (e.g., US, GB, DE)",
                placeholder="e.g., KP, IR, SY",
            )

        if availability_type == "allowlist_only":
            st.write("**Allowed Countries**")
            allowed_countries = st.text_input(
                "Country codes to allow (comma-separated)",
                help="ISO 3166-1 alpha-2 codes (e.g., US, GB, DE)",
                placeholder="e.g., US, CA, GB, DE, FR",
            )

        submitted = st.form_submit_button("Continue to Stage 8", type="primary")

        if submitted:
            if availability_type == "all_with_exclusions" and not excluded_countries:
                st.error("Please specify countries to exclude")
                return

            if availability_type == "allowlist_only" and not allowed_countries:
                st.error("Please specify countries to allow")
                return

            # Set data
            orchestrator.set_stage_data("availability_type", availability_type)

            if excluded_countries:
                codes = [c.strip().upper() for c in excluded_countries.split(",")]
                orchestrator.set_stage_data("excluded_countries", codes)

            if allowed_countries:
                codes = [c.strip().upper() for c in allowed_countries.split(",")]
                orchestrator.set_stage_data("allowed_countries", codes)

            # Complete stage
            complete_stage_with_feedback(
                orchestrator, "Stage 7", "Updating offer availability..."
            )


def stage8_form():
    """Stage 8: Allowlist Configuration Form"""
    st.header("🔐 Stage 8: Account Allowlist (Optional)")
    st.write("Optionally restrict your offer to specific AWS accounts.")

    orchestrator = st.session_state.orchestrator

    with st.form("stage8_form"):
        st.info(
            "This stage is optional. Leave blank to make your offer publicly available."
        )

        buyer_accounts = st.text_area(
            "AWS Account IDs (optional)",
            help="12-digit AWS account IDs, one per line or comma-separated",
            placeholder="123456789012\n234567890123\n345678901234",
            height=100,
        )

        col1, col2 = st.columns(2)

        with col1:
            skip = st.form_submit_button(
                "Skip (Public Offer)", use_container_width=True
            )

        with col2:
            submitted = st.form_submit_button(
                "Complete Workflow", type="primary", use_container_width=True
            )

        if skip or submitted:
            # Set data if provided
            if buyer_accounts and submitted:
                # Parse account IDs
                accounts = []
                for line in buyer_accounts.replace(",", "\n").split("\n"):
                    account = line.strip()
                    if account and account.isdigit() and len(account) == 12:
                        accounts.append(account)

                if accounts:
                    orchestrator.set_stage_data("buyer_accounts", accounts)

            # Complete stage
            complete_stage_with_feedback(
                orchestrator, "Stage 8", "Updating offer targeting..."
            )


def workflow_complete():
    """Show workflow completion"""
    st.header("🎉 Workflow Complete!")
    st.success("All stages have been completed successfully!")

    orchestrator = st.session_state.orchestrator

    # Show summary
    st.subheader("Summary")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Product ID", orchestrator.product_id or "N/A")

    with col2:
        st.metric("Offer ID", orchestrator.offer_id or "N/A")

    st.metric("Progress", f"{orchestrator.get_progress_percentage()}%")

    # Show all collected data
    with st.expander("View All Collected Data"):
        st.json(orchestrator.export_data())

    # Actions
    st.subheader("Next Steps")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Start New Listing", use_container_width=True):
            orchestrator.reset_workflow()
            # Orchestrator resets to PRODUCT_INFO automatically
            st.rerun()

    with col2:
        if st.button("📥 Export Data", use_container_width=True):
            import json

            data = orchestrator.export_data()
            st.download_button(
                "Download JSON",
                data=json.dumps(data, indent=2),
                file_name="marketplace_listing.json",
                mime="application/json",
            )

    with col3:
        st.link_button(
            "🌐 View in AWS Console",
            "https://aws.amazon.com/marketplace/management/products",
            use_container_width=True,
        )


def main():
    """Main app"""
    st.set_page_config(
        page_title="AWS Marketplace Listing Creator", page_icon="📦", layout="wide"
    )

    st.title("📦 AWS Marketplace SaaS Listing Creator")
    st.caption("Form-Based Workflow")

    # Initialize
    init_session_state()

    orchestrator = st.session_state.orchestrator
    current_stage = orchestrator.current_stage

    # Progress bar
    progress = orchestrator.get_progress_percentage()
    st.progress(progress / 100, text=f"Progress: {progress}%")

    # Show current stage
    st.write(f"**Current Stage:** {current_stage.value}/8 - {current_stage.name}")

    # Render appropriate form
    if current_stage == WorkflowStage.PRODUCT_INFO:
        stage1_form()
    elif current_stage == WorkflowStage.FULFILLMENT:
        stage2_form()
    elif current_stage == WorkflowStage.PRICING_CONFIG:
        stage3_form()
    elif current_stage == WorkflowStage.PRICE_REVIEW:
        stage4_form()
    elif current_stage == WorkflowStage.REFUND_POLICY:
        stage5_form()
    elif current_stage == WorkflowStage.EULA_CONFIG:
        stage6_form()
    elif current_stage == WorkflowStage.OFFER_AVAILABILITY:
        stage7_form()
    elif current_stage == WorkflowStage.ALLOWLIST:
        stage8_form()
    elif current_stage == WorkflowStage.COMPLETE:
        workflow_complete()
    else:
        st.error(f"Unknown stage: {current_stage}")

    # Sidebar with info
    with st.sidebar:
        st.header("ℹ️ Information")

        if orchestrator.product_id:
            st.success("Product Created!")
            st.code(f"Product ID:\n{orchestrator.product_id}")

        if orchestrator.offer_id:
            st.code(f"Offer ID:\n{orchestrator.offer_id}")

        st.divider()

        st.subheader("Completed Stages")
        for stage in orchestrator.completed_stages:
            st.write(f"✅ Stage {stage.value}: {stage.name}")

        st.divider()

        st.caption("AWS Marketplace Listing Creator")
        st.caption("Form-Based UI v1.0")


if __name__ == "__main__":
    main()
