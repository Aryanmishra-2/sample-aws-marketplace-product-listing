"""
BedrockAgentCore Runtime Entrypoint for Strands Marketplace Agent
Enables serverless deployment via agentcore CLI
"""

import os
import json
from strands import Agent, tool

# Import orchestrator and tools
from agent.orchestrator import ListingOrchestrator
from agent.tools.listing_tools import ListingTools

# Initialize BedrockAgentCore app
app = BedrockAgentCoreApp()

# Initialize orchestrator and AWS tools
listing_tools = ListingTools(region=os.environ.get('AWS_REGION', 'us-east-1'))
orchestrator = ListingOrchestrator(listing_tools=listing_tools)


# Define tools for Strands agent
@tool
def store_field_data(field_name: str, field_value: str) -> dict:
    """
    Store a field value for the current stage.
    Call this IMMEDIATELY when user provides any information.
    
    Args:
        field_name: Name of the field to store
        field_value: Value to store for the field
    
    Returns:
        Dictionary with success status and remaining fields
    """
    orchestrator.set_stage_data(field_name, field_value)
    current_agent = orchestrator.get_current_agent()
    
    return {
        "success": True,
        "message": f"Stored {field_name}",
        "fields_collected": list(current_agent.stage_data.keys()),
        "fields_remaining": [f for f in current_agent.get_required_fields() 
                           if f not in current_agent.stage_data],
        "is_stage_complete": current_agent.is_stage_complete()
    }


@tool
def get_collected_data() -> dict:
    """
    Get all data collected for current stage.
    Use this to check what information has already been collected.
    
    Returns:
        Dictionary with stage info and collected data
    """
    current_agent = orchestrator.get_current_agent()
    
    return {
        "stage_name": current_agent.stage_name,
        "stage_number": current_agent.stage_number,
        "required_fields": current_agent.get_required_fields(),
        "optional_fields": current_agent.get_optional_fields(),
        "collected_data": current_agent.stage_data,
        "fields_remaining": [f for f in current_agent.get_required_fields() 
                           if f not in current_agent.stage_data],
        "is_complete": current_agent.is_stage_complete()
    }


@tool
def complete_stage() -> dict:
    """
    Mark current stage as complete and execute AWS Marketplace API calls.
    Call this ONLY when all required fields for the current stage are collected.
    
    Returns:
        Dictionary with completion status, API results, and transition info
    """
    if orchestrator.check_stage_completion():
        result = orchestrator.complete_current_stage()
        return result
    else:
        current_agent = orchestrator.get_current_agent()
        required = current_agent.get_required_fields()
        collected = list(current_agent.stage_data.keys())
        missing = [f for f in required if f not in collected]
        return {
            "success": False,
            "message": "Stage not complete - missing required fields",
            "missing_fields": missing,
            "required_fields": required,
            "collected_fields": collected
        }


@tool
def get_stage_info() -> dict:
    """
    Get information about the current workflow stage.
    Use this to understand what stage you're in and what's needed.
    
    Returns:
        Dictionary with stage details and progress
    """
    stage_info = orchestrator.get_stage_info()
    return {
        **stage_info,
        "progress_percentage": orchestrator.get_progress_percentage(),
        "completed_stages": [s.value for s in orchestrator.completed_stages]
    }


@tool
def get_workflow_summary() -> dict:
    """
    Get a summary of the entire workflow progress.
    
    Returns:
        Dictionary with workflow summary
    """
    return {
        "summary": orchestrator.get_workflow_summary(),
        "current_stage": orchestrator.current_stage.value,
        "progress": orchestrator.get_progress_percentage(),
        "product_id": orchestrator.product_id,
        "offer_id": orchestrator.offer_id
    }


# Create Strands agent with all tools
agent = Agent(
    tools=[
        store_field_data,
        get_collected_data,
        complete_stage,
        get_stage_info,
        get_workflow_summary
    ],
    model=os.environ.get('MODEL_ID', 'us.anthropic.claude-3-7-sonnet-20250219-v1:0')
)


@app.entrypoint
def agent_invocation(payload, context):
    """
    Handler for agent invocation via BedrockAgentCore Runtime
    
    Args:
        payload: Input payload with 'prompt' key
        context: AgentCore context with session info
        
    Returns:
        Dictionary with agent response
    """
    try:
        # Extract user message
        user_message = payload.get("prompt", "")
        
        if not user_message:
            return {
                "error": "No prompt provided",
                "message": "Please provide a 'prompt' key in the payload"
            }
        
        # Get current stage context
        stage_info = orchestrator.get_stage_info()
        current_agent = orchestrator.get_current_agent()
        
        # Build collected data summary
        collected_fields = list(current_agent.stage_data.keys())
        missing_fields = [f for f in stage_info['required_fields'] if f not in collected_fields]
        
        # Build context-aware prompt
        context_prompt = f"""You are an AWS Marketplace listing assistant in Stage {stage_info['stage_number']}/8: {stage_info['stage_name']}.

COLLECTED DATA SO FAR:
{json.dumps(current_agent.stage_data, indent=2) if current_agent.stage_data else "None yet"}

STILL NEEDED (Required):
{', '.join(missing_fields) if missing_fields else 'All required fields collected!'}

REQUIRED FIELDS FOR THIS STAGE:
{json.dumps(stage_info['required_fields'], indent=2)}

YOUR WORKFLOW:
1. Check what data is already collected (see "COLLECTED DATA SO FAR" above)
2. Ask for ONE missing required field at a time
3. When user provides information, IMMEDIATELY call store_field_data tool to save it
4. After storing, ask for the next missing field
5. When ALL required fields are collected, call complete_stage tool
6. Be conversational and helpful

TOOLS YOU MUST USE:
- store_field_data(field_name, field_value) - Call this IMMEDIATELY when user provides any information
- get_collected_data() - Check what's been collected if unsure
- complete_stage() - Call this when all required fields are collected
- get_stage_info() - Get current stage information

CRITICAL RULES:
- DO NOT ask for information that's already in "COLLECTED DATA SO FAR"
- ALWAYS call store_field_data when user provides information
- DO NOT proceed to next field until you've stored the current one
- Call complete_stage when all required fields are collected

User message: {user_message}"""
        
        # Invoke Strands agent
        result = agent(context_prompt)
        
        # Log context for debugging
        app.logger.info(f"Session: {context.session_id if hasattr(context, 'session_id') else 'N/A'}")
        app.logger.info(f"Stage: {stage_info['stage_number']}/8 - {stage_info['stage_name']}")
        app.logger.info(f"Progress: {orchestrator.get_progress_percentage()}%")
        
        return {
            "result": result.message,
            "stage": stage_info['stage_number'],
            "progress": orchestrator.get_progress_percentage()
        }
    
    except Exception as e:
        app.logger.error(f"Agent error: {str(e)}")
        return {
            "error": str(e),
            "message": "An error occurred processing your request"
        }


if __name__ == "__main__":
    app.run()
