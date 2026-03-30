// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
import { NextRequest, NextResponse } from 'next/server';
import { STSClient, GetCallerIdentityCommand } from '@aws-sdk/client-sts';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Support both nested and flat credential structures
    const credentials = body.credentials || body;
    const { aws_access_key_id, aws_secret_access_key, aws_session_token } = credentials;

    if (!aws_access_key_id || !aws_secret_access_key) {
      return NextResponse.json(
        { success: false, error: 'Missing required credentials' },
        { status: 400 }
      );
    }

    // Use AWS SDK directly to validate credentials
    const stsClient = new STSClient({
      region: 'us-east-1',
      credentials: {
        accessKeyId: aws_access_key_id,
        secretAccessKey: aws_secret_access_key,
        sessionToken: aws_session_token,
      },
    });

    const identity = await stsClient.send(new GetCallerIdentityCommand({}));
    
    const accountId = identity.Account || '';
    const userArn = identity.Arn || '';
    const userId = identity.UserId || '';
    
    // Extract user name from ARN
    const arnParts = userArn.split('/');
    const userName = arnParts[arnParts.length - 1] || userId;

    return NextResponse.json({
      success: true,
      account_id: accountId,
      user_arn: userArn,
      user_type: userArn.includes(':assumed-role/') ? 'assumed_role' : 'iam_user',
      user_name: userName,
      organization: 'AWS Account ' + accountId,
      session_id: 'session-' + Date.now(),
      permissions_verified: false,
      permissions_note: 'STS identity verified. Specific IAM permissions have not been checked.',
      can_proceed: true,
    });
  } catch (error: any) {
    console.error('Validate credentials error:', error);
    return NextResponse.json(
      { success: false, error: error.message || 'Invalid credentials' },
      { status: 401 }
    );
  }
}
