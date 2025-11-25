import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { product_id, email, stack_name, region, credentials } = body;

    if (!product_id || !email || !stack_name || !credentials) {
      return NextResponse.json(
        { success: false, error: 'Missing required data' },
        { status: 400 }
      );
    }

    // Call FastAPI backend
    const response = await fetch('http://localhost:8000/deploy-saas', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        product_id,
        email,
        stack_name,
        region: region || 'us-east-1',
        credentials,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { success: false, error: data.error || 'Deployment failed' },
        { status: response.status }
      );
    }

    return NextResponse.json({
      success: true,
      stack_id: data.stack_id,
      message: data.message || 'SaaS integration deployed successfully',
    });
  } catch (error: any) {
    console.error('Deploy SaaS error:', error);
    return NextResponse.json(
      { success: false, error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
