"""
Stage 8: Allowlist Agent
"""

from typing import Dict, Any, List
from .base_agent import BaseSubAgent


class AllowlistAgent(BaseSubAgent):
    """Stage 8: Configure Allowlist (Optional)"""
    
    def __init__(self):
        super().__init__(stage_number=8, stage_name="Allowlist Configuration")
    
    def get_required_fields(self) -> List[str]:
        return []  # This stage is entirely optional
    
    def get_optional_fields(self) -> List[str]:
        return ["allowlist_account_ids"]
    
    def get_field_validations(self) -> Dict[str, Dict[str, Any]]:
        return {
            "allowlist_account_ids": {
                "type": "array",
                "description": "AWS account IDs to allowlist (12-digit numbers)"
            }
        }
    
    def get_stage_instructions(self) -> str:
        return """
You are configuring the Allowlist (optional).

PURPOSE:
- Restrict offer to specific AWS accounts
- Useful for private offers, beta testing, or specific customers
- Completely optional

ACCOUNT IDS:
- 12-digit AWS account numbers
- Comma-separated list
- Example: 123456789012, 987654321098

GUIDANCE:
- Most public offers don't need allowlist
- Use for private/limited offers
- Can be updated later

If user doesn't want allowlist, skip this stage.

Be brief. This is optional and simple.
"""
    
    def process_stage(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if "allowlist_account_ids" not in self.stage_data and not context.get("skip_allowlist"):
            return {
                "status": "collecting",
                "message": "Do you want to allowlist specific AWS accounts? (optional)",
                "hint": "Type account IDs separated by commas, or 'skip' to skip",
                "next_question": "allowlist_account_ids"
            }
        
        # Validate if provided
        if "allowlist_account_ids" in self.stage_data:
            errors = self.validate_all_fields(self.stage_data)
            if errors:
                return {"status": "error", "errors": errors}
        
        self.is_complete = True
        
        if "allowlist_account_ids" in self.stage_data and self.stage_data["allowlist_account_ids"]:
            count = len(self.stage_data["allowlist_account_ids"])
            return {
                "status": "complete",
                "message": f"✅ Allowlist configured with {count} account(s)!",
                "data": self.stage_data
            }
        else:
            return {
                "status": "complete",
                "message": "✅ No allowlist configured (public offer).",
                "data": {}
            }
