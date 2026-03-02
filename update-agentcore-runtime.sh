#!/bin/bash
# Manually update AgentCore runtime with the latest image

set -e

RUNTIME_ARN="arn:aws:bedrock-agentcore:us-east-1:605345174368:runtime/marketplaceAgent-MmeCs3B9mE"
ECR_REPO="605345174368.dkr.ecr.us-east-1.amazonaws.com/bedrock-agentcore-marketplaceagent"

# Get the latest image digest
LATEST_DIGEST=$(aws ecr describe-images \
  --repository-name bedrock-agentcore-marketplaceagent \
  --region us-east-1 \
  --profile default \
  --query 'sort_by(imageDetails, &imagePushedAt)[-1].imageDigest' \
  --output text)

echo "Latest image digest: $LATEST_DIGEST"
IMAGE_URI="${ECR_REPO}@${LATEST_DIGEST}"
echo "Image URI: $IMAGE_URI"

# Update the runtime
echo "Updating AgentCore runtime..."
aws bedrock-agent-runtime update-agent-runtime \
  --agent-runtime-id marketplaceAgent-MmeCs3B9mE \
  --image-uri "$IMAGE_URI" \
  --region us-east-1 \
  --profile default

echo "✅ AgentCore runtime updated successfully"
echo "Please wait 1-2 minutes for the runtime to restart with the new image"
