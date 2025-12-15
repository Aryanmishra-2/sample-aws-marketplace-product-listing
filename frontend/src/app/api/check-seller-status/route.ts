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
    const response = await fetch('http://localhost:8000/check-seller-status', {
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
        { success: false, error: data.error || 'Status check failed' },
        { status: response.status }
      );
    }

    return NextResponse.json({
      success: true,
      seller_status: data.seller_status,
      account_id: data.account_id,
      owned_products: data.owned_products || [],
      message: data.message || '',
    });
  } catch (error: any) {
    console.error('Check seller status error:', error);
    return NextResponse.json(
      { success: false, error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
