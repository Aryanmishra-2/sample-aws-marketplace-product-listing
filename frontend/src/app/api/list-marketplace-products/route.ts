'use server';

import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    const response = await fetch('http://localhost:8000/list-marketplace-products', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error: any) {
    console.error('List marketplace products API error:', error);
    return NextResponse.json(
      { success: false, error: error.message || 'Failed to list marketplace products' },
      { status: 500 }
    );
  }
}
