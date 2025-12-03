# AWS Marketplace Seller Registration Guide

## Overview

Registering as a seller is the first step to selling your products on AWS Marketplace. This guide covers the complete registration process, requirements, and eligibility criteria.

## Seller Types

AWS Marketplace supports several types of sellers:

### Independent Software Vendors (ISVs)
Software companies that develop, market, and sell software products that run on or integrate with AWS services. ISVs can offer:
- AMI-based products
- Container products
- SaaS products
- Machine learning models

### Channel Partners
Organizations that resell or distribute software products from ISVs. Channel partners can:
- Create private offers for authorized products
- Set their own pricing and terms
- Resell third-party solutions

### Managed Service Providers (MSPs)
Companies that provide managed services for AWS environments, including:
- Monitoring services
- Security services
- Optimization services

### Individual Developers
Individual developers or consultants who have created software products or professional services that work with AWS services.

## General Requirements for All Sellers

All sellers must meet these basic requirements:

- Have an AWS account in good standing
- Meet the requirements in the terms and conditions for AWS Marketplace sellers
- Provide a valid email address accessible by appropriate contacts within your organization
- Use AWS Identity and Access Management (IAM) roles to sign in to the AWS Marketplace Management Portal (strongly recommended over root account credentials)

## Requirements for Free Products

To create and offer free products in AWS Marketplace, you must:

- Sell publicly available, full-feature production-ready software
- Have a defined customer support process and support organization
- Provide a means to keep software regularly updated and free of vulnerabilities
- Follow best practices and guidelines when marketing your product in AWS Marketplace
- Be an AWS customer in good standing

**Note:** If you offer only free products, you don't have to provide banking information to AWS Marketplace.

## Requirements for Paid Products

If you charge for your products or offer Bring Your Own License (BYOL) products, you must also meet these additional requirements:

### Location Requirements
- Be a permanent resident or citizen in an eligible jurisdiction
- OR be a business entity organized or incorporated in an eligible jurisdiction

### Tax Information
- **US-based entities:** Provide W-9 form
- **Non-US sellers:** Provide W-8 form and VAT/GST registration number

### Banking Information
- **US sellers:** Banking account from a US-based bank
- **Non-US sellers:** Bank account with SWIFT code in an eligible jurisdiction
- **India-based sellers:** Special requirements apply (see India-specific documentation)
- Associate bank account with a disbursement preference to create public or private offers

**Note:** Non-US sellers can register for a virtual US bank account from Hyperwallet if needed.

### Know Your Customer (KYC) Process
Complete KYC process if:
- Selling to customers in Europe, the Middle East, and Africa (EMEA) excluding Turkey and South Africa
- Getting paid for Republic of Korea transactions
- Using UK-based bank accounts

### EMEA Considerations
When selling to EMEA customers through Amazon Web Services EMEA SARL:
- You receive up to two disbursements (for transactions through AWS Inc. and Amazon Web Services EMEA SARL)
- You may be taxed on the listing fee for certain transactions
- AWS Marketplace will provide a tax-compliant invoice if VAT is assessed

## Eligible Jurisdictions for Paid Products

To sell paid products on AWS Marketplace, you must be located in one of these jurisdictions:

- Australia¹
- Bahrain¹ ²
- Canada
- Colombia¹ ²
- European Union (EU) member states¹
- Hong Kong SAR
- India³
- Israel¹ ²
- Japan⁴
- New Zealand¹
- Norway¹ ²
- Qatar
- South Korea
- Switzerland¹ ²
- United Arab Emirates (UAE)¹ ²
- United Kingdom (UK)¹
- United States (US)

**Notes:**
1. Sellers in these countries must provide VAT registration information in country of establishment
2. If seller and buyer are in the same country, seller may be responsible for tax invoicing, collections, and remittances
3. India-based sellers can only sell to buyers in India
4. Special procedures apply from April 1, 2025 for Japanese consumption tax

**Important:** If you are moving from one jurisdiction to another, consult with your legal and tax advisor before proceeding, as this might impact all active agreements.

## Special Requirements by Product Type

### Data Product Providers
- Must meet AWS Data Exchange eligibility requirements
- Request onboarding through AWS Support case wizard

### Professional Services Providers
- Must complete the Tax Questionnaire for DAC7

### BYOL Product Providers
- Often require additional seller registration requirements beyond standard paid product requirements

### AWS GovCloud (US) Products
- Must have an AWS GovCloud (US) account
- Must meet ITAR requirements if applicable

## Registration Process Steps

1. **Review Requirements**
   - Determine if you'll offer free or paid products
   - Verify you meet eligibility requirements for your jurisdiction
   - Gather required documentation

2. **Complete Seller Registration**
   - Use existing AWS account or create new account
   - Access AWS Marketplace Management Portal
   - Submit seller registration form

3. **Provide Tax Information**
   - Submit W-9 (US) or W-8 (non-US) form
   - Provide VAT/GST registration if applicable
   - Complete any jurisdiction-specific tax requirements

4. **Provide Banking Information**
   - Add bank account details
   - Verify bank account
   - Associate with disbursement preference

5. **Complete KYC Process (if required)**
   - Submit required documentation
   - Wait for verification approval

6. **Set Up IAM Roles**
   - Create IAM roles for portal access
   - Configure appropriate permissions
   - Avoid using root account credentials

## India-Specific Requirements

Sellers in India have specific registration requirements and processes that differ from other regions:
- Can only sell to buyers in India
- Different banking and tax requirements
- See separate India seller documentation for details

## Next Steps After Registration

Once registered as a seller:
1. Learn about product types and choose what to offer
2. Review pricing models available
3. Prepare your product for submission
4. Access seller tools in the Management Portal
5. Review seller reports and analytics capabilities

## Important Resources

- **AWS Marketplace Management Portal:** Main tool for managing products and seller account
- **Seller Operations Team:** Contact for questions about requirements or registration
- **AWS Marketplace Seller Terms:** Review listing fees and terms (available in Management Portal)
- **AWS Marketplace Sellers FAQ:** Answers to frequently asked questions

## Permissions and Access

For information about the permissions that AWS Marketplace sellers need, see the Policies and Permissions for AWS Marketplace Sellers documentation.

## Listing Fees

Listing fees vary based on:
- Offer type
- Deployment method
- Total contract value
- Buyer jurisdiction

Fees typically range from 1.5% to 20% for standard offers, with additional regional fees for specific jurisdictions. Registered sellers can view detailed fee information in the AWS Marketplace Seller Terms.

## Support and Contact

For questions about AWS Marketplace seller requirements or the registration process:
- Contact AWS Marketplace Seller Operations team
- Submit support case through AWS Support
- Review documentation and FAQs
