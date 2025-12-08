import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { product_id, credentials } = body;

    if (!product_id || !credentials) {
      return NextResponse.json(
        { success: false, error: 'Missing required data' },
        { status: 400 }
      );
    }

    // Call FastAPI backend with timeout (120 seconds for buyer experience)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000);

    try {
      const response = await fetch('http://localhost:8000/run-buyer-experience', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          product_id,
          credentials,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      const data = await response.json();

      if (!response.ok) {
        return NextResponse.json(
          { success: false, error: data.detail?.error || data.error || 'Buyer experience failed' },
          { status: response.status }
        );
      }

      return NextResponse.json({
        success: true,
        buyer_result: data.buyer_result,
        pricing_model: data.pricing_model,
        next_step: data.next_step,
        next_step_result: data.next_step_result,
      });
    } catch (fetchError: any) {
      clearTimeout(timeoutId);
      if (fetchError.name === 'AbortError') {
        return NextResponse.json(
          { success: false, error: 'Buyer experience request timed out. Please try again.' },
          { status: 504 }
        );
      }
      throw fetchError;
    }
  } catch (error: any) {
    console.error('Run buyer experience error:', error);
    return NextResponse.json(
      { success: false, error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
