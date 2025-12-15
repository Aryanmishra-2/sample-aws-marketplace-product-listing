# AWS Marketplace Private Offers and Disbursements Guide

## Table of Contents
1. [Private Offers Overview](#private-offers-overview)
2. [Creating Private Offers](#creating-private-offers)
3. [Installment Plans](#installment-plans)
4. [Disbursement Setup](#disbursement-setup)
5. [Managing Disbursements](#managing-disbursements)
6. [Multi-Currency Support](#multi-currency-support)

---

## Private Offers Overview

### What are Private Offers?

Private offers allow AWS Marketplace sellers to negotiate custom pricing and terms with individual buyers. They provide flexibility beyond standard public listings.

### Key Features

**Custom Pricing**
- Negotiate discounted rates
- Volume-based pricing
- Custom contract values
- Multi-year deals

**Custom Terms**
- Custom End User License Agreements (EULAs)
- Custom payment schedules
- Flexible contract durations
- Custom legal documents

**Targeted Distribution**
- Extend offers to specific AWS accounts
- Up to 24 buyers per offer
- Geo-targeting by country
- Organization-wide sharing

### Benefits for Sellers

- **Close Enterprise Deals:** Negotiate large contracts with custom terms
- **Flexible Pricing:** Offer discounts and custom pricing structures
- **Strategic Partnerships:** Create tailored agreements for key customers
- **Multi-Year Contracts:** Secure long-term revenue commitments
- **Channel Partner Support:** Enable resellers with custom offers

### Benefits for Buyers

- **Negotiated Pricing:** Get better rates than public listings
- **Custom Terms:** Negotiate terms that fit business needs
- **Flexible Payments:** Installment plans for large purchases
- **Organization Sharing:** Share offers across AWS accounts
- **Predictable Costs:** Lock in pricing for contract duration

### Eligibility Requirements

To create private offers, you must:
- Have at least one active public listing
- Complete seller registration
- Provide tax and banking information
- Set up disbursement preferences
- Have appropriate IAM permissions

---

## Creating Private Offers

### Step-by-Step Process

#### Step 1: Start a New Private Offer

1. Sign in to AWS Marketplace Management Portal
2. Navigate to **Offers** → **Private offers**
3. Click **Create private offer**
4. Select:
   - Offer type (Standard or Channel Partner)
   - Product type (AMI, SaaS, Container, etc.)
   - Specific product
5. Click **Continue to offer details**

**Important Notes:**
- Cannot change product type after creation
- Processing takes up to 30 seconds
- Channel partners must select ISV and authorization

#### Step 2: Provide Offer Information

**Required Information:**
- **Offer Name:** Internal reference name
- **Offer Details:** Description and notes
- **Renewal Type:** 
  - New customer
  - Existing customer on AWS Marketplace
  - Existing customer moving to AWS Marketplace
- **Offer Expiration Date:** When offer becomes invalid (23:59:59 UTC)

**Renewal Definition:**
A renewal is any private offer to:
- Customer with existing/prior private offer for the product
- Customer with existing paid subscription (including expansions/upsells)
- Customer migrating from outside AWS Marketplace

#### Step 3: Configure Pricing and Duration

**Pricing Model Options:**
- Contract pricing (upfront)
- Contract with consumption (hybrid)
- Subscription pricing (usage-based)
- Custom pricing dimensions

**Contract Duration:**
- 1 month to 3 years
- Custom durations available
- Multi-year contracts supported

**Currency Selection:**
- USD (default for public offers)
- EUR, GBP, AUD, JPY (for private offers)
- INR (India sellers only)
- Must configure disbursement preferences first

**Payment Schedule:**
- Upfront payment
- Installment plans (see Installment Plans section)
- Custom payment schedules

#### Step 4: Add Buyers

**Buyer Requirements:**
- Provide AWS account ID for each buyer
- Up to 24 buyers per offer
- Each buyer must be in supported region for selected currency
- Linked accounts follow payer account rules

**Geo-Targeting:**
- Select countries where buyers can view/accept offer
- Option to select "All Countries" for global availability
- India sellers limited to India buyers only
- Based on buyer location, not payer account location

#### Step 5: Configure Legal Terms

**Three Options:**

1. **Public Offer EULA**
   - Use EULA from your public listing
   - Simplest option
   - No additional documents needed

2. **Standard Contract for AWS Marketplace (SCMP)**
   - AWS-provided standard contract
   - Pre-approved terms
   - Faster processing

3. **Custom Legal Terms**
   - Upload up to 5 files
   - Supported documents:
     - Custom EULA
     - Statement of Work (SOW)
     - Bill of Materials
     - Pricing sheet
     - Other addendums
   - Files merged into single document

#### Step 6: Review and Create

1. Review all offer details carefully
2. Verify pricing, duration, and terms
3. Confirm buyer AWS account IDs
4. Click **Create offer** to publish

**Processing:**
- Takes up to 1 hour to validate and process
- Request visible on **Requests** page
- Offer extended only if request succeeds
- System errors or validation errors must be corrected

### Offer Statuses

**Draft**
- Incomplete offer being prepared
- Not subject to retention schedule
- Can be edited freely
- Must complete all required fields to publish

**Active**
- Published and extended to buyer
- Not yet expired
- Buyers can subscribe
- Cannot be modified (must create new offer)

**Expired**
- Published but past expiration date
- Buyers cannot subscribe
- Can update expiration date to extend
- Becomes agreement once accepted

**Accepted**
- Buyer has accepted the offer
- Shows as agreement in Agreements tab
- Offer status doesn't change
- Contract is now active

### Managing Private Offers

**Cloning Offers**
- Duplicate existing offer
- Modify for new buyer
- Saves time on similar deals
- Maintains original offer settings

**Downloading Offer Details**
- Export offer information
- Share with internal teams
- Record keeping
- Audit purposes

**Saving Progress**
- Draft offers saved automatically
- Return to complete later
- No time limit on drafts
- Can delete unwanted drafts

**Updating Expiration**
- Extend expiration date for active offers
- Give buyers more time to accept
- Cannot shorten expiration
- Useful for delayed procurement

**Cancelling Offers**
- Cancel active offers before acceptance
- Cannot cancel after buyer accepts
- Buyer notified of cancellation
- Must create new offer if needed

### Call-to-Action Buttons

**Private Offer Request Button**
- Add to product detail page
- Buyers can request custom offers
- Captures buyer contact information
- Requires APN Customer Engagements Program (ACE) membership

**Demo Request Button**
- Enable guided product demos
- Captures buyer interest
- AWS Demand Generation team qualifies leads
- Transfers qualified requests to seller

**Supported Product Types:**
- Amazon Machine Image (AMI)
- Software as a Service (SaaS)
- Container
- CloudFormation templates

---

## Installment Plans

### Overview

Installment plans (flexible payment schedules) allow buyers to pay for private offers in multiple payments over the contract duration instead of one upfront payment.

### Benefits

**For Sellers:**
- Close larger deals
- Reduce buyer payment friction
- Competitive advantage
- Predictable revenue stream

**For Buyers:**
- Manage cash flow better
- Spread costs over time
- Easier budget approval
- Reduced upfront investment

### Eligibility

**Available for:**
- AMI products with contract pricing
- SaaS products with contract pricing
- Container products with contract pricing
- Multi-year contracts
- Custom duration contracts

**Not available for:**
- Subscription (usage-based) pricing
- Public offers (private offers only)
- Free products

### Creating Installment Plans

#### Configuration Parameters

**Contract Total**
- Total amount buyer will pay
- Divided across installments
- Includes all fees and charges

**Initial Payment (Optional)**
- First payment can differ from others
- Useful for larger down payment
- Remaining balance divided equally
- Can be zero for equal payments

**Frequency Options:**
- **Monthly:** Payment every month
- **Quarterly:** Payment every 3 months
- **Annually:** Payment every year
- **Custom:** Define specific number of installments

**Number of Installments**
- Up to 60 payments supported
- Must fit within contract duration
- Can adjust individual payment amounts
- Total must equal contract total

**First Invoice Date**
- When first payment is due
- Can be before offer acceptance
- Subsequent dates calculated automatically
- Must fall within contract duration

#### Step-by-Step Creation

1. On **Configure offer pricing and duration** page:
   - Select **Contract pricing with installment plan**
   - Choose contract duration

2. Under **Buyer installment plan**, enter:
   - Contract total amount
   - Initial payment (if different)
   - Payment frequency
   - First invoice date

3. Click **Generate installment plan**
   - System validates dates
   - Calculates payment amounts
   - Shows payment schedule

4. Review payment schedule:
   - Verify all invoice amounts
   - Check invoice dates
   - Confirm total matches contract value
   - Adjust individual payments if needed

5. Complete remaining offer creation steps

### Payment Processing

**Invoice Generation:**
- Invoices generated at 00:00 UTC on scheduled dates
- First invoice can occur before acceptance
- If accepted after first date, invoice generated immediately
- Buyers see schedule on AWS invoice

**Payment Collection:**
- AWS Marketplace collects from buyer
- Seller receives payment after collection
- Standard disbursement schedule applies
- Listing fees deducted per payment

**Buyer Visibility:**
- All scheduled payments visible
- Shown on AWS Billing Console
- Helps track spending
- Predictable cost management

### Installment Plan Reporting

**Monthly Billed Revenue Report:**
- Section 4 covers installment plans
- Shows payment schedule
- Tracks collected payments
- Revenue recognition details

**Best Practices:**
- Align payments with buyer budget cycles
- Consider quarterly for enterprise customers
- Use initial payment for implementation costs
- Set realistic first invoice dates
- Verify total matches negotiated amount

### Limitations and Considerations

**Cannot Modify After Acceptance:**
- Payment schedule is fixed once buyer accepts
- Must create new offer for changes
- Plan carefully before publishing

**Invoice Date Restrictions:**
- Must fall within contract duration
- System validates dates
- Error if dates outside contract period

**Multi-Year Contracts:**
- For AMI products, specify instance counts
- Set hourly pricing for additional instances
- Charges apply after specified instances launched

---

## Disbursement Setup

### Overview

Disbursement preferences determine how you receive payments from AWS Marketplace sales. Proper setup is required before creating paid offers.

### Requirements

**All Sellers:**
- Must associate USD as disbursement preference
- Required for public offers (USD only)
- Mandatory for product listing and offer creation

**India Sellers:**
- Must associate INR to bank account
- Can create public offers in USD
- Can create private offers in USD
- Receive disbursements in INR only

**Wait Period:**
- May need to wait 2 business days after registration
- Between creating public profile and adding disbursement method

### Bank Account Requirements

#### US-Based Sellers

**Requirements:**
- US-based bank account
- Can accept ACH transfers
- Must receive payments in USD
- Account holder name matches legal entity

**Account Types:**
- ACH accounts (USD only)
- Hyperwallet accounts (USD only)

#### Non-US Sellers (Excluding India)

**Requirements:**
- Bank account in eligible jurisdiction
- Can accept wire transfers
- Must have valid SWIFT code
- Can receive USD payments

**Options:**
- SWIFT bank account (required for non-USD)
- Hyperwallet for US account access
- Multiple currencies to single account (where supported)

#### India-Based Sellers

**Requirements:**
- India-domiciled bank account
- Must have IFSC code
- Can receive INR only
- Specific deduction requirements apply

### Setting Up Disbursement Preferences

#### Step-by-Step Process

1. **Access Payment Settings**
   - Sign in to AWS Marketplace Management Portal
   - Navigate to **Settings**
   - Select **Payment information** tab

2. **Add Disbursement Method**
   - Click **Add disbursement method**
   - Select currency preference
   - Choose associated bank account

3. **Configure Disbursement Frequency**
   
   **Daily Disbursements:**
   - Payments when funds available
   - Must have positive balance
   - Faster access to funds
   - Good for high-volume sellers

   **Monthly Disbursements:**
   - Choose day of month (1-28)
   - Predictable payment schedule
   - Better for budgeting
   - Can reduce transaction fees

4. **Save Configuration**
   - Click **Add disbursement method**
   - Verify settings
   - Can add multiple methods for different currencies

### Hyperwallet Option

#### What is Hyperwallet?

Hyperwallet is an independent service provider that provides US bank accounts for non-US sellers to receive USD disbursements.

#### Benefits

- Receive USD in US account
- Transfer to local bank in local currency
- Simplified international payments
- Service fee waived for AWS Marketplace (limited time)

#### Fees and Considerations

**Potential Fees:**
- Transfer fees (to local bank)
- Foreign exchange fees
- Currency conversion rates
- Check Hyperwallet support site for current fees

**Service Fee Waiver:**
- Hyperwallet service fee waived for AWS Marketplace
- Limited time offer
- Other fees may still apply

#### Registration Process

1. **Initiate from AWS Marketplace Portal**
   - Go to Settings → Payment information
   - Select **Complete banking information**
   - Choose "No" for US bank account
   - Choose "No" for Hyperwallet registration

2. **Receive PIN and Link**
   - AWS provides personal identification number (PIN)
   - Link to Hyperwallet registration portal
   - Follow Hyperwallet registration steps

3. **Complete Hyperwallet Registration**
   - Activate Hyperwallet account
   - Complete registration process
   - Receive deposit account information

4. **Add to AWS Marketplace**
   - Return to AWS Marketplace Settings
   - Add Hyperwallet account information
   - Associate with disbursement preferences

5. **Updates and Support**
   - Contact Hyperwallet support for account changes
   - Access through Hyperwallet Portal
   - Check Support tab for hours and contact info

### Best Practices

**Account Information:**
- Double-check all account numbers
- Verify routing numbers and SWIFT codes
- Ensure accuracy before submitting
- Contact bank if unsure about details

**Account Status:**
- Ensure account in good standing
- Verify can receive international transfers
- Confirm USD payment capability
- Test with small transfer if possible

**Entity Matching:**
- Bank account holder name must match legal entity
- Mismatches cause payment delays or rejections
- Verify during tax information step
- Update if entity changes

**Keep Updated:**
- Update promptly if changing banks
- Maintain current account information
- Avoid payment delays
- Cannot delete accounts after adding

---

## Managing Disbursements

### Modifying Disbursement Methods

#### Updating Existing Methods

1. Sign in to AWS Marketplace Management Portal
2. Navigate to **Settings** → **Payment information**
3. In **Disbursement methods** section:
   - **Add new:** Click **Add disbursement method**
   - **Edit existing:** Select method and click **Edit**
4. Update currency, bank account, or schedule
5. Click **Save** or **Add disbursement method**

#### What Can Be Modified

- Currency preferences
- Bank account associations
- Disbursement frequency (daily/monthly)
- Monthly disbursement day
- Disbursement thresholds

### Currency Support and Restrictions

#### Available Currencies

- **USD** - United States Dollar (required for all non-India sellers)
- **EUR** - Euro
- **GBP** - Great Britain Pound
- **AUD** - Australian Dollar
- **JPY** - Japanese Yen
- **INR** - Indian Rupee (India sellers only)

#### Currency Restrictions by Account Type

**US ACH Accounts:**
- USD only
- Cannot receive other currencies
- Most common for US sellers

**Hyperwallet Accounts:**
- USD only
- Transfer to local currency available
- Additional fees may apply

**SWIFT Bank Accounts:**
- Required for non-USD disbursements
- Optional for USD
- Multiple currencies supported
- Must support international transfers

**IFSC Bank Accounts (India):**
- INR only
- Required for India sellers
- India-domiciled accounts only

#### Multiple Currency Management

- Assign multiple currencies to single bank account (where supported)
- Different currencies can use different accounts
- Configure preferences per currency
- Receive disbursements in offer currency

### Disbursement Timing and Processing

#### Payment Schedule

**Daily Disbursements:**
- Occur when funds become available
- Require positive balance
- Faster access to revenue
- More frequent transactions

**Monthly Disbursements:**
- Occur on specified day (1-28)
- Predictable schedule
- Fewer transactions
- Better for budgeting

#### Processing Timeline

**Payment Collection:**
- Funds disbursed after collected from customer
- Not immediate upon sale
- Depends on customer payment

**Bank Transfer Time:**
- 1-2 business days after disbursement date
- ACH transfers (US)
- SWIFT transfers (international)
- Varies by bank and location

**Dashboard Updates:**
- Updated 3-5 days after disbursement
- Shows disbursement history
- Tracks payment status
- Available in Management Portal

### Disbursement Thresholds

#### Purpose

- Set minimum amount before disbursement
- Reduce transaction fees
- Optimize payment processing
- Particularly useful for international transfers

#### Best Practices

**High Volume Sellers:**
- Lower thresholds
- More frequent payments
- Better cash flow
- Daily disbursements recommended

**Low Volume Sellers:**
- Higher thresholds
- Less frequent payments
- Reduce wire transfer fees
- Monthly disbursements may be better

**International Sellers:**
- Consider wire transfer fees
- Set higher thresholds to offset fees
- Balance cash flow needs with costs
- Review regularly and adjust

### Multi-Currency Disbursements

#### Private Offer Currency Matching

**How It Works:**
- Receive disbursements in same currency as private offer
- Listing fees deducted in offer currency
- Must configure disbursement preferences for each currency
- Cannot create offers in currencies without setup

#### Setup Requirements

**Before Creating Non-USD Offers:**
1. Set up bank account for target currency
2. Ensure bank supports SWIFT (for non-USD)
3. Configure disbursement preferences for currency
4. Verify currency appears in offer creation

**Channel Partner Offers:**
- Both ISV and channel partner receive in offer currency
- Both must have currency configured
- Disbursement timing may vary
- Separate disbursements for each party

#### Currency Selection Availability

- Only configured currencies appear in offer creation
- Must set up before creating offers
- Cannot change currency after offer created
- Plan currency needs in advance

### Best Practices for Managing Disbursements

#### Cash Flow Optimization

**Choose Right Schedule:**
- Align with business cash flow needs
- Consider payment processing costs
- Balance frequency with fees
- Review and adjust as business grows

**Set Appropriate Thresholds:**
- Minimize transaction fees
- Especially important for international transfers
- Higher thresholds for wire transfers
- Lower for ACH transfers

**Monitor Regularly:**
- Review disbursement history
- Ensure payments processing correctly
- Identify any issues early
- Track against sales reports

#### Account Maintenance

**Keep Information Current:**
- Update bank details promptly
- Avoid payment delays
- Verify account status regularly
- Test with small transactions

**Multiple Currencies:**
- Configure all needed currencies upfront
- Understand bank's currency support
- Plan for international expansion
- Review exchange rates and fees

**Documentation:**
- Keep records of all disbursements
- Match against sales reports
- Track listing fees
- Maintain for tax purposes

### Troubleshooting Disbursements

**Payment Delays:**
- Verify bank account information correct
- Check account can receive transfers
- Confirm positive balance
- Review disbursement schedule

**Missing Payments:**
- Check disbursement dashboard
- Verify funds collected from customer
- Review threshold settings
- Contact AWS Marketplace support

**Currency Issues:**
- Ensure currency configured
- Verify bank supports currency
- Check SWIFT code for international
- Confirm disbursement preferences set

**Account Mismatches:**
- Verify legal entity name matches
- Update tax information if needed
- Contact support for assistance
- May require re-verification

---

## Multi-Currency Support

### Overview

AWS Marketplace supports multiple currencies for private offers, allowing sellers to negotiate deals in buyers' preferred currencies.

### Supported Currencies

**For Private Offers:**
- USD - United States Dollar
- EUR - Euro
- GBP - Great Britain Pound
- AUD - Australian Dollar
- JPY - Japanese Yen
- INR - Indian Rupee (India only)

**For Public Offers:**
- USD only
- All public offers must be in USD
- Private offers can use other currencies

### Currency Configuration

#### Prerequisites

1. **Bank Account Setup**
   - Must have bank account for each currency
   - SWIFT required for non-USD
   - ACH for USD (US sellers)
   - IFSC for INR (India sellers)

2. **Disbursement Preferences**
   - Configure for each currency
   - Associate with appropriate bank account
   - Set disbursement schedule
   - Verify before creating offers

3. **Regional Considerations**
   - Buyer must be in region supporting currency
   - Geo-targeting applies
   - Linked accounts follow payer rules

#### Setting Up Multiple Currencies

1. Add bank account for each currency
2. Configure disbursement method per currency
3. Set schedules and thresholds
4. Verify currency appears in offer creation
5. Test with small transaction if possible

### Creating Multi-Currency Offers

#### Currency Selection

**During Offer Creation:**
- Select currency on pricing page
- Only configured currencies available
- Cannot change after offer created
- Must match buyer's supported region

**Pricing Considerations:**
- Set prices in offer currency
- Consider exchange rate fluctuations
- Account for currency conversion costs
- Price competitively for region

#### Buyer Requirements

**Account Location:**
- Buyer AWS account must be in region supporting currency
- Geo-targeting rules apply
- Verify buyer eligibility before creating offer

**Organization Accounts:**
- Linked accounts follow payer account location
- Geo-targeting based on buyer location
- Not payer account location

### Disbursement for Multi-Currency Offers

#### Payment Processing

**Currency Matching:**
- Receive payment in same currency as offer
- No automatic currency conversion
- Direct deposit to configured account
- Listing fees in offer currency

**Fee Calculation:**
- Listing fees deducted in offer currency
- Percentage-based fees apply
- Regional fees may apply
- Net amount disbursed

**Timing:**
- Standard disbursement schedule applies
- May vary by currency and region
- 1-2 business days to bank
- Dashboard updated 3-5 days later

#### Channel Partner Considerations

**For ISV and Channel Partner:**
- Both receive in offer currency
- Both must have currency configured
- Separate disbursements
- Individual disbursement schedules

**Revenue Split:**
- Calculated in offer currency
- Fees deducted before split
- Each party receives net amount
- Reported separately

### Best Practices

#### Currency Strategy

**Plan Ahead:**
- Identify target markets
- Set up currencies before needed
- Consider buyer preferences
- Research regional pricing

**Pricing Strategy:**
- Research local market rates
- Consider currency volatility
- Account for exchange costs
- Price competitively

**Risk Management:**
- Monitor exchange rates
- Consider hedging strategies
- Review pricing regularly
- Adjust for major fluctuations

#### Operational Excellence

**Documentation:**
- Track offers by currency
- Maintain exchange rate records
- Document pricing decisions
- Keep for tax purposes

**Reporting:**
- Review disbursements by currency
- Track revenue by region
- Monitor currency performance
- Analyze profitability

**Customer Communication:**
- Clearly state currency in offers
- Explain payment terms
- Provide currency-specific support
- Address exchange rate questions

### India-Specific Considerations

**For India Sellers:**
- Can only sell to India buyers
- Must receive disbursements in INR
- Can create offers in USD
- Special deduction requirements

**For India Buyers:**
- Receive invoices in INR
- Private offers can be in INR
- Specific payment methods
- Regional pricing applies

### Troubleshooting Multi-Currency Issues

**Currency Not Available:**
- Verify disbursement preferences configured
- Check bank account supports currency
- Ensure SWIFT code provided (non-USD)
- Wait for configuration to propagate

**Payment Issues:**
- Verify buyer in supported region
- Check currency configuration
- Confirm bank can receive currency
- Review disbursement settings

**Exchange Rate Concerns:**
- AWS doesn't perform conversion
- Receive in offer currency
- Bank may charge conversion fees
- Consider local bank accounts

---

## Additional Resources

### AWS Marketplace Management Portal
- Create and manage private offers
- Configure disbursement preferences
- Monitor payment history
- Access reports and analytics

### Support and Contact
- **AWS Marketplace Seller Operations:** For questions about offers and disbursements
- **Hyperwallet Support:** For Hyperwallet account issues
- **AWS Support:** For technical issues and account problems

### Documentation
- Private Offer FAQ
- Seller Reports Guide
- IAM Permissions for Sellers
- Product-Specific Guides

### Best Practices
- Review offers before publishing
- Test with small transactions
- Monitor disbursements regularly
- Keep documentation current
- Stay informed of policy updates
