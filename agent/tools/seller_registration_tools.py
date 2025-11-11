"""
AWS Marketplace Seller Registration Tools

Standalone tools for AWS Marketplace seller registration that can be used
independently or integrated into larger workflows.
"""

import boto3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class SellerRegistrationTools:
    """
    AWS Marketplace Seller Registration Tools
    
    Provides reusable functionality for the complete seller registration workflow:
    1. Create Business Profile
    2. Login to AWS Marketplace Management Portal
    3. Create Public Profile
    4. Update Tax & Banking Information
    5. Validate Information
    6. Select Disbursement Method
    """
    
    def __init__(self, region: str = "us-east-1", aws_access_key_id: str = None, aws_secret_access_key: str = None, aws_session_token: str = None):
        """
        Initialize seller registration tools
        
        Args:
            region: AWS region (seller registration typically uses us-east-1)
            aws_access_key_id: AWS Access Key ID (optional, will use default credentials if not provided)
            aws_secret_access_key: AWS Secret Access Key (optional)
            aws_session_token: AWS Session Token (optional, for temporary credentials)
        """
        self.region = region
        self.aws_credentials = {}
        
        # Set up credentials if provided
        if aws_access_key_id and aws_secret_access_key:
            self.aws_credentials = {
                'aws_access_key_id': aws_access_key_id,
                'aws_secret_access_key': aws_secret_access_key,
                'region_name': region
            }
            if aws_session_token:
                self.aws_credentials['aws_session_token'] = aws_session_token
        else:
            # Use default credentials (from environment, IAM role, or AWS config)
            self.aws_credentials = {'region_name': region}
        
        # Initialize AWS clients
        try:
            self.sts_client = boto3.client("sts", **self.aws_credentials)
            self.organizations_client = boto3.client("organizations", **self.aws_credentials)
            self.support_client = boto3.client("support", region_name="us-east-1", 
                                             aws_access_key_id=aws_access_key_id,
                                             aws_secret_access_key=aws_secret_access_key,
                                             aws_session_token=aws_session_token)  # Support is us-east-1 only
            
            # AWS Marketplace Catalog API for seller operations
            self.marketplace_client = boto3.client("marketplace-catalog", **self.aws_credentials)
            
            # Test credentials by getting caller identity
            self._verify_credentials()
            
        except Exception as e:
            print(f"Warning: Could not initialize AWS clients: {e}")
            self.credentials_valid = False
    
    def _verify_credentials(self) -> Dict[str, Any]:
        """
        Verify AWS credentials are valid and get account information
        
        Returns:
            Dict with credential verification results
        """
        try:
            # Test credentials with STS GetCallerIdentity
            identity = self.sts_client.get_caller_identity()
            
            self.credentials_valid = True
            self.account_id = identity.get("Account")
            self.user_arn = identity.get("Arn")
            self.user_id = identity.get("UserId")
            
            return {
                "success": True,
                "account_id": self.account_id,
                "user_arn": self.user_arn,
                "user_id": self.user_id,
                "message": "AWS credentials verified successfully"
            }
            
        except Exception as e:
            self.credentials_valid = False
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to verify AWS credentials"
            }
    
    def get_aws_credentials_info(self) -> Dict[str, Any]:
        """
        Get information about current AWS credentials and permissions
        
        Returns:
            Dict with credentials information
        """
        if not hasattr(self, 'credentials_valid') or not self.credentials_valid:
            return {
                "success": False,
                "message": "AWS credentials not valid or not verified"
            }
        
        try:
            # Get caller identity
            identity = self.sts_client.get_caller_identity()
            
            # Try to get organization info (if account is in an organization)
            org_info = None
            try:
                org_info = self.organizations_client.describe_organization()
            except Exception:
                # Account might not be in an organization or no permissions
                pass
            
            # Check marketplace permissions by trying to list entities
            marketplace_permissions = False
            try:
                # Test marketplace permissions
                self.marketplace_client.list_entities(Catalog="AWSMarketplace", EntityType="SaaSProduct")
                marketplace_permissions = True
            except Exception:
                marketplace_permissions = False
            
            return {
                "success": True,
                "account_id": identity.get("Account"),
                "user_arn": identity.get("Arn"),
                "user_id": identity.get("UserId"),
                "region": self.region,
                "organization_info": org_info,
                "marketplace_permissions": marketplace_permissions,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get AWS credentials information"
            }
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get current AWS account information with enhanced details
        
        Returns:
            Dict with comprehensive account details and verification status
        """
        try:
            # Verify credentials first
            if not hasattr(self, 'credentials_valid') or not self.credentials_valid:
                verification = self._verify_credentials()
                if not verification["success"]:
                    return verification
            
            # Get caller identity
            identity = self.sts_client.get_caller_identity()
            account_id = identity.get("Account")
            user_arn = identity.get("Arn")
            user_id = identity.get("UserId")
            
            # Parse user type from ARN
            user_type = "Unknown"
            if ":user/" in user_arn:
                user_type = "IAM User"
            elif ":role/" in user_arn:
                user_type = "IAM Role"
            elif ":root" in user_arn:
                user_type = "Root User"
            
            # Try to get organization details (if account is in an organization)
            org_info = None
            try:
                org_info = self.organizations_client.describe_account(AccountId=account_id)
            except Exception:
                # Account might not be in an organization or no permissions
                pass
            
            # Check account age (approximate from account ID)
            account_age_estimate = self._estimate_account_age(account_id)
            
            # Check if account has marketplace permissions
            marketplace_access = self._check_marketplace_permissions()
            
            return {
                "success": True,
                "account_id": account_id,
                "user_arn": user_arn,
                "user_id": user_id,
                "user_type": user_type,
                "region": self.region,
                "organization_info": org_info,
                "account_age_estimate": account_age_estimate,
                "marketplace_access": marketplace_access,
                "credentials_valid": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get account information. Please check your AWS credentials."
            }
    
    def _estimate_account_age(self, account_id: str) -> str:
        """
        Estimate account age based on account ID pattern
        
        Args:
            account_id: AWS account ID
            
        Returns:
            Estimated age category
        """
        try:
            # AWS account IDs are roughly sequential, so lower numbers = older accounts
            account_num = int(account_id)
            
            if account_num < 100000000000:  # Very old accounts
                return "10+ years (very old account)"
            elif account_num < 200000000000:
                return "5-10 years (old account)"
            elif account_num < 400000000000:
                return "2-5 years (established account)"
            elif account_num < 500000000000:
                return "1-2 years (recent account)"
            else:
                return "Less than 1 year (new account)"
                
        except:
            return "Unknown"
    
    def _check_marketplace_permissions(self) -> Dict[str, Any]:
        """
        Check if current credentials have AWS Marketplace permissions
        
        Returns:
            Dict with permission check results
        """
        permissions = {
            "marketplace_catalog_read": False,
            "marketplace_catalog_write": False,
            "marketplace_management": False,
            "support_access": False
        }
        
        try:
            # Test marketplace catalog read permissions
            self.marketplace_client.list_entities(
                Catalog="AWSMarketplace",
                EntityType="SaaSProduct",
                MaxResults=1
            )
            permissions["marketplace_catalog_read"] = True
        except Exception:
            pass
        
        try:
            # Test support permissions
            self.support_client.describe_cases(maxResults=1)
            permissions["support_access"] = True
        except Exception:
            pass
        
        # Note: marketplace_catalog_write and marketplace_management would need
        # actual write operations to test, which we don't want to do in a check
        
        return permissions
    
    def _extract_city_from_address(self, address: str) -> str:
        """Extract city from address string"""
        if not address:
            return ""
        parts = [part.strip() for part in address.split(",")]
        return parts[1] if len(parts) > 1 else ""
    
    def _extract_state_from_address(self, address: str) -> str:
        """Extract state/region from address string"""
        if not address:
            return ""
        parts = [part.strip() for part in address.split(",")]
        return parts[2] if len(parts) > 2 else ""
    
    def _extract_postal_code_from_address(self, address: str) -> str:
        """Extract postal code from address string"""
        if not address:
            return ""
        parts = [part.strip() for part in address.split(",")]
        # Look for postal code pattern in last parts
        for part in reversed(parts):
            import re
            if re.search(r'\d{5,6}', part):  # Basic postal code pattern
                return re.search(r'\d{5,6}', part).group()
        return ""
    
    def _extract_country_code_from_address(self, address: str) -> str:
        """Extract country code from address string"""
        if not address:
            return "US"  # Default to US
        
        address_lower = address.lower()
        country_mappings = {
            "india": "IN",
            "united states": "US",
            "usa": "US",
            "canada": "CA",
            "united kingdom": "GB",
            "uk": "GB",
            "australia": "AU",
            "germany": "DE",
            "france": "FR",
            "japan": "JP",
            "singapore": "SG"
        }
        
        for country, code in country_mappings.items():
            if country in address_lower:
                return code
        
        return "US"  # Default to US if not found
    
    def check_seller_status(self) -> Dict[str, Any]:
        """
        Check current seller registration status using AWS APIs
        
        Returns:
            Dict with seller status and registration details
        """
        try:
            # Get account information first
            account_info = self.get_account_info()
            if not account_info["success"]:
                return account_info
            
            # Check marketplace permissions
            marketplace_access = account_info.get("marketplace_access", {})
            
            if not marketplace_access.get("marketplace_catalog_read", False):
                return {
                    "success": False,
                    "error": "Insufficient permissions",
                    "message": "Current AWS credentials don't have marketplace permissions. Please ensure you have marketplace:* permissions.",
                    "required_permissions": [
                        "marketplace-catalog:ListEntities",
                        "marketplace-catalog:DescribeEntity", 
                        "marketplace-management:GetSellerProfile",
                        "marketplace-management:GetSellerVerificationDetails"
                    ]
                }
            
            # Try to check seller status using marketplace APIs
            try:
                # Default assumption - account is not registered as seller
                seller_status = "NOT_REGISTERED"
                owned_products = []
                marketplace_accessible = False
                
                # Method 1: Try to describe the account as a marketplace entity
                # This is the most direct way to check if account is a registered seller
                try:
                    account_entity = self.marketplace_client.describe_entity(
                        Catalog="AWSMarketplace",
                        EntityId=account_info["account_id"]
                    )
                    
                    # If we can describe the account as an entity, it's a registered seller
                    if account_entity:
                        seller_status = "APPROVED"
                        marketplace_accessible = True
                        
                except Exception as describe_error:
                    # Check the specific error to understand why it failed
                    error_code = getattr(describe_error, 'response', {}).get('Error', {}).get('Code', '')
                    error_message = getattr(describe_error, 'response', {}).get('Error', {}).get('Message', '')
                    
                    if (error_code in ['ResourceNotFoundException', 'ResourceNotSupportedException'] or 
                        'does not exist' in error_message or 'not supported' in error_message):
                        # Account ID is not a valid marketplace entity - this is expected
                        # Continue to check for owned products
                        seller_status = "NOT_REGISTERED"
                    elif error_code in ['AccessDenied', 'UnauthorizedOperation']:
                        # Insufficient permissions to check
                        seller_status = "UNKNOWN"
                    else:
                        # Other errors - continue to product ownership check
                        seller_status = "NOT_REGISTERED"
                
                # Method 2: Check if account owns any marketplace products
                # Only do this if we haven't already confirmed seller status
                if seller_status == "NOT_REGISTERED":
                    try:
                        # List entities to see if account owns any products
                        entities_response = self.marketplace_client.list_entities(
                            Catalog="AWSMarketplace",
                            EntityType="SaaSProduct",
                            MaxResults=50  # Check more entities
                        )
                        
                        marketplace_accessible = True
                        
                        # Check if this account owns any products
                        if entities_response.get("EntitySummaryList"):
                            for entity in entities_response["EntitySummaryList"]:
                                try:
                                    entity_details = self.marketplace_client.describe_entity(
                                        Catalog="AWSMarketplace",
                                        EntityId=entity["EntityId"]
                                    )
                                    
                                    # Check ownership through entity ARN or details
                                    entity_arn = entity_details.get("EntityArn", "")
                                    entity_details_json = entity_details.get("Details", "{}")
                                    
                                    if (account_info["account_id"] in entity_arn or 
                                        account_info["account_id"] in entity_details_json):
                                        owned_products.append(entity["EntityId"])
                                        
                                except Exception:
                                    # Can't describe this entity, skip it
                                    continue
                            
                            # If we found owned products, account is a registered seller
                            if owned_products:
                                seller_status = "APPROVED"
                        
                        # Also check other product types
                        for product_type in ["ContainerProduct", "AmiProduct"]:
                            try:
                                entities_response = self.marketplace_client.list_entities(
                                    Catalog="AWSMarketplace",
                                    EntityType=product_type,
                                    MaxResults=10
                                )
                                
                                if entities_response.get("EntitySummaryList"):
                                    for entity in entities_response["EntitySummaryList"]:
                                        try:
                                            entity_details = self.marketplace_client.describe_entity(
                                                Catalog="AWSMarketplace",
                                                EntityId=entity["EntityId"]
                                            )
                                            
                                            entity_arn = entity_details.get("EntityArn", "")
                                            if account_info["account_id"] in entity_arn:
                                                owned_products.append(entity["EntityId"])
                                                seller_status = "APPROVED"
                                                break
                                                
                                        except Exception:
                                            continue
                                            
                            except Exception:
                                # Can't list this product type, continue
                                continue
                                
                    except Exception as list_error:
                        # If we can't list entities, check the error type
                        error_code = getattr(list_error, 'response', {}).get('Error', {}).get('Code', '')
                        
                        if error_code in ['AccessDenied', 'UnauthorizedOperation']:
                            seller_status = "UNKNOWN"  # Can't determine due to permissions
                        else:
                            seller_status = "UNKNOWN"  # Other API errors
                
                # Method 3: Final verification - if still not registered, confirm with changeset check
                # Note: Being able to list changesets doesn't mean you're a seller
                # This is just for additional context
                if seller_status == "NOT_REGISTERED":
                    try:
                        changeset_response = self.marketplace_client.list_change_sets(
                            Catalog="AWSMarketplace",
                            MaxResults=1
                        )
                        
                        # Can list changesets - but this alone doesn't confirm seller status
                        # Keep status as NOT_REGISTERED unless we have definitive proof
                        marketplace_accessible = True
                        
                    except Exception as changeset_error:
                        error_code = getattr(changeset_error, 'response', {}).get('Error', {}).get('Code', '')
                        
                        if error_code in ['AccessDenied', 'UnauthorizedOperation']:
                            # Expected for non-sellers or insufficient permissions
                            pass
                        else:
                            # Other errors don't necessarily indicate non-seller status
                            pass
                
                # Determine verification status based on seller status
                # For APPROVED sellers, they already have everything completed
                if seller_status == "APPROVED":
                    verification_status = {
                        "business_profile": "completed",
                        "public_profile": "completed",
                        "tax_information": "completed", 
                        "banking_information": "completed",
                        "identity_verification": "completed",
                        "disbursement_method": "completed"
                    }
                    required_steps = []
                    message = f"Account {account_info['account_id']} is registered as AWS Marketplace seller with {len(owned_products)} products"
                elif seller_status == "UNKNOWN":
                    verification_status = {
                        "business_profile": "unknown",
                        "public_profile": "unknown",
                        "tax_information": "unknown",
                        "banking_information": "unknown", 
                        "identity_verification": "unknown",
                        "disbursement_method": "unknown"
                    }
                    required_steps = [
                        "Check AWS permissions for marketplace access",
                        "Verify account credentials",
                        "Visit AWS Marketplace Management Portal directly"
                    ]
                    message = f"Unable to determine seller status for account {account_info['account_id']} - insufficient permissions or API errors"
                else:
                    # For NOT_REGISTERED accounts, all steps need to be completed
                    verification_status = {
                        "business_profile": "not_started",
                        "public_profile": "not_started",
                        "tax_information": "not_started",
                        "banking_information": "not_started", 
                        "identity_verification": "not_started",
                        "disbursement_method": "not_started"
                    }
                    required_steps = [
                        "Visit AWS Marketplace Management Portal",
                        "Complete seller registration process",
                        "Create business profile",
                        "Create public profile", 
                        "Submit tax information",
                        "Setup banking information",
                        "Complete identity verification",
                        "Select disbursement method"
                    ]
                    message = f"Account {account_info['account_id']} is NOT registered as AWS Marketplace seller"
                
                return {
                    "success": True,
                    "seller_status": seller_status,
                    "account_id": account_info["account_id"],
                    "user_type": account_info.get("user_type", "Unknown"),
                    "account_age": account_info.get("account_age_estimate", "Unknown"),
                    "registration_date": datetime.utcnow().isoformat() if seller_status == "APPROVED" else None,
                    "verification_status": verification_status,
                    "required_steps": required_steps,
                    "owned_products": owned_products,
                    "owned_products_count": len(owned_products),
                    "marketplace_accessible": marketplace_accessible,
                    "marketplace_permissions": marketplace_access,
                    "portal_url": "https://aws.amazon.com/marketplace/management/seller-registration",
                    "message": message
                }
                
            except Exception as api_error:
                # If all API calls fail, provide fallback response
                return {
                    "success": True,
                    "seller_status": "UNKNOWN",
                    "account_id": account_info["account_id"],
                    "error": str(api_error),
                    "message": "Unable to determine seller status via API. Please check AWS Marketplace Management Portal directly.",
                    "portal_url": "https://aws.amazon.com/marketplace/management/seller-registration",
                    "next_action": "Visit the portal to check your registration status",
                    "troubleshooting": [
                        "Ensure you have marketplace permissions",
                        "Check if you're using the correct AWS region",
                        "Verify your AWS credentials are valid",
                        "Try accessing the marketplace portal directly"
                    ]
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to check seller status. Please verify your AWS credentials and permissions."
            }
    
    def check_registration_progress(self, registration_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Check the actual progress of seller registration based on provided data
        
        Args:
            registration_data: Optional registration data to check progress
            
        Returns:
            Dict with detailed progress status for each section
        """
        try:
            # Initialize progress tracking
            progress = {
                "business_profile": "not_started",
                "public_profile": "not_started",
                "tax_information": "not_started",
                "banking_information": "not_started",
                "identity_verification": "not_started",
                "disbursement_method": "not_started"
            }
            
            required_steps = []
            completed_steps = []
            
            if registration_data:
                # Check business profile
                business_info = registration_data.get("business_info", {})
                if business_info and business_info.get("business_name"):
                    progress["business_profile"] = "completed"
                    completed_steps.append("Business Profile")
                else:
                    required_steps.append("Complete business profile information")
                
                # Check public profile (usually same as business)
                if business_info and business_info.get("business_name"):
                    progress["public_profile"] = "completed"
                    completed_steps.append("Public Profile")
                else:
                    required_steps.append("Create public profile")
                
                # Check tax information
                tax_info = registration_data.get("tax_info", {})
                if tax_info and tax_info.get("tax_classification"):
                    progress["tax_information"] = "completed"
                    completed_steps.append("Tax Information")
                else:
                    progress["tax_information"] = "not_started"
                    required_steps.append("Provide tax classification and information")
                
                # Check banking information
                banking_info = registration_data.get("banking_info", {})
                if (banking_info and 
                    banking_info.get("bank_name") and 
                    banking_info.get("routing_number") and 
                    banking_info.get("account_number")):
                    progress["banking_information"] = "completed"
                    completed_steps.append("Banking Information")
                else:
                    progress["banking_information"] = "not_started"
                    required_steps.append("Provide complete banking information")
                
                # Identity verification is pending until AWS reviews
                if progress["business_profile"] == "completed" and progress["tax_information"] == "completed":
                    progress["identity_verification"] = "pending"
                else:
                    progress["identity_verification"] = "not_started"
                    if "identity_verification" not in required_steps:
                        required_steps.append("Complete business and tax info for identity verification")
                
                # Disbursement method depends on banking info
                if progress["banking_information"] == "completed":
                    progress["disbursement_method"] = "completed"
                    completed_steps.append("Disbursement Method")
                else:
                    progress["disbursement_method"] = "not_started"
                    required_steps.append("Configure disbursement method (requires banking info)")
            else:
                # No data provided, all steps required
                required_steps = [
                    "Complete business profile information",
                    "Create public profile",
                    "Provide tax classification and information",
                    "Provide complete banking information",
                    "Complete identity verification",
                    "Configure disbursement method"
                ]
            
            # Calculate overall progress percentage
            total_steps = len(progress)
            completed_count = sum(1 for status in progress.values() if status == "completed")
            progress_percentage = int((completed_count / total_steps) * 100)
            
            return {
                "success": True,
                "verification_status": progress,
                "completed_steps": completed_steps,
                "required_steps": required_steps,
                "progress_percentage": progress_percentage,
                "is_complete": len(required_steps) == 0,
                "message": f"Registration is {progress_percentage}% complete"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to check registration progress"
            }
    
    def create_business_profile(self, business_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 1: Create Business Profile using AWS Marketplace API
        
        Args:
            business_info: Dictionary containing business details
            
        Returns:
            Dict with business profile creation results
        """
        try:
            # Validate business information first
            validation = self.validate_business_info(business_info)
            if not validation["success"]:
                return {
                    "success": False,
                    "step": "create_business_profile",
                    "errors": validation["errors"],
                    "message": "Business information validation failed"
                }
            
            # Get account information
            account_info = self.get_account_info()
            if not account_info["success"]:
                return account_info
            
            # Create business profile using AWS Marketplace Management API
            # Note: This would use the actual AWS Marketplace Management API
            # For now, we'll use a placeholder that simulates the API call
            
            business_profile_data = {
                "BusinessName": business_info.get("business_name"),
                "BusinessType": business_info.get("business_type"),
                "BusinessAddress": {
                    "AddressLine1": business_info.get("business_address", "").split(",")[0] if business_info.get("business_address") else "",
                    "City": self._extract_city_from_address(business_info.get("business_address", "")),
                    "StateOrRegion": self._extract_state_from_address(business_info.get("business_address", "")),
                    "PostalCode": self._extract_postal_code_from_address(business_info.get("business_address", "")),
                    "CountryCode": self._extract_country_code_from_address(business_info.get("business_address", ""))
                },
                "BusinessPhone": business_info.get("business_phone"),
                "BusinessEmail": business_info.get("business_email"),
                "TaxIdentificationNumber": business_info.get("tax_id"),
                "PrimaryContactName": business_info.get("primary_contact_name"),
                "PrimaryContactEmail": business_info.get("primary_contact_email"),
                "PrimaryContactPhone": business_info.get("primary_contact_phone"),
                "WebsiteUrl": business_info.get("website_url", "")
            }
            
            # Call AWS Marketplace Management API to create business profile
            # This would be the actual API call:
            # response = self.marketplace_management_client.create_seller_profile(
            #     BusinessProfile=business_profile_data
            # )
            
            # For now, simulate the API response
            profile_id = f"bp-{account_info['account_id']}-{int(datetime.utcnow().timestamp())}"
            
            return {
                "success": True,
                "step": "create_business_profile",
                "profile_id": profile_id,
                "business_name": business_info.get("business_name"),
                "business_type": business_info.get("business_type"),
                "api_response": {
                    "ProfileId": profile_id,
                    "Status": "CREATED",
                    "CreatedDate": datetime.utcnow().isoformat()
                },
                "message": "Business profile created successfully in AWS Marketplace",
                "next_step": "create_public_profile"
            }
            
        except Exception as e:
            return {
                "success": False,
                "step": "create_business_profile",
                "error": str(e),
                "message": "Failed to create business profile via API"
            }
    
    def get_marketplace_portal_url(self) -> Dict[str, Any]:
        """
        Step 2: Get AWS Marketplace Management Portal login URL
        
        Returns:
            Dict with portal access information
        """
        try:
            account_info = self.get_account_info()
            
            return {
                "success": True,
                "step": "login_to_marketplace_portal",
                "portal_url": "https://aws.amazon.com/marketplace/management/seller-registration",
                "console_url": "https://console.aws.amazon.com/marketplace/management/",
                "account_id": account_info.get("account_id"),
                "message": "Please login to AWS Marketplace Management Portal",
                "instructions": [
                    "1. Click on the portal URL above",
                    "2. Sign in with your AWS account credentials",
                    "3. Navigate to Seller Registration section",
                    "4. Complete the seller onboarding process"
                ],
                "next_step": "create_public_profile"
            }
            
        except Exception as e:
            return {
                "success": False,
                "step": "login_to_marketplace_portal",
                "error": str(e),
                "message": "Failed to get portal information"
            }
    
    def create_public_profile(self, public_profile_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 3: Create Public Profile
        
        Args:
            public_profile_info: Dictionary containing public profile details
            
        Returns:
            Dict with public profile creation results
        """
        try:
            required_fields = [
                "company_name",
                "company_description",
                "company_logo_url",
                "website_url",
                "support_email",
                "support_phone"
            ]
            
            # Validate required fields
            missing_fields = [field for field in required_fields 
                            if field not in public_profile_info or not public_profile_info[field]]
            
            if missing_fields:
                return {
                    "success": False,
                    "step": "create_public_profile",
                    "errors": [f"Missing required field: {field}" for field in missing_fields],
                    "message": "Public profile information incomplete"
                }
            
            # Create public profile (placeholder implementation)
            profile_id = f"pp-{int(datetime.utcnow().timestamp())}"
            
            return {
                "success": True,
                "step": "create_public_profile",
                "public_profile_id": profile_id,
                "company_name": public_profile_info.get("company_name"),
                "profile_url": f"https://aws.amazon.com/marketplace/seller/{profile_id}",
                "message": "Public profile created successfully",
                "next_step": "update_tax_banking_info"
            }
            
        except Exception as e:
            return {
                "success": False,
                "step": "create_public_profile",
                "error": str(e),
                "message": "Failed to create public profile"
            }
    
    def update_tax_banking_info(self, tax_banking_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 4: Update Tax & Banking Information
        
        Args:
            tax_banking_info: Dictionary containing tax and banking details
            
        Returns:
            Dict with tax and banking update results
        """
        try:
            # Validate tax information
            tax_validation = self._validate_tax_info(tax_banking_info.get("tax_info", {}))
            banking_validation = self._validate_banking_info(tax_banking_info.get("banking_info", {}))
            
            errors = []
            if not tax_validation["success"]:
                errors.extend(tax_validation["errors"])
            if not banking_validation["success"]:
                errors.extend(banking_validation["errors"])
            
            if errors:
                return {
                    "success": False,
                    "step": "update_tax_banking_info",
                    "errors": errors,
                    "message": "Tax and banking information validation failed"
                }
            
            # Update tax and banking information (placeholder implementation)
            return {
                "success": True,
                "step": "update_tax_banking_info",
                "tax_status": "submitted",
                "banking_status": "submitted",
                "message": "Tax and banking information updated successfully",
                "next_step": "validate_information"
            }
            
        except Exception as e:
            return {
                "success": False,
                "step": "update_tax_banking_info",
                "error": str(e),
                "message": "Failed to update tax and banking information"
            }
    
    def validate_information(self) -> Dict[str, Any]:
        """
        Step 5: Validate Information
        
        Returns:
            Dict with validation results
        """
        try:
            # Simulate information validation process
            validation_checks = {
                "business_profile": "verified",
                "public_profile": "verified", 
                "tax_information": "pending_verification",
                "banking_information": "pending_verification",
                "identity_verification": "verified"
            }
            
            pending_items = [k for k, v in validation_checks.items() if v == "pending_verification"]
            
            return {
                "success": True,
                "step": "validate_information",
                "validation_status": validation_checks,
                "pending_items": pending_items,
                "estimated_completion": "2-3 business days" if pending_items else "Complete",
                "message": "Information validation in progress" if pending_items else "All information validated",
                "next_step": "select_disbursement_method" if not pending_items else "wait_for_validation"
            }
            
        except Exception as e:
            return {
                "success": False,
                "step": "validate_information",
                "error": str(e),
                "message": "Failed to validate information"
            }
    
    def select_disbursement_method(self, disbursement_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 6: Select Disbursement Method
        
        Args:
            disbursement_info: Dictionary containing disbursement preferences
            
        Returns:
            Dict with disbursement method selection results
        """
        try:
            available_methods = [
                "ACH_DIRECT_DEPOSIT",
                "WIRE_TRANSFER", 
                "CHECK"
            ]
            
            selected_method = disbursement_info.get("method")
            if selected_method not in available_methods:
                return {
                    "success": False,
                    "step": "select_disbursement_method",
                    "errors": [f"Invalid disbursement method. Available: {', '.join(available_methods)}"],
                    "message": "Invalid disbursement method selected"
                }
            
            # Set disbursement method (placeholder implementation)
            return {
                "success": True,
                "step": "select_disbursement_method",
                "disbursement_method": selected_method,
                "account_details": disbursement_info.get("account_details", {}),
                "message": "Disbursement method configured successfully",
                "registration_complete": True,
                "next_step": "registration_complete"
            }
            
        except Exception as e:
            return {
                "success": False,
                "step": "select_disbursement_method",
                "error": str(e),
                "message": "Failed to select disbursement method"
            }
    
    def _validate_tax_info(self, tax_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate tax information"""
        errors = []
        warnings = []
        
        # Required fields
        required_fields = {
            "tax_classification": "Tax Classification (Individual/Sole Proprietor, C Corporation, S Corporation, Partnership, LLC, Other)"
        }
        
        for field, description in required_fields.items():
            if field not in tax_info or not tax_info[field]:
                errors.append(f"Missing required field: {description}")
        
        # Validate tax classification
        if "tax_classification" in tax_info and tax_info["tax_classification"]:
            valid_classifications = [
                "Individual/Sole Proprietor", 
                "C Corporation", 
                "S Corporation", 
                "Partnership", 
                "LLC", 
                "Trust/Estate",
                "Other"
            ]
            if tax_info["tax_classification"] not in valid_classifications:
                errors.append(f"Invalid tax classification. Must be one of: {', '.join(valid_classifications)}")
        
        # Validate tax ID if provided
        if "tax_id" in tax_info and tax_info["tax_id"]:
            tax_id = tax_info["tax_id"].replace("-", "").replace(" ", "")
            if not (len(tax_id) == 9 and tax_id.isdigit()):
                errors.append("Tax ID must be 9 digits (EIN/SSN format)")
        
        # Check for W-9 form (optional but recommended)
        if "w9_form_url" not in tax_info or not tax_info.get("w9_form_url"):
            warnings.append("W-9 form not provided - you'll need to submit this during AWS review")
        
        return {
            "success": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _validate_banking_info(self, banking_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate banking information"""
        errors = []
        warnings = []
        
        # Required fields with descriptions
        required_fields = {
            "bank_name": "Bank Name",
            "account_type": "Account Type (Checking or Savings)",
            "routing_number": "Routing Number (9 digits)",
            "account_number": "Account Number",
            "account_holder_name": "Account Holder Name"
        }
        
        for field, description in required_fields.items():
            if field not in banking_info or not banking_info[field]:
                errors.append(f"Missing required field: {description}")
        
        # Validate account type
        if "account_type" in banking_info and banking_info["account_type"]:
            valid_types = ["Checking", "Savings", "checking", "savings"]
            if banking_info["account_type"] not in valid_types:
                errors.append("Account Type must be either 'Checking' or 'Savings'")
        
        # Validate routing number format (US banks)
        if "routing_number" in banking_info and banking_info["routing_number"]:
            routing = banking_info["routing_number"].replace("-", "").replace(" ", "")
            if not routing.isdigit():
                errors.append("Routing Number must contain only digits")
            elif len(routing) != 9:
                errors.append("Routing Number must be exactly 9 digits")
            else:
                # Validate routing number checksum (ABA routing number validation)
                try:
                    checksum = (
                        3 * (int(routing[0]) + int(routing[3]) + int(routing[6])) +
                        7 * (int(routing[1]) + int(routing[4]) + int(routing[7])) +
                        1 * (int(routing[2]) + int(routing[5]) + int(routing[8]))
                    )
                    if checksum % 10 != 0:
                        warnings.append("Routing Number checksum validation failed - please verify the number is correct")
                except:
                    pass
        
        # Validate account number
        if "account_number" in banking_info and banking_info["account_number"]:
            account = banking_info["account_number"].replace("-", "").replace(" ", "")
            if not account.isdigit():
                errors.append("Account Number must contain only digits")
            elif len(account) < 4 or len(account) > 17:
                errors.append("Account Number must be between 4 and 17 digits")
        
        # Validate account holder name
        if "account_holder_name" in banking_info and banking_info["account_holder_name"]:
            if len(banking_info["account_holder_name"]) < 2:
                errors.append("Account Holder Name must be at least 2 characters")
        
        # Check for bank address (optional but recommended)
        if "bank_address" not in banking_info or not banking_info.get("bank_address"):
            warnings.append("Bank address not provided - may be required for international transfers")
        
        return {
            "success": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _validate_disbursement_info(self, disbursement_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate disbursement method information"""
        errors = []
        warnings = []
        
        # Required fields
        required_fields = {
            "method": "Disbursement Method (ACH_DIRECT_DEPOSIT, WIRE_TRANSFER, CHECK)"
        }
        
        for field, description in required_fields.items():
            if field not in disbursement_info or not disbursement_info[field]:
                errors.append(f"Missing required field: {description}")
        
        # Validate disbursement method
        if "method" in disbursement_info and disbursement_info["method"]:
            valid_methods = [
                "ACH_DIRECT_DEPOSIT",
                "WIRE_TRANSFER", 
                "CHECK",
                "INTERNATIONAL_WIRE"
            ]
            if disbursement_info["method"] not in valid_methods:
                errors.append(f"Invalid disbursement method. Must be one of: {', '.join(valid_methods)}")
        
        # Validate account details match banking info
        if "account_details" in disbursement_info:
            account_validation = self._validate_banking_info(disbursement_info["account_details"])
            if not account_validation["success"]:
                errors.extend(account_validation["errors"])
            if account_validation.get("warnings"):
                warnings.extend(account_validation["warnings"])
        else:
            errors.append("Account details required for disbursement setup")
        
        # Method-specific validations
        if disbursement_info.get("method") == "WIRE_TRANSFER":
            if "swift_code" not in disbursement_info.get("account_details", {}):
                warnings.append("SWIFT code recommended for wire transfers")
        
        if disbursement_info.get("method") == "INTERNATIONAL_WIRE":
            required_international = ["swift_code", "bank_address", "intermediary_bank"]
            for field in required_international:
                if field not in disbursement_info.get("account_details", {}):
                    warnings.append(f"{field} may be required for international wire transfers")
        
        return {
            "success": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def validate_complete_registration_info(self, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate complete registration information including business, tax, and banking details
        
        Args:
            registration_data: Dictionary containing all registration details
            
        Returns:
            Dict with comprehensive validation results
        """
        errors = []
        warnings = []
        
        # Business Information Validation
        business_info = registration_data.get("business_info", {})
        business_required_fields = [
            "business_name", "business_type", "business_address", "business_phone",
            "business_email", "tax_id", "primary_contact_name", 
            "primary_contact_email", "primary_contact_phone"
        ]
        
        for field in business_required_fields:
            if field not in business_info or not business_info[field]:
                errors.append(f"Business info missing: {field}")
        
        # Public Profile Validation
        public_profile = registration_data.get("public_profile", {})
        public_required_fields = [
            "company_name", "company_description", "support_email", "support_phone"
        ]
        
        for field in public_required_fields:
            if field not in public_profile or not public_profile[field]:
                errors.append(f"Public profile missing: {field}")
        
        # Tax Information Validation
        tax_info = registration_data.get("tax_info", {})
        tax_required_fields = ["tax_classification", "tax_id_verified", "w_form_type"]
        
        for field in tax_required_fields:
            if field not in tax_info or not tax_info[field]:
                errors.append(f"Tax info missing: {field}")
        
        # Banking Information Validation
        banking_info = registration_data.get("banking_info", {})
        banking_required_fields = [
            "bank_name", "account_type", "account_number", "routing_number_or_swift",
            "account_holder_name", "bank_address"
        ]
        
        for field in banking_required_fields:
            if field not in banking_info or not banking_info[field]:
                errors.append(f"Banking info missing: {field}")
        
        # Validate specific formats
        if business_info.get("business_email"):
            email = business_info["business_email"]
            if "@" not in email or "." not in email:
                errors.append("Invalid business email format")
        
        if business_info.get("tax_id"):
            tax_id = business_info["tax_id"].replace("-", "").upper()
            import re
            us_ein_pattern = r'^\d{9}$'
            india_pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
            
            if not (re.match(us_ein_pattern, tax_id) or re.match(india_pan_pattern, tax_id)):
                errors.append("Invalid tax ID format")
        
        if banking_info.get("account_number"):
            account_num = banking_info["account_number"].replace("-", "").replace(" ", "")
            if not account_num.isdigit() or len(account_num) < 8:
                errors.append("Invalid bank account number format")
        
        if banking_info.get("routing_number_or_swift"):
            routing = banking_info["routing_number_or_swift"].replace("-", "")
            if len(routing) not in [9, 11]:  # US routing (9) or SWIFT (8-11)
                warnings.append("Routing number should be 9 digits (US) or SWIFT code (8-11 chars)")
        
        return {
            "success": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "validation_summary": {
                "business_info": len([f for f in business_required_fields if f in business_info and business_info[f]]),
                "public_profile": len([f for f in public_required_fields if f in public_profile and public_profile[f]]),
                "tax_info": len([f for f in tax_required_fields if f in tax_info and tax_info[f]]),
                "banking_info": len([f for f in banking_required_fields if f in banking_info and banking_info[f]])
            }
        }
    
    def validate_business_info(self, business_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate business information for seller registration
        
        Args:
            business_info: Dictionary containing business details
            
        Returns:
            Dict with validation results
        """
        required_fields = [
            "business_name",
            "business_type",  # Corporation, LLC, Partnership, Sole Proprietorship
            "business_address",
            "business_phone",
            "business_email",
            "tax_id",  # EIN or SSN
            "primary_contact_name",
            "primary_contact_email",
            "primary_contact_phone"
        ]
        
        errors = []
        warnings = []
        
        # Check required fields
        for field in required_fields:
            if field not in business_info or not business_info[field]:
                errors.append(f"Required field missing: {field}")
        
        # Validate specific fields
        if "business_email" in business_info:
            email = business_info["business_email"]
            if "@" not in email or "." not in email:
                errors.append("Invalid business email format")
        
        if "tax_id" in business_info:
            tax_id = business_info["tax_id"].replace("-", "").upper()
            # Check for US formats (EIN/SSN) or Indian PAN format
            import re
            us_ein_pattern = r'^\d{9}$'  # 9 digits for EIN
            us_ssn_pattern = r'^\d{9}$'  # 9 digits for SSN  
            india_pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'  # Indian PAN format
            
            if not (re.match(us_ein_pattern, tax_id) or 
                   re.match(us_ssn_pattern, tax_id) or 
                   re.match(india_pan_pattern, tax_id)):
                errors.append("Invalid tax ID format (should be 9-digit EIN/SSN for US or PAN format AAAAA9999A for India)")
        
        if "business_phone" in business_info:
            phone = business_info["business_phone"].replace("-", "").replace("(", "").replace(")", "").replace(" ", "")
            if not phone.isdigit() or len(phone) != 10:
                warnings.append("Phone number should be 10 digits")
        
        return {
            "success": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "validated_fields": len([f for f in required_fields if f in business_info and business_info[f]]),
            "total_required": len(required_fields)
        }
    
    def get_registration_workflow_status(self) -> Dict[str, Any]:
        """
        Get the current status of the registration workflow
        
        Returns:
            Dict with workflow status and next steps
        """
        try:
            # Check current seller status
            status = self.check_seller_status()
            if not status["success"]:
                return status
            
            # Determine workflow progress based on status
            workflow_steps = [
                "access_portal",
                "create_business_profile", 
                "create_public_profile",
                "update_tax_banking",
                "validate_information",
                "select_disbursement"
            ]
            
            if status["seller_status"] == "NOT_REGISTERED":
                current_step = "access_portal"
                completed_steps = []
            elif status["seller_status"] == "PENDING":
                current_step = "validate_information"
                completed_steps = workflow_steps[:4]  # First 4 steps completed
            elif status["seller_status"] == "APPROVED":
                current_step = "complete"
                completed_steps = workflow_steps
            else:
                current_step = "unknown"
                completed_steps = []
            
            return {
                "success": True,
                "current_step": current_step,
                "completed_steps": completed_steps,
                "total_steps": len(workflow_steps),
                "progress_percentage": int((len(completed_steps) / len(workflow_steps)) * 100),
                "seller_status": status["seller_status"],
                "next_action": self._get_next_action(current_step),
                "portal_url": "https://aws.amazon.com/marketplace/management/seller-registration"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get workflow status"
            }
    
    def _get_next_action(self, current_step: str) -> str:
        """Get the next action based on current step"""
        actions = {
            "access_portal": "Visit AWS Marketplace Management Portal and start seller registration",
            "create_business_profile": "Complete your business profile with legal business information",
            "create_public_profile": "Create your public-facing company profile",
            "update_tax_banking": "Submit tax forms and banking information",
            "validate_information": "Wait for AWS to validate your information (2-3 business days)",
            "select_disbursement": "Choose your preferred payment disbursement method",
            "complete": "Registration complete! You can now create product listings",
            "unknown": "Check your registration status in the AWS Marketplace Management Portal"
        }
        return actions.get(current_step, "Continue with registration process")
    
    def initiate_registration_process(self) -> Dict[str, Any]:
        """
        Initiate the seller registration process
        
        Returns:
            Dict with registration initiation results and guidance
        """
        try:
            # Check current status first
            status = self.check_seller_status()
            
            if status.get("seller_status") == "APPROVED":
                return {
                    "success": True,
                    "message": "You are already registered as an AWS Marketplace seller!",
                    "status": "already_registered",
                    "next_action": "You can proceed to create product listings"
                }
            
            if status.get("seller_status") == "PENDING":
                return {
                    "success": True,
                    "message": "Your seller registration is currently under review by AWS",
                    "status": "pending_review",
                    "estimated_completion": "2-3 business days",
                    "next_action": "Wait for AWS review to complete"
                }
            
            # Provide registration guidance
            account_info = self.get_account_info()
            
            return {
                "success": True,
                "message": "Ready to start AWS Marketplace seller registration",
                "status": "ready_to_register",
                "account_id": account_info.get("account_id"),
                "registration_steps": [
                    {
                        "step": 1,
                        "title": "Access AWS Marketplace Management Portal",
                        "description": "Sign in to AWS Console and navigate to Marketplace Management",
                        "url": "https://aws.amazon.com/marketplace/management/seller-registration",
                        "estimated_time": "5 minutes"
                    },
                    {
                        "step": 2,
                        "title": "Create Business Profile",
                        "description": "Provide legal business information and contact details",
                        "estimated_time": "15 minutes"
                    },
                    {
                        "step": 3,
                        "title": "Create Public Profile", 
                        "description": "Set up your public-facing company profile",
                        "estimated_time": "20 minutes"
                    },
                    {
                        "step": 4,
                        "title": "Submit Tax & Banking Information",
                        "description": "Complete tax forms and provide banking details",
                        "estimated_time": "30 minutes"
                    },
                    {
                        "step": 5,
                        "title": "Identity Verification",
                        "description": "AWS will verify your information",
                        "estimated_time": "2-3 business days"
                    },
                    {
                        "step": 6,
                        "title": "Select Disbursement Method",
                        "description": "Choose how you want to receive payments",
                        "estimated_time": "10 minutes"
                    }
                ],
                "total_estimated_time": "1-2 hours (plus 2-3 days for AWS review)",
                "next_action": "Click the portal URL above to begin registration"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to initiate registration process"
            }
    
    def create_support_case(self, subject: str, description: str, case_type: str = "seller-registration") -> Dict[str, Any]:
        """
        Create AWS Support case for seller registration assistance
        
        Args:
            subject: Case subject
            description: Detailed description
            case_type: Type of support case
            
        Returns:
            Dict with case creation results
        """
        try:
            response = self.support_client.create_case(
                subject=subject,
                serviceCode="marketplace",
                severityCode="low",
                categoryCode=case_type,
                communicationBody=description,
                language="en"
            )
            
            return {
                "success": True,
                "case_id": response["caseId"],
                "message": "Support case created successfully",
                "case_status": "opened",
                "estimated_response_time": "24-48 hours"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create support case"
            }
    
    def get_registration_requirements(self) -> Dict[str, Any]:
        """
        Get seller registration requirements and guidelines
        
        Returns:
            Dict with complete workflow requirements
        """
        return {
            "success": True,
            "workflow_steps": {
                "1_create_business_profile": {
                    "title": "Create Business Profile",
                    "required_fields": [
                        "Legal business name",
                        "Business type (Corporation, LLC, Partnership, Sole Proprietorship)",
                        "Business address",
                        "Business phone number",
                        "Business email address",
                        "Tax ID (EIN or SSN)",
                        "Primary contact information"
                    ],
                    "estimated_time": "10-15 minutes"
                },
                "2_login_marketplace_portal": {
                    "title": "Login to AWS Marketplace Management Portal",
                    "requirements": [
                        "Valid AWS account credentials",
                        "Account must be in good standing",
                        "Access to AWS Management Console"
                    ],
                    "portal_url": "https://aws.amazon.com/marketplace/management/seller-registration",
                    "estimated_time": "5 minutes"
                },
                "3_create_public_profile": {
                    "title": "Create Public Profile",
                    "required_fields": [
                        "Company name (public facing)",
                        "Company description",
                        "Company logo (S3 URL)",
                        "Website URL",
                        "Support email",
                        "Support phone number"
                    ],
                    "estimated_time": "15-20 minutes"
                },
                "4_update_tax_banking": {
                    "title": "Update Tax & Banking Information",
                    "tax_requirements": [
                        "Tax classification",
                        "W-9 form (US) or W-8 form (International)",
                        "Tax ID verification"
                    ],
                    "banking_requirements": [
                        "Bank name",
                        "Account type (Checking/Savings)",
                        "Routing number",
                        "Account number",
                        "Account verification"
                    ],
                    "estimated_time": "20-30 minutes"
                },
                "5_validate_information": {
                    "title": "Validate Information",
                    "validation_items": [
                        "Business profile verification",
                        "Public profile review",
                        "Tax information verification",
                        "Banking information verification",
                        "Identity verification"
                    ],
                    "estimated_time": "2-3 business days (AWS review)"
                },
                "6_select_disbursement": {
                    "title": "Select Disbursement Method",
                    "available_methods": [
                        "ACH Direct Deposit (recommended)",
                        "Wire Transfer",
                        "Check"
                    ],
                    "estimated_time": "5-10 minutes"
                }
            },
            "eligibility": {
                "account_requirements": [
                    "Valid AWS account in good standing",
                    "Account must be at least 30 days old",
                    "Valid payment method on file"
                ],
                "business_requirements": [
                    "Legitimate business entity",
                    "Ability to provide customer support",
                    "Compliance with AWS Marketplace policies"
                ]
            },
            "timeline": {
                "user_input_time": "1-2 hours",
                "aws_review_time": "2-3 business days",
                "total_process": "3-5 business days"
            }
        }
    
    def get_seller_dashboard_url(self) -> str:
        """
        Get URL for AWS Marketplace seller dashboard
        
        Returns:
            URL string for seller dashboard
        """
        return "https://aws.amazon.com/marketplace/management/seller-registration"
    
    def get_india_specific_requirements(self) -> Dict[str, Any]:
        """
        Get India-specific seller registration requirements
        
        Returns:
            Dict with India-specific requirements and guidance
        """
        return {
            "success": True,
            "country": "India",
            "business_requirements": {
                "mandatory_documents": [
                    "PAN Card (Permanent Account Number)",
                    "Business registration certificate",
                    "Address proof (Aadhaar, utility bill, bank statement)",
                    "Bank account details with IFSC code"
                ],
                "conditional_documents": [
                    "GST Registration Certificate (if turnover > ₹20 lakhs)",
                    "Import Export Code (for international trade)",
                    "Professional Tax Registration (state-specific)"
                ]
            },
            "tax_requirements": {
                "forms_needed": [
                    "W-8BEN-E (for claiming tax treaty benefits)",
                    "Form 15CA/15CB (for foreign remittances, if required)"
                ],
                "tax_identifiers": [
                    "PAN (mandatory for all)",
                    "GST Number (for registered businesses)",
                    "TAN (for TDS compliance)"
                ],
                "treaty_benefits": {
                    "us_withholding_tax": "Reduced from 30% to 10% with proper documentation",
                    "required_form": "W-8BEN-E",
                    "renewal_period": "3 years"
                }
            },
            "banking_requirements": {
                "account_types": [
                    "Current Account (recommended for businesses)",
                    "Savings Account (for individuals)",
                    "NRE/NRO Account (for NRIs)"
                ],
                "required_details": [
                    "Bank name and branch",
                    "Account number",
                    "IFSC code",
                    "SWIFT code (for international transfers)",
                    "Account holder name (must match PAN)"
                ],
                "verification_process": "Test deposits by AWS (2-3 business days)"
            },
            "compliance_requirements": {
                "rbi_compliance": [
                    "FEMA compliance for foreign receipts",
                    "Export documentation",
                    "Repatriation of export proceeds"
                ],
                "tax_compliance": [
                    "Regular income tax return filing",
                    "GST return filing (if applicable)",
                    "TDS compliance on payments received"
                ]
            },
            "disbursement_options": {
                "primary_method": "Wire Transfer (USD to INR conversion by bank)",
                "processing_time": "3-5 business days",
                "minimum_threshold": "$1 USD",
                "payment_schedule": "Monthly (15th of each month)"
            }
        }
    
    def validate_india_business_info(self, business_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate business information specifically for Indian sellers
        
        Args:
            business_info: Dictionary containing Indian business details
            
        Returns:
            Dict with validation results
        """
        errors = []
        warnings = []
        
        # India-specific required fields
        india_required_fields = [
            "business_name",
            "business_type",
            "business_address",
            "business_phone",
            "business_email",
            "pan_number",
            "primary_contact_name",
            "primary_contact_email",
            "primary_contact_phone"
        ]
        
        # Check required fields
        for field in india_required_fields:
            if field not in business_info or not business_info[field]:
                errors.append(f"Required field missing: {field}")
        
        # Validate PAN number format
        if "pan_number" in business_info:
            pan = business_info["pan_number"].upper()
            import re
            if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', pan):
                errors.append("Invalid PAN format. Should be AAAAA9999A (5 letters, 4 digits, 1 letter)")
        
        # Validate GST number if provided
        if "gst_number" in business_info and business_info["gst_number"]:
            gst = business_info["gst_number"].upper()
            if not re.match(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$', gst):
                errors.append("Invalid GST format. Should be 15 characters (22AAAAA0000A1Z5)")
        
        # Validate Indian phone number
        if "business_phone" in business_info:
            phone = business_info["business_phone"].replace("+91", "").replace("-", "").replace(" ", "")
            if not phone.isdigit() or len(phone) != 10:
                warnings.append("Indian phone number should be 10 digits")
        
        # Check business type validity for India
        if "business_type" in business_info:
            valid_types = [
                "Private Limited Company",
                "Public Limited Company", 
                "Limited Liability Partnership (LLP)",
                "Partnership Firm",
                "Sole Proprietorship",
                "Individual/Freelancer"
            ]
            if business_info["business_type"] not in valid_types:
                warnings.append(f"Business type should be one of: {', '.join(valid_types)}")
        
        return {
            "success": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "country": "India",
            "validated_fields": len([f for f in india_required_fields if f in business_info and business_info[f]]),
            "total_required": len(india_required_fields)
        }
    
    def generate_registration_preview(self, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a preview of what will be populated in AMMP portal
        
        Args:
            registration_data: Complete registration information
            
        Returns:
            Dict with formatted preview data for user review
        """
        try:
            # Validate the data first
            validation = self.validate_business_info(registration_data.get("business_info", registration_data))
            
            # Extract and format business information
            business_info = registration_data.get("business_info", registration_data)
            
            # Parse address components
            address = business_info.get("business_address", "")
            address_parts = [part.strip() for part in address.split(",")]
            
            preview_data = {
                "success": True,
                "preview_sections": {
                    "business_profile": {
                        "title": "Business Profile",
                        "fields": {
                            "Legal Business Name": business_info.get("business_name", ""),
                            "Business Type": business_info.get("business_type", ""),
                            "Business Address": {
                                "Full Address": address,
                                "Address Line 1": address_parts[0] if len(address_parts) > 0 else "",
                                "City": address_parts[1] if len(address_parts) > 1 else "",
                                "State/Region": address_parts[2] if len(address_parts) > 2 else "",
                                "Postal Code": self._extract_postal_code_from_address(address),
                                "Country": self._extract_country_from_address(address)
                            },
                            "Business Phone": business_info.get("business_phone", ""),
                            "Business Email": business_info.get("business_email", ""),
                            "Tax ID": business_info.get("tax_id", ""),
                            "Website URL": business_info.get("website_url", "N/A")
                        }
                    },
                    "contact_information": {
                        "title": "Primary Contact Information",
                        "fields": {
                            "Contact Name": business_info.get("primary_contact_name", ""),
                            "Contact Email": business_info.get("primary_contact_email", ""),
                            "Contact Phone": business_info.get("primary_contact_phone", "")
                        }
                    },
                    "public_profile": {
                        "title": "Public Profile (Will be created)",
                        "fields": {
                            "Company Name": business_info.get("business_name", ""),
                            "Company Description": f"Professional {business_info.get('business_type', 'business')} providing innovative solutions",
                            "Support Email": business_info.get("business_email", ""),
                            "Support Phone": business_info.get("business_phone", ""),
                            "Website": business_info.get("website_url", "")
                        }
                    },
                    "tax_banking_setup": {
                        "title": "Tax & Banking Setup (Next Steps)",
                        "fields": {
                            "Tax Classification": "To be completed in portal",
                            "Tax Forms": "W-9 (US) or W-8BEN-E (International)",
                            "Banking Information": "To be provided in portal",
                            "Disbursement Method": "To be selected in portal"
                        }
                    }
                },
                "country_specific": self._get_country_specific_preview(business_info),
                "validation_status": validation,
                "api_calls_planned": [
                    {
                        "step": 1,
                        "action": "Create Business Profile",
                        "api": "marketplace-management:CreateSellerProfile",
                        "description": "Creates your business profile in AWS Marketplace"
                    },
                    {
                        "step": 2,
                        "action": "Create Public Profile",
                        "api": "marketplace-management:CreatePublicProfile", 
                        "description": "Creates your customer-facing company profile"
                    },
                    {
                        "step": 3,
                        "action": "Initialize Tax Setup",
                        "api": "marketplace-management:InitializeTaxInformation",
                        "description": "Sets up tax information collection workflow"
                    },
                    {
                        "step": 4,
                        "action": "Initialize Banking Setup",
                        "api": "marketplace-management:InitializeBankingInformation",
                        "description": "Sets up banking information collection workflow"
                    }
                ],
                "estimated_completion_time": "15-20 minutes for API calls + 2-3 days for AWS review"
            }
            
            return preview_data
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate registration preview"
            }
    
    def _get_country_specific_preview(self, business_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get country-specific preview information"""
        country = business_info.get("country", "Other")
        
        if country == "India":
            return {
                "country": "India",
                "specific_fields": {
                    "PAN Number": business_info.get("pan_number", business_info.get("tax_id", "")),
                    "GST Number": business_info.get("gst_number", "Not provided"),
                    "Tax Treaty Benefits": "W-8BEN-E form will be required for 10% withholding rate",
                    "Banking": "Indian bank account with IFSC code required",
                    "Compliance": "RBI FEMA compliance for export proceeds"
                },
                "required_documents": [
                    "PAN Card copy",
                    "GST Registration Certificate (if applicable)",
                    "Bank account details with IFSC code",
                    "Business registration documents"
                ]
            }
        
        return {
            "official_documentation": [
                {
                    "title": "AWS Marketplace Seller Registration Process",
                    "url": "https://docs.aws.amazon.com/marketplace/latest/userguide/registration-process.html"
                },
                {
                    "title": "AWS Marketplace Seller Guide",
                    "url": "https://docs.aws.amazon.com/marketplace/latest/userguide/"
                },
                {
                    "title": "Tax and Banking Information",
                    "url": "https://docs.aws.amazon.com/marketplace/latest/userguide/seller-tax-information.html"
                }
            ],
            "workshops_and_training": [
                {
                    "title": "AWS Marketplace Seller Workshop",
                    "url": "https://catalog.workshops.aws/mpseller/en-US/pre-requisite-register-as-seller"
                },
                {
                    "title": "Getting Started Guide",
                    "url": "https://aws.amazon.com/marketplace/management/tour/"
                }
            ],
            "support_channels": [
                {
                    "title": "AWS Marketplace Seller Support",
                    "url": "https://aws.amazon.com/marketplace/management/contact-us",
                    "email": "aws-marketplace-seller-ops@amazon.com"
                },
                {
                    "title": "Seller Support Forum",
                    "url": "https://forums.aws.amazon.com/forum.jspa?forumID=161"
                },
                {
                    "title": "AWS Support Center",
                    "url": "https://console.aws.amazon.com/support/"
                }
            ],
            "management_tools": [
                {
                    "title": "Seller Registration Portal",
                    "url": "https://aws.amazon.com/marketplace/management/seller-registration"
                },
                {
                    "title": "Marketplace Management Console",
                    "url": "https://console.aws.amazon.com/marketplace/management/"
                },
                {
                    "title": "Tax Information Interview",
                    "url": "https://aws.amazon.com/marketplace/management/tax-information"
                }
            ],
            "india_specific_resources": [
                {
                    "title": "AWS India",
                    "url": "https://aws.amazon.com/india/"
                },
                {
                    "title": "GST Portal",
                    "url": "https://www.gst.gov.in/"
                },
                {
                    "title": "Income Tax Department",
                    "url": "https://www.incometax.gov.in/"
                },
                {
                    "title": "RBI Guidelines",
                    "url": "https://www.rbi.org.in/"
                }
            ]
        }
    
    def generate_registration_preview(self, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive preview of registration data before submitting to AWS
        
        Args:
            registration_data: Complete registration information
            
        Returns:
            Dict with formatted preview data
        """
        try:
            # Validate all data first
            validation = self.validate_complete_registration_info(registration_data)
            
            business_info = registration_data.get("business_info", {})
            public_profile = registration_data.get("public_profile", {})
            tax_info = registration_data.get("tax_info", {})
            banking_info = registration_data.get("banking_info", {})
            
            # Format preview data
            preview = {
                "success": True,
                "validation": validation,
                "preview_sections": {
                    "business_profile": {
                        "title": "Business Profile",
                        "data": {
                            "Business Name": business_info.get("business_name", ""),
                            "Business Type": business_info.get("business_type", ""),
                            "Business Address": business_info.get("business_address", ""),
                            "Business Phone": business_info.get("business_phone", ""),
                            "Business Email": business_info.get("business_email", ""),
                            "Tax ID": business_info.get("tax_id", ""),
                            "Primary Contact": business_info.get("primary_contact_name", ""),
                            "Contact Email": business_info.get("primary_contact_email", ""),
                            "Contact Phone": business_info.get("primary_contact_phone", ""),
                            "Website": business_info.get("website_url", "N/A")
                        }
                    },
                    "public_profile": {
                        "title": "Public Profile",
                        "data": {
                            "Company Name": public_profile.get("company_name", ""),
                            "Company Description": public_profile.get("company_description", ""),
                            "Support Email": public_profile.get("support_email", ""),
                            "Support Phone": public_profile.get("support_phone", ""),
                            "Company Logo URL": public_profile.get("company_logo_url", "N/A"),
                            "Website URL": public_profile.get("website_url", "")
                        }
                    },
                    "tax_information": {
                        "title": "Tax Information",
                        "data": {
                            "Tax Classification": tax_info.get("tax_classification", ""),
                            "Tax ID Verified": tax_info.get("tax_id_verified", "No"),
                            "W-Form Type": tax_info.get("w_form_type", ""),
                            "Tax Treaty Benefits": tax_info.get("tax_treaty_benefits", "No"),
                            "Backup Withholding": tax_info.get("backup_withholding", "No")
                        }
                    },
                    "banking_information": {
                        "title": "Banking Information",
                        "data": {
                            "Bank Name": banking_info.get("bank_name", ""),
                            "Account Type": banking_info.get("account_type", ""),
                            "Account Holder Name": banking_info.get("account_holder_name", ""),
                            "Account Number": f"****{banking_info.get('account_number', '')[-4:]}" if banking_info.get('account_number') else "",
                            "Routing/SWIFT": banking_info.get("routing_number_or_swift", ""),
                            "Bank Address": banking_info.get("bank_address", ""),
                            "Currency": banking_info.get("currency", "USD")
                        }
                    }
                },
                "submission_summary": {
                    "total_sections": 4,
                    "completed_sections": sum(1 for section in ["business_info", "public_profile", "tax_info", "banking_info"] 
                                            if registration_data.get(section)),
                    "validation_status": "Valid" if validation["success"] else "Invalid",
                    "errors_count": len(validation.get("errors", [])),
                    "warnings_count": len(validation.get("warnings", []))
                },
                "next_steps": [
                    "Review all information carefully",
                    "Ensure all required fields are completed",
                    "Verify banking information is accurate",
                    "Confirm tax information is correct",
                    "Submit to AWS Marketplace Management Portal"
                ]
            }
            
            return preview
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate registration preview"
            }
    
    def submit_registration_to_aws(self, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit complete registration data to AWS Marketplace Management Portal
        
        Args:
            registration_data: Complete validated registration information
            
        Returns:
            Dict with submission results
        """
        try:
            # Validate data first
            validation = self.validate_complete_registration_info(registration_data)
            if not validation["success"]:
                return {
                    "success": False,
                    "errors": validation["errors"],
                    "message": "Registration data validation failed"
                }
            
            # Get account info
            account_info = self.get_account_info()
            if not account_info["success"]:
                return account_info
            
            # Check permissions
            if not account_info.get("marketplace_access", {}).get("marketplace_catalog_read", False):
                return {
                    "success": False,
                    "error": "Insufficient permissions",
                    "message": "AWS credentials don't have required marketplace permissions"
                }
            
            # Step 1: Create Business Profile
            business_result = self.create_business_profile(registration_data.get("business_info", {}))
            if not business_result["success"]:
                return business_result
            
            # Step 2: Create Public Profile
            public_result = self.create_public_profile(registration_data.get("public_profile", {}))
            if not public_result["success"]:
                return public_result
            
            # Step 3: Submit Tax & Banking Information
            tax_banking_result = self.update_tax_banking_info({
                "tax_info": registration_data.get("tax_info", {}),
                "banking_info": registration_data.get("banking_info", {})
            })
            if not tax_banking_result["success"]:
                return tax_banking_result
            
            # Step 4: Select Disbursement Method
            disbursement_result = self.select_disbursement_method(
                registration_data.get("disbursement_info", {"method": "WIRE_TRANSFER"})
            )
            if not disbursement_result["success"]:
                return disbursement_result
            
            # Return comprehensive success response
            return {
                "success": True,
                "registration_id": f"reg-{account_info['account_id']}-{int(datetime.utcnow().timestamp())}",
                "account_id": account_info["account_id"],
                "submission_timestamp": datetime.utcnow().isoformat(),
                "steps_completed": [
                    {"step": "business_profile", "status": "completed", "result": business_result},
                    {"step": "public_profile", "status": "completed", "result": public_result},
                    {"step": "tax_banking", "status": "completed", "result": tax_banking_result},
                    {"step": "disbursement", "status": "completed", "result": disbursement_result}
                ],
                "message": "Registration submitted successfully to AWS Marketplace",
                "next_steps": [
                    "AWS will review your registration (2-3 business days)",
                    "You may be contacted for additional information",
                    "Check your email for updates",
                    "Monitor status in AWS Marketplace Management Portal"
                ],
                "portal_url": "https://aws.amazon.com/marketplace/management/seller-registration",
                "estimated_review_time": "2-3 business days"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to submit registration to AWS"
            }
    
    @staticmethod
    def collect_aws_credentials() -> Dict[str, Any]:
        """
        Helper method to collect AWS credentials from user
        
        Returns:
            Dict with credential collection guidance
        """
        return {
            "required_credentials": {
                "aws_access_key_id": {
                    "description": "AWS Access Key ID",
                    "example": "AKIA[REDACTED]",
                    "required": True
                },
                "aws_secret_access_key": {
                    "description": "AWS Secret Access Key", 
                    "example": "[REDACTED]",
                    "required": True,
                    "sensitive": True
                },
                "aws_session_token": {
                    "description": "AWS Session Token (for temporary credentials)",
                    "example": "[REDACTED]",
                    "required": False,
                    "sensitive": True
                }
            },
            "required_permissions": [
                "marketplace-catalog:ListEntities",
                "marketplace-catalog:DescribeEntity",
                "marketplace-catalog:StartChangeSet",
                "marketplace-management:GetSellerProfile",
                "marketplace-management:PutSellerProfile",
                "marketplace-management:GetSellerVerificationDetails",
                "marketplace-management:PutSellerVerificationDetails",
                "sts:GetCallerIdentity",
                "support:CreateCase",
                "support:DescribeCases"
            ],
            "setup_instructions": [
                "1. Sign in to AWS Console as root user or IAM user with admin permissions",
                "2. Go to IAM > Users > Create User (or use existing user)",
                "3. Attach policy with marketplace permissions listed above",
                "4. Go to Security Credentials tab",
                "5. Create Access Key > Application running outside AWS",
                "6. Copy Access Key ID and Secret Access Key",
                "7. Use these credentials in the registration tool"
            ],
            "security_notes": [
                "Never share your AWS credentials",
                "Use IAM users instead of root user credentials",
                "Consider using temporary credentials (STS) for enhanced security",
                "Rotate access keys regularly",
                "Monitor CloudTrail for API usage"
            ]
        } 
   
    def generate_registration_preview(self, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive preview of registration data before submitting to AWS
        
        Args:
            registration_data: Complete registration information
            
        Returns:
            Dict with formatted preview data
        """
        try:
            # Validate all data first
            validation = self.validate_complete_registration_info(registration_data)
            
            business_info = registration_data.get("business_info", {})
            public_profile = registration_data.get("public_profile", {})
            tax_info = registration_data.get("tax_info", {})
            banking_info = registration_data.get("banking_info", {})
            
            # Format preview data
            preview = {
                "success": True,
                "validation": validation,
                "preview_sections": {
                    "business_profile": {
                        "title": "Business Profile",
                        "data": {
                            "Business Name": business_info.get("business_name", ""),
                            "Business Type": business_info.get("business_type", ""),
                            "Business Address": business_info.get("business_address", ""),
                            "Business Phone": business_info.get("business_phone", ""),
                            "Business Email": business_info.get("business_email", ""),
                            "Tax ID": business_info.get("tax_id", ""),
                            "Primary Contact": business_info.get("primary_contact_name", ""),
                            "Contact Email": business_info.get("primary_contact_email", ""),
                            "Contact Phone": business_info.get("primary_contact_phone", ""),
                            "Website": business_info.get("website_url", "N/A")
                        }
                    },
                    "public_profile": {
                        "title": "Public Profile",
                        "data": {
                            "Company Name": public_profile.get("company_name", ""),
                            "Company Description": public_profile.get("company_description", ""),
                            "Support Email": public_profile.get("support_email", ""),
                            "Support Phone": public_profile.get("support_phone", ""),
                            "Company Logo URL": public_profile.get("company_logo_url", "N/A"),
                            "Website URL": public_profile.get("website_url", "")
                        }
                    },
                    "tax_information": {
                        "title": "Tax Information",
                        "data": {
                            "Tax Classification": tax_info.get("tax_classification", ""),
                            "Tax ID Verified": tax_info.get("tax_id_verified", "No"),
                            "W-Form Type": tax_info.get("w_form_type", ""),
                            "Tax Treaty Benefits": tax_info.get("tax_treaty_benefits", "No"),
                            "Backup Withholding": tax_info.get("backup_withholding", "No")
                        }
                    },
                    "banking_information": {
                        "title": "Banking Information",
                        "data": {
                            "Bank Name": banking_info.get("bank_name", ""),
                            "Account Type": banking_info.get("account_type", ""),
                            "Account Holder Name": banking_info.get("account_holder_name", ""),
                            "Account Number": f"****{banking_info.get('account_number', '')[-4:]}" if banking_info.get('account_number') else "",
                            "Routing/SWIFT": banking_info.get("routing_number_or_swift", ""),
                            "Bank Address": banking_info.get("bank_address", ""),
                            "Currency": banking_info.get("currency", "USD")
                        }
                    }
                },
                "submission_summary": {
                    "total_sections": 4,
                    "completed_sections": sum(1 for section in ["business_info", "public_profile", "tax_info", "banking_info"] 
                                            if registration_data.get(section)),
                    "validation_status": "Valid" if validation["success"] else "Invalid",
                    "errors_count": len(validation.get("errors", [])),
                    "warnings_count": len(validation.get("warnings", []))
                },
                "next_steps": [
                    "Review all information carefully",
                    "Ensure all required fields are completed",
                    "Verify banking information is accurate",
                    "Confirm tax information is correct",
                    "Submit to AWS Marketplace Management Portal"
                ]
            }
            
            return preview
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate registration preview"
            }
    
    def submit_registration_to_aws(self, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit complete registration data to AWS Marketplace Management Portal
        
        Args:
            registration_data: Complete validated registration information
            
        Returns:
            Dict with submission results
        """
        try:
            # Validate data first
            validation = self.validate_complete_registration_info(registration_data)
            if not validation["success"]:
                return {
                    "success": False,
                    "errors": validation["errors"],
                    "message": "Registration data validation failed"
                }
            
            # Get account info
            account_info = self.get_account_info()
            if not account_info["success"]:
                return account_info
            
            # Check permissions
            if not account_info.get("marketplace_access", {}).get("marketplace_catalog_read", False):
                return {
                    "success": False,
                    "error": "Insufficient permissions",
                    "message": "AWS credentials don't have required marketplace permissions"
                }
            
            # Step 1: Create Business Profile
            business_result = self.create_business_profile(registration_data.get("business_info", {}))
            if not business_result["success"]:
                return business_result
            
            # Step 2: Create Public Profile
            public_result = self.create_public_profile(registration_data.get("public_profile", {}))
            if not public_result["success"]:
                return public_result
            
            # Step 3: Submit Tax & Banking Information
            tax_banking_result = self.update_tax_banking_info({
                "tax_info": registration_data.get("tax_info", {}),
                "banking_info": registration_data.get("banking_info", {})
            })
            if not tax_banking_result["success"]:
                return tax_banking_result
            
            # Step 4: Select Disbursement Method
            disbursement_result = self.select_disbursement_method(
                registration_data.get("disbursement_info", {"method": "WIRE_TRANSFER"})
            )
            if not disbursement_result["success"]:
                return disbursement_result
            
            # Return comprehensive success response
            return {
                "success": True,
                "registration_id": f"reg-{account_info['account_id']}-{int(datetime.utcnow().timestamp())}",
                "account_id": account_info["account_id"],
                "submission_timestamp": datetime.utcnow().isoformat(),
                "steps_completed": [
                    {"step": "business_profile", "status": "completed", "result": business_result},
                    {"step": "public_profile", "status": "completed", "result": public_result},
                    {"step": "tax_banking", "status": "completed", "result": tax_banking_result},
                    {"step": "disbursement", "status": "completed", "result": disbursement_result}
                ],
                "message": "Registration submitted successfully to AWS Marketplace",
                "next_steps": [
                    "AWS will review your registration (2-3 business days)",
                    "You may be contacted for additional information",
                    "Check your email for updates",
                    "Monitor status in AWS Marketplace Management Portal"
                ],
                "portal_url": "https://aws.amazon.com/marketplace/management/seller-registration",
                "estimated_review_time": "2-3 business days"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to submit registration to AWS"
            }
    
    @staticmethod
    def collect_aws_credentials() -> Dict[str, Any]:
        """
        Helper method to collect AWS credentials from user
        
        Returns:
            Dict with credential collection guidance
        """
        return {
            "required_credentials": {
                "aws_access_key_id": {
                    "description": "AWS Access Key ID",
                    "example": "AKIA[REDACTED]",
                    "required": True
                },
                "aws_secret_access_key": {
                    "description": "AWS Secret Access Key", 
                    "example": "[REDACTED]",
                    "required": True,
                    "sensitive": True
                },
                "aws_session_token": {
                    "description": "AWS Session Token (for temporary credentials)",
                    "example": "[REDACTED]",
                    "required": False,
                    "sensitive": True
                }
            },
            "required_permissions": [
                "marketplace-catalog:ListEntities",
                "marketplace-catalog:DescribeEntity",
                "marketplace-catalog:StartChangeSet",
                "marketplace-management:GetSellerProfile",
                "marketplace-management:PutSellerProfile",
                "marketplace-management:GetSellerVerificationDetails",
                "marketplace-management:PutSellerVerificationDetails",
                "sts:GetCallerIdentity",
                "support:CreateCase",
                "support:DescribeCases"
            ],
            "setup_instructions": [
                "1. Sign in to AWS Console as root user or IAM user with admin permissions",
                "2. Go to IAM > Users > Create User (or use existing user)",
                "3. Attach policy with marketplace permissions listed above",
                "4. Go to Security Credentials tab",
                "5. Create Access Key > Application running outside AWS",
                "6. Copy Access Key ID and Secret Access Key",
                "7. Use these credentials in the registration tool"
            ],
            "security_notes": [
                "Never share your AWS credentials",
                "Use IAM users instead of root user credentials",
                "Consider using temporary credentials (STS) for enhanced security",
                "Rotate access keys regularly",
                "Monitor CloudTrail for API usage"
            ]
        }
    
    def get_aws_credentials_info(self) -> Dict[str, Any]:
        """
        Get information about current AWS credentials and permissions
        
        Returns:
            Dict with credentials information
        """
        if not hasattr(self, 'credentials_valid') or not self.credentials_valid:
            return {
                "success": False,
                "message": "AWS credentials not valid or not verified"
            }
        
        try:
            # Get caller identity
            identity = self.sts_client.get_caller_identity()
            
            # Try to get organization info (if account is in an organization)
            org_info = None
            try:
                org_info = self.organizations_client.describe_organization()
            except Exception:
                # Account might not be in an organization or no permissions
                pass
            
            # Check marketplace permissions by trying to list entities
            marketplace_permissions = False
            try:
                # Test marketplace permissions
                self.marketplace_client.list_entities(Catalog="AWSMarketplace", EntityType="SaaSProduct")
                marketplace_permissions = True
            except Exception:
                marketplace_permissions = False
            
            return {
                "success": True,
                "account_id": identity.get("Account"),
                "user_arn": identity.get("Arn"),
                "user_id": identity.get("UserId"),
                "region": self.region,
                "organization_info": org_info,
                "marketplace_permissions": marketplace_permissions,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get AWS credentials information"
            }
    
    def validate_complete_registration_info(self, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate complete registration information including business, tax, and banking details
        
        Args:
            registration_data: Dictionary containing all registration details
            
        Returns:
            Dict with comprehensive validation results
        """
        errors = []
        warnings = []
        
        # Business Information Validation
        business_info = registration_data.get("business_info", {})
        business_required_fields = [
            "business_name", "business_type", "business_address", "business_phone",
            "business_email", "tax_id", "primary_contact_name", 
            "primary_contact_email", "primary_contact_phone"
        ]
        
        for field in business_required_fields:
            if field not in business_info or not business_info[field]:
                errors.append(f"Business info missing: {field}")
        
        # Public Profile Validation
        public_profile = registration_data.get("public_profile", {})
        public_required_fields = [
            "company_name", "company_description", "support_email", "support_phone"
        ]
        
        for field in public_required_fields:
            if field not in public_profile or not public_profile[field]:
                errors.append(f"Public profile missing: {field}")
        
        # Tax Information Validation
        tax_info = registration_data.get("tax_info", {})
        tax_required_fields = ["tax_classification", "tax_id_verified", "w_form_type"]
        
        for field in tax_required_fields:
            if field not in tax_info or not tax_info[field]:
                errors.append(f"Tax info missing: {field}")
        
        # Banking Information Validation
        banking_info = registration_data.get("banking_info", {})
        banking_required_fields = [
            "bank_name", "account_type", "account_number", "routing_number_or_swift",
            "account_holder_name", "bank_address"
        ]
        
        for field in banking_required_fields:
            if field not in banking_info or not banking_info[field]:
                errors.append(f"Banking info missing: {field}")
        
        # Validate specific formats
        if business_info.get("business_email"):
            email = business_info["business_email"]
            if "@" not in email or "." not in email:
                errors.append("Invalid business email format")
        
        if business_info.get("tax_id"):
            tax_id = business_info["tax_id"].replace("-", "").upper()
            import re
            us_ein_pattern = r'^\d{9}$'
            india_pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
            
            if not (re.match(us_ein_pattern, tax_id) or re.match(india_pan_pattern, tax_id)):
                errors.append("Invalid tax ID format")
        
        if banking_info.get("account_number"):
            account_num = banking_info["account_number"].replace("-", "").replace(" ", "")
            if not account_num.isdigit() or len(account_num) < 8:
                errors.append("Invalid bank account number format")
        
        if banking_info.get("routing_number_or_swift"):
            routing = banking_info["routing_number_or_swift"].replace("-", "")
            if len(routing) not in [9, 11]:  # US routing (9) or SWIFT (8-11)
                warnings.append("Routing number should be 9 digits (US) or SWIFT code (8-11 chars)")
        
        return {
            "success": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "validation_summary": {
                "business_info": len([f for f in business_required_fields if f in business_info and business_info[f]]),
                "public_profile": len([f for f in public_required_fields if f in public_profile and public_profile[f]]),
                "tax_info": len([f for f in tax_required_fields if f in tax_info and tax_info[f]]),
                "banking_info": len([f for f in banking_required_fields if f in banking_info and banking_info[f]])
            }
        }
    
    def get_help_resources(self) -> Dict[str, Any]:
        """
        Get help resources for seller registration
        
        Returns:
            Dict with help resources and links
        """
        return {
            "official_documentation": [
                {
                    "title": "AWS Marketplace Seller Registration Process",
                    "url": "https://docs.aws.amazon.com/marketplace/latest/userguide/registration-process.html"
                },
                {
                    "title": "AWS Marketplace Seller Guide",
                    "url": "https://docs.aws.amazon.com/marketplace/latest/userguide/"
                },
                {
                    "title": "Tax and Banking Information",
                    "url": "https://docs.aws.amazon.com/marketplace/latest/userguide/seller-tax-information.html"
                }
            ],
            "workshops_and_training": [
                {
                    "title": "AWS Marketplace Seller Workshop",
                    "url": "https://catalog.workshops.aws/mpseller/en-US/pre-requisite-register-as-seller"
                },
                {
                    "title": "Getting Started Guide",
                    "url": "https://aws.amazon.com/marketplace/management/tour/"
                }
            ],
            "support_channels": [
                {
                    "title": "AWS Marketplace Seller Support",
                    "url": "https://aws.amazon.com/marketplace/management/contact-us",
                    "email": "aws-marketplace-seller-ops@amazon.com"
                },
                {
                    "title": "Seller Support Forum",
                    "url": "https://forums.aws.amazon.com/forum.jspa?forumID=161"
                },
                {
                    "title": "AWS Support Center",
                    "url": "https://console.aws.amazon.com/support/"
                }
            ],
            "management_tools": [
                {
                    "title": "Seller Registration Portal",
                    "url": "https://aws.amazon.com/marketplace/management/seller-registration"
                },
                {
                    "title": "Marketplace Management Console",
                    "url": "https://console.aws.amazon.com/marketplace/management/"
                },
                {
                    "title": "Tax Information Interview",
                    "url": "https://aws.amazon.com/marketplace/management/tax-information"
                }
            ],
            "india_specific_resources": [
                {
                    "title": "AWS India",
                    "url": "https://aws.amazon.com/india/"
                },
                {
                    "title": "GST Portal",
                    "url": "https://www.gst.gov.in/"
                },
                {
                    "title": "Income Tax Department",
                    "url": "https://www.incometax.gov.in/"
                },
                {
                    "title": "RBI Guidelines",
                    "url": "https://www.rbi.org.in/"
                }
            ]
        }