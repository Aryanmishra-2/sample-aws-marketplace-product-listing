import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    // Return the public visibility guide steps
    const guide = {
      title: "Request Public Visibility",
      description: "Submit a request to make your product publicly available on AWS Marketplace",
      steps: [
        {
          step: 1,
          title: "Prepare Product Information",
          description: "Ensure your product listing has all required information",
          actions: [
            "Verify product title, description, and features are complete",
            "Confirm pricing information is accurate",
            "Ensure all required documentation is uploaded",
            "Review product screenshots and marketing materials"
          ]
        },
        {
          step: 2,
          title: "Submit Public Visibility Request",
          description: "Request to change product visibility from Limited to Public",
          actions: [
            "Navigate to AWS Marketplace Management Portal",
            "Select your product",
            "Go to 'Offers' tab",
            "Click 'Request changes to public offer'",
            "Submit the visibility change request"
          ]
        },
        {
          step: 3,
          title: "AWS Review Process",
          description: "AWS will review your request",
          expected: [
            "Review typically takes 1-3 business days",
            "You'll receive email notifications about the status",
            "AWS may request additional information or changes",
            "Once approved, your product will be publicly visible"
          ]
        },
        {
          step: 4,
          title: "Monitor Request Status",
          description: "Track the status of your visibility request",
          actions: [
            "Check your email for AWS Marketplace notifications",
            "Monitor the 'Request Log' in the Management Portal",
            "Respond promptly to any AWS requests for information",
            "Once approved, verify your product appears in public search"
          ]
        }
      ]
    };

    return NextResponse.json({
      success: true,
      guide
    });
  } catch (error: any) {
    console.error('Error in public-visibility-guide:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: error.message || 'Failed to get public visibility guide' 
      },
      { status: 500 }
    );
  }
}
