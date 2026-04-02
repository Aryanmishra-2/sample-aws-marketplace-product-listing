# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from strands import Agent
import boto3
import json
import os

class CreateSaasAgent(Agent):
    def __init__(self):
        super().__init__(name="CreateSaas")
        self._product_id = None
        self._pricing_model = None
        self._aws_credentials = None
        self._pricing_dimensions = None  # Store user-entered dimensions
    
    def set_credentials(self, access_key, secret_key, session_token=None):
        """Set AWS credentials for API calls"""
        self._aws_credentials = {
            'aws_access_key_id': access_key,
            'aws_secret_access_key': secret_key,
            'aws_session_token': session_token
        }
    
    def set_product_id(self, product_id):
        """Set the product ID to work with"""
        self._product_id = product_id
    
    def get_product_id(self):
        if not self._product_id:
            raise ValueError("Product ID is not set. Call set_product_id() first.")
        return self._product_id
    
    def get_aws_account_id(self):
        return os.environ.get("AWS_ACCOUNT_ID", "<YOUR_ACCOUNT_ID>")
    
    def get_pricing_model_dimension(self):
        """Retrieve pricing model from the product's limited listing"""
        print(f"[CREATE_SAAS] ===== GET_PRICING_MODEL DEBUG =====")
        print(f"[CREATE_SAAS] → Product ID: {self._product_id}")
        print(f"[CREATE_SAAS] → In-memory pricing model: {self._pricing_model}")
        
        if self._pricing_model:
            print(f"[CREATE_SAAS] ✓ Using in-memory pricing model: {self._pricing_model}")
            return self._pricing_model
        
        # First priority: Try to load from stored file (for existing stacks)
        stored_pricing_model = self._load_stored_pricing_model()
        if stored_pricing_model:
            self._pricing_model = stored_pricing_model
            print(f"[CREATE_SAAS] ✓ Using stored pricing model: {stored_pricing_model}")
            return stored_pricing_model
        
        # Second priority: Try to fetch from marketplace catalog
        if self._aws_credentials and self._product_id:
            try:
                pricing_model = self._fetch_pricing_model_from_marketplace()
                if pricing_model:
                    self._pricing_model = pricing_model
                    print(f"[CREATE_SAAS] ✓ Using marketplace API pricing model: {pricing_model}")
                    return pricing_model
            except Exception as e:
                print(f"[CREATE_SAAS] → Could not fetch pricing model from marketplace: {e}")
        
        # Fallback to default (should not happen if user entered data properly)
        print(f"[CREATE_SAAS] ⚠ Using fallback pricing model - no user data found!")
        return "Usage-based-pricing"
    
    def set_pricing_dimensions(self, dimensions):
        """Store the pricing dimensions from create listing process"""
        self._pricing_dimensions = dimensions
        print(f"[CREATE_SAAS] ✓ Stored {len(dimensions)} pricing dimensions from create listing")
    
    def get_usage_dimensions(self):
        """Retrieve usage dimensions from the create listing process (user-entered)"""
        print(f"[CREATE_SAAS] ===== GET_USAGE_DIMENSIONS DEBUG =====")
        print(f"[CREATE_SAAS] → Product ID: {self._product_id}")
        print(f"[CREATE_SAAS] → Has AWS credentials: {bool(self._aws_credentials)}")
        print(f"[CREATE_SAAS] → In-memory pricing dimensions: {self._pricing_dimensions}")
        
        try:
            # First priority: Use dimensions from create listing process (in-memory)
            if self._pricing_dimensions:
                print(f"[CREATE_SAAS] → PRIORITY 1: Found in-memory pricing dimensions")
                dimension_keys = []
                for dim in self._pricing_dimensions:
                    # Only include "Metered" dimensions for usage tracking
                    dim_type = dim.get("type", "").lower()
                    print(f"[CREATE_SAAS] → Checking dimension: {dim.get('name', 'N/A')} (type: {dim.get('type', 'N/A')})")
                    
                    if dim_type == "metered":
                        # Extract the key from user-entered dimension
                        # Priority: key > name (converted to key format) > fallback
                        key = dim.get("key")
                        if not key and dim.get("name"):
                            # Convert name to key format (lowercase, underscores)
                            key = dim.get("name", "").lower().replace(" ", "_").replace("-", "_")
                        
                        if key:
                            dimension_keys.append(key)
                            print(f"[CREATE_SAAS] → ✓ Added METERED dimension: {key} (name: {dim.get('name', 'N/A')})")
                    else:
                        print(f"[CREATE_SAAS] → ✗ Skipped NON-METERED dimension: {dim.get('name', 'N/A')} (type: {dim.get('type', 'N/A')})")
                
                if dimension_keys:
                    print(f"[CREATE_SAAS] ✓ RETURNING {len(dimension_keys)} METERED dimensions from PRIORITY 1: {dimension_keys}")
                    return dimension_keys
                else:
                    print(f"[CREATE_SAAS] → No METERED dimensions found in in-memory data")
            else:
                print(f"[CREATE_SAAS] → PRIORITY 1: No in-memory pricing dimensions")
            
            # Second priority: Try to load from stored file (for existing stacks)
            print(f"[CREATE_SAAS] → PRIORITY 2: Trying to load from stored file...")
            stored_dimensions = self._load_stored_dimensions()
            if stored_dimensions:
                print(f"[CREATE_SAAS] ✓ RETURNING from PRIORITY 2: {stored_dimensions}")
                return stored_dimensions
            else:
                print(f"[CREATE_SAAS] → PRIORITY 2: No stored dimensions found")
            
            # Third priority: Try to fetch from marketplace catalog
            if self._aws_credentials and self._product_id:
                print(f"[CREATE_SAAS] → PRIORITY 3: Trying marketplace API...")
                dimensions = self._fetch_dimensions_from_marketplace()
                if dimensions:
                    print(f"[CREATE_SAAS] ✓ RETURNING from PRIORITY 3 (MARKETPLACE API): {dimensions}")
                    print(f"[CREATE_SAAS] ⚠ WARNING: Using marketplace API dimensions, not user-entered!")
                    return dimensions
                else:
                    print(f"[CREATE_SAAS] → PRIORITY 3: AWS Marketplace API returned no dimensions")
            else:
                print(f"[CREATE_SAAS] → PRIORITY 3: Skipped (no credentials or product ID)")
            
            # No fallback to hardcoded dimensions - return empty list if no user dimensions found
            print(f"[CREATE_SAAS] ✗ ALL PRIORITIES FAILED - No dimensions found anywhere")
            print(f"[CREATE_SAAS] → Returning empty dimension list - metering will be skipped")
            print(f"[CREATE_SAAS] ===== END GET_USAGE_DIMENSIONS DEBUG =====")
            return []
            
        except Exception as e:
            print(f"[CREATE_SAAS] ✗ Error retrieving dimensions: {e}")
            print(f"[CREATE_SAAS] → Returning empty dimension list - metering will be skipped")
            print(f"[CREATE_SAAS] ===== END GET_USAGE_DIMENSIONS DEBUG =====")
            return []
    
    def _load_stored_pricing_model(self):
        """Load pricing model from stored file (for existing stacks)"""
        try:
            if not self._product_id:
                print(f"[CREATE_SAAS] → No product ID available for loading stored pricing model")
                return None
            
            import os
            import json
            
            # Look for stored dimensions file
            backend_dir = os.path.dirname(os.path.dirname(__file__))  # Go up from agents/ to project root
            storage_dir = os.path.join(backend_dir, 'backend', 'storage')
            dimensions_file = os.path.join(storage_dir, f'pricing_dimensions_{self._product_id}.json')
            
            print(f"[CREATE_SAAS] → Looking for stored pricing model: {dimensions_file}")
            
            if os.path.exists(dimensions_file):
                with open(dimensions_file, 'r') as f:
                    dimension_data = json.load(f)
                
                stored_pricing_model = dimension_data.get('pricing_model')
                print(f"[CREATE_SAAS] → Found stored pricing model: {stored_pricing_model}")
                
                return stored_pricing_model
            else:
                print(f"[CREATE_SAAS] → No stored pricing model file found")
                return None
                
        except Exception as e:
            print(f"[CREATE_SAAS] → Error loading stored pricing model: {e}")
            return None

    def _load_stored_dimensions(self):
        """Load pricing dimensions from stored file (for existing stacks)"""
        try:
            if not self._product_id:
                print(f"[CREATE_SAAS] → No product ID available for loading stored dimensions")
                return None
            
            import os
            import json
            
            # Look for stored dimensions file
            backend_dir = os.path.dirname(os.path.dirname(__file__))  # Go up from agents/ to project root
            storage_dir = os.path.join(backend_dir, 'backend', 'storage')
            dimensions_file = os.path.join(storage_dir, f'pricing_dimensions_{self._product_id}.json')
            
            print(f"[CREATE_SAAS] → Looking for stored dimensions: {dimensions_file}")
            
            if os.path.exists(dimensions_file):
                with open(dimensions_file, 'r') as f:
                    dimension_data = json.load(f)
                
                stored_dimensions = dimension_data.get('pricing_dimensions', [])
                print(f"[CREATE_SAAS] → Found stored file with {len(stored_dimensions)} dimensions")
                
                # Extract dimension keys from stored data - only METERED dimensions
                dimension_keys = []
                for dim in stored_dimensions:
                    # Only include "Metered" dimensions for usage tracking
                    dim_type = dim.get("type", "").lower()
                    print(f"[CREATE_SAAS] → Checking stored dimension: {dim.get('name', 'N/A')} (type: {dim.get('type', 'N/A')})")
                    
                    if dim_type == "metered":
                        # Extract the key from stored dimension
                        key = dim.get("key")
                        if not key and dim.get("name"):
                            # Convert name to key format (lowercase, underscores)
                            key = dim.get("name", "").lower().replace(" ", "_").replace("-", "_")
                        
                        if key:
                            dimension_keys.append(key)
                            print(f"[CREATE_SAAS] → ✓ Loaded METERED dimension: {key} (name: {dim.get('name', 'N/A')})")
                    else:
                        print(f"[CREATE_SAAS] → ✗ Skipped NON-METERED stored dimension: {dim.get('name', 'N/A')} (type: {dim.get('type', 'N/A')})")
                
                return dimension_keys if dimension_keys else None
            else:
                print(f"[CREATE_SAAS] → No stored dimensions file found")
                return None
                
        except Exception as e:
            print(f"[CREATE_SAAS] → Error loading stored dimensions: {e}")
            return None

    def _fetch_dimensions_from_marketplace(self):
        """Fetch dimensions from AWS Marketplace Catalog API"""
        try:
            catalog_client = boto3.client(
                'marketplace-catalog',
                region_name='us-east-1',
                aws_access_key_id=self._aws_credentials['aws_access_key_id'],
                aws_secret_access_key=self._aws_credentials['aws_secret_access_key'],
                aws_session_token=self._aws_credentials.get('aws_session_token')
            )
            
            # Get entity ID with revision
            entity_id = self._get_entity_id(catalog_client)
            if not entity_id:
                print(f"  → Could not find entity ID for product {self._product_id}")
                return None
            
            print(f"  → Found entity ID: {entity_id}")
            
            # Describe the entity to get dimensions
            response = catalog_client.describe_entity(
                Catalog='AWSMarketplace',
                EntityId=entity_id
            )
            
            details = response.get('Details', {})
            if isinstance(details, str):
                details = json.loads(details)
            
            # Extract dimensions
            dimensions = details.get('Dimensions', [])
            if not dimensions:
                print(f"  → No dimensions found in marketplace listing")
                return None
            
            # Extract dimension keys/names - only METERED dimensions (skip contract/entitled)
            dimension_names = []
            for dim in dimensions:
                print(f"  → [DEBUG] Raw dimension data: {dim}")
                
                key = dim.get('Key')
                name = dim.get('Name') 
                description = dim.get('Description')
                dim_types = dim.get('Types', [])
                
                # Skip contract/entitled dimensions - only include metered ones
                # Types can be ['Metered'], ['Entitled'], or ['Metered', 'Entitled'] etc.
                is_metered = 'Metered' in dim_types if dim_types else True  # default to include if no Types field
                is_entitled_only = dim_types and 'Entitled' in dim_types and 'Metered' not in dim_types
                
                if is_entitled_only:
                    print(f"  → ✗ Skipping CONTRACT/ENTITLED dimension: Key='{key}', Name='{name}', Types={dim_types}")
                    continue
                
                if key:
                    dimension_names.append(key)
                    print(f"  → ✓ Found METERED dimension: Key='{key}', Name='{name}', Types={dim_types}")
                else:
                    print(f"  → [WARNING] Dimension missing 'Key' field: {dim}")
            
            if dimension_names:
                print(f"  → Retrieved {len(dimension_names)} dimension(s): {dimension_names}")
                print(f"  → [INFO] These are the API identifiers used for metering")
                return dimension_names
            else:
                print(f"  → No dimension keys could be extracted")
                return None
                
        except Exception as e:
            print(f"  → Error fetching dimensions from marketplace: {e}")
            return None
    
    def _fetch_pricing_model_from_marketplace(self):
        """Fetch pricing model from AWS Marketplace Catalog API"""
        try:
            catalog_client = boto3.client(
                'marketplace-catalog',
                region_name='us-east-1',
                **self._aws_credentials
            )
            
            # Get entity ID with revision
            entity_id = self._get_entity_id(catalog_client)
            if not entity_id:
                return None
            
            # Describe the product entity
            response = catalog_client.describe_entity(
                Catalog='AWSMarketplace',
                EntityId=entity_id
            )
            
            details = response.get('Details', '{}')
            if isinstance(details, str):
                details = json.loads(details)
            
            print(f"  → Analyzing product pricing configuration...")
            
            # Check pricing terms (most reliable method)
            pricing_terms = details.get('PricingTerms', [])
            has_usage_based = False
            has_contract = False
            
            for term in pricing_terms:
                term_type = term.get('Type', '')
                print(f"  → Found pricing term: {term_type}")
                
                if term_type == 'UsageBasedPricingTerm':
                    has_usage_based = True
                elif term_type in ['ConfigurableUpfrontPricingTerm', 'FixedUpfrontPricingTerm']:
                    has_contract = True
            
            # Determine pricing model based on terms
            if has_usage_based and has_contract:
                print(f"  → Detected: Contract-with-consumption")
                return "Contract-with-consumption"
            elif has_usage_based:
                print(f"  → Detected: Usage-based-pricing")
                return "Usage-based-pricing"
            elif has_contract:
                print(f"  → Detected: Contract-based-pricing")
                return "Contract-based-pricing"
            
            # Fallback: Check dimensions
            dimensions = details.get('Dimensions', [])
            if dimensions:
                print(f"  → Checking {len(dimensions)} dimension(s) as fallback...")
                for dim in dimensions:
                    dim_types = dim.get('Types', [])
                    print(f"  → Dimension types: {dim_types}")
                    
                    if 'Metered' in dim_types:
                        print(f"  → Detected: Usage-based-pricing (from dimensions)")
                        return "Usage-based-pricing"
                    elif 'Entitled' in dim_types:
                        print(f"  → Detected: Contract-based-pricing (from dimensions)")
                        return "Contract-based-pricing"
            
            print(f"  → Could not determine pricing model from marketplace data")
            return None
            
        except Exception as e:
            print(f"Error fetching pricing model: {e}")
            return None
    
    def _get_entity_id(self, catalog_client):
        """Get entity ID with revision for the product"""
        try:
            # List entities to find current revision
            response = catalog_client.list_entities(
                Catalog='AWSMarketplace',
                EntityType='SaaSProduct',
                MaxResults=50
            )
            
            for entity in response.get('EntitySummaryList', []):
                entity_id = entity.get('EntityId', '')
                if entity_id.startswith(self._product_id):
                    return entity_id
            
            # Try with pagination
            next_token = response.get('NextToken')
            while next_token:
                response = catalog_client.list_entities(
                    Catalog='AWSMarketplace',
                    EntityType='SaaSProduct',
                    MaxResults=50,
                    NextToken=next_token
                )
                
                for entity in response.get('EntitySummaryList', []):
                    entity_id = entity.get('EntityId', '')
                    if entity_id.startswith(self._product_id):
                        return entity_id
                
                next_token = response.get('NextToken')
            
            # Fallback: try common revision numbers
            for revision in range(1, 11):
                try:
                    test_id = f"{self._product_id}@{revision}"
                    catalog_client.describe_entity(
                        Catalog='AWSMarketplace',
                        EntityId=test_id
                    )
                    return test_id
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"Error getting entity ID: {e}")
            return None
    
    def get_email_dimension(self):
        return os.environ.get('CONTACT_EMAIL', 'support@example.com')
    
