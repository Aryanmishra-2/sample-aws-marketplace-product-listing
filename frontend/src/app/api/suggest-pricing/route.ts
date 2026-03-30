// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
import { NextRequest, NextResponse } from 'next/server';
import { invokeAgentCore } from '@/lib/agentcore';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { analysis, product_context, credentials } = body;

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

    // Invoke AgentCore
    const result = await invokeAgentCore(
      {
        action: 'suggest_pricing',
        analysis,
        product_context,
      } as any,
      { accessKeyId, secretAccessKey, sessionToken }
    );

    if (!result.success) {
      return NextResponse.json(
        { success: false, error: result.error || 'Pricing suggestion failed' },
        { status: 500 }
      );
    }

    // Extract pricing from response
    let pricing;
    if (typeof result.response === 'object' && result.response !== null) {
      const resp = result.response as Record<string, unknown>;
      pricing = resp.pricing || resp;
    } else {
      pricing = { raw_response: result.response };
    }

    return NextResponse.json({
      success: true,
      pricing: pricing,
    });
  } catch (error: unknown) {
    console.error('Suggest pricing error:', error);
    const errorMessage = error instanceof Error ? error.message : 'Internal server error';
    return NextResponse.json(
      { success: false, error: errorMessage },
      { status: 500 }
    );
  }
}
