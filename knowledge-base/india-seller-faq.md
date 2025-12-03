# AWS Marketplace India - Seller FAQ

## Account Setup

### Q: Do I need a separate AWS account to sell in India?
**A: Yes.** You MUST create a standalone AWS account that is:
- NOT part of AWS Organizations
- Specifically configured for selling in India
- Cannot be used to sell to buyers outside India
- Cannot use an existing buyer account for seller registration

### Q: If I'm already registered as a buyer with AWS India, do I still need a separate account for selling?
**A: Yes.** You must create a new standalone AWS Marketplace account for seller registration to:
- Prevent incorrect tax and invoicing treatment
- Avoid complications with AWS Organizations structure changes

## Registration Requirements

### Q: What information do I need to provide for seller registration?
**A: Required Information:**
1. **GSTIN** (GST Identification Number)
2. **PAN** (Permanent Account Number) - auto-populates from GSTIN
3. **Seller Signature** - for tax invoices
4. **Legal Business Name and Address** - corresponding to GSTIN
5. **Acknowledgements**:
   - Withholding tax non-applicability
   - E-invoicing enablement
   - Authorization for AWS India to raise invoices
6. **Bank Account Details** - Valid India domiciled bank account

## Support

### Q: How do I get support and assistance as a seller in India?
**A: Use Contact Us form in AWS Marketplace Management Portal:**

**For Banking/Disbursement:**
- Select: Commercial Marketplace → Seller Account → Banking

**For Private Offer Help:**
- Select: Commercial Marketplace → Private Offer → Offer Creation

**For India-Specific Questions:**
- Tax obligations, banking, regulatory requirements
- Consult with local advisors familiar with India regulations
- Provide detailed information for faster resolution

## Geographic Restrictions

### Q: Can I sell to buyers outside of India as a seller in India?
**A: No.** 
- Sellers in India can ONLY sell to buyers in India
- Buyers outside India can view listings but cannot purchase
- Geographic restrictions enforced at platform level

### Q: How do I indicate that my product is available only in India?
**A:**
- Products from India sellers automatically restricted to India buyers
- Include `[IN]` in product title for clarity
- Geographic restriction enforced at platform level

## Pricing and Currency

### Q: What currencies can I use for pricing my products?
**A:**
- **Public Offers**: Must be priced in USD only
- **Private Offers**: Can be priced in INR or USD
- **Listing Fees**: Always deducted in INR
- **Disbursements**: Always in INR (regardless of pricing currency)
- **INR Private Offers**: No currency conversion or exchange rate variability

### Q: How do product pricing currency and seller disbursements work in detail?

**For USD Offers:**
- Buyers receive invoices with:
  - USD pricing
  - Applicable GST
  - Foreign exchange conversion rate to INR
- Tax invoice uses same rate as commercial invoice
- Your disbursement in INR = Converted amount minus:
  - Withholding tax (0.1%)
  - TCS (0.5%)
  - Listing fees
  - Tax on listing fees

**For INR Private Offers:**
- Buyers receive invoices with agreed INR amount
- No foreign exchange variability
- Invoices show both INR and USD amounts
- Fixed FX rate applied at offer acceptance
- Minor rounding differences may occur (max ±0.005 USD per line item)
- Due to backend USD processing

## Product Types

### Q: What product types can I create offers for?
**A: Supported Product Types:**
- SaaS
- AMI (Amazon Machine Images)
- Containers
- Professional Services
- ML (Machine Learning)
- AWS Data Exchange

## Taxation

### Q: What are my GST tax obligations and liability as a seller in India?
**A: Your Responsibilities:**
- Buyers charged 18% GST
- GST paid to you as part of disbursement
- **You are responsible** for remitting GST to tax authorities
- Must comply with all applicable tax laws in India
- Must ensure GSTIN is enabled for e-invoicing
- Must comply with GST registration and filing requirements

**AWS India's Role:**
- Facilitates issuing GST tax invoices to buyers
- You are listed as Seller on Record (SoR)
- Shares tax invoice with you via email
- For your records and compliance purposes

### Q: Do I need to withhold tax on listing fees?
**A: No.**
- Per Section 194-O subsection 4 of Income Tax Act, 1960
- Once withholding tax processed at any point in payment flow
- Sellers exempt from TDS (Tax Deducted at Source) on listing fees
- AWS deducts TDS from buyer payments
- AWS remits TDS to tax authorities
- TDS certificates shared with you for tax claiming purposes

