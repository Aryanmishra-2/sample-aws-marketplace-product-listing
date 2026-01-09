#!/bin/bash
set -e

# =============================================================================
# AWS Marketplace Seller Portal - One-Click Deployment Script
# =============================================================================
# Deploys the complete application to your AWS account:
# 1. Backend agents to Bedrock AgentCore Runtime
# 2. Frontend to AWS ECS Fargate with ALB
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_NAME="ai-agent-marketplace"
DEFAULT_REGION="us-east-1"

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    command -v aws &> /dev/null || { log_error "AWS CLI not installed"; exit 1; }
    command -v docker &> /dev/null || { log_error "Docker not installed"; exit 1; }
    command -v node &> /dev/null || { log_error "Node.js not installed"; exit 1; }
    command -v python3 &> /dev/null || { log_error "Python 3 not installed"; exit 1; }
    
    if ! command -v agentcore &> /dev/null; then
        log_warning "AgentCore CLI not found. Installing..."
        pip install bedrock-agentcore-cli
    fi
    
    log_success "Prerequisites check completed"
}

get_aws_info() {
    log_info "Getting AWS account information..."
    
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")
    AWS_REGION=${AWS_DEFAULT_REGION:-$DEFAULT_REGION}
    
    if [ -z "$AWS_ACCOUNT_ID" ]; then
        log_error "Unable to get AWS account ID. Please configure AWS CLI credentials."
        exit 1
    fi
    
    log_success "AWS Account: $AWS_ACCOUNT_ID"
    log_success "AWS Region: $AWS_REGION"
    
    export AWS_ACCOUNT_ID AWS_REGION
}

deploy_backend() {
    log_info "Deploying backend agents to Bedrock AgentCore..."
    
    pip install -r requirements.txt -q
    
    # Check if existing config has a different account ID - if so, recreate it
    if [ -f ".bedrock_agentcore.yaml" ]; then
        EXISTING_ACCOUNT=$(grep "account:" .bedrock_agentcore.yaml | head -1 | grep -o "'[0-9]*'" | tr -d "'" || echo "")
        if [ -n "$EXISTING_ACCOUNT" ] && [ "$EXISTING_ACCOUNT" != "$AWS_ACCOUNT_ID" ]; then
            log_warning "Existing config is for account $EXISTING_ACCOUNT, recreating for $AWS_ACCOUNT_ID..."
            rm -rf .bedrock_agentcore.yaml .bedrock_agentcore/
        fi
    fi
    
    if [ ! -f ".bedrock_agentcore.yaml" ]; then
        log_info "Creating AgentCore configuration..."
        cat > .bedrock_agentcore.yaml << EOF
default_agent: marketplaceAgent
agents:
  marketplaceAgent:
    name: marketplaceAgent
    entrypoint: agentcore_app.py
    deployment_type: container
    platform: linux/arm64
    container_runtime: docker
    source_path: .
    aws:
      execution_role_auto_create: true
      account: '$AWS_ACCOUNT_ID'
      region: $AWS_REGION
      ecr_auto_create: true
      s3_auto_create: true
      network_configuration:
        network_mode: PUBLIC
      protocol_configuration:
        server_protocol: HTTP
      observability:
        enabled: true
    bedrock_agentcore:
      memory:
        type: short_term
        auto_create: true
EOF
    fi
    
    agentcore deploy --agent marketplaceAgent --auto-update-on-conflict
    log_success "Backend deployed successfully"
}

