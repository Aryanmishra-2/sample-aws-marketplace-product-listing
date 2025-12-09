import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { product_id, email, stack_name, region, credentials, pricing_model } = body;

    console.log('[API ROUTE DEBUG] Received pricing_model from frontend:', pricing_model);

    if (!product_id || !email || !stack_name || !credentials) {
      return NextResponse.json(
        { success: false, error: 'Missing required data' },
        { status: 400 }
      );
    }

    if (!pricing_model) {
      console.log('[API ROUTE ERROR] Pricing model is missing!');
      return NextResponse.json(
        { success: false, error: 'Pricing model is required' },
        { status: 400 }
      );
    }

    // Call FastAPI backend with timeout (60 seconds for initial deploy)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);

    try {
      const payloadToBackend = {
        product_id,
        email,
        stack_name,
        region: region || 'us-east-1',
        pricing_model,
        credentials,
      };
      
      console.log('[API ROUTE DEBUG] Sending to backend with pricing_model:', pricing_model);
      console.log('[API ROUTE DEBUG] Full payload to backend:', JSON.stringify(payloadToBackend, null, 2));
      console.log('[API ROUTE DEBUG] Attempting to connect to: http://localhost:8000/deploy-saas');
      
      const response = await fetch('http://localhost:8000/deploy-saas', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payloadToBackend),
        signal: controller.signal,
      });
      
      console.log('[API ROUTE DEBUG] Backend response status:', response.status);

      clearTimeout(timeoutId);
      const data = await response.json();

      if (!response.ok) {
        return NextResponse.json(
          { success: false, error: data.detail?.error || data.error || 'Deployment failed' },
          { status: response.status }
        );
      }

      return NextResponse.json({
        success: true,
        stack_id: data.stack_id,
        stack_name: data.stack_name,
        message: data.message || 'SaaS integration deployment initiated',
      });
    } catch (fetchError: any) {
      clearTimeout(timeoutId);
      if (fetchError.name === 'AbortError') {
        return NextResponse.json(
          { success: false, error: 'Deployment request timed out. Please try again.' },
          { status: 504 }
        );
      }
      throw fetchError;
    }
  } catch (error: any) {
    console.error('Deploy SaaS error:', error);
    return NextResponse.json(
      { success: false, error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
