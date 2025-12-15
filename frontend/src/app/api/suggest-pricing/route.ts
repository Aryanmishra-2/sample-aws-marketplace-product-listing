import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { analysis, credentials } = body;

    // Call FastAPI backend
    const response = await fetch('http://localhost:8000/suggest-pricing', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ analysis, credentials }),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { success: false, error: data.error || 'Pricing suggestion failed' },
        { status: response.status }
      );
    }

    return NextResponse.json({
      success: true,
      pricing: data.pricing,
    });
  } catch (error: any) {
    console.error('Suggest pricing error:', error);
    return NextResponse.json(
      { success: false, error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
