import { NextRequest, NextResponse } from 'next/server';
import { invokeAgentCore } from '@/lib/agentcore';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { product_id, credentials } = body;

    console.log('[METERING API] Running metering agent for product:', product_id);

    // Extract credentials (support both camelCase and snake_case)
    const accessKeyId = credentials?.accessKeyId || credentials?.aws_access_key_id;
    const secretAccessKey = credentials?.secretAccessKey || credentials?.aws_secret_access_key;
    const sessionToken = credentials?.sessionToken || credentials?.aws_session_token;

    if (!product_id || !accessKeyId || !secretAccessKey) {
      console.error('[METERING API] Missing required data');
      return NextResponse.json(
        { success: false, error: 'Missing required data (product_id and credentials)', steps: [] },
        { status: 400 }
      );
    }

    // Invoke AgentCore metering action
    const result = await invokeAgentCore(
      {
        action: 'metering',
        product_id,
        sub_action: 'check_and_add',
      } as any,
      { accessKeyId, secretAccessKey, sessionToken }
    );

    if (!result.success) {
      console.error('[METERING API] AgentCore error:', result.error);
      return NextResponse.json(
        { 
          success: false, 
          error: result.error || 'Metering failed',
          steps: []
        },
        { status: 500 }
      );
    }

    // Extract response data
    const response = result.response as Record<string, unknown>;
    
    console.log('[METERING API] Metering agent completed');

    return NextResponse.json({
      success: response.success !== false,
      steps: response.steps || [],
      message: response.message || 'Metering check completed',
      skipped: response.skipped || false,
      reason: response.reason || null,
    });
  } catch (error: unknown) {
    console.error('[METERING API] Error:', error);
    const errorMessage = error instanceof Error ? error.message : 'Internal server error';
    return NextResponse.json(
      { success: false, error: errorMessage, steps: [] },
      { status: 500 }
    );
  }
}
