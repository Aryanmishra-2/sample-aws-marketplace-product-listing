#!/usr/bin/env python3
"""
AWS Marketplace Seller Registration - Integration Examples

This file demonstrates how to integrate the seller registration module
with various types of agents and applications.
"""

import sys
import os
from typing import Dict, Any, Optional

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from seller_registration_module import SellerRegistrationModule, quick_seller_check, is_seller_registered


# ==================== EXAMPLE 1: SIMPLE AGENT INTEGRATION ====================

class MarketplaceListingAgent:
    """
    Example: Marketplace listing agent that needs seller registration
    """
    
    def __init__(self):
        # Integrate seller registration module
        self.seller_registration = SellerRegistrationModule()
        self.name = "Marketplace Listing Agent"
    
    def create_listing(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a marketplace listing (requires seller registration)"""
        
        # Step 1: Check if seller is registered
        if not self.seller_registration.is_seller_registered():
            return {
                "success": False,
                "error": "Seller registration required",
                "message": "You must be registered as an AWS Marketplace seller before creating listings",
                "next_action": self.seller_registration.get_next_action(),
                "registration_status": self.seller_registration.check_seller_status()
            }
        
        # Step 2: Proceed with listing creation
        print(f"✅ Seller registration verified. Creating listing...")
        return {
            "success": True,
            "message": "Listing created successfully",
            "listing_id": "listing-12345"
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status including seller registration"""
        seller_status = self.seller_registration.check_seller_status()
        
        return {
            "agent_name": self.name,
            "seller_registered": self.seller_registration.is_seller_registered(),
            "seller_status": seller_status.get("seller_status", "Unknown"),
            "account_id": seller_status.get("account_id", "Unknown"),
            "ready_for_listings": self.seller_registration.is_seller_registered()
        }


# ==================== EXAMPLE 2: CHATBOT INTEGRATION ====================

class MarketplaceChatbot:
    """
    Example: Chatbot that helps users with marketplace operations
    """
    
    def __init__(self):
        self.seller_registration = SellerRegistrationModule()
        self.conversation_history = []
    
    def handle_user_message(self, message: str) -> str:
        """Handle user messages and provide appropriate responses"""
        
        message_lower = message.lower()
        
        # Check for seller registration related queries
        if any(keyword in message_lower for keyword in ["register", "seller", "marketplace", "status"]):
            return self._handle_seller_registration_query(message)
        
        # Check for listing creation queries
        elif any(keyword in message_lower for keyword in ["create", "listing", "product", "publish"]):
            return self._handle_listing_query(message)
        
        else:
            return "I can help you with AWS Marketplace seller registration and listing creation. What would you like to know?"
    
    def _handle_seller_registration_query(self, message: str) -> str:
        """Handle seller registration related queries"""
        
        # Check current status
        status = self.seller_registration.check_seller_status()
        
        if status.get("seller_status") == "APPROVED":
            return f"✅ Great news! Your AWS account ({status.get('account_id')}) is already registered as a marketplace seller. You can proceed with creating listings."
        
        elif status.get("seller_status") == "PENDING":
            return f"⏳ Your seller registration is currently under review by AWS. This typically takes 2-3 business days. Please check back later."
        
        else:
            requirements = self.seller_registration.get_registration_requirements()
            return f"📋 You need to register as an AWS Marketplace seller first. The process involves {len(requirements.get('workflow_steps', {}))} steps and typically takes 1-2 hours of your time plus 2-3 days for AWS review. Would you like me to guide you through the process?"
    
    def _handle_listing_query(self, message: str) -> str:
        """Handle listing creation queries"""
        
        if not self.seller_registration.is_seller_registered():
            return f"❌ You need to be registered as an AWS Marketplace seller before creating listings. {self.seller_registration.get_next_action()}"
        
        return "✅ You're registered as a seller! I can help you create marketplace listings. What type of product would you like to list?"


# ==================== EXAMPLE 3: WORKFLOW ORCHESTRATOR ====================

class MarketplaceWorkflowOrchestrator:
    """
    Example: Orchestrator that manages complex marketplace workflows
    """
    
    def __init__(self):
        self.seller_registration = SellerRegistrationModule()
        self.workflows = {}
    
    def start_marketplace_workflow(self, workflow_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Start a marketplace workflow with seller registration check"""
        
        workflow_id = f"workflow-{len(self.workflows) + 1}"
        
        # Step 1: Always check seller registration first
        seller_check = self._ensure_seller_registered()
        if not seller_check["success"]:
            return {
                "success": False,
                "workflow_id": workflow_id,
                "blocked_by": "seller_registration",
                "message": seller_check["message"],
                "next_action": seller_check["next_action"]
            }
        
        # Step 2: Proceed with specific workflow
        if workflow_type == "create_listing":
            return self._start_listing_workflow(workflow_id, data)
        elif workflow_type == "update_pricing":
            return self._start_pricing_workflow(workflow_id, data)
        else:
            return {
                "success": False,
                "error": f"Unknown workflow type: {workflow_type}"
            }
    
    def _ensure_seller_registered(self) -> Dict[str, Any]:
        """Ensure seller is registered before proceeding"""
        
        if self.seller_registration.is_seller_registered():
            return {
                "success": True,
                "message": "Seller registration verified"
            }
        
        return {
            "success": False,
            "message": "Seller registration required before proceeding",
            "next_action": self.seller_registration.get_next_action(),
            "registration_progress": self.seller_registration.get_registration_progress()
        }
    
    def _start_listing_workflow(self, workflow_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Start listing creation workflow"""
        
        self.workflows[workflow_id] = {
            "type": "create_listing",
            "status": "in_progress",
            "data": data,
            "steps_completed": ["seller_verification"]
        }
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "message": "Listing creation workflow started",
            "next_step": "product_information"
        }
    
    def _start_pricing_workflow(self, workflow_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Start pricing update workflow"""
        
        self.workflows[workflow_id] = {
            "type": "update_pricing",
            "status": "in_progress", 
            "data": data,
            "steps_completed": ["seller_verification"]
        }
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "message": "Pricing update workflow started",
            "next_step": "pricing_validation"
        }


# ==================== EXAMPLE 4: MICROSERVICE INTEGRATION ====================

class MarketplaceMicroservice:
    """
    Example: Microservice that provides marketplace operations via API
    """
    
    def __init__(self):
        self.seller_registration = SellerRegistrationModule()
    
    def health_check(self) -> Dict[str, Any]:
        """Health check endpoint that includes seller registration status"""
        
        try:
            # Check AWS connectivity and seller status
            account_info = self.seller_registration.get_account_info()
            seller_status = self.seller_registration.check_seller_status()
            
            return {
                "service": "marketplace-microservice",
                "status": "healthy",
                "aws_connectivity": account_info.get("success", False),
                "seller_registered": self.seller_registration.is_seller_registered(),
                "seller_status": seller_status.get("seller_status", "Unknown"),
                "account_id": account_info.get("account_id", "Unknown"),
                "timestamp": account_info.get("timestamp")
            }
            
        except Exception as e:
            return {
                "service": "marketplace-microservice",
                "status": "unhealthy",
                "error": str(e),
                "aws_connectivity": False,
                "seller_registered": False
            }
    
    def create_listing_endpoint(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """API endpoint for creating listings"""
        
        # Validate seller registration
        if not self.seller_registration.is_seller_registered():
            return {
                "success": False,
                "error_code": "SELLER_NOT_REGISTERED",
                "message": "Seller registration required",
                "registration_info": {
                    "status": self.seller_registration.check_seller_status(),
                    "next_action": self.seller_registration.get_next_action(),
                    "help_resources": self.seller_registration.get_help_resources()
                }
            }
        
        # Process listing creation
        return {
            "success": True,
            "message": "Listing creation initiated",
            "listing_id": "listing-api-12345"
        }


# ==================== EXAMPLE 5: DECORATOR PATTERN ====================

def requires_seller_registration(func):
    """
    Decorator that ensures seller registration before executing a function
    """
    def wrapper(*args, **kwargs):
        # Get the instance (assumes first argument is self)
        instance = args[0] if args else None
        
        # Check if instance has seller registration module
        if hasattr(instance, 'seller_registration'):
            seller_reg = instance.seller_registration
        else:
            # Create a temporary module for checking
            seller_reg = SellerRegistrationModule()
        
        # Check seller registration
        if not seller_reg.is_seller_registered():
            return {
                "success": False,
                "error": "Seller registration required",
                "message": f"Function '{func.__name__}' requires seller registration",
                "next_action": seller_reg.get_next_action(),
                "registration_status": seller_reg.check_seller_status()
            }
        
        # Execute the original function
        return func(*args, **kwargs)
    
    return wrapper


class DecoratedMarketplaceAgent:
    """
    Example: Agent using decorator pattern for seller registration
    """
    
    def __init__(self):
        self.seller_registration = SellerRegistrationModule()
    
    @requires_seller_registration
    def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a product (requires seller registration)"""
        return {
            "success": True,
            "message": "Product created successfully",
            "product_id": "prod-12345"
        }
    
    @requires_seller_registration
    def update_pricing(self, pricing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update pricing (requires seller registration)"""
        return {
            "success": True,
            "message": "Pricing updated successfully"
        }


# ==================== EXAMPLE 6: PLUGIN ARCHITECTURE ====================

class MarketplaceAgentWithPlugins:
    """
    Example: Agent with plugin architecture that includes seller registration
    """
    
    def __init__(self):
        self.plugins = {}
        self.load_seller_registration_plugin()
    
    def load_seller_registration_plugin(self):
        """Load seller registration as a plugin"""
        
        seller_reg = SellerRegistrationModule()
        
        # Add as plugin
        self.plugins['seller_registration'] = {
            'module': seller_reg,
            'methods': seller_reg.create_agent_tool_methods(),
            'version': seller_reg.version,
            'capabilities': seller_reg.get_module_info()['capabilities']
        }
        
        # Add methods to agent
        for method_name, method_func in self.plugins['seller_registration']['methods'].items():
            setattr(self, method_name, method_func)
    
    def list_plugins(self) -> Dict[str, Any]:
        """List all loaded plugins"""
        return {
            plugin_name: {
                'version': plugin_info.get('version', 'Unknown'),
                'capabilities': plugin_info.get('capabilities', [])
            }
            for plugin_name, plugin_info in self.plugins.items()
        }
    
    def execute_with_plugins(self, operation: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute operation with plugin support"""
        
        # Check seller registration via plugin
        if hasattr(self, 'is_seller_registered') and not self.is_seller_registered():
            return {
                "success": False,
                "error": "Seller registration required",
                "next_action": self.get_next_action() if hasattr(self, 'get_next_action') else "Register as seller"
            }
        
        # Execute operation
        return {
            "success": True,
            "message": f"Operation '{operation}' executed successfully",
            "plugins_used": list(self.plugins.keys())
        }


# ==================== TESTING AND EXAMPLES ====================

def run_integration_examples():
    """Run all integration examples"""
    
    print("🚀 AWS Marketplace Seller Registration - Integration Examples")
    print("=" * 70)
    
    # Example 1: Simple Agent
    print("\n📋 Example 1: Simple Agent Integration")
    listing_agent = MarketplaceListingAgent()
    status = listing_agent.get_status()
    print(f"Agent: {status['agent_name']}")
    print(f"Seller Registered: {status['seller_registered']}")
    print(f"Ready for Listings: {status['ready_for_listings']}")
    
    # Example 2: Chatbot
    print("\n📋 Example 2: Chatbot Integration")
    chatbot = MarketplaceChatbot()
    response = chatbot.handle_user_message("What's my seller registration status?")
    print(f"Chatbot Response: {response[:100]}...")
    
    # Example 3: Workflow Orchestrator
    print("\n📋 Example 3: Workflow Orchestrator")
    orchestrator = MarketplaceWorkflowOrchestrator()
    workflow_result = orchestrator.start_marketplace_workflow("create_listing", {"product": "test"})
    print(f"Workflow Success: {workflow_result.get('success', False)}")
    
    # Example 4: Microservice
    print("\n📋 Example 4: Microservice Integration")
    microservice = MarketplaceMicroservice()
    health = microservice.health_check()
    print(f"Service Status: {health['status']}")
    print(f"AWS Connectivity: {health['aws_connectivity']}")
    
    # Example 5: Decorator Pattern
    print("\n📋 Example 5: Decorator Pattern")
    decorated_agent = DecoratedMarketplaceAgent()
    result = decorated_agent.create_product({"name": "Test Product"})
    print(f"Product Creation: {result.get('success', False)}")
    
    # Example 6: Plugin Architecture
    print("\n📋 Example 6: Plugin Architecture")
    plugin_agent = MarketplaceAgentWithPlugins()
    plugins = plugin_agent.list_plugins()
    print(f"Loaded Plugins: {list(plugins.keys())}")
    
    print("\n✅ All integration examples completed!")


if __name__ == "__main__":
    run_integration_examples()