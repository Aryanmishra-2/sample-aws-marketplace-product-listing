# Buyer Experience Integration with Pricing-Based Routing

## Overview

This integration adds automated buyer experience testing with intelligent routing to the appropriate next steps based on the product's pricing model.

## Flow

### 1. Stack Deployment
- User deploys CloudFormation stack for SaaS integration
- Stack creates DynamoDB tables, Lambda functions, API Gateway, SNS topics, and IAM roles

### 2. SNS Confirmation
- User confirms SNS subscription via email
- This enables notifications for marketplace events

### 3. Buyer Experience Simulation
- User clicks "I've Confirmed" to proceed to buyer experience testing
- System loads the buyer experience guide with step-by-step instructions
- User follows the guide to simulate a buyer purchasing and registering

### 4. Complete Testing (Automated Routing)
- User clicks "Complete Testing" button
- **Backend automatically:**
  1. Runs buyer experience agent to verify the simulation
  2. Fetches the product's pricing model from AWS Marketplace
  3. Routes to the appropriate agent based on pricing model:
     - **Usage-based pricing** → Metering Agent
     - **Contract-with-consumption** → Metering Agent
     - **Contract-based pricing** → Public Visibility Agent

### 5. Next Steps (Pricing-Dependent)

#### For Usage-Based Pricing:
- **Metering Setup Guide** is displayed
- Steps include:
  1. Check customer entitlement in DynamoDB
  2. Create metering records
  3. Trigger metering Lambda function
  4. Verify metering success

#### For Contract-Based Pricing:
- **Public Visibility Request Guide** is displayed
- Steps include:
  1. Prepare product information
  2. Submit public visibility request
  3. AWS review process (1-3 days)
  4. Post-approval actions

## Architecture

### Backend Endpoints

#### `/run-buyer-experience` (NEW)
- **Purpose**: Execute buyer experience simulation and route to next step
- **Input**: 
  - `product_id`: AWS Marketplace product ID
  - `credentials`: AWS credentials
- **Process**:
  1. Runs `BuyerExperienceAgent.simulate_buyer_journey()`
  2. Fetches pricing model from AWS Marketplace Catalog API
  3. Routes to appropriate agent:
     - `MeteringAgent` for usage-based pricing
     - `PublicVisibilityAgent` for contract-based pricing
- **Output**:
  - `buyer_result`: Result of buyer experience simulation
  - `pricing_model`: Detected pricing model
  - `next_step`: Either "metering" or "public_visibility"
  - `next_step_result`: Result from the routed agent

#### `/buyer-experience-guide`
- Returns step-by-step guide for buyer experience testing

#### `/metering-guide`
- Returns step-by-step guide for metering setup

#### `/public-visibility-guide`
- Returns step-by-step guide for public visibility request

### Frontend Integration

#### SaaS Integration Page (`saas-integration/page.tsx`)
- Updated "Complete Testing" button to call `/run-buyer-experience`
- Automatically displays appropriate guide based on routing result
- Shows loading state during buyer experience execution

### Agent Integration

#### BuyerExperienceAgent
- Guides user through marketplace purchase simulation
- Verifies registration completion
- Checks DynamoDB for customer records

#### MeteringAgent
- Creates test customer if needed
- Adds metering records to DynamoDB
- Triggers Lambda function for BatchMeterUsage API calls

#### PublicVisibilityAgent
- Collects pricing dimension values
- Submits change set to AWS Marketplace Catalog API
- Requests visibility change from Limited to Public

## Pricing Model Detection

The system detects pricing models by analyzing:
1. **PricingTerms** in AWS Marketplace Catalog API response:
   - `UsageBasedPricingTerm` → Usage-based
   - `ConfigurableUpfrontPricingTerm` or `FixedUpfrontPricingTerm` → Contract-based
   - Both → Contract-with-consumption

2. **Dimensions** (fallback):
   - `Metered` type → Usage-based
   - `Entitled` type → Contract-based

## Benefits

1. **Automated Routing**: No manual decision-making required
2. **Pricing-Aware**: Adapts workflow to product's pricing model
3. **Seamless Experience**: Single button click handles complex routing logic
4. **Error Handling**: Graceful fallbacks if pricing model detection fails
5. **Clear Guidance**: Step-by-step instructions for each path

## Testing

To test the integration:

1. Deploy a SaaS product with usage-based pricing
2. Complete stack deployment and SNS confirmation
3. Click "Complete Testing" → Should route to Metering Guide

4. Deploy a SaaS product with contract-based pricing
5. Complete stack deployment and SNS confirmation
6. Click "Complete Testing" → Should route to Public Visibility Guide

## Future Enhancements

- Add progress indicators during buyer experience execution
- Implement automatic metering verification
- Add CloudWatch logs integration for debugging
- Support for hybrid pricing models
