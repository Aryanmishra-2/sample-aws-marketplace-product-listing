import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { listing_data, credentials } = body;

    if (!listing_data || !credentials) {
      return NextResponse.json(
        { success: false, error: 'Missing required data' },
        { status: 400 }
      );
    }

    // Call FastAPI backend
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

    if (!response.ok) {
      return NextResponse.json(
        { success: false, error: data.error || 'Listing creation failed' },
        { status: response.status }
      );
    }

    return NextResponse.json({
      success: true,
      product_id: data.product_id,
      offer_id: data.offer_id,
      published_to_limited: data.published_to_limited || false,
      message: data.message || 'Listing created successfully',
    });
  } catch (error: any) {
    console.error('Create listing error:', error);
    return NextResponse.json(
      { success: false, error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
