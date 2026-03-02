import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    // Return the detailed buyer experience steps from buyer_experience.py
    const guide = {
      title: "AWS Marketplace Buyer Experience Simulation",
      description: "Follow these steps to test your SaaS product as a buyer would",
      documentation_url: "https://docs.aws.amazon.com/marketplace/latest/userguide/saas-integration-testing.html",
      steps: [
        {
          step: 1,
          title: "Access Product in AWS Marketplace Management Portal",
          description: "Navigate to your product listing in the AWS Marketplace Management Portal",
          actions: [
            "Open AWS Marketplace Management Portal: https://aws.amazon.com/marketplace/management/products",
            "Navigate to your SaaS product listing",
            "Select your product"
          ],
          icon: "🏢",
          color: "#0073bb"
        },
        {
          step: 2,
          title: "Validate Fulfillment URL Update",
          description: "Verify that the fulfillment URL was updated successfully",
          actions: [
            "Go to the 'Request Log' tab",
            "Check that the last request status is 'Succeeded'",
            "This confirms the fulfillment URL was updated successfully"
          ],
          icon: "✅",
          color: "#037f0c"
        },
        {
          step: 3,
          title: "Review Product Information",
          description: "Verify your product information is accurate",
          actions: [
            "Select 'View on AWS Marketplace'",
            "Review that your product information is accurate",
            "Verify pricing, description, and features are correct"
          ],
          icon: "👁️",
          color: "#0073bb"
        },
        {
          step: 4,
          title: "Simulate Purchase Process",
          description: "Complete a test purchase of your product",
          actions: [
            "Select 'View purchase options'",
            "Under 'How long do you want your contract to run?', select '1 month'",
            "Set 'Renewal Settings' to 'No'",
            "Under 'Contract Options', set any option quantity to 1",
            "Select 'Create contract' then 'Pay now'"
          ],
          icon: "🛍️",
          color: "#ff9900"
        },
        {
          step: 5,
          title: "Account Setup and Registration",
          description: "Complete the registration process",
          actions: [
            "Select 'Set up your account'",
            "You'll be redirected to your custom registration page",
            "Fill in the registration information (Company name, Contact email, etc.)",
            "Select 'Register'"
          ],
          icon: "📝",
          color: "#0073bb"
        },
        {
          step: 6,
          title: "Verify Registration Success",
          description: "Confirm the registration was successful",
          expected: [
            "Blue banner appears confirming successful registration",
            "Email notification sent to your admin email",
            "Customer record created in DynamoDB"
          ],
          icon: "🎉",
          color: "#037f0c"
        }
      ]
    };

    return NextResponse.json({
      success: true,
      guide
    });
  } catch (error: any) {
    console.error('Error in buyer-experience-guide:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: error.message || 'Failed to get buyer experience guide' 
      },
      { status: 500 }
    );
  }
}
