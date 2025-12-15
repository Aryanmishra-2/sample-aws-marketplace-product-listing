#!/usr/bin/env python3
"""
Cleanup script for Listing Products in AWS Marketplace Agent
Removes all AWS resources and local artifacts
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

def cleanup_local_artifacts(dry_run=False):
    """Clean up local build artifacts and cache"""
    print("\n🧹 Cleaning local artifacts...")
    
    artifacts = [
        "frontend/.next",
        "frontend/node_modules/.cache",
        "backend/__pycache__",
        "**/__pycache__",
        "**/*.pyc",
        ".agent_arn",
        ".deployment_info.json",
    ]
    
    for pattern in artifacts:
        if dry_run:
            print(f"   [DRY RUN] Would remove: {pattern}")
        else:
            if "*" in pattern:
                # Use find for glob patterns
                subprocess.run(
                    f"find . -type d -name '{pattern.split('/')[-1]}' -exec rm -rf {{}} + 2>/dev/null",
                    shell=True
                )
            else:
                path = Path(pattern)
                if path.exists():
                    if path.is_dir():
                        subprocess.run(["rm", "-rf", str(path)])
                        print(f"   ✅ Removed: {pattern}")
                    else:
                        path.unlink()
                        print(f"   ✅ Removed: {pattern}")

def cleanup_cloudformation_stacks(region, dry_run=False):
    """Clean up CloudFormation stacks"""
    print(f"\n☁️  Cleaning CloudFormation stacks in {region}...")
    
    try:
        # List stacks with our naming pattern
        result = subprocess.run(
            [
                "aws", "cloudformation", "list-stacks",
                "--region", region,
                "--stack-status-filter", "CREATE_COMPLETE", "UPDATE_COMPLETE",
                "--query", "StackSummaries[?contains(StackName, 'marketplace-listing') || contains(StackName, 'MarketplaceListing')].StackName",
                "--output", "text"
            ],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            stacks = result.stdout.strip().split()
            for stack in stacks:
                if dry_run:
                    print(f"   [DRY RUN] Would delete stack: {stack}")
                else:
                    print(f"   🗑️  Deleting stack: {stack}")
                    subprocess.run(
                        ["aws", "cloudformation", "delete-stack", "--stack-name", stack, "--region", region],
                        check=True
                    )
                    print(f"   ✅ Stack deletion initiated: {stack}")
        else:
            print("   ℹ️  No CloudFormation stacks found")
    
    except subprocess.CalledProcessError as e:
        print(f"   ⚠️  Error listing/deleting stacks: {e}")

def cleanup_iam_roles(dry_run=False, skip_iam=False):
    """Clean up IAM roles"""
    if skip_iam:
        print("\n⏭️  Skipping IAM role cleanup (--skip-iam)")
        return
    
    print("\n🔐 Cleaning IAM roles...")
    
    role_names = [
        "MarketplaceListingAgentRole",
        "MarketplaceListingLambdaRole",
        "MarketplaceListingSaaSRole",
    ]
    
    for role_name in role_names:
        try:
            # Check if role exists
            result = subprocess.run(
                ["aws", "iam", "get-role", "--role-name", role_name],
                capture_output=True
            )
            
            if result.returncode == 0:
                if dry_run:
                    print(f"   [DRY RUN] Would delete role: {role_name}")
                else:
                    # Detach policies first
                    print(f"   🗑️  Deleting role: {role_name}")
                    
                    # List and detach managed policies
                    policies_result = subprocess.run(
                        ["aws", "iam", "list-attached-role-policies", "--role-name", role_name, "--query", "AttachedPolicies[].PolicyArn", "--output", "text"],
                        capture_output=True,
                        text=True
                    )
                    
                    if policies_result.stdout.strip():
                        for policy_arn in policies_result.stdout.strip().split():
                            subprocess.run(
                                ["aws", "iam", "detach-role-policy", "--role-name", role_name, "--policy-arn", policy_arn]
                            )
                    
                    # Delete inline policies
                    inline_result = subprocess.run(
                        ["aws", "iam", "list-role-policies", "--role-name", role_name, "--query", "PolicyNames", "--output", "text"],
                        capture_output=True,
                        text=True
                    )
                    
                    if inline_result.stdout.strip():
                        for policy_name in inline_result.stdout.strip().split():
                            subprocess.run(
                                ["aws", "iam", "delete-role-policy", "--role-name", role_name, "--policy-name", policy_name]
                            )
                    
                    # Delete role
                    subprocess.run(
                        ["aws", "iam", "delete-role", "--role-name", role_name],
                        check=True
                    )
                    print(f"   ✅ Role deleted: {role_name}")
        
        except subprocess.CalledProcessError:
            # Role doesn't exist or error occurred
            pass

def cleanup_s3_artifacts(region, dry_run=False):
    """Clean up S3 build artifacts"""
    print(f"\n📦 Cleaning S3 artifacts in {region}...")
    
    try:
        # List buckets with our naming pattern
        result = subprocess.run(
            ["aws", "s3", "ls"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            buckets = [line.split()[-1] for line in result.stdout.strip().split('\n') if 'marketplace-listing' in line.lower()]
            
            for bucket in buckets:
                if dry_run:
                    print(f"   [DRY RUN] Would delete bucket: {bucket}")
                else:
                    print(f"   🗑️  Deleting bucket: {bucket}")
                    # Empty bucket first
                    subprocess.run(["aws", "s3", "rm", f"s3://{bucket}", "--recursive"])
                    # Delete bucket
                    subprocess.run(["aws", "s3", "rb", f"s3://{bucket}"])
                    print(f"   ✅ Bucket deleted: {bucket}")
        
        if not buckets:
            print("   ℹ️  No S3 buckets found")
    
    except subprocess.CalledProcessError as e:
        print(f"   ⚠️  Error cleaning S3: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Clean up Listing Products in AWS Marketplace Agent resources"
    )
    parser.add_argument(
        "--region",
        default="us-east-1",
        help="AWS region (default: us-east-1)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be deleted without actually deleting"
    )
    parser.add_argument(
        "--skip-iam",
        action="store_true",
        help="Skip IAM role cleanup (useful if roles are shared)"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("  Listing Products in AWS Marketplace - Cleanup")
    print("=" * 80)
    
    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No resources will be deleted")
    
    # Clean up resources
    cleanup_local_artifacts(args.dry_run)
    cleanup_cloudformation_stacks(args.region, args.dry_run)
    cleanup_s3_artifacts(args.region, args.dry_run)
    cleanup_iam_roles(args.dry_run, args.skip_iam)
    
    print("\n" + "=" * 80)
    if args.dry_run:
        print("✅ Dry run complete! Run without --dry-run to actually delete resources.")
    else:
        print("✅ Cleanup complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
