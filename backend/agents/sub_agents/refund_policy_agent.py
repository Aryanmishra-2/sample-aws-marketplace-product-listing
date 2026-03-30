# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
Stage 5: Refund Policy Agent
"""

from typing import Dict, Any, List
from .base_agent import BaseSubAgent


class RefundPolicyAgent(BaseSubAgent):
    """Stage 5: Specify Refund Policy"""
    
    def __init__(self):
        super().__init__(stage_number=5, stage_name="Refund Policy")
    
    def get_required_fields(self) -> List[str]:
        return ["refund_policy"]
    
    def get_optional_fields(self) -> List[str]:
        return []
    
    def get_field_validations(self) -> Dict[str, Dict[str, Any]]:
        return {
            "refund_policy": {
                "type": "string",
                "min_length": 50,
                "max_length": 5000,
                "description": "Refund policy for customers"
            }
        }
    
    def get_stage_instructions(self) -> str:
        return """
You are collecting the Refund Policy.

REQUIRED:
- Refund Policy (50-5000 characters)
  Clear statement of refund terms and conditions

GUIDANCE:
- Be clear about refund eligibility
- Specify timeframes (e.g., "30-day money-back guarantee")
- Explain the refund process
- Include any exceptions or limitations

EXAMPLE:
"We offer a 30-day money-back guarantee. If you're not satisfied, contact support@example.com 
within 30 days of purchase for a full refund. Refunds are processed within 5-7 business days."

Be brief. Just collect the policy text.
"""
    
    def update_support_terms(self, offer_id: str) -> Dict[str, Any]:
        """
        Update support terms on the Offer using the fixed API
        
        IMPORTANT: Support terms go on the Offer, not the Product!
        """
        from ..tools.listing_tools import ListingTools
        
        tools = ListingTools()
        
        result = tools.update_support_terms(
            offer_id=offer_id,  # ✅ Correct: offer_id, not product_id
            refund_policy=self.stage_data.get("refund_policy")
        )
        
        return result
    
    def process_stage(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if "refund_policy" not in self.stage_data:
            return {
                "status": "collecting",
                "message": "What is your refund policy?",
                "hint": "Provide clear refund terms (50-5000 characters)",
                "next_question": "refund_policy",
                "note": "This will be added to your Offer (not Product)"
            }
        
        errors = self.validate_all_fields(self.stage_data)
        if errors:
            return {"status": "error", "errors": errors}
        
        self.is_complete = True
        return {
            "status": "complete",
            "message": "✅ Refund policy configured!",
            "data": self.stage_data,
            "api_ready": True,  # Ready to call update_support_terms()
            "api_note": "Use update_support_terms(offer_id) to apply this to the Offer"
        }
