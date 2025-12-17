import { NextRequest, NextResponse } from 'next/server';
import { invokeAgentCore } from '@/lib/agentcore';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { listing_data, credentials, product_id } = body;

    // Extract credentials (support both camelCase and snake_case)
    const accessKeyId = credentials?.accessKeyId || credentials?.aws_access_key_id;
    const secretAccessKey = credentials?.secretAccessKey || credentials?.aws_secret_access_key;
    const sessionToken = credentials?.sessionToken || credentials?.aws_session_token;

    if (!accessKeyId || !secretAccessKey) {
      return NextResponse.json(
        { success: false, error: 'AWS credentials are required' },
        { status: 400 }
      );
    }

    console.log('[create-listing-stream] Invoking AgentCore create_listing action');

    // Invoke AgentCore create_listing action
    const result = await invokeAgentCore(
      {
        action: 'create_listing',
        listing_data,
        product_id,
      } as any,
      { accessKeyId, secretAccessKey, sessionToken }
    );

    console.log('[create-listing-stream] AgentCore result:', JSON.stringify(result, null, 2));

    if (!result.success) {
      return NextResponse.json(
        { success: false, error: result.error || 'Failed to create listing' },
        { status: 500 }
      );
    }

    const response = result.response as Record<string, unknown>;
    
    // Return full response including stages for progress tracking
    return NextResponse.json({
      success: response.success !== false,
      product_id: response.product_id,
      offer_id: response.offer_id,
      published_to_limited: response.published_to_limited || false,
      message: response.message,
      stages: response.stages || [],
      listing_data: response.listing_data,
      note: response.note,
      error: response.error,
    });
  } catch (error: unknown) {
    console.error('Error in create-listing-stream route:', error);
    const errorMessage = error instanceof Error ? error.message : 'Failed to start listing creation';
    return NextResponse.json(
      { success: false, error: errorMessage },
      { status: 500 }
    );
  }
}
