import { NextRequest, NextResponse } from 'next/server';
import { invokeAgentCore } from '@/lib/agentcore';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { product_id, email, stack_name, region, credentials, pricing_model, pricing_dimensions } = body;

    console.log('[DEPLOY SAAS] Received pricing_model:', pricing_model);

    // Extract credentials (support both camelCase and snake_case)
    const accessKeyId = credentials?.accessKeyId || credentials?.aws_access_key_id;
    const secretAccessKey = credentials?.secretAccessKey || credentials?.aws_secret_access_key;
    const sessionToken = credentials?.sessionToken || credentials?.aws_session_token;

    if (!product_id || !email || !accessKeyId || !secretAccessKey) {
      return NextResponse.json(
        { success: false, error: 'Missing required data (product_id, email, credentials)' },
        { status: 400 }
      );
    }

    if (!pricing_model) {
      console.log('[DEPLOY SAAS] Pricing model is missing!');
      return NextResponse.json(
        { success: false, error: 'Pricing model is required' },
        { status: 400 }
      );
    }

    // Invoke AgentCore deploy_saas action
    const result = await invokeAgentCore(
      {
        action: 'deploy_saas',
        product_id,
        email,
        pricing_model,
        pricing_dimensions,
        region: region || 'us-east-1',
      } as any,
      { accessKeyId, secretAccessKey, sessionToken }
    );

    if (!result.success) {
      console.error('[DEPLOY SAAS] AgentCore error:', result.error);
      return NextResponse.json(
        { success: false, error: result.error || 'Deployment failed' },
        { status: 500 }
      );
    }

    const response = result.response as Record<string, unknown>;

    return NextResponse.json({
      success: response.success !== false,
      stack_id: response.stack_id,
      stack_name: response.stack_name,
      message: response.message || 'SaaS integration deployment initiated',
      status: response.status,
    });
  } catch (error: unknown) {
    console.error('[DEPLOY SAAS] Error:', error);
    const errorMessage = error instanceof Error ? error.message : 'Internal server error';
    return NextResponse.json(
      { success: false, error: errorMessage },
      { status: 500 }
    );
  }
}
