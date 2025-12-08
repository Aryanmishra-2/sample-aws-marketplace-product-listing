from strands import Agent
import boto3
import json

class CreateSaasAgent(Agent):
    def __init__(self):
        super().__init__(name="CreateSaas")
        self._product_id = None
        self._pricing_model = None
        self._aws_credentials = None
    
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
        return self._product_id or "prod-ebsllm6bj3ccm"
    
    def get_aws_account_id(self):
        return "605345174368"
    
    def get_pricing_model_dimension(self):
        """Retrieve pricing model from the product's limited listing"""
        if self._pricing_model:
            return self._pricing_model
        
        # Try to fetch from marketplace catalog
        if self._aws_credentials and self._product_id:
            try:
                pricing_model = self._fetch_pricing_model_from_marketplace()
                if pricing_model:
                    self._pricing_model = pricing_model
                    return pricing_model
            except Exception as e:
                print(f"Warning: Could not fetch pricing model from marketplace: {e}")
        
        # Fallback to default
        return "Usage-based-pricing"
    
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
        return "jain.manasvi1999@gmail.com"
    
    def get_usage_dimensions(self):
        return ["dimension_1_id"]