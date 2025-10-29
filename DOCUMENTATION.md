# AWS Marketplace SaaS Listing Creator - Complete Documentation

## Table of Contents
1. [Quick Start](#quick-start)
2. [Features](#features)
3. [Pricing Models](#pricing-models)
4. [Workflow Guide](#workflow-guide)
5. [Technical Details](#technical-details)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Installation

```bash
# The app is ready to run with pre-installed dependencies
./run_streamlit.sh
```

### Create Your First Listing

1. Click "Start AI-Guided Creation"
2. Enter your product website URL
3. AI analyzes and generates all content
4. Review and customize
5. Click "Create Listing"
6. **Your listing is created!**

---

## Features

### AI-Powered Analysis
- Automatically extracts product information from your website
- Suggests optimal pricing model
- Recommends pricing dimensions
- Generates product descriptions and highlights
- Selects appropriate categories and keywords

### Supported Pricing Models
1. **Usage-based**: Pay-as-you-go metered pricing
2. **Contract-based**: Upfront commitment pricing
3. **Contract with Consumption**: Hybrid model (contract + overages)

### Auto-Publish to Limited
- **One-click publishing** to Limited stage
- **Immediate testing** with your AWS account
- **Optional buyer accounts** for testing
- **Enabled by default**

### 8-Stage Workflow
1. Product Information (title, description, logo)
2. Fulfillment Configuration (URLs)
3. Pricing & Dimensions
4. Price Review (contract durations)
5. Refund Policy
6. EULA Configuration
7. Geographic Availability
8. Account Allowlist (optional)

---

## Pricing Models

### 1. Usage-Based Pricing

**Best For**: Pay-as-you-go services, API platforms, consumption-based products

**How It Works**:
- Customers pay only for what they use
- Metered dimensions track usage
- Billed monthly based on actual consumption

**Example**:
```
Dimension: API Calls
Type: Metered
Price: $0.001 per call
```

**Dimension Requirements**:
- Type: `["Metered", "ExternallyMetered"]` (both required)
- At least 1 dimension, maximum 24

---

### 2. Contract-Based Pricing

**Best For**: Enterprise SaaS, annual subscriptions, predictable revenue

**How It Works**:
- Customers commit to a contract period (1-36 months)
- Pay upfront for entitled dimensions
- Fixed pricing regardless of usage

**Example**:
```
Dimension: User Seats
Type: Entitled
Contract: 12 months
Price: $1,000/year for 100 seats
```

**Dimension Requirements**:
- Type: `["Entitled"]`
- Contract durations: 1, 3, 6, 12, 24, or 36 months

---

### 3. Contract with Consumption (Hybrid)

**Best For**: Products with base usage + overages, scalable SaaS platforms

**How It Works**:
- Customers commit to a base contract
- Entitled dimensions included in contract
- Metered dimensions for usage beyond entitlement
- Pay-per-use for overages

**Example**:
```
Contract: $1,000/year
Entitled Dimension: 100 Included Users
Metered Dimension: Additional Users at $10/user/month

Customer gets 100 users included, pays $10/month for each additional user
```

**Dimension Requirements**:
- At least 1 Entitled dimension: `["Entitled"]`
- At least 1 Metered dimension: `["Metered", "ExternallyMetered"]`
- Contract durations required
- Both dimension types must be present

---

## Workflow Guide

### Step 1: Provide Product Information

Enter your product URLs:
- **Product Website** (required) - Main landing page
- **Documentation URL** (optional) - Technical docs
- **Pricing Page** (optional) - Existing pricing info

The AI will analyze these URLs to understand your product.

### Step 2: AI Analysis

The AI performs:
1. **Product Analysis** - Understands product type, features, audience
2. **Content Generation** - Creates title, descriptions, highlights
3. **Pricing Suggestion** - Recommends optimal pricing model
4. **Category Selection** - Suggests AWS Marketplace categories

This takes 30-60 seconds.

### Step 3: Review & Configure

Review and edit AI-generated content:

#### Product Information
- **Product Title** (5-72 chars) - Keep it clear and compelling
- **Logo S3 URL** - Upload logo to S3 first
- **Short Description** (10-500 chars) - For search results
- **Long Description** (50-5000 chars) - Detailed features
- **Highlights** (1-3) - Key features, 5-250 chars each
- **Categories** (1-3) - AWS Marketplace categories
- **Keywords** (1-10) - Search keywords, max 50 chars each

#### Support Information
- **Support Email** - Valid email address
- **Fulfillment URL** - Your SaaS signup/activation URL
- **Support Description** (20-2000 chars) - How you provide support

#### Pricing Configuration
- **Pricing Model** - Usage, Contract, or Hybrid
- **Dimensions** - Add 1-24 pricing dimensions:
  - Dimension Name (display name)
  - Dimension Key (API identifier)
  - Description (what it measures)
  - Type (Metered or Entitled)
- **Contract Durations** (for Contract pricing) - Select 1-6 options

#### Refund Policy
- **Refund Policy** (50-5000 chars) - AI generates template, edit as needed

#### EULA
- **SCMP** (Standard Contract) - Recommended, pre-approved by AWS
- **Custom EULA** - Provide S3 URL to your custom EULA PDF

#### Geographic Availability
- **All countries** - Worldwide availability
- **All except specific** - Exclude certain countries
- **Only specific countries** - Allowlist specific countries

#### Account Allowlist (Optional)
- Add AWS account IDs for Limited testing
- Leave empty for public offer

#### Auto-Publish to Limited
- **Enable** - Automatically publish to Limited stage
- **Offer Name** - Defaults to product title
- **Offer Description** - Brief description
- **Buyer Accounts** - Optional AWS account IDs for testing

### Step 4: Create Listing

Click "Create Listing" and the app will:
1. Create product with all information
2. Configure fulfillment URL
3. Add pricing dimensions
4. Apply pricing terms
5. Set support terms
6. Configure EULA
7. Set geographic availability
8. Apply account allowlist (if specified)
9. **Publish to Limited stage** (if enabled)

You'll receive:
- **Product ID** - Use this to find your product
- **Offer ID** - Use this to manage your offer

### Step 5: Test in Limited Stage

If auto-publish is enabled:
1. Go to [AWS Marketplace](https://aws.amazon.com/marketplace)
2. Search for your product title
3. Subscribe and test the flow
4. Verify fulfillment URL works
5. Check metering/entitlement (if applicable)

### Step 6: Publish to Public

When ready:
1. Update pricing from test values ($0.001) to production
2. Go to [Management Portal](https://aws.amazon.com/marketplace/management/products)
3. Find your product
4. Submit for AWS review
5. Once approved, listing is public

---

## Technical Details

### Character Sanitization

AWS Marketplace doesn't support certain Unicode characters. The app automatically converts:
- Smart quotes → Regular quotes
- Em/en dashes → Hyphens
- Ellipsis → Three dots
- Trademark symbols → (TM)
- Copyright symbols → (C)

### Dimension Types

**For Usage Pricing**:
```json
{
  "Key": "api_calls",
  "Description": "Number of API calls",
  "Types": ["Metered", "ExternallyMetered"]
}
```

**For Contract Pricing**:
```json
{
  "Key": "users",
  "Description": "Number of user seats",
  "Types": ["Entitled"]
}
```

**For Hybrid Pricing**:
```json
{
  "dimensions": [
    {
      "Key": "included_users",
      "Description": "Users included in contract",
      "Types": ["Entitled"]
    },
    {
      "Key": "additional_users",
      "Description": "Additional users beyond contract",
      "Types": ["Metered", "ExternallyMetered"]
    }
  ]
}
```

### API Mapping

**Pricing Model**:
- UI: "Usage" → API: `"Usage"`
- UI: "Contract" → API: `"Contract"`
- UI: "Contract with Consumption" → API: `"Contract"` (with mixed dimensions)

**Contract Durations**:
- UI: "12 Months" → API: `"P12M"` (ISO 8601 format)

### Architecture

```
Streamlit UI
    ↓
StrandsMarketplaceAgent (Strands SDK)
    ↓
ListingOrchestrator (8-stage workflow)
    ↓
Sub-Agents (specialized per stage)
    ↓
ListingTools (AWS Marketplace Catalog API)
```

**Components**:
- **Strands Agent** - LLM interaction with @tool decorators
- **Orchestrator** - Manages workflow state and transitions
- **Sub-Agents** - 8 specialized agents (one per stage)
- **Listing Tools** - AWS Marketplace Catalog API wrapper

---

## Troubleshooting

### Common Issues

#### 1. Import Error: "No module named 'strands'"

**Solution**:
```bash
pip install strands-agents strands-agents-tools
```

Note: Package is `strands-agents` but import is `from strands import Agent`

#### 2. Model Access Denied

**Solution**:
1. Go to https://console.aws.amazon.com/bedrock/
2. Navigate to: Model access → Manage model access
3. Enable: Claude 3.7 Sonnet
4. Wait 2-3 minutes for activation

#### 3. AWS Credentials Not Found

**Solution**:
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and region
```

#### 4. Invalid Logo URL

**Problem**: Logo URL must be S3 URL

**Solution**:
1. Upload logo to S3 bucket
2. Make it publicly readable
3. Use format: `https://bucket-name.s3.region.amazonaws.com/logo.png`

#### 5. Dimension Type Error

**Problem**: Wrong dimension types for pricing model

**Solution**:
- **Usage pricing**: Use Metered dimensions
- **Contract pricing**: Use Entitled dimensions
- **Hybrid pricing**: Use both types

#### 6. Changeset Stuck in PREPARING

**Problem**: AWS is processing the changeset

**Solution**:
- Wait 5-10 minutes (normal processing time)
- Check [Management Portal](https://aws.amazon.com/marketplace/management/products)
- Changeset will complete automatically

### Debug Tools

**Check Test Results**:
```bash
export VIRTUAL_ENV=/Users/avivenk/Library/CloudStorage/WorkDocsDrive-Documents/MPAgent/venv
export PATH="$VIRTUAL_ENV/bin:$PATH"
python test_strands_migration.py
```

**Check Agent Status**:
```python
from agent.strands_marketplace_agent import StrandsMarketplaceAgent
agent = StrandsMarketplaceAgent()
status = agent.get_workflow_status()
print(status)
```

---

## Best Practices

### Pricing Strategy
1. Start with test prices ($0.001) in Limited stage
2. Test full subscription flow
3. Update to production prices before public launch
4. Consider offering multiple contract durations
5. Use hybrid pricing for scalable products

### Product Information
1. Use clear, concise product titles (max 72 chars)
2. Write customer-focused descriptions
3. Highlight key benefits in bullet points
4. Use professional logo (120x120px minimum)
5. Provide comprehensive support information

### Testing
1. Always test in Limited stage first
2. Verify fulfillment URL works correctly
3. Test metering integration (if applicable)
4. Check entitlement provisioning
5. Validate billing and invoicing

### Launch Checklist
- [ ] Product information complete and accurate
- [ ] Pricing tested and validated
- [ ] Fulfillment URL working
- [ ] Support contact information correct
- [ ] EULA reviewed and approved
- [ ] Tested in Limited stage
- [ ] Production pricing configured
- [ ] Marketing materials ready

---

## Additional Resources

### AWS Documentation
- [Seller Guide](https://docs.aws.amazon.com/marketplace/latest/userguide/)
- [SaaS Guidelines](https://docs.aws.amazon.com/marketplace/latest/userguide/saas-guidelines.html)
- [Pricing Models](https://docs.aws.amazon.com/marketplace/latest/userguide/saas-pricing-models.html)
- [Testing Guide](https://docs.aws.amazon.com/marketplace/latest/userguide/saas-prepare.html)

### Strands SDK
- Package: `strands-agents`
- Import: `from strands import Agent, tool`
- [AWS Bedrock AgentCore](https://aws.amazon.com/bedrock/)

---

## Version History

### Current Version (Strands SDK)
- ✅ All 3 pricing models supported
- ✅ AI-powered product analysis
- ✅ Character sanitization
- ✅ Auto-publish to Limited
- ✅ Comprehensive validation
- ✅ 8-stage workflow
- ✅ Strands SDK integration
- ✅ 27% less code than previous version

---

**Ready to create your listing?**

```bash
./run_streamlit.sh
```
