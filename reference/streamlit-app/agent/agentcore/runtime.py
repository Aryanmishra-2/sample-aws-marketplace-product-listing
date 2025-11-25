"""
Agentcore Runtime - Agent execution engine
Orchestrates agent processing with model invocation and tool execution
"""

from typing import Dict, Any, List, Optional
import time
from botocore.exceptions import ClientError


class AgentRuntime:
    """
    Agentcore Runtime manages agent execution flow
    
    Responsibilities:
    - Invoke foundation model via Bedrock
    - Coordinate tool execution through Gateway
    - Manage conversation flow
    - Handle multi-turn interactions
    """
    
    def __init__(
        self,
        model_id: str,
        bedrock_client,
        gateway,
        memory,
        system_prompt: str,
        max_iterations: int = 10,
        min_request_interval: float = 1.0
    ):
        """
        Initialize AgentRuntime
        
        Args:
            model_id: Bedrock model identifier
            bedrock_client: Boto3 Bedrock client
            gateway: Agentcore Gateway for tool routing
            memory: Agentcore Memory for conversation persistence
            system_prompt: System instructions for the agent
            max_iterations: Maximum tool execution iterations
            min_request_interval: Minimum seconds between API calls (rate limiting)
        """
        self.model_id = model_id
        self.bedrock_client = bedrock_client
        self.gateway = gateway
        self.memory = memory
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
        self.min_request_interval = min_request_interval
        self.last_request_time = 0
    
    def process(
        self,
        message: str,
        session_id: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        system_prompt_override: Optional[str] = None
    ) -> str:
        """
        Process a user message through the agent runtime
        
        Args:
            message: User input message
            session_id: Session identifier
            conversation_history: Previous conversation messages
            system_prompt_override: Optional system prompt to use instead of default
            
        Returns:
            Agent response text
        """
        # Use override if provided, otherwise use default
        system_prompt = system_prompt_override if system_prompt_override else self.system_prompt
        
        # Build conversation context
        messages = conversation_history or []
        messages.append({
            "role": "user",
            "content": [{"text": message}]
        })
        
        # Execute agent loop with tool calling
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            
            # Invoke model
            response = self._invoke_model(messages, system_prompt)
            
            # Check stop reason
            stop_reason = response.get('stopReason')
            output_message = response['output']['message']
            messages.append(output_message)
            
            # If no tool use, return response
            if stop_reason != 'tool_use':
                return self._extract_text_response(output_message)
            
            # Execute tools via Gateway
            tool_results = self._execute_tools(output_message)
            
            # Add tool results to conversation
            messages.append({
                "role": "user",
                "content": tool_results
            })
        
        # Provide helpful error message with context
        return (
            "I've reached the maximum number of tool execution steps. "
            "This usually means the task is complex or I got stuck in a loop. "
            "Please try:\n"
            "1. Breaking your request into smaller steps\n"
            "2. Starting a new conversation\n"
            "3. Being more specific about what you need\n\n"
            f"I completed {iteration} tool execution cycles."
        )
    
    def _invoke_model(self, messages: List[Dict[str, Any]], system_prompt: str) -> Dict[str, Any]:
        """Invoke Bedrock model with conversation and retry logic"""
        # Rate limiting: ensure minimum interval between requests
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        max_retries = 5
        base_delay = 2  # Start with 2 seconds
        
        for attempt in range(max_retries):
            try:
                self.last_request_time = time.time()
                return self.bedrock_client.converse(
                    modelId=self.model_id,
                    messages=messages,
                    system=[{"text": system_prompt}],
                    toolConfig={
                        "tools": self.gateway.get_tool_definitions()
                    }
                )
            except ClientError as e:
                error_code = e.response['Error']['Code']
                
                if error_code == 'ThrottlingException':
                    if attempt < max_retries - 1:
                        # Exponential backoff: 2s, 4s, 8s, 16s, 32s
                        delay = base_delay * (2 ** attempt)
                        print(f"⏳ Rate limit hit. Waiting {delay}s before retry {attempt + 1}/{max_retries}...")
                        time.sleep(delay)
                        continue
                    else:
                        raise Exception(f"Rate limit exceeded after {max_retries} retries. Please wait a few minutes.")
                else:
                    # Re-raise other errors immediately
                    raise
            except Exception:
                # Re-raise unexpected errors
                raise
        
        # Should never reach here due to raises above, but for type safety
        raise Exception("Failed to invoke model after all retries")
    
    def _execute_tools(self, message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute tools requested by the model"""
        tool_results = []
        
        for content in message.get('content', []):
            if 'toolUse' in content:
                tool_use = content['toolUse']
                
                # Route through Gateway
                result = self.gateway.execute_action(
                    action_name=tool_use['name'],
                    parameters=tool_use['input']
                )
                
                tool_results.append({
                    "toolResult": {
                        "toolUseId": tool_use['toolUseId'],
                        "content": [{"json": result}]
                    }
                })
        
        return tool_results
    
    def _extract_text_response(self, message: Dict[str, Any]) -> str:
        """Extract text content from model response"""
        for content in message.get('content', []):
            if 'text' in content:
                return content['text']
        return ""
