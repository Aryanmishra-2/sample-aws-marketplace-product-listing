import { NextRequest, NextResponse } from 'next/server';
import { invokeAnalyzeProduct } from '@/lib/agentcore';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { product_context, credentials } = body;

    if (!product_context) {
      return NextResponse.json(
        { success: false, error: 'Missing product context' },
        { status: 400 }
      );
    }

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
    const result = await invokeAnalyzeProduct(
      product_context,
      { accessKeyId, secretAccessKey, sessionToken }
    );

    if (!result.success) {
      return NextResponse.json(
        { success: false, error: result.error || 'Analysis failed' },
        { status: 500 }
      );
    }

    // Extract analysis from response
    let analysis;
    if (typeof result.response === 'object' && result.response !== null) {
      const resp = result.response as Record<string, unknown>;
      analysis = resp.analysis || resp;
    } else {
      analysis = { raw_response: result.response };
    }

    return NextResponse.json({
      success: true,
      analysis: analysis,
    });
  } catch (error: unknown) {
    console.error('Analyze product error:', error);
    const errorMessage = error instanceof Error ? error.message : 'Internal server error';
    return NextResponse.json(
      { success: false, error: errorMessage },
      { status: 500 }
    );
  }
}
