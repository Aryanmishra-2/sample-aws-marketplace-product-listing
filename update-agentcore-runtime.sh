#!/bin/bash
# Manually update AgentCore runtime with the latest image

set -e

# Resolve account and region dynamically
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION="${AWS_DEFAULT_REGION:-us-east-1}"

# Derive ARN and ECR repo from agentcore config or environment
RUNTIME_ID="${AGENTCORE_RUNTIME_ID:-marketplaceAgent-MmeCs3B9mE}"
RUNTIME_ARN="arn:aws:bedrock-agentcore:${AWS_REGION}:${AWS_ACCOUNT_ID}:runtime/${RUNTIME_ID}"
ECR_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/bedrock-agentcore-marketplaceagent"

# Get the latest image digest
LATEST_DIGEST=$(aws ecr describe-images \
  --repository-name bedrock-agentcore-marketplaceagent \
  --region "${AWS_REGION}" \
  --query 'sort_by(imageDetails, &imagePushedAt)[-1].imageDigest' \
  --output text)

echo "Latest image digest: $LATEST_DIGEST"
IMAGE_URI="${ECR_REPO}@${LATEST_DIGEST}"
echo "Image URI: $IMAGE_URI"

# Update the runtime
echo "Updating AgentCore runtime..."
aws bedrock-agent-runtime update-agent-runtime \
  --agent-runtime-id "${RUNTIME_ID}" \
  --image-uri "$IMAGE_URI" \
  --region "${AWS_REGION}"

echo "✅ AgentCore runtime updated successfully"
echo "Please wait 1-2 minutes for the runtime to restart with the new image"
