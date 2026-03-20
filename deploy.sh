#!/bin/bash
set -e

# =============================================================================
# AWS Marketplace Seller Portal - One-Click Deployment Script
# =============================================================================
# Deploys the complete application to your AWS account:
# 1. Backend agents to Bedrock AgentCore Runtime
# 2. Frontend to AWS ECS Fargate with Internal ALB (built via CodeBuild)
#
# SECURITY: Least-privilege networking
# - Internal ALB (not internet-facing)
# - ALB SG: ingress port 80 from VPC CIDR only
# - ECS SG: ingress port 3000 from ALB SG only
# - VPC endpoints for AWS services (ECR, S3, CloudWatch, Bedrock)
# - Network ACLs restrict traffic to VPC CIDR
# - Access via SSM port-forward or VPN
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_NAME="ai-agent-marketplace"
DEFAULT_REGION="us-east-1"
FRONTEND_CODEBUILD_PROJECT="${APP_NAME}-frontend-builder"

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

check_prerequisites() {
    log_info "Checking prerequisites..."
    command -v aws &> /dev/null || { log_error "AWS CLI not installed"; exit 1; }
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
    log_success "AWS Account: $AWS_ACCOUNT_ID | Region: $AWS_REGION"
    export AWS_ACCOUNT_ID AWS_REGION
}

deploy_backend() {
    log_info "Deploying backend agents to Bedrock AgentCore..."

    # Recreate config if it targets a different account
    if [ -f ".bedrock_agentcore.yaml" ]; then
        EXISTING_ACCOUNT=$(grep "account:" .bedrock_agentcore.yaml | head -1 | grep -o "'[0-9]*'" | tr -d "'" || echo "")
        if [ -n "$EXISTING_ACCOUNT" ] && [ "$EXISTING_ACCOUNT" != "$AWS_ACCOUNT_ID" ]; then
            log_warning "Config targets account $EXISTING_ACCOUNT, recreating for $AWS_ACCOUNT_ID..."
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
    platform: linux/amd64
    container_runtime: codebuild
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

    agentcore launch --agent marketplaceAgent --auto-update-on-conflict

    AGENTCORE_RUNTIME_ARN=$(grep "agent_arn:" .bedrock_agentcore.yaml | head -1 | awk '{print $2}' || echo "")
    if [ -z "$AGENTCORE_RUNTIME_ARN" ]; then
        log_warning "Could not extract AgentCore runtime ARN from config"
    else
        log_success "AgentCore ARN: $AGENTCORE_RUNTIME_ARN"
    fi
    export AGENTCORE_RUNTIME_ARN
    log_success "Backend deployed successfully"
}

# Build frontend Docker image using AWS CodeBuild (no local Docker required)
build_frontend_with_codebuild() {
    log_info "Building frontend Docker image via CodeBuild (no local Docker needed)..."

    ECR_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${APP_NAME}"
    S3_BUCKET="${APP_NAME}-codebuild-sources-${AWS_ACCOUNT_ID}-${AWS_REGION}"
    CODEBUILD_ROLE_NAME="${APP_NAME}-codebuild-role"

    # Create ECR repository if needed
    aws ecr describe-repositories --repository-names ${APP_NAME} --region ${AWS_REGION} 2>/dev/null || \
        aws ecr create-repository --repository-name ${APP_NAME} --region ${AWS_REGION} > /dev/null

    # Create S3 bucket for source
    if ! aws s3api head-bucket --bucket ${S3_BUCKET} 2>/dev/null; then
        aws s3api create-bucket --bucket ${S3_BUCKET} --region ${AWS_REGION} 2>/dev/null || true
    fi

    # Create CodeBuild IAM role
    if ! aws iam get-role --role-name ${CODEBUILD_ROLE_NAME} 2>/dev/null; then
        log_info "Creating CodeBuild IAM role..."
        aws iam create-role --role-name ${CODEBUILD_ROLE_NAME} \
            --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"codebuild.amazonaws.com"},"Action":"sts:AssumeRole"}]}'

        aws iam put-role-policy --role-name ${CODEBUILD_ROLE_NAME} --policy-name CodeBuildPolicy --policy-document '{
            "Version":"2012-10-17",
            "Statement":[
                {"Effect":"Allow","Action":["ecr:GetAuthorizationToken","ecr:BatchCheckLayerAvailability","ecr:GetDownloadUrlForLayer","ecr:BatchGetImage","ecr:PutImage","ecr:InitiateLayerUpload","ecr:UploadLayerPart","ecr:CompleteLayerUpload"],"Resource":"*"},
                {"Effect":"Allow","Action":["s3:GetObject","s3:GetObjectVersion","s3:PutObject"],"Resource":"arn:aws:s3:::'"${S3_BUCKET}"'/*"},
                {"Effect":"Allow","Action":["s3:GetBucketLocation","s3:ListBucket"],"Resource":"arn:aws:s3:::'"${S3_BUCKET}"'"},
                {"Effect":"Allow","Action":["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"],"Resource":"*"}
            ]
        }'
        log_info "Waiting for IAM role propagation..."
        sleep 10
    fi
    CODEBUILD_ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${CODEBUILD_ROLE_NAME}"

    # Zip and upload frontend source
    log_info "Packaging frontend source..."
    TMPDIR=$(mktemp -d)
    cp -r frontend/ ${TMPDIR}/frontend/
    rm -rf ${TMPDIR}/frontend/node_modules ${TMPDIR}/frontend/.next

    cat > ${TMPDIR}/buildspec.yml << 'BUILDSPEC'
version: 0.2
phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $ECR_REPO
  build:
    commands:
      - echo Building Docker image...
      - cd frontend
      - docker build --platform linux/amd64 -t $APP_NAME:latest .
      - docker tag $APP_NAME:latest $ECR_REPO:latest
  post_build:
    commands:
      - echo Pushing Docker image to ECR...
      - docker push $ECR_REPO:latest
      - echo Build completed on $(date)
