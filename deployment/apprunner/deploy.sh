#!/bin/bash
set -e

# Configuration
APP_NAME="ai-agent-marketplace"
REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${APP_NAME}"

# AgentCore Agent IDs (update these with your deployed agent IDs)
AGENTCORE_AGENT_ID="${AGENTCORE_AGENT_ID:-agent-A747Dl9mYv}"
AGENTCORE_MARKETPLACE_AGENT_ID="${AGENTCORE_MARKETPLACE_AGENT_ID:-marketplaceAgent-5UlKW791jd}"
AGENTCORE_AGENT_ALIAS_ID="${AGENTCORE_AGENT_ALIAS_ID:-TSTALIASID}"

echo "=== AI Agent Marketplace - App Runner Deployment ==="
echo "Region: ${REGION}"
echo "Account: ${ACCOUNT_ID}"

# Step 1: Create ECR repository if it doesn't exist
echo ""
echo "Step 1: Setting up ECR repository..."
aws ecr describe-repositories --repository-names ${APP_NAME} --region ${REGION} 2>/dev/null || \
  aws ecr create-repository --repository-name ${APP_NAME} --region ${REGION}

# Step 2: Login to ECR
echo ""
echo "Step 2: Logging into ECR..."
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

# Step 3: Build Docker image
echo ""
echo "Step 3: Building Docker image..."
cd "$(dirname "$0")/../../frontend"
docker build -t ${APP_NAME}:latest .

# Step 4: Tag and push to ECR
echo ""
echo "Step 4: Pushing to ECR..."
docker tag ${APP_NAME}:latest ${ECR_REPO}:latest
docker push ${ECR_REPO}:latest

# Step 5: Create IAM role for App Runner (if not exists)
echo ""
echo "Step 5: Setting up IAM role..."
ROLE_NAME="AppRunnerECRAccessRole"

# Check if role exists
if ! aws iam get-role --role-name ${ROLE_NAME} 2>/dev/null; then
  echo "Creating IAM role..."
  aws iam create-role \
    --role-name ${ROLE_NAME} \
    --assume-role-policy-document '{
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "build.apprunner.amazonaws.com"},
        "Action": "sts:AssumeRole"
      }]
    }'
  
  aws iam attach-role-policy \
    --role-name ${ROLE_NAME} \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess
  
  echo "Waiting for role to propagate..."
  sleep 10
fi

# Step 6: Create instance role for App Runner (to call AWS services)
INSTANCE_ROLE_NAME="AppRunnerInstanceRole"

if ! aws iam get-role --role-name ${INSTANCE_ROLE_NAME} 2>/dev/null; then
  echo "Creating instance IAM role..."
  aws iam create-role \
    --role-name ${INSTANCE_ROLE_NAME} \
    --assume-role-policy-document '{
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "tasks.apprunner.amazonaws.com"},
        "Action": "sts:AssumeRole"
      }]
    }'
  
  # Attach policies for Bedrock, Marketplace, CloudFormation, etc.
  aws iam attach-role-policy \
    --role-name ${INSTANCE_ROLE_NAME} \
    --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
  
  aws iam attach-role-policy \
    --role-name ${INSTANCE_ROLE_NAME} \
    --policy-arn arn:aws:iam::aws:policy/AWSMarketplaceSellerFullAccess
  
  aws iam attach-role-policy \
    --role-name ${INSTANCE_ROLE_NAME} \
    --policy-arn arn:aws:iam::aws:policy/AWSCloudFormationFullAccess
  
  aws iam attach-role-policy \
    --role-name ${INSTANCE_ROLE_NAME} \
    --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
  
  echo "Waiting for role to propagate..."
  sleep 10
fi

ACCESS_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"
INSTANCE_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${INSTANCE_ROLE_NAME}"

# Step 7: Create or update App Runner service
echo ""
echo "Step 6: Deploying to App Runner..."

SERVICE_ARN=$(aws apprunner list-services --region ${REGION} \
  --query "ServiceSummaryList[?ServiceName=='${APP_NAME}'].ServiceArn" \
  --output text 2>/dev/null)

if [ -z "$SERVICE_ARN" ] || [ "$SERVICE_ARN" == "None" ]; then
  echo "Creating new App Runner service..."
  aws apprunner create-service \
    --service-name ${APP_NAME} \
    --region ${REGION} \
    --source-configuration "{
      \"AuthenticationConfiguration\": {
        \"AccessRoleArn\": \"${ACCESS_ROLE_ARN}\"
      },
      \"ImageRepository\": {
        \"ImageIdentifier\": \"${ECR_REPO}:latest\",
        \"ImageRepositoryType\": \"ECR\",
        \"ImageConfiguration\": {
          \"Port\": \"3000\",
          \"RuntimeEnvironmentVariables\": {
            \"NODE_ENV\": \"production\",
            \"AGENTCORE_AGENT_ID\": \"${AGENTCORE_AGENT_ID}\",
            \"AGENTCORE_MARKETPLACE_AGENT_ID\": \"${AGENTCORE_MARKETPLACE_AGENT_ID}\",
            \"AGENTCORE_AGENT_ALIAS_ID\": \"${AGENTCORE_AGENT_ALIAS_ID}\",
            \"AWS_REGION\": \"${REGION}\"
          }
        }
      },
      \"AutoDeploymentsEnabled\": true
    }" \
    --instance-configuration "{
      \"Cpu\": \"1024\",
      \"Memory\": \"2048\",
      \"InstanceRoleArn\": \"${INSTANCE_ROLE_ARN}\"
    }" \
    --health-check-configuration "{
      \"Protocol\": \"HTTP\",
      \"Path\": \"/\",
      \"Interval\": 10,
      \"Timeout\": 5,
      \"HealthyThreshold\": 1,
      \"UnhealthyThreshold\": 5
    }"
else
  echo "Updating existing App Runner service..."
  aws apprunner update-service \
    --service-arn ${SERVICE_ARN} \
    --region ${REGION} \
    --source-configuration "{
      \"AuthenticationConfiguration\": {
        \"AccessRoleArn\": \"${ACCESS_ROLE_ARN}\"
      },
      \"ImageRepository\": {
        \"ImageIdentifier\": \"${ECR_REPO}:latest\",
        \"ImageRepositoryType\": \"ECR\",
        \"ImageConfiguration\": {
          \"Port\": \"3000\",
          \"RuntimeEnvironmentVariables\": {
            \"NODE_ENV\": \"production\",
            \"AGENTCORE_AGENT_ID\": \"${AGENTCORE_AGENT_ID}\",
            \"AGENTCORE_MARKETPLACE_AGENT_ID\": \"${AGENTCORE_MARKETPLACE_AGENT_ID}\",
            \"AGENTCORE_AGENT_ALIAS_ID\": \"${AGENTCORE_AGENT_ALIAS_ID}\",
            \"AWS_REGION\": \"${REGION}\"
          }
        }
      },
      \"AutoDeploymentsEnabled\": true
    }"
fi

echo ""
echo "=== Deployment initiated! ==="
echo ""
echo "Check status with:"
echo "  aws apprunner list-services --region ${REGION}"
echo ""
echo "Once running, your app will be available at the App Runner URL."
