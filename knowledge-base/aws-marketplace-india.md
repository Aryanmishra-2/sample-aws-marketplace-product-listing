# AWS Marketplace India - Knowledge Base

## Overview

AWS Marketplace customers based in India can now buy offerings from India-based AWS Marketplace Sellers, with transactions being facilitated by Amazon Web Services India Private Limited ("AWS India"). This allows customers to benefit from local invoicing and local payment options for their AWS Marketplace purchases.

## Key Changes

### What is Changing?
- India-based third-party sellers are now on-boarded onto AWS Marketplace
- If AWS has identified your account location to be in India, you can purchase from India-based sellers
- Transactions with India-based sellers are facilitated by AWS India
- Sales by non-India based sellers and Amazon-affiliated entities continue to be facilitated by AWS, Inc.

### Benefits
- Local invoicing in Indian Rupees (INR)
- Local payment options
- Access to India-based sellers and their offerings
- **Note**: UPI and Netbanking are NOT available as payment methods at launch

## Identifying India-Based Sellers

### How to Identify
1. Check the [Marketing page](https://aws.amazon.com/marketplace/solutions/india) for public listings from India-based sellers
2. In the marketplace catalog, sellers should explicitly state in the product description that the offer is issued by their Indian entity
3. Contact the seller directly to confirm local availability

## Invoicing

### For India-Based Seller Purchases (AWS India)
You will receive:
1. **Commercial Invoice/Statement**: Lists all purchases from India-based sellers
2. **Separate Tax Invoices**: One from each seller
   - If you provided verified tax information, invoices will contain QR code and IRN number
   - Can be used to claim input tax credit (ITC)

### For Non-India Based Seller Purchases (AWS, Inc.)
You will receive:
- Commercial invoice from AWS, Inc. listing all purchases
- Tax invoice from AWS, Inc. (only if you haven't provided tax information)
- No tax invoice if you have provided tax information (you must deposit tax directly)

### Separate Invoices for Cloud and Marketplace
- If you buy AWS cloud services from AWS India, you will receive separate invoices for:
  - AWS Cloud purchases
  - AWS Marketplace purchases

### Invoice Delivery
- Available on the billing console
- Delivered to root and other email addresses based on configured billing preferences

## Taxation

### GST on India-Based Seller Purchases
- **18% Goods & Services Tax (GST)** charged on purchases
- AWS India facilitates issuance of tax invoices in INR
- Seller is the Seller on Record (SOR)
- GST collected is remitted to the seller, who deposits it to tax authorities

### GST on Non-India Based Seller Purchases (AWS, Inc. as MPO)
- 18% GST collected if you haven't provided tax information
- AWS, Inc. collects and deposits tax directly to authorities
- No GST collected if you have provided tax information (you must deposit directly)

### Tax Type Determination (IGST vs CGST/SGST)
1. **Same State**: If your tax info and seller's tax info are in the same state → CGST and SGST applied
2. **Different States**: If you and seller are in different states → IGST applied
3. **SEZ**: If either party is in a Special Economic Zone → IGST applied (regardless of above rules)

## Tax Information

### Tax Settings
- Tax information from the [Tax Settings page](https://console.aws.amazon.com/billing/home?#/tax) is used
- Same tax information used for AWS India Cloud purchases
- Review and verify all details are accurate
- If part of an Organization, invoices may be consolidated for accounts with same Tax Settings

### Without Tax Information
- You can still make purchases
- However, you cannot claim input tax credit (ITC) on GST charged

### GSTIN Requirement
- Enter GSTIN information on Tax Settings page to receive tax invoices that can be used to claim ITC

## Payment

### Payment Currency and Methods
- **Currency**: Indian Rupee (INR) only for AWS India transactions
- **Credit/Debit Cards**: AMEX, MasterCard, RuPay, or Visa
  - Must be tokenized per Reserve Bank of India (RBI) regulations
  - Same card used for AWS India cloud purchases can be used
  - **Restrictions**: Credit/debit card users face restrictions when purchasing:
    - Contract pricing products
    - Contract with consumption pricing products
  - **No Restrictions**: Can purchase PAYG, free products, free-trial products, and BYOL products
  - **Solution**: Switch to Pay by Invoice (PBI) for contract pricing products

### Payment Methods NOT Available
- NetBanking (not available at launch)
- UPI (not available at launch)

### Pricing and Currency Conversion
- Service pricing published in USD (exclusive of GST)
- Amounts computed in USD and converted to INR for billing
- Private offers can be in USD or INR
- **INR Private Offers**: No FX variability on negotiated price

### Wire Transfer Payments

#### For AWS India Marketplace Purchases
- Updated remittance instructions required
- Separate India-based bank account (different from AWS India cloud services)
- Refer to remittance information in AWS India Marketplace invoices
- Contact AWS Support or account manager for early remittance information

#### For Non-India Based Seller Purchases
- Remit to AWS Inc.'s US-based bank account

#### Important Payment Rules
- **Cannot combine**: AWS cloud and AWS Marketplace payments must go to respective bank accounts
- **Cannot mix**: AWS Inc. and AWS India Marketplace payments must go to respective bank accounts
- Wrong bank account payments will be rejected and cause delays

### Invoice Amount Discrepancies

#### Commercial Invoice vs Tax Invoice
- Amounts generally match
- May differ by a few rupees due to separate processes
- You can pay using either invoice based on your AP reconciliation processes

#### INR Priced Offers
- Small rounding errors may occur between GST invoice summary and detailed usage section
- Due to FX conversion handling between systems
- AWS is working to resolve this issue

#### Private Offer Amount Mismatch
- INR invoices show: INR amount, equivalent USD amount, and fixed FX rate at offer acceptance
- Slight rounding differences may occur due to FX rounding mechanism
- AWS is working to resolve this discrepancy

## Account Changes

### Changing Location from India to Non-India
If you change your account's legal profile from India to non-India (by changing tax/billing address) while having active purchases from India-based sellers:
1. You will be notified to either:
   - Revert billing/tax information back to India to continue with India-based seller, OR
   - Select an alternate non-India based seller's offering (India-based seller offering will be terminated)

## Existing Subscriptions

### Impact on Current Subscriptions
- Existing subscriptions are from non-India based sellers or Amazon-affiliated entities
- These continue to be facilitated and invoiced by AWS, Inc.
- If seller offers same product via Indian entity:
  - You can switch to India-based offer
  - Must cancel current subscription from non-India based seller

## Cost Optimization Tools

### AWS Cost Explorer and CUR
- Use tools the same way as before
- **Billing Entity**: Tagged as 'AWS Marketplace'
- **Legal Entity Field**: Seller's name appears here
- **Invoicing Entity Field**:
  - 'AWS India' for India-based seller purchases
  - 'AWS, Inc.' for non-India based seller purchases

## Multiple AWS Accounts

### Account Management
- Check tax information is up to date for all accounts via Tax Settings page
- Tax invoice issued according to Tax Settings of each AWS account
- Enter GSTIN on Tax Settings page to receive tax invoices for ITC claims

### AWS Organizations
- Invoices consolidated when possible for accounts with same Tax Settings
- If using payer account and linked accounts:
  - Turn on tax inheritance feature to reflect payer account's tax info to linked accounts

## Tax Withholding

### No Withholding Required
- **Do NOT withhold taxes** on payments to AWS India for India-based seller purchases
- Under Section 194-O of Income Tax Act, 1961:
  - AWS India withholds taxes when passing payments to sellers/resellers
  - Customer withholding on same transaction is not required

## Purchase Orders

### Existing Purchase Orders
To use existing POs for AWS Marketplace purchases through AWS India:
1. Ensure PO has "AWS Marketplace" blanket usage selected as line item type
2. Select AWS India in 'Bill From' section (or select 'All')
3. Only Marketplace POs configured for AWS India will be stamped on invoices

### New Purchase Orders
- Feature will be enabled once AWS Marketplace launches in AWS India
- AWS Marketplace Blanket Usage value in Line-Item Type won't be enabled until launch

## Additional Resources

- [Tax FAQs](https://external-mp-channel-partners.s3.us-west-2.amazonaws.com/AWS_Marketplace_India_Tax.pdf)
- [Buyer Tax Help](https://aws.amazon.com/tax-help/india/india-marketplace-buyers/)
- [India FAQs](https://aws.amazon.com/legal/awsin/)
- [Customer Service](https://console.aws.amazon.com/support/home/)
- [Tax Settings](https://console.aws.amazon.com/billing/home?#/tax)

## Quick Reference

### Key Points for India-Based Buyers
✅ Local invoicing in INR
✅ 18% GST on all purchases
✅ Separate invoices for cloud and marketplace
✅ Credit/debit cards accepted (tokenized)
✅ Wire transfer available
✅ Can claim ITC with GSTIN
❌ No UPI at launch
❌ No NetBanking at launch
❌ Cannot withhold taxes
❌ Cannot mix payments between accounts

### Key Points for India-Based Sellers
✅ Can sell to India-based customers
✅ Transactions facilitated by AWS India
✅ Must issue tax invoices with QR code and IRN
✅ Collect 18% GST and remit to authorities
✅ Can offer private offers in INR or USD
✅ Must explicitly state Indian entity in product description

---

**Last Updated**: December 2024
**Source**: AWS Marketplace India Documentation


## Getting Started as a Seller in India

### Key Benefits for Sellers

✅ Sell paid offers on AWS Marketplace to buyers in India
✅ Receive disbursements to Indian bank accounts in INR
✅ Buyers invoiced in INR with GST included
✅ AWS India facilitates tax-compliant invoices with you as Seller of Record (SoR)

### Important Considerations for Sellers

⚠️ **If seller is outside India**: Sales to India buyers remain in USD via AWS Inc.
⚠️ **AWS Organizations**: Must use separate standalone account (not linked account) to avoid taxation errors
⚠️ **Container products**: Private offers with contract/consumption and usage-based pricing remain in USD
⚠️ **Geographic restriction**: Can only sell to buyers in India (even if targeting other countries)

### Registration Process for India-Based Sellers

#### Step 1: Create New Standalone AWS Account
- Create new AWS India account ID
- **Must be standalone account** (not linked in AWS Organizations)
- Using linked account leads to incorrect and non-compliant tax invoices

#### Step 2: Complete Seller Registration
1. Register on AWS Marketplace Management Portal
2. Provide unique legal business name (used on tax invoices)
3. Create public profile
4. Reference: [Create Public Profile Guide](https://docs.aws.amazon.com/marketplace/latest/userguide/create-public-profile.html)

#### Step 3: Provide Tax Information

**Required Information:**
1. **GSTIN** (GST Identification Number)
2. **PAN** (Permanent Account Number) - auto-populated from GSTIN
3. **Seller Signature** - for tax invoices (submit via contact us form)
4. **Legal Business Name and Address** - corresponding to GSTIN
5. **Acknowledgements**:
   - Non-applicability of Withholding Tax (WHT) on listing fees
   - Confirmation that GSTIN is enabled for e-invoicing
   - Authorization to AWS India to raise invoices for your sales
   - Declaration of responsibility to remit GST to Government

**Important Note on Signatures:**
- B2B transactions with e-invoicing: Signature relaxation available
- B2C transactions: Signature required on tax invoice for compliance
- Transaction classification:
  - **B2B**: Customer provided valid GST details
  - **B2C**: Customer hasn't provided GST details
- Specimen signature used solely for generating invoices
- Handled securely per AWS Privacy Notice

#### Step 4: Provide Bank Account Information

**Required Details:**
- Account number
- Indian Financial System Code (IFSC) number
- Full name and address associated with account

#### Step 5: Add Disbursement Method

**Configuration:**
1. Navigate to Payment information → Disbursement methods
2. Choose "Add disbursement method"
3. Select INR from Currency dropdown
4. Select appropriate bank account for INR
5. Choose disbursement frequency: Monthly or Daily
6. Disbursements sent via NEFT/RTGS to designated bank account

**Important Notes:**
- Sellers in India can only receive disbursements in INR
- Can only associate INR currency to one bank account
- Can switch association to different bank account
- Public offers remain in USD
- Do NOT add USD as disbursement method (cannot receive USD disbursements)

#### Step 6: Create Offers

**Geographic Restrictions:**
- Can sell public and private offers to buyers in India ONLY
- Even if targeting other countries, buyers outside India cannot subscribe
- Must complete banking info and disbursement preferences first

**Product Listing Requirements:**
- AWS Marketplace product listings always in USD
- INR option available for private offers
- **Product title must be suffixed with `[IN]`**

### Creating Direct Private Offers

**Steps:**
1. From Offers menu in AWS Marketplace Management Portal
2. Choose "Create private offer"
3. Select: Direct private offer, product type, and your product
4. At step 2 (set offer duration and prices):
   - Select currency from dropdown (USD or INR)
5. Enter all details
6. Review and choose "Create private offer"

### Creating Channel Partner Private Offers (CPPO)

**For ISVs or DSOR Partners:**

**One-Time Setup (Mandatory):**
1. Log into AWS Marketplace Management Portal
2. Navigate to Settings tab
3. Choose "Service linked roles"
4. Choose "Create service-linked role"
5. Required for ISVs, DSORs, and CPs to create/accept selling authorizations

**Creating Resale Authorization:**
1. From Partners menu, choose "Create opportunity"
2. Under Discounts and Products:
   - Select discount type
   - Select your product for resale
3. Select currency from dropdown
4. Enter all details
5. Review and choose "Create opportunity"

**Important CPPO Notes:**
- Sellers in India and DSORs can only send resale authorizations to channel partners in India
- Resale authorization to non-India channel partner will fail
- Channel partner can only create CPPO in same currency
- CPPOs can only be extended to buyers in India

### Seller Quick Checklist

**Before You Start:**
- [ ] Create standalone AWS India account (not in Organizations)
- [ ] Register as seller on AWS Marketplace Management Portal
- [ ] Create public profile with unique legal business name

**Tax Setup:**
- [ ] Provide GSTIN
- [ ] Verify PAN (auto-populated)
- [ ] Submit seller signature via contact form
- [ ] Provide legal business name and address
- [ ] Complete all required acknowledgements

**Banking Setup:**
- [ ] Provide Indian bank account details (Account, IFSC, Name, Address)
- [ ] Add INR disbursement method
- [ ] Select disbursement frequency (Monthly/Daily)

**Product Setup:**
- [ ] Create product listing (in USD)
- [ ] Suffix product title with `[IN]`
- [ ] Create private offers (USD or INR)
- [ ] Target India buyers only

**For Channel Partners:**
- [ ] Create Service-Linked Role (one-time)
- [ ] Create resale authorizations in INR
- [ ] Send to India-based channel partners only

### Common Seller Scenarios

**Scenario 1: Seller in India, Buyer in India**
- Transaction facilitated by AWS India
- Invoice in INR with 18% GST
- Disbursement in INR to Indian bank account
- Tax-compliant invoice with QR code and IRN

**Scenario 2: Seller outside India, Buyer in India**
- Transaction facilitated by AWS Inc.
- Invoice in USD
- Disbursement in USD to non-India bank account
- Standard AWS Inc. invoicing

**Scenario 3: Seller in India, Buyer outside India**
- Buyer cannot subscribe to offer
- Geographic restriction enforced
- Must use non-India entity to sell outside India

### Resources for Sellers

- [AWS Marketplace Management Portal](https://aws.amazon.com/marketplace/management/)
- [Product Preparation Guide](https://docs.aws.amazon.com/marketplace/latest/userguide/product-preparation.html)
- [Create Public Profile](https://docs.aws.amazon.com/marketplace/latest/userguide/create-public-profile.html)
- [AWS Privacy Notice](https://aws.amazon.com/privacy/)
- [Tax FAQs](https://external-mp-channel-partners.s3.us-west-2.amazonaws.com/AWS_Marketplace_India_Tax.pdf)
- [Customer Service](https://console.aws.amazon.com/support/home/)

---

**Document Version**: 2.0
**Last Updated**: December 2024
**Sources**: 
- AWS Marketplace India Documentation
- AWS Legal - AWS India FAQs
- AWS Marketplace User Guide - Getting Started as Seller in India
