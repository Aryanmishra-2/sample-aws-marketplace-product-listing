import { NextRequest, NextResponse } from 'next/server';
import { invokeAgentCore } from '@/lib/agentcore';

export async function POST(request: NextRequest) {
  const requestId = Math.random().toString(36).substring(7);
  const timestamp = new Date().toISOString();
  
  console.log(`[${timestamp}] [REQUEST-${requestId}] CREATE-LISTING REQUEST`);
  
  try {
    const body = await request.json();
    const { listing_data, credentials, product_id } = body;

    console.log(`[${timestamp}] [REQUEST-${requestId}] Product Title: ${listing_data?.title}`);

    // Extract credentials (support both camelCase and snake_case)
    const accessKeyId = credentials?.accessKeyId || credentials?.aws_access_key_id;
    const secretAccessKey = credentials?.secretAccessKey || credentials?.aws_secret_access_key;
    const sessionToken = credentials?.sessionToken || credentials?.aws_session_token;

    if (!listing_data || !accessKeyId || !secretAccessKey) {
      console.log(`[${timestamp}] [REQUEST-${requestId}] ERROR: Missing required data`);
      return NextResponse.json(
        { success: false, error: 'Missing required data (listing_data and credentials)' },
        { status: 400 }
      );
    }

    // Invoke AgentCore create_listing action
    const result = await invokeAgentCore(
      {
        action: 'create_listing',
        listing_data,
        product_id,
      } as any,
      { accessKeyId, secretAccessKey, sessionToken }
    );

    if (!result.success) {
      console.log(`[${timestamp}] [REQUEST-${requestId}] ERROR: AgentCore error`);
      return NextResponse.json(
        { success: false, error: result.error || 'Listing creation failed' },
        { status: 500 }
      );
    }

    const response = result.response as Record<string, unknown>;

    console.log(`[${timestamp}] [REQUEST-${requestId}] SUCCESS`);
    
    return NextResponse.json({
      success: response.success !== false,
      product_id: response.product_id,
      offer_id: response.offer_id,
      published_to_limited: response.published_to_limited || false,
      message: response.message || 'Listing data prepared',
      stages: response.stages || [],
      listing_data: response.listing_data,
      note: response.note,
    });
  } catch (error: unknown) {
    console.error(`[${timestamp}] [REQUEST-${requestId}] EXCEPTION:`, error);
    const errorMessage = error instanceof Error ? error.message : 'Internal server error';
    return NextResponse.json(
      { success: false, error: errorMessage },
      { status: 500 }
    );
  }
}
