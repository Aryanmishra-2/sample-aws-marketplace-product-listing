"""Tools for AWS Marketplace Catalog API operations"""

import boto3
from typing import Dict, Any, List, Optional


class ListingTools:
    """AWS Marketplace listing management tools"""

    def __init__(self, region: str = "us-east-1", session=None):
        """
        Initialize ListingTools with AWS credentials
        
        Args:
            region: AWS region (default: us-east-1)
            session: boto3.Session object with credentials (recommended)
        """
        self.region = region
        self.session = session
        
        if session:
            self.catalog_client = session.client("marketplace-catalog", region_name=region)
        else:
            # Fallback to default credentials (not recommended for production)
            self.catalog_client = boto3.client("marketplace-catalog", region_name=region)
    
    def update_credentials(self, session):
        """Update AWS credentials using a boto3 session"""
        self.session = session
        self.catalog_client = session.client("marketplace-catalog", region_name=self.region)
        if session.region_name:
            self.region = session.region_name

    def get_entity_details(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """
        Get current entity details including revision number

        Args:
            entity_type: Entity type (e.g., "SaaSProduct@1.0", "Offer@1.0")
            entity_id: Entity identifier

        Returns:
            Dict with EntityIdentifier, EntityType, LastModifiedDate, and Details
        """
        try:
            # Strip revision suffix from entity_id if present (e.g., "prod-abc@1" -> "prod-abc")
            clean_entity_id = self._strip_revision_suffix(entity_id)
            
            response = self.catalog_client.describe_entity(
                Catalog="AWSMarketplace", EntityId=clean_entity_id
            )
            return {
                "success": True,
                "entity_id": response.get("EntityIdentifier"),
                "entity_type": response.get("EntityType"),
                "last_modified": response.get("LastModifiedDate"),
                "details": response.get("Details"),
                "entity_arn": response.get("EntityArn"),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _strip_revision_suffix(self, entity_id: str) -> str:
        """
        Strip revision suffix from entity identifier.
        
        AWS Marketplace entity identifiers can have revision suffixes like "@1", "@2", etc.
        These need to be stripped when making API calls that don't expect them.
        
        Args:
            entity_id: Entity identifier (e.g., "prod-abc@1" or "offer-xyz@2")
            
        Returns:
            Entity identifier without revision suffix (e.g., "prod-abc" or "offer-xyz")
        """
        if entity_id and '@' in entity_id:
            return entity_id.split('@')[0]
        return entity_id

    def create_product_minimal(self, product_title: str) -> Dict[str, Any]:
        """
        Create a minimal SaaS product with just the title

        This creates the product immediately so we can get the product_id,
        then update it with full details later.

        Args:
            product_title: Product name (required)

        Returns:
            Dict with change_set_id and status
        """
        try:
            change_set = [
                {
                    "ChangeType": "CreateProduct",
                    "ChangeName": "CreateProductChange",
                    "Entity": {"Type": "SaaSProduct@1.0"},
                    "DetailsDocument": {"ProductTitle": product_title},
                },
                {
                    "ChangeType": "CreateOffer",
                    "ChangeName": "CreateOfferChange",
                    "Entity": {"Type": "Offer@1.0"},
                    "DetailsDocument": {
                        "ProductId": "$CreateProductChange.Entity.Identifier",
                        "Name": f"{product_title} - Default Offer",
                    },
                },
            ]

            response = self.catalog_client.start_change_set(
                Catalog="AWSMarketplace", ChangeSet=change_set
            )

            return {
                "success": True,
                "change_set_id": response["ChangeSetId"],
                "message": f"Product '{product_title}' created. Polling for product_id...",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create product",
            }

    def create_listing_draft(
        self,
        product_title: str,
        short_description: str = None,
        long_description: str = None,
        logo_url: str = None,
        categories: List[str] = None,
        search_keywords: List[str] = None,
        highlights: List[str] = None,
        video_urls: List[str] = None,
        additional_resources: List[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new SaaS product listing draft with offer

        Uses the correct AWS Marketplace pattern:
        1. CreateProduct (minimal info)
        2. UpdateInformation (full product details including highlights)
        3. CreateOffer (linked to product)

        Args:
            product_title: Product name (required)
            short_description: Brief product description
            long_description: Detailed product description
            logo_url: URL to product logo (S3 URL to PNG/JPG)
            categories: Product categories (1-3 items)
            search_keywords: Keywords for search (1-10 items)
            highlights: Product highlights (array of strings, 5-250 chars each)
            video_urls: Optional video URLs
            additional_resources: Optional additional resources

        Returns:
            Dict with product_id, offer_id, change_set_id and status
        """
        try:
            # Build change set with proper chaining
            change_set = [
                # Step 1: Create Product with minimal info
                {
                    "ChangeType": "CreateProduct",
                    "ChangeName": "CreateProductChange",
                    "Entity": {"Type": "SaaSProduct@1.0"},
                    "DetailsDocument": {"ProductTitle": product_title},
                }
            ]

            # Step 2: Update product information if additional details provided
            if any(
                [
                    short_description,
                    long_description,
                    logo_url,
                    categories,
                    search_keywords,
                    highlights,
                    video_urls,
                    additional_resources,
                ]
            ):
                update_details = {}
                if short_description:
                    update_details["ShortDescription"] = short_description
                if long_description:
                    update_details["LongDescription"] = long_description
                if logo_url:
                    update_details["LogoUrl"] = logo_url
                if categories:
                    update_details["Categories"] = categories
                if search_keywords:
                    update_details["SearchKeywords"] = search_keywords
                # FIXED: Highlights is an array of strings in UpdateInformation
                if highlights:
                    update_details["Highlights"] = highlights
                if video_urls:
                    update_details["VideoUrls"] = video_urls
                if additional_resources:
                    update_details["AdditionalResources"] = additional_resources
                else:
                    # AWS requires this field even if empty
                    update_details["AdditionalResources"] = []

                change_set.append(
                    {
                        "ChangeType": "UpdateInformation",
                        "ChangeName": "UpdateProductInfoChange",
                        "Entity": {
                            "Type": "SaaSProduct@1.0",
                            "Identifier": "$CreateProductChange.Entity.Identifier",
                        },
                        "DetailsDocument": update_details,
                    }
                )

            # Step 3: Create Offer linked to the product
            change_set.append(
                {
                    "ChangeType": "CreateOffer",
                    "ChangeName": "CreateOfferChange",
                    "Entity": {"Type": "Offer@1.0"},
                    "DetailsDocument": {
                        "ProductId": "$CreateProductChange.Entity.Identifier",
                        "Name": f"{product_title} - Default Offer",
                    },
                }
            )

            response = self.catalog_client.start_change_set(
                Catalog="AWSMarketplace", ChangeSet=change_set
            )

            return {
                "success": True,
                "change_set_id": response["ChangeSetId"],
                "message": "Product and offer draft created successfully. Use get_listing_status to retrieve product_id and offer_id once processing completes.",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create listing draft",
            }

    def update_product_information(
        self, product_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing product's information

        Args:
            product_id: The product entity ID
            updates: Dictionary of fields to update (e.g., ProductTitle, ShortDescription, etc.)

        Returns:
            Dict with update status
        """
        try:
            # Strip revision suffix from product_id
            clean_product_id = self._strip_revision_suffix(product_id)
            
            # Get current entity details
            entity_details = self.get_entity_details("SaaSProduct@1.0", clean_product_id)
            if not entity_details.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to get product details: {entity_details.get('error')}",
                    "message": "Could not fetch current product revision",
                }

            change_set = [
                {
                    "ChangeType": "UpdateInformation",
                    "Entity": {
                        "Type": entity_details["entity_type"],
                        "Identifier": clean_product_id,
                    },
                    "DetailsDocument": updates,
                }
            ]

            response = self.catalog_client.start_change_set(
                Catalog="AWSMarketplace", ChangeSet=change_set
            )

            return {
                "success": True,
                "change_set_id": response["ChangeSetId"],
                "message": "Product information updated successfully",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to update product information",
            }

    def create_offer(self, product_id: str, offer_name: str) -> Dict[str, Any]:
        """
        Create a new offer for an existing product

        Args:
            product_id: The product entity ID
            offer_name: Name for the offer

        Returns:
            Dict with offer creation status
        """
        try:
            # Strip revision suffix from product_id
            clean_product_id = self._strip_revision_suffix(product_id)
            
            change_set = [
                {
                    "ChangeType": "CreateOffer",
                    "Entity": {"Type": "Offer@1.0"},
                    "DetailsDocument": {"ProductId": clean_product_id, "Name": offer_name},
                }
            ]

            response = self.catalog_client.start_change_set(
                Catalog="AWSMarketplace", ChangeSet=change_set
            )

            return {
                "success": True,
                "change_set_id": response["ChangeSetId"],
                "message": "Offer created successfully",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create offer",
            }

    def update_offer_information(
        self, offer_id: str, name: str, description: str
    ) -> Dict[str, Any]:
        """
        Update offer name and description. REQUIRED before releasing to Limited stage.

        Args:
            offer_id: The offer entity ID
            name: Name for the offer
            description: Description text for the offer

        Returns:
            Dict with update status
        """
        try:
            # Strip revision suffix from offer_id
            clean_offer_id = self._strip_revision_suffix(offer_id)
            
            change_set = [
                {
                    "ChangeType": "UpdateInformation",
                    "Entity": {"Type": "Offer@1.0", "Identifier": clean_offer_id},
                    "DetailsDocument": {"Name": name, "Description": description},
                }
            ]

            response = self.catalog_client.start_change_set(
                Catalog="AWSMarketplace", ChangeSet=change_set
            )

            return {
                "success": True,
                "change_set_id": response["ChangeSetId"],
                "message": "Offer information updated successfully",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to update offer information",
            }
    
    def update_product_targeting(
        self, product_id: str, buyer_accounts: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Update product targeting with buyer account allowlist for Limited testing.
        Optional - if not set, only your account can access the product.

        Args:
            product_id: The product entity ID
            buyer_accounts: List of AWS account IDs to allowlist (optional)

        Returns:
            Dict with update status
        """
        try:
            # Strip revision suffix from product_id
            clean_product_id = self._strip_revision_suffix(product_id)
            
            details_document = {}
            
            if buyer_accounts:
                details_document = {
                    "PositiveTargeting": {"BuyerAccounts": buyer_accounts}
                }
            
            change_set = [
                {
                    "ChangeType": "UpdateTargeting",
                    "Entity": {"Type": "SaaSProduct@1.0", "Identifier": clean_product_id},
                    "DetailsDocument": details_document,
                }
            ]

            response = self.catalog_client.start_change_set(
                Catalog="AWSMarketplace", ChangeSet=change_set
            )

            return {
                "success": True,
                "change_set_id": response["ChangeSetId"],
                "message": f"Product targeting updated with {len(buyer_accounts) if buyer_accounts else 0} buyer accounts",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to update product targeting",
            }

    def add_pricing(
        self,
        offer_id: str,
        pricing_model: str,
        dimensions: Optional[List[Dict[str, Any]]] = None,
        contract_durations: Optional[List[str]] = None,
        multiple_dimension_selection: str = "Allowed",
        quantity_configuration: str = "Allowed",
    ) -> Dict[str, Any]:
        """
        Add pricing information to an offer (not product!)

        Pricing is configured on Offers, not Products in AWS Marketplace.

        Args:
            offer_id: The OFFER entity ID (not product ID)
            pricing_model: "Usage", "Contract", or "Free"
            dimensions: Pricing dimensions for usage-based pricing
                       Format: [{"Key": "dimension_name", "Description": "...", "Types": ["Metered"]}]

        Returns:
            Dict with update status
        """
        try:
            # Build pricing terms based on model
            terms = []

            if pricing_model == "Free":
                # Free pricing - no additional terms needed
                pricing_details = {"PricingModel": "Free"}
            elif pricing_model == "Usage":
                # Usage-based pricing with dimensions
                if not dimensions:
                    return {
                        "success": False,
                        "error": "Dimensions required for Usage pricing model",
                        "message": "Please provide pricing dimensions",
                    }

                # Build rate card from dimensions
                rate_card = []
                for dim in dimensions:
                    rate_card.append(
                        {"DimensionKey": dim.get("Key"), "Price": dim.get("Price", 0.0)}
                    )

                terms.append(
                    {
                        "Type": "UsageBasedPricingTerm",
                        "CurrencyCode": "USD",
                        "RateCards": [{"RateCard": rate_card}],
                    }
                )

                pricing_details = {"PricingModel": "Usage", "Terms": terms}
            elif pricing_model == "Contract":
                # Contract pricing - create contract terms with dimensions
                if not dimensions:
                    return {
                        "success": False,
                        "error": "Contract details required for Contract pricing model",
                        "message": "Please provide contract pricing details",
                    }

                # Build rate card from dimensions for contract pricing
                rate_card = []
                for dim in dimensions:
                    rate_card.append(
                        {
                            "DimensionKey": dim.get("Key"),
                            "Price": "0.001",  # Default test price
                        }
                    )

                # Map duration strings to ISO 8601 duration format
                duration_map = {
                    "1 Month": "P1M",
                    "3 Months": "P3M",
                    "6 Months": "P6M",
                    "12 Months": "P12M",
                    "24 Months": "P24M",
                    "36 Months": "P36M",
                }

                # Default to 12 months if not specified
                if not contract_durations:
                    contract_durations = ["12 Months"]

                # Create rate cards for each duration
                rate_cards = []
                for duration_str in contract_durations:
                    iso_duration = duration_map.get(duration_str, "P12M")
                    rate_cards.append(
                        {
                            "Selector": {"Type": "Duration", "Value": iso_duration},
                            "Constraints": {
                                "MultipleDimensionSelection": multiple_dimension_selection,
                                "QuantityConfiguration": quantity_configuration,
                            },
                            "RateCard": rate_card,
                        }
                    )

                # Create contract term with all durations
                terms.append(
                    {
                        "Type": "ConfigurableUpfrontPricingTerm",
                        "CurrencyCode": "USD",
                        "RateCards": rate_cards,
                    }
                )

                pricing_details = {"PricingModel": "Contract", "Terms": terms}
            else:
                return {
                    "success": False,
                    "error": f"Invalid pricing model: {pricing_model}",
                    "message": "Pricing model must be 'Usage', 'Contract', or 'Free'",
                }

            # Strip revision suffix from offer_id
            clean_offer_id = self._strip_revision_suffix(offer_id)
            
            # Get current entity details
            entity_details = self.get_entity_details("Offer@1.0", clean_offer_id)
            if not entity_details.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to get offer details: {entity_details.get('error')}",
                    "message": "Could not fetch current offer revision",
                }

            change_set = [
                {
                    "ChangeType": "UpdatePricingTerms",
                    "Entity": {
                        "Type": entity_details["entity_type"],
                        "Identifier": clean_offer_id,
                    },
                    "DetailsDocument": pricing_details,
                }
            ]

            response = self.catalog_client.start_change_set(
                Catalog="AWSMarketplace", ChangeSet=change_set
            )

            return {
                "success": True,
                "change_set_id": response["ChangeSetId"],
                "message": f"{pricing_model} pricing added to offer successfully",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to add pricing",
            }

    def update_support_terms(self, offer_id: str, refund_policy: str) -> Dict[str, Any]:
        """
        Update support terms on an offer (includes refund policy)

        IMPORTANT: Support information goes on the Offer, not the Product!

        Args:
            offer_id: The OFFER entity ID (not product ID)
            refund_policy: Refund policy text (50-5000 characters)

        Returns:
            Dict with update status
        """
        try:
            # Strip revision suffix from offer_id
            clean_offer_id = self._strip_revision_suffix(offer_id)
            
            # Get current entity details
            entity_details = self.get_entity_details("Offer@1.0", clean_offer_id)
            if not entity_details.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to get offer details: {entity_details.get('error')}",
                    "message": "Could not fetch current offer revision",
                }

            change_set = [
                {
                    "ChangeType": "UpdateSupportTerms",
                    "Entity": {
                        "Type": entity_details["entity_type"],
                        "Identifier": clean_offer_id,
                    },
                    "DetailsDocument": {
                        "Terms": [
                            {"Type": "SupportTerm", "RefundPolicy": refund_policy}
                        ]
                    },
                }
            ]

            response = self.catalog_client.start_change_set(
                Catalog="AWSMarketplace", ChangeSet=change_set
            )

            return {
                "success": True,
                "change_set_id": response["ChangeSetId"],
                "message": "Support terms updated successfully",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to update support terms",
            }

    def update_legal_terms(
        self, offer_id: str, eula_type: str = "StandardEula", eula_url: str = None
    ) -> Dict[str, Any]:
        """
        Update legal terms (EULA) on an offer

        Args:
            offer_id: The OFFER entity ID (not product ID)
            eula_type: "StandardEula" or "CustomEula"
            eula_url: S3 URL to custom EULA PDF (required if eula_type is "CustomEula")

        Returns:
            Dict with update status
        """
        try:
            if eula_type == "StandardEula":
                documents = [{"Type": "StandardEula", "Version": "2022-07-14"}]
            elif eula_type == "CustomEula":
                if not eula_url:
                    return {
                        "success": False,
                        "error": "eula_url required for CustomEula",
                        "message": "Please provide a custom EULA URL",
                    }
                documents = [{"Type": "CustomEula", "Url": eula_url}]
            else:
                return {
                    "success": False,
                    "error": f"Invalid EULA type: {eula_type}",
                    "message": "EULA type must be 'StandardEula' or 'CustomEula'",
                }

            # Strip revision suffix from offer_id
            clean_offer_id = self._strip_revision_suffix(offer_id)
            
            # Get current entity details
            entity_details = self.get_entity_details("Offer@1.0", clean_offer_id)
            if not entity_details.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to get offer details: {entity_details.get('error')}",
                    "message": "Could not fetch current offer revision",
                }

            change_set = [
                {
                    "ChangeType": "UpdateLegalTerms",
                    "Entity": {
                        "Type": entity_details["entity_type"],
                        "Identifier": clean_offer_id,
                    },
                    "DetailsDocument": {
                        "Terms": [{"Type": "LegalTerm", "Documents": documents}]
                    },
                }
            ]

            response = self.catalog_client.start_change_set(
                Catalog="AWSMarketplace", ChangeSet=change_set
            )

            return {
                "success": True,
                "change_set_id": response["ChangeSetId"],
                "message": "Legal terms updated successfully",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to update legal terms",
            }
    
    def update_renewal_terms(self, offer_id: str) -> Dict[str, Any]:
        """
        Update renewal terms on an offer. REQUIRED for Contract pricing before release.
        
        Args:
            offer_id: The OFFER entity ID
            
        Returns:
            Dict with update status
        """
        try:
            # Strip revision suffix from offer_id
            clean_offer_id = self._strip_revision_suffix(offer_id)
            
            # Get current entity details
            entity_details = self.get_entity_details("Offer@1.0", clean_offer_id)
            if not entity_details.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to get offer details: {entity_details.get('error')}",
                    "message": "Could not fetch current offer revision",
                }

            change_set = [
                {
                    "ChangeType": "UpdateRenewalTerms",
                    "Entity": {
                        "Type": entity_details["entity_type"],
                        "Identifier": clean_offer_id,
                    },
                    "DetailsDocument": {
                        "Terms": [{"Type": "RenewalTerm"}]
                    },
                }
            ]

            response = self.catalog_client.start_change_set(
                Catalog="AWSMarketplace", ChangeSet=change_set
            )

            return {
                "success": True,
                "change_set_id": response["ChangeSetId"],
                "message": "Renewal terms updated successfully",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to update renewal terms",
            }

    def update_offer_availability(
        self,
        offer_id: str,
        availability_type: str = "all",
        country_codes: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Update offer availability (geographic restrictions)

        Args:
            offer_id: The OFFER entity ID
            availability_type: "all", "exclude", or "include"
            country_codes: List of ISO 3166-1 alpha-2 country codes

        Returns:
            Dict with update status
        """
        try:
            if availability_type == "all":
                availability_details = {
                    "AvailabilityEndDate": None  # Available indefinitely
                }
            elif availability_type == "exclude":
                if not country_codes:
                    return {
                        "success": False,
                        "error": "country_codes required for exclude availability",
                        "message": "Please provide country codes to exclude",
                    }
                availability_details = {
                    "AvailabilityEndDate": None,
                    "CountryRestrictions": {
                        "Type": "Exclude",
                        "CountryCodes": country_codes,
                    },
                }
            elif availability_type == "include":
                if not country_codes:
                    return {
                        "success": False,
                        "error": "country_codes required for include availability",
                        "message": "Please provide country codes to include",
                    }
                availability_details = {
                    "AvailabilityEndDate": None,
                    "CountryRestrictions": {
                        "Type": "Include",
                        "CountryCodes": country_codes,
                    },
                }
            else:
                return {
                    "success": False,
                    "error": f"Invalid availability type: {availability_type}",
                    "message": "Availability type must be 'all', 'exclude', or 'include'",
                }

            # Strip revision suffix from offer_id
            clean_offer_id = self._strip_revision_suffix(offer_id)
            
            # Get current entity details
            entity_details = self.get_entity_details("Offer@1.0", clean_offer_id)
            if not entity_details.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to get offer details: {entity_details.get('error')}",
                    "message": "Could not fetch current offer revision",
                }

            change_set = [
                {
                    "ChangeType": "UpdateAvailability",
                    "Entity": {
                        "Type": entity_details["entity_type"],
                        "Identifier": clean_offer_id,
                    },
                    "DetailsDocument": availability_details,
                }
            ]

            response = self.catalog_client.start_change_set(
                Catalog="AWSMarketplace", ChangeSet=change_set
            )

            return {
                "success": True,
                "change_set_id": response["ChangeSetId"],
                "message": "Offer availability updated successfully",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to update offer availability",
            }

    def update_offer_targeting(
        self, offer_id: str, buyer_accounts: List[str] = None
    ) -> Dict[str, Any]:
        """
        Update offer targeting (allowlist specific AWS accounts)

        Args:
            offer_id: The OFFER entity ID
            buyer_accounts: List of 12-digit AWS account IDs

        Returns:
            Dict with update status
        """
        try:
            # Strip revision suffix from offer_id
            clean_offer_id = self._strip_revision_suffix(offer_id)
            
            if not buyer_accounts:
                # Remove targeting (make public)
                targeting_details = {}
            else:
                targeting_details = {
                    "PositiveTargeting": {"BuyerAccounts": buyer_accounts}
                }

            # Get current entity details
            entity_details = self.get_entity_details("Offer@1.0", clean_offer_id)
            if not entity_details.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to get offer details: {entity_details.get('error')}",
                    "message": "Could not fetch current offer revision",
                }

            change_set = [
                {
                    "ChangeType": "UpdateTargeting",
                    "Entity": {
                        "Type": entity_details["entity_type"],
                        "Identifier": clean_offer_id,
                    },
                    "DetailsDocument": targeting_details,
                }
            ]

            response = self.catalog_client.start_change_set(
                Catalog="AWSMarketplace", ChangeSet=change_set
            )

            return {
                "success": True,
                "change_set_id": response["ChangeSetId"],
                "message": "Offer targeting updated successfully",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to update offer targeting",
            }

    def add_dimensions(
        self, product_id: str, dimensions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Add pricing dimensions to a SaaS product

        Dimensions must be added to the Product before they can be used in Offer pricing.

        Args:
            product_id: The product entity ID
            dimensions: List of dimension definitions
                Format: [{
                    "Key": "api_id",
                    "Name": "Display Name",
                    "Description": "Description",
                    "Types": ["Entitled" or "Metered"],
                    "Unit": "Units" (optional)
                }]

        Returns:
            Dict with update status
        """
        try:
            # Strip revision suffix from product_id
            clean_product_id = self._strip_revision_suffix(product_id)
            
            # Get current entity details
            entity_details = self.get_entity_details("SaaSProduct@1.0", clean_product_id)
            if not entity_details.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to get product details: {entity_details.get('error')}",
                    "message": "Could not fetch current product revision",
                }

            change_set = [
                {
                    "ChangeType": "AddDimensions",
                    "Entity": {
                        "Type": entity_details["entity_type"],
                        "Identifier": clean_product_id,
                    },
                    "DetailsDocument": dimensions,
                }
            ]

            response = self.catalog_client.start_change_set(
                Catalog="AWSMarketplace", ChangeSet=change_set
            )

            return {
                "success": True,
                "change_set_id": response["ChangeSetId"],
                "message": f"Added {len(dimensions)} dimension(s) successfully",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to add dimensions",
            }

    def add_delivery_options(
        self,
        product_id: str,
        fulfillment_url: str,
        quick_launch_enabled: bool = False,
        launch_url: str = None,
    ) -> Dict[str, Any]:
        """
        Add delivery options (fulfillment URL) to a SaaS product

        Args:
            product_id: The product entity ID
            fulfillment_url: URL to seller's account registration/login page (HTTPS required)
            quick_launch_enabled: Enable Quick Launch feature
            launch_url: URL for Quick Launch (required if quick_launch_enabled=True)

        Returns:
            Dict with update status
        """
        try:
            # Strip revision suffix from product_id
            clean_product_id = self._strip_revision_suffix(product_id)
            
            # Get current entity details to get the latest revision
            entity_details = self.get_entity_details("SaaSProduct@1.0", clean_product_id)
            if not entity_details.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to get product details: {entity_details.get('error')}",
                    "message": "Could not fetch current product revision",
                }

            delivery_details = {
                "DeliveryOptions": [
                    {
                        "Details": {
                            "SaaSUrlDeliveryOptionDetails": {
                                "FulfillmentUrl": fulfillment_url,
                                "QuickLaunchEnabled": quick_launch_enabled,
                            }
                        }
                    }
                ]
            }

            if quick_launch_enabled:
                if not launch_url:
                    return {
                        "success": False,
                        "error": "launch_url required when quick_launch_enabled is True",
                        "message": "Please provide a launch URL",
                    }
                delivery_details["DeliveryOptions"][0]["Details"][
                    "SaaSUrlDeliveryOptionDetails"
                ]["LaunchUrl"] = launch_url

            change_set = [
                {
                    "ChangeType": "AddDeliveryOptions",
                    "Entity": {
                        "Type": entity_details["entity_type"],
                        "Identifier": clean_product_id,
                    },
                    "DetailsDocument": delivery_details,
                }
            ]

            response = self.catalog_client.start_change_set(
                Catalog="AWSMarketplace", ChangeSet=change_set
            )

            return {
                "success": True,
                "change_set_id": response["ChangeSetId"],
                "message": "Delivery options added successfully",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to add delivery options",
            }

    def validate_listing(self, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate listing data against AWS Marketplace requirements

        Args:
            listing_data: Complete listing information

        Returns:
            Dict with validation results
        """
        errors = []
        warnings = []

        # Validate required fields
        required_fields = ["ProductTitle", "ShortDescription", "LongDescription"]

        for field in required_fields:
            if field not in listing_data or not listing_data[field]:
                errors.append(f"Missing required field: {field}")

        # Validate field lengths
        if "ProductTitle" in listing_data:
            title_len = len(listing_data["ProductTitle"])
            if title_len < 5 or title_len > 255:
                errors.append("ProductTitle must be between 5 and 255 characters")

        if "ShortDescription" in listing_data:
            desc_len = len(listing_data["ShortDescription"])
            if desc_len < 10 or desc_len > 500:
                errors.append("ShortDescription must be between 10 and 500 characters")

        if "LongDescription" in listing_data:
            desc_len = len(listing_data["LongDescription"])
            if desc_len < 50:
                warnings.append("LongDescription should be at least 50 characters")

        if "Categories" in listing_data:
            cat_count = len(listing_data["Categories"])
            if cat_count < 1 or cat_count > 3:
                errors.append("Must have between 1 and 3 categories")

        # Check for delivery options
        if "FulfillmentUrl" not in listing_data:
            warnings.append("No fulfillment URL specified - required for publishing")

        # Check for offer
        if "OfferId" not in listing_data:
            warnings.append("No offer created - required for publishing")

        # Check for pricing
        if "PricingModel" not in listing_data:
            warnings.append("No pricing model specified - required for publishing")

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def get_listing_status(self, change_set_id: str) -> Dict[str, Any]:
        """
        Get the status of a change set

        Args:
            change_set_id: The change set ID

        Returns:
            Dict with status information
        """
        try:
            response = self.catalog_client.describe_change_set(
                Catalog="AWSMarketplace", ChangeSetId=change_set_id
            )

            return {
                "success": True,
                "status": response["Status"],
                "change_set": response.get("ChangeSet", []),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def release_offer_to_limited(self, offer_id: str) -> Dict[str, Any]:
        """
        Release an offer to Limited stage (visible to allowlisted accounts)

        Args:
            offer_id: The offer entity ID

        Returns:
            Dict with success status and change_set_id
        """
        try:
            # Strip revision suffix from offer_id
            clean_offer_id = self._strip_revision_suffix(offer_id)
            
            change_set = [
                {
                    "ChangeType": "ReleaseOffer",
                    "Entity": {"Type": "Offer@1.0", "Identifier": clean_offer_id},
                    "Details": "{}",
                }
            ]

            response = self.catalog_client.start_change_set(
                Catalog="AWSMarketplace",
                ChangeSet=change_set,
                ChangeSetName=f"Release offer {clean_offer_id} to Limited",
            )

            return {
                "success": True,
                "change_set_id": response["ChangeSetId"],
                "message": f"Offer release initiated to Limited stage",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to release offer: {str(e)}",
            }

    def add_dimensions_and_pricing_for_usage(
        self, product_id: str, offer_id: str, dimensions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Add dimensions to product AND pricing to offer in a single changeset for Usage pricing.
        AWS Marketplace requires both operations together for Usage-based SaaS products.

        Args:
            product_id: The product entity ID
            offer_id: The offer entity ID
            dimensions: List of dimension definitions with Types: ["Metered", "ExternallyMetered"]

        Returns:
            Dict with update status
        """
        try:
            # Strip revision suffixes
            clean_product_id = self._strip_revision_suffix(product_id)
            clean_offer_id = self._strip_revision_suffix(offer_id)
            
            # Get current entity details
            product_details = self.get_entity_details("SaaSProduct@1.0", clean_product_id)
            if not product_details.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to get product details: {product_details.get('error')}",
                    "message": "Could not fetch current product revision",
                }

            offer_details = self.get_entity_details("Offer@1.0", clean_offer_id)
            if not offer_details.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to get offer details: {offer_details.get('error')}",
                    "message": "Could not fetch current offer revision",
                }

            # Build rate card from dimensions
            rate_card = []
            for dim in dimensions:
                rate_card.append(
                    {
                        "DimensionKey": dim.get("Key"),
                        "Price": "0.001",  # Default test price
                    }
                )

            # Create a combined changeset with both operations
            change_set = [
                # First: Add dimensions to product
                {
                    "ChangeType": "AddDimensions",
                    "Entity": {
                        "Type": product_details["entity_type"],
                        "Identifier": clean_product_id,
                    },
                    "DetailsDocument": dimensions,
                },
                # Second: Add pricing to offer
                {
                    "ChangeType": "UpdatePricingTerms",
                    "Entity": {
                        "Type": offer_details["entity_type"],
                        "Identifier": clean_offer_id,
                    },
                    "DetailsDocument": {
                        "PricingModel": "Usage",
                        "Terms": [
                            {
                                "Type": "UsageBasedPricingTerm",
                                "CurrencyCode": "USD",
                                "RateCards": [{"RateCard": rate_card}],
                            }
                        ],
                    },
                },
            ]

            response = self.catalog_client.start_change_set(
                Catalog="AWSMarketplace",
                ChangeSet=change_set,
                ChangeSetName=f"Add dimensions and pricing for Usage model",
            )

            return {
                "success": True,
                "change_set_id": response["ChangeSetId"],
                "message": f"Added {len(dimensions)} dimension(s) and pricing successfully",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to add dimensions and pricing",
            }

    def add_dimensions_and_pricing_for_hybrid(
        self,
        product_id: str,
        offer_id: str,
        dimensions: List[Dict[str, Any]],
        contract_durations: List[str],
        multiple_dimension_selection: str = "Allowed",
        quantity_configuration: str = "Allowed",
    ) -> Dict[str, Any]:
        """
        Add dimensions and pricing for Contract with Consumption (hybrid) pricing.
        Requires both Entitled and Metered dimensions with both pricing term types.

        Args:
            product_id: The product entity ID
            offer_id: The offer entity ID
            dimensions: List with both Entitled and Metered dimensions
            contract_durations: List of contract durations (e.g., ["12 Months"])
            multiple_dimension_selection: "Allowed" or "Disallowed"
            quantity_configuration: "Allowed" or "Disallowed"

        Returns:
            Dict with update status
        """
        try:
            # Strip revision suffixes
            clean_product_id = self._strip_revision_suffix(product_id)
            clean_offer_id = self._strip_revision_suffix(offer_id)
            
            # Get current entity details
            product_details = self.get_entity_details("SaaSProduct@1.0", clean_product_id)
            if not product_details.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to get product details: {product_details.get('error')}",
                    "message": "Could not fetch current product revision",
                }

            offer_details = self.get_entity_details("Offer@1.0", clean_offer_id)
            if not offer_details.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to get offer details: {offer_details.get('error')}",
                    "message": "Could not fetch current offer revision",
                }

            # Separate Entitled and Metered dimensions
            entitled_dims = [d for d in dimensions if "Entitled" in d.get("Types", [])]
            metered_dims = [d for d in dimensions if "Metered" in d.get("Types", [])]

            if not entitled_dims or not metered_dims:
                return {
                    "success": False,
                    "error": "Hybrid pricing requires both Entitled and Metered dimensions",
                    "message": "Please provide at least one Entitled and one Metered dimension",
                }

            # Build rate cards for contract pricing (Entitled dimensions)
            contract_rate_card = []
            for dim in entitled_dims:
                contract_rate_card.append(
                    {
                        "DimensionKey": dim.get("Key"),
                        "Price": "0.001",  # Default test price
                    }
                )

            # Build rate card for usage pricing (Metered dimensions)
            usage_rate_card = []
            for dim in metered_dims:
                usage_rate_card.append(
                    {
                        "DimensionKey": dim.get("Key"),
                        "Price": "0.001",  # Default test price
                    }
                )

            # Map duration strings to ISO 8601
            duration_map = {
                "1 Month": "P1M",
                "3 Months": "P3M",
                "6 Months": "P6M",
                "12 Months": "P12M",
                "24 Months": "P24M",
                "36 Months": "P36M",
            }

            # Create rate cards for each contract duration
            contract_rate_cards = []
            for duration_str in contract_durations:
                iso_duration = duration_map.get(duration_str, "P12M")
                contract_rate_cards.append(
                    {
                        "Selector": {"Type": "Duration", "Value": iso_duration},
                        "Constraints": {
                            "MultipleDimensionSelection": multiple_dimension_selection,
                            "QuantityConfiguration": quantity_configuration,
                        },
                        "RateCard": contract_rate_card,
                    }
                )

            # Create combined changeset
            change_set = [
                # First: Add ALL dimensions to product
                {
                    "ChangeType": "AddDimensions",
                    "Entity": {
                        "Type": product_details["entity_type"],
                        "Identifier": clean_product_id,
                    },
                    "DetailsDocument": dimensions,
                },
                # Second: Add BOTH pricing terms to offer
                {
                    "ChangeType": "UpdatePricingTerms",
                    "Entity": {
                        "Type": offer_details["entity_type"],
                        "Identifier": clean_offer_id,
                    },
                    "DetailsDocument": {
                        "PricingModel": "Contract",
                        "Terms": [
                            # Contract term for Entitled dimensions
                            {
                                "Type": "ConfigurableUpfrontPricingTerm",
                                "CurrencyCode": "USD",
                                "RateCards": contract_rate_cards,
                            },
                            # Usage term for Metered dimensions
                            {
                                "Type": "UsageBasedPricingTerm",
                                "CurrencyCode": "USD",
                                "RateCards": [{"RateCard": usage_rate_card}],
                            },
                        ],
                    },
                },
            ]

            response = self.catalog_client.start_change_set(
                Catalog="AWSMarketplace",
                ChangeSet=change_set,
                ChangeSetName="Add dimensions and pricing for hybrid model",
            )

            return {
                "success": True,
                "change_set_id": response["ChangeSetId"],
                "message": f"Added {len(dimensions)} dimension(s) and hybrid pricing successfully",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to add hybrid pricing: {str(e)}",
            }

    def add_dimensions_and_pricing_for_contract(
        self,
        product_id: str,
        offer_id: str,
        dimensions: List[Dict[str, Any]],
        contract_durations: List[str],
        multiple_dimension_selection: str = "Allowed",
        quantity_configuration: str = "Allowed",
    ) -> Dict[str, Any]:
        """
        Add dimensions to product AND pricing to offer in a single changeset for Contract pricing.
        AWS Marketplace requires dimensions to exist before pricing can be configured.

        Args:
            product_id: The product entity ID
            offer_id: The offer entity ID
            dimensions: List of dimension definitions with Types: ["Entitled"]
            contract_durations: List of contract durations (e.g., ["12 Months"])
            multiple_dimension_selection: "Allowed" or "Disallowed"
            quantity_configuration: "Allowed" or "Disallowed"

        Returns:
            Dict with update status
        """
        try:
            # Strip revision suffixes
            clean_product_id = self._strip_revision_suffix(product_id)
            clean_offer_id = self._strip_revision_suffix(offer_id)
            
            # Get current entity details
            product_details = self.get_entity_details("SaaSProduct@1.0", clean_product_id)
            if not product_details.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to get product details: {product_details.get('error')}",
                    "message": "Could not fetch current product revision",
                }

            offer_details = self.get_entity_details("Offer@1.0", clean_offer_id)
            if not offer_details.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to get offer details: {offer_details.get('error')}",
                    "message": "Could not fetch current offer revision",
                }

            # Build rate card from dimensions
            rate_card = []
            for dim in dimensions:
                rate_card.append(
                    {
                        "DimensionKey": dim.get("Key"),
                        "Price": "0.001",  # Default test price
                    }
                )

            # Map duration strings to ISO 8601 duration format
            duration_map = {
                "1 Month": "P1M",
                "3 Months": "P3M",
                "6 Months": "P6M",
                "12 Months": "P12M",
                "24 Months": "P24M",
                "36 Months": "P36M",
            }

            # Create rate cards for each duration
            rate_cards = []
            for duration_str in contract_durations:
                iso_duration = duration_map.get(duration_str, "P12M")
                rate_cards.append(
                    {
                        "Selector": {"Type": "Duration", "Value": iso_duration},
                        "Constraints": {
                            "MultipleDimensionSelection": multiple_dimension_selection,
                            "QuantityConfiguration": quantity_configuration,
                        },
                        "RateCard": rate_card,
                    }
                )

            # Create a combined changeset with both operations
            change_set = [
                # First: Add dimensions to product
                {
                    "ChangeType": "AddDimensions",
                    "Entity": {
                        "Type": product_details["entity_type"],
                        "Identifier": clean_product_id,
                    },
                    "DetailsDocument": dimensions,
                },
                # Second: Add pricing to offer
                {
                    "ChangeType": "UpdatePricingTerms",
                    "Entity": {
                        "Type": offer_details["entity_type"],
                        "Identifier": clean_offer_id,
                    },
                    "DetailsDocument": {
                        "PricingModel": "Contract",
                        "Terms": [
                            {
                                "Type": "ConfigurableUpfrontPricingTerm",
                                "CurrencyCode": "USD",
                                "RateCards": rate_cards,
                            }
                        ],
                    },
                },
            ]

            response = self.catalog_client.start_change_set(
                Catalog="AWSMarketplace",
                ChangeSet=change_set,
                ChangeSetName="Add dimensions and pricing for Contract model",
            )

            return {
                "success": True,
                "change_set_id": response["ChangeSetId"],
                "message": f"Added {len(dimensions)} dimension(s) and contract pricing successfully",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to add dimensions and pricing",
            }

    def release_product_and_offer_to_limited(
        self,
        product_id: str,
        offer_id: str,
        offer_name: str,
        offer_description: str,
        pricing_model: str = "Usage",
        buyer_accounts: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Release both product and offer to Limited stage.
        AWS Marketplace requires offer name and description before release.
        For Contract pricing, also requires renewal terms.

        Args:
            product_id: The product entity ID
            offer_id: The offer entity ID
            offer_name: Name for the offer (required)
            offer_description: Description for the offer (required)
            pricing_model: Pricing model ("Usage" or "Contract")
            buyer_accounts: Optional list of AWS account IDs to allowlist

        Returns:
            Dict with success status and change_set_id
        """
        try:
            import time
            
            # Step 1: Update offer information (name and description - REQUIRED)
            info_result = self.update_offer_information(offer_id, offer_name, offer_description)
            if not info_result.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to set offer information: {info_result.get('error')}",
                    "message": "Offer name and description are required before release",
                }
            
            # Wait for offer info changeset to complete
            info_changeset_id = info_result.get("change_set_id")
            if info_changeset_id:
                max_wait = 60  # 60 attempts * 5s = 300 seconds
                for attempt in range(max_wait):
                    time.sleep(5)
                    status_result = self.get_listing_status(info_changeset_id)
                    status = status_result.get("status", "UNKNOWN")
                    
                    if status == "SUCCEEDED":
                        break
                    elif status == "FAILED":
                        return {
                            "success": False,
                            "error": f"Offer information update failed: {status_result.get('error')}",
                            "message": "Could not update offer information",
                        }
                    elif attempt == max_wait - 1:
                        return {
                            "success": False,
                            "error": "Timeout waiting for offer information update",
                            "message": "Offer information update is taking too long",
                        }
            
            # Step 2: Update renewal terms for Contract pricing (REQUIRED for Contract)
            if pricing_model == "Contract":
                renewal_result = self.update_renewal_terms(offer_id)
                if not renewal_result.get("success"):
                    return {
                        "success": False,
                        "error": f"Failed to set renewal terms: {renewal_result.get('error')}",
                        "message": "Renewal terms are required for Contract pricing",
                    }
                
                # Wait for renewal terms changeset to complete
                renewal_changeset_id = renewal_result.get("change_set_id")
                if renewal_changeset_id:
                    for attempt in range(max_wait):
                        time.sleep(5)
                        status_result = self.get_listing_status(renewal_changeset_id)
                        status = status_result.get("status", "UNKNOWN")
                        
                        if status == "SUCCEEDED":
                            break
                        elif status == "FAILED":
                            return {
                                "success": False,
                                "error": f"Renewal terms update failed: {status_result.get('error')}",
                                "message": "Could not update renewal terms",
                            }
                        elif attempt == max_wait - 1:
                            return {
                                "success": False,
                                "error": "Timeout waiting for renewal terms update",
                                "message": "Renewal terms update is taking too long",
                            }
            
            # Step 3: Update product targeting if buyer accounts provided (OPTIONAL)
            if buyer_accounts:
                targeting_result = self.update_product_targeting(product_id, buyer_accounts)
                if not targeting_result.get("success"):
                    return {
                        "success": False,
                        "error": f"Failed to set product targeting: {targeting_result.get('error')}",
                        "message": "Could not set buyer account allowlist",
                    }
                
                # Wait for targeting changeset to complete
                targeting_changeset_id = targeting_result.get("change_set_id")
                if targeting_changeset_id:
                    for attempt in range(max_wait):
                        time.sleep(5)
                        status_result = self.get_listing_status(targeting_changeset_id)
                        status = status_result.get("status", "UNKNOWN")
                        
                        if status == "SUCCEEDED":
                            break
                        elif status == "FAILED":
                            return {
                                "success": False,
                                "error": f"Product targeting update failed: {status_result.get('error')}",
                                "message": "Could not update product targeting",
                            }
                        elif attempt == max_wait - 1:
                            return {
                                "success": False,
                                "error": "Timeout waiting for product targeting update",
                                "message": "Product targeting update is taking too long",
                            }

            # Step 4: Release both product and offer in a single changeset
            # Strip revision suffixes for the release changeset
            clean_product_id = self._strip_revision_suffix(product_id)
            clean_offer_id = self._strip_revision_suffix(offer_id)
            
            change_set = [
                {
                    "ChangeType": "ReleaseProduct",
                    "Entity": {"Type": "SaaSProduct@1.0", "Identifier": clean_product_id},
                    "DetailsDocument": {},
                },
                {
                    "ChangeType": "ReleaseOffer",
                    "Entity": {"Type": "Offer@1.0", "Identifier": clean_offer_id},
                    "DetailsDocument": {},
                },
            ]

            response = self.catalog_client.start_change_set(
                Catalog="AWSMarketplace",
                ChangeSet=change_set,
                ChangeSetName="Release product and offer to Limited",
            )

            return {
                "success": True,
                "change_set_id": response["ChangeSetId"],
                "message": "Product and offer release to Limited initiated successfully",
            }

        except Exception as e:
            error_msg = str(e)
            return {
                "success": False,
                "error": error_msg,
                "message": f"Failed to release to Limited: {error_msg}",
            }
