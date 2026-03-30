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
        action: 'generate_content',
        analysis,
        product_context,
      } as any,
      { accessKeyId, secretAccessKey, sessionToken }
    );

    if (!result.success) {
      return NextResponse.json(
        { success: false, error: result.error || 'Content generation failed' },
        { status: 500 }
      );
    }

    // Extract content from response
    let content;
    if (typeof result.response === 'object' && result.response !== null) {
      const resp = result.response as Record<string, unknown>;
      content = resp.content || resp;
    } else {
      content = { raw_response: result.response };
    }

    return NextResponse.json({
      success: true,
      content: content,
    });
  } catch (error: unknown) {
    console.error('Generate content error:', error);
    const errorMessage = error instanceof Error ? error.message : 'Internal server error';
    return NextResponse.json(
      { success: false, error: errorMessage },
      { status: 500 }
    );
  }
}