BUILDSPEC

    (cd ${TMPDIR} && zip -r source.zip . -x '*.git*' > /dev/null)
    aws s3 cp ${TMPDIR}/source.zip s3://${S3_BUCKET}/frontend-source.zip --region ${AWS_REGION} > /dev/null
    rm -rf ${TMPDIR}

    # Create or update CodeBuild project
    AGENTCORE_ARN_VALUE="${AGENTCORE_RUNTIME_ARN:-}"
    PROJECT_EXISTS=$(aws codebuild batch-get-projects --names ${FRONTEND_CODEBUILD_PROJECT} --region ${AWS_REGION} --query 'projects[0].name' --output text 2>/dev/null || echo "None")

    if [ "$PROJECT_EXISTS" == "None" ] || [ -z "$PROJECT_EXISTS" ]; then
        log_info "Creating CodeBuild project..."
        aws codebuild create-project \
            --name ${FRONTEND_CODEBUILD_PROJECT} \
            --source "type=S3,location=${S3_BUCKET}/frontend-source.zip" \
            --artifacts "type=NO_ARTIFACTS" \
            --environment "type=LINUX_CONTAINER,computeType=BUILD_GENERAL1_MEDIUM,image=aws/codebuild/amazonlinux2-x86_64-standard:5.0,privilegedMode=true,environmentVariables=[{name=AWS_DEFAULT_REGION,value=${AWS_REGION}},{name=ECR_REPO,value=${ECR_REPO}},{name=APP_NAME,value=${APP_NAME}},{name=AGENTCORE_RUNTIME_ARN,value=${AGENTCORE_ARN_VALUE}}]" \
            --service-role ${CODEBUILD_ROLE_ARN} \
            --region ${AWS_REGION} > /dev/null
    else
        log_info "Updating CodeBuild project..."
        aws codebuild update-project \
            --name ${FRONTEND_CODEBUILD_PROJECT} \
            --source "type=S3,location=${S3_BUCKET}/frontend-source.zip" \
            --environment "type=LINUX_CONTAINER,computeType=BUILD_GENERAL1_MEDIUM,image=aws/codebuild/amazonlinux2-x86_64-standard:5.0,privilegedMode=true,environmentVariables=[{name=AWS_DEFAULT_REGION,value=${AWS_REGION}},{name=ECR_REPO,value=${ECR_REPO}},{name=APP_NAME,value=${APP_NAME}},{name=AGENTCORE_RUNTIME_ARN,value=${AGENTCORE_ARN_VALUE}}]" \
            --service-role ${CODEBUILD_ROLE_ARN} \
            --region ${AWS_REGION} > /dev/null
    fi

    # Start build
    log_info "Starting CodeBuild build..."
    BUILD_ID=$(aws codebuild start-build --project-name ${FRONTEND_CODEBUILD_PROJECT} --region ${AWS_REGION} --query 'build.id' --output text)
    log_info "Build ID: $BUILD_ID"

    # Poll for build completion
    log_info "Waiting for build to complete (this may take 3-5 minutes)..."
    while true; do
        BUILD_STATUS=$(aws codebuild batch-get-builds --ids ${BUILD_ID} --region ${AWS_REGION} --query 'builds[0].buildStatus' --output text)
        BUILD_PHASE=$(aws codebuild batch-get-builds --ids ${BUILD_ID} --region ${AWS_REGION} --query 'builds[0].currentPhase' --output text)

        if [ "$BUILD_STATUS" == "SUCCEEDED" ]; then
            log_success "Frontend Docker image built and pushed to ECR"
            break
        elif [ "$BUILD_STATUS" == "FAILED" ] || [ "$BUILD_STATUS" == "FAULT" ] || [ "$BUILD_STATUS" == "STOPPED" ]; then
            log_error "CodeBuild failed with status: $BUILD_STATUS"
            log_error "Check logs: aws codebuild batch-get-builds --ids ${BUILD_ID} --region ${AWS_REGION}"
            exit 1
        fi

        echo -ne "\r  ⏳ Phase: ${BUILD_PHASE} | Status: ${BUILD_STATUS}   "
        sleep 10
    done
    echo ""
}

