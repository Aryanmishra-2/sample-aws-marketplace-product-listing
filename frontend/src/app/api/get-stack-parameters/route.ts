import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { stack_name, region, credentials } = body;

    console.log('[API ROUTE DEBUG] Getting stack parameters for:', stack_name);

    if (!stack_name || !credentials) {
      return NextResponse.json(
        { success: false, error: 'Missing required data' },
        { status: 400 }
      );
    }

    // Call FastAPI backend
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);

    try {
      const response = await fetch('http://localhost:8000/get-stack-parameters', {
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
          { success: false, error: data.detail?.error || data.error || 'Failed to get stack parameters' },
          { status: response.status }
        );
      }

      console.log('[API ROUTE DEBUG] Stack parameters retrieved:', data.pricing_model);

      return NextResponse.json({
        success: true,
        pricing_model: data.pricing_model,
        pricing_dimensions: data.pricing_dimensions,
        parameters: data.parameters,
      });
    } catch (fetchError: any) {
      clearTimeout(timeoutId);
      if (fetchError.name === 'AbortError') {
        return NextResponse.json(
          { success: false, error: 'Request timed out' },
          { status: 504 }
        );
      }
      throw fetchError;
    }
  } catch (error: any) {
    console.error('Get stack parameters error:', error);
    return NextResponse.json(
      { success: false, error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
