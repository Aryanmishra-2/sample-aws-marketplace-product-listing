# End-to-End Test Guide

## Quick Start

```bash
streamlit run streamlit_form_app.py
```

## Complete 8-Stage Workflow

### Stage 1: Product Information ✅

**Fill out:**
- Product Title: `CloudSync Pro`
- Logo S3 URL: `https://your-bucket.s3.amazonaws.com/logo.png`
- Short Description: `Real-time cloud synchronization service for enterprises`
- Long Description: `CloudSync Pro provides enterprise-grade cloud synchronization with real-time updates, advanced security features, and 99.99% uptime SLA. Perfect for businesses that need reliable data synchronization across multiple cloud platforms.`
- Highlights:
  1. `Real-time synchronization across all platforms`
  2. `Enterprise-grade security with encryption`
  3. `99.99% uptime SLA guarantee`
- Support Email: `support@example.com`
- Support Description: `We provide 24/7 support via email and phone. Our dedicated support team is available to help with any issues or questions.`
- Categories: `Data Integration`
- Keywords: `sync, cloud, integration, backup, enterprise`

**Click:** "Create Product"

**Expected Result:**
- ✅ Product created successfully
- 🆔 Product ID displayed
- 🆔 Offer ID displayed
- Automatically advances to Stage 2

---

### Stage 2: Fulfillment Options ✅

**Fill out:**
- Fulfillment URL: `https://app.example.com/signup`
- Quick Launch: `Unchecked` (or check and provide launch URL)

**Click:** "Continue to Stage 3"

**Expected Result:**
- ✅ Delivery options added
- Automatically advances to Stage 3

---

### Stage 3: Pricing Configuration ✅

**Fill out:**
- Pricing Model: `Usage`
- Number of dimensions: `1`
- Dimension 1:
  - API ID: `users`
  - Display Name: `Active Users`
  - Description: `Number of active users per month`
  - Type: `Metered`

**Click:** "Continue to Stage 4"

**Expected Result:**
- ✅ Pricing configuration saved
- Automatically advances to Stage 4

---

### Stage 4: Price Review ✅

**Fill out:**
- Purchasing Option: `Standard Contract`
- Contract Durations: `12 Months` (select one or more)

**Click:** "Continue to Stage 5"

**Expected Result:**
- ✅ Pricing applied to offer
- Automatically advances to Stage 5

---

### Stage 5: Refund Policy ✅

**Fill out:**
- Refund Policy: `We offer a 30-day money-back guarantee. If you're not satisfied with our service, contact support@example.com within 30 days of purchase for a full refund. Refunds are processed within 5-7 business days.`

**Or use a template:**
- Click "30-Day Refund" button for quick template

**Click:** "Continue to Stage 6"

**Expected Result:**
- ✅ Refund policy saved
- Automatically advances to Stage 6

---

### Stage 6: EULA Configuration ✅

**Fill out:**
- EULA Type: `Standard Contract for AWS Marketplace (SCMP)` (recommended)

**Click:** "Continue to Stage 7"

**Expected Result:**
- ✅ EULA configuration saved
- Automatically advances to Stage 7

---

### Stage 7: Offer Availability ✅

**Fill out:**
- Availability Type: `All Countries (Worldwide)` (recommended)

**Click:** "Continue to Stage 8"

**Expected Result:**
- ✅ Availability configuration saved
- Automatically advances to Stage 8

---

### Stage 8: Account Allowlist (Optional) ✅

**Options:**
1. **Skip** - Click "Skip (Public Offer)" for public availability
2. **Add Allowlist** - Enter AWS account IDs and click "Complete Workflow"

**Click:** "Skip (Public Offer)" or "Complete Workflow"

**Expected Result:**
- ✅ Workflow complete!
- Shows completion page with summary

---

## Completion Page

**Shows:**
- 🎉 Success message
- Product ID
- Offer ID
- Progress: 100%
- All collected data (expandable)

**Actions:**
- 🔄 Start New Listing
- 📥 Export Data (download JSON)
- 🌐 View in AWS Console

---

## Quick Test Data

