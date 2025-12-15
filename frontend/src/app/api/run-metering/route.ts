import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { product_id, credentials } = body;

    console.log('[METERING API] Running metering agent for product:', product_id);
    console.log('[METERING API] [DEBUG] Request body:', JSON.stringify({ 
      product_id, 
      has_credentials: !!credentials,
      has_access_key: !!credentials?.aws_access_key_id,
      has_secret_key: !!credentials?.aws_secret_access_key,
      has_session_token: !!credentials?.aws_session_token
    }));

    if (!product_id || !credentials) {
      console.error('[METERING API] [DEBUG] Missing required data:', { product_id: !!product_id, credentials: !!credentials });
      return NextResponse.json(
        { success: false, error: 'Missing required data' },
        { status: 400 }
      );
    }

    // Call FastAPI backend with timeout (120 seconds for metering)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000);

    try {
      const response = await fetch('http://localhost:8000/run-metering', {
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
      
      console.log('[METERING API] [DEBUG] Backend response status:', response.status);
      console.log('[METERING API] [DEBUG] Backend response data:', JSON.stringify(data, null, 2));

      if (!response.ok) {
        console.error('[METERING API] [DEBUG] Backend returned error:', data.detail?.error || data.error);
        return NextResponse.json(
          { 
            success: false, 
            error: data.detail?.error || data.error || 'Metering failed',
            steps: data.steps || []
          },
          { status: response.status }
        );
      }

      console.log('[METERING API] Metering agent completed:', data.success ? 'success' : 'failed');
      console.log('[METERING API] [DEBUG] Steps count:', data.steps?.length || 0);

      // Return the full response including steps for detailed progress display
      return NextResponse.json({
        success: data.success,
        steps: data.steps || [],
        message: data.message,
        skipped: data.skipped || false,
        reason: data.reason || null,
      });
    } catch (fetchError: any) {
      clearTimeout(timeoutId);
      if (fetchError.name === 'AbortError') {
        return NextResponse.json(
          { success: false, error: 'Metering request timed out. Please try again.', steps: [] },
          { status: 504 }
        );
      }
      throw fetchError;
    }
  } catch (error: any) {
    console.error('[METERING API] Error:', error);
    return NextResponse.json(
      { success: false, error: error.message || 'Internal server error', steps: [] },
      { status: 500 }
    );
  }
}
