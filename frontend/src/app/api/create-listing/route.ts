import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const requestId = Math.random().toString(36).substring(7);
  const timestamp = new Date().toISOString();
  
  console.log(`[${timestamp}] [REQUEST-${requestId}] ========================================`);
  console.log(`[${timestamp}] [REQUEST-${requestId}] NEW CREATE-LISTING REQUEST RECEIVED`);
  console.log(`[${timestamp}] [REQUEST-${requestId}] ========================================`);
  
  try {
    const body = await request.json();
    const { listing_data, credentials } = body;

    console.log(`[${timestamp}] [REQUEST-${requestId}] Product Title: ${listing_data?.title}`);
    console.log(`[${timestamp}] [REQUEST-${requestId}] Forwarding to backend...`);

    if (!listing_data || !credentials) {
      console.log(`[${timestamp}] [REQUEST-${requestId}] ERROR: Missing required data`);
      return NextResponse.json(
        { success: false, error: 'Missing required data' },
        { status: 400 }
      );
    }

    // Call FastAPI backend
    console.log(`[${timestamp}] [REQUEST-${requestId}] Calling backend at http://localhost:8000/create-listing`);
    const response = await fetch('http://localhost:8000/create-listing', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        listing_data,
        credentials,
      }),
    });

    const data = await response.json();

    console.log(`[${timestamp}] [REQUEST-${requestId}] Backend response status: ${response.status}`);
    console.log(`[${timestamp}] [REQUEST-${requestId}] Backend success: ${data.success}`);
    console.log(`[${timestamp}] [REQUEST-${requestId}] Product ID: ${data.product_id}`);

    if (!response.ok) {
      console.log(`[${timestamp}] [REQUEST-${requestId}] ERROR: Backend returned error`);
      return NextResponse.json(
        { success: false, error: data.error || 'Listing creation failed' },
        { status: response.status }
      );
    }

    console.log(`[${timestamp}] [REQUEST-${requestId}] SUCCESS - Returning to frontend`);
    console.log(`[${timestamp}] [REQUEST-${requestId}] ========================================`);
    
    return NextResponse.json({
      success: data.success !== false,
      product_id: data.product_id,
      offer_id: data.offer_id,
      published_to_limited: data.published_to_limited || false,
      message: data.message || 'Listing created successfully',
      stages: data.stages || [],
      error: data.error,
    });
  } catch (error: any) {
    console.error(`[${timestamp}] [REQUEST-${requestId}] EXCEPTION:`, error);
    return NextResponse.json(
      { success: false, error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
