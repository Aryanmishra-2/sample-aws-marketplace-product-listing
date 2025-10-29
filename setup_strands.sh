#!/bin/bash
# Setup script for Strands SDK version
# Creates virtual environment and installs dependencies

set -e  # Exit on error

echo "🚀 Setting up AWS Marketplace Listing Creator (Strands SDK)"
echo "============================================================"
echo ""

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Found Python $python_version"

# Check if Python 3.8+
required_version="3.8"
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "❌ Error: Python 3.8 or higher is required"
    echo "   Please install Python 3.8+ and try again"
    exit 1
fi
echo "   ✅ Python version OK"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "   ⚠️  Virtual environment already exists"
    read -p "   Remove and recreate? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
        echo "   ✅ Virtual environment recreated"
    else
        echo "   ℹ️  Using existing virtual environment"
    fi
else
    python3 -m venv venv
    echo "   ✅ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate
echo "   ✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "   ✅ pip upgraded"
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
echo "   This may take a few minutes..."
pip install -r requirements_strands.txt
echo "   ✅ Dependencies installed"
echo ""

# Check AWS credentials
echo "🔐 Checking AWS credentials..."
if aws sts get-caller-identity > /dev/null 2>&1; then
    account_id=$(aws sts get-caller-identity --query Account --output text)
    echo "   ✅ AWS credentials configured"
    echo "   Account ID: $account_id"
else
    echo "   ⚠️  AWS credentials not configured"
    echo "   Run: aws configure"
    echo ""
fi
echo ""

# Run tests
echo "🧪 Running tests..."
if python test_strands_migration.py; then
    echo ""
    echo "============================================================"
    echo "✅ Setup complete! Everything is working."
    echo "============================================================"
    echo ""
    echo "🎯 Next steps:"
    echo ""
    echo "1. Activate the virtual environment (if not already active):"
    echo "   source venv/bin/activate"
    echo ""
    echo "2. Run the Streamlit app:"
    echo "   streamlit run streamlit_strands_app.py"
    echo ""
    echo "3. Or use Python directly:"
    echo "   python -c \"from agent.strands_marketplace_agent import StrandsMarketplaceAgent; agent = StrandsMarketplaceAgent(); print(agent.process_message('Create a listing'))\""
    echo ""
    echo "4. Deploy to AgentCore (optional):"
    echo "   pip install bedrock-agentcore-cli"
    echo "   agentcore configure --config agentcore_config.yaml"
    echo "   agentcore launch"
    echo ""
    echo "📚 Documentation:"
    echo "   - Quick Start: QUICKSTART_STRANDS.md"
    echo "   - Full Guide: README_STRANDS.md"
    echo "   - Migration: MIGRATION_GUIDE.md"
    echo ""
else
    echo ""
    echo "============================================================"
    echo "⚠️  Setup complete but tests failed"
    echo "============================================================"
    echo ""
    echo "Common issues:"
    echo ""
    echo "1. AWS credentials not configured:"
    echo "   aws configure"
    echo ""
    echo "2. Bedrock models not enabled:"
    echo "   Go to: https://console.aws.amazon.com/bedrock/"
    echo "   Enable: Claude 3.7 Sonnet"
    echo ""
    echo "3. Missing dependencies:"
    echo "   pip install -r requirements_strands.txt"
    echo ""
    echo "Run tests again:"
    echo "   python test_strands_migration.py"
    echo ""
fi
