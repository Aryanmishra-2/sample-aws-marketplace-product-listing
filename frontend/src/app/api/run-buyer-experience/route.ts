import { NextRequest, NextResponse } from 'next/server';
import { invokeAgentCore } from '@/lib/agentcore';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { product_id, credentials, pricing_model } = body;

    console.log('[BUYER EXP API] Running buyer experience for product:', product_id);

    // Extract credentials (support both camelCase and snake_case)
    const accessKeyId = credentials?.accessKeyId || credentials?.aws_access_key_id;
    const secretAccessKey = credentials?.secretAccessKey || credentials?.aws_secret_access_key;
    const sessionToken = credentials?.sessionToken || credentials?.aws_session_token;

    if (!product_id || !accessKeyId || !secretAccessKey) {
      return NextResponse.json(
        { success: false, error: 'Missing required data (product_id and credentials)' },
        { status: 400 }
      );
    }

    // Invoke AgentCore buyer_experience action
    const result = await invokeAgentCore(
      {
        action: 'buyer_experience',
        product_id,
        sub_action: 'simulate',
      } as any,
      { accessKeyId, secretAccessKey, sessionToken }
    );

    if (!result.success) {
      console.error('[BUYER EXP API] AgentCore error:', result.error);
      return NextResponse.json(
        { success: false, error: result.error || 'Buyer experience failed' },
        { status: 500 }
      );
    }

    // Extract response data
    const response = result.response as Record<string, unknown>;
    
    console.log('[BUYER EXP API] Buyer experience completed');

    return NextResponse.json({
      success: response.success !== false,
      buyer_result: response.buyer_result || response,
      pricing_model: pricing_model,
      next_step: response.next_step,
      next_step_result: response.next_step_result,
    });
  } catch (error: unknown) {
    console.error('[BUYER EXP API] Error:', error);
    const errorMessage = error instanceof Error ? error.message : 'Internal server error';
    return NextResponse.json(
      { success: false, error: errorMessage },
      { status: 500 }
    );
  }
}
