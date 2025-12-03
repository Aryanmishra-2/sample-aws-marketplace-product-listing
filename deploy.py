#!/usr/bin/env python3
"""
Deployment script for Listing Products in AWS Marketplace Agent
Deploys the application to AWS using Bedrock AgentCore (future) or current architecture
"""

import argparse
import sys
import subprocess
import os
from pathlib import Path

def check_prerequisites():
    """Check if all prerequisites are installed"""
    print("🔍 Checking prerequisites...")
    
    checks = {
        "Python 3.10+": sys.version_info >= (3, 10),
        "Node.js": subprocess.run(["node", "--version"], capture_output=True).returncode == 0,
        "npm": subprocess.run(["npm", "--version"], capture_output=True).returncode == 0,
        "AWS CLI": subprocess.run(["aws", "--version"], capture_output=True).returncode == 0,
    }
    
    all_passed = True
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check}")
        if not passed:
            all_passed = False
    
    return all_passed

def install_dependencies():
    """Install Python and Node.js dependencies"""
    print("\n📦 Installing dependencies...")
    
    # Python dependencies
    print("  Installing Python packages...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    
    # Node.js dependencies
    print("  Installing Node.js packages...")
    subprocess.run(["npm", "install"], cwd="frontend", check=True)
    
    print("✅ Dependencies installed")

def deploy_backend(args):
    """Deploy FastAPI backend"""
    print("\n🚀 Deploying backend...")
    
    # For now, just provide instructions
    print("""
    Backend deployment options:
    
    1. Local Development:
       cd backend
       uvicorn main:app --host 0.0.0.0 --port 8000
    
    2. AWS ECS Fargate (Production):
       - Build Docker image
       - Push to ECR
       - Deploy to ECS
       See deployment/README.md for details
    
    3. AWS Lambda (Serverless):
       - Package with dependencies
       - Deploy via SAM or CDK
       See deployment/lambda/README.md for details
    """)

def deploy_frontend(args):
    """Deploy Next.js frontend"""
    print("\n🚀 Deploying frontend...")
    
    print("""
    Frontend deployment options:
    
    1. Local Development:
       cd frontend
       npm run dev
    
    2. AWS Amplify (Recommended):
       - Connect GitHub repository
       - Auto-deploy on push
       See deployment/amplify/README.md for details
    
    3. S3 + CloudFront:
       - Build static export
       - Upload to S3
       - Configure CloudFront
       See deployment/s3-cloudfront/README.md for details
    """)

def deploy_agentcore(args):
    """Deploy to Bedrock AgentCore (Future)"""
    print("\n🔮 Deploying to Bedrock AgentCore...")
    
    print("""
    Bedrock AgentCore deployment (Coming Soon):
    
    This will deploy the agent infrastructure to AWS Bedrock AgentCore:
    - Runtime: Serverless agent execution
    - Memory: Multi-strategy memory storage
    - Gateway: MCP-compatible tool integration
    - Identity: IAM-based access management
    - Observability: CloudWatch + X-Ray tracing
    
    See deployment/bedrock-agentcore/README.md for details
    """)

def main():
    parser = argparse.ArgumentParser(
        description="Deploy Listing Products in AWS Marketplace Agent"
    )
    parser.add_argument(
        "--agent-name",
        default="marketplace_listing_agent",
        help="Name for the agent (default: marketplace_listing_agent)"
    )
    parser.add_argument(
        "--region",
        default="us-east-1",
        help="AWS region (default: us-east-1)"
    )
    parser.add_argument(
        "--role-name",
        default="MarketplaceListingAgentRole",
        help="IAM role name (default: MarketplaceListingAgentRole)"
    )
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Skip prerequisite validation"
    )
    parser.add_argument(
        "--component",
        choices=["backend", "frontend", "agentcore", "all"],
        default="all",
        help="Component to deploy (default: all)"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("  Listing Products in AWS Marketplace - Deployment")
    print("=" * 80)
    
    # Check prerequisites
    if not args.skip_checks:
        if not check_prerequisites():
            print("\n❌ Prerequisites check failed. Install missing dependencies.")
            print("   Use --skip-checks to bypass this check.")
            sys.exit(1)
    
    # Install dependencies
    try:
        install_dependencies()
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Failed to install dependencies: {e}")
        sys.exit(1)
    
    # Deploy components
    if args.component in ["backend", "all"]:
        deploy_backend(args)
    
    if args.component in ["frontend", "all"]:
        deploy_frontend(args)
    
    if args.component in ["agentcore", "all"]:
        deploy_agentcore(args)
    
    print("\n" + "=" * 80)
    print("✅ Deployment preparation complete!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Start backend: cd backend && uvicorn main:app --reload")
    print("2. Start frontend: cd frontend && npm run dev")
    print("3. Open browser: http://localhost:3000")
    print("\nFor production deployment, see deployment/README.md")

if __name__ == "__main__":
    main()
