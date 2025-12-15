import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { question } = body;

    if (!question) {
      return NextResponse.json(
        { success: false, error: 'Question is required' },
        { status: 400 }
      );
    }

    // Forward to backend
    const response = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question }),
    });

    const data = await response.json();

    return NextResponse.json(data);
  } catch (error: any) {
    console.error('Chat API error:', error);
    return NextResponse.json(
      { success: false, error: error.message || 'Failed to get response' },
      { status: 500 }
    );
  }
}
