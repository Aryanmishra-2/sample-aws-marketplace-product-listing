// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
import { NextRequest, NextResponse } from 'next/server';
import { invokeAgentCore } from '@/lib/agentcore';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { stack_name, product_id, credentials, region } = body;

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

    if (!stack_name && !product_id) {
      return NextResponse.json(
        { success: false, error: 'stack_name or product_id is required' },
        { status: 400 }
      );
    }

    // Invoke AgentCore get_stack_status action
    const result = await invokeAgentCore(
      {
        action: 'get_stack_status',
        stack_name,
        product_id,
        region: region || 'us-east-1',
      } as any,
      { accessKeyId, secretAccessKey, sessionToken }
    );

    if (!result.success) {
      return NextResponse.json(
        { success: false, error: result.error || 'Failed to get stack status', stack_status: 'POLLING' },
        { status: 200 } // Return 200 so frontend continues polling
      );
    }

    const response = result.response as Record<string, unknown>;

    return NextResponse.json({
      success: response.success !== false,
      stack_name: response.stack_name,
      stack_status: response.status,
      status_reason: response.status_reason,
      outputs: response.outputs,
      creation_time: response.creation_time,
    });
  } catch (error: unknown) {
    console.error('Stack status API error:', error);
    const errorMessage = error instanceof Error ? error.message : 'Failed to get stack status';
    return NextResponse.json(
      { success: false, error: errorMessage, stack_status: 'POLLING' },
      { status: 200 } // Return 200 so frontend continues polling
    );
  }
}
