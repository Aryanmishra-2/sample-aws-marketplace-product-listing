# Buyer Experience Integration Flow

## Complete Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. Stack Deployment                          │
│  User deploys CloudFormation stack with SaaS integration       │
│  - DynamoDB tables, Lambda, API Gateway, SNS, IAM roles        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   2. SNS Confirmation                           │
│  User confirms SNS subscription via email                       │
│  - Enables marketplace event notifications                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              3. Buyer Experience Simulation                     │
│  User follows step-by-step guide to simulate purchase           │
│  - Access product in Management Portal                          │
│  - Validate fulfillment URL update                              │
│  - Review product information                                   │
│  - Simulate purchase process                                    │
│  - Complete account setup and registration                      │
│  - Verify registration success                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│           4. Complete Testing (Click Button)                    │
│  Frontend calls: POST /api/run-buyer-experience                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Backend: /run-buyer-experience                     │
│  1. Run BuyerExperienceAgent.simulate_buyer_journey()           │
│  2. Fetch pricing model from AWS Marketplace Catalog API        │
│  3. Analyze PricingTerms and Dimensions                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
                    ┌────┴────┐
                    │ Pricing │
                    │  Model  │
                    └────┬────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌────────┐    ┌──────────┐    ┌──────────┐
    │ Usage  │    │Contract  │    │Contract  │
    │ Based  │    │   with   │    │  Based   │
    │        │    │Consump.  │    │          │
    └───┬────┘    └────┬─────┘    └────┬─────┘
        │              │               │
        └──────┬───────┘               │
               │                       │
               ▼                       ▼
    ┌──────────────────┐    ┌──────────────────┐
    │ MeteringAgent    │    │PublicVisibility  │
    │                  │    │     Agent        │
    │ - Check customer │    │ - Prepare info   │
    │   entitlement    │    │ - Submit request │
    │ - Create records │    │ - AWS review     │
    │ - Trigger Lambda │    │ - Post-approval  │
    └────────┬─────────┘    └────────┬─────────┘
             │                       │
             ▼                       ▼
    ┌──────────────────┐    ┌──────────────────┐
    │ Metering Setup   │    │Public Visibility │
    │     Guide        │    │      Guide       │
    │                  │    │                  │
    │ 4 steps to       │    │ 4 steps to       │
    │ configure usage  │    │ request public   │
    │ tracking         │    │ visibility       │
    └──────────────────┘    └──────────────────┘
```

## Key Components

### Backend Endpoints

1. **`/run-buyer-experience`** (NEW)
   - Orchestrates the entire flow
   - Runs buyer experience agent
   - Detects pricing model
   - Routes to appropriate agent
   - Returns next step guidance

2. **`/buyer-experience-guide`**
   - Returns step-by-step buyer simulation guide

3. **`/metering-guide`**
   - Returns metering setup instructions

4. **`/public-visibility-guide`**
   - Returns public visibility request instructions

### Frontend Integration

**SaaS Integration Page** (`saas-integration/page.tsx`)
- "Complete Testing" button triggers `/run-buyer-experience`
- Automatically displays appropriate guide based on response
- Shows loading state during execution
- Handles errors gracefully

### Agent Routing Logic

```python
if pricing_model in ["Usage-based-pricing", "Contract-with-consumption"]:
    # Route to MeteringAgent
    metering_agent.check_entitlement_and_add_metering()
    next_step = "metering"
else:  # Contract-based-pricing
    # Route to PublicVisibilityAgent
    visibility_agent.raise_public_visibility_request()
    next_step = "public_visibility"
```

## Pricing Model Detection

### Primary Method: PricingTerms Analysis
```python
for term in pricing_terms:
    if term['Type'] == 'UsageBasedPricingTerm':
        has_usage_based = True
    elif term['Type'] in ['ConfigurableUpfrontPricingTerm', 'FixedUpfrontPricingTerm']:
        has_contract = True

# Determine model
if has_usage_based and has_contract:
    pricing_model = "Contract-with-consumption"
elif has_usage_based:
    pricing_model = "Usage-based-pricing"
elif has_contract:
    pricing_model = "Contract-based-pricing"
```

### Fallback Method: Dimensions Analysis
```python
for dim in dimensions:
    if 'Metered' in dim['Types']:
        pricing_model = "Usage-based-pricing"
    elif 'Entitled' in dim['Types']:
        pricing_model = "Contract-based-pricing"
```

## Benefits

✅ **Automated**: Single button click handles complex routing
✅ **Intelligent**: Adapts to product's pricing model
✅ **Seamless**: No manual decision-making required
✅ **Clear**: Step-by-step guidance for each path
✅ **Robust**: Fallback mechanisms for pricing detection
