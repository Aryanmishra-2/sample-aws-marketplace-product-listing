import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const registrationData = body.registration_data || {};

    // Generate a preview of the registration data
    const preview = {
      business_details: {
        name: registrationData.business_name || "Not provided",
        address: registrationData.business_address || "Not provided",
        country: registrationData.country || "Not provided",
        tax_id: registrationData.tax_id ? "Provided" : "Not provided"
      },
      contact_details: {
        email: registrationData.contact_email || "Not provided",
        phone: registrationData.contact_phone || "Not provided"
      },
      payment_status: registrationData.payment_info ? "Configured" : "Not configured",
      terms_status: registrationData.terms_accepted ? "Accepted" : "Not accepted",
      estimated_review_time: "2-5 business days",
      notes: [
        "All information will be verified by AWS",
        "You will receive email confirmation once approved",
        "Additional documentation may be requested"
      ]
    };

    return NextResponse.json({
      success: true,
      preview
    });
  } catch (error: unknown) {
    console.error('Generate registration preview error:', error);
    const errorMessage = error instanceof Error ? error.message : 'Internal server error';
    return NextResponse.json(
      { success: false, error: errorMessage },
      { status: 500 }
    );
  }
}
