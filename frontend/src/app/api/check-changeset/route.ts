// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
import { NextRequest, NextResponse } from 'next/server';
import { MarketplaceCatalogClient, DescribeChangeSetCommand } from '@aws-sdk/client-marketplace-catalog';

// Check changeset status directly via AWS Marketplace Catalog API
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { change_set_id, credentials } = body;

    if (!change_set_id) {
      return NextResponse.json(
        { success: false, error: 'change_set_id is required' },
        { status: 400 }
      );
    }

    const accessKeyId = credentials?.accessKeyId || credentials?.aws_access_key_id;
    const secretAccessKey = credentials?.secretAccessKey || credentials?.aws_secret_access_key;
    const sessionToken = credentials?.sessionToken || credentials?.aws_session_token;

    if (!accessKeyId || !secretAccessKey) {
      return NextResponse.json(
        { success: false, error: 'AWS credentials are required' },
        { status: 400 }
      );
    }

    const client = new MarketplaceCatalogClient({
      region: 'us-east-1',
      credentials: {
        accessKeyId,
        secretAccessKey,
        sessionToken,
      },
    });

    const command = new DescribeChangeSetCommand({
      Catalog: 'AWSMarketplace',
      ChangeSetId: change_set_id,
    });

    const response = await client.send(command);

    // Extract product_id and offer_id from changeset
    let product_id = null;
    let offer_id = null;
    
    if (response.ChangeSet) {
      for (const change of response.ChangeSet) {
        const identifier = change.Entity?.Identifier;
        if (identifier) {
          // Strip revision suffix (e.g., "prod-xxx@1" -> "prod-xxx")
          const cleanId = identifier.split('@')[0];
          if (change.ChangeType === 'CreateProduct' || identifier.startsWith('prod-')) {
            product_id = cleanId;
          } else if (change.ChangeType === 'CreateOffer' || identifier.startsWith('offer-')) {
            offer_id = cleanId;
          }
        }
      }
    }

    // Get error details if failed
    let errorDetails: string[] = [];
    if (response.ChangeSet) {
      for (const change of response.ChangeSet) {
        if (change.ErrorDetailList && change.ErrorDetailList.length > 0) {
          for (const err of change.ErrorDetailList) {
            errorDetails.push(err.ErrorMessage || 'Unknown error');
          }
        }
      }
    }

    return NextResponse.json({
      success: true,
      status: response.Status,
      change_set_id: response.ChangeSetId,
      change_set_name: response.ChangeSetName,
      product_id,
      offer_id,
      failure_code: response.FailureCode,
      failure_description: response.FailureDescription || errorDetails.join('; '),
      error_details: errorDetails,
      start_time: response.StartTime,
      end_time: response.EndTime,
    });
  } catch (error: unknown) {
    console.error('Error checking changeset:', error);
    const errorMessage = error instanceof Error ? error.message : 'Failed to check changeset';
    return NextResponse.json(
      { success: false, error: errorMessage },
      { status: 500 }
    );
  }
}
