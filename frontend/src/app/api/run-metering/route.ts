import { NextRequest, NextResponse } from 'next/server';
import { invokeAgentCore } from '@/lib/agentcore';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { product_id, credentials, pricing_dimensions } = body;

    if (!product_id || !credentials) {
      return NextResponse.json(
        { success: false, error: 'Missing required parameters' },
        { status: 400 }
      );
    }

    // Extract credentials (support both camelCase and snake_case)
    const accessKeyId = credentials?.accessKeyId || credentials?.aws_access_key_id;
    const secretAccessKey = credentials?.secretAccessKey || credentials?.aws_secret_access_key;
    const sessionToken = credentials?.sessionToken || credentials?.aws_session_token;

    if (!accessKeyId || !secretAccessKey) {
      return NextResponse.json(
        { success: false, error: 'Missing AWS credentials' },
        { status: 400 }
      );
    }

    console.log('[RUN-METERING] Starting metering workflow for product:', product_id);
    console.log('[RUN-METERING] Has pricing dimensions:', !!pricing_dimensions);
    console.log('[RUN-METERING] Pricing dimensions:', pricing_dimensions);
    console.log('[RUN-METERING] Credentials:', {
      hasAccessKey: !!accessKeyId,
      hasSecretKey: !!secretAccessKey,
      hasSessionToken: !!sessionToken
    });

    // Invoke AgentCore run_metering action
    console.log('[RUN-METERING] Calling AgentCore with payload:', {
      action: 'run_metering',
      product_id,
      has_pricing_dimensions: !!pricing_dimensions
    });
    
    const result = await invokeAgentCore(
      {
        action: 'run_metering',
        product_id,
        pricing_dimensions,
      } as any,
      { accessKeyId, secretAccessKey, sessionToken }
    );

    console.log('[RUN-METERING] AgentCore response:', result);
    console.log('[RUN-METERING] Response success:', result.success);
    console.log('[RUN-METERING] Response status:', result.status);
    console.log('[RUN-METERING] Response reason:', result.reason);

    if (!result.success) {
      console.error('[RUN-METERING] AgentCore error:', result.error);
      return NextResponse.json(
        { 
          success: false, 
          error: result.error || 'Failed to run metering workflow' 
        },
        { status: 500 }
      );
    }

    console.log('[RUN-METERING] Metering workflow completed:', result);

    // Add metering guide steps to the response
    const guideSteps = [
      {
        step: 1,
        title: "Verify SaaS Integration",
        description: "Ensure your SaaS integration stack is deployed and running",
        status: result.success ? "completed" : "pending"
      },
      {
        step: 2,
        title: "Configure Metering Dimensions",
        description: "Set up the usage dimensions you want to track (API calls, users, storage, etc.)",
        status: result.usage_dimensions && result.usage_dimensions.length > 0 ? "completed" : "pending"
      },
      {
        step: 3,
        title: "Test Metering Records",
        description: "Send test metering records to verify the integration",
        status: result.status === "success" ? "completed" : "pending"
      },
      {
        step: 4,
        title: "Monitor Usage",
        description: "Use CloudWatch to monitor metering records and customer usage",
        status: "pending"
      }
    ];

    return NextResponse.json({
      success: true,
      steps: guideSteps,
      message: result.message,
      metering_result: result
    });
  } catch (error: any) {
    console.error('[RUN-METERING] Error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: error.message || 'Failed to run metering workflow' 
      },
      { status: 500 }
    );
  }
}
