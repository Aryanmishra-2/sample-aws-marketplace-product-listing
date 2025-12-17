import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const registrationData = body.registration_data || {};

    // Return progress based on provided data
    const steps = [
      {
        step: 1,
        name: "Account Creation",
        status: "completed",
        description: "AWS account created"
      },
      {
        step: 2,
        name: "Business Information",
        status: registrationData.business_name ? "completed" : "pending",
        description: "Business details submitted"
      },
      {
        step: 3,
        name: "Tax Information",
        status: registrationData.tax_id ? "completed" : "pending",
        description: "Tax details verified"
      },
      {
        step: 4,
        name: "Payment Setup",
        status: registrationData.payment_info ? "completed" : "pending",
        description: "Payment method configured"
      },
      {
        step: 5,
        name: "Terms Acceptance",
        status: registrationData.terms_accepted ? "completed" : "pending",
        description: "AWS Marketplace terms accepted"
      }
    ];

    const completedSteps = steps.filter(s => s.status === "completed").length;
    const totalSteps = steps.length;
    const progressPercent = Math.round((completedSteps / totalSteps) * 100);

    return NextResponse.json({
      success: true,
      progress: {
        steps,
        completed_steps: completedSteps,
        total_steps: totalSteps,
        progress_percent: progressPercent,
        is_complete: completedSteps === totalSteps,
        next_step: steps.find(s => s.status === "pending")?.name || null
      }
    });
  } catch (error: unknown) {
    console.error('Check registration progress error:', error);
    const errorMessage = error instanceof Error ? error.message : 'Internal server error';
    return NextResponse.json(
      { success: false, error: errorMessage },
      { status: 500 }
    );
  }
}
