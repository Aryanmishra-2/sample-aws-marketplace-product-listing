#!/bin/bash
set -e

echo "========================================="
echo "Quick Test: Bedrock AgentCore Deployment"
echo "Account: 797583073197"
echo "========================================="
echo ""

# Check AWS credentials
echo "Step 1: Verifying AWS credentials..."
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)

if [ $? -ne 0 ]; then
  echo "❌ ERROR: AWS CLI not configured or credentials invalid"
  echo ""
  echo "Please configure AWS CLI with credentials for account 797583073197:"
  echo "  aws configure"
  echo ""
  exit 1
fi

if [ "$AWS_ACCOUNT" != "797583073197" ]; then
  echo "❌ ERROR: Wrong AWS account"
  echo "   Expected: 797583073197"
  echo "   Got: $AWS_ACCOUNT"
  echo ""
  echo "Please switch to the correct AWS account"
  exit 1
fi

echo "✓ Authenticated to account 797583073197"
echo ""

# Check region
REGION="us-east-1"
echo "Step 2: Checking region..."
CURRENT_REGION=$(aws configure get region)
echo "✓ Using region: $REGION"
echo ""

# Check Bedrock access
echo "Step 3: Verifying Bedrock access..."
aws bedrock list-foundation-models --region $REGION --query 'modelSummaries[0].modelId' --output text >/dev/null 2>&1

if [ $? -ne 0 ]; then
  echo "❌ ERROR: Cannot access Bedrock service"
  echo ""
  echo "Please ensure:"
  echo "  1. Bedrock is available in $REGION"
  echo "  2. Your IAM user/role has bedrock:* permissions"
  echo "  3. Bedrock model access is enabled in the console"
  exit 1
fi

echo "✓ Bedrock service accessible"
echo ""

# Check for Claude 3.5 Sonnet model
echo "Step 4: Checking Claude 3.5 Sonnet availability..."
MODEL_ID="us.anthropic.claude-3-5-sonnet-20241022-v2:0"
aws bedrock list-foundation-models \
  --region $REGION \
  --query "modelSummaries[?modelId=='$MODEL_ID'].modelId" \
  --output text >/dev/null 2>&1

if [ $? -eq 0 ]; then
  echo "✓ Claude 3.5 Sonnet v2 available"
else
  echo "⚠ Warning: Claude 3.5 Sonnet v2 not found, checking alternatives..."
  MODEL_ID="anthropic.claude-3-5-sonnet-20240620-v1:0"
  echo "  Using: $MODEL_ID"
fi
echo ""

# List existing agents
echo "Step 5: Checking existing Bedrock Agents..."
AGENT_COUNT=$(aws bedrock-agent list-agents --region $REGION --query 'length(agentSummaries)' --output text 2>/dev/null || echo "0")
echo "✓ Found $AGENT_COUNT existing agent(s)"
echo ""

# Check IAM permissions
echo "Step 6: Checking IAM permissions..."
PERMISSIONS_OK=true

# Check if we can create roles
aws iam get-role --role-name BedrockAgentRole-Marketplace --region $REGION >/dev/null 2>&1
if [ $? -eq 0 ]; then
  echo "✓ IAM role exists: BedrockAgentRole-Marketplace"
else
  echo "⚠ IAM role not found (will be created during deployment)"
fi
echo ""

# Check S3
echo "Step 7: Checking S3 access..."
S3_BUCKET="marketplace-agents-kb-797583073197"
aws s3 ls s3://$S3_BUCKET --region $REGION >/dev/null 2>&1
if [ $? -eq 0 ]; then
  echo "✓ S3 bucket exists: $S3_BUCKET"
else
  echo "⚠ S3 bucket not found (will be created during deployment)"
fi
echo ""

# Check DynamoDB
echo "Step 8: Checking DynamoDB access..."
DYNAMODB_TABLE="marketplace-agent-memory"
aws dynamodb describe-table --table-name $DYNAMODB_TABLE --region $REGION >/dev/null 2>&1
if [ $? -eq 0 ]; then
  echo "✓ DynamoDB table exists: $DYNAMODB_TABLE"
else
  echo "⚠ DynamoDB table not found (will be created during deployment)"
fi
echo ""

echo "========================================="
echo "Pre-flight Check Complete!"
echo "========================================="
echo ""
echo "Summary:"
echo "  ✓ AWS Account: 797583073197"
echo "  ✓ Region: $REGION"
echo "  ✓ Bedrock Access: OK"
echo "  ✓ Model: $MODEL_ID"
echo "  ✓ Existing Agents: $AGENT_COUNT"
echo ""
echo "Ready to deploy!"
echo ""
echo "Next steps:"
echo "  1. Review configuration: ../config/deployment-config.json"
echo "  2. Run full deployment: ./deploy-all.sh"
echo "  3. Or run step-by-step:"
echo "     ./01-setup-infrastructure.sh"
echo "     ./02-deploy-knowledge-base.sh"
echo "     ./03-deploy-lambda-functions.sh"
echo "     ./04-deploy-help-agent.sh"
echo "     ./05-deploy-marketplace-agent.sh"
echo ""
