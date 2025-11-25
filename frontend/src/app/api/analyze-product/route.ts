import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { product_context } = body;

    if (!product_context) {
      return NextResponse.json(
        { success: false, error: 'Missing product context' },
        { status: 400 }
      );
    }

    // Call FastAPI backend
    const response = await fetch('http://localhost:8000/analyze-product', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ product_context }),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { success: false, error: data.error || 'Analysis failed' },
        { status: response.status }
      );
    }

    return NextResponse.json({
      success: true,
      analysis: data.analysis,
    });
  } catch (error: any) {
    console.error('Analyze product error:', error);
    return NextResponse.json(
      { success: false, error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
