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

    // Extract the actual response data from AgentCore wrapper
    const meteringData = (result.response as Record<string, unknown>) || {};
    const lambdaTrigger = meteringData.lambda_trigger as Record<string, unknown> | undefined;

    // Build detailed steps with real backend data
    const guideSteps = [
      {
        step: 1,
        name: "Locate CloudFormation Stack & DynamoDB Tables",
        description: "Searched CloudFormation stacks to find the SaaS integration stack matching your product ID, then identified the NewSubscribers and MeteringRecords DynamoDB tables from the stack resources.",
        status: result.success ? "completed" : "failed",
        subscribers_table: meteringData.subscribers_table,
        metering_table: meteringData.metering_table,
      },
      {
        step: 2,
        name: "Check Entitlement & Retrieve Customer",
        description: `Verified the pricing model (${meteringData.pricing_model || 'N/A'}) requires metering, then scanned the NewSubscribers table to find an active customer for metering record creation.`,
        status: meteringData.customer_identifier ? "completed" : "failed",
        customer_identifier: meteringData.customer_identifier,
        pricing_model: meteringData.pricing_model,
      },
      {
        step: 3,
        name: "Resolve Usage Dimensions & Insert Metering Record",
        description: meteringData.usage_dimensions && (meteringData.usage_dimensions as any[]).length > 0
          ? `Loaded ${(meteringData.usage_dimensions as any[]).length} metered dimension(s) and inserted a test metering record into DynamoDB with metering_pending=true and 10 sample units per dimension.`
          : "Attempted to load usage dimensions from stored config, in-memory cache, or Marketplace API.",
        status: meteringData.usage_dimensions && (meteringData.usage_dimensions as any[]).length > 0 ? "completed" : "failed",
        usage_dimensions: meteringData.usage_dimensions,
        timestamp: meteringData.timestamp,
      },
      {
        step: 4,
        name: "Trigger Hourly Metering Lambda",
        description: lambdaTrigger
          ? lambdaTrigger.status === "triggered"
            ? `Found and invoked the hourly metering Lambda function (${lambdaTrigger.function_name || 'N/A'}). The Lambda reads pending metering records from DynamoDB and calls the AWS Marketplace BatchMeterUsage API to report usage.`
            : lambdaTrigger.status === "not_found"
              ? "Could not find a Lambda function with 'hourly' in its name. The metering record was saved to DynamoDB but won't be processed until the Lambda runs."
              : `Lambda invocation failed: ${lambdaTrigger.message || lambdaTrigger.error || 'Unknown error'}`
          : "Waiting for entitlement check to complete before triggering Lambda.",
        status: lambdaTrigger
          ? lambdaTrigger.status === "triggered" ? "completed"
            : lambdaTrigger.status === "not_found" ? "warning"
            : "failed"
          : meteringData.status === "success" ? "warning" : "pending",
        lambda_function: lambdaTrigger?.function_name as string | undefined,
        lambda_result: lambdaTrigger ? { status: lambdaTrigger.status, status_code: lambdaTrigger.status_code } : undefined,
      },
    ];

    return NextResponse.json({
      success: true,
      steps: guideSteps,
      message: meteringData.message || 'Metering workflow completed',
      metering_result: meteringData
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
