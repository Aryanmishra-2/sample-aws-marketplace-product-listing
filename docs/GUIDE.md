# Technical Guide - AWS Marketplace SaaS Listing Creator

## Overview

An intelligent multi-agent system that automates AWS Marketplace SaaS product listing creation using AWS Bedrock AgentCore architecture.

**Architecture:** 1 Master Orchestrator + 8 Specialized Sub-Agents

## Quick Start

### 1. Setup

```bash
# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure AWS credentials
./setup_aws_credentials.sh

# Verify setup
python3 test_setup.py
```

### 2. Choose Your Workflow

```bash
# Launcher (Choose AI-Guided or Manual Form)
streamlit run streamlit_launcher.py

# Or directly:
streamlit run streamlit_guided_app.py   # AI-Guided (5-10 min)
streamlit run streamlit_form_app.py     # Manual Form (20-30 min)
```

## Workflows

### AI-Guided Workflow (Recommended for First-Time Users)

**Process:**
1. **Provide Context** - Share website URL, documentation, or description
2. **AI Analysis** - AI analyzes product and generates content
3. **Review & Edit** - Review AI suggestions and make adjustments
4. **Create** - One-click creation of complete listing

**AI Generates:**
- Product title (marketplace-optimized, max 72 chars)
- Short description (10-500 chars)
- Long description (50-5000 chars)
- Highlights (3-5 bullet points)
- Search keywords (5-10 terms)
- Category suggestions
- Pricing model recommendations

**Requirements:**
- Amazon Bedrock access (Claude 3.5 Sonnet or 3.7 Sonnet)
- Product documentation or website
- Basic product knowledge

**Time:** 5-10 minutes total

### Manual Form Workflow (Full Control)

**Process:**
- Fill out 8 stages sequentially
- Complete control over every field
- Real-time validation
- Save and resume anytime

**Best For:**
- Experienced users
- Specific content requirements
- Brand compliance needs
- Pre-written content

**Time:** 20-30 minutes total

## The 8-Stage Workflow

### Stage 1: Product Information
**Required:** Title, Logo S3 URL, Short/Long Description, Highlight, Support Details, Categories, Keywords  
**Optional:** SKU, Video URL, Additional Highlights, Resources  
**Time:** 5-10 minutes

### Stage 2: Fulfillment Options
**Required:** Fulfillment URL (HTTPS)  
**Optional:** Quick Launch configuration  
**Time:** 2-3 minutes

### Stage 3: Pricing Configuration
**Required:** Pricing model (usage/contract/hybrid), Dimensions (1-24)  
**Features:** Auto-generate API IDs, dimension creation wizard  
**Time:** 5-10 minutes

### Stage 4: Price Review
**Required:** Purchasing option, Contract durations  
**Note:** Test pricing set to $0.001  
**Time:** 3-5 minutes

### Stage 5: Refund Policy
**Required:** Refund policy text (50-5000 chars)  
**Time:** 2-3 minutes

### Stage 6: EULA Configuration
**Required:** EULA type (SCMP or Custom)  
**Optional:** Custom EULA S3 URL (if custom)  
**Time:** 2-3 minutes

### Stage 7: Offer Availability
**Required:** Availability type (all countries/with exclusions/allowlist)  
**Optional:** Country codes  
**Time:** 2-3 minutes

### Stage 8: Allowlist (Optional)
**Optional:** AWS account IDs to allowlist  
**Time:** 1-2 minutes

## Architecture

### Master Orchestrator
- Manages workflow state across 8 stages
- Routes to appropriate sub-agent
- Tracks progress (0-100%)
- Handles stage transitions
- Aggregates all data

### Sub-Agents
Each sub-agent specializes in one stage:
- Focused instructions
- Stage-specific validation
- Clear completion criteria
- Reduced complexity

### Benefits
- ✅ Clear, guided workflow
- ✅ Real-time progress tracking
- ✅ Comprehensive validation
- ✅ Can go back and edit
- ✅ Save/resume capability
- ✅ Educational explanations

## AWS Configuration