Copy and paste this for quick testing:

### Stage 1
```
Product Title: Test Product
Logo: https://test-bucket.s3.amazonaws.com/logo.png
Short: Test product for AWS Marketplace
Long: This is a test product created for testing the AWS Marketplace listing workflow. It includes all required fields and demonstrates the complete process.
Highlight 1: First feature
Highlight 2: Second feature
Highlight 3: Third feature
Email: test@example.com
Support: 24/7 support available via email
Categories: Developer Tools
Keywords: test, demo, sample
```

### Stage 2
```
Fulfillment URL: https://app.example.com/signup
```

### Stage 3
```
Model: Usage
Dimensions: 1
  - API ID: users
  - Name: Users
  - Description: Number of users
  - Type: Metered
```

### Stage 4
```
Option: Standard Contract
Durations: 12 Months
```

### Stage 5
```
Policy: We offer a 30-day money-back guarantee. Contact support@example.com for refunds.
```

### Stage 6
```
EULA: SCMP
```

### Stage 7
```
Availability: All Countries
```

### Stage 8
```
Skip (Public Offer)
```

---

## Expected Timeline

| Stage | Time | Total |
|-------|------|-------|
| 1. Product Info | 2-3 min | 2-3 min |
| 2. Fulfillment | 30 sec | 3-4 min |
| 3. Pricing Config | 1-2 min | 4-6 min |
| 4. Price Review | 30 sec | 5-7 min |
| 5. Refund Policy | 1 min | 6-8 min |
| 6. EULA Config | 30 sec | 7-9 min |
| 7. Availability | 30 sec | 8-10 min |
| 8. Allowlist | 30 sec | 9-11 min |

**Total Time: 9-11 minutes** (with test data)

---

## Troubleshooting

### Stage 1 Fails
- **Check:** S3 URL format (must match pattern)
- **Check:** All required fields filled
- **Check:** Field lengths meet requirements
- **Check:** AWS credentials configured

### Stage 2 Fails
- **Check:** Fulfillment URL starts with `https://`
- **Check:** Product ID available from Stage 1

### Stage 3 Fails
- **Check:** At least 1 dimension defined
- **Check:** All dimension fields filled

### Stage 4 Fails
- **Check:** At least 1 contract duration selected
- **Check:** Offer ID available

### Stages 5-8 Fail
- **Check:** Required fields filled
- **Check:** Field length requirements met

### General Issues
- **Refresh page** if stuck
- **Check terminal** for error messages
- **Check AWS credentials:** `aws sts get-caller-identity`
- **Check browser console** for JavaScript errors

---

## Success Indicators

### Stage 1
- ✅ "Product created and updated successfully!"
- 🆔 Product ID shown
- 🆔 Offer ID shown

### Stage 2
- ✅ "Stage 2 Complete!"
- Advances to Stage 3

### Stages 3-8
- ✅ "Stage X Complete!"
- Advances to next stage

### Completion
- 🎉 "Workflow Complete!"
- 100% progress
- All data visible

---

## What Gets Created in AWS

After completing all stages, you will have:

1. **Product** (SaaSProduct@1.0)
   - Title, descriptions, highlights
   - Logo, categories, keywords
   - Delivery options (fulfillment URL)
   - Pricing dimensions

2. **Offer** (Offer@1.0)
   - Linked to product
   - Pricing terms
   - Support terms (refund policy)
   - Legal terms (EULA)
   - Availability settings
   - Optional account allowlist

---

## Next Steps After Completion

1. **View in AWS Console**
   - Go to AWS Marketplace Management Portal
   - Find your product by Product ID
   - Review all settings

2. **Test the Listing**
   - Preview how it appears to customers
   - Test the fulfillment URL
   - Verify all information is correct

3. **Submit for Review**
   - AWS will review your listing
   - May take 1-2 weeks
   - You'll receive feedback if changes needed

4. **Publish**
   - Once approved, publish to marketplace
   - Customers can now find and purchase

---

## Ready to Test!

```bash
streamlit run streamlit_form_app.py
```

Follow the stages above and complete the entire workflow end-to-end! 🚀