## Banking and Disbursements

### Q: What banking information do I need to provide?
**A: Required Bank Details:**
- Account number
- Indian Financial System Code (IFSC)
- Name and address of account holder

**Important:**
- Only bank accounts domiciled in India accepted
- International bank accounts NOT accepted
- All disbursements processed in INR only
- To your India bank account only

### Q: When will I receive disbursements?
**A:**
- Follow standard AWS Marketplace schedule
- Processed in INR to your India bank account
- Timing and frequency align with standard AWS Marketplace practices
- Can ONLY receive disbursements in INR
- To bank account domiciled in India

### Q: How are AWS Marketplace listing fees handled for sellers in India?
**A:**
- Fee structure follows standard AWS Marketplace rates
- All fees calculated and charged in INR
- 18% GST applicable on listing fees
- AWS Marketplace provides GST tax invoice for listing fees
- Both listing fees and GST deducted from seller disbursement
- No TDS withholding required (Section 194-O exemption)
- Refer to AWS Marketplace Seller Terms for current fee information

## Account Migration

### Q: How do I migrate from selling outside India to selling in India?

**Option 1: Create New Standalone Account (Recommended)**
1. Create new standalone account for India-based entity
2. Re-list your offers
3. Use `[IN]` in listing names to differentiate
4. Buyers must cancel existing agreements
5. Re-negotiate from your India-based entity

**Option 2: Change Existing Account Location to India**
1. Update tax location in AWS Billing Console to India
2. Ensure no linked accounts or turn off tax inheritance
3. Submit GSTIN, PAN, seller signature, and India bank account
4. Upon validation, can start listing on AWS India

**Consequences of Option 2:**
- ❌ Lose ability to sell to non-India buyers
- ❌ Existing non-India disbursements blocked
- ❌ Must cancel all agreements with non-India buyers
- ✅ Existing contracts with India buyers invoiced in INR from AWS India

## Channel Partners

### Q: What are the restrictions for working with channel partners in India?
**A: Geographic Restrictions:**
- Can only work with channel partners located in India
- India-based channel partners can extend CPPO to India buyers only
- Cannot extend CPPOs to non-India buyers (regardless of ISV location)
- Cannot extend CPPOs from non-India ISVs to India buyers

**As India-Based Channel Partner:**
- Can extend CPPOs authorized by India-registered ISVs
- To India-based buyers only

### Q: Can non-India sellers use channel partners in India to sell to buyers in India?
**A: Yes, through DSOR (Designated Seller on Record) program:**
- India-based channel partner lists offerings on behalf of non-India seller
- AWS Marketplace settles with the channel partner
- Non-India seller receives payment directly from channel partner
- Payment occurs outside AWS Marketplace
- Contact AWS account representative or AWS Marketplace Seller Operations for details

## Private Offers

### Q: Can I create private offers for buyers in India?
**A: Yes.**
- Use standard private offer process
- All private offers only available to buyers in India
- Can be priced in either USD or INR
- Geographic restrictions automatically enforced

## Compliance

### Q: What compliance requirements apply to sellers in India?
**A: Your Responsibilities:**
- Comply with all applicable laws and regulations in India
- Including but not limited to:
  - Tax laws
  - Data protection requirements
  - Software licensing regulations
- AWS provides the platform
- **Compliance with local laws is YOUR responsibility**

## Quick Reference

### Key Points for India Sellers

**Account Setup:**
- ✅ Must be standalone account (not in Organizations)
- ✅ Cannot use buyer account
- ✅ Separate from non-India selling

**Pricing:**
- ✅ Public offers: USD only
- ✅ Private offers: USD or INR
- ✅ Disbursements: INR only

**Geographic:**
- ✅ Can sell to India buyers only
- ❌ Cannot sell to non-India buyers
- ✅ Use `[IN]` in product title

**Tax:**
- ✅ 18% GST collected
- ✅ You remit GST to authorities
- ✅ No TDS withholding on listing fees
- ✅ GSTIN must be e-invoicing enabled

**Banking:**
- ✅ India bank account only
- ✅ INR disbursements only
- ❌ No international bank accounts

**Fees:**
- ✅ Listing fees in INR
- ✅ 18% GST on listing fees
- ✅ Deducted from disbursement
- ✅ TDS exempt (Section 194-O)

---

**Document Version**: 1.0
**Last Updated**: December 2024
**Source**: AWS Marketplace User Guide - India Seller FAQ
