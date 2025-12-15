# AWS Marketplace Pricing Models Guide

## Overview

AWS Marketplace offers flexible pricing models to help sellers monetize their products effectively. This guide covers all available pricing models and how to implement them.

## General Pricing Models

### 1. Annual Pricing

**Description:**
Offer products with 12-month subscriptions providing savings compared to hourly pricing.

**How it works:**
- Customers subscribe for 12 months
- Invoiced upfront for the subscription period
- Charged hourly after subscription expires
- Charged for excess instances beyond subscription

**Features:**
- Multi-year contracts supported
- Custom duration contracts available
- Installment payment plans
- Automatic renewal options

**Best for:**
- Products with predictable usage
- Enterprise customers
- Long-term commitments
- Providing discounts for annual commitment

**Requirements:**
- Agree to annual product refund policies
- Define annual pricing tiers
- Set up renewal handling

**Refund Policy:**
Sellers must establish clear refund policies for annual subscriptions, including:
- Cancellation terms
- Prorated refunds
- Upgrade/downgrade policies

### 2. Usage Pricing

**Description:**
Charge customers based on actual product usage.

**How it works:**
- Customers pay only for what they use
- Metering tracks usage in real-time
- Billed hourly, daily, or monthly
- No upfront commitment required

**Usage Dimensions:**
- **Per Hour:** Instance hours, compute hours
- **Per User:** Active users, concurrent users
- **Per Unit:** API calls, transactions, requests
- **Per Data:** GB transferred, GB stored, GB processed
- **Per Resource:** Hosts scanned, devices monitored

**Best for:**
- Variable usage patterns
- Pay-as-you-go models
- Products with unpredictable usage
- Attracting customers who want flexibility

**Implementation:**
- Define usage dimensions
- Integrate with Metering Service
- Send usage records regularly
- Set per-unit pricing

### 3. Contract Pricing

**Description:**
Customers purchase licenses upfront for a specific duration.

**How it works:**
- Fixed pricing for contract period
- Upfront or installment payments
- No usage metering required
- Entitlements define access levels

**Contract Types:**
- **Fixed Duration:** 1 month, 1 year, 2 years, 3 years
- **Custom Duration:** Negotiate specific timeframes
- **Auto-renewal:** Automatic contract renewal
- **One-time:** Single purchase, no renewal

**Features:**
- AWS License Manager integration
- Entitlement management
- Upgrade/downgrade support
- Renewal automation

**Best for:**
- Enterprise customers
- Predictable revenue
- Products with fixed capacity
- Long-term customer relationships

**Requirements:**
- IAM role for License Manager
- Entitlement Service integration
- Define contract dimensions
- Set up renewal processes

### 4. Bring Your Own License (BYOL)

**Description:**
Customers use existing licenses with AWS infrastructure.

**How it works:**
- Customers already own product licenses
- Deploy on AWS using existing licenses
- No additional software fees through AWS Marketplace
- May pay for AWS infrastructure costs

**Use Cases:**
- Customers with existing enterprise agreements
- License portability from on-premises
- Compliance requirements
- Cost optimization for existing customers

**Best for:**
- Established software vendors
- Enterprise products
- Customers with existing licenses
- Hybrid cloud deployments

**Requirements:**
- License verification mechanism
- Clear BYOL terms in EULA
- Support for license validation
- Additional seller registration requirements

## Product-Specific Pricing Models

### AMI Product Pricing

**Available Models:**
- Hourly pricing
- Annual pricing
- Usage pricing
- Contract pricing
- BYOL

**Pricing Dimensions:**
- Per instance hour
- Per instance type
- Per software feature
- Per user

**Features:**
- Instance type-based pricing
- Free tier options
- Volume discounts
- Regional pricing

### Container Product Pricing

**Available Models:**
- Usage pricing
- Contract pricing
- Contract with consumption

**Pricing Dimensions:**
- Per vCPU hour
- Per GB memory hour
- Per task hour
- Per pod hour
- Custom dimensions

**Features:**
- Kubernetes integration
- ECS/EKS support
- Flexible resource-based pricing

### SaaS Product Pricing

**Available Models:**
1. **SaaS Subscriptions (Pay-As-You-Go)**
   - Usage-based metering
   - Hourly billing
   - Variable costs

2. **SaaS Contracts**
   - Fixed upfront pricing
   - Entitlement-based
   - Predictable costs

3. **SaaS Contracts with Consumption**
   - Base contract + overage
   - Hybrid model
   - Flexibility with predictability

**Pricing Dimensions:**
- Per user
- Per API call
- Per GB data
- Per transaction
- Custom metrics

### Machine Learning Product Pricing

**Available Models:**
- Usage pricing
- Contract pricing

**Pricing Dimensions:**
- Per inference hour
- Per training hour
- Per model
- Per prediction
- Per data processed

**Integration:**
- Amazon SageMaker integration
- Automated metering
- Model package pricing

## Pricing Features and Options

### Free Trials

**Types:**
- Time-based (e.g., 30 days free)
- Usage-based (e.g., 100 API calls free)
- Feature-limited trials

**Benefits:**
- Attract new customers
- Reduce purchase friction
- Demonstrate value
- Convert to paid

**Implementation:**
- Configure in Management Portal
- Track trial usage
- Automate conversion
- Send notifications

### Private Offers

**Description:**
Negotiate custom pricing and terms with specific customers.

**Features:**
- Custom pricing
- Custom payment terms
- Custom EULAs
- Flexible contract duration
- Multi-year deals
- Installment payments

**Use Cases:**
- Enterprise deals
- Volume discounts
- Strategic partnerships
- Custom requirements

