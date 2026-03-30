# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
Tools for completing stages with collected data
"""

from typing import Dict, Any, List


def set_product_information(
    product_title: str,
    short_description: str,
    long_description: str,
    logo_s3_url: str,
    highlights: List[str],
    categories: List[str],
    search_keywords: List[str],
    support_email: str,
    support_description: str,
    sku: str = None,
    video_urls: List[str] = None
) -> Dict[str, Any]:
    """
    Set all product information for Stage 1 at once
    
    This tool should be called by the LLM when it has extracted all required
    product information from the user's messages.
    
    Args:
        product_title: Product name (5-255 characters)
        short_description: Brief description (10-500 characters)
        long_description: Detailed description (50-5000 characters)
        logo_s3_url: S3 URL to logo PNG/JPG
        highlights: List of 1-10 key features (5-250 chars each)
        categories: List of 1-3 AWS Marketplace categories
        search_keywords: List of 1-10 keywords (max 50 chars each)
        support_email: Support contact email
        support_description: Description of support offerings (20-2000 chars)
        sku: Optional SKU
        video_urls: Optional list of video URLs
        
    Returns:
        Dict with success status and message
    """
    # This is a placeholder - the actual implementation will be in the runtime
    # The runtime will call orchestrator.set_stage_data() for each field
    
    return {
        "success": True,
        "message": "Product information set successfully. Ready to create product.",
        "fields_set": [
            "product_title",
            "short_description", 
            "long_description",
            "logo_s3_url",
            "highlights",
            "categories",
            "search_keywords",
            "support_email",
            "support_description"
        ]
    }


def complete_stage_1() -> Dict[str, Any]:
    """
    Complete Stage 1 and create the product in AWS Marketplace
    
    This should be called after set_product_information() to trigger
    the actual product creation.
    
    Returns:
        Dict with product_id, offer_id, and status
    """
    # This is a placeholder - the actual implementation will be in the runtime
    # The runtime will call orchestrator.complete_current_stage()
    
    return {
        "success": True,
        "message": "Stage 1 completion triggered. Creating product in AWS Marketplace...",
        "note": "This will create the product and return product_id and offer_id"
    }