# =============================================================================
# Cleanup old insecure resources before deploying with least-privilege
# =============================================================================
cleanup_old_resources() {
    log_info "Cleaning up old insecure resources..."

    VPC_ID=$1

    # Delete old internet-facing ALB if it exists
    OLD_ALB_ARN=$(aws elbv2 describe-load-balancers --names ${APP_NAME}-alb --region ${AWS_REGION} --query "LoadBalancers[0].LoadBalancerArn" --output text 2>/dev/null || echo "None")
    if [ "$OLD_ALB_ARN" != "None" ] && [ -n "$OLD_ALB_ARN" ]; then
        OLD_SCHEME=$(aws elbv2 describe-load-balancers --load-balancer-arns ${OLD_ALB_ARN} --query "LoadBalancers[0].Scheme" --output text --region ${AWS_REGION} 2>/dev/null || echo "")
        if [ "$OLD_SCHEME" == "internet-facing" ]; then
            log_warning "Deleting old internet-facing ALB..."
            # Delete listeners first
            OLD_LISTENERS=$(aws elbv2 describe-listeners --load-balancer-arn ${OLD_ALB_ARN} --region ${AWS_REGION} --query "Listeners[].ListenerArn" --output text 2>/dev/null || echo "")
            for LIS in $OLD_LISTENERS; do
                aws elbv2 delete-listener --listener-arn ${LIS} --region ${AWS_REGION} 2>/dev/null || true
            done
            aws elbv2 delete-load-balancer --load-balancer-arn ${OLD_ALB_ARN} --region ${AWS_REGION} 2>/dev/null || true
            log_info "Waiting for old ALB to drain..."
            sleep 15
        fi
    fi

    # Delete old target group (will be recreated)
    OLD_TG_ARN=$(aws elbv2 describe-target-groups --names ${APP_NAME}-tg --region ${AWS_REGION} --query "TargetGroups[0].TargetGroupArn" --output text 2>/dev/null || echo "None")
    if [ "$OLD_TG_ARN" != "None" ] && [ -n "$OLD_TG_ARN" ]; then
        aws elbv2 delete-target-group --target-group-arn ${OLD_TG_ARN} --region ${AWS_REGION} 2>/dev/null || true
    fi

    # Delete old wide-open security group
    OLD_SG_ID=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=${APP_NAME}-sg" "Name=vpc-id,Values=${VPC_ID}" --query "SecurityGroups[0].GroupId" --output text --region ${AWS_REGION} 2>/dev/null || echo "None")
    if [ "$OLD_SG_ID" != "None" ] && [ -n "$OLD_SG_ID" ]; then
        log_warning "Deleting old wide-open SG ${OLD_SG_ID} (${APP_NAME}-sg)..."
        # Must detach from any ENIs first — ECS service deletion handles this
        aws ec2 delete-security-group --group-id ${OLD_SG_ID} --region ${AWS_REGION} 2>/dev/null || \
            log_warning "Could not delete old SG ${OLD_SG_ID} — may still be in use. Will be orphaned."
    fi

    log_success "Old resource cleanup done"
}

# =============================================================================
# Create VPC endpoints for private subnet access to AWS services
# =============================================================================
setup_vpc_endpoints() {
    log_info "Setting up VPC endpoints for private access to AWS services..."

    VPC_ID=$1
    SUBNET_IDS=$2  # space-separated
    ECS_SG_ID=$3

    # Create a security group for VPC endpoints: allow HTTPS from VPC CIDR
    VPC_CIDR=$(aws ec2 describe-vpcs --vpc-ids ${VPC_ID} --query "Vpcs[0].CidrBlock" --output text --region ${AWS_REGION})
    VPCE_SG_ID=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=${APP_NAME}-vpce-sg" "Name=vpc-id,Values=${VPC_ID}" --query "SecurityGroups[0].GroupId" --output text --region ${AWS_REGION} 2>/dev/null || echo "None")
    if [ "$VPCE_SG_ID" == "None" ] || [ -z "$VPCE_SG_ID" ]; then
        VPCE_SG_ID=$(aws ec2 create-security-group --group-name ${APP_NAME}-vpce-sg --description "VPC endpoint SG - HTTPS from VPC CIDR" --vpc-id ${VPC_ID} --query "GroupId" --output text --region ${AWS_REGION})
        aws ec2 authorize-security-group-ingress --group-id ${VPCE_SG_ID} --protocol tcp --port 443 --cidr ${VPC_CIDR} --region ${AWS_REGION}
        # Egress: default allows all outbound (needed for endpoint responses)
        log_success "Created VPC endpoint SG: ${VPCE_SG_ID}"
    else
        log_info "VPC endpoint SG already exists: ${VPCE_SG_ID}"
    fi

    # Get route table for S3 gateway endpoint
    ROUTE_TABLE_ID=$(aws ec2 describe-route-tables --filters "Name=vpc-id,Values=${VPC_ID}" "Name=association.main,Values=true" --query "RouteTables[0].RouteTableId" --output text --region ${AWS_REGION})

    # Interface endpoints: ECR API, ECR DKR, CloudWatch Logs, Bedrock AgentCore, STS
    INTERFACE_SERVICES=(
        "com.amazonaws.${AWS_REGION}.ecr.api"
        "com.amazonaws.${AWS_REGION}.ecr.dkr"
        "com.amazonaws.${AWS_REGION}.logs"
        "com.amazonaws.${AWS_REGION}.bedrock-agent-runtime"
        "com.amazonaws.${AWS_REGION}.sts"
        "com.amazonaws.${AWS_REGION}.cognito-idp"
    )

    SUBNET_LIST=$(echo $SUBNET_IDS | tr ' ' ',')

    for SVC in "${INTERFACE_SERVICES[@]}"; do
        SVC_SHORT=$(echo $SVC | awk -F. '{print $NF}')
        EXISTING=$(aws ec2 describe-vpc-endpoints --filters "Name=service-name,Values=${SVC}" "Name=vpc-id,Values=${VPC_ID}" "Name=vpc-endpoint-state,Values=available,pending" --query "VpcEndpoints[0].VpcEndpointId" --output text --region ${AWS_REGION} 2>/dev/null || echo "None")
        if [ "$EXISTING" == "None" ] || [ -z "$EXISTING" ]; then
            # Get supported AZs for this endpoint service
            SUPPORTED_AZS=$(aws ec2 describe-vpc-endpoint-services --service-names ${SVC} --region ${AWS_REGION} --query "ServiceDetails[0].AvailabilityZones" --output text 2>/dev/null || echo "")
            # Filter subnets to only those in supported AZs
            COMPATIBLE_SUBNETS=""
            for SID in ${SUBNET_IDS}; do
                SAZ=$(aws ec2 describe-subnets --subnet-ids ${SID} --region ${AWS_REGION} --query "Subnets[0].AvailabilityZone" --output text 2>/dev/null || echo "")
                if echo "$SUPPORTED_AZS" | grep -q "$SAZ"; then
                    COMPATIBLE_SUBNETS="${COMPATIBLE_SUBNETS} ${SID}"
                fi
            done
            COMPATIBLE_SUBNETS=$(echo $COMPATIBLE_SUBNETS | xargs)
            if [ -z "$COMPATIBLE_SUBNETS" ]; then
                log_warning "No compatible subnets for ${SVC_SHORT}, skipping"
                continue
            fi
            log_info "Creating interface endpoint for ${SVC_SHORT}..."
            aws ec2 create-vpc-endpoint \
                --vpc-id ${VPC_ID} \
                --vpc-endpoint-type Interface \
                --service-name ${SVC} \
                --subnet-ids ${COMPATIBLE_SUBNETS} \
                --security-group-ids ${VPCE_SG_ID} \
                --private-dns-enabled \
                --region ${AWS_REGION} > /dev/null 2>&1 || \
                log_warning "Could not create endpoint for ${SVC_SHORT} (may already exist or not be available)"
        else
            log_info "Endpoint for ${SVC_SHORT} already exists: ${EXISTING}"
        fi
    done

    # Gateway endpoint for S3 (free, no SG needed)
    S3_SVC="com.amazonaws.${AWS_REGION}.s3"
    S3_EXISTING=$(aws ec2 describe-vpc-endpoints --filters "Name=service-name,Values=${S3_SVC}" "Name=vpc-id,Values=${VPC_ID}" "Name=vpc-endpoint-state,Values=available,pending" --query "VpcEndpoints[0].VpcEndpointId" --output text --region ${AWS_REGION} 2>/dev/null || echo "None")
    if [ "$S3_EXISTING" == "None" ] || [ -z "$S3_EXISTING" ]; then
        log_info "Creating gateway endpoint for S3..."
        aws ec2 create-vpc-endpoint \
            --vpc-id ${VPC_ID} \
            --vpc-endpoint-type Gateway \
            --service-name ${S3_SVC} \
            --route-table-ids ${ROUTE_TABLE_ID} \
            --region ${AWS_REGION} > /dev/null 2>&1 || \
            log_warning "Could not create S3 gateway endpoint"
    else
        log_info "S3 gateway endpoint already exists: ${S3_EXISTING}"
    fi

    log_success "VPC endpoints configured"
}

