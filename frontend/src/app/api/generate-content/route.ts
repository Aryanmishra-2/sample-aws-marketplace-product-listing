import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { analysis, product_context } = body;

    // Call FastAPI backend
    const response = await fetch('http://localhost:8000/generate-content', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ analysis, product_context }),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { success: false, error: data.error || 'Content generation failed' },
        { status: response.status }
      );
    }

    return NextResponse.json({
      success: true,
      content: data.content,
    });
  } catch (error: any) {
    console.error('Generate content error:', error);
    return NextResponse.json(
      { success: false, error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
