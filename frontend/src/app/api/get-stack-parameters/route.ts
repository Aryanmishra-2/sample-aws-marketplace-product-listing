// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
import { NextRequest, NextResponse } from 'next/server';
import { invokeAgentCore } from '@/lib/agentcore';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { stack_name, region, credentials } = body;

    if (!stack_name || !credentials) {
      return NextResponse.json(
        { success: false, error: 'Missing required parameters' },
        { status: 400 }
      );
    }

    // Extract credentials (support both camelCase and snake_case)
    const accessKeyId = credentials?.accessKeyId || credentials?.aws_access_key_id;
    const secretAccessKey = credentials?.secretAccessKey || credentials?.aws_secret_access_key;
    const sessionToken = credentials?.sessionToken || credentials?.aws_session_token;

    if (!accessKeyId || !secretAccessKey) {
      return NextResponse.json(
        { success: false, error: 'Missing AWS credentials' },
        { status: 400 }
      );
    }

    console.log('[GET-STACK-PARAMETERS] Fetching parameters for stack:', stack_name);

    // Invoke AgentCore get_stack_parameters action
    const result = await invokeAgentCore(
      {
        action: 'get_stack_parameters',
        stack_name,
        region: region || 'us-east-1',
      } as any,
      { accessKeyId, secretAccessKey, sessionToken }
    );

    if (!result.success) {
      console.error('[GET-STACK-PARAMETERS] AgentCore error:', result.error);
      return NextResponse.json(
        { 
          success: false, 
          error: result.error || 'Failed to get stack parameters' 
        },
        { status: 500 }
      );
    }

    console.log('[GET-STACK-PARAMETERS] Stack parameters retrieved:', result);

    return NextResponse.json({
      success: true,
      pricing_model: result.pricing_model,
      pricing_dimensions: result.pricing_dimensions,
      parameters: result.parameters,
      outputs: result.outputs,
      status: result.status,
    });
  } catch (error: any) {
    console.error('[GET-STACK-PARAMETERS] Error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: error.message || 'Failed to get stack parameters' 
      },
      { status: 500 }
    );
  }
}
