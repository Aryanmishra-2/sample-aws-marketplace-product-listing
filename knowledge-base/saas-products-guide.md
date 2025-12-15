# AWS Marketplace SaaS Products Guide

## Overview

Software as a Service (SaaS) products allow you to deploy software hosted on AWS infrastructure and grant AWS Marketplace buyers access to the software in your AWS environment. As a seller, you are responsible for managing customer access, account creation, resource provisioning, and account management within your software.

## What is a SaaS Product?

With SaaS products on AWS Marketplace:
- Your software is hosted on AWS infrastructure
- Buyers access your software in your AWS environment
- You manage customer accounts and access
- AWS Marketplace handles billing and payments
- Customers are billed through their AWS account

## Prerequisites

Before creating a SaaS product, you must:

1. **Register as AWS Marketplace Seller**
   - Complete seller registration process
   - Submit tax and banking information
   - Have AWS account in good standing

2. **Access Management Portal**
   - Use AWS Marketplace Management Portal
   - Set up IAM roles for access
   - Avoid using root account credentials

3. **Plan Your SaaS Product**
   - Determine pricing model
   - Define product features
   - Prepare integration strategy

## SaaS Product Lifecycle

### 1. Product Creation
- Create product listing in Management Portal
- Define product metadata and description
- Set up initial configuration

### 2. Integration
- Integrate with AWS Marketplace APIs
- Implement customer onboarding flow
- Configure metering or entitlement checking

### 3. Testing
- Test integration in limited visibility mode
- Verify customer subscription flow
- Validate billing and metering

### 4. Launch
- Submit for public visibility
- AWS Marketplace Operations reviews product
- Product goes live to customers

### 5. Management
- Monitor customer subscriptions
- Update product information
- Manage pricing and offers

## SaaS Pricing Models

### 1. SaaS Subscriptions (Pay-As-You-Go)
**How it works:**
- Customers pay based on actual usage
- You meter customer usage hourly
- Send metering records to AWS Marketplace
- AWS bills customers based on your metering data

**Best for:**
- Variable usage patterns
- Usage-based pricing (per user, per GB, per API call)
- Products where consumption varies significantly

**Requirements:**
- Integrate with AWS Marketplace Metering Service
- Send metering records hourly (recommended)
- Define pricing dimensions (e.g., users, data processed)

### 2. SaaS Contracts
**How it works:**
- Customers purchase upfront licenses
- Fixed pricing for contract duration
- No usage metering required
- Customers pay upfront or in installments

**Best for:**
- Predictable pricing
- Enterprise customers
- Annual or multi-year commitments

**Requirements:**
- Integrate with AWS Marketplace Entitlement Service
- Verify customer entitlements
- Support contract renewals

### 3. SaaS Contracts with Pay-As-You-Go
**How it works:**
- Combines contract and subscription models
- Customers purchase base contract
- Additional usage beyond contract is metered
- Provides flexibility and predictability

**Best for:**
- Products with baseline + overage usage
- Enterprise customers with variable needs
- Hybrid pricing strategies

**Requirements:**
- Integrate with both Metering and Entitlement Services
- Track contract entitlements
- Meter usage beyond entitlements

## Creating a SaaS Product

### Step 1: Decide to List a SaaS Product
- Have a SaaS product ready to sell
- Review SaaS product guidelines
- Understand integration requirements

### Step 2: Determine Pricing and Offer Type
- Choose between subscription, contract, or hybrid
- Define pricing dimensions
- Set pricing tiers and rates

### Step 3: Collect Required Assets

**Product Logo URL**
- Publicly accessible Amazon S3 URL
- Clear image of product logo
- Meets size and format requirements

**End User License Agreement (EULA)**
- Available as PDF file
- Link to Amazon S3 bucket
- Customers can review on product page

**Product Registration URL**
- URL where buyers are redirected after subscribing
- Your application's onboarding page
- Must handle AWS Marketplace tokens

**Product Metadata**
- Product name and description
- Category and keywords
- Feature highlights
- Screenshots and videos

**Support Information**
- Support email addresses
- Support URLs
- Support channels and hours

### Step 4: Submit Product for Integration
- Create product in Management Portal
- Product published as "limited" visibility
- Only available for integration and testing
- Receive product code and EventBridge configuration

**Important:** Keep product at reduced price during testing to avoid high costs during integration testing.

### Step 5: Integrate with AWS Marketplace

Integration requirements depend on your pricing model:

**For Subscriptions:**
- Implement customer onboarding
- Validate subscriptions via ResolveCustomer API
- Send metering records via BatchMeterUsage API
- Handle subscription notifications

**For Contracts:**
- Implement customer onboarding
- Check entitlements via GetEntitlements API
- Verify customer access levels
- Handle contract renewals

**For Contracts with Pay-As-You-Go:**
- Implement both subscription and contract flows
- Check entitlements for base contract
- Meter usage beyond entitlements
- Handle both notification types

### Step 6: Test Your Integration
- Subscribe to your own product
- Verify customer experience
- Test payment processing
- Validate metering/entitlement checking
- Confirm links work correctly

**Important:** Cancel test subscriptions before requesting public visibility.

### Step 7: Submit for Launch
- Update visibility to public
- AWS Marketplace Operations reviews product
- Team verifies integration and updates pricing
- Process takes 7-10 business days

## Customer Onboarding Flow

### 1. Customer Subscribes
- Customer finds product on AWS Marketplace
- Clicks "Subscribe" or "Continue to Subscribe"
- Accepts terms and pricing