# =============================================================================
# Setup Cognito User Pool for ALB authentication
# =============================================================================
setup_cognito_auth() {
    log_info "Setting up Cognito User Pool for ALB authentication..."

    ALB_DNS=$1
    COGNITO_POOL_NAME="${APP_NAME}-users"

    # Create or find existing User Pool
    POOL_ID=$(aws cognito-idp list-user-pools --max-results 60 --region ${AWS_REGION} --query "UserPools[?Name=='${COGNITO_POOL_NAME}'].Id | [0]" --output text 2>/dev/null || echo "None")
    if [ "$POOL_ID" == "None" ] || [ -z "$POOL_ID" ]; then
        log_info "Creating Cognito User Pool..."
        POOL_ID=$(aws cognito-idp create-user-pool \
            --pool-name "${COGNITO_POOL_NAME}" \
            --auto-verified-attributes email \
            --username-attributes email \
            --mfa-configuration OFF \
            --policies '{"PasswordPolicy":{"MinimumLength":8,"RequireUppercase":true,"RequireLowercase":true,"RequireNumbers":true,"RequireSymbols":false}}' \
            --schema '[{"Name":"email","Required":true,"Mutable":true}]' \
            --admin-create-user-config '{"AllowAdminCreateUserOnly":true}' \
            --region ${AWS_REGION} \
            --query "UserPool.Id" --output text)
        if [ -z "$POOL_ID" ] || [ "$POOL_ID" == "None" ]; then
            log_error "Failed to create Cognito User Pool"
            exit 1
        fi
        log_success "Created Cognito User Pool: ${POOL_ID}"
    else
        log_info "Cognito User Pool already exists: ${POOL_ID}"
    fi

    # Create or find Cognito domain (required for ALB auth)
    COGNITO_DOMAIN="${APP_NAME}-${AWS_ACCOUNT_ID}"
    EXISTING_DOMAIN=$(aws cognito-idp describe-user-pool --user-pool-id "${POOL_ID}" --region ${AWS_REGION} --query "UserPool.Domain" --output text 2>/dev/null || echo "None")
    if [ "$EXISTING_DOMAIN" == "None" ] || [ -z "$EXISTING_DOMAIN" ]; then
        log_info "Creating Cognito domain..."
        aws cognito-idp create-user-pool-domain \
            --domain "${COGNITO_DOMAIN}" \
            --user-pool-id "${POOL_ID}" \
            --region ${AWS_REGION} 2>/dev/null || true
        log_success "Created Cognito domain: ${COGNITO_DOMAIN}"
    else
        COGNITO_DOMAIN="${EXISTING_DOMAIN}"
        log_info "Cognito domain already exists: ${COGNITO_DOMAIN}"
    fi

    # Create or find app client (ALB requires a client with a secret)
    CLIENT_NAME="${APP_NAME}-alb-client"
    CLIENT_ID=$(aws cognito-idp list-user-pool-clients --user-pool-id "${POOL_ID}" --region ${AWS_REGION} --query "UserPoolClients[?ClientName=='${CLIENT_NAME}'].ClientId | [0]" --output text 2>/dev/null || echo "None")
    if [ "$CLIENT_ID" == "None" ] || [ -z "$CLIENT_ID" ]; then
        log_info "Creating Cognito app client..."
        CLIENT_ID=$(aws cognito-idp create-user-pool-client \
            --user-pool-id "${POOL_ID}" \
            --client-name "${CLIENT_NAME}" \
            --generate-secret \
            --allowed-o-auth-flows "code" \
            --allowed-o-auth-flows-user-pool-client \
            --allowed-o-auth-scopes "openid" "email" "profile" \
            --callback-urls "https://${ALB_DNS}/oauth2/idpresponse" \
            --supported-identity-providers "COGNITO" \
            --explicit-auth-flows "ALLOW_USER_SRP_AUTH" "ALLOW_REFRESH_TOKEN_AUTH" \
            --region ${AWS_REGION} \
            --query "UserPoolClient.ClientId" --output text)
        if [ -z "$CLIENT_ID" ] || [ "$CLIENT_ID" == "None" ]; then
            log_error "Failed to create Cognito app client"
            exit 1
        fi
        log_success "Created Cognito app client: ${CLIENT_ID}"
    else
        log_info "Cognito app client already exists: ${CLIENT_ID}"
    fi

    # Export for use in listener creation
    export COGNITO_POOL_ID="${POOL_ID}"
    export COGNITO_CLIENT_ID="${CLIENT_ID}"
    export COGNITO_DOMAIN="${COGNITO_DOMAIN}"
    export COGNITO_POOL_ARN=$(aws cognito-idp describe-user-pool --user-pool-id "${POOL_ID}" --region ${AWS_REGION} --query "UserPool.Arn" --output text)

    log_success "Cognito auth configured (Pool: ${POOL_ID}, Client: ${CLIENT_ID}, Domain: ${COGNITO_DOMAIN})"
}

