// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
import { NextRequest, NextResponse } from 'next/server';
import { invokeAgentCore } from '@/lib/agentcore';

// Call the full create_listing orchestration
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { listing_data, credentials } = body;

    const accessKeyId = credentials?.accessKeyId || credentials?.aws_access_key_id;
    const secretAccessKey = credentials?.secretAccessKey || credentials?.aws_secret_access_key;
    const sessionToken = credentials?.sessionToken || credentials?.aws_session_token;

    if (!accessKeyId || !secretAccessKey) {
      return NextResponse.json(
        { success: false, error: 'AWS credentials are required' },
        { status: 400 }
      );
    }

    console.log('[create-listing-stream] Calling create_listing (full orchestration)');

    // Call the full create_listing action - this runs all stages
    const result = await invokeAgentCore(
      {
        action: 'create_listing',
        listing_data: listing_data,
      } as any,
      { accessKeyId, secretAccessKey, sessionToken }
    );

    console.log('[create-listing-stream] Result:', JSON.stringify(result, null, 2));

    if (!result.success) {
      return NextResponse.json(
        { success: false, error: result.error || 'Failed to create listing' },
        { status: 500 }
      );
    }

    const response = result.response as Record<string, unknown>;
    
    return NextResponse.json({
      success: response.success !== false,
      product_id: response.product_id,
      offer_id: response.offer_id,
      published_to_limited: response.published_to_limited,
      message: response.message,
      stages: response.stages,
      error: response.error,
    });
  } catch (error: unknown) {
    console.error('Error in create-listing-stream:', error);
    const errorMessage = error instanceof Error ? error.message : 'Failed to create listing';
    return NextResponse.json(
      { success: false, error: errorMessage },
      { status: 500 }
    );
  }
}
