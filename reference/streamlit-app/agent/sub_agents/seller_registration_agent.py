"""
Seller Registration Agent

Sub-agent for AWS Marketplace seller registration process.
Follows the BaseSubAgent pattern for consistency with existing agents.
"""

from typing import Dict, Any, List
from .base_agent import BaseSubAgent
from ..tools.seller_registration_tools import SellerRegistrationTools


class SellerRegistrationAgent(BaseSubAgent):
    """
    Seller Registration Agent
    
    Handles the seller registration process including:
    - Account verification
    - Business information collection
    - Tax information setup
    - Banking information setup
    - Registration submission
    - Status tracking
    """
    
    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None, aws_session_token=None, region='us-east-1'):
        super().__init__(stage_number=0, stage_name="Seller Registration")
        self.seller_tools = SellerRegistrationTools(
            region=region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token
        )
        self.registration_status = None
        self.aws_credentials = {
            'access_key_id': aws_access_key_id,
            'secret_access_key': aws_secret_access_key,
            'session_token': aws_session_token,
            'region': region
        }
    
    def get_required_fields(self) -> List[str]:
        """Return list of required field names for seller registration"""
        return [
            "business_name",
            "business_type",
            "business_address",
            "business_phone",
            "business_email",
            "tax_id",
            "primary_contact_name",
            "primary_contact_email",
            "primary_contact_phone"
        ]
    
    def get_optional_fields(self) -> List[str]:
        """Return list of optional field names"""
        return [
            "website_url",
            "business_description",
            "years_in_business",
            "business_license_number",
            "additional_contacts"
        ]
    
    def get_field_validations(self) -> Dict[str, Dict[str, Any]]:
        """Return validation rules for each field"""
        return {
            "business_name": {
                "type": "string",
                "min_length": 2,
                "max_length": 100,
                "description": "Legal name of your business"
            },
            "business_type": {
                "type": "string",
                "allowed_values": ["Corporation", "LLC", "Partnership", "Sole Proprietorship"],
                "description": "Type of business entity"
            },
            "business_address": {
                "type": "string",
                "min_length": 10,
                "max_length": 200,
                "description": "Complete business address"
            },
            "business_phone": {
                "type": "string",
                "pattern": r"^\+?[\d\s\-\(\)]{10,15}$",
                "description": "Business phone number"
            },
            "business_email": {
                "type": "string",
                "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                "description": "Business email address"
            },
            "tax_id": {
                "type": "string",
                "pattern": r"^\d{2}-?\d{7}$|^\d{3}-?\d{2}-?\d{4}$|^[A-Z]{5}[0-9]{4}[A-Z]{1}$",
                "description": "Tax ID (EIN, SSN, or PAN for India)"
            },
            "primary_contact_name": {
                "type": "string",
                "min_length": 2,
                "max_length": 50,
                "description": "Name of primary business contact"
            },
            "primary_contact_email": {
                "type": "string",
                "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                "description": "Email of primary business contact"
            },
            "primary_contact_phone": {
                "type": "string",
                "pattern": r"^\+?[\d\s\-\(\)]{10,15}$",
                "description": "Phone of primary business contact"
            },
            "website_url": {
                "type": "string",
                "pattern": r"^https?://[^\s]+$",
                "description": "Business website URL (optional)"
            },
            "business_description": {
                "type": "string",
                "max_length": 500,
                "description": "Brief description of your business (optional)"
            },
            "years_in_business": {
                "type": "integer",
                "min_value": 0,
                "max_value": 100,
                "description": "Number of years in business (optional)"
            }
        }
    
    def get_stage_instructions(self) -> str:
        """Return instructions for seller registration stage"""
        return """
        Welcome to AWS Marketplace Seller Registration!
        
        To become an AWS Marketplace seller, I need to collect some business information.
        This is a one-time process that typically takes 5-10 business days to complete.
        
        I'll guide you through:
        1. Business Information - Legal name, type, address, contact details
        2. Tax Information - Tax ID and classification
        3. Banking Information - Payment account setup
        4. Registration Submission - Submit to AWS for review
        
        Let's start with your business information. You can provide all details at once
        or I can ask you for each piece of information step by step.
        
        Required information:
        - Business name and type
        - Business address and contact information
        - Tax ID (EIN or SSN)
        - Primary contact person details
        """
    
    def process_stage(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user input for seller registration stage
        
        Args:
            user_input: User's message
            context: Current conversation context
            
        Returns:
            Response dictionary with status and next steps
        """
        # Check current seller status first
        if not self.registration_status:
            status_check = self.seller_tools.check_seller_status()
            self.registration_status = status_check
            
            if status_check["success"] and status_check["seller_status"] == "APPROVED":
                return {
                    "status": "complete",
                    "message": "Great news! Your AWS account is already registered as a Marketplace seller. You can proceed directly to creating listings.",
                    "data": status_check,
                    "next_question": None,
                    "errors": []
                }
            elif status_check["success"] and status_check["seller_status"] == "PENDING":
                return {
                    "status": "pending",
                    "message": "Your seller registration is currently under review by AWS. This typically takes 1-3 business days. You can check the status in your AWS Marketplace Management Console.",
                    "data": status_check,
                    "next_question": "Would you like me to help you with anything else while we wait for approval?",
                    "errors": []
                }
        
        # Parse user input to extract business information
        extracted_data = self._extract_business_info(user_input)
        
        # Update stage data with extracted information
        for field, value in extracted_data.items():
            if value:
                self.stage_data[field] = value
        
        # Validate current data
        validation_errors = self.validate_all_fields(self.stage_data)
        
        # Check what information is still needed
        missing_required = [
            field for field in self.get_required_fields()
            if field not in self.stage_data or not self.stage_data[field]
        ]
        
        if not missing_required and not validation_errors:
            # All required information collected and valid
            return self._prepare_registration_submission()
        elif missing_required:
            # Still need more information
            return {
                "status": "collecting",
                "message": self._generate_collection_message(missing_required),
                "data": self.stage_data,
                "next_question": self._get_next_question(missing_required[0]),
                "errors": validation_errors
            }
        else:
            # Have all info but validation errors
            return {
                "status": "validating",
                "message": f"I have all the required information, but there are some validation issues: {', '.join(validation_errors)}",
                "data": self.stage_data,
                "next_question": "Please provide the correct information for the fields with errors.",
                "errors": validation_errors
            }
    
    def _extract_business_info(self, user_input: str) -> Dict[str, Any]:
        """
        Extract business information from user input
        
        This uses pattern matching to extract structured information
        """
        extracted = {}
        
        # Define extraction patterns
        patterns = {
            "business_name": [
                r"business name[:\s]+([^\n]+)",
                r"company name[:\s]+([^\n]+)",
                r"legal name[:\s]+([^\n]+)"
            ],
            "business_type": [
                r"business type[:\s]+([^\n]+)",
                r"company type[:\s]+([^\n]+)",
                r"entity type[:\s]+([^\n]+)"
            ],
            "business_address": [
                r"business address[:\s]+([^\n]+)",
                r"company address[:\s]+([^\n]+)",
                r"address[:\s]+([^\n]+)"
            ],
            "business_phone": [
                r"business phone[:\s]+([^\n]+)",
                r"phone[:\s]+([^\n]+)",
                r"contact number[:\s]+([^\n]+)"
            ],
            "business_email": [
                r"business email[:\s]+([^\n]+)",
                r"email[:\s]+([^\n]+)",
                r"contact email[:\s]+([^\n]+)"
            ],
            "tax_id": [
                r"tax id[:\s]+([^\n]+)",
                r"tax number[:\s]+([^\n]+)",
                r"ein[:\s]+([^\n]+)",
                r"pan[:\s]+([^\n]+)"
            ],
            "primary_contact_name": [
                r"primary contact name[:\s]+([^\n]+)",
                r"contact name[:\s]+([^\n]+)",
                r"contact person[:\s]+([^\n]+)"
            ],
            "primary_contact_email": [
                r"primary contact email[:\s]+([^\n]+)",
                r"contact email[:\s]+([^\n]+)"
            ],
            "primary_contact_phone": [
                r"primary contact phone[:\s]+([^\n]+)",
                r"contact phone[:\s]+([^\n]+)"
            ],
            "website_url": [
                r"website[:\s]+([^\n]+)",
                r"website url[:\s]+([^\n]+)",
                r"web[:\s]+([^\n]+)"
            ]
        }
        
        import re
        
        # Extract information using patterns
        for field, field_patterns in patterns.items():
            for pattern in field_patterns:
                match = re.search(pattern, user_input.lower())
                if match:
                    value = match.group(1).strip()
                    # Clean up the extracted value
                    value = value.strip('",\'')
                    if value and len(value) > 1:
                        extracted[field] = value
                        break  # Use first match found
        
        # Also try to extract email addresses using email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, user_input)
        
        if emails:
            # If we don't have business_email yet, use first email
            if "business_email" not in extracted and emails:
                extracted["business_email"] = emails[0]
            
            # If we have multiple emails, second might be contact email
            if "primary_contact_email" not in extracted and len(emails) > 1:
                extracted["primary_contact_email"] = emails[1]
        
        # Extract phone numbers
        phone_pattern = r'[\+]?[1-9]?[0-9]{1,4}?[-.\s]?\(?[0-9]{1,4}\)?[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,9}'
        phones = re.findall(phone_pattern, user_input)
        
        if phones:
            # Clean up phone numbers
            clean_phones = []
            for phone in phones:
                clean_phone = re.sub(r'[^\d+]', '', phone)
                if len(clean_phone) >= 10:  # Valid phone number
                    clean_phones.append(phone.strip())
            
            if clean_phones:
                if "business_phone" not in extracted:
                    extracted["business_phone"] = clean_phones[0]
                if "primary_contact_phone" not in extracted and len(clean_phones) > 1:
                    extracted["primary_contact_phone"] = clean_phones[1]
                elif "primary_contact_phone" not in extracted:
                    extracted["primary_contact_phone"] = clean_phones[0]
        
        return extracted
    
    def _generate_collection_message(self, missing_fields: List[str]) -> str:
        """Generate message for collecting missing information"""
        if len(missing_fields) == 1:
            field = missing_fields[0]
            return f"I still need your {field.replace('_', ' ')}. {self._get_field_description(field)}"
        else:
            field_list = ", ".join([f.replace('_', ' ') for f in missing_fields[:3]])
            if len(missing_fields) > 3:
                field_list += f" and {len(missing_fields) - 3} more fields"
            return f"I still need the following information: {field_list}. Let's start with your {missing_fields[0].replace('_', ' ')}."
    
    def _get_next_question(self, field: str) -> str:
        """Get specific question for a field"""
        questions = {
            "business_name": "What is the legal name of your business?",
            "business_type": "What type of business entity is this? (Corporation, LLC, Partnership, or Sole Proprietorship)",
            "business_address": "What is your complete business address?",
            "business_phone": "What is your business phone number?",
            "business_email": "What is your business email address?",
            "tax_id": "What is your Tax ID (EIN or SSN)?",
            "primary_contact_name": "Who is the primary contact person for this business?",
            "primary_contact_email": "What is the primary contact's email address?",
            "primary_contact_phone": "What is the primary contact's phone number?"
        }
        return questions.get(field, f"Please provide your {field.replace('_', ' ')}.")
    
    def _get_field_description(self, field: str) -> str:
        """Get description for a field"""
        validations = self.get_field_validations()
        return validations.get(field, {}).get("description", "")
    
    def _prepare_registration_submission(self) -> Dict[str, Any]:
        """Prepare and submit seller registration"""
        # Validate business information
        validation = self.seller_tools.validate_business_info(self.stage_data)
        
        if not validation["success"]:
            return {
                "status": "error",
                "message": "Business information validation failed.",
                "data": self.stage_data,
                "next_question": "Please correct the validation errors and try again.",
                "errors": validation["errors"]
            }
        
        # Submit registration
        registration_data = {
            "business_info": self.stage_data,
            "submission_timestamp": self.seller_tools.get_account_info().get("timestamp")
        }
        
        submission_result = self.seller_tools.initiate_registration_process()
        
        if submission_result["success"]:
            return {
                "status": "complete",
                "message": f"Seller registration submitted successfully! {submission_result['message']}",
                "data": {
                    "registration_data": self.stage_data,
                    "submission_result": submission_result
                },
                "next_question": None,
                "errors": []
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to submit registration: {submission_result.get('message', 'Unknown error')}",
                "data": self.stage_data,
                "next_question": "Would you like me to help you resolve this issue?",
                "errors": [submission_result.get("error", "Submission failed")]
            }
    
    def get_registration_requirements(self) -> Dict[str, Any]:
        """Get seller registration requirements"""
        return self.seller_tools.get_registration_requirements()
    
    def get_help_resources(self) -> Dict[str, Any]:
        """Get help resources for seller registration"""
        return self.seller_tools.get_help_resources()
    
    def update_credentials(self, aws_access_key_id: str, aws_secret_access_key: str, 
                          aws_session_token: str = None, region: str = 'us-east-1'):
        """Update AWS credentials for the seller tools"""
        self.seller_tools = SellerRegistrationTools(
            region=region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token
        )
        self.aws_credentials = {
            'access_key_id': aws_access_key_id,
            'secret_access_key': aws_secret_access_key,
            'session_token': aws_session_token,
            'region': region
        }
        self.registration_status = None  # Reset status when credentials change
    
    def check_seller_status(self) -> Dict[str, Any]:
        """Check current seller registration status"""
        return self.seller_tools.check_seller_status()
    
    def create_support_case(self, subject: str, description: str) -> Dict[str, Any]:
        """Create support case for registration assistance"""
        return self.seller_tools.create_support_case(subject, description)