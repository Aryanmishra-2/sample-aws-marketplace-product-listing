#!/bin/bash
set -e

# Configuration
APP_NAME="ai-agent-marketplace"
REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${APP_NAME}"

echo "=== AI Agent Marketplace - ECS Fargate Deployment ==="
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

# Step 3: Build and push Docker image
echo ""
echo "Step 3: Building and pushing Docker image..."
cd "$(dirname "$0")/../../frontend"
docker build -t ${APP_NAME}:latest .
docker tag ${APP_NAME}:latest ${ECR_REPO}:latest
docker push ${ECR_REPO}:latest
cd -

# Step 4: Get default VPC and subnets
echo ""
echo "Step 4: Getting VPC configuration..."
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text --region ${REGION})
if [ "$VPC_ID" == "None" ] || [ -z "$VPC_ID" ]; then
  echo "No default VPC found. Creating one..."
  VPC_ID=$(aws ec2 create-default-vpc --query "Vpc.VpcId" --output text --region ${REGION} 2>/dev/null || \
    aws ec2 describe-vpcs --query "Vpcs[0].VpcId" --output text --region ${REGION})
fi
echo "Using VPC: ${VPC_ID}"

SUBNETS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=${VPC_ID}" --query "Subnets[*].SubnetId" --output text --region ${REGION} | tr '\t' ',')
echo "Using Subnets: ${SUBNETS}"

# Step 5: Create security group
echo ""
echo "Step 5: Setting up security group..."
SG_NAME="${APP_NAME}-sg"
SG_ID=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=${SG_NAME}" "Name=vpc-id,Values=${VPC_ID}" --query "SecurityGroups[0].GroupId" --output text --region ${REGION} 2>/dev/null)

if [ "$SG_ID" == "None" ] || [ -z "$SG_ID" ]; then
  echo "Creating security group..."
  SG_ID=$(aws ec2 create-security-group \
    --group-name ${SG_NAME} \
    --description "Security group for ${APP_NAME}" \
    --vpc-id ${VPC_ID} \
    --query "GroupId" \
    --output text \
    --region ${REGION})
  
  # Allow inbound HTTP traffic
  aws ec2 authorize-security-group-ingress \
    --group-id ${SG_ID} \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0 \
    --region ${REGION}
  
  aws ec2 authorize-security-group-ingress \
    --group-id ${SG_ID} \
    --protocol tcp \
    --port 3000 \
    --cidr 0.0.0.0/0 \
    --region ${REGION}
fi
echo "Using Security Group: ${SG_ID}"

# Step 6: Create ECS cluster
echo ""
echo "Step 6: Creating ECS cluster..."
aws ecs describe-clusters --clusters ${APP_NAME} --region ${REGION} --query "clusters[?status=='ACTIVE'].clusterName" --output text | grep -q ${APP_NAME} || \
  aws ecs create-cluster --cluster-name ${APP_NAME} --region ${REGION}

# Step 7: Create IAM roles
echo ""
echo "Step 7: Setting up IAM roles..."

# Task execution role
EXEC_ROLE_NAME="${APP_NAME}-task-execution-role"
if ! aws iam get-role --role-name ${EXEC_ROLE_NAME} 2>/dev/null; then
  echo "Creating task execution role..."
  aws iam create-role \
    --role-name ${EXEC_ROLE_NAME} \
    --assume-role-policy-document '{
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "ecs-tasks.amazonaws.com"},
        "Action": "sts:AssumeRole"
      }]
    }'
  
  aws iam attach-role-policy \
    --role-name ${EXEC_ROLE_NAME} \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
  
  sleep 10
fi
EXEC_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${EXEC_ROLE_NAME}"

# Task role (for AWS service access)
TASK_ROLE_NAME="${APP_NAME}-task-role"
if ! aws iam get-role --role-name ${TASK_ROLE_NAME} 2>/dev/null; then
  echo "Creating task role..."
  aws iam create-role \
    --role-name ${TASK_ROLE_NAME} \
    --assume-role-policy-document '{
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "ecs-tasks.amazonaws.com"},
        "Action": "sts:AssumeRole"
      }]
    }'
  
  aws iam attach-role-policy \
    --role-name ${TASK_ROLE_NAME} \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
  
  # Scoped permissions instead of FullAccess managed policies
  aws iam put-role-policy --role-name ${TASK_ROLE_NAME} --policy-name ScopedBedrockAccess --policy-document '{
    "Version":"2012-10-17",
    "Statement":[
      {
        "Effect":"Allow",
        "Action":[
          "bedrock:InvokeModel",
          "bedrock:InvokeAgent",
          "bedrock:Retrieve",
          "bedrock:RetrieveAndGenerate"
        ],
        "Resource":"*"
      },
      {
        "Effect":"Allow",
        "Action":[
          "marketplace-catalog:DescribeEntity",
          "marketplace-catalog:ListEntities",
          "marketplace-catalog:StartChangeSet",
          "marketplace-catalog:DescribeChangeSet",
          "marketplace-catalog:ListChangeSets",
          "aws-marketplace:GetEntitlements",
          "aws-marketplace:MeterUsage",
          "aws-marketplace:BatchMeterUsage",
          "aws-marketplace:ResolveCustomer"
        ],
        "Resource":"*"
      },
      {
        "Effect":"Allow",
        "Action":["sts:GetCallerIdentity"],
        "Resource":"*"
      }
    ]
  }'
  
  sleep 10
fi
TASK_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${TASK_ROLE_NAME}"

# Step 8: Create CloudWatch log group
echo ""
echo "Step 8: Creating CloudWatch log group..."
aws logs create-log-group --log-group-name "/ecs/${APP_NAME}" --region ${REGION} 2>/dev/null || true