### Credentials
```bash
# Check status
aws sts get-caller-identity

# Refresh if needed
./setup_aws_credentials.sh
```

### Recommended Model
**Claude 3.7 Sonnet** - 250 req/min (vs 1 req/min for Claude 3.5 Sonnet V2)

Update `config/multi_agent_config.yaml`:
```yaml
bedrock:
  model_id: "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
  region: "us-east-1"
```

### Rate Limits by Model
| Model | Rate Limit | Improvement |
|-------|------------|-------------|
| Claude 3.7 Sonnet | 250/min | 250x |
| Claude Sonnet 4 | 200/min | 200x |
| Claude 3 Haiku | 40/min | 40x |
| Claude 3.5 Sonnet V2 | 1/min | Current |

## Validation Rules

### Field Limits
- Product Title: 5-255 characters
- Short Description: 10-500 characters
- Long Description: 50-5000 characters
- Highlights: 5-250 characters each
- Support Description: 20-2000 characters
- Categories: 1-3 items
- Keywords: 1-10 items (max 50 chars each)
- Dimensions: 1-24 items
- Dimension API ID: 1-50 chars (lowercase, alphanumeric, underscores)
- Refund Policy: 50-5000 characters

### URL Formats
- Logo: S3 URL to PNG/JPG
- Fulfillment: HTTPS URL
- Custom EULA: S3 URL to PDF

### Other Rules
- Email: Valid email format
- Country Codes: ISO 3166-1 alpha-2
- Account IDs: 12-digit numbers

## Troubleshooting

### Rate Limit Errors
**Solution:** Agent has automatic retry with exponential backoff (2s, 4s, 8s, 16s, 32s)  
**Better:** Switch to Claude 3.7 Sonnet for 250x higher limits

### Maximum Iterations Reached
**Cause:** Agent hit 20 tool execution limit  
**Solution:** Break request into smaller steps, start new conversation  
**Fixed:** Multi-agent architecture reduces iterations per stage

### AWS Credentials Expired
```bash
./setup_aws_credentials.sh
```

### Validation Errors
- Check field lengths
- Verify URL formats (must be HTTPS)
- Ensure required fields provided
- Check array sizes (categories, keywords, dimensions)

## Testing

### Verify Installation
```bash
python3 test_setup.py
```

### Check Bedrock Models
```bash
python3 check_bedrock_models.py
```

### Test Multi-Agent System
```python
from agent.orchestrator import ListingOrchestrator

orchestrator = ListingOrchestrator()
print(f"Stage: {orchestrator.current_stage.name}")
print(f"Progress: {orchestrator.get_progress_percentage()}%")
```

## API Implementation

### Product vs Offer
**Critical:** AWS Marketplace has TWO entities:
- **Product** - What you're selling (title, description, highlights, etc.)
- **Offer** - How you're selling it (pricing, terms, support, etc.)

### Correct Workflow
1. `create_listing_draft` - Creates Product + Offer (includes highlights)
2. `get_listing_status` - Get product_id and offer_id
3. `add_dimensions(product_id)` - Add pricing dimensions to Product
4. `add_delivery_options(product_id)` - Add fulfillment URL to Product
5. `add_pricing(offer_id)` - Add pricing to Offer (NOT product!)
6. `update_support_terms(offer_id)` - Add refund policy to Offer (NOT product!)
7. `update_legal_terms(offer_id)` - Add EULA to Offer
8. `update_offer_availability(offer_id)` - Set geographic restrictions
9. `update_offer_targeting(offer_id)` - Optional account allowlist

### Product Operations (use product_id)
✅ `update_product_information(product_id)` - Title, descriptions, highlights  
✅ `add_dimensions(product_id)` - Pricing dimensions  
✅ `add_delivery_options(product_id)` - Fulfillment URL  

### Offer Operations (use offer_id)
✅ `add_pricing(offer_id)` - Pricing model and terms  
✅ `update_support_terms(offer_id)` - Refund policy  
✅ `update_legal_terms(offer_id)` - EULA configuration  
✅ `update_offer_availability(offer_id)` - Geographic restrictions  
✅ `update_offer_targeting(offer_id)` - Account allowlist  

