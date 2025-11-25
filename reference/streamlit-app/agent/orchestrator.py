"""
Master Orchestrator Agent
Manages workflow across all 8 stages of SaaS listing creation
"""

from typing import Dict, Any, Optional
from enum import Enum

from .sub_agents import (
    SellerRegistrationAgent,
    ProductInformationAgent,
    FulfillmentAgent,
    PricingConfigAgent,
    PriceReviewAgent,
    RefundPolicyAgent,
    EULAConfigAgent,
    OfferAvailabilityAgent,
    AllowlistAgent
)


class WorkflowStage(Enum):
    """Workflow stages"""
    SELLER_REGISTRATION = 0
    PRODUCT_INFO = 1
    FULFILLMENT = 2
    PRICING_CONFIG = 3
    PRICE_REVIEW = 4
    REFUND_POLICY = 5
    EULA_CONFIG = 6
    OFFER_AVAILABILITY = 7
    ALLOWLIST = 8
    COMPLETE = 9


class ListingOrchestrator:
    """
    Master Orchestrator for AWS Marketplace SaaS Listing Creation
    
    Manages:
    - Workflow state across 8 stages
    - Routing to appropriate sub-agent
    - Progress tracking
    - Data aggregation
    - Stage transitions
    - API execution
    """
    
    def __init__(self, listing_tools=None):
        # Initialize all sub-agents
        self.agents = {
            WorkflowStage.PRODUCT_INFO: ProductInformationAgent(),
            WorkflowStage.FULFILLMENT: FulfillmentAgent(),
            WorkflowStage.PRICING_CONFIG: PricingConfigAgent(),
            WorkflowStage.PRICE_REVIEW: PriceReviewAgent(),
            WorkflowStage.REFUND_POLICY: RefundPolicyAgent(),
            WorkflowStage.EULA_CONFIG: EULAConfigAgent(),
            WorkflowStage.OFFER_AVAILABILITY: OfferAvailabilityAgent(),
            WorkflowStage.ALLOWLIST: AllowlistAgent()
        }
        
        # Workflow state
        self.current_stage = WorkflowStage.PRODUCT_INFO
        self.completed_stages = set()
        self.all_data = {}
        self.workflow_started = False
        
        # API tools (injected from main agent)
        self.listing_tools = listing_tools
        
        # Entity IDs from AWS Marketplace
        self.product_id = None
        self.offer_id = None
        self.change_set_ids = []
    
    def get_current_agent(self):
        """Get the sub-agent for current stage"""
        return self.agents.get(self.current_stage)
    
    def set_stage_data(self, field: str, value: Any):
        """
        Set data for current stage
        
        This is called by the LLM/runtime when it extracts information
        """
        current_agent = self.get_current_agent()
        if current_agent:
            current_agent.stage_data[field] = value
    
    def check_stage_completion(self) -> bool:
        """Check if current stage has all required data"""
        current_agent = self.get_current_agent()
        if current_agent:
            return current_agent.is_stage_complete()
        return False
    
    def complete_current_stage(self) -> Dict[str, Any]:
        """
        Mark current stage as complete and execute API calls
        
        Returns response with transition info
        """
        current_agent = self.get_current_agent()
        
        if not current_agent or not current_agent.is_stage_complete():
            return {
                "status": "error",
                "message": "Stage not ready to complete - missing required fields"
            }
        
        # Save stage data
        self.all_data[self.current_stage.name] = current_agent.stage_data.copy()
        self.completed_stages.add(self.current_stage)
        
        # Execute API calls
        api_result = self._execute_stage_api_calls(self.current_stage)
        
        # Debug: Log API result
        print(f"[DEBUG] Stage {self.current_stage.name} API Result: {api_result}")
        
        # If successful and we got a change_set_id, wait for it to complete
        if api_result and api_result.get("success") and api_result.get("change_set_id"):
            change_set_id = api_result["change_set_id"]
            print(f"[DEBUG] Waiting for change set {change_set_id} to complete...")
            self._wait_for_changeset(change_set_id, max_wait_seconds=30)
        
        # Move to next stage
        next_stage = self._get_next_stage()
        
        response = {
            "status": "complete",
            "message": f"✅ Stage {self.current_stage.value} complete!",
            "data": current_agent.stage_data,
            "api_result": api_result
        }
        
        if next_stage:
            self.current_stage = next_stage
            next_agent = self.get_current_agent()
            
            transition_msg = f"\n\n📍 Moving to Stage {next_stage.value}: {next_agent.stage_name}"
            if api_result and api_result.get("success"):
                transition_msg += f"\n✅ {api_result.get('message', 'API calls completed')}"
                if api_result.get("product_id"):
                    transition_msg += f"\n🆔 Product ID: {api_result['product_id']}"
                if api_result.get("offer_id"):
                    transition_msg += f"\n🆔 Offer ID: {api_result['offer_id']}"
            
            response["transition"] = {
                "message": transition_msg,
                "progress": self.get_progress_percentage()
            }
        else:
            self.current_stage = WorkflowStage.COMPLETE
            response["workflow_complete"] = True
        
        return response
    
    def process_message(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process user message through appropriate sub-agent
        
        Args:
            user_message: User's input
            context: Additional context
            
        Returns:
            Response dict with status, message, and data
        """
        context = context or {}
        
        # Check if workflow is complete
        if self.current_stage == WorkflowStage.COMPLETE:
            return {
                "status": "complete",
                "message": "🎉 All stages complete! Your listing is ready to be created.",
                "data": self.all_data,
                "summary": self.get_workflow_summary()
            }
        
        # Get current sub-agent
        agent = self.get_current_agent()
        
        if not agent:
            return {
                "status": "error",
                "message": "Invalid workflow stage"
            }
        
        # Process through sub-agent
        response = agent.process_stage(user_message, context)
        
        # Check if stage is complete
        if response.get("status") == "complete":
            # Save stage data
            self.all_data[self.current_stage.name] = response.get("data", {})
            self.completed_stages.add(self.current_stage)
            
            # Execute API calls for completed stage
            api_result = self._execute_stage_api_calls(self.current_stage)
            if api_result:
                response["api_result"] = api_result
            
            # Move to next stage
            next_stage = self._get_next_stage()
            
            if next_stage:
                self.current_stage = next_stage
                next_agent = self.get_current_agent()
                
                # Add transition message
                transition_msg = f"\n\n📍 Moving to Stage {next_stage.value}: {next_agent.stage_name}"
                if api_result and api_result.get("success"):
                    transition_msg += f"\n✅ {api_result.get('message', 'Stage API calls completed')}"
                
                response["transition"] = {
                    "message": transition_msg,
                    "progress": self.get_progress_percentage()
                }
            else:
                # All stages complete
                self.current_stage = WorkflowStage.COMPLETE
                response["workflow_complete"] = True
        
        # Add progress info
        response["current_stage"] = self.current_stage.value
        response["stage_name"] = agent.stage_name
        response["progress"] = self.get_progress_percentage()
        
        return response
    
    def _wait_for_changeset(self, change_set_id: str, max_wait_seconds: int = 30) -> bool:
        """
        Wait for a change set to complete
        
        Args:
            change_set_id: The change set ID to wait for
            max_wait_seconds: Maximum time to wait in seconds
            
        Returns:
            True if succeeded, False otherwise
        """
        import time
        max_attempts = max_wait_seconds // 3
        attempt = 0
        
        while attempt < max_attempts:
            time.sleep(3)
            attempt += 1
            
            status_result = self.listing_tools.get_listing_status(change_set_id)
            
            if not status_result.get("success"):
                print(f"[DEBUG] Failed to get status: {status_result.get('error')}")
                return False
            
            status = status_result.get("status")
            print(f"[DEBUG] Change set status: {status} (attempt {attempt}/{max_attempts})")
            
            if status == "SUCCEEDED":
                print(f"[DEBUG] Change set {change_set_id} completed successfully!")
                return True
            elif status in ["FAILED", "CANCELLED"]:
                print(f"[DEBUG] Change set {change_set_id} {status}")
                return False
        
        print(f"[DEBUG] Timeout waiting for change set {change_set_id}")
        return False
    
    def _get_next_stage(self) -> Optional[WorkflowStage]:
        """Get next workflow stage"""
        current_value = self.current_stage.value
        
        # Find next stage
        for stage in WorkflowStage:
            if stage.value == current_value + 1 and stage != WorkflowStage.COMPLETE:
                return stage
        
        # No more stages, workflow complete
        return None
    
    def get_progress_percentage(self) -> int:
        """Calculate workflow progress percentage"""
        total_stages = len(WorkflowStage) - 1  # Exclude COMPLETE
        completed = len(self.completed_stages)
        return int((completed / total_stages) * 100)
    
    def get_workflow_summary(self) -> str:
        """Get summary of entire workflow"""
        summary = "AWS Marketplace SaaS Listing - Workflow Summary\n"
        summary += "=" * 60 + "\n\n"
        
        for stage in WorkflowStage:
            if stage == WorkflowStage.COMPLETE:
                continue
            
            agent = self.agents[stage]
            status = "✅ Complete" if stage in self.completed_stages else "⏳ Pending"
            
            summary += f"Stage {stage.value}: {agent.stage_name} - {status}\n"
            
            if stage in self.completed_stages:
                data = self.all_data.get(stage.name, {})
                summary += f"  Data collected: {len(data)} fields\n"
        
        summary += "\n" + "=" * 60 + "\n"
        summary += f"Progress: {self.get_progress_percentage()}%\n"
        
        return summary
    
    def get_stage_info(self, stage: Optional[WorkflowStage] = None) -> Dict[str, Any]:
        """Get information about a specific stage"""
        stage = stage or self.current_stage
        agent = self.agents.get(stage)
        
        if not agent:
            return {}
        
        return {
            "stage_number": stage.value,
            "stage_name": agent.stage_name,
            "required_fields": agent.get_required_fields(),
            "optional_fields": agent.get_optional_fields(),
            "is_complete": stage in self.completed_stages,
            "instructions": agent.get_stage_instructions()
        }
    
    def skip_stage(self, stage: WorkflowStage) -> bool:
        """
        Skip a stage (only if optional)
        
        Returns:
            True if skipped, False if required
        """
        agent = self.agents.get(stage)
        
        if not agent:
            return False
        
        # Check if stage has no required fields (fully optional)
        if len(agent.get_required_fields()) == 0:
            self.completed_stages.add(stage)
            return True
        
        return False
    
    def go_to_stage(self, stage: WorkflowStage) -> bool:
        """
        Jump to a specific stage
        
        Returns:
            True if successful, False if not allowed
        """
        # Can only go to current or previous stages
        if stage.value <= self.current_stage.value:
            self.current_stage = stage
            return True
        
        return False
    
    def reset_workflow(self):
        """Reset entire workflow"""
        self.current_stage = WorkflowStage.PRODUCT_INFO
        self.completed_stages = set()
        self.all_data = {}
        self.workflow_started = False
        
        # Reset all agents
        for agent in self.agents.values():
            agent.reset()
    
    def export_data(self) -> Dict[str, Any]:
        """Export all collected data"""
        return {
            "workflow_version": "1.0",
            "progress": self.get_progress_percentage(),
            "current_stage": self.current_stage.value,
            "completed_stages": [s.value for s in self.completed_stages],
            "data": self.all_data,
            "product_id": self.product_id,
            "offer_id": self.offer_id,
            "change_set_ids": self.change_set_ids
        }
    
    def import_data(self, data: Dict[str, Any]) -> bool:
        """Import previously exported data"""
        try:
            self.all_data = data.get("data", {})
            self.current_stage = WorkflowStage(data.get("current_stage", 1))
            self.completed_stages = {WorkflowStage(s) for s in data.get("completed_stages", [])}
            self.product_id = data.get("product_id")
            self.offer_id = data.get("offer_id")
            return True
        except Exception:
            return False
    
    def _execute_stage_api_calls(self, stage: WorkflowStage) -> Optional[Dict[str, Any]]:
        """
        Execute AWS Marketplace API calls for completed stage
        
        Returns:
            Result dict with success status and message
        """
        print(f"[DEBUG] _execute_stage_api_calls called for stage: {stage.name}")
        
        if not self.listing_tools:
            print("[DEBUG] No listing_tools available!")
            return None
        
        stage_data = self.all_data.get(stage.name, {})
        print(f"[DEBUG] Stage data: {stage_data}")
        
        try:
            if stage == WorkflowStage.PRODUCT_INFO:
                # Stage 1: Create Product and Offer
                return self._create_product_and_offer(stage_data)
            
            elif stage == WorkflowStage.FULFILLMENT:
                # Stage 2: Add delivery options
                return self._add_delivery_options(stage_data)
            
            elif stage == WorkflowStage.PRICING_CONFIG:
                # Stage 3: Add pricing dimensions to Product
                return self._add_pricing_dimensions(stage_data)
            
            elif stage == WorkflowStage.PRICE_REVIEW:
                # Stage 4: Apply pricing to Offer
                return self._apply_pricing(stage_data)
            
            elif stage == WorkflowStage.REFUND_POLICY:
                # Stage 5: Update support terms on Offer
                return self._update_support_terms(stage_data)
            
            elif stage == WorkflowStage.EULA_CONFIG:
                # Stage 6: Update legal terms on Offer
                return self._update_legal_terms(stage_data)
            
            elif stage == WorkflowStage.OFFER_AVAILABILITY:
                # Stage 7: Update offer availability
                return self._update_offer_availability(stage_data)
            
            elif stage == WorkflowStage.ALLOWLIST:
                # Stage 8: Update offer targeting
                return self._update_offer_targeting(stage_data)
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"API call failed: {str(e)}"
            }
        
        return None
    
    def _create_product_and_offer(self, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create product and offer in AWS Marketplace
        
        Uses two-step approach:
        1. Create minimal product with just title (fast)
        2. Update with full details after getting product_id
        
        Note: This method will poll for up to 30 seconds. If the change set
        is still processing, it returns success anyway and the IDs can be
        retrieved later.
        """
        
        product_title = stage_data.get("product_title")
        
        if not product_title:
            return {
                "success": False,
                "error": "Product title is required",
                "message": "Cannot create product without a title"
            }
        
        # Step 1: Create minimal product with just title
        result = self.listing_tools.create_product_minimal(product_title)
        
        if not result.get("success"):
            return result
        
        # Store change set ID
        change_set_id = result.get("change_set_id")
        self.change_set_ids.append(change_set_id)
        
        # Step 2: Poll for change set completion (max 30 seconds - reduced for better UX)
        import time
        max_attempts = 10  # 10 attempts x 3 seconds = 30 seconds max
        attempt = 0
        status = None
        
        while attempt < max_attempts:
            time.sleep(3)
            attempt += 1
            
            status_result = self.listing_tools.get_listing_status(change_set_id)
            
            if not status_result.get("success"):
                break
            
            status = status_result.get("status")
            
            if status == "SUCCEEDED":
                # Extract entity IDs from change set
                change_set = status_result.get("change_set", [])
                for change in change_set:
                    entity = change.get("Entity", {})
                    entity_type = entity.get("Type", "")
                    entity_id = entity.get("Identifier", "")
                    
                    # Strip @revision suffix from entity ID
                    if "@" in entity_id:
                        entity_id = entity_id.split("@")[0]
                    
                    if "SaaSProduct" in entity_type:
                        self.product_id = entity_id
                    elif "Offer" in entity_type:
                        self.offer_id = entity_id
                
                # Step 3: Update product with full details
                if self.product_id:
                    update_result = self._update_product_details(stage_data)
                    if not update_result.get("success"):
                        return {
                            "success": True,
                            "message": f"Product created but update failed: {update_result.get('error')}",
                            "product_id": self.product_id,
                            "offer_id": self.offer_id,
                            "note": "You can update details manually later"
                        }
                
                return {
                    "success": True,
                    "message": f"✅ Product '{product_title}' created and updated successfully!",
                    "product_id": self.product_id,
                    "offer_id": self.offer_id,
                    "change_set_id": change_set_id
                }
            
            elif status in ["FAILED", "CANCELLED"]:
                return {
                    "success": False,
                    "error": f"Change set {status}",
                    "message": f"Product creation {status.lower()}"
                }
        
        # Timeout - product still processing, but that's OK!
        # Return success so workflow can continue
        return {
            "success": True,
            "message": f"✅ Product '{product_title}' creation initiated successfully!\n\n⏳ AWS is still processing (Change Set: {change_set_id})\n\n💡 The product will be ready shortly. You can continue to the next stage, and the product_id will be available when needed.",
            "change_set_id": change_set_id,
            "status": status or "PROCESSING",
            "note": "Product creation in progress - IDs will be available soon"
        }
    
    def check_pending_changeset(self) -> bool:
        """
        Check if there's a pending change set and try to extract IDs
        
        Returns:
            True if IDs were extracted, False otherwise
        """
        if self.product_id and self.offer_id:
            return True  # Already have IDs
        
        if not self.change_set_ids:
            return False  # No change sets to check
        
        # Check the most recent change set
        change_set_id = self.change_set_ids[-1]
        
        status_result = self.listing_tools.get_listing_status(change_set_id)
        
        if not status_result.get("success"):
            return False
        
        status = status_result.get("status")
        
        if status == "SUCCEEDED":
            # Extract entity IDs
            change_set = status_result.get("change_set", [])
            for change in change_set:
                entity = change.get("Entity", {})
                entity_type = entity.get("Type", "")
                entity_id = entity.get("Identifier", "")
                
                # Strip @revision suffix from entity ID
                if "@" in entity_id:
                    entity_id = entity_id.split("@")[0]
                
                if "SaaSProduct" in entity_type:
                    self.product_id = entity_id
                elif "Offer" in entity_type:
                    self.offer_id = entity_id
            
            return bool(self.product_id and self.offer_id)
        
        return False
    
    def _update_product_details(self, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update product with full details after creation
        
        Args:
            stage_data: Stage data with all product information
            
        Returns:
            Result dict
        """
        if not self.product_id:
            return {
                "success": False,
                "error": "No product_id available"
            }
        
        # Build update details
        updates = {}
        
        # Get highlights - now stored as array
        highlights = stage_data.get("highlights", [])
        if not highlights:
            # Backward compatibility: convert old format
            if stage_data.get("highlight_1"):
                highlights.append(stage_data["highlight_1"])
            if stage_data.get("highlight_2"):
                highlights.append(stage_data["highlight_2"])
            if stage_data.get("highlight_3"):
                highlights.append(stage_data["highlight_3"])
        
        if highlights:
            updates["Highlights"] = highlights
        
        # Get video URLs
        video_urls = stage_data.get("video_urls", [])
        if not video_urls and stage_data.get("product_video_url"):
            video_urls = [stage_data["product_video_url"]]
        
        if video_urls:
            updates["VideoUrls"] = video_urls
        
        # Add other fields
        if stage_data.get("short_description"):
            updates["ShortDescription"] = stage_data["short_description"]
        
        if stage_data.get("long_description"):
            updates["LongDescription"] = stage_data["long_description"]
        
        if stage_data.get("logo_s3_url"):
            updates["LogoUrl"] = stage_data["logo_s3_url"]
        
        if stage_data.get("categories"):
            updates["Categories"] = stage_data["categories"]
        
        if stage_data.get("search_keywords"):
            updates["SearchKeywords"] = stage_data["search_keywords"]
        
        # Always include AdditionalResources (AWS requires it)
        updates["AdditionalResources"] = []
        
        # Update product
        result = self.listing_tools.update_product_information(
            product_id=self.product_id,
            updates=updates
        )
        
        if result.get("success"):
            change_set_id = result.get("change_set_id")
            if change_set_id:
                self.change_set_ids.append(change_set_id)
                # Wait for update changeset to complete before proceeding
                print(f"[DEBUG] Waiting for product update changeset {change_set_id} to complete...")
                self._wait_for_changeset(change_set_id, max_wait_seconds=30)
        
        return result
    
    def _add_delivery_options(self, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add delivery options to product"""
        
        print("[DEBUG] _add_delivery_options called")
        print(f"[DEBUG] Current product_id: {self.product_id}")
        
        # Check if we need to retrieve product_id from pending change set
        if not self.product_id:
            print("[DEBUG] No product_id, checking pending changesets...")
            self.check_pending_changeset()
            print(f"[DEBUG] After check, product_id: {self.product_id}")
        
        if not self.product_id:
            print("[DEBUG] Still no product_id, returning error")
            return {
                "success": False,
                "error": "No product_id available",
                "message": "Product must be created first. Please wait for Stage 1 to complete."
            }
        
        # Retry logic for ResourceInUseException (entity locked by another changeset)
        import time
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            result = self.listing_tools.add_delivery_options(
                product_id=self.product_id,
                fulfillment_url=stage_data.get("fulfillment_url"),
                quick_launch_enabled=stage_data.get("quick_launch_enabled", False),
                launch_url=stage_data.get("launch_url")
            )
            
            # Check if we got ResourceInUseException
            if not result.get("success") and "ResourceInUseException" in result.get("error", ""):
                if attempt < max_retries - 1:
                    print(f"[DEBUG] Entity locked, retrying in {retry_delay} seconds (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"[DEBUG] Entity still locked after {max_retries} attempts")
                    return {
                        "success": False,
                        "error": "Product entity is locked by another changeset",
                        "message": "Please wait a moment and try again, or continue to next stage"
                    }
            
            # Success or other error - break retry loop
            if result.get("success"):
                change_set_id = result.get("change_set_id")
                self.change_set_ids.append(change_set_id)
            
            return result
        
        return result
    
    def _apply_pricing(self, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply pricing to offer"""
        
        # Check if we need to retrieve offer_id from pending change set
        if not self.offer_id:
            self.check_pending_changeset()
        
        if not self.offer_id:
            return {
                "success": False,
                "error": "No offer_id available",
                "message": "Offer must be created first. Please wait for Stage 1 to complete."
            }
        
        # Get pricing config from Stage 3
        pricing_config = self.all_data.get("PRICING_CONFIG", {})
        
        # Capitalize pricing model for API
        pricing_model = pricing_config.get("pricing_model", "usage")
        pricing_model = pricing_model.capitalize()  # "contract" -> "Contract"
        
        dimensions = pricing_config.get("dimensions", [])
        
        # Check if dimensions were skipped in stage 3
        stage3_result = self.all_data.get("PRICING_CONFIG", {})
        dimensions_skipped = stage3_result.get("dimensions_skipped", False)
        
        # Check if this is hybrid pricing (has both Entitled and Metered dimensions)
        has_entitled = any("Entitled" in d.get("Types", []) for d in dimensions)
        has_metered = any("Metered" in d.get("Types", []) for d in dimensions)
        is_hybrid = has_entitled and has_metered
        
        # Get Stage 4 data (durations and constraints)
        contract_durations = stage_data.get("contract_durations", ["12 Months"])
        multiple_dimension_selection = stage_data.get("multiple_dimension_selection", "Allowed")
        quantity_configuration = stage_data.get("quantity_configuration", "Allowed")
        
        # For Usage pricing, add dimensions and pricing in a single changeset
        if pricing_model == "Usage" and dimensions and dimensions_skipped:
            result = self.listing_tools.add_dimensions_and_pricing_for_usage(
                product_id=self.product_id,
                offer_id=self.offer_id,
                dimensions=dimensions
            )
            
            if result.get("success"):
                change_set_id = result.get("change_set_id")
                self.change_set_ids.append(change_set_id)
            
            return result
        
        # For hybrid pricing (Contract with Consumption), add dimensions and both pricing terms together
        if is_hybrid and dimensions_skipped:
            result = self.listing_tools.add_dimensions_and_pricing_for_hybrid(
                product_id=self.product_id,
                offer_id=self.offer_id,
                dimensions=dimensions,
                contract_durations=contract_durations,
                multiple_dimension_selection=multiple_dimension_selection,
                quantity_configuration=quantity_configuration
            )
            
            if result.get("success"):
                change_set_id = result.get("change_set_id")
                self.change_set_ids.append(change_set_id)
            
            return result
        
        # For pure Contract pricing, add pricing normally (dimensions already added in stage 3)
        result = self.listing_tools.add_pricing(
            offer_id=self.offer_id,
            pricing_model=pricing_model,
            dimensions=dimensions,
            contract_durations=contract_durations,
            multiple_dimension_selection=multiple_dimension_selection,
            quantity_configuration=quantity_configuration
        )
        
        if result.get("success"):
            change_set_id = result.get("change_set_id")
            self.change_set_ids.append(change_set_id)
        
        return result

    def _add_pricing_dimensions(self, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add pricing dimensions to Product"""
        
        # Check if we need to retrieve product_id from pending change set
        if not self.product_id:
            self.check_pending_changeset()
        
        if not self.product_id:
            return {
                "success": False,
                "error": "No product_id available",
                "message": "Product must be created first. Please wait for Stage 1 to complete."
            }
        
        dimensions = stage_data.get("dimensions", [])
        pricing_model = stage_data.get("pricing_model", "").lower()
        
        if not dimensions:
            return {
                "success": True,
                "message": "No dimensions to add"
            }
        
        # Check if this is hybrid pricing (has both Entitled and Metered dimensions)
        has_entitled = any("Entitled" in d.get("Types", []) for d in dimensions)
        has_metered = any("Metered" in d.get("Types", []) for d in dimensions)
        is_hybrid = has_entitled and has_metered
        
        # For Usage pricing or hybrid pricing, skip adding dimensions here
        # They will be added as part of pricing terms in the next stage
        if pricing_model == "usage" or is_hybrid:
            # Store the skipped flag in all_data for Stage 4 to check
            if "PRICING_CONFIG" not in self.all_data:
                self.all_data["PRICING_CONFIG"] = {}
            self.all_data["PRICING_CONFIG"]["dimensions_skipped"] = True
            
            model_type = "hybrid" if is_hybrid else "Usage"
            return {
                "success": True,
                "message": f"Skipping dimension addition for {model_type} pricing (will be added with pricing terms)",
                "skipped": True
            }
        
        # For pure Contract pricing, add dimensions now
        result = self.listing_tools.add_dimensions(
            product_id=self.product_id,
            dimensions=dimensions
        )
        
        if result.get("success"):
            change_set_id = result.get("change_set_id")
            if change_set_id:
                self.change_set_ids.append(change_set_id)
        
        return result
    
    def _update_support_terms(self, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update support terms on Offer"""
        
        # Check if we need to retrieve offer_id from pending change set
        if not self.offer_id:
            self.check_pending_changeset()
        
        if not self.offer_id:
            return {
                "success": False,
                "error": "No offer_id available",
                "message": "Offer must be created first. Please wait for Stage 1 to complete."
            }
        
        refund_policy = stage_data.get("refund_policy")
        
        if not refund_policy:
            return {
                "success": False,
                "error": "Refund policy is required"
            }
        
        result = self.listing_tools.update_support_terms(
            offer_id=self.offer_id,
            refund_policy=refund_policy
        )
        
        if result.get("success"):
            change_set_id = result.get("change_set_id")
            if change_set_id:
                self.change_set_ids.append(change_set_id)
        
        return result
    
    def _update_legal_terms(self, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update legal terms on Offer"""
        
        # Check if we need to retrieve offer_id from pending change set
        if not self.offer_id:
            self.check_pending_changeset()
        
        if not self.offer_id:
            return {
                "success": False,
                "error": "No offer_id available",
                "message": "Offer must be created first. Please wait for Stage 1 to complete."
            }
        
        eula_type = stage_data.get("eula_type")
        
        if not eula_type:
            return {
                "success": False,
                "error": "EULA type is required"
            }
        
        # Convert to API format
        if eula_type == "scmp":
            api_eula_type = "StandardEula"
            eula_url = None
        else:  # custom
            api_eula_type = "CustomEula"
            eula_url = stage_data.get("custom_eula_s3_url")
        
        result = self.listing_tools.update_legal_terms(
            offer_id=self.offer_id,
            eula_type=api_eula_type,
            eula_url=eula_url
        )
        
        if result.get("success"):
            change_set_id = result.get("change_set_id")
            if change_set_id:
                self.change_set_ids.append(change_set_id)
        
        return result
    
    def _update_offer_availability(self, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update offer availability"""
        
        # Check if we need to retrieve offer_id from pending change set
        if not self.offer_id:
            self.check_pending_changeset()
        
        if not self.offer_id:
            return {
                "success": False,
                "error": "No offer_id available",
                "message": "Offer must be created first. Please wait for Stage 1 to complete."
            }
        
        availability_type = stage_data.get("availability_type")
        
        if not availability_type:
            return {
                "success": False,
                "error": "Availability type is required"
            }
        
        # Convert to API format
        if availability_type == "all_countries":
            api_type = "all"
            country_codes = None
        elif availability_type == "all_with_exclusions":
            api_type = "exclude"
            country_codes = stage_data.get("excluded_countries", [])
        else:  # allowlist_only
            api_type = "include"
            country_codes = stage_data.get("allowed_countries", [])
        
        result = self.listing_tools.update_offer_availability(
            offer_id=self.offer_id,
            availability_type=api_type,
            country_codes=country_codes
        )
        
        if result.get("success"):
            change_set_id = result.get("change_set_id")
            if change_set_id:
                self.change_set_ids.append(change_set_id)
        
        return result
    
    def _update_offer_targeting(self, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update offer targeting (allowlist)"""
        
        # Check if we need to retrieve offer_id from pending change set
        if not self.offer_id:
            self.check_pending_changeset()
        
        if not self.offer_id:
            return {
                "success": False,
                "error": "No offer_id available",
                "message": "Offer must be created first. Please wait for Stage 1 to complete."
            }
        
        buyer_accounts = stage_data.get("buyer_accounts", [])
        
        # If no accounts specified, skip (public offer)
        if not buyer_accounts:
            return {
                "success": True,
                "message": "No account allowlist specified - offer will be public"
            }
        
        result = self.listing_tools.update_offer_targeting(
            offer_id=self.offer_id,
            buyer_accounts=buyer_accounts
        )
        
        if result.get("success"):
            change_set_id = result.get("change_set_id")
            if change_set_id:
                self.change_set_ids.append(change_set_id)
        
        return result
