import { NextRequest, NextResponse } from 'next/server';
import { invokeChat } from '@/lib/agentcore';
import { BedrockRuntimeClient, ConverseCommand } from '@aws-sdk/client-bedrock-runtime';

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

// Search AWS Documentation using the AWS Documentation Search API
async function searchAWSDocumentation(question: string): Promise<string | null> {
  try {
    // Use AWS Documentation Search API (same as MCP server uses)
    const searchUrl = 'https://docs.aws.amazon.com/search/doc-search.html';
    const params = new URLSearchParams({
      searchQuery: question,
      searchPath: 'en_us',
      this_doc_guide: '',
      doc_locale: 'en_us',
    });

    const response = await fetch(`${searchUrl}?${params}`, {
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    
    if (data.items && data.items.length > 0) {
      // Get top 3 results and format them
      const results = data.items.slice(0, 3).map((item: any) => {
        return `**${item.title}**\n${item.excerpt || ''}\nSource: ${item.url}`;
      });
      
      return results.join('\n\n---\n\n');
    }
    
    return null;
  } catch (error) {
    console.error('AWS Documentation search error:', error);
    return null;
  }
}

// Generate response using Bedrock with AWS documentation context
async function generateResponseWithContext(
  question: string,
  context: string,
  accessKeyId: string,
  secretAccessKey: string,
  sessionToken?: string,
  conversationHistory?: Array<{ role: string; content: string }>
): Promise<string> {
  const client = new BedrockRuntimeClient({
    region: 'us-east-1',
    credentials: { accessKeyId, secretAccessKey, sessionToken },
  });

  const systemPrompt = `You are an AWS Help Agent. You provide accurate information about AWS services.

IMPORTANT RULES:
1. Use the provided AWS documentation context to answer questions accurately
2. If the context contains relevant information, base your answer on it
3. If you're not sure about something, say so rather than guessing
4. Always be factual and cite AWS documentation when possible
5. For AWS Marketplace questions, focus on seller registration, SaaS listings, pricing, and integration

AWS DOCUMENTATION CONTEXT:
${context}

Provide helpful, accurate, and concise answers based on the documentation above.`;

  const messages: Array<{ role: 'user' | 'assistant'; content: Array<{ text: string }> }> = [];
  
  // Add conversation history - filter to ensure it starts with user message
  if (conversationHistory && conversationHistory.length > 0) {
    let startIdx = 0;
    for (let i = 0; i < conversationHistory.length; i++) {
      if (conversationHistory[i].role === 'user') {
        startIdx = i;
        break;
      }
    }
    
    for (let i = startIdx; i < conversationHistory.length; i++) {
      const msg = conversationHistory[i];
      if (msg.role && msg.content) {
        messages.push({
          role: msg.role === 'user' ? 'user' : 'assistant',
          content: [{ text: msg.content }],
        });
      }
    }
  }
  
  messages.push({
    role: 'user',
    content: [{ text: question }],
  });

  const command = new ConverseCommand({
    modelId: 'anthropic.claude-3-sonnet-20240229-v1:0',
    system: [{ text: systemPrompt }],
    messages,
    inferenceConfig: { maxTokens: 2048, temperature: 0.3 }, // Lower temperature for more factual responses
  });

  const response = await client.send(command);
  
  let responseText = '';
  if (response.output?.message?.content) {
    for (const block of response.output.message.content) {
      if ('text' in block) {
        responseText += block.text;
      }
    }
  }
  
  return responseText;
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

    // If no credentials, still try to help with AWS documentation
    if (!accessKeyId || !secretAccessKey) {
      // Try AWS documentation search (doesn't need credentials)
      const awsDocsContext = await searchAWSDocumentation(question);
      
      if (awsDocsContext) {
        return NextResponse.json({
          success: true,
          response: `Based on AWS documentation:\n\n${awsDocsContext}\n\nFor more detailed assistance, please provide your AWS credentials.`,
          source: 'aws_docs',
          session_id: session_id || `chat-${Date.now()}`,
        });
      }
      
      return NextResponse.json({
        success: true,
        response: "I'm here to help with AWS Marketplace and AWS services! You can ask me about:\n\n• Seller registration process\n• SaaS integration\n• Creating product listings\n• Pricing models\n• AWS services\n\nPlease provide your AWS credentials for more detailed, personalized assistance.",
        source: 'fallback',
        session_id: session_id || `chat-${Date.now()}`,
      });
    }

    // Step 2: Search AWS Documentation for context
    const awsDocsContext = await searchAWSDocumentation(question);
    
    if (awsDocsContext) {
      // Generate response using Bedrock with AWS documentation context
      const response = await generateResponseWithContext(
        question,
        awsDocsContext,
        accessKeyId,
        secretAccessKey,
        sessionToken,
        conversation_history
      );
      
      return NextResponse.json({
        success: true,
        response,
        source: 'aws_docs_enhanced',
        session_id: session_id || `chat-${Date.now()}`,
      });
    }

    // Step 3: Try AgentCore for Marketplace-specific questions
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

        if (responseText && responseText.length > 50) {
          return NextResponse.json({
            success: true,
            response: responseText,
            source: 'agentcore',
            session_id: result.sessionId || session_id || `chat-${Date.now()}`,
          });
        }
      }
    } catch (agentError) {
      console.log('AgentCore not available:', agentError);
    }

    // Step 4: Fallback to direct Bedrock call
    const fallbackResponse = await generateResponseWithContext(
      question,
      'No specific documentation found. Provide general AWS guidance based on your knowledge, but be clear about any limitations.',
      accessKeyId,
      secretAccessKey,
      sessionToken,
      conversation_history
    );

    return NextResponse.json({
      success: true,
      response: fallbackResponse,
      source: 'bedrock_direct',
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
