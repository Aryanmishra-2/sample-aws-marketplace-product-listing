"""
Stage 4: Price Review Agent
Reviews and configures purchasing options
"""

from typing import Dict, Any, List
from .base_agent import BaseSubAgent


class PriceReviewAgent(BaseSubAgent):
    """Stage 4: Review Prices and Configure Purchasing Options"""
    
    def __init__(self):
        super().__init__(stage_number=4, stage_name="Price Review")
    
    def get_required_fields(self) -> List[str]:
        return ["contract_durations", "multiple_dimension_selection", "quantity_configuration"]
    
    def get_optional_fields(self) -> List[str]:
        return []
    
    def get_field_validations(self) -> Dict[str, Dict[str, Any]]:
        return {
            "purchasing_option": {
                "type": "string",
                "enum": ["multiple_dimensions", "single_dimension"],
                "description": "Multiple dimensions per contract or single dimension"
            },
            "contract_durations": {
                "type": "array",
                "min_items": 1,
                "description": "Contract duration options (e.g., 1 month, 12 months, 24 months)"
            }
        }
    
    def get_stage_instructions(self) -> str:
        return """
You are reviewing pricing and configuring purchasing options.

STEP 1: Explain Purchasing Options
- Multiple Dimensions per Contract: Customers can purchase multiple dimensions in one contract
- Single Dimension per Contract: Each dimension is a separate contract

Help user understand which fits their business model.

STEP 2: Contract Durations
Common options:
- 1 month
- 12 months (1 year)
- 24 months (2 years)
- 36 months (3 years)

User can select one or more durations.

PRICING NOTE:
- Initial prices set to $0.001 USD for testing
- Separate agent will update pricing before going public

Be clear and concise. This is a configuration stage.
"""
    
    def process_stage(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if "purchasing_option" not in self.stage_data:
            return {
                "status": "collecting",
                "message": "How should customers purchase dimensions?",
                "options": {
                    "multiple_dimensions": "Multiple dimensions per contract (bundle)",
                    "single_dimension": "Single dimension per contract (separate)"
                },
                "next_question": "purchasing_option"
            }
        
        if "contract_durations" not in self.stage_data:
            return {
                "status": "collecting",
                "message": "Which contract durations do you want to offer?",
                "options": ["1 month", "12 months", "24 months", "36 months"],
                "hint": "You can select multiple durations",
                "next_question": "contract_durations"
            }
        
        self.is_complete = True
        return {
            "status": "complete",
            "message": "✅ Price review complete! Prices set to $0.001 for testing.",
            "data": self.stage_data
        }
