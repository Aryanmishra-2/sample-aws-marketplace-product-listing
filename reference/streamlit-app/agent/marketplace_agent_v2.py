"""
AWS Marketplace Listing Agent V2 - Multi-Agent Architecture
Integrates Master Orchestrator with 8 specialized sub-agents
"""

import yaml
import boto3
import json
from typing import Dict, Any, Optional

from .orchestrator import ListingOrchestrator, WorkflowStage
from .agentcore.runtime import AgentRuntime
from .agentcore.gateway import Gateway, ActionGroup
from .agentcore.identity import IdentityManager, Session
from .agentcore.memory import MemoryStore, ConversationMemory
from .tools import ListingTools, KnowledgeBaseTools


class MarketplaceListingAgentV2:
    """
    AWS Marketplace SaaS Listing Agent V2
    
    Multi-agent architecture with:
    - 1 Master Orchestrator managing workflow
    - 8 Specialized Sub-Agents for each stage
    - AgentCore components (Runtime, Gateway, Identity, Memory)
    - AWS Marketplace Catalog API integration
    """
    
    def __init__(self, config_path: str = "config/multi_agent_config.yaml"):
        """Initialize the multi-agent system"""
        self.config = self._load_config(config_path)
        
        # Initialize AWS clients
        bedrock_config = self.config['bedrock']
        
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=bedrock_config['region']
        )
        
        self.bedrock_agent_runtime = boto3.client(
            'bedrock-agent-runtime',
            region_name=bedrock_config['region']
        )
        
        # Initialize tools
        self.listing_tools = ListingTools(region=bedrock_config['region'])
        self.kb_tools = KnowledgeBaseTools(
            knowledge_base_id=self.config.get('knowledge_base', {}).get('id', ''),
            region=bedrock_config['region']
        )
        self.kb_tools.kb_client = self.bedrock_agent_runtime
        
        # Initialize Agentcore components
        self._setup_agentcore_components()
        
        # Initialize Master Orchestrator with listing tools
        self.orchestrator = ListingOrchestrator(listing_tools=self.listing_tools)
        
        # Workflow state
        self.current_session = None
    
    def _setup_agentcore_components(self):
        """Setup Agentcore Runtime, Gateway, Identity, and Memory"""
        
        # 1. Agentcore Identity - Manage user sessions
        self.identity_manager = IdentityManager()
        
        # 2. Agentcore Memory - Persist conversations
        self.memory_store = MemoryStore(backend="local")
        self.conversation_memory = ConversationMemory(
            memory_store=self.memory_store
        )
        
        # 3. Agentcore Gateway - Route actions to tools
        self.gateway = Gateway()
        self._register_action_groups()
        
        # 4. Agentcore Runtime - Execute agent logic
        self.runtime = AgentRuntime(
            model_id=self.config['bedrock']['model_id'],
            bedrock_client=self.bedrock_runtime,
            gateway=self.gateway,
            memory=self.conversation_memory,
            system_prompt=self.config['orchestrator_instructions'],
            max_iterations=self.config['bedrock'].get('max_iterations', 15),
            min_request_interval=self.config['bedrock'].get('min_request_interval', 0.5)
        )
    
    def _register_action_groups(self):
        """Register action groups with the Gateway"""
        
        # Listing Management Action Group
        listing_actions = ActionGroup(
            name="ListingManagement",
            description="Create and manage AWS Marketplace SaaS listings"
        )
        
        listing_actions.add_action(
            name="create_listing_draft",
            description="Create a new SaaS product with offer",
            handler=self._handle_create_listing,
            parameters={
                "product_title": {"type": "string", "required": True},
                "short_description": {"type": "string", "required": False},
                "long_description": {"type": "string", "required": False},
                "logo_url": {"type": "string", "required": False},
                "categories": {"type": "array", "required": False},
                "search_keywords": {"type": "array", "required": False}
            }
        )
        
        listing_actions.add_action(
            name="add_delivery_options",
            description="Add fulfillment URL to product",
            handler=self._handle_add_delivery,
            parameters={
                "product_id": {"type": "string", "required": True},
                "fulfillment_url": {"type": "string", "required": True}
            }
        )
        
        listing_actions.add_action(
            name="add_pricing",
            description="Add pricing to OFFER (use offer_id)",
            handler=self._handle_add_pricing,
            parameters={
                "offer_id": {"type": "string", "required": True},
                "pricing_model": {"type": "string", "required": True},
                "dimensions": {"type": "array", "required": False}
            }
        )
        
        listing_actions.add_action(
            name="get_listing_status",
            description="Check change set status and get entity IDs",
            handler=self._handle_get_status,
            parameters={
                "change_set_id": {"type": "string", "required": True}
            }
        )
        
        self.gateway.register_action_group(listing_actions)
        
        # Workflow Management Action Group (NEW)
        workflow_actions = ActionGroup(
            name="WorkflowManagement",
            description="Manage workflow state and stage data"
        )
        

        
        workflow_actions.add_action(
            name="complete_stage",
            description="Mark current stage as complete and execute API calls",
            handler=self._handle_complete_stage,
            parameters={}
        )
        
        self.gateway.register_action_group(workflow_actions)
        
        # Knowledge Base Action Group
        kb_actions = ActionGroup(
            name="KnowledgeBase",
            description="Query AWS Marketplace documentation"
        )
        
        kb_actions.add_action(
            name="query_knowledge_base",
            description="Search AWS Marketplace documentation",
            handler=self._handle_kb_query,
            parameters={
                "query": {"type": "string", "required": True},
                "max_results": {"type": "integer", "required": False, "default": 5}
            }
        )
        
        self.gateway.register_action_group(kb_actions)
        
        # Workflow Management Action Group
        workflow_actions = ActionGroup(
            name="WorkflowManagement",
            description="Manage workflow state and stage data"
        )
        
        workflow_actions.add_action(
            name="store_field_data",
            description="Store a field value for the current stage",
            handler=self._handle_store_field,
            parameters={
                "field_name": {"type": "string", "required": True},
                "field_value": {"type": "string", "required": True}
            }
        )
        
        workflow_actions.add_action(
            name="get_collected_data",
            description="Get all data collected for current stage",
            handler=self._handle_get_collected_data,
            parameters={}
        )
        
        workflow_actions.add_action(
            name="complete_stage",
            description="Mark current stage as complete and move to next stage",
            handler=self._handle_complete_stage,
            parameters={}
        )
        
        self.gateway.register_action_group(workflow_actions)
    
    # Action handlers
    def _handle_create_listing(self, **kwargs) -> Dict[str, Any]:
        """Handler for create_listing_draft action"""
        return self.listing_tools.create_listing_draft(**kwargs)
    
    def _handle_add_delivery(self, **kwargs) -> Dict[str, Any]:
        """Handler for add_delivery_options action"""
        return self.listing_tools.add_delivery_options(**kwargs)
    
    def _handle_add_pricing(self, **kwargs) -> Dict[str, Any]:
        """Handler for add_pricing action"""
        return self.listing_tools.add_pricing(**kwargs)
    
    def _handle_get_status(self, change_set_id: str) -> Dict[str, Any]:
        """Handler for get_listing_status action"""
        return self.listing_tools.get_listing_status(change_set_id)
    
    def _handle_kb_query(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Handler for query_knowledge_base action"""
        return self.kb_tools.query_knowledge_base(query, max_results)
    
    # Workflow management handlers
    def _handle_store_field(self, field_name: str, field_value: str) -> Dict[str, Any]:
        """Handler for storing stage field data"""
        try:
            self.orchestrator.set_stage_data(field_name, field_value)
            current_agent = self.orchestrator.get_current_agent()
            
            return {
                "success": True,
                "message": f"Stored {field_name}",
                "fields_collected": list(current_agent.stage_data.keys()),
                "fields_remaining": [f for f in current_agent.get_required_fields() 
                                   if f not in current_agent.stage_data]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _handle_get_collected_data(self) -> Dict[str, Any]:
        """Handler for getting collected stage data"""
        current_agent = self.orchestrator.get_current_agent()
        
        return {
            "stage_name": current_agent.stage_name,
            "stage_number": current_agent.stage_number,
            "required_fields": current_agent.get_required_fields(),
            "optional_fields": current_agent.get_optional_fields(),
            "fields_collected": list(current_agent.stage_data.keys()),
            "collected_data": current_agent.stage_data,
            "fields_remaining": [f for f in current_agent.get_required_fields() 
                               if f not in current_agent.stage_data],
            "is_complete": current_agent.is_stage_complete(),
            "validation_errors": current_agent.validate_all_fields(current_agent.stage_data)
        }
    
    def _handle_complete_stage(self) -> Dict[str, Any]:
        """Handler for completing current stage"""
        try:
            result = self.orchestrator.complete_current_stage()
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to complete stage: {str(e)}"
            }
    
    def _handle_store_field(self, field_name: str, field_value: str) -> Dict[str, Any]:
        """Handler for store_field_data action"""
        self.orchestrator.set_stage_data(field_name, field_value)
        return {
            "success": True,
            "message": f"Stored {field_name}",
            "field_name": field_name
        }
    
    def _handle_get_collected_data(self) -> Dict[str, Any]:
        """Handler for get_collected_data action"""
        current_agent = self.orchestrator.get_current_agent()
        return {
            "success": True,
            "data": current_agent.stage_data,
            "fields_collected": list(current_agent.stage_data.keys())
        }
    
    def _handle_complete_stage(self) -> Dict[str, Any]:
        """Handler for complete_stage action"""
        if self.orchestrator.check_stage_completion():
            result = self.orchestrator.complete_current_stage()
            return result
        else:
            current_agent = self.orchestrator.get_current_agent()
            required = current_agent.get_required_fields()
            collected = list(current_agent.stage_data.keys())
            missing = [f for f in required if f not in collected]
            return {
                "success": False,
                "message": "Stage not complete - missing required fields",
                "missing_fields": missing
            }
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load YAML configuration file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def create_session(self, user_id: str, session_attributes: Optional[Dict[str, Any]] = None) -> Session:
        """Create a new user session"""
        self.current_session = self.identity_manager.create_session(
            user_id=user_id,
            attributes=session_attributes or {}
        )
        return self.current_session
    
    def process_message(self, user_message: str, user_id: Optional[str] = None) -> str:
        """
        Process user message through orchestrator and runtime
        
        Args:
            user_message: User's input message
            user_id: Optional user identifier
            
        Returns:
            Agent's response
        """
        # Ensure session exists
        if not self.current_session and user_id:
            self.create_session(user_id)
        
        session_id = self.current_session.session_id if self.current_session else "default"
        
        # Get current stage info
        stage_info = self.orchestrator.get_stage_info()
        current_agent = self.orchestrator.get_current_agent()
        
        # Build context with what we've collected so far
        collected_fields = list(current_agent.stage_data.keys())
        missing_fields = [f for f in stage_info['required_fields'] if f not in collected_fields]
        
        # Load conversation history (keep last 10 messages for context)
        # Note: We start with empty history for each turn to avoid tool result format issues
        # The system prompt contains all the context about collected data
        conversation_history = []
        
        # Build system prompt with stage context and collected data
        system_prompt = f"""You are an AWS Marketplace listing assistant in Stage {stage_info['stage_number']}/8: {stage_info['stage_name']}.

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

CRITICAL RULES:
- DO NOT ask for information that's already in "COLLECTED DATA SO FAR"
- ALWAYS call store_field_data when user provides information
- DO NOT proceed to next field until you've stored the current one
- Call complete_stage when all required fields are collected

EXAMPLE:
User: "My product is called CloudSync Pro"
You: [Call store_field_data("product_title", "CloudSync Pro")]
You: "Great! I've saved CloudSync Pro as your product title. Now, what's your logo S3 URL?"
"""
        
        # Process through runtime with enhanced context
        response = self.runtime.process(
            message=user_message,
            session_id=session_id,
            conversation_history=conversation_history,
            system_prompt_override=system_prompt
        )
        
        # Check if LLM indicated stage completion
        if "STAGE_COMPLETE" in response:
            # Try to complete the stage
            if current_agent.is_stage_complete():
                completion_result = self.orchestrator.complete_current_stage()
                
                # Build response with completion info
                response = response.replace("STAGE_COMPLETE", "")
                response += f"\n\n✅ {completion_result.get('message', 'Stage complete!')}"
                
                if completion_result.get('api_result'):
                    api_result = completion_result['api_result']
                    if api_result.get('success'):
                        response += f"\n{api_result.get('message', '')}"
                        if api_result.get('product_id'):
                            response += f"\n🆔 Product ID: {api_result['product_id']}"
                        if api_result.get('offer_id'):
                            response += f"\n🆔 Offer ID: {api_result['offer_id']}"
                
                if completion_result.get('transition'):
                    response += completion_result['transition']['message']
            else:
                response += "\n\n⚠️ Some required fields are still missing. Let me help you complete them."
        
        # Save to memory
        self.conversation_memory.add_message(
            session_id=session_id,
            role="user",
            content=user_message
        )
        self.conversation_memory.add_message(
            session_id=session_id,
            role="assistant",
            content=response
        )
        
        return response
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        return {
            "current_stage": self.orchestrator.current_stage.value,
            "stage_name": self.orchestrator.get_current_agent().stage_name,
            "progress": self.orchestrator.get_progress_percentage(),
            "completed_stages": [s.value for s in self.orchestrator.completed_stages],
            "summary": self.orchestrator.get_workflow_summary()
        }
    
    def reset_workflow(self):
        """Reset workflow to beginning"""
        self.orchestrator.reset_workflow()
    
    def export_workflow_data(self) -> Dict[str, Any]:
        """Export all collected workflow data"""
        return self.orchestrator.export_data()
    
    def import_workflow_data(self, data: Dict[str, Any]) -> bool:
        """Import previously exported workflow data"""
        return self.orchestrator.import_data(data)
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information"""
        if not self.current_session:
            return {"session_id": None, "user_id": None}
        
        return {
            "session_id": self.current_session.session_id,
            "user_id": self.current_session.user_id,
            "created_at": self.current_session.created_at,
            "attributes": self.current_session.attributes
        }
