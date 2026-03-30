// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const country = body.country || 'US';

    // Return static registration requirements
    const requirements = {
      general: {
        title: "AWS Marketplace Seller Registration Requirements",
        steps: [
          "Create an AWS account if you don't have one",
          "Complete the seller registration form",
          "Provide business information and tax details",
          "Set up payment information",
          "Accept the AWS Marketplace Terms and Conditions"
        ],
        documentation_url: "https://docs.aws.amazon.com/marketplace/latest/userguide/seller-registration-process.html"
      },
      business_info: {
        required_fields: [
          "Legal business name",
          "Business address",
          "Tax identification number (EIN/VAT)",
          "Contact information"
        ]
      },
      payment_info: {
        required_fields: [
          "Bank account details",
          "Routing number",
          "Account number"
        ]
      }
    };

    // Add India-specific requirements if applicable
    if (country === 'IN' || country === 'India') {
      (requirements as any).india_specific = {
        required_fields: [
          "GST Number",
          "PAN Number",
          "Indian bank account details"
        ],
        notes: [
          "GST registration is mandatory for Indian sellers",
          "PAN verification is required for tax compliance"
        ]
      };
    }

    return NextResponse.json({
      success: true,
      requirements,
      country
    });
  } catch (error: unknown) {
    console.error('Get registration requirements error:', error);
    const errorMessage = error instanceof Error ? error.message : 'Internal server error';
    return NextResponse.json(
      { success: false, error: errorMessage },
      { status: 500 }
    );
  }
}
