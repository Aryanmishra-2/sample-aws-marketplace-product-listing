#!/bin/bash
# Upload CloudFormation template to S3 for AgentCore runtime access

set -e

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --profile default)
BUCKET_NAME="ai-agent-marketplace-templates-${AWS_ACCOUNT_ID}"
REGION="us-east-1"

echo "Creating S3 bucket: ${BUCKET_NAME}"
aws s3api create-bucket --bucket ${BUCKET_NAME} --region ${REGION} --profile default 2>/dev/null || echo "Bucket already exists"

echo "Uploading CloudFormation template..."
aws s3 cp deployment/cloudformation/Integration.yaml s3://${BUCKET_NAME}/cloudformation/Integration.yaml --region ${REGION} --profile default

echo "✅ Template uploaded to s3://${BUCKET_NAME}/cloudformation/Integration.yaml"
