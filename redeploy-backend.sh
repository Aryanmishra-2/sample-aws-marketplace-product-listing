#!/bin/bash
# Redeploy AgentCore backend with embedded CloudFormation template

set -e

echo "🚀 Redeploying AgentCore backend..."

# Update the config to use the latest image tag
LATEST_TAG=$(aws ecr describe-images \
  --repository-name bedrock-agentcore-marketplaceagent \
  --region us-east-1 \
  --profile default \
  --query 'sort_by(imageDetails, &imagePushedAt)[-1].imageTags[0]' \
  --output text)

echo "Latest image tag: $LATEST_TAG"

# Launch with auto-update
AWS_PROFILE=default agentcore launch --agent marketplaceAgent --auto-update-on-conflict

echo "✅ Backend redeployed successfully"
