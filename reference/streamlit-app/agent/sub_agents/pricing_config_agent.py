"""
Stage 3: Pricing Configuration Agent
Configures pricing model and dimensions
"""

from typing import Dict, Any, List
from .base_agent import BaseSubAgent


class PricingConfigAgent(BaseSubAgent):
    """
    Stage 3: Configure Product Pricing
    
    Steps:
    1. Choose pricing model (usage-based, contract-based, contract with consumption)
    2. Select dimension unit types
    3. Create dimensions with API identifiers, display names, descriptions
    """
    
    def __init__(self):
        super().__init__(stage_number=3, stage_name="Pricing Configuration")
        self.pricing_models = {
            "usage": "Usage-based (Pay-as-you-go)",
            "contract": "Contract-based (Upfront commitment)",
            "contract_consumption": "Contract with Consumption (Hybrid)"
        }
        self.dimension_types = {
            "users": "Number of users/seats",
            "api_calls": "API calls/requests",
            "data_gb": "Data storage (GB)",
            "data_tb": "Data storage (TB)",
            "compute_hours": "Compute hours",
            "transactions": "Number of transactions",
            "bandwidth_gb": "Bandwidth (GB)",
            "custom": "Custom dimension"
        }
    
    def get_required_fields(self) -> List[str]:
        return [
            "pricing_model",
            "dimensions"  # Array of dimension objects
        ]
    
    def get_optional_fields(self) -> List[str]:
        return ["free_trial_days"]
    
    def get_field_validations(self) -> Dict[str, Dict[str, Any]]:
        return {
            "pricing_model": {
                "type": "string",
                "enum": ["usage", "contract", "contract_consumption"],
                "description": "Pricing model type"
            },
            "dimensions": {
                "type": "array",
                "min_items": 1,
                "max_items": 24,
                "description": "Pricing dimensions (1-24)"
            },
            "dimension_api_id": {
                "type": "string",
                "pattern": r"^[a-z][a-z0-9_]{0,49}$",
                "min_length": 1,
                "max_length": 50,
                "description": "API identifier (lowercase, alphanumeric, underscores, starts with letter)"
            },
            "dimension_display_name": {
                "type": "string",
                "min_length": 1,
                "max_length": 100,
                "description": "Display name shown to customers"
            },
            "dimension_description": {
                "type": "string",
                "min_length": 10,
                "max_length": 500,
                "description": "Description of what this dimension measures"
            }
        }
    
    def get_stage_instructions(self) -> str:
        return """
You are configuring Pricing for AWS Marketplace SaaS.

STEP 1: Choose Pricing Model
- Usage-based: Pay-as-you-go (metered usage)
- Contract-based: Upfront commitment (annual/monthly)
- Contract with Consumption: Hybrid (commitment + overages)

Explain each model briefly and help user choose.

STEP 2: Select Dimension Types
Common types:
- Users/Seats
- API Calls
- Data Storage (GB/TB)
- Compute Hours
- Transactions
- Bandwidth
- Custom

Help user understand which dimensions fit their product.

STEP 3: Create Dimensions
For each dimension, collect:
1. API Identifier (e.g., "users", "api_calls")
   - Lowercase, alphanumeric, underscores only
   - Starts with letter
   - Max 50 chars
   OR offer to generate from display name

2. Display Name (e.g., "Number of Users")
   - What customers see
   - Max 100 chars

3. Description (e.g., "Number of active users per month")
   - Explains what's measured
   - 10-500 chars

VALIDATION:
- At least 1 dimension required
- Max 24 dimensions
- API IDs must be unique
- API IDs must follow naming rules

Be helpful and educational. Many users are new to marketplace pricing.
"""
    
    def process_stage(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process pricing configuration"""
        
        # Step 1: Choose pricing model
        if "pricing_model" not in self.stage_data:
            return {
                "status": "collecting",
                "message": "Let's configure pricing. Which pricing model fits your product?",
                "options": self.pricing_models,
                "hint": "Choose based on how you want to charge customers",
                "next_question": "pricing_model"
            }
        
        # Step 2: Create dimensions
        if "dimensions" not in self.stage_data:
            self.stage_data["dimensions"] = []
        
        dimensions = self.stage_data["dimensions"]
        
        if len(dimensions) == 0:
            return {
                "status": "collecting",
                "message": "Now let's create pricing dimensions. What do you want to charge for?",
                "dimension_types": self.dimension_types,
                "hint": "Common examples: users, API calls, storage, etc.",
                "next_question": "dimension_type"
            }
        
        # Check if current dimension is complete
        if dimensions and not self._is_dimension_complete(dimensions[-1]):
            return {
                "status": "collecting",
                "message": "Let's complete this dimension.",
                "current_dimension": dimensions[-1],
                "next_question": self._get_next_dimension_field(dimensions[-1])
            }
        
        # Ask if more dimensions needed
        if not context.get("dimensions_complete"):
            return {
                "status": "collecting",
                "message": f"Dimension created! Add another dimension? (You have {len(dimensions)}, max 24)",
                "hint": "Type 'yes' to add more, 'no' to continue",
                "next_question": "add_more_dimensions"
            }
        
        # Validate
        errors = self.validate_all_fields(self.stage_data)
        if errors:
            return {
                "status": "error",
                "message": "Please fix the following issues:",
                "errors": errors
            }
        
        self.is_complete = True
        return {
            "status": "complete",
            "message": f"✅ Pricing configured with {len(dimensions)} dimension(s)!",
            "data": self.stage_data
        }
    
    def _is_dimension_complete(self, dimension: Dict[str, Any]) -> bool:
        """Check if dimension has all required fields"""
        required = ["api_id", "display_name", "description"]
        return all(field in dimension for field in required)
    
    def _get_next_dimension_field(self, dimension: Dict[str, Any]) -> str:
        """Get next field needed for dimension"""
        if "api_id" not in dimension:
            return "api_id"
        if "display_name" not in dimension:
            return "display_name"
        if "description" not in dimension:
            return "description"
        return None
    
    def generate_api_id(self, display_name: str) -> str:
        """Generate API ID from display name"""
        # Convert to lowercase, replace spaces with underscores
        api_id = display_name.lower().replace(" ", "_")
        # Remove non-alphanumeric except underscores
        api_id = "".join(c for c in api_id if c.isalnum() or c == "_")
        # Ensure starts with letter
        if api_id and not api_id[0].isalpha():
            api_id = "dim_" + api_id
        # Truncate to 50 chars
        return api_id[:50]