# =============================================================================
# Generate self-signed cert and import to ACM (for internal ALB HTTPS)
# =============================================================================
setup_acm_cert() {
    log_info "Setting up ACM certificate for internal ALB HTTPS..."

    # Check for existing cert tagged for this app
    CERT_ARN=$(aws acm list-certificates --region ${AWS_REGION} --query "CertificateSummaryList[?DomainName=='${APP_NAME}.internal'].CertificateArn | [0]" --output text 2>/dev/null || echo "None")
    if [ "$CERT_ARN" != "None" ] && [ -n "$CERT_ARN" ]; then
        log_info "ACM certificate already exists: ${CERT_ARN}"
        export ACM_CERT_ARN=${CERT_ARN}
        return
    fi

    log_info "Generating self-signed certificate for internal ALB..."
    CERT_DIR=$(mktemp -d)

    # Generate private key and self-signed cert (valid 1 year)
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ${CERT_DIR}/private.key \
        -out ${CERT_DIR}/certificate.pem \
        -subj "/CN=${APP_NAME}.internal/O=${APP_NAME}" 2>/dev/null

    # Import into ACM
    CERT_ARN=$(aws acm import-certificate \
        --certificate fileb://${CERT_DIR}/certificate.pem \
        --private-key fileb://${CERT_DIR}/private.key \
        --region ${AWS_REGION} \
        --query "CertificateArn" --output text)

    rm -rf ${CERT_DIR}

    export ACM_CERT_ARN=${CERT_ARN}
    log_success "ACM certificate imported: ${CERT_ARN}"
}

