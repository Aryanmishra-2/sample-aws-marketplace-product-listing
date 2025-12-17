import { NextRequest, NextResponse } from 'next/server';
import { invokeChat } from '@/lib/agentcore';

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

    if (!accessKeyId || !secretAccessKey) {
      return NextResponse.json(
        { success: false, error: 'AWS credentials are required' },
        { status: 400 }
      );
    }

    // Invoke AgentCore
    const result = await invokeChat(
      question,
      { accessKeyId, secretAccessKey, sessionToken },
      session_id,
      conversation_history
    );

    if (!result.success) {
      return NextResponse.json(
        { success: false, error: result.error || 'Failed to get response from agent' },
        { status: 500 }
      );
    }

    // Extract response text
    let responseText = '';
    if (typeof result.response === 'object' && result.response !== null) {
      const resp = result.response as Record<string, unknown>;
      responseText = (resp.response as string) || JSON.stringify(resp);
    } else {
      responseText = String(result.response);
    }

    return NextResponse.json({
      success: true,
      response: responseText,
      session_id: result.sessionId || session_id || `chat-${Date.now()}`,
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
