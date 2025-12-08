import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { stack_name, region, credentials } = body;

    if (!stack_name || !credentials) {
      return NextResponse.json(
        { success: false, error: 'Missing required data' },
        { status: 400 }
      );
    }

    // Call FastAPI backend with short timeout (deletion is now non-blocking)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 seconds

    try {
      const response = await fetch('http://localhost:8000/delete-stack', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          stack_name,
          region: region || 'us-east-1',
          credentials,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      const data = await response.json();

      if (!response.ok) {
        return NextResponse.json(
          { success: false, error: data.detail?.error || data.error || 'Stack deletion failed' },
          { status: response.status }
        );
      }

      return NextResponse.json({
        success: true,
        message: data.message || 'Stack deletion initiated',
        stack_name: data.stack_name,
        status: data.status,
      });
    } catch (fetchError: any) {
      clearTimeout(timeoutId);
      if (fetchError.name === 'AbortError') {
        return NextResponse.json(
          { success: false, error: 'Stack deletion request timed out. Please try again.' },
          { status: 504 }
        );
      }
      throw fetchError;
    }
  } catch (error: any) {
    console.error('Delete stack error:', error);
    return NextResponse.json(
      { success: false, error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
