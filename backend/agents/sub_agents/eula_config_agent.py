"""
Stage 6: EULA Configuration Agent
"""

from typing import Dict, Any, List
from .base_agent import BaseSubAgent


class EULAConfigAgent(BaseSubAgent):
    """Stage 6: Configure EULA"""
    
    def __init__(self):
        super().__init__(stage_number=6, stage_name="EULA Configuration")
    
    def get_required_fields(self) -> List[str]:
        return ["eula_type"]
    
    def get_optional_fields(self) -> List[str]:
        return ["custom_eula_s3_url"]
    
    def get_field_validations(self) -> Dict[str, Dict[str, Any]]:
        return {
            "eula_type": {
                "type": "string",
                "enum": ["scmp", "custom"],
                "description": "EULA type: SCMP or Custom"
            },
            "custom_eula_s3_url": {
                "type": "string",
                "pattern": r"^https://.*\.s3\..*\.amazonaws\.com/.*\.pdf$",
                "description": "S3 URL to custom EULA PDF (required if custom EULA)"
            }
        }
    
    def get_stage_instructions(self) -> str:
        return """
You are configuring the End User License Agreement (EULA).

OPTIONS:
1. Standard Contract for AWS Marketplace (SCMP)
   - AWS's standard terms
   - No additional setup needed
   - Recommended for most sellers

2. Custom EULA
   - Your own license agreement
   - Requires S3 URL to PDF document
   - Must be reviewed by AWS

EXPLAIN THE DIFFERENCE:
- SCMP: Quick, standard, AWS-managed
- Custom: Your terms, requires legal review, more control

If Custom EULA chosen, collect S3 URL to PDF.

VALIDATION:
- Custom EULA must be PDF in S3
- URL must be accessible

Be clear about the implications of each choice.
"""
    
    def update_legal_terms(self, offer_id: str) -> Dict[str, Any]:
        """
        Update legal terms on the Offer using the fixed API
        
        IMPORTANT: Legal terms go on the Offer, not the Product!
        """
        from ..tools.listing_tools import ListingTools
        
        tools = ListingTools()
        
        eula_type = self.stage_data.get("eula_type")
        
        if eula_type == "scmp":
            result = tools.update_legal_terms(
                offer_id=offer_id,  # ✅ Correct: offer_id, not product_id
                eula_type="StandardEula"
            )
        else:  # custom
            result = tools.update_legal_terms(
                offer_id=offer_id,
                eula_type="CustomEula",
                eula_url=self.stage_data.get("custom_eula_s3_url")
            )
        
        return result
    
    def process_stage(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if "eula_type" not in self.stage_data:
            return {
                "status": "collecting",
                "message": "Which EULA type do you want to use?",
                "options": {
                    "scmp": "Standard Contract for AWS Marketplace (SCMP) - Recommended",
                    "custom": "Custom EULA - Your own license agreement"
                },
                "hint": "SCMP is faster and easier. Custom requires legal review.",
                "next_question": "eula_type",
                "note": "This will be added to your Offer (not Product)"
            }
        
        if self.stage_data["eula_type"] == "custom" and "custom_eula_s3_url" not in self.stage_data:
            return {
                "status": "collecting",
                "message": "Please provide the S3 URL to your custom EULA PDF",
                "hint": "Must be S3 URL ending in .pdf",
                "next_question": "custom_eula_s3_url"
            }
        
        errors = self.validate_all_fields(self.stage_data)
        if errors:
            return {"status": "error", "errors": errors}
        
        self.is_complete = True
        return {
            "status": "complete",
            "message": f"✅ EULA configured ({self.stage_data['eula_type'].upper()})!",
            "data": self.stage_data,
            "api_ready": True,  # Ready to call update_legal_terms()
            "api_note": "Use update_legal_terms(offer_id) to apply this to the Offer"
        }
