// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
import { NextRequest, NextResponse } from 'next/server';
import { MarketplaceCatalogClient, ListChangeSetsCommand } from '@aws-sdk/client-marketplace-catalog';

// List recent changesets from AWS Marketplace Catalog API
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { credentials, max_results = 20 } = body;

    const accessKeyId = credentials?.accessKeyId || credentials?.aws_access_key_id;
    const secretAccessKey = credentials?.secretAccessKey || credentials?.aws_secret_access_key;
    const sessionToken = credentials?.sessionToken || credentials?.aws_session_token;

    if (!accessKeyId || !secretAccessKey) {
      return NextResponse.json({ success: false, error: 'AWS credentials required' }, { status: 400 });
    }

    const client = new MarketplaceCatalogClient({
      region: 'us-east-1',
      credentials: { accessKeyId, secretAccessKey, sessionToken },
    });

    // List recent changesets (last hour)
    const command = new ListChangeSetsCommand({
      Catalog: 'AWSMarketplace',
      MaxResults: max_results,
      Sort: {
        SortBy: 'StartTime',
        SortOrder: 'DESCENDING',
      },
    });

    const response = await client.send(command);

    const changesets = (response.ChangeSetSummaryList || []).map(cs => ({
      change_set_id: cs.ChangeSetId,
      change_set_name: cs.ChangeSetName,
      status: cs.Status,
      start_time: cs.StartTime,
      end_time: cs.EndTime,
      failure_code: cs.FailureCode,
      entity_id: cs.EntityIdList?.[0],
    }));

    return NextResponse.json({
      success: true,
      changesets,
    });
  } catch (error: unknown) {
    console.error('Error listing changesets:', error);
    const errorMessage = error instanceof Error ? error.message : 'Failed to list changesets';
    return NextResponse.json({ success: false, error: errorMessage }, { status: 500 });
  }
}
