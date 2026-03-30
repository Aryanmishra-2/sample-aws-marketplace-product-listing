// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
import { NextRequest, NextResponse } from 'next/server';
import { invokeAgentCore } from '@/lib/agentcore';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { aws_access_key_id, aws_secret_access_key, aws_session_token } = body;

    if (!aws_access_key_id || !aws_secret_access_key) {
      return NextResponse.json(
        { success: false, error: 'Missing credentials' },
        { status: 400 }
      );
    }

    // Call AgentCore backend which has the full product listing logic
    const result = await invokeAgentCore(
      {
        action: 'list_marketplace_products',
      } as any,
      {
        accessKeyId: aws_access_key_id,
        secretAccessKey: aws_secret_access_key,
        sessionToken: aws_session_token,
      }
    );

    if (!result.success) {
      console.error('AgentCore list products error:', result.error);
      return NextResponse.json({
        success: true,
        products: [],
        total: 0,
        message: result.error || 'No products found',
      });
    }

    const response = result.response as Record<string, unknown>;

    return NextResponse.json({
      success: true,
      products: response.products || [],
      total: response.count || 0,
      account_id: response.account_id,
    });
  } catch (error: any) {
    console.error('List marketplace products API error:', error);
    
    return NextResponse.json({
      success: true,
      products: [],
      total: 0,
      message: 'Failed to load products',
    });
  }
}
