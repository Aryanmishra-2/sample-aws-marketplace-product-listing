import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const businessInfo = body.business_info || {};

    // Basic validation
    const errors: string[] = [];
    const warnings: string[] = [];

    if (!businessInfo.business_name) {
      errors.push("Business name is required");
    }

    if (!businessInfo.business_address) {
      errors.push("Business address is required");
    }

    if (!businessInfo.tax_id) {
      warnings.push("Tax ID is recommended for faster verification");
    }

    if (!businessInfo.contact_email) {
      errors.push("Contact email is required");
    }

    const isValid = errors.length === 0;

    return NextResponse.json({
      success: true,
      validation: {
        is_valid: isValid,
        errors,
        warnings,
        message: isValid 
          ? "Business information is valid" 
          : "Please correct the errors before proceeding"
      }
    });
  } catch (error: unknown) {
    console.error('Validate business info error:', error);
    const errorMessage = error instanceof Error ? error.message : 'Internal server error';
    return NextResponse.json(
      { success: false, error: errorMessage },
      { status: 500 }
    );
  }
}
