// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
import { NextRequest, NextResponse } from 'next/server';
import { invokeChat } from '@/lib/agentcore';

// Local knowledge base responses for quick answers about this app
const LOCAL_KB: Record<string, string> = {
  register: "To register as an AWS Marketplace seller:\n\n1. Validate your AWS credentials on the home page\n2. If you see 'NOT_REGISTERED' status, click 'Create Business Profile'\n3. Complete tax information (W-9 or W-8 form)\n4. Set up payment information\n5. Submit for AWS review (2-3 business days)\n\nOnce approved, you can create product listings!",
  saas: "SaaS Integration connects your SaaS product to AWS Marketplace:\n\n• Deploys serverless infrastructure (DynamoDB, Lambda, API Gateway)\n• Handles subscription management\n• Processes metering and billing\n• Provides fulfillment endpoint\n\nFor LIMITED products, click 'Configure SaaS' to deploy the integration automatically.",
  listing: "Creating a product listing is easy:\n\n1. Click 'Create New Product' from the seller registration page\n2. Enter product information (name, description, URLs)\n3. AI analyzes your product and generates content\n4. Review and edit the suggestions\n5. Submit to create the listing\n\nThe AI handles all the marketplace-specific formatting!",
  pricing: "AWS Marketplace supports multiple pricing models:\n\n• Usage-based: Pay per use (hourly, API calls, etc.)\n• Contract-based: Fixed price for a term\n• Contract with consumption: Hybrid model\n• Free trial: Let customers try before buying\n\nChoose the model that fits your business during listing creation.",
};

// Check if question matches local KB
function getLocalKBResponse(question: string): string | null {
  const lowerQuestion = question.toLowerCase();
  
  if (lowerQuestion.includes('register') && lowerQuestion.includes('seller')) {
    return LOCAL_KB.register;
  }
  if (lowerQuestion.includes('saas') && lowerQuestion.includes('integration')) {
    return LOCAL_KB.saas;
  }
  if ((lowerQuestion.includes('create') || lowerQuestion.includes('how')) && lowerQuestion.includes('listing')) {
    return LOCAL_KB.listing;
  }
  if (lowerQuestion.includes('pricing') && lowerQuestion.includes('model')) {
    return LOCAL_KB.pricing;
  }
  
  return null;
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { question, credentials, session_id, conversation_history } = body;

    if (!question) {
      return NextResponse.json(
        { success: false, error: 'Question is required' },
        { status: 400 }
      );
    }

    // Extract credentials (support both camelCase and snake_case)
    const accessKeyId = credentials?.accessKeyId || credentials?.aws_access_key_id;
    const secretAccessKey = credentials?.secretAccessKey || credentials?.aws_secret_access_key;
    const sessionToken = credentials?.sessionToken || credentials?.aws_session_token;

    // Step 1: Check local knowledge base first (for app-specific questions)
    const localResponse = getLocalKBResponse(question);
    if (localResponse) {
      return NextResponse.json({
        success: true,
        response: localResponse,
        source: 'local_kb',
        session_id: session_id || `chat-${Date.now()}`,
      });
    }

    if (!accessKeyId || !secretAccessKey) {
      return NextResponse.json({
        success: true,
        response: "I'm here to help with AWS Marketplace and AWS services! You can ask me about:\n\n• Seller registration process\n• SaaS integration\n• Creating product listings\n• Pricing models\n• AWS services\n\nPlease provide your AWS credentials for more detailed, personalized assistance.",
        source: 'fallback',
        session_id: session_id || `chat-${Date.now()}`,
      });
    }

    // Step 2: Use AgentCore for all chat queries (routes through backend agent which uses Amazon Bedrock)
    try {
      const result = await invokeChat(
        question,
        { accessKeyId, secretAccessKey, sessionToken },
        session_id,
        conversation_history
      );

      if (result.success) {
        let responseText = '';
        if (typeof result.response === 'object' && result.response !== null) {
          const resp = result.response as Record<string, unknown>;
          responseText = (resp.response as string) || JSON.stringify(resp);
        } else {
          responseText = String(result.response);
        }

        if (responseText && responseText.length > 10) {
          return NextResponse.json({
            success: true,
            response: responseText,
            source: 'agentcore',
            session_id: result.sessionId || session_id || `chat-${Date.now()}`,
          });
        }
      }
    } catch (agentError) {
      console.error('AgentCore chat error:', agentError);
    }

    // Step 3: Fallback - AgentCore unavailable
    return NextResponse.json({
      success: false,
      error: 'Chat service is temporarily unavailable. The AgentCore backend may still be starting up. Please try again in a few minutes.',
      session_id: session_id || `chat-${Date.now()}`,
    });

  } catch (error: unknown) {
    console.error('Chat API error:', error);
    const errorMessage = error instanceof Error ? error.message : 'Failed to get response';
    return NextResponse.json(
      { success: false, error: errorMessage },
      { status: 500 }
    );
  }
}
