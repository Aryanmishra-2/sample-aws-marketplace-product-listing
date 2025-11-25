"""
Traced Runtime - Runtime with execution tracing for UI
"""

from .runtime import AgentRuntime
from typing import Dict, Any, List, Optional, Callable


class TracedRuntime(AgentRuntime):
    """
    AgentRuntime with execution tracing
    Emits events for UI visualization
    """
    
    def __init__(
        self,
        model_id: str,
        bedrock_client,
        gateway,
        memory,
        system_prompt: str,
        max_iterations: int = 10,
        min_request_interval: float = 1.0,
        trace_callback: Optional[Callable] = None
    ):
        """
        Initialize TracedRuntime
        
        Args:
            trace_callback: Function to call with trace events
                           Signature: callback(event_type: str, data: dict)
        """
        super().__init__(
            model_id=model_id,
            bedrock_client=bedrock_client,
            gateway=gateway,
            memory=memory,
            system_prompt=system_prompt,
            max_iterations=max_iterations,
            min_request_interval=min_request_interval
        )
        self.trace_callback = trace_callback or (lambda t, d: None)
    
    def _emit_trace(self, event_type: str, data: dict):
        """Emit a trace event"""
        try:
            self.trace_callback(event_type, data)
        except Exception:
            pass  # Don't let trace errors break execution
    
    def _invoke_model(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Invoke model with tracing"""
        self._emit_trace("model_call_start", {
            "model_id": self.model_id,
            "message_count": len(messages)
        })
        
        try:
            result = super()._invoke_model(messages)
            self._emit_trace("model_call_success", {
                "stop_reason": result.get('stopReason')
            })
            return result
        except Exception as e:
            self._emit_trace("model_call_error", {
                "error": str(e)
            })
            raise
    
    def _execute_tools(self, message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute tools with tracing"""
        tool_results = []
        
        for content in message.get('content', []):
            if 'toolUse' in content:
                tool_use = content['toolUse']
                tool_name = tool_use['name']
                tool_input = tool_use['input']
                
                self._emit_trace("tool_call_start", {
                    "tool_name": tool_name,
                    "parameters": tool_input
                })
                
                try:
                    # Route through Gateway
                    result = self.gateway.execute_action(
                        action_name=tool_name,
                        parameters=tool_input
                    )
                    
                    self._emit_trace("tool_call_success", {
                        "tool_name": tool_name,
                        "result": result
                    })
                    
                    tool_results.append({
                        "toolResult": {
                            "toolUseId": tool_use['toolUseId'],
                            "content": [{"json": result}]
                        }
                    })
                except Exception as e:
                    self._emit_trace("tool_call_error", {
                        "tool_name": tool_name,
                        "error": str(e)
                    })
                    raise
        
        return tool_results
