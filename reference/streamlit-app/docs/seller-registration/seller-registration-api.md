# AWS Marketplace Seller Registration API Reference

## Overview

This document outlines the AWS APIs and services required for seller registration in AWS Marketplace.

## Primary APIs

### 1. AWS Marketplace Management Portal API
- **Service**: `marketplace-management`
- **Purpose**: Seller account management and registration
- **Region**: `us-east-1` (primary)

### 2. AWS Organizations API
- **Service**: `organizations`
- **Purpose**: Account verification and organization details
- **Region**: Account's home region

### 3. AWS Support API
- **Service**: `support`
- **Purpose**: Support case creation for seller verification
- **Region**: `us-east-1`

### 4. AWS STS API
- **Service**: `sts`
- **Purpose**: Account identity verification
- **Region**: Any

## Key Operations

### Account Verification
```python
# Get caller identity
sts_client.get_caller_identity()

# Get account details
organizations_client.describe_account(AccountId='123456789012')
```

### Seller Registration Status
```python
# Check current seller status
marketplace_client.get_seller_verification_details()

# Submit seller registration
marketplace_client.put_seller_verification_details(
    SellerContactInfo={...},
    BusinessInfo={...},
    TaxInfo={...}
)
```

### Support Case Creation
```python
# Create verification support case
support_client.create_case(
    subject="AWS Marketplace Seller Registration",
    serviceCode="marketplace",
    severityCode="low",
    categoryCode="seller-registration",
    communicationBody="Seller registration request..."
)
```

## Response Formats

### Seller Status Response
```json
{
    "SellerStatus": "PENDING" | "APPROVED" | "REJECTED" | "NOT_REGISTERED",
    "RegistrationDate": "2024-01-15T10:30:00Z",
    "VerificationDetails": {
        "BusinessVerified": true,
        "TaxInfoVerified": false,
        "ContactVerified": true
    },
    "RequiredActions": [
        "SUBMIT_TAX_INFORMATION",
        "VERIFY_BANK_ACCOUNT"
    ]
}
```

## Error Handling

### Common Error Codes
- `AccessDenied`: Insufficient permissions
- `InvalidAccount`: Account not eligible for seller registration
- `RegistrationInProgress`: Registration already in progress
- `ValidationException`: Invalid input parameters

## Required Permissions

### IAM Policy
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "marketplace-management:GetSellerVerificationDetails",
                "marketplace-management:PutSellerVerificationDetails",
                "organizations:DescribeAccount",
                "sts:GetCallerIdentity",
                "support:CreateCase",
                "support:DescribeCases"
            ],
            "Resource": "*"
        }
    ]
}
```

## Rate Limits

- Seller verification API: 10 requests per minute
- Support API: 5 requests per minute
- Organizations API: 20 requests per minute

## Notes

- Seller registration is a one-time process per AWS account
- Verification can take 1-3 business days
- Some regions may have additional requirements
- Business verification may require additional documentation