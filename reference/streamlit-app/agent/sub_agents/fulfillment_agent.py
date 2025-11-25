"""
Stage 2: Fulfillment Options Agent
Configures SaaS fulfillment URL
"""

from typing import Dict, Any, List
from .base_agent import BaseSubAgent


class FulfillmentAgent(BaseSubAgent):
    """
    Stage 2: Configure Fulfillment Options
    
    Mandatory: Fulfillment URL
    Future: API-based Agents & Tools support
    """
    
    def __init__(self):
        super().__init__(stage_number=2, stage_name="Fulfillment Options")
    
    def get_required_fields(self) -> List[str]:
        return ["fulfillment_url"]
    
    def get_optional_fields(self) -> List[str]:
        return ["quick_launch_enabled", "launch_url"]
    
    def get_field_validations(self) -> Dict[str, Dict[str, Any]]:
        return {
            "fulfillment_url": {
                "type": "string",
                "pattern": r"^https://.*",
                "description": "HTTPS URL where customers register/login (e.g., https://yourapp.com/signup)"
            },
            "quick_launch_enabled": {
                "type": "boolean",
                "description": "Enable Quick Launch feature for faster deployment"
            },
            "launch_url": {
                "type": "string",
                "pattern": r"^https://.*",
                "description": "Launch URL for Quick Launch (required if Quick Launch enabled)"
            }
        }
    
    def get_stage_instructions(self) -> str:
        return """
You are configuring Fulfillment Options for AWS Marketplace SaaS.

REQUIRED:
- Fulfillment URL: Where customers go to register/login after subscribing
  Must be HTTPS URL (e.g., https://yourapp.com/signup)

OPTIONAL:
- Quick Launch: Enables faster deployment (ask if user wants this)
- Launch URL: Required if Quick Launch enabled

VALIDATION:
- URL must start with https://
- URL must be accessible and valid
- If Quick Launch enabled, Launch URL is required

Be brief and clear. This is a simple stage with just one required field.
"""
    
    def process_stage(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process fulfillment configuration"""
        
        if "fulfillment_url" not in self.stage_data:
            return {
                "status": "collecting",
                "message": "What is your fulfillment URL? (Where customers register/login)",
                "hint": "Must be HTTPS URL, e.g., https://yourapp.com/signup",
                "next_question": "fulfillment_url"
            }
        
        # Validate
        errors = self.validate_all_fields(self.stage_data)
        if errors:
            return {
                "status": "error",
                "message": "Please fix the following issues:",
                "errors": errors
            }
        
        # Check Quick Launch
        if "quick_launch_enabled" not in self.stage_data and not context.get("skip_optional"):
            return {
                "status": "collecting_optional",
                "message": "Would you like to enable Quick Launch? (yes/no)",
                "hint": "Quick Launch allows customers to deploy faster with pre-configured templates"
            }
        
        self.is_complete = True
        return {
            "status": "complete",
            "message": "✅ Fulfillment Options configured!",
            "data": self.stage_data
        }
