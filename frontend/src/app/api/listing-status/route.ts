import { NextRequest, NextResponse } from 'next/server';
import { invokeAgentCore } from '@/lib/agentcore';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { change_set_id, credentials } = body;

    // Extract credentials
    const accessKeyId = credentials?.accessKeyId || credentials?.aws_access_key_id;
    const secretAccessKey = credentials?.secretAccessKey || credentials?.aws_secret_access_key;
    const sessionToken = credentials?.sessionToken || credentials?.aws_session_token;

    if (!accessKeyId || !secretAccessKey) {
      return NextResponse.json(
        { success: false, error: 'AWS credentials are required' },
        { status: 400 }
      );
    }

    if (!change_set_id) {
      return NextResponse.json(
        { success: false, error: 'change_set_id is required' },
        { status: 400 }
      );
    }

    // Check listing status
    const result = await invokeAgentCore(
      {
        action: 'listing_get_status',
        change_set_id,
      } as any,
      { accessKeyId, secretAccessKey, sessionToken }
    );

    if (!result.success) {
      return NextResponse.json(
        { success: false, error: result.error || 'Failed to get listing status' },
        { status: 500 }
      );
    }

    const response = result.response as Record<string, unknown>;
    
    return NextResponse.json({
      success: true,
      status: response.status,
      product_id: response.product_id,
      offer_id: response.offer_id,
      message: response.message,
      error: response.error,
    });
  } catch (error: unknown) {
    console.error('Error in listing-status route:', error);
    const errorMessage = error instanceof Error ? error.message : 'Failed to get listing status';
    return NextResponse.json(
      { success: false, error: errorMessage },
      { status: 500 }
    );
  }
}
