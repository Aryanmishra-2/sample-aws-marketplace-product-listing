// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // OPTIMIZATION: Ultra-lightweight health check for App Runner
    // Returns immediately without any heavy operations or imports
    const response = NextResponse.json({ 
      status: 'healthy',
      timestamp: Date.now(),
      service: 'aws-marketplace-seller-portal',
      uptime: process.uptime(),
      memory: process.memoryUsage().heapUsed
    }, { 
      status: 200,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Content-Type': 'application/json',
      }
    });
    
    return response;
  } catch (error) {
    // Fallback response if anything fails
    return new Response(JSON.stringify({
      status: 'error',
      timestamp: Date.now(),
      error: 'Health check failed'
    }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
      }
    });
  }
}