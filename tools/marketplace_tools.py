# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
AWS Marketplace Catalog API tools
"""

import boto3
from typing import Dict, Any, Optional

def validate_credentials(access_key: str, secret_key: str, session_token: Optional[str] = None, region: str = "us-east-1") -> Dict[str, Any]:
    """
    Validate AWS credentials using STS GetCallerIdentity
    
    Args:
        access_key: AWS access key ID
        secret_key: AWS secret access key
        session_token: Optional session token
        region: AWS region
    
    Returns:
        Dict with validation result and identity information
    """
    try:
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token,
            region_name=region
        )
        
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        return {
            "valid": True,
            "account_id": identity['Account'],
            "user_id": identity['UserId'],
            "arn": identity['Arn']
        }
    
    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }

def check_seller_status(session: boto3.Session) -> Dict[str, Any]:
    """
    Check AWS Marketplace seller registration status
    
    Args:
        session: Boto3 session with valid credentials
    
    Returns:
        Dict with seller status information
    """
    try:
        marketplace = session.client('marketplace-catalog')
        
        # Try to describe seller entity
        response = marketplace.list_entities(
            Catalog='AWSMarketplace',
            EntityType='Seller'
        )
        
        if response['EntitySummaryList']:
            seller = response['EntitySummaryList'][0]
            return {
                "registered": True,
                "seller_id": seller.get('EntityId'),
                "name": seller.get('Name'),
                "status": "active"
            }
        else:
            return {
                "registered": False,
                "message": "No seller registration found"
            }
    
    except Exception as e:
        return {
            "registered": False,
            "error": str(e)
        }

def create_product_listing(
    session: boto3.Session,
    product_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a product listing in AWS Marketplace
    
    Args:
        session: Boto3 session with valid credentials
        product_data: Product information including title, description, pricing, etc.
    
    Returns:
        Dict with product ID and offer ID
    """
    try:
        marketplace = session.client('marketplace-catalog')
        
        # Start change set for product creation
        response = marketplace.start_change_set(
            Catalog='AWSMarketplace',
            ChangeSet=[
                {
                    'ChangeType': 'CreateProduct',
                    'Entity': {
                        'Type': 'SaaSProduct@1.0'
                    },
                    'Details': product_data
                }
            ]
        )
        
        change_set_id = response['ChangeSetId']
        
        # Wait for change set to complete
        waiter = marketplace.get_waiter('change_set_complete')
        waiter.wait(
            Catalog='AWSMarketplace',
            ChangeSetId=change_set_id
        )
        
        # Get change set details
        change_set = marketplace.describe_change_set(
            Catalog='AWSMarketplace',
            ChangeSetId=change_set_id
        )
        
        return {
            "success": True,
            "change_set_id": change_set_id,
            "product_id": change_set['ChangeSet'][0]['Entity']['Identifier'],
            "status": change_set['Status']
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_listing_status(
    session: boto3.Session,
    product_id: str
) -> Dict[str, Any]:
    """
    Get the status of a product listing
    
    Args:
        session: Boto3 session with valid credentials
        product_id: Product entity ID
    
    Returns:
        Dict with listing status information
    """
    try:
        marketplace = session.client('marketplace-catalog')
        
        response = marketplace.describe_entity(
            Catalog='AWSMarketplace',
            EntityId=product_id
        )
        
        return {
            "success": True,
            "product_id": product_id,
            "status": response.get('Details', {}).get('Status'),
            "details": response.get('Details', {})
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
