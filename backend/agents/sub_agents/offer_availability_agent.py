"""
Stage 7: Offer Availability Agent
"""

from typing import Dict, Any, List
from .base_agent import BaseSubAgent


class OfferAvailabilityAgent(BaseSubAgent):
    """Stage 7: Configure Offer Availability"""
    
    def __init__(self):
        super().__init__(stage_number=7, stage_name="Offer Availability")
    
    def get_required_fields(self) -> List[str]:
        return ["availability_type"]
    
    def get_optional_fields(self) -> List[str]:
        return ["excluded_countries", "allowed_countries"]
    
    def get_field_validations(self) -> Dict[str, Dict[str, Any]]:
        return {
            "availability_type": {
                "type": "string",
                "enum": ["all_countries", "all_with_exclusions", "allowlist_only"],
                "description": "Offer availability scope"
            },
            "excluded_countries": {
                "type": "array",
                "description": "Country codes to exclude (ISO 3166-1 alpha-2)"
            },
            "allowed_countries": {
                "type": "array",
                "description": "Country codes to allow (ISO 3166-1 alpha-2)"
            }
        }
    
    def get_stage_instructions(self) -> str:
        return """
You are configuring Offer Availability (geographic restrictions).

OPTIONS:
1. All Countries
   - Available worldwide
   - No restrictions
   - Recommended for most products

2. All Countries with Exclusions
   - Available worldwide except specific countries
   - Useful for compliance/legal restrictions
   - Specify excluded country codes

3. Allowlist Only
   - Only available in specific countries
   - Most restrictive
   - Specify allowed country codes

COUNTRY CODES:
Use ISO 3166-1 alpha-2 codes (e.g., US, GB, DE, JP)

GUIDANCE:
- Most sellers choose "All Countries"
- Consider export restrictions and compliance
- Can be changed later

Be clear and help user understand implications.
"""
    
    def update_availability(self, offer_id: str) -> Dict[str, Any]:
        """
        Update offer availability using the fixed API
        
        IMPORTANT: Availability goes on the Offer, not the Product!
        """
        from ..tools.listing_tools import ListingTools
        
        tools = ListingTools()
        
        availability_type = self.stage_data.get("availability_type")
        
        if availability_type == "all_countries":
            result = tools.update_offer_availability(
                offer_id=offer_id,  # ✅ Correct: offer_id, not product_id
                availability_type="all"
            )
        elif availability_type == "all_with_exclusions":
            result = tools.update_offer_availability(
                offer_id=offer_id,
                availability_type="exclude",
                country_codes=self.stage_data.get("excluded_countries", [])
            )
        else:  # allowlist_only
            result = tools.update_offer_availability(
                offer_id=offer_id,
                availability_type="include",
                country_codes=self.stage_data.get("allowed_countries", [])
            )
        
        return result
    
    def process_stage(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if "availability_type" not in self.stage_data:
            return {
                "status": "collecting",
                "message": "Where should your offer be available?",
                "options": {
                    "all_countries": "All countries (worldwide)",
                    "all_with_exclusions": "All countries except specific ones",
                    "allowlist_only": "Only specific countries"
                },
                "hint": "Most sellers choose 'All countries'",
                "next_question": "availability_type",
                "note": "This will be configured on your Offer (not Product)"
            }
        
        availability = self.stage_data["availability_type"]
        
        if availability == "all_with_exclusions" and "excluded_countries" not in self.stage_data:
            return {
                "status": "collecting",
                "message": "Which countries do you want to exclude?",
                "hint": "Provide country codes (e.g., US, GB, DE) separated by commas",
                "next_question": "excluded_countries"
            }
        
        if availability == "allowlist_only" and "allowed_countries" not in self.stage_data:
            return {
                "status": "collecting",
                "message": "Which countries should be allowed?",
                "hint": "Provide country codes (e.g., US, GB, DE) separated by commas",
                "next_question": "allowed_countries"
            }
        
        errors = self.validate_all_fields(self.stage_data)
        if errors:
            return {"status": "error", "errors": errors}
        
        self.is_complete = True
        return {
            "status": "complete",
            "message": f"✅ Offer availability configured ({availability})!",
            "data": self.stage_data,
            "api_ready": True,  # Ready to call update_availability()
            "api_note": "Use update_availability(offer_id) to apply this to the Offer"
        }
