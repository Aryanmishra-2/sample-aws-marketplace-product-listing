# AWS Marketplace SaaS Listing Creator - Complete Documentation

## Table of Contents
1. [Quick Start](#quick-start)
2. [Features](#features)
3. [Pricing Models](#pricing-models)
4. [Publishing Guide](#publishing-guide)
5. [Technical Details](#technical-details)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites
- AWS Account with Marketplace Seller registration
- AWS credentials configured
- Python 3.8+
- Bedrock access enabled

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Configure AWS credentials
./setup_aws_credentials.sh

# Run the app
streamlit run streamlit_guided_app.py
```

### Create Your First Listing
1. Enter your product website URL
2. AI analyzes and suggests configurations
3. Review and customize product information
4. Configure pricing model and dimensions
5. Set support terms and policies
6. **Enable auto-publish** (checked by default)
7. Click "Create Listing"
8. **Your listing is published to Limited stage automatically!**

---

## Features

### AI-Powered Analysis
- Automatically extracts product information from your website
- Suggests optimal pricing model based on your product
- Recommends pricing dimensions
- Generates product descriptions and highlights

### Supported Pricing Models
1. **Usage-based**: Pay-as-you-go metered pricing
2. **Contract-based**: Upfront commitment pricing
3. **Contract with Consumption**: Hybrid model (contract + overages)

### Auto-Publish to Limited
- **One-click publishing** - Automatically publishes to Limited stage
- **Immediate testing** - Test your listing right after creation
- **Optional buyer accounts** - Add AWS account IDs for testing
- **Enabled by default** - Can disable for manual publishing

### 8-Stage Workflow
1. Product Information (title, description, logo)
2. Fulfillment Configuration (URLs)
3. Pricing & Dimensions
4. Offer Creation
5. Support Terms
6. EULA Configuration
7. Refund Policy
8. Geographic Availability

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

**Best For**: Enterprise SaaS, annual subscriptions, predictable revenue models

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

**Configuration Steps**:
1. Select "Contract with Consumption" pricing model
2. Add Entitled dimensions (what's included in contract)
3. Add Metered dimensions (what's billed as overage)
4. Select contract durations
5. System automatically:
   - Adds all dimensions to product
   - Creates ConfigurableUpfrontPricingTerm for Entitled dimensions
   - Creates UsageBasedPricingTerm for Metered dimensions
   - Combines both in a single changeset

**Technical Implementation**:
- Dimensions and pricing added together in one changeset
- Two pricing terms in the offer:
  - `ConfigurableUpfrontPricingTerm` for contract/entitled
  - `UsageBasedPricingTerm` for usage/metered
- AWS Marketplace automatically handles the hybrid billing

---

## Publishing Guide

### Auto-Publish (Recommended)

**Default behavior** - Your listing is automatically published to Limited stage:

1. **Enable auto-publish** (checked by default in UI)
2. **Review offer information** (auto-filled from product details)
3. **Optionally add buyer accounts** for testing
4. **Click "Create Listing"**
5. **Wait 2-3 minutes** for completion
6. **Test immediately!** Your listing is live in Limited stage

**What happens automatically:**
- Creates listing (all 8 stages)
- Sets offer name and description
- Adds renewal terms (for Contract pricing)
- Optionally sets buyer account allowlist
- Releases product and offer to Limited
- Polls for completion

### Manual Publishing (If Auto-Publish Disabled)

If you disabled auto-publish, follow these steps:

#### Step 1: Open AWS Marketplace Management Portal
1. Go to [AWS Marketplace Management Portal](https://aws.amazon.com/marketplace/management/products)
2. Sign in with your AWS seller account

#### Step 2: Find Your Product
1. Click **"Products"** in left sidebar
2. Search for your Product ID (shown in success page)
3. Click on the product name

3. Add offer name and description
4. Add renewal terms (for Contract pricing)
5. Publish product to Limited
6. Publish offer to Limited

See AWS Marketplace Management Portal for detailed steps.

### Publish to Public (When Ready)
1. Update pricing from test values ($0.001) to production prices
2. Submit for AWS Marketplace review
3. AWS reviews (typically 1-2 weeks)
4. Once approved, listing is publicly available

---

## Technical Details

### Character Sanitization
AWS Marketplace doesn't support certain Unicode characters. The app automatically converts:
- Smart quotes → Regular quotes
- Em/en dashes → Hyphens
- Ellipsis → Three dots
- Trademark symbols → (TM)
- Copyright symbols → (C)
- And more...

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

**UI to API Pricing Model**:
- "Usage" → `"Usage"`
- "Contract" → `"Contract"`
- "Contract with Consumption" → `"Contract"` (with mixed dimension types)

**Contract Durations**:
- UI: "12 Months"
- API: `"P12M"` (ISO 8601 duration format)

### Workflow Architecture

The app uses a multi-stage orchestrator pattern:
1. Each stage has a dedicated sub-agent
2. Stages execute sequentially
3. Data flows between stages via orchestrator
4. All API calls use AWS Marketplace Catalog API
5. Changesets track all modifications

---

## Troubleshooting

### Common Issues

#### 1. "MISSING_DESCRIPTION" Error
**Problem**: Offer can't be published without description

**Solution**: 
- Add offer description in AWS Marketplace Management Portal
- Navigate to Offers → Edit offer information → Add description

#### 2. Invalid Dimension Types
**Problem**: API rejects dimension configuration

**Solution**:
- Usage pricing: Use `["Metered", "ExternallyMetered"]`
- Contract pricing: Use `["Entitled"]`
- Both types required for Metered dimensions

#### 3. Hybrid Pricing Not Working
**Problem**: Contract with Consumption validation fails

**Solution**:
- Must have at least 1 Entitled dimension
- Must have at least 1 Metered dimension
- Must select contract durations

#### 4. Character Encoding Errors
**Problem**: AWS rejects text with Unicode characters

**Solution**:
- App automatically sanitizes text
- Review sanitization warnings
- Manually edit if needed

#### 5. Changeset Stuck in PREPARING
**Problem**: Changeset doesn't complete

**Solution**:
- Wait 5-10 minutes (normal processing time)
- Check AWS Marketplace Management Portal
- Use `check_changeset_status.py` script

### Debug Tools

**Check Changeset Status**:
```bash
python check_changeset_status.py <changeset-id>
```

**Verify Bedrock Access**:
```bash
python check_bedrock_models.py
```

**Test AWS Credentials**:
```bash
python test_setup.py
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
- [AWS Marketplace Seller Guide](https://docs.aws.amazon.com/marketplace/latest/userguide/what-is-marketplace.html)
- [SaaS Product Guidelines](https://docs.aws.amazon.com/marketplace/latest/userguide/saas-guidelines.html)
- [Pricing Models](https://docs.aws.amazon.com/marketplace/latest/userguide/saas-pricing-models.html)
- [Testing Your Product](https://docs.aws.amazon.com/marketplace/latest/userguide/saas-prepare.html)

### Support
- AWS Marketplace Seller Support
- AWS Support Console
- Marketplace Seller Forums

---

## Version History

### Current Version
- ✅ All 3 pricing models supported
- ✅ AI-powered product analysis
- ✅ Character sanitization
- ✅ Manual publishing guide
- ✅ Comprehensive validation
- ✅ 8-stage workflow

### Recent Changes
- Re-implemented Contract with Consumption pricing
- Removed auto-publish (replaced with manual steps)
- Enhanced success page with detailed instructions
- Fixed dimension type combinations
- Added hybrid pricing validation

---

## File Structure

```
.
├── streamlit_guided_app.py          # Main application
├── streamlit_launcher.py            # App launcher
├── agent/
│   ├── orchestrator.py              # Workflow orchestrator
│   ├── tools/
│   │   └── listing_tools.py         # AWS Marketplace API tools
│   └── sub_agents/                  # Stage-specific agents
├── config/
│   ├── agent_config.yaml            # Agent configuration
│   └── marketplace_config.yaml      # Marketplace settings
├── docs/
│   └── MULTI_AGENT_ARCHITECTURE.md  # Architecture details
├── DOCUMENTATION.md                 # This file
└── README.md                        # Project overview
```

---

## License
See LICENSE file for details.

## Contributing
Contributions welcome! Please follow AWS Marketplace guidelines and test thoroughly.
