# Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Setup (One Time)
```bash
# Clone or download the repository
cd MPAgent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure AWS credentials
./setup_aws_credentials.sh
# Or manually: aws configure
```

### Step 2: Choose Your Workflow
```bash
# Launch the workflow selector
streamlit run streamlit_launcher.py
```

### Step 3: Create Your Listing!

#### Option A: 🤖 AI-Guided (5-10 minutes)
1. Click "Start AI-Guided Creation"
2. Provide product documentation or URL
3. Review AI-generated content
4. Click "Create Listing"
5. Done! ✅

#### Option B: 📝 Manual Form (20-30 minutes)
1. Click "Use Manual Form"
2. Fill out 8 stages step-by-step
3. Review and submit each stage
4. Done! ✅

## What You Need

### Required
- ✅ AWS Account with Marketplace seller registration
- ✅ AWS CLI configured (`aws configure`)
- ✅ Python 3.9+ installed
- ✅ Product information ready

### For AI-Guided Workflow
- ✅ Amazon Bedrock access (Claude 3.5 Sonnet)
- ✅ Product documentation, website, or description

### For Manual Form
- ✅ Pre-written content (title, descriptions, etc.)
- ✅ Basic AWS Marketplace knowledge

## Test Your Setup

```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check Bedrock access (for AI-Guided)
python check_bedrock_models.py

# Run setup verification
python test_setup.py
```

## Quick Commands

```bash
# AI-Guided Workflow
streamlit run streamlit_guided_app.py

# Manual Form Workflow
streamlit run streamlit_form_app.py

# Workflow Selector
streamlit run streamlit_launcher.py
```

## Sample Data for Testing

### AI-Guided Input
```
Website: https://example.com
Description: "Cloud-based project management tool with 
real-time collaboration, task tracking, and team analytics. 
Perfect for remote teams and agile workflows."
```

### Manual Form Input
See [END_TO_END_TEST_GUIDE.md](END_TO_END_TEST_GUIDE.md) for complete sample data.

## Next Steps

1. **Create your first listing** using either workflow
2. **Review in AWS Console** - AWS Marketplace Management Portal
3. **Test the integration** - Subscribe to your own product
4. **Update pricing** - Change from test prices ($0.001) to production
5. **Submit for publication** - Request visibility change to "Public"

## Need Help?

- **AI-Guided**: [AI_GUIDED_WORKFLOW.md](AI_GUIDED_WORKFLOW.md)
- **Manual Form**: [END_TO_END_TEST_GUIDE.md](END_TO_END_TEST_GUIDE.md)
- **Comparison**: [WORKFLOWS_COMPARISON.md](WORKFLOWS_COMPARISON.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## Common Issues

### "No Bedrock access"
```bash
# Request model access in AWS Console
# Bedrock > Model access > Request access to Claude 3.5 Sonnet
```

### "AWS credentials not configured"
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and region
```

### "Module not found"
```bash
pip install -r requirements.txt
```

## Support

For issues or questions:
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review [docs/MULTI_AGENT_ARCHITECTURE.md](docs/MULTI_AGENT_ARCHITECTURE.md)
3. Check AWS Marketplace documentation

Happy listing! 🎉
