#!/usr/bin/env python3
"""
AWS Marketplace Listing Creator - Launcher

Choose between AI-Guided or Manual Form workflows.
"""

import streamlit as st
import subprocess
import sys

st.set_page_config(
    page_title="AWS Marketplace Listing Creator",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 AWS Marketplace Listing Creator")

st.markdown("""
Welcome! Choose how you'd like to create your AWS Marketplace listing:
""")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("🤖 AI-Guided Creation")
    st.markdown("""
    **Best for:** First-time users, quick setup
    
    **Features:**
    - 📄 Analyzes your product documentation
    - 💡 Suggests pricing models automatically
    - ✍️ Generates all text content with AI
    - 🎯 Selects categories and keywords
    - ⚡ Creates listing in minutes
    
    **Perfect if you:**
    - Have product documentation ready
    - Want AI to handle the details
    - Don't know AWS Marketplace terminology
    - Need to create listings quickly
    """)
    
    if st.button("🤖 Start AI-Guided Creation", type="primary", use_container_width=True):
        st.info("Starting AI-Guided workflow...")
        st.code("streamlit run streamlit_guided_app.py", language="bash")
        st.markdown("**Run this command in your terminal:**")
        st.code("streamlit run streamlit_guided_app.py")

with col2:
    st.subheader("📝 Manual Form")
    st.markdown("""
    **Best for:** Experienced users, precise control
    
    **Features:**
    - 📋 Step-by-step form interface
    - ✏️ Full control over every field
    - 📊 Clear validation and guidance
    - 🔍 See exactly what you're submitting
    - 💾 Save and resume anytime
    
    **Perfect if you:**
    - Know exactly what you want
    - Have all information prepared
    - Want complete control
    - Prefer traditional forms
    """)
    
    if st.button("📝 Use Manual Form", use_container_width=True):
        st.info("Starting Manual Form workflow...")
        st.code("streamlit run streamlit_form_app.py", language="bash")
        st.markdown("**Run this command in your terminal:**")
        st.code("streamlit run streamlit_form_app.py")

st.divider()

st.markdown("""
### 📚 Need Help?

- **Documentation:** Check `END_TO_END_TEST_GUIDE.md` for detailed instructions
- **Troubleshooting:** See `TROUBLESHOOTING.md` for common issues
- **Architecture:** Review `docs/MULTI_AGENT_ARCHITECTURE.md` to understand the system

### 🔧 Prerequisites

Make sure you have:
- ✅ AWS credentials configured
- ✅ Amazon Bedrock access (for AI-Guided mode)
- ✅ AWS Marketplace seller account
- ✅ Python dependencies installed (`pip install -r requirements.txt`)
""")
