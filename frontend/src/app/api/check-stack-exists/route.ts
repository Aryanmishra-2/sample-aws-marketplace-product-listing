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

    // Invoke AgentCore check_stack_exists action
    const result = await invokeAgentCore(
      {
        action: 'check_stack_exists',
        stack_name,
        product_id,
        region: region || 'us-east-1',
      } as any,
      { accessKeyId, secretAccessKey, sessionToken }
    );

    if (!result.success) {
      console.error('AgentCore check_stack_exists error:', result.error);
      // Return exists: false on error
      return NextResponse.json({
        success: true,
        exists: false,
        stack_name: stack_name || `saas-integration-${product_id}`,
      });
    }

    const response = result.response as Record<string, unknown>;

    return NextResponse.json({
      success: true,
      exists: response.exists || false,
      stack_name: response.stack_name,
      stack_id: response.stack_id,
      status: response.status,
    });
  } catch (error: unknown) {
    console.error('Check stack exists error:', error);
    // If error, assume stack doesn't exist
    return NextResponse.json({
      success: true,
      exists: false,
      stack_name: stack_name || `saas-integration-${product_id}`,
    });
  }
}
