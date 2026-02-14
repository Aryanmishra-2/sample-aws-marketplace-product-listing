/**
 * AgentCore Runtime Client for invoking agents deployed to Amazon Bedrock AgentCore
 * 
 * AgentCore uses HTTP POST to /invocations endpoint with SigV4 authentication,
 * NOT the BedrockAgentRuntimeClient (which is for standard Bedrock Agents).
 */

import { SignatureV4 } from '@smithy/signature-v4';
import { Sha256 } from '@aws-crypto/sha256-js';
import { HttpRequest } from '@smithy/protocol-http';

// AgentCore configuration
// AGENTCORE_RUNTIME_ARN is injected via ECS task definition environment variable during deployment
const RUNTIME_ARN = process.env.AGENTCORE_RUNTIME_ARN || '';
const REGION = process.env.AWS_REGION || 'us-east-1';

// Extract runtime ID from ARN
function getRuntimeId(arn: string): string {
  const parts = arn.split('/');
  return parts[parts.length - 1];
}

// Get the AgentCore data plane endpoint
function getDataPlaneEndpoint(region: string): string {
  return `https://bedrock-agentcore.${region}.amazonaws.com`;
}

export interface AgentCredentials {
  accessKeyId: string;
  secretAccessKey: string;
  sessionToken?: string;
}

export interface AgentResponse {
  success: boolean;
  response: string | Record<string, unknown>;
  sessionId?: string;
  error?: string;
}

export interface AgentPayload {
  action: 'chat' | 'workflow' | 'metering' | 'visibility' | 'buyer_experience' | 'analyze_product' | 'health';
  credentials?: {
    accessKeyId: string;
    secretAccessKey: string;
    sessionToken?: string;
  };
  prompt?: string;
  question?: string;
  product_id?: string;
  product_context?: Record<string, unknown>;
  lambda_function_name?: string;
  sub_action?: string;
  session_id?: string;
  conversation_history?: Array<{ role: string; content: string }>;
}

/**
 * Invoke the AgentCore Runtime agent
 */
export async function invokeAgentCore(
  payload: AgentPayload,
  credentials: AgentCredentials,
  sessionId?: string
): Promise<AgentResponse> {
  try {
    if (!RUNTIME_ARN) {
      return {
        success: false,
        response: '',
        error: 'AGENTCORE_RUNTIME_ARN environment variable is not configured. Backend may not be deployed.',
      };
    }

    const runtimeId = getRuntimeId(RUNTIME_ARN);
    const endpoint = getDataPlaneEndpoint(REGION);
    const url = `${endpoint}/runtimes/${encodeURIComponent(RUNTIME_ARN)}/invocations`;
    
    // Add credentials to payload if not already present
    if (!payload.credentials && credentials) {
      payload.credentials = {
        accessKeyId: credentials.accessKeyId,
        secretAccessKey: credentials.secretAccessKey,
        sessionToken: credentials.sessionToken,
      };
    }
    
    if (sessionId) {
      payload.session_id = sessionId;
    }
    
    const body = JSON.stringify(payload);
    
    // Create the HTTP request
    const request = new HttpRequest({
      method: 'POST',
      protocol: 'https:',
      hostname: `bedrock-agentcore.${REGION}.amazonaws.com`,
      path: `/runtimes/${encodeURIComponent(RUNTIME_ARN)}/invocations`,
      headers: {
        'Content-Type': 'application/json',
        'Host': `bedrock-agentcore.${REGION}.amazonaws.com`,
      },
      body: body,
    });
    
    // Sign the request with SigV4
    const signer = new SignatureV4({
      credentials: {
        accessKeyId: credentials.accessKeyId,
        secretAccessKey: credentials.secretAccessKey,
        sessionToken: credentials.sessionToken,
      },
      region: REGION,
      service: 'bedrock-agentcore',
      sha256: Sha256,
    });
    
    const signedRequest = await signer.sign(request);
    
    // Make the request
    const response = await fetch(url, {
      method: 'POST',
      headers: signedRequest.headers as Record<string, string>,
      body: body,
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('[AgentCore] Error response:', errorText);
      return {
        success: false,
        response: '',
        error: `AgentCore request failed: ${response.status} ${errorText}`,
      };
    }
    
    const result = await response.json();
    
    return {
      success: true,
      response: result,
      sessionId: sessionId,
    };
  } catch (error: unknown) {
    console.error('[AgentCore] Error invoking agent:', error);
    const errorMessage = error instanceof Error ? error.message : 'Failed to invoke agent';
    return {
      success: false,
      response: '',
      error: errorMessage,
    };
  }
}

/**
 * Invoke the chat action on AgentCore
 */
export async function invokeChat(
  question: string,
  credentials: AgentCredentials,
  sessionId?: string,
  conversationHistory?: Array<{ role: string; content: string }>
): Promise<AgentResponse> {
  return invokeAgentCore(
    {
      action: 'chat',
      prompt: question,
      conversation_history: conversationHistory,
    },
    credentials,
    sessionId
  );
}

/**
 * Invoke the workflow action on AgentCore
 */
export async function invokeWorkflow(
  credentials: AgentCredentials,
  productId?: string,
  lambdaFunctionName?: string
): Promise<AgentResponse> {
  return invokeAgentCore(
    {
      action: 'workflow',
      product_id: productId,
      lambda_function_name: lambdaFunctionName,
    },
    credentials
  );
}

/**
 * Invoke the metering action on AgentCore
 */
export async function invokeMetering(
  credentials: AgentCredentials,
  subAction: 'check_and_add' | 'trigger_lambda' | 'insert_test_customer' = 'check_and_add',
  lambdaFunctionName?: string
): Promise<AgentResponse> {
  return invokeAgentCore(
    {
      action: 'metering',
      sub_action: subAction,
      lambda_function_name: lambdaFunctionName,
    },
    credentials
  );
}

/**
 * Invoke the analyze_product action on AgentCore
 */
export async function invokeAnalyzeProduct(
  productContext: Record<string, unknown>,
  credentials: AgentCredentials
): Promise<AgentResponse> {
  return invokeAgentCore(
    {
      action: 'analyze_product',
      product_context: productContext,
    },
    credentials
  );
}

/**
 * Parse JSON from agent response
 */
export function parseAgentJsonResponse<T>(response: string | Record<string, unknown>): T | null {
  try {
    if (typeof response === 'object') {
      return response as T;
    }
    
    // Try to find JSON in the response
    const jsonMatch = response.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]) as T;
    }
    
    // Try to find JSON array
    const arrayMatch = response.match(/\[[\s\S]*\]/);
    if (arrayMatch) {
      return JSON.parse(arrayMatch[0]) as T;
    }
    
    return null;
  } catch {
    return null;
  }
}
