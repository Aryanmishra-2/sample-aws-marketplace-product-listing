"""
AWS Marketplace Listing Agent - Strands SDK Implementation
Integrates Strands Agent with existing orchestrator and sub-agents
"""

import json
import os
from typing import Dict, Any, Optional, List
from strands import Agent, tool

from .orchestrator import ListingOrchestrator, WorkflowStage
from .tools.listing_tools import ListingTools


class StrandsMarketplaceAgent:
    """
    AWS Marketplace SaaS Listing Agent using Strands SDK
    
    Architecture:
    - Strands Agent for LLM interaction and tool execution
    - Existing ListingOrchestrator for workflow management
    - Existing sub-agents for stage-specific logic
    - Existing ListingTools for AWS Marketplace API calls
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Strands-based marketplace agent"""
        self.config = config or {}
        
        # Initialize AWS Marketplace tools
        region = self.config.get('region', 'us-east-1')
        self.listing_tools = ListingTools(region=region)
        
        # Initialize orchestrator with listing tools
        self.orchestrator = ListingOrchestrator(listing_tools=self.listing_tools)
        
        # Get model configuration
        model_id = self.config.get('model_id', 'us.anthropic.claude-3-7-sonnet-20250219-v1:0')
        
        # Create Strands agent with tools
        self.agent = Agent(
            tools=[
                self._create_store_field_tool(),
                self._create_get_collected_data_tool(),
                self._create_complete_stage_tool(),
                self._create_get_stage_info_tool(),
                self._create_create_listing_tool(),
                self._create_add_delivery_tool(),
                self._create_add_pricing_tool(),
                self._create_get_status_tool(),
            ],
            model=model_id
        )
    
    def _create_store_field_tool(self):
        """Create tool for storing field data"""
        orchestrator = self.orchestrator
        
        @tool
        def store_field_data(field_name: str, field_value: str) -> dict:
            """
            Store a field value for the current stage.
            Call this IMMEDIATELY when user provides any information.
            
            Args:
                field_name: Name of the field to store (e.g., "product_title", "logo_s3_url")
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
        
        return store_field_data
    
    def _create_get_collected_data_tool(self):
        """Create tool for getting collected data"""
        orchestrator = self.orchestrator
        
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
        
        return get_collected_data
    
    def _create_complete_stage_tool(self):
        """Create tool for completing current stage"""
        orchestrator = self.orchestrator
        
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
        
        return complete_stage
    
    def _create_get_stage_info_tool(self):
        """Create tool for getting stage information"""
        orchestrator = self.orchestrator
        
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
        
        return get_stage_info
    
    def _create_create_listing_tool(self):
        """Create tool for creating listing draft"""
        listing_tools = self.listing_tools
        
        @tool
        def create_listing_draft(
            product_title: str,
            short_description: str = None,
            long_description: str = None,
            logo_url: str = None,
            categories: list = None,
            search_keywords: list = None,
            highlights: list = None
        ) -> dict:
            """
            Create a new SaaS product with offer in AWS Marketplace.
            This is called automatically by the orchestrator, not directly by you.
            
            Args:
                product_title: Product name (required)
                short_description: Brief product description
                long_description: Detailed product description
                logo_url: URL to product logo
                categories: Product categories (1-3 items)
                search_keywords: Keywords for search (1-10 items)
                highlights: Product highlights (array of strings)
            
            Returns:
                Dictionary with product_id, offer_id, and change_set_id
            """
            return listing_tools.create_listing_draft(
                product_title=product_title,
                short_description=short_description,
                long_description=long_description,
                logo_url=logo_url,
                categories=categories,
                search_keywords=search_keywords,
                highlights=highlights
            )
        
        return create_listing_draft
    
    def _create_add_delivery_tool(self):
        """Create tool for adding delivery options"""
        listing_tools = self.listing_tools
        
        @tool
        def add_delivery_options(
            product_id: str,
            fulfillment_url: str,
            quick_launch_enabled: bool = False,
            launch_url: str = None
        ) -> dict:
            """
            Add fulfillment URL to product.
            This is called automatically by the orchestrator.
            
            Args:
                product_id: The product entity ID
                fulfillment_url: SaaS fulfillment URL
                quick_launch_enabled: Enable quick launch
                launch_url: Quick launch URL
            
            Returns:
                Dictionary with update status
            """
            return listing_tools.add_delivery_options(
                product_id=product_id,
                fulfillment_url=fulfillment_url,
                quick_launch_enabled=quick_launch_enabled,
                launch_url=launch_url
            )
        
        return add_delivery_options
    
    def _create_add_pricing_tool(self):
        """Create tool for adding pricing"""
        listing_tools = self.listing_tools
        
        @tool
        def add_pricing(
            offer_id: str,
            pricing_model: str,
            dimensions: list = None,
            contract_durations: list = None
        ) -> dict:
            """
            Add pricing to offer.
            This is called automatically by the orchestrator.
            
            Args:
                offer_id: The offer entity ID
                pricing_model: "Usage", "Contract", or "Free"
                dimensions: Pricing dimensions
                contract_durations: Contract durations for Contract pricing
            
            Returns:
                Dictionary with update status
            """
            return listing_tools.add_pricing(
                offer_id=offer_id,
                pricing_model=pricing_model,
                dimensions=dimensions,
                contract_durations=contract_durations
            )
        
        return add_pricing
    
    def _create_get_status_tool(self):
        """Create tool for getting changeset status"""
        listing_tools = self.listing_tools
        
        @tool
        def get_listing_status(change_set_id: str) -> dict:
            """
            Check AWS Marketplace changeset status and get entity IDs.
            
            Args:
                change_set_id: The changeset ID to check
            
            Returns:
                Dictionary with status and entity IDs
            """
            return listing_tools.get_listing_status(change_set_id)
        
        return get_listing_status
    
    def process_message(self, user_message: str, session_id: Optional[str] = None) -> str:
        """
        Process user message through Strands agent
        
        Args:
            user_message: User's input message
            session_id: Optional session identifier
            
        Returns:
            Agent's response
        """
        # Get current stage context
        stage_info = self.orchestrator.get_stage_info()
        current_agent = self.orchestrator.get_current_agent()
        
        # Build collected data summary
        collected_fields = list(current_agent.stage_data.keys())
        missing_fields = [f for f in stage_info['required_fields'] if f not in collected_fields]
        
        # Build context-aware system prompt
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

CRITICAL RULES:
- DO NOT ask for information that's already in "COLLECTED DATA SO FAR"
- ALWAYS call store_field_data when user provides information
- DO NOT proceed to next field until you've stored the current one
- Call complete_stage when all required fields are collected

User message: {user_message}"""
        
        # Invoke Strands agent
        result = self.agent(context_prompt)
        
        return result.message
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        return {
            "current_stage": self.orchestrator.current_stage.value,
            "stage_name": self.orchestrator.get_current_agent().stage_name,
            "progress": self.orchestrator.get_progress_percentage(),
            "completed_stages": [s.value for s in self.orchestrator.completed_stages],
            "product_id": self.orchestrator.product_id,
            "offer_id": self.orchestrator.offer_id
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