### 2. Redirect to Your Application
- AWS Marketplace redirects to your registration URL
- URL includes temporary token parameter
- Token used to verify subscription

### 3. Resolve Customer
- Your application calls ResolveCustomer API
- Exchanges token for customer identifier
- Receives customer AWS account ID and product code

### 4. Create Customer Account
- Create account in your system
- Associate with AWS customer identifier
- Provision resources and access

### 5. Grant Access
- Customer can now use your product
- Begin metering usage (if subscription model)
- Check entitlements (if contract model)

## Metering for SaaS Subscriptions

### Metering Best Practices

**Meter Hourly**
- Send metering records every hour
- Provides granular visibility for customers
- Reduces risk of unreported usage

**Use BatchMeterUsage**
- Required for all SaaS products
- Send up to 25 records per batch
- Payload must not exceed 1MB

**Handle Deduplication**
- AWS deduplicates per product/customer/hour/dimension
- Can retry requests safely
- Original quantity is billed if multiple requests sent

**Send Historical Records**
- Can send records up to 6 hours in the past
- Must send within 1 hour after unsubscribe
- Prevents lost revenue from delays

**Report Zero Usage**
- Send records even with zero usage
- Maintains visibility for customers
- Cannot amend records after sending

### Metering Dimensions

Define dimensions that match your pricing:
- **Users:** Number of active users
- **Data:** GB transferred or stored
- **API Calls:** Number of requests
- **Hosts:** Number of scanned hosts
- **Custom:** Any measurable unit

### Vendor-Metered Tagging (Optional)

Split usage across properties for buyer cost analysis:
- Add tags to usage allocations
- Buyers view costs by tag values
- Example: Split by Department, Project, or Environment
- Doesn't change total usage or price

## Entitlements for SaaS Contracts

### Checking Entitlements

**Use GetEntitlements API**
- Call when customer logs in
- Verify customer has active contract
- Check which features are entitled

**Entitlement Dimensions**
- Define what customers can access
- Examples: Users, Features, Data limits
- Set different tiers (Basic, Pro, Enterprise)

**Handle Upgrades**
- Customers can upgrade during contract
- Check entitlements regularly
- Grant access to new features immediately

**Handle Expirations**
- Contracts have end dates
- Support automatic renewals
- Notify customers before expiration

## Amazon EventBridge Integration

### Subscription Events

AWS Marketplace sends events for:
- **subscribe-success:** New subscription created
- **subscribe-fail:** Subscription failed
- **unsubscribe-pending:** Customer initiated unsubscribe (1 hour to send final metering)
- **unsubscribe-success:** Subscription ended

### Contract Events

Events for contract products:
- **entitlement-updated:** Contract entitlements changed
- **contract-created:** New contract created
- **contract-renewed:** Contract renewed

### Event Handling

Configure EventBridge rules to:
- Trigger Lambda functions
- Update customer records
- Send notifications
- Automate workflows

## Amazon SNS Notifications

Alternative to EventBridge for receiving notifications:
- Configure SNS topic
- Receive JSON notifications
- Parse and process events
- Update customer status

## Free Trials

Offer free trials to attract customers:

**Trial Types:**
- Time-based (e.g., 30 days)
- Usage-based (e.g., 100 API calls)
- Feature-limited trials

**Implementation:**
- Configure in Management Portal
- Track trial usage in your application
- Convert to paid after trial ends
- Send metering records during trial

## Private Offers for SaaS

Create custom deals for specific customers:
- Negotiate custom pricing
- Offer custom terms
- Create custom EULAs
- Target specific AWS accounts

## Reporting for SaaS Products

Access reports in Management Portal:
- Customer subscription data
- Usage and metering data
- Revenue and disbursements
- Customer demographics

## API Integration Details

### AWS Marketplace Metering Service
- **BatchMeterUsage:** Send usage records
- Available in multiple AWS Regions
- Default: US East (N. Virginia)
- Contact Seller Operations for additional regions

### AWS Marketplace Entitlement Service
- **GetEntitlements:** Check customer entitlements
- Returns active entitlements
- Includes dimension values and expiration

### AWS Marketplace Catalog API
- **ResolveCustomer:** Verify subscription
- Exchange token for customer ID
- Called during onboarding

## Security Best Practices

- Use IAM roles for API access
- Validate all tokens from AWS Marketplace
- Encrypt customer data
- Implement secure authentication
- Log all API calls with CloudTrail

## Troubleshooting

### Common Issues

**Metering records not received:**
- Check API credentials
- Verify product code
- Confirm customer is subscribed
- Review CloudTrail logs

**Customer can't access product:**
- Verify subscription status
- Check ResolveCustomer response
- Confirm registration URL is correct
- Review EventBridge/SNS notifications

**Integration testing fails:**
- Ensure product is in limited visibility
- Verify all required APIs are integrated
- Check that metering records are sent
- Contact Seller Operations for assistance

## Additional Resources

- **SaaS Product Guidelines:** Best practices for SaaS products
- **Code Examples:** Sample integration code
- **API Reference:** Detailed API documentation
- **Seller Operations:** Contact for assistance
- **AWS PrivateLink:** Deliver products through VPC

## Next Steps

1. Review SaaS product guidelines
2. Plan your pricing model
3. Prepare integration assets
4. Create product in Management Portal
5. Integrate with AWS Marketplace APIs
6. Test thoroughly
7. Submit for public launch
