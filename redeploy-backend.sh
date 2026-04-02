#!/bin/bash
# Redeploy AgentCore backend with embedded CloudFormation template

set -e

echo "🚀 Redeploying AgentCore backend..."

AWS_REGION="${AWS_DEFAULT_REGION:-us-east-1}"

# Update the config to use the latest image tag
LATEST_TAG=$(aws ecr describe-images \
  --repository-name bedrock-agentcore-marketplaceagent \
  --region "${AWS_REGION}" \
  --query 'sort_by(imageDetails, &imagePushedAt)[-1].imageTags[0]' \
  --output text)

echo "Latest image tag: $LATEST_TAG"

# Launch with auto-update
agentcore launch --agent marketplaceAgent --auto-update-on-conflict

echo "✅ Backend redeployed successfully"
