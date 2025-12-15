import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Forward to backend with timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
    
    try {
      const response = await fetch('http://localhost:8000/get-stack-status', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      const data = await response.json();
      return NextResponse.json(data);
    } catch (fetchError: any) {
      clearTimeout(timeoutId);
      if (fetchError.name === 'AbortError') {
        return NextResponse.json(
          { success: false, error: 'Request timeout', stack_status: 'POLLING' },
          { status: 200 } // Return 200 so frontend continues polling
        );
      }
      throw fetchError;
    }
  } catch (error: any) {
    console.error('Stack status API error:', error);
    return NextResponse.json(
      { success: false, error: error.message || 'Failed to get stack status' },
      { status: 500 }
    );
  }
}