deploy_frontend() {
    log_info "Deploying frontend to ECS Fargate..."
    
    ECR_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${APP_NAME}"
    
    # ECR setup
    aws ecr describe-repositories --repository-names ${APP_NAME} --region ${AWS_REGION} 2>/dev/null || \
        aws ecr create-repository --repository-name ${APP_NAME} --region ${AWS_REGION}
    
    aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
    
    # Build and push (linux/amd64 for Fargate)
    log_info "Building Docker image for linux/amd64..."
    cd frontend
    docker buildx build --platform linux/amd64 -t ${APP_NAME}:latest --load .
    docker tag ${APP_NAME}:latest ${ECR_REPO}:latest
    docker push ${ECR_REPO}:latest
    cd ..
    
    # VPC and networking
    VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text --region ${AWS_REGION})
    SUBNETS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=${VPC_ID}" --query "Subnets[0:3].SubnetId" --output text --region ${AWS_REGION} | tr '\t' ' ')
    
    # Security group
    SG_ID=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=${APP_NAME}-sg" "Name=vpc-id,Values=${VPC_ID}" --query "SecurityGroups[0].GroupId" --output text --region ${AWS_REGION} 2>/dev/null)
    if [ "$SG_ID" == "None" ] || [ -z "$SG_ID" ]; then
        SG_ID=$(aws ec2 create-security-group --group-name ${APP_NAME}-sg --description "Security group for ${APP_NAME}" --vpc-id ${VPC_ID} --query "GroupId" --output text --region ${AWS_REGION})
        aws ec2 authorize-security-group-ingress --group-id ${SG_ID} --protocol tcp --port 80 --cidr 0.0.0.0/0 --region ${AWS_REGION}
        aws ec2 authorize-security-group-ingress --group-id ${SG_ID} --protocol tcp --port 3000 --cidr 0.0.0.0/0 --region ${AWS_REGION}
    fi
    
    # ECS cluster
    aws ecs describe-clusters --clusters ${APP_NAME} --region ${AWS_REGION} --query "clusters[?status=='ACTIVE'].clusterName" --output text | grep -q ${APP_NAME} || \
        aws ecs create-cluster --cluster-name ${APP_NAME} --region ${AWS_REGION}
    
    # IAM roles
    EXEC_ROLE_NAME="${APP_NAME}-task-execution-role"
    TASK_ROLE_NAME="${APP_NAME}-task-role"
    
    if ! aws iam get-role --role-name ${EXEC_ROLE_NAME} 2>/dev/null; then
        aws iam create-role --role-name ${EXEC_ROLE_NAME} --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
        aws iam attach-role-policy --role-name ${EXEC_ROLE_NAME} --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
        sleep 10
    fi
    
    if ! aws iam get-role --role-name ${TASK_ROLE_NAME} 2>/dev/null; then
        aws iam create-role --role-name ${TASK_ROLE_NAME} --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
        aws iam attach-role-policy --role-name ${TASK_ROLE_NAME} --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
        aws iam attach-role-policy --role-name ${TASK_ROLE_NAME} --policy-arn arn:aws:iam::aws:policy/AWSMarketplaceSellerFullAccess
        sleep 10
    fi
    
    # CloudWatch logs
    aws logs create-log-group --log-group-name "/ecs/${APP_NAME}" --region ${AWS_REGION} 2>/dev/null || true
    
    # Task definition
    cat > /tmp/task-def.json << EOF
{"family":"${APP_NAME}","networkMode":"awsvpc","requiresCompatibilities":["FARGATE"],"cpu":"1024","memory":"2048","executionRoleArn":"arn:aws:iam::${AWS_ACCOUNT_ID}:role/${EXEC_ROLE_NAME}","taskRoleArn":"arn:aws:iam::${AWS_ACCOUNT_ID}:role/${TASK_ROLE_NAME}","containerDefinitions":[{"name":"${APP_NAME}","image":"${ECR_REPO}:latest","essential":true,"portMappings":[{"containerPort":3000,"hostPort":3000,"protocol":"tcp"}],"environment":[{"name":"NODE_ENV","value":"production"},{"name":"PORT","value":"3000"},{"name":"HOSTNAME","value":"0.0.0.0"},{"name":"AWS_REGION","value":"${AWS_REGION}"}],"logConfiguration":{"logDriver":"awslogs","options":{"awslogs-group":"/ecs/${APP_NAME}","awslogs-region":"${AWS_REGION}","awslogs-stream-prefix":"ecs"}},"healthCheck":{"command":["CMD-SHELL","curl -f http://localhost:3000/ || exit 1"],"interval":30,"timeout":10,"retries":10,"startPeriod":300}}]}
EOF
    aws ecs register-task-definition --cli-input-json file:///tmp/task-def.json --region ${AWS_REGION} > /dev/null
    
    # ALB
    ALB_ARN=$(aws elbv2 describe-load-balancers --names ${APP_NAME}-alb --region ${AWS_REGION} --query "LoadBalancers[0].LoadBalancerArn" --output text 2>/dev/null || echo "None")
    if [ "$ALB_ARN" == "None" ] || [ -z "$ALB_ARN" ]; then
        ALB_ARN=$(aws elbv2 create-load-balancer --name ${APP_NAME}-alb --subnets ${SUBNETS} --security-groups ${SG_ID} --scheme internet-facing --type application --query "LoadBalancers[0].LoadBalancerArn" --output text --region ${AWS_REGION})
    fi
    ALB_DNS=$(aws elbv2 describe-load-balancers --load-balancer-arns ${ALB_ARN} --query "LoadBalancers[0].DNSName" --output text --region ${AWS_REGION})
    
    # Target group
    TG_ARN=$(aws elbv2 describe-target-groups --names ${APP_NAME}-tg --region ${AWS_REGION} --query "TargetGroups[0].TargetGroupArn" --output text 2>/dev/null || echo "None")
    if [ "$TG_ARN" == "None" ] || [ -z "$TG_ARN" ]; then
        TG_ARN=$(aws elbv2 create-target-group --name ${APP_NAME}-tg --protocol HTTP --port 3000 --vpc-id ${VPC_ID} --target-type ip --health-check-path "/" --health-check-interval-seconds 30 --unhealthy-threshold-count 10 --query "TargetGroups[0].TargetGroupArn" --output text --region ${AWS_REGION})
    fi
    
    # Listener
    LISTENER_ARN=$(aws elbv2 describe-listeners --load-balancer-arn ${ALB_ARN} --region ${AWS_REGION} --query "Listeners[0].ListenerArn" --output text 2>/dev/null || echo "None")
    if [ "$LISTENER_ARN" == "None" ] || [ -z "$LISTENER_ARN" ]; then
        aws elbv2 create-listener --load-balancer-arn ${ALB_ARN} --protocol HTTP --port 80 --default-actions Type=forward,TargetGroupArn=${TG_ARN} --region ${AWS_REGION} > /dev/null
    fi
    
    # ECS Service
    SUBNETS_COMMA=$(echo $SUBNETS | tr ' ' ',')
    SERVICE_EXISTS=$(aws ecs describe-services --cluster ${APP_NAME} --services ${APP_NAME} --region ${AWS_REGION} --query "services[?status=='ACTIVE'].serviceName" --output text 2>/dev/null)
    if [ -n "$SERVICE_EXISTS" ]; then
        aws ecs update-service --cluster ${APP_NAME} --service ${APP_NAME} --task-definition ${APP_NAME} --force-new-deployment --region ${AWS_REGION} > /dev/null
    else
        aws ecs create-service --cluster ${APP_NAME} --service-name ${APP_NAME} --task-definition ${APP_NAME} --desired-count 1 --launch-type FARGATE --network-configuration "awsvpcConfiguration={subnets=[${SUBNETS_COMMA}],securityGroups=[${SG_ID}],assignPublicIp=ENABLED}" --load-balancers "targetGroupArn=${TG_ARN},containerName=${APP_NAME},containerPort=3000" --health-check-grace-period-seconds 600 --region ${AWS_REGION} > /dev/null
    fi
    
    log_success "Frontend deployed to: http://${ALB_DNS}"
    echo ""
    echo "========================================="
    echo "🎉 Deployment Complete!"
    echo "========================================="
    echo ""
    echo "🌐 Application URL: http://${ALB_DNS}"
    echo ""
    echo "Note: It may take 5-10 minutes for the service to become healthy."
    echo ""
    echo "Monitor with:"
    echo "  aws ecs describe-services --cluster ${APP_NAME} --services ${APP_NAME} --region ${AWS_REGION}"
}

main() {
    echo ""
    echo "========================================="
    echo "🚀 AWS Marketplace Seller Portal"
    echo "========================================="
    echo ""
    
    SKIP_BACKEND=false
    SKIP_FRONTEND=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-backend) SKIP_BACKEND=true; shift ;;
            --skip-frontend) SKIP_FRONTEND=true; shift ;;
            --help)
                echo "Usage: $0 [--skip-backend] [--skip-frontend]"
                exit 0 ;;
            *) log_error "Unknown option: $1"; exit 1 ;;
        esac
    done
    
    check_prerequisites
    get_aws_info
    
    [ "$SKIP_BACKEND" = false ] && deploy_backend || log_warning "Skipping backend"
    [ "$SKIP_FRONTEND" = false ] && deploy_frontend || log_warning "Skipping frontend"
}

main "$@"
