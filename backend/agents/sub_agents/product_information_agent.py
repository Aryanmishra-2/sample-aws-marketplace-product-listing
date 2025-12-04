"""
Stage 1: Product Information Agent
Collects product details, descriptions, and metadata
"""

from typing import Dict, Any, List
from .base_agent import BaseSubAgent


class ProductInformationAgent(BaseSubAgent):
    """
    Stage 1: Collect Product Information

    Mandatory: Product Title, Logo S3 URL, Short Description, Long Description,
               Highlight 1, Support Details, Categories, Keywords
    Optional: SKU, Video URL, Highlights 2-3, Learning Resources, Assets
    """

    def __init__(self):
        super().__init__(stage_number=1, stage_name="Product Information")

    def get_required_fields(self) -> List[str]:
        return [
            "product_title",
            "logo_s3_url",
            "short_description",
            "long_description",
            "highlights",  # Changed: Now a single array field
            "support_email",
            "support_description",
            "categories",
            "search_keywords",
        ]

    def get_optional_fields(self) -> List[str]:
        return [
            "sku",
            "video_urls",  # Changed: Now an array
            "learning_resources",
            "additional_resources",
        ]

    def get_field_validations(self) -> Dict[str, Dict[str, Any]]:
        """AWS Marketplace field validation rules"""
        return {
            "product_title": {
                "type": "string",
                "min_length": 5,
                "max_length": 255,
                "description": "Product name displayed in AWS Marketplace",
            },
            "logo_s3_url": {
                "type": "string",
                "pattern": r"^https://[^/]+\.s3[.-][^/]*amazonaws\.com/.*\.(png|jpg|jpeg)$",
                "description": "S3 URL to product logo (PNG/JPG, min 110x110px, max 5MB)",
            },
            "short_description": {
                "type": "string",
                "min_length": 10,
                "max_length": 500,
                "description": "Brief product description for search results",
            },
            "long_description": {
                "type": "string",
                "min_length": 50,
                "max_length": 5000,
                "description": "Detailed product description with features and benefits",
            },
            "highlights": {
                "type": "array",
                "min_items": 1,
                "max_items": 10,
                "item_min_length": 5,
                "item_max_length": 250,
                "description": "Product highlights (1-10 items, 5-250 chars each)",
            },
            "support_email": {
                "type": "string",
                "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                "description": "Support contact email",
            },
            "support_description": {
                "type": "string",
                "min_length": 20,
                "max_length": 2000,
                "description": "Description of support offerings",
            },
            "categories": {
                "type": "array",
                "min_items": 1,
                "max_items": 3,
                "description": "AWS Marketplace categories (1-3)",
            },
            "search_keywords": {
                "type": "array",
                "min_items": 1,
                "max_items": 10,
                "description": "Keywords for marketplace search (1-10, max 50 chars each)",
            },
            "sku": {
                "type": "string",
                "max_length": 50,
                "description": "Stock Keeping Unit (optional)",
            },
            "video_urls": {
                "type": "array",
                "max_items": 5,
                "item_pattern": r"^https://.*",
                "description": "URLs to product demo videos (max 5)",
            },
        }

    def get_stage_instructions(self) -> str:
        return """
You are collecting Product Information for an AWS Marketplace SaaS listing.

Your goal: Gather all required product details efficiently in ONE REQUEST.

REQUIRED FIELDS (collect all at once):
1. Product Title (5-255 chars)
2. Logo S3 URL (must be S3 URL to PNG/JPG)
3. Short Description (10-500 chars) - for search results
4. Long Description (50-5000 chars) - detailed features
5. Highlights (3-5 recommended, 5-250 chars each) - key features as bullet points
6. Support Email (valid email)
7. Support Description (20-2000 chars)
8. Categories (1-3 categories from AWS Marketplace)
9. Search Keywords (1-10 keywords, max 50 chars each)

OPTIONAL FIELDS (ask if user wants to provide):
- SKU
- Video URLs (array of video links)
- Learning Resources
- Additional Resources

IMPORTANT INSTRUCTIONS:
1. **ASK FOR ALL REQUIRED FIELDS IN ONE MESSAGE** - Don't ask one at a time!
2. Present them as a clear list or form
3. Highlights should be collected as bullet points (will be converted to array)
4. Validate all inputs after receiving them
5. If any field is invalid, ask user to fix only those fields
6. Once all required fields are valid, ask about optional fields
7. Confirm all data with user before completing

EXAMPLE PROMPT:
"Please provide the following information for your SaaS product:

**Product Title:** 
**Logo S3 URL:** 
**Short Description:** 
**Long Description:** 
**Highlights (3-5 key features):**
- 
- 
- 
**Support Email:** 
**Support Description:** 
**Categories (1-3):** 
**Search Keywords (1-10):** 

You can provide all of this at once, or we can go through it step by step if you prefer."

VALIDATION:
- Check field lengths
- Validate URLs (must be HTTPS for S3)
- Validate email format
- Ensure S3 URLs are properly formatted
- Check array sizes (categories, keywords, highlights)

Be efficient - collect everything at once to save time!
"""

    def create_product_draft(self) -> Dict[str, Any]:
        """
        Create product draft using the collected information

        Uses the fixed API with highlights properly included
        """
        from ..tools.listing_tools import ListingTools

        tools = ListingTools()

        # Prepare data for API call
        result = tools.create_listing_draft(
            product_title=self.stage_data.get("product_title"),
            short_description=self.stage_data.get("short_description"),
            long_description=self.stage_data.get("long_description"),
            logo_url=self.stage_data.get("logo_s3_url"),
            categories=self.stage_data.get("categories", []),
            search_keywords=self.stage_data.get("search_keywords", []),
            highlights=self.stage_data.get("highlights", []),  # ✅ Now included
            video_urls=self.stage_data.get("video_urls", []),
            additional_resources=[],  # Can be populated from optional fields
        )

        return result

    def process_stage(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process user input for product information stage"""

        # Extract data from user input (simplified - in real implementation, use NLP/LLM)
        # This is a placeholder - the actual implementation will use the LLM to extract data

        # Check what's missing
        required = self.get_required_fields()
        missing_required = [f for f in required if f not in self.stage_data]

        if missing_required:
            # First time - ask for ALL required fields at once
            if len(missing_required) == len(required):
                return {
                    "status": "collecting",
                    "message": """Please provide all the following information for your SaaS product:

**Required Information:**

1. **Product Title** (5-255 characters)
2. **Logo S3 URL** (S3 URL to PNG/JPG image)
3. **Short Description** (10-500 characters) - Brief description for search results
4. **Long Description** (50-5000 characters) - Detailed product description
5. **Highlights** (3-5 key features, 5-250 characters each):
   - Feature 1
   - Feature 2
   - Feature 3
6. **Support Email** (valid email address)
7. **Support Description** (20-2000 characters) - How you provide support
8. **Categories** (1-3 AWS Marketplace categories)
9. **Search Keywords** (1-10 keywords, max 50 characters each)

You can provide all of this information at once, or we can go through it step by step if you prefer.

What would you like to do?""",
                    "hint": "Provide all fields at once to save time, or say 'step by step' to go through each field individually",
                    "all_required_fields": required,
                    "progress": "0/9 required fields collected",
                }

            # Some fields collected - ask for remaining
            return {
                "status": "collecting",
                "message": f"Still need the following fields:\n\n"
                + "\n".join(
                    [f"- {f.replace('_', ' ').title()}" for f in missing_required]
                ),
                "hint": "Please provide the missing information",
                "missing_fields": missing_required,
                "progress": f"{len(required) - len(missing_required)}/{len(required)} required fields collected",
            }

        # All required fields collected
        optional = self.get_optional_fields()
        missing_optional = [f for f in optional if f not in self.stage_data]

        if missing_optional and not context.get("skip_optional"):
            return {
                "status": "collecting_optional",
                "message": "✅ All required fields collected!\n\nWould you like to add optional information?\n\n**Optional Fields:**\n- SKU\n- Video URLs\n- Learning Resources\n- Additional Resources",
                "optional_fields": missing_optional,
                "hint": "Say 'yes' to add optional fields, or 'skip' to continue",
            }

        # Validate all data
        errors = self.validate_all_fields(self.stage_data)

        if errors:
            return {
                "status": "error",
                "message": "Please fix the following issues:",
                "errors": errors,
            }

        # Stage complete
        self.is_complete = True
        return {
            "status": "complete",
            "message": "✅ Product Information stage complete!",
            "data": self.stage_data,
            "summary": self.get_progress_summary(),
            "api_ready": True,  # Indicates data is ready for API call
        }
