"""AWS Marketplace Listing Agent"""

from .marketplace_agent_v2 import MarketplaceListingAgentV2

# Alias for backward compatibility
MarketplaceListingAgent = MarketplaceListingAgentV2

__all__ = ["MarketplaceListingAgent", "MarketplaceListingAgentV2"]
