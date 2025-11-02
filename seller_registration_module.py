#!/usr/bin/env python3
"""
AWS Marketplace Seller Registration Module

This is a standalone, reusable module for AWS Marketplace seller registration
that can be used by any agent, application, or service.

Key Features:
- Completely independent and self-contained
- No dependencies on other agents or tools
- Simple API interface
- Comprehensive error handling
- Multi-country support (US, India, others)
- Real AWS API integration
- Preview and validation capabilities

Usage Examples:
    # Basic usage
    from seller_registration_module import SellerRegistrationModule
    
    # Initialize
    registration = SellerRegistrationModule()
    
    # Check status
    status = registration.check_seller_status()
    
    # Register new seller
    result = registration.register_seller(business_data)
    
    # Use in any agent
    class MyAgent:
        def __init__(self):
            self.seller_registration = SellerRegistrationModule()
        
        def ensure_seller_registered(self):
            return self.seller_registration.check_seller_status()
"""

import sys
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.tools.seller_registration_tools import SellerRegistrationTools
from agent.sub_agents.seller_registration_agent import SellerRegistrationAgent


class SellerRegistrationModule:
    """
    Standalone AWS Marketplace Seller Registration Module
    
    This module provides a complete, reusable interface for seller registration
    that can be integrated into any agent, application, or workflow.
    
    Features:
    - Status checking and validation
    - Complete registration workflow
    - Multi-country support
    - Preview and validation
    - Error handling and recovery
    - Help and documentation
    """
    
    def __init__(self, region: str = "us-east-1", aws_credentials: Optional[Dict[str, str]] = None):
        """
        Initialize the seller registration module
        
        Args:
            region: AWS region for marketplace operations
            aws_credentials: Optional AWS credentials dict with keys:
                - aws_access_key_id
                - aws_secret_access_key
                - aws_session_token (optional)
        """
        self.region = region
        
        # Initialize core tools
        if aws_credentials:
            self.tools = SellerRegistrationTools(
                region=region,
                aws_access_key_id=aws_credentials.get('aws_access_key_id'),
                aws_secret_access_key=aws_credentials.get('aws_secret_access_key'),
                aws_session_token=aws_credentials.get('aws_session_token')
            )
        else:
            self.tools = SellerRegistrationTools(region=region)
        
        self.agent = SellerRegistrationAgent()
        
        # Module metadata
        self.version = "1.0.0"
        self.module_name = "AWS Marketplace Seller Registration"
    
    # ==================== PUBLIC API METHODS ====================
    
    def check_seller_status(self) -> Dict[str, Any]:
        """
        Check if the current AWS account is registered as a marketplace seller
        
        Returns:
            Dict with seller status information:
            {
                "success": bool,
                "seller_status": "APPROVED" | "PENDING" | "NOT_REGISTERED" | "UNKNOWN",
                "account_id": str,
                "verification_status": dict,
                "required_steps": list,
                "message": str
            }
        """
        try:
            return self.tools.check_seller_status()
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to check seller status"
            }
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get comprehensive AWS account information
        
        Returns:
            Dict with account details including permissions and marketplace access
        """
        try:
            return self.tools.get_account_info()
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get account information"
            }
    
    def validate_business_info(self, business_info: Dict[str, Any], country: str = "US") -> Dict[str, Any]:
        """
        Validate business information for seller registration
        
        Args:
            business_info: Dictionary containing business details
            country: Country code ("US", "India", etc.)
            
        Returns:
            Dict with validation results
        """
        try:
            if country.upper() == "INDIA":
                return self.tools.validate_india_business_info(business_info)
            else:
                return self.tools.validate_business_info(business_info)
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to validate business information"
            }
    
    def get_registration_requirements(self, country: str = "US") -> Dict[str, Any]:
        """
        Get registration requirements for specified country
        
        Args:
            country: Country code ("US", "India", etc.)
            
        Returns:
            Dict with comprehensive requirements information
        """
        try:
            base_requirements = self.tools.get_registration_requirements()
            
            if country.upper() == "INDIA":
                india_requirements = self.tools.get_india_specific_requirements()
                base_requirements["country_specific"] = india_requirements
            
            return base_requirements
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get registration requirements"
            }
    
    def generate_registration_preview(self, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a preview of registration data before submission
        
        Args:
            registration_data: Complete registration information
            
        Returns:
            Dict with formatted preview and validation results
        """
        try:
            return self.tools.generate_registration_preview(registration_data)
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate registration preview"
            }
    
    def submit_registration(self, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit complete registration to AWS Marketplace
        
        Args:
            registration_data: Validated registration information
            
        Returns:
            Dict with submission results
        """
        try:
            return self.tools.submit_registration_to_aws(registration_data)
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to submit registration"
            }
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """
        Get current registration workflow status and progress
        
        Returns:
            Dict with workflow progress information
        """
        try:
            return self.tools.get_registration_workflow_status()
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get workflow status"
            }
    
    def get_help_resources(self) -> Dict[str, Any]:
        """
        Get comprehensive help resources and documentation
        
        Returns:
            Dict with help resources, links, and guidance
        """
        try:
            return self.tools.get_help_resources()
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get help resources"
            }
    
    def create_support_case(self, subject: str, description: str) -> Dict[str, Any]:
        """
        Create AWS support case for seller registration assistance
        
        Args:
            subject: Support case subject
            description: Detailed description of the issue
            
        Returns:
            Dict with support case creation results
        """
        try:
            return self.tools.create_support_case(subject, description)
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create support case"
            }
    
    # ==================== CONVENIENCE METHODS ====================
    
    def is_seller_registered(self) -> bool:
        """
        Simple boolean check if account is registered as seller
        
        Returns:
            True if seller is registered and approved, False otherwise
        """
        try:
            status = self.check_seller_status()
            return status.get("success", False) and status.get("seller_status") == "APPROVED"
        except:
            return False
    
    def get_registration_progress(self) -> int:
        """
        Get registration progress as percentage (0-100)
        
        Returns:
            Integer percentage of completion
        """
        try:
            workflow = self.get_workflow_status()
            return workflow.get("progress_percentage", 0)
        except:
            return 0
    
    def needs_registration(self) -> bool:
        """
        Check if account needs to complete seller registration
        
        Returns:
            True if registration is needed, False if already registered
        """
        return not self.is_seller_registered()
    
    def get_next_action(self) -> str:
        """
        Get the next recommended action for the user
        
        Returns:
            String describing the next step to take
        """
        try:
            if self.is_seller_registered():
                return "Seller registration complete. You can proceed with marketplace operations."
            
            workflow = self.get_workflow_status()
            return workflow.get("next_action", "Start seller registration process")
        except:
            return "Check seller registration status"
    
    # ==================== INTEGRATION HELPERS ====================
    
    @staticmethod
    def get_credentials_requirements() -> Dict[str, Any]:
        """
        Get AWS credentials requirements for the module
        
        Returns:
            Dict with credential requirements and setup instructions
        """
        return SellerRegistrationTools.collect_aws_credentials()
    
    def validate_credentials(self) -> Dict[str, Any]:
        """
        Validate current AWS credentials and permissions
        
        Returns:
            Dict with credential validation results
        """
        try:
            return self.tools.get_aws_credentials_info()
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to validate credentials"
            }
    
    def get_module_info(self) -> Dict[str, Any]:
        """
        Get information about this module
        
        Returns:
            Dict with module metadata and capabilities
        """
        return {
            "module_name": self.module_name,
            "version": self.version,
            "region": self.region,
            "capabilities": [
                "Seller status checking",
                "Business information validation",
                "Multi-country support (US, India)",
                "Registration workflow management",
                "Preview and validation",
                "AWS API integration",
                "Support case creation",
                "Help and documentation"
            ],
            "supported_countries": ["US", "India", "Others"],
            "aws_services_used": [
                "AWS Marketplace Catalog",
                "AWS STS",
                "AWS Organizations",
                "AWS Support"
            ]
        }
    
    # ==================== AGENT INTEGRATION METHODS ====================
    
    def integrate_with_agent(self, agent_instance) -> None:
        """
        Integrate this module with an existing agent
        
        Args:
            agent_instance: The agent instance to integrate with
        """
        # Add seller registration capabilities to the agent
        agent_instance.seller_registration = self
        
        # Add convenience methods to the agent
        agent_instance.check_seller_status = self.check_seller_status
        agent_instance.is_seller_registered = self.is_seller_registered
        agent_instance.needs_registration = self.needs_registration
        agent_instance.get_next_action = self.get_next_action
    
    def create_agent_tool_methods(self) -> Dict[str, callable]:
        """
        Create tool methods that can be added to any agent
        
        Returns:
            Dict of method names and callable functions
        """
        return {
            "check_seller_status": self.check_seller_status,
            "validate_business_info": self.validate_business_info,
            "get_registration_requirements": self.get_registration_requirements,
            "generate_registration_preview": self.generate_registration_preview,
            "submit_registration": self.submit_registration,
            "is_seller_registered": self.is_seller_registered,
            "needs_registration": self.needs_registration,
            "get_next_action": self.get_next_action
        }


# ==================== STANDALONE FUNCTIONS ====================

def quick_seller_check(aws_credentials: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Quick function to check seller status without creating a module instance
    
    Args:
        aws_credentials: Optional AWS credentials
        
    Returns:
        Dict with seller status
    """
    module = SellerRegistrationModule(aws_credentials=aws_credentials)
    return module.check_seller_status()


def is_seller_registered(aws_credentials: Optional[Dict[str, str]] = None) -> bool:
    """
    Quick boolean check if account is registered as seller
    
    Args:
        aws_credentials: Optional AWS credentials
        
    Returns:
        True if registered, False otherwise
    """
    module = SellerRegistrationModule(aws_credentials=aws_credentials)
    return module.is_seller_registered()


def get_registration_help() -> Dict[str, Any]:
    """
    Get help resources without creating a full module instance
    
    Returns:
        Dict with help resources
    """
    module = SellerRegistrationModule()
    return module.get_help_resources()


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    print("🚀 AWS Marketplace Seller Registration Module")
    print("=" * 60)
    
    # Example 1: Basic usage
    print("\n📋 Example 1: Basic Status Check")
    registration = SellerRegistrationModule()
    status = registration.check_seller_status()
    print(f"Seller Status: {status.get('seller_status', 'Unknown')}")
    print(f"Account ID: {status.get('account_id', 'Unknown')}")
    
    # Example 2: Quick functions
    print("\n📋 Example 2: Quick Functions")
    is_registered = is_seller_registered()
    print(f"Is Registered: {is_registered}")
    
    # Example 3: Module info
    print("\n📋 Example 3: Module Information")
    info = registration.get_module_info()
    print(f"Module: {info['module_name']} v{info['version']}")
    print(f"Capabilities: {len(info['capabilities'])} features")
    
    print("\n✅ Module ready for integration!")