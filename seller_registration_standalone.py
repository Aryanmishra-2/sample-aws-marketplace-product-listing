#!/usr/bin/env python3
"""
Standalone AWS Marketplace Seller Registration Tool

This tool can be used independently or integrated into other processes.
Provides a simple interface for seller registration functionality.
"""

import sys
import json
from typing import Dict, Any, Optional
from agent.tools.seller_registration_tools import SellerRegistrationTools
from agent.sub_agents.seller_registration_agent import SellerRegistrationAgent


class SellerRegistrationTool:
    """
    Standalone Seller Registration Tool
    
    Can be used as:
    1. Command-line tool
    2. Python module import
    3. API endpoint backend
    4. Integration component
    """
    
    def __init__(self, region: str = "us-east-1"):
        """Initialize the seller registration tool"""
        self.tools = SellerRegistrationTools(region=region)
        self.agent = SellerRegistrationAgent()
    
    def check_status(self) -> Dict[str, Any]:
        """Check seller registration status"""
        return self.tools.check_seller_status()
    
    def get_requirements(self) -> Dict[str, Any]:
        """Get registration requirements"""
        return self.tools.get_registration_requirements()
    
    def validate_business_info(self, business_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate business information"""
        return self.tools.validate_business_info(business_info)
    
    def submit_registration(self, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit seller registration"""
        return self.tools.submit_seller_registration(registration_data)
    
    def interactive_registration(self) -> Dict[str, Any]:
        """Run interactive registration process"""
        print("🚀 AWS Marketplace Seller Registration")
        print("=" * 50)
        
        # Check current status
        print("Checking current seller status...")
        status = self.check_status()
        
        if status["success"]:
            if status["seller_status"] == "APPROVED":
                print("✅ You're already registered as an AWS Marketplace seller!")
                return status
            elif status["seller_status"] == "PENDING":
                print("⏳ Your registration is pending review.")
                return status
        
        print("\n📋 Starting seller registration process...")
        
        # Get requirements
        requirements = self.get_requirements()
        print(f"\n📖 Registration Requirements:")
        print(f"- Business information (required)")
        print(f"- Tax information (required)")
        print(f"- Banking information (required)")
        print(f"- Estimated timeline: {requirements['timeline']['total_process']}")
        
        # Collect business information
        business_info = self._collect_business_info()
        
        # Validate information
        print("\n🔍 Validating business information...")
        validation = self.validate_business_info(business_info)
        
        if not validation["success"]:
            print("❌ Validation failed:")
            for error in validation["errors"]:
                print(f"  - {error}")
            return validation
        
        print("✅ Business information validated successfully!")
        
        # Submit registration
        print("\n📤 Submitting seller registration...")
        registration_data = {"business_info": business_info}
        result = self.submit_registration(registration_data)
        
        if result["success"]:
            print(f"✅ {result['message']}")
            print(f"📧 Registration ID: {result.get('registration_id', 'N/A')}")
            print(f"⏱️  Estimated review time: {result.get('estimated_review_time', 'N/A')}")
            print("\n📋 Next steps:")
            for step in result.get("next_steps", []):
                print(f"  - {step}")
        else:
            print(f"❌ Registration failed: {result.get('message', 'Unknown error')}")
        
        return result
    
    def _collect_business_info(self) -> Dict[str, Any]:
        """Collect business information interactively"""
        print("\n📝 Business Information Collection")
        print("-" * 40)
        
        business_info = {}
        
        # Required fields
        required_fields = [
            ("business_name", "Business Name"),
            ("business_type", "Business Type (Corporation/LLC/Partnership/Sole Proprietorship)"),
            ("business_address", "Business Address"),
            ("business_phone", "Business Phone"),
            ("business_email", "Business Email"),
            ("tax_id", "Tax ID (EIN or SSN)"),
            ("primary_contact_name", "Primary Contact Name"),
            ("primary_contact_email", "Primary Contact Email"),
            ("primary_contact_phone", "Primary Contact Phone")
        ]
        
        for field_key, field_label in required_fields:
            while True:
                value = input(f"{field_label}: ").strip()
                if value:
                    business_info[field_key] = value
                    break
                else:
                    print("This field is required. Please enter a value.")
        
        # Optional fields
        optional_fields = [
            ("website_url", "Website URL (optional)"),
            ("business_description", "Business Description (optional)")
        ]
        
        print("\n📝 Optional Information")
        print("-" * 25)
        
        for field_key, field_label in optional_fields:
            value = input(f"{field_label}: ").strip()
            if value:
                business_info[field_key] = value
        
        return business_info
    
    def get_help(self) -> Dict[str, Any]:
        """Get help resources"""
        return self.tools.get_help_resources()
    
    def create_support_case(self, subject: str, description: str) -> Dict[str, Any]:
        """Create support case"""
        return self.tools.create_support_case(subject, description)


def main():
    """Command-line interface"""
    if len(sys.argv) < 2:
        print("Usage: python seller_registration_standalone.py <command>")
        print("\nCommands:")
        print("  status      - Check seller registration status")
        print("  requirements - Show registration requirements")
        print("  register    - Start interactive registration")
        print("  help        - Show help resources")
        return
    
    command = sys.argv[1].lower()
    tool = SellerRegistrationTool()
    
    if command == "status":
        result = tool.check_status()
        print(json.dumps(result, indent=2))
    
    elif command == "requirements":
        result = tool.get_requirements()
        print(json.dumps(result, indent=2))
    
    elif command == "register":
        result = tool.interactive_registration()
        print(f"\nFinal result: {json.dumps(result, indent=2)}")
    
    elif command == "help":
        result = tool.get_help()
        print(json.dumps(result, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        print("Use 'python seller_registration_standalone.py' for usage info")


if __name__ == "__main__":
    main()