# AWS Marketplace SaaS Listing Creator

AI-powered tool to create AWS Marketplace SaaS listings using Strands SDK.

## 🚀 Quick Start

```bash
# Run the app
./run_streamlit.sh
```

## 📋 What It Does

Creates complete AWS Marketplace SaaS listings through an AI-guided workflow:

1. **Provide URLs** - Enter your product website, docs, pricing page
2. **AI Analysis** - AI analyzes and generates all content automatically
3. **Review & Configure** - Review AI suggestions and configure:
   - Product information (title, descriptions, highlights)
   - Pricing dimensions (metered/entitled)
   - Contract durations
   - Geographic availability
   - Account allowlist
   - Support & EULA
4. **Create & Publish** - One-click creation with optional auto-publish to Limited stage

## ✨ Features

- ✅ **AI-Powered** - Analyzes your product and generates optimized content
- ✅ **Complete Workflow** - All 8 AWS Marketplace stages
- ✅ **Pricing Models** - Usage, Contract, or Hybrid (Contract with Consumption)
- ✅ **Auto-Publish** - Optionally publish to Limited stage automatically
- ✅ **Strands SDK** - Built on AWS Strands agent framework

## 📦 Setup

### Prerequisites

- Python 3.8+
- AWS Account with Marketplace Seller registration
- AWS credentials configured
- Bedrock access (Claude 3.7 Sonnet enabled)

### Installation

The packages are already installed in:
```
/Users/avivenk/Library/CloudStorage/WorkDocsDrive-Documents/MPAgent/venv
```

The `run_streamlit.sh` script automatically uses this venv.

### Manual Setup (if needed)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements_strands.txt

# Configure AWS
aws configure

# Enable Bedrock models
# Go to: https://console.aws.amazon.com/bedrock/
# Enable: Claude 3.7 Sonnet
```

## 🎯 Usage

### Run the App

```bash
./run_streamlit.sh
```

### Workflow

1. **Welcome** - Click "Start AI-Guided Creation"
2. **Provide URLs** - Enter product website, docs, pricing URLs
3. **AI Analysis** - Wait while AI analyzes your product
4. **Review** - Review and edit AI-generated content:
   - Product title, descriptions, highlights
   - Categories and keywords
   - Pricing model and dimensions
   - Contract durations (if applicable)
   - Support information
   - Refund policy
   - EULA configuration
   - Geographic availability
   - Account allowlist (optional)
5. **Create** - Click "Create Listing" to publish

### Auto-Publish to Limited

Enable the checkbox to automatically publish your listing to Limited stage for testing. This allows you to test immediately with your AWS account.

## 📊 Pricing Models

### Usage-Based
Pay-as-you-go metered pricing
- Add metered dimensions (e.g., API calls, storage)
- Customers pay only for what they use

### Contract-Based
Upfront commitment pricing
- Add entitled dimensions (e.g., user seats)
- Select contract durations (1-36 months)
- Customers pay upfront

### Contract with Consumption (Hybrid)
Base contract + usage overages
- Add both entitled and metered dimensions
- Customers get base entitlement + pay for overages

## 🏗️ Architecture

```
Streamlit UI
    ↓
StrandsMarketplaceAgent (Strands SDK)
    ↓
ListingOrchestrator (8-stage workflow)
    ↓
Sub-Agents (specialized per stage)
    ↓
ListingTools (AWS Marketplace API)
```

### Key Components

- **Strands Agent** - LLM interaction with @tool decorators
- **Orchestrator** - Manages 8-stage workflow
- **Sub-Agents** - Stage-specific logic (Product Info, Pricing, etc.)
- **Listing Tools** - AWS Marketplace Catalog API integration

## 📁 Files

### Main Files
- **`streamlit_app_complete.py`** - Complete AI-guided UI (recommended)
- **`run_streamlit.sh`** - Launch script
- **`requirements_strands.txt`** - Python dependencies

### Agent Files
- `agent/strands_marketplace_agent.py` - Main Strands agent
- `agent/orchestrator.py` - Workflow orchestration
- `agent/sub_agents/*.py` - 8 specialized sub-agents
- `agent/tools/listing_tools.py` - AWS Marketplace API tools

### Configuration
- `config/multi_agent_config.yaml` - Agent configuration
- `agentcore_config.yaml` - AgentCore deployment config

### Testing
- `test_strands_migration.py` - Test suite

## 🧪 Testing

```bash
export VIRTUAL_ENV=/Users/avivenk/Library/CloudStorage/WorkDocsDrive-Documents/MPAgent/venv
export PATH="$VIRTUAL_ENV/bin:$PATH"
python test_strands_migration.py
```

Expected: 8/9 tests passing (89%)

## 🔧 Configuration

### Model Configuration

Edit `config/multi_agent_config.yaml`:

```yaml
bedrock:
  model_id: "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
  region: "us-east-1"
```

### Virtual Environment

The app uses:
```
/Users/avivenk/Library/CloudStorage/WorkDocsDrive-Documents/MPAgent/venv
```

The `run_streamlit.sh` script handles this automatically.

## 📚 AWS Marketplace Resources

- [Seller Guide](https://docs.aws.amazon.com/marketplace/latest/userguide/)
- [SaaS Guidelines](https://docs.aws.amazon.com/marketplace/latest/userguide/saas-guidelines.html)
- [Management Portal](https://aws.amazon.com/marketplace/management/products)

## 🐛 Troubleshooting

### Import Error: "No module named 'strands'"

The package is `strands-agents` but import is:
```python
from strands import Agent, tool
```

Install:
```bash
pip install strands-agents strands-agents-tools
```

### Model Access Denied

Enable Claude models in Bedrock console:
1. Go to https://console.aws.amazon.com/bedrock/
2. Navigate to: Model access → Manage model access
3. Enable: Claude 3.7 Sonnet

### AWS Credentials

```bash
aws configure
```

## 💡 Tips

1. **Provide good URLs** - Better URLs = better AI analysis
2. **Review everything** - Always review AI-generated content
3. **Test in Limited** - Use auto-publish to test immediately
4. **Start with test pricing** - Use $0.001 for testing
5. **Update before public** - Change to production prices before going public

## 🎉 What's New (Strands SDK)

This version uses **Strands SDK** instead of custom runtime:

### Before (Custom)
- Custom AgentRuntime class
- Custom Gateway for tool routing
- Manual conversation management
- ~1,500 lines of code

### After (Strands SDK)
- Strands Agent class
- @tool decorator for tools
- Built-in conversation handling
- ~1,100 lines of code (-27%)

### What Stayed the Same
- ✅ All 8 workflow stages
- ✅ Orchestration logic
- ✅ Sub-agents
- ✅ AWS Marketplace API tools
- ✅ Data validation

## 📄 License

See LICENSE file for details.

---

**Ready to create your AWS Marketplace listing?**

```bash
./run_streamlit.sh
```