# Step 9: Register task definition
echo ""
echo "Step 9: Registering task definition..."
TASK_DEF=$(cat <<EOF
{
  "family": "${APP_NAME}",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "${EXEC_ROLE_ARN}",
  "taskRoleArn": "${TASK_ROLE_ARN}",
  "containerDefinitions": [
    {
      "name": "${APP_NAME}",
      "image": "${ECR_REPO}:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 3000,
          "hostPort": 3000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "NODE_ENV", "value": "production"},
        {"name": "PORT", "value": "3000"},
        {"name": "HOSTNAME", "value": "0.0.0.0"},
        {"name": "AWS_REGION", "value": "${REGION}"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/${APP_NAME}",
          "awslogs-region": "${REGION}",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "node -e \"require('http').get('http://localhost:3000/', (r) => process.exit(r.statusCode === 200 ? 0 : 1))\" || exit 1"],
        "interval": 30,
        "timeout": 10,
        "retries": 10,
        "startPeriod": 300
      }
    }
  ]
}
EOF
)

echo "$TASK_DEF" > /tmp/task-definition.json
aws ecs register-task-definition --cli-input-json file:///tmp/task-definition.json --region ${REGION}

# Step 10: Create Application Load Balancer
echo ""
echo "Step 10: Creating Application Load Balancer..."
ALB_NAME="${APP_NAME}-alb"
SUBNET_ARRAY=(${SUBNETS//,/ })

ALB_ARN=$(aws elbv2 describe-load-balancers --names ${ALB_NAME} --region ${REGION} --query "LoadBalancers[0].LoadBalancerArn" --output text 2>/dev/null || echo "None")

if [ "$ALB_ARN" == "None" ] || [ -z "$ALB_ARN" ]; then
  echo "Creating ALB..."
  ALB_ARN=$(aws elbv2 create-load-balancer \
    --name ${ALB_NAME} \
    --subnets ${SUBNET_ARRAY[@]} \
    --security-groups ${SG_ID} \
    --scheme internet-facing \
    --type application \
    --query "LoadBalancers[0].LoadBalancerArn" \
    --output text \
    --region ${REGION})
fi
echo "ALB ARN: ${ALB_ARN}"

ALB_DNS=$(aws elbv2 describe-load-balancers --load-balancer-arns ${ALB_ARN} --query "LoadBalancers[0].DNSName" --output text --region ${REGION})
echo "ALB DNS: ${ALB_DNS}"

# Step 11: Create target group
echo ""
echo "Step 11: Creating target group..."
TG_NAME="${APP_NAME}-tg"
TG_ARN=$(aws elbv2 describe-target-groups --names ${TG_NAME} --region ${REGION} --query "TargetGroups[0].TargetGroupArn" --output text 2>/dev/null || echo "None")

if [ "$TG_ARN" == "None" ] || [ -z "$TG_ARN" ]; then
  echo "Creating target group..."
  TG_ARN=$(aws elbv2 create-target-group \
    --name ${TG_NAME} \
    --protocol HTTP \
    --port 3000 \
    --vpc-id ${VPC_ID} \
    --target-type ip \
    --health-check-protocol HTTP \
    --health-check-path "/" \
    --health-check-interval-seconds 30 \
    --health-check-timeout-seconds 10 \
    --healthy-threshold-count 2 \
    --unhealthy-threshold-count 10 \
    --query "TargetGroups[0].TargetGroupArn" \
    --output text \
    --region ${REGION})
fi
echo "Target Group ARN: ${TG_ARN}"

# Step 12: Create listener
echo ""
echo "Step 12: Creating ALB listener..."
LISTENER_ARN=$(aws elbv2 describe-listeners --load-balancer-arn ${ALB_ARN} --region ${REGION} --query "Listeners[0].ListenerArn" --output text 2>/dev/null || echo "None")

if [ "$LISTENER_ARN" == "None" ] || [ -z "$LISTENER_ARN" ]; then
  echo "Creating listener..."
  aws elbv2 create-listener \
    --load-balancer-arn ${ALB_ARN} \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=${TG_ARN} \
    --region ${REGION}
fi

# Step 13: Create or update ECS service
echo ""
echo "Step 13: Creating ECS Fargate service..."
SERVICE_EXISTS=$(aws ecs describe-services --cluster ${APP_NAME} --services ${APP_NAME} --region ${REGION} --query "services[?status=='ACTIVE'].serviceName" --output text 2>/dev/null)

if [ -n "$SERVICE_EXISTS" ]; then
  echo "Updating existing service..."
  aws ecs update-service \
    --cluster ${APP_NAME} \
    --service ${APP_NAME} \
    --task-definition ${APP_NAME} \
    --force-new-deployment \
    --region ${REGION}
else
  echo "Creating new service..."
  aws ecs create-service \
    --cluster ${APP_NAME} \
    --service-name ${APP_NAME} \
    --task-definition ${APP_NAME} \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[${SUBNETS}],securityGroups=[${SG_ID}],assignPublicIp=ENABLED}" \
    --load-balancers "targetGroupArn=${TG_ARN},containerName=${APP_NAME},containerPort=3000" \
    --health-check-grace-period-seconds 600 \
    --region ${REGION}
fi

echo ""
echo "=== Deployment Complete! ==="
echo ""
echo "Your application will be available at:"
echo "  http://${ALB_DNS}"
echo ""
echo "Note: It may take 5-10 minutes for the service to become healthy."
echo ""
echo "Monitor deployment with:"
echo "  aws ecs describe-services --cluster ${APP_NAME} --services ${APP_NAME} --region ${REGION}"
echo ""
echo "View logs with:"
echo "  aws logs tail /ecs/${APP_NAME} --follow --region ${REGION}"
