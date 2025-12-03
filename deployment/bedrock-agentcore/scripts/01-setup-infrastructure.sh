#!/bin/bash
set -e

echo "========================================="
echo "Setting up Bedrock AgentCore Infrastructure"
echo "Account: 797583073197"
echo "Region: us-east-1"
echo "========================================="

# Load configuration
CONFIG_FILE="../config/deployment-config.json"
ACCOUNT_ID=$(jq -r '.account_id' $CONFIG_FILE)
REGION=$(jq -r '.region' $CONFIG_FILE)
S3_BUCKET=$(jq -r '.resources.s3_bucket' $CONFIG_FILE)
DYNAMODB_TABLE=$(jq -r '.resources.dynamodb_table' $CONFIG_FILE)
LOG_GROUP=$(jq -r '.resources.log_group' $CONFIG_FILE)

echo "Step 1: Creating S3 bucket for Knowledge Base..."
aws s3 mb s3://$S3_BUCKET --region $REGION 2>/dev/null || echo "Bucket already exists"

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket $S3_BUCKET \
  --versioning-configuration Status=Enabled

# Add bucket policy for Bedrock access
cat > /tmp/bucket-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockKnowledgeBaseAccess",
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::$S3_BUCKET",
        "arn:aws:s3:::$S3_BUCKET/*"
      ],
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "$ACCOUNT_ID"
        }
      }
    }
  ]
}
EOF

aws s3api put-bucket-policy \
  --bucket $S3_BUCKET \
  --policy file:///tmp/bucket-policy.json

echo "✓ S3 bucket created: $S3_BUCKET"

echo "Step 2: Creating DynamoDB table for agent memory..."
aws dynamodb create-table \
  --table-name $DYNAMODB_TABLE \
  --attribute-definitions \
    AttributeName=session_id,AttributeType=S \
    AttributeName=timestamp,AttributeType=S \
  --key-schema \
    AttributeName=session_id,KeyType=HASH \
    AttributeName=timestamp,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --tags Key=Project,Value=MarketplaceAgents Key=Environment,Value=dev \
  --region $REGION 2>/dev/null || echo "Table already exists"

# Enable TTL
aws dynamodb update-time-to-live \
  --table-name $DYNAMODB_TABLE \
  --time-to-live-specification "Enabled=true, AttributeName=ttl" \
  --region $REGION 2>/dev/null || true

echo "✓ DynamoDB table created: $DYNAMODB_TABLE"

echo "Step 3: Creating IAM roles..."

# Bedrock Agent Role
cat > /tmp/agent-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "$ACCOUNT_ID"
        }
      }
    }
  ]
}
EOF

aws iam create-role \
  --role-name BedrockAgentRole-Marketplace \
  --assume-role-policy-document file:///tmp/agent-trust-policy.json \
  --description "Role for Bedrock Agents in Marketplace Portal" \
  2>/dev/null || echo "Role already exists"

# Attach policies
aws iam attach-role-policy \
  --role-name BedrockAgentRole-Marketplace \
  --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess

# Create inline policy for additional permissions
cat > /tmp/agent-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:$REGION:$ACCOUNT_ID:function:marketplace-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:$REGION:$ACCOUNT_ID:table/$DYNAMODB_TABLE"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::$S3_BUCKET",
        "arn:aws:s3:::$S3_BUCKET/*"
      ]
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name BedrockAgentRole-Marketplace \
  --policy-name AdditionalPermissions \
  --policy-document file:///tmp/agent-policy.json

echo "✓ IAM role created: BedrockAgentRole-Marketplace"

# Lambda Execution Role
cat > /tmp/lambda-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
  --role-name LambdaExecutionRole-MarketplaceAgents \
  --assume-role-policy-document file:///tmp/lambda-trust-policy.json \
  --description "Execution role for Marketplace Agent Lambda functions" \
  2>/dev/null || echo "Role already exists"

aws iam attach-role-policy \
  --role-name LambdaExecutionRole-MarketplaceAgents \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam attach-role-policy \
  --role-name LambdaExecutionRole-MarketplaceAgents \
  --policy-arn arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess

# Add marketplace permissions
cat > /tmp/lambda-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "aws-marketplace:*",
        "marketplace-catalog:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:*"
      ],
      "Resource": "arn:aws:dynamodb:$REGION:$ACCOUNT_ID:table/$DYNAMODB_TABLE"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:Retrieve"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name LambdaExecutionRole-MarketplaceAgents \
  --policy-name MarketplacePermissions \
  --policy-document file:///tmp/lambda-policy.json

echo "✓ IAM role created: LambdaExecutionRole-MarketplaceAgents"

echo "Step 4: Creating CloudWatch Log Groups..."
aws logs create-log-group \
  --log-group-name $LOG_GROUP \
  --region $REGION 2>/dev/null || echo "Log group already exists"

aws logs put-retention-policy \
  --log-group-name $LOG_GROUP \
  --retention-in-days 30 \
  --region $REGION

aws logs create-log-group \
  --log-group-name "${LOG_GROUP}/errors" \
  --region $REGION 2>/dev/null || true

echo "✓ CloudWatch log groups created"

echo "Step 5: Creating CloudWatch Dashboard..."
cat > /tmp/dashboard.json <<EOF
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["BedrockAgents/Marketplace", "AgentInvocations", {"stat": "Sum"}],
          [".", "ToolInvocations", {"stat": "Sum"}]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "$REGION",
        "title": "Agent Activity"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["BedrockAgents/Marketplace", "AgentDuration", {"stat": "Average"}],
          ["...", {"stat": "p99"}]
        ],
        "period": 300,
        "region": "$REGION",
        "title": "Response Time (ms)"
      }
    }
  ]
}
EOF

aws cloudwatch put-dashboard \
  --dashboard-name BedrockAgents-Marketplace \
  --dashboard-body file:///tmp/dashboard.json \
  --region $REGION

echo "✓ CloudWatch dashboard created"

echo ""
echo "========================================="
echo "Infrastructure setup complete!"
echo "========================================="
echo "Resources created:"
echo "  - S3 Bucket: $S3_BUCKET"
echo "  - DynamoDB Table: $DYNAMODB_TABLE"
echo "  - IAM Roles: BedrockAgentRole-Marketplace, LambdaExecutionRole-MarketplaceAgents"
echo "  - CloudWatch Log Group: $LOG_GROUP"
echo "  - CloudWatch Dashboard: BedrockAgents-Marketplace"
echo ""
echo "Next step: Run ./02-deploy-knowledge-base.sh"
echo "========================================="
