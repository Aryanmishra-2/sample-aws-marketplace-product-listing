import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Forward to backend
    const response = await fetch('http://localhost:8000/create-listing-with-stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    
    return NextResponse.json(data);
  } catch (error: any) {
    console.error('Error in create-listing-stream route:', error);
    return NextResponse.json(
      { success: false, error: error.message || 'Failed to start listing creation' },
      { status: 500 }
    );
  }
}
