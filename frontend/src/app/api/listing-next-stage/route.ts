// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
import { NextRequest, NextResponse } from 'next/server';
import { invokeAgentCore } from '@/lib/agentcore';

// Run the next stage of listing creation
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { stage, product_id, offer_id, listing_data, credentials } = body;

    const accessKeyId = credentials?.accessKeyId || credentials?.aws_access_key_id;
    const secretAccessKey = credentials?.secretAccessKey || credentials?.aws_secret_access_key;
    const sessionToken = credentials?.sessionToken || credentials?.aws_session_token;

    if (!accessKeyId || !secretAccessKey) {
      return NextResponse.json({ success: false, error: 'AWS credentials required' }, { status: 400 });
    }

    console.log(`[listing-next-stage] Running stage: ${stage}`);

    let action = '';
    let payload: Record<string, unknown> = {};

    switch (stage) {
      case 'fulfillment':
        if (!listing_data.fulfillment_url) {
          return NextResponse.json({ success: true, skipped: true, message: 'No fulfillment URL' });
        }
        action = 'listing_update_info';
        payload = {
          product_id,
          fulfillment_url: listing_data.fulfillment_url,
        };
        break;

      case 'pricing':
        action = 'listing_add_pricing';
        payload = {
          product_id,
          offer_id,
          pricing_model: listing_data.pricing_model || 'usage',
          dimensions: listing_data.pricing_dimensions || [],
        };
        break;

      case 'refund':
        action = 'listing_update_support';
        payload = {
          offer_id,
          refund_policy: listing_data.refund_policy || 'No refunds after 30 days.',
        };
        break;

      case 'eula':
        action = 'listing_update_legal';
        payload = {
          offer_id,
          eula_type: listing_data.eula_type || 'STANDARD',
        };
        break;

      case 'availability':
        action = 'listing_update_availability';
        payload = {
          offer_id,
          availability_type: 'all',
        };
        break;

      case 'publish':
        action = 'listing_release_to_limited';
        payload = {
          product_id,
          offer_id,
          offer_name: listing_data.offer_name || `${listing_data.title} - Public Offer`,
          offer_description: listing_data.offer_description || `Public offer for ${listing_data.title}`,
        };
        break;

      default:
        return NextResponse.json({ success: false, error: `Unknown stage: ${stage}` }, { status: 400 });
    }

    const result = await invokeAgentCore(
      { action, ...payload } as any,
      { accessKeyId, secretAccessKey, sessionToken }
    );

    console.log(`[listing-next-stage] ${stage} result:`, JSON.stringify(result, null, 2));

    if (!result.success) {
      return NextResponse.json({
        success: false,
        error: result.error || `Failed to run ${stage}`,
      }, { status: 500 });
    }

    const response = result.response as Record<string, unknown>;

    return NextResponse.json({
      success: true,
      change_set_id: response.change_set_id,
      message: response.message,
    });
  } catch (error: unknown) {
    console.error('Error in listing-next-stage:', error);
    const errorMessage = error instanceof Error ? error.message : 'Failed to run stage';
    return NextResponse.json({ success: false, error: errorMessage }, { status: 500 });
  }
}
