import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { aws_access_key_id, aws_secret_access_key, aws_session_token } = body;

    if (!aws_access_key_id || !aws_secret_access_key) {
      return NextResponse.json(
        { success: false, error: 'Missing required credentials' },
        { status: 400 }
      );
    }

    // Call FastAPI backend
    const response = await fetch('http://localhost:8000/validate-credentials', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        aws_access_key_id,
        aws_secret_access_key,
        aws_session_token,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { success: false, error: data.error || 'Validation failed' },
        { status: response.status }
      );
    }

    return NextResponse.json({
      success: true,
      account_id: data.account_id,
      region_type: data.region_type,
      user_arn: data.user_arn,
      organization: data.organization,
      session_id: data.session_id || 'session-' + Date.now(),
    });
  } catch (error: any) {
    console.error('Validate credentials error:', error);
    return NextResponse.json(
      { success: false, error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