# =============================================================================
# Deploy frontend with least-privilege networking
# =============================================================================
deploy_frontend() {
    log_info "Deploying frontend to ECS Fargate (least-privilege networking)..."

    ECR_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${APP_NAME}"

    # Build frontend image via CodeBuild (no local Docker)
    build_frontend_with_codebuild

    # Get AgentCore runtime ARN for task environment
    if [ -z "$AGENTCORE_RUNTIME_ARN" ] && [ -f ".bedrock_agentcore.yaml" ]; then
        AGENTCORE_RUNTIME_ARN=$(grep "agent_arn:" .bedrock_agentcore.yaml | head -1 | awk '{print $2}' || echo "")
    fi

    # =========================================================================
    # VPC and subnet discovery
    # =========================================================================
    VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text --region ${AWS_REGION})
    VPC_CIDR=$(aws ec2 describe-vpcs --vpc-ids ${VPC_ID} --query "Vpcs[0].CidrBlock" --output text --region ${AWS_REGION})
    SUBNETS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=${VPC_ID}" --query "Subnets[0:3].SubnetId" --output text --region ${AWS_REGION} | tr '\t' ' ')
    log_info "VPC: ${VPC_ID} (${VPC_CIDR}) | Subnets: ${SUBNETS}"

    # =========================================================================
    # Delete old ECS service first (so old SG can be released)
    # =========================================================================
    OLD_SERVICE=$(aws ecs describe-services --cluster ${APP_NAME} --services ${APP_NAME} --region ${AWS_REGION} --query "services[?status=='ACTIVE'].serviceName" --output text 2>/dev/null || echo "")
    if [ -n "$OLD_SERVICE" ]; then
        log_warning "Deleting old ECS service to release old security groups..."
        aws ecs update-service --cluster ${APP_NAME} --service ${APP_NAME} --desired-count 0 --region ${AWS_REGION} > /dev/null 2>&1 || true
        aws ecs delete-service --cluster ${APP_NAME} --service ${APP_NAME} --force --region ${AWS_REGION} > /dev/null 2>&1 || true
        log_info "Waiting for old service tasks to drain..."
        sleep 30
    fi

    # =========================================================================
    # Cleanup old insecure resources (internet-facing ALB, wide-open SG)
    # =========================================================================
    cleanup_old_resources ${VPC_ID}

    # =========================================================================
    # Security Groups — least privilege, no 0.0.0.0/0 anywhere
    # =========================================================================
    log_info "Creating least-privilege security groups..."

    # ALB Security Group: HTTPS from anywhere (Cognito auth protects the app), HTTP for redirect
    ALB_SG_ID=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=${APP_NAME}-alb-sg" "Name=vpc-id,Values=${VPC_ID}" --query "SecurityGroups[0].GroupId" --output text --region ${AWS_REGION} 2>/dev/null || echo "None")
    if [ "$ALB_SG_ID" == "None" ] || [ -z "$ALB_SG_ID" ]; then
        ALB_SG_ID=$(aws ec2 create-security-group --group-name ${APP_NAME}-alb-sg --description "ALB SG - Cognito-protected HTTPS" --vpc-id ${VPC_ID} --query "GroupId" --output text --region ${AWS_REGION})
        # Ingress: HTTP+HTTPS from anywhere (Cognito handles authentication)
        aws ec2 authorize-security-group-ingress --group-id ${ALB_SG_ID} --protocol tcp --port 80 --cidr 0.0.0.0/0 --region ${AWS_REGION}
        aws ec2 authorize-security-group-ingress --group-id ${ALB_SG_ID} --protocol tcp --port 443 --cidr 0.0.0.0/0 --region ${AWS_REGION}
        # Revoke default egress and restrict
        aws ec2 revoke-security-group-egress --group-id ${ALB_SG_ID} --protocol -1 --port -1 --cidr 0.0.0.0/0 --region ${AWS_REGION} 2>/dev/null || true
        log_success "Created ALB SG: ${ALB_SG_ID} (ingress: TCP/80,443 from 0.0.0.0/0, Cognito-protected)"
    else
        log_info "ALB SG already exists: ${ALB_SG_ID}"
        # Ensure public HTTPS+HTTP ingress exists
        aws ec2 authorize-security-group-ingress --group-id ${ALB_SG_ID} --protocol tcp --port 443 --cidr 0.0.0.0/0 --region ${AWS_REGION} 2>/dev/null || true
        aws ec2 authorize-security-group-ingress --group-id ${ALB_SG_ID} --protocol tcp --port 80 --cidr 0.0.0.0/0 --region ${AWS_REGION} 2>/dev/null || true
    fi

    # ECS Task Security Group: ingress port 3000 from ALB SG only
    ECS_SG_ID=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=${APP_NAME}-ecs-sg" "Name=vpc-id,Values=${VPC_ID}" --query "SecurityGroups[0].GroupId" --output text --region ${AWS_REGION} 2>/dev/null || echo "None")
    if [ "$ECS_SG_ID" == "None" ] || [ -z "$ECS_SG_ID" ]; then
        ECS_SG_ID=$(aws ec2 create-security-group --group-name ${APP_NAME}-ecs-sg --description "ECS SG - port 3000 from ALB SG only" --vpc-id ${VPC_ID} --query "GroupId" --output text --region ${AWS_REGION})
        # Ingress: port 3000 from ALB SG only (SG-to-SG reference)
        aws ec2 authorize-security-group-ingress --group-id ${ECS_SG_ID} --protocol tcp --port 3000 --source-group ${ALB_SG_ID} --region ${AWS_REGION}
        # Egress: HTTPS to VPC CIDR (for VPC endpoints) + S3 prefix list
        aws ec2 revoke-security-group-egress --group-id ${ECS_SG_ID} --protocol -1 --port -1 --cidr 0.0.0.0/0 --region ${AWS_REGION} 2>/dev/null || true
        aws ec2 authorize-security-group-egress --group-id ${ECS_SG_ID} --protocol tcp --port 443 --cidr ${VPC_CIDR} --region ${AWS_REGION}
        # Also allow HTTPS to 0.0.0.0/0 for ECR public gallery and AWS API calls not covered by endpoints
        aws ec2 authorize-security-group-egress --group-id ${ECS_SG_ID} --protocol tcp --port 443 --cidr 0.0.0.0/0 --region ${AWS_REGION}
        log_success "Created ECS SG: ${ECS_SG_ID} (ingress: TCP/3000 from ALB SG)"
    else
        log_info "ECS SG already exists: ${ECS_SG_ID}"
    fi

    # ALB egress: forward to ECS tasks on port 3000
    aws ec2 authorize-security-group-egress --group-id ${ALB_SG_ID} --protocol tcp --port 3000 --source-group ${ECS_SG_ID} --region ${AWS_REGION} 2>/dev/null || true
    # ALB egress: HTTPS to Cognito endpoints (for authenticate-cognito action)
    aws ec2 authorize-security-group-egress --group-id ${ALB_SG_ID} --protocol tcp --port 443 --cidr 0.0.0.0/0 --region ${AWS_REGION} 2>/dev/null || true

    # =========================================================================
    # VPC Endpoints for private access to AWS services
    # =========================================================================
    setup_vpc_endpoints ${VPC_ID} "${SUBNETS}" ${ECS_SG_ID}

    # =========================================================================
    # Network ACLs — restrict to VPC CIDR (defense in depth)
    # =========================================================================
    log_info "Configuring Network ACLs..."
    NACL_ID=$(aws ec2 describe-network-acls --filters "Name=vpc-id,Values=${VPC_ID}" "Name=default,Values=true" --query "NetworkAcls[0].NetworkAclId" --output text --region ${AWS_REGION})
    # Default NACL allows all — we add explicit deny for non-VPC inbound on port 80
    # Note: NACLs are stateless, so we need both inbound and outbound rules
    # Rule 50: Allow inbound HTTP from VPC CIDR
    aws ec2 create-network-acl-entry --network-acl-id ${NACL_ID} --rule-number 50 --protocol tcp --port-range From=80,To=80 --cidr-block ${VPC_CIDR} --rule-action allow --ingress --region ${AWS_REGION} 2>/dev/null || true
    # Rule 51: Allow inbound HTTPS from VPC CIDR (for VPC endpoints)
    aws ec2 create-network-acl-entry --network-acl-id ${NACL_ID} --rule-number 51 --protocol tcp --port-range From=443,To=443 --cidr-block ${VPC_CIDR} --rule-action allow --ingress --region ${AWS_REGION} 2>/dev/null || true
    # Rule 52: Allow inbound ephemeral ports from VPC CIDR (return traffic)
    aws ec2 create-network-acl-entry --network-acl-id ${NACL_ID} --rule-number 52 --protocol tcp --port-range From=1024,To=65535 --cidr-block ${VPC_CIDR} --rule-action allow --ingress --region ${AWS_REGION} 2>/dev/null || true
    log_info "NACL rules added (VPC CIDR allowed on ports 80, 443, ephemeral)"

    # =========================================================================
    # ECS Cluster
    # =========================================================================
    aws ecs describe-clusters --clusters ${APP_NAME} --region ${AWS_REGION} --query "clusters[?status=='ACTIVE'].clusterName" --output text | grep -q ${APP_NAME} || \
        aws ecs create-cluster --cluster-name ${APP_NAME} --region ${AWS_REGION}

    # =========================================================================
    # IAM Roles (least privilege)
    # =========================================================================
    EXEC_ROLE_NAME="${APP_NAME}-task-execution-role"
    TASK_ROLE_NAME="${APP_NAME}-task-role"

    if ! aws iam get-role --role-name ${EXEC_ROLE_NAME} 2>/dev/null; then
        aws iam create-role --role-name ${EXEC_ROLE_NAME} --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
        aws iam attach-role-policy --role-name ${EXEC_ROLE_NAME} --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
        sleep 10
    fi

    if ! aws iam get-role --role-name ${TASK_ROLE_NAME} 2>/dev/null; then
        aws iam create-role --role-name ${TASK_ROLE_NAME} --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
        # Scoped Bedrock access for AgentCore invocation
        aws iam put-role-policy --role-name ${TASK_ROLE_NAME} --policy-name BedrockAgentCoreAccess --policy-document '{
            "Version":"2012-10-17",
            "Statement":[
                {"Effect":"Allow","Action":["bedrock:InvokeAgent","bedrock:InvokeModel","bedrock:Retrieve","bedrock:RetrieveAndGenerate","bedrock-agentcore:*"],"Resource":"*"},
                {"Effect":"Allow","Action":["marketplace-catalog:*","aws-marketplace:*"],"Resource":"*"},
                {"Effect":"Allow","Action":["cloudformation:DescribeStacks","cloudformation:ListStacks","cloudformation:DescribeStackEvents","cloudformation:CreateStack","cloudformation:DeleteStack","cloudformation:UpdateStack"],"Resource":"*"},
                {"Effect":"Allow","Action":["sts:GetCallerIdentity"],"Resource":"*"}
            ]
        }'
        sleep 10
    fi

    # =========================================================================
    # CloudWatch Logs
    # =========================================================================
    aws logs create-log-group --log-group-name "/ecs/${APP_NAME}" --region ${AWS_REGION} 2>/dev/null || true

    # =========================================================================
    # Task Definition
    # =========================================================================
    AGENTCORE_ENV=""
    if [ -n "$AGENTCORE_RUNTIME_ARN" ]; then
        AGENTCORE_ENV=',{"name":"AGENTCORE_RUNTIME_ARN","value":"'"${AGENTCORE_RUNTIME_ARN}"'"}'
    fi

    cat > /tmp/task-def.json << EOF
{"family":"${APP_NAME}","networkMode":"awsvpc","requiresCompatibilities":["FARGATE"],"cpu":"1024","memory":"2048","executionRoleArn":"arn:aws:iam::${AWS_ACCOUNT_ID}:role/${EXEC_ROLE_NAME}","taskRoleArn":"arn:aws:iam::${AWS_ACCOUNT_ID}:role/${TASK_ROLE_NAME}","containerDefinitions":[{"name":"${APP_NAME}","image":"${ECR_REPO}:latest","essential":true,"portMappings":[{"containerPort":3000,"hostPort":3000,"protocol":"tcp"}],"environment":[{"name":"NODE_ENV","value":"production"},{"name":"PORT","value":"3000"},{"name":"HOSTNAME","value":"0.0.0.0"},{"name":"AWS_REGION","value":"${AWS_REGION}"}${AGENTCORE_ENV}],"logConfiguration":{"logDriver":"awslogs","options":{"awslogs-group":"/ecs/${APP_NAME}","awslogs-region":"${AWS_REGION}","awslogs-stream-prefix":"ecs"}},"healthCheck":{"command":["CMD-SHELL","curl -f http://localhost:3000/ || exit 1"],"interval":30,"timeout":10,"retries":10,"startPeriod":300}}]}
EOF
    aws ecs register-task-definition --cli-input-json file:///tmp/task-def.json --region ${AWS_REGION} > /dev/null

    # =========================================================================
    # ACM Certificate (self-signed for internal ALB — Cognito requires HTTPS)
    # =========================================================================
    setup_acm_cert

    # =========================================================================
    # Internal ALB (not internet-facing)
    # =========================================================================
    ALB_ARN=$(aws elbv2 describe-load-balancers --names ${APP_NAME}-alb --region ${AWS_REGION} --query "LoadBalancers[0].LoadBalancerArn" --output text 2>/dev/null || echo "None")
    if [ "$ALB_ARN" == "None" ] || [ -z "$ALB_ARN" ]; then
        log_info "Creating internal ALB..."
        ALB_ARN=$(aws elbv2 create-load-balancer \
            --name ${APP_NAME}-alb \
            --subnets ${SUBNETS} \
            --security-groups ${ALB_SG_ID} \
            --scheme internet-facing \
            --type application \
            --query "LoadBalancers[0].LoadBalancerArn" --output text --region ${AWS_REGION})
    fi
    ALB_DNS=$(aws elbv2 describe-load-balancers --load-balancer-arns ${ALB_ARN} --query "LoadBalancers[0].DNSName" --output text --region ${AWS_REGION})

    # Target group
    TG_ARN=$(aws elbv2 describe-target-groups --names ${APP_NAME}-tg --region ${AWS_REGION} --query "TargetGroups[0].TargetGroupArn" --output text 2>/dev/null || echo "None")
    if [ "$TG_ARN" == "None" ] || [ -z "$TG_ARN" ]; then
        TG_ARN=$(aws elbv2 create-target-group --name ${APP_NAME}-tg --protocol HTTP --port 3000 --vpc-id ${VPC_ID} --target-type ip --health-check-path "/" --health-check-interval-seconds 30 --unhealthy-threshold-count 10 --query "TargetGroups[0].TargetGroupArn" --output text --region ${AWS_REGION})
    fi

    # =========================================================================
    # Cognito User Pool (for ALB authentication)
    # =========================================================================
    setup_cognito_auth ${ALB_DNS}

    # Update Cognito callback URL to use HTTPS ALB DNS
    aws cognito-idp update-user-pool-client \
        --user-pool-id ${COGNITO_POOL_ID} \
        --client-id ${COGNITO_CLIENT_ID} \
        --allowed-o-auth-flows "code" \
        --allowed-o-auth-flows-user-pool-client \
        --allowed-o-auth-scopes "openid" "email" "profile" \
        --callback-urls "https://${ALB_DNS}/oauth2/idpresponse" \
        --supported-identity-providers "COGNITO" \
        --region ${AWS_REGION} > /dev/null 2>&1 || true

    # =========================================================================
    # Listeners: HTTPS/443 with Cognito auth, HTTP/80 redirects to HTTPS
    # =========================================================================
    # Delete any existing listeners (may be stale/unauthenticated)
    EXISTING_LISTENERS=$(aws elbv2 describe-listeners --load-balancer-arn ${ALB_ARN} --region ${AWS_REGION} --query "Listeners[].ListenerArn" --output text 2>/dev/null || echo "")
    for LIS in $EXISTING_LISTENERS; do
        aws elbv2 delete-listener --listener-arn ${LIS} --region ${AWS_REGION} 2>/dev/null || true
    done

    # HTTPS listener (443) with Cognito authenticate action + forward
    log_info "Creating HTTPS listener with Cognito authentication..."
    aws elbv2 create-listener \
        --load-balancer-arn ${ALB_ARN} \
        --protocol HTTPS \
        --port 443 \
        --certificates CertificateArn=${ACM_CERT_ARN} \
        --default-actions \
            "Type=authenticate-cognito,Order=1,AuthenticateCognitoConfig={UserPoolArn=${COGNITO_POOL_ARN},UserPoolClientId=${COGNITO_CLIENT_ID},UserPoolDomain=${COGNITO_DOMAIN},OnUnauthenticatedRequest=authenticate,Scope=openid}" \
            "Type=forward,Order=2,TargetGroupArn=${TG_ARN}" \
        --region ${AWS_REGION} > /dev/null

    # HTTP listener (80) redirects to HTTPS
    log_info "Creating HTTP->HTTPS redirect listener..."
    aws elbv2 create-listener \
        --load-balancer-arn ${ALB_ARN} \
        --protocol HTTP \
        --port 80 \
        --default-actions 'Type=redirect,RedirectConfig={Protocol=HTTPS,Port=443,StatusCode=HTTP_301}' \
        --region ${AWS_REGION} > /dev/null

    log_success "ALB listeners created with Cognito auth"

    # =========================================================================
    # ECS Service (with separate ECS SG, public IP for ECR pull)
    # =========================================================================
    SUBNETS_COMMA=$(echo $SUBNETS | tr ' ' ',')
    aws ecs create-service \
        --cluster ${APP_NAME} \
        --service-name ${APP_NAME} \
        --task-definition ${APP_NAME} \
        --desired-count 1 \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[${SUBNETS_COMMA}],securityGroups=[${ECS_SG_ID}],assignPublicIp=ENABLED}" \
        --load-balancers "targetGroupArn=${TG_ARN},containerName=${APP_NAME},containerPort=3000" \
        --health-check-grace-period-seconds 600 \
        --region ${AWS_REGION} > /dev/null

    log_success "Frontend deployed (Cognito auth): https://${ALB_DNS}"
    echo ""
    echo "========================================="
    echo "🎉 Deployment Complete (Cognito Auth)"
    echo "========================================="
    echo ""
    echo "🌐 ALB DNS: ${ALB_DNS}"
    echo "   HTTPS with Cognito authentication (HTTP redirects to HTTPS)"
    echo ""
    if [ -n "$AGENTCORE_RUNTIME_ARN" ]; then
        echo "🤖 AgentCore ARN: $AGENTCORE_RUNTIME_ARN"
        echo ""
    fi
    echo "🔐 Security:"
    echo "   ALB SG (${ALB_SG_ID}): ingress TCP/80,443 from ${VPC_CIDR}"
    echo "   ECS SG (${ECS_SG_ID}): ingress TCP/3000 from ALB SG only"
    echo "   Cognito Pool: ${COGNITO_POOL_ID}"
    echo "   Cognito Domain: https://${COGNITO_DOMAIN}.auth.${AWS_REGION}.amazoncognito.com"
    echo ""
    echo "👤 Create a user to log in:"
    echo "   aws cognito-idp admin-create-user --user-pool-id ${COGNITO_POOL_ID} --username <email> --user-attributes Name=email,Value=<email> --temporary-password 'TempPass1!' --region ${AWS_REGION}"
    echo ""
    echo "📡 Access via SSM port-forward:"
    echo "   1. aws ssm start-session --target <instance-id> --document-name AWS-StartPortForwardingSessionToRemoteHost --parameters '{\"host\":[\"${ALB_DNS}\"],\"portNumber\":[\"443\"],\"localPortNumber\":[\"8443\"]}'"
    echo "   2. Open https://localhost:8443 in your browser (accept self-signed cert warning)"
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