### Common Mistakes
❌ `add_pricing(product_id)` - Wrong!  
✅ `add_pricing(offer_id)` - Correct!  

❌ `update_product_information(product_id, {"RefundPolicy": "..."})` - Wrong!  
✅ `update_support_terms(offer_id, "...")` - Correct!  

❌ Missing highlights in product creation - Wrong!  
✅ Include highlights array in `create_listing_draft()` - Correct!

## Project Structure

```
marketplace-listing-agent/
├── agent/
│   ├── orchestrator.py           # Master orchestrator
│   ├── marketplace_agent.py      # Main agent (legacy)
│   ├── sub_agents/               # 8 specialized agents
│   │   ├── base_agent.py
│   │   ├── product_information_agent.py
│   │   ├── fulfillment_agent.py
│   │   ├── pricing_config_agent.py
│   │   ├── price_review_agent.py
│   │   ├── refund_policy_agent.py
│   │   ├── eula_config_agent.py
│   │   ├── offer_availability_agent.py
│   │   └── allowlist_agent.py
│   ├── agentcore/                # Runtime, Gateway, Identity, Memory
│   └── tools/                    # AWS Marketplace API tools
├── config/
│   ├── multi_agent_config.yaml   # Multi-agent configuration
│   ├── agent_config.yaml         # Legacy agent config
│   └── marketplace_config.yaml   # Validation rules
├── docs/
│   └── MULTI_AGENT_ARCHITECTURE.md  # Architecture details
├── main.py                       # CLI interface
├── streamlit_app.py             # Streamlit UI
├── requirements.txt
└── GUIDE.md                     # This file
```

## Configuration Files

### `config/multi_agent_config.yaml`
- Stage definitions
- Validation rules
- Feature flags
- Orchestrator instructions

### `config/agent_config.yaml`
- Model selection
- Bedrock settings
- Agent instructions (legacy)

### `config/marketplace_config.yaml`
- AWS Marketplace validation rules
- Field limits
- Pricing models

## Development

### Adding a New Stage
1. Create sub-agent class extending `BaseSubAgent`
2. Implement required methods
3. Add to orchestrator
4. Update configuration
5. Add validation rules

### Testing Sub-Agents
```python
from agent.sub_agents import ProductInformationAgent

agent = ProductInformationAgent()
response = agent.process_stage("CloudSync Pro", {})
print(response)
```

### Debugging
```python
# Check orchestrator state
print(f"Current: {orchestrator.current_stage}")
print(f"Completed: {orchestrator.completed_stages}")
print(f"Progress: {orchestrator.get_progress_percentage()}%")

# Export state
state = orchestrator.export_data()
print(state)
```

## Resources

### Documentation
- **Architecture:** `docs/MULTI_AGENT_ARCHITECTURE.md`
- **Configuration:** `config/multi_agent_config.yaml`
- **This Guide:** `GUIDE.md`

### AWS Documentation
- [AWS Marketplace Seller Guide](https://docs.aws.amazon.com/marketplace/latest/userguide/)
- [AWS Marketplace Catalog API](https://docs.aws.amazon.com/marketplace/latest/APIReference/)
- [AWS Bedrock AgentCore](https://github.com/awslabs/amazon-bedrock-agentcore-samples)

### Support
- Check AWS credentials: `aws sts get-caller-identity`
- Verify Bedrock access: `python3 check_bedrock_models.py`
- Test setup: `python3 test_setup.py`

## Summary

**What it does:**
- Guides you through 8 stages of SaaS listing creation
- Validates all inputs against AWS Marketplace rules
- Tracks progress in real-time
- Creates complete listing specification
- Submits to AWS Marketplace Catalog API

**Key features:**
- Multi-agent architecture (1 orchestrator + 8 sub-agents)
- Comprehensive validation
- Progress tracking
- Save/resume capability
- Educational guidance

**Time to complete:** 20-40 minutes (depending on preparation)

**Status:** Ready to use! 🚀
