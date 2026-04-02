#!/bin/bash
# Upload CloudFormation template to S3 for AgentCore runtime access

set -e

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET_NAME="ai-agent-marketplace-templates-${AWS_ACCOUNT_ID}"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"

echo "Creating S3 bucket: ${BUCKET_NAME}"
aws s3api create-bucket --bucket ${BUCKET_NAME} --region ${REGION} 2>/dev/null || echo "Bucket already exists"

# Block public access
aws s3api put-public-access-block --bucket ${BUCKET_NAME} \
    --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Enable server-side encryption
aws s3api put-bucket-encryption --bucket ${BUCKET_NAME} \
    --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"aws:kms"},"BucketKeyEnabled":true}]}'

echo "Uploading CloudFormation template..."
aws s3 cp deployment/cloudformation/Integration.yaml s3://${BUCKET_NAME}/cloudformation/Integration.yaml --region ${REGION}

echo "✅ Template uploaded to s3://${BUCKET_NAME}/cloudformation/Integration.yaml"
