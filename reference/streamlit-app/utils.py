#!/usr/bin/env python3
"""
Utility scripts for AWS Marketplace SaaS Listing Creator
Consolidated testing and debugging tools
"""

import sys
import os
import time
import boto3
from botocore.exceptions import ClientError


def check_bedrock_models():
    """Check available Bedrock models"""
    print("=" * 70)
    print("AWS Bedrock Model Availability Check")
    print("=" * 70)
    print()
    
    try:
        bedrock = boto3.client('bedrock', region_name='us-east-1')
        
        print("Checking foundation models...")
        response = bedrock.list_foundation_models()
        
        # Filter for Claude models
        claude_models = [
            model for model in response.get('modelSummaries', [])
            if 'claude' in model.get('modelId', '').lower()
        ]
        
        if claude_models:
            print(f"\n✓ Found {len(claude_models)} Claude models:\n")
            for model in claude_models:
                model_id = model.get('modelId', 'Unknown')
                model_name = model.get('modelName', 'Unknown')
                status = model.get('modelLifecycle', {}).get('status', 'Unknown')
                
                if '3-5-sonnet' in model_id or '3.5' in model_name:
                    print(f"  ⭐ {model_id}")
                    print(f"     Name: {model_name}")
                    print(f"     Status: {status}")
                    print()
        else:
            print("\n✗ No Claude models found")
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDeniedException':
            print("✗ Access denied to Bedrock")
            print("\nTo fix:")
            print("  1. Enable model access in Bedrock console")
            print("  2. Check IAM permissions")
        else:
            print(f"✗ Error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("Recommended Model IDs")
    print("=" * 70)
    
    recommended = [
        ("us.anthropic.claude-3-5-sonnet-20241022-v2:0", "Claude 3.5 Sonnet v2 (US cross-region)"),
        ("anthropic.claude-3-5-sonnet-20240620-v1:0", "Claude 3.5 Sonnet v1"),
        ("anthropic.claude-3-sonnet-20240229-v1:0", "Claude 3 Sonnet"),
    ]
    
    for model_id, description in recommended:
        print(f"  • {model_id}")
        print(f"    {description}")
        print()
    
    return True


def check_changeset(change_set_id: str, wait: bool = False):
    """Check change set status and extract entity IDs"""
    from agent.tools.listing_tools import ListingTools
    
    tools = ListingTools()
    
    print(f"Checking change set: {change_set_id}")
    print("=" * 70)
    
    max_attempts = 20 if wait else 1
    attempt = 0
    
    while attempt < max_attempts:
        result = tools.get_listing_status(change_set_id)
        
        if not result.get("success"):
            print(f"❌ Error: {result.get('error')}")
            return None
        
        status = result.get("status")
        print(f"\nAttempt {attempt + 1}/{max_attempts}")
        print(f"Status: {status}")
        
        if status == "SUCCEEDED":
            print("\n✅ Change set completed successfully!")
            
            # Extract entity IDs
            change_set = result.get("change_set", [])
            product_id = None
            offer_id = None
            
            for change in change_set:
                entity = change.get("Entity", {})
                entity_type = entity.get("Type", "")
                entity_id = entity.get("Identifier", "")
                change_type = change.get("ChangeType", "")
                
                print(f"\n  Change: {change_type}")
                print(f"  Entity Type: {entity_type}")
                print(f"  Entity ID: {entity_id}")
                
                if "SaaSProduct" in entity_type:
                    product_id = entity_id
                elif "Offer" in entity_type:
                    offer_id = entity_id
            
            print("\n" + "=" * 70)
            print("ENTITY IDs EXTRACTED:")
            print("=" * 70)
            if product_id:
                print(f"✅ Product ID: {product_id}")
            if offer_id:
                print(f"✅ Offer ID: {offer_id}")
            
            return {
                "product_id": product_id,
                "offer_id": offer_id,
                "status": status
            }
        
        elif status in ["FAILED", "CANCELLED"]:
            print(f"\n❌ Change set {status}")
            change_set = result.get("change_set", [])
            for change in change_set:
                error_detail = change.get("ErrorDetailList", [])
                if error_detail:
                    print("\nError Details:")
                    for error in error_detail:
                        print(f"  - {error.get('ErrorMessage', 'Unknown error')}")
            return None
        
        elif status in ["PREPARING", "APPLYING"]:
            if wait and attempt < max_attempts - 1:
                print(f"⏳ Still processing... waiting 3 seconds")
                time.sleep(3)
                attempt += 1
            else:
                print(f"\n⏳ Change set is still {status}")
                print(f"\nRun with --wait flag to poll: python utils.py changeset {change_set_id} --wait")
                return None
        else:
            print(f"\n⚠️  Unknown status: {status}")
            return None
    
    print(f"\n⏱️  Timeout after {max_attempts * 3} seconds")
    return None


def test_setup():
    """Test setup and configuration"""
    print("=" * 70)
    print("Setup Verification")
    print("=" * 70)
    
    results = []
    
    # Python version
    print("\n1. Python Version")
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}")
    if version.major >= 3 and version.minor >= 8:
        print("   ✓ Compatible (3.8+)")
        results.append(True)
    else:
        print("   ✗ Too old (need 3.8+)")
        results.append(False)
    
    # Dependencies
    print("\n2. Dependencies")
    required = ["boto3", "yaml", "streamlit"]
    all_installed = True
    for package in required:
        try:
            if package == "yaml":
                __import__("yaml")
            else:
                __import__(package)
            print(f"   ✓ {package}")
        except ImportError:
            print(f"   ✗ {package} not installed")
            all_installed = False
    results.append(all_installed)
    
    # Config files
    print("\n3. Configuration Files")
    configs = ["config/agent_config.yaml", "config/marketplace_config.yaml"]
    all_exist = True
    for config in configs:
        if os.path.exists(config):
            print(f"   ✓ {config}")
        else:
            print(f"   ✗ {config} missing")
            all_exist = False
    results.append(all_exist)
    
    # AWS credentials
    print("\n4. AWS Credentials")
    try:
        boto3.client('sts').get_caller_identity()
        print("   ✓ AWS credentials configured")
        results.append(True)
    except Exception as e:
        print(f"   ✗ AWS credentials not configured: {e}")
        results.append(False)
    
    print("\n" + "=" * 70)
    if all(results):
        print("✅ All checks passed!")
        print("\nRun the app: streamlit run streamlit_guided_app.py")
        return 0
    else:
        print("❌ Some checks failed")
        print("\nFix:")
        print("  pip install -r requirements.txt")
        print("  ./setup_aws_credentials.sh")
        return 1


def print_usage():
    """Print usage information"""
    print("""
AWS Marketplace SaaS Listing Creator - Utilities

Usage:
  python utils.py <command> [options]

Commands:
  test              Run setup verification tests
  bedrock           Check Bedrock model availability
  changeset <id>    Check changeset status
                    Options: --wait (poll until complete)

Examples:
  python utils.py test
  python utils.py bedrock
  python utils.py changeset abc123xyz
  python utils.py changeset abc123xyz --wait
""")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print_usage()
        return 1
    
    command = sys.argv[1].lower()
    
    if command == "test":
        return test_setup()
    
    elif command == "bedrock":
        check_bedrock_models()
        return 0
    
    elif command == "changeset":
        if len(sys.argv) < 3:
            print("Error: changeset ID required")
            print("Usage: python utils.py changeset <changeset_id> [--wait]")
            return 1
        change_set_id = sys.argv[2]
        wait = "--wait" in sys.argv or "-w" in sys.argv
        result = check_changeset(change_set_id, wait=wait)
        return 0 if result else 1
    
    else:
        print(f"Unknown command: {command}")
        print_usage()
        return 1


if __name__ == "__main__":
    sys.exit(main())
