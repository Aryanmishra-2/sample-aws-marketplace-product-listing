#!/bin/bash
# Quick script to run the Streamlit app with the correct venv

# Set the venv path
export VIRTUAL_ENV=/Users/avivenk/Library/CloudStorage/WorkDocsDrive-Documents/MPAgent/venv
export PATH="$VIRTUAL_ENV/bin:$PATH"

echo "🚀 Starting AI-Guided Marketplace Listing Creator..."
echo "📍 Using venv: $VIRTUAL_ENV"
echo ""

streamlit run streamlit_app_complete.py