**Process:**
1. Negotiate with customer
2. Create private offer in portal
3. Specify customer AWS account
4. Set custom pricing and terms
5. Customer accepts offer
6. Contract activated

### Multi-Currency Pricing

**Description:**
Offer pricing in multiple currencies for private offers.

**Supported Currencies:**
- USD (US Dollar)
- EUR (Euro)
- GBP (British Pound)
- JPY (Japanese Yen)
- And others

**Benefits:**
- Simplify international sales
- Reduce currency risk for buyers
- Improve customer experience
- Expand global reach

### Flexible Payment Schedules

**Options:**
- Upfront payment
- Monthly installments
- Quarterly installments
- Annual installments
- Custom schedules

**Best for:**
- Large contracts
- Enterprise customers
- Multi-year deals
- Cash flow management

## Pricing Strategy Best Practices

### 1. Understand Your Costs
- Calculate infrastructure costs
- Include support costs
- Factor in AWS Marketplace fees
- Consider payment processing

### 2. Research Market Pricing
- Analyze competitor pricing
- Understand customer budgets
- Consider value proposition
- Test different price points

### 3. Choose Right Model
- Match pricing to usage patterns
- Consider customer preferences
- Align with product type
- Support multiple models if beneficial

### 4. Offer Flexibility
- Provide multiple tiers
- Support upgrades/downgrades
- Enable easy scaling
- Offer trials

### 5. Optimize for Conversion
- Clear pricing information
- Simple pricing structure
- Transparent costs
- No hidden fees

## Changing Pricing Models

**Process:**
- Contact AWS Marketplace Seller Operations
- Submit pricing change request
- Provide justification
- Wait for approval

**Timeline:**
- Expect 30-90 days processing time
- Varies by complexity
- May require customer migration

**Considerations:**
- Impact on existing customers
- Customer communication plan
- Migration strategy
- Refund policies

## Pricing and Refunds

### Refund Scenarios

**Subscription Cancellations:**
- Customer cancels subscription
- Prorated refunds may apply
- Depends on refund policy

**Upgrades/Downgrades:**
- Customer changes tier
- Prorated adjustments
- Immediate or next billing cycle

**Metering Errors:**
- Incorrect usage reported
- Seller corrects billing
- Customer receives credit

**Product Issues:**
- Product doesn't work as described
- Customer requests refund
- Seller evaluates case-by-case

### Refund Policies

**Requirements:**
- Define clear refund policy
- Include in product listing
- Communicate to customers
- Follow consistently

**Best Practices:**
- Be fair and reasonable
- Respond quickly to requests
- Document all refunds
- Learn from refund patterns

## Listing Fees

AWS Marketplace charges listing fees based on:

### Fee Structure

**Standard Offers:**
- 1.5% to 20% of transaction value
- Varies by offer type
- Varies by deployment method
- Varies by total contract value

**Regional Fees:**
- Additional fees for specific jurisdictions
- EMEA transactions
- Japan transactions
- Other regions

**Fee Calculation:**
- Based on customer payment
- Deducted before disbursement
- Shown in seller reports
- Varies by product type

### Fee Examples

**SaaS Products:**
- Typically 10-20% listing fee
- Lower for high-volume products
- Negotiable for strategic products

**AMI Products:**
- Typically 5-15% listing fee
- Varies by pricing model
- Volume discounts available

**Container Products:**
- Similar to AMI products
- 5-15% typical range

**Data Products:**
- Different fee structure
- Contact Seller Operations

## Updating Product Pricing

### Price Updates

**Process:**
1. Access Management Portal
2. Navigate to product
3. Update pricing information
4. Submit for review
5. Wait for approval

**Timeline:**
- Simple updates: 1-3 business days
- Complex changes: 5-10 business days
- Pricing model changes: 30-90 days

**Considerations:**
- Impact on existing customers
- Grandfathering options
- Customer notifications
- Effective date

### Adding Pricing Dimensions

**Process:**
- Define new dimension
- Set pricing
- Update product integration
- Test thoroughly
- Submit for approval

**Requirements:**
- Update metering code
- Update product description
- Communicate to customers

## Pricing Transparency

### Customer Visibility

**AWS Billing Console:**
- Customers see detailed usage
- Line items per dimension
- Total costs per billing cycle
- Historical usage data

**Cost and Usage Reports:**
- Detailed cost breakdown
- Per-unit rates
- Usage quantities
- Tag-based allocation

**Best Practices:**
- Clear dimension names
- Descriptive pricing
- Accurate metering
- Transparent communication

## Multi-Product Pricing

### Product Bundles

**Description:**
Offer multiple products together at discounted price.

**Benefits:**
- Increase average deal size
- Provide customer value
- Simplify purchasing
- Cross-sell products

**Implementation:**
- Create solution listing
- Include multiple products
- Set bundle pricing
- Manage entitlements

### Volume Discounts

**Tiers:**
- 0-100 units: Standard price
- 101-1000 units: 10% discount
- 1001+ units: 20% discount

**Implementation:**
- Define tier thresholds
- Set discount percentages
- Automate tier calculation
- Communicate clearly

## Pricing Resources

- **Pricing Calculator:** Estimate customer costs
- **Seller Reports:** Analyze pricing performance
- **Seller Operations:** Get pricing guidance
- **Documentation:** Detailed pricing guides
- **Best Practices:** Learn from successful sellers

## Next Steps

1. Choose appropriate pricing model
2. Define pricing dimensions
3. Set competitive prices
4. Configure in Management Portal
5. Test pricing with customers
6. Monitor and optimize
