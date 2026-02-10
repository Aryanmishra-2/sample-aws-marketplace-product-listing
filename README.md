# AWS Marketplace Seller Portal

AI-powered portal for AWS Marketplace seller registration and product listing creation.

## Quick Start

### Prerequisites

- AWS CLI configured with credentials
- Python 3.10+ with venv
- AgentCore CLI (`pip install bedrock-agentcore-cli`)
- No Docker required — builds happen via AWS CodeBuild

### Deploy

```bash
python3 -m venv venv
source venv/bin/activate
./deploy.sh
```

This deploys:
1. **Backend**: Python agents to Bedrock AgentCore Runtime (ARM64 via CodeBuild)
2. **Frontend**: Next.js to ECS Fargate with ALB + Cognito authentication (AMD64 via CodeBuild)

### Options

```bash
./deploy.sh --skip-backend   # Deploy frontend only
./deploy.sh --skip-frontend  # Deploy backend only
```

### Post-Deploy: Create a User

The ALB is protected by Cognito. Create a user to log in:

```bash
aws cognito-idp admin-create-user \
  --user-pool-id <pool-id-from-deploy-output> \
  --username your@email.com \
  --user-attributes Name=email,Value=your@email.com \
  --temporary-password 'TempPass1!' \
  --region us-east-1
```

Then open the ALB URL from the deploy output — you'll set a permanent password on first login.

## Configuration

| Variable | Description |
|---|---|
| `AGENTCORE_RUNTIME_ARN` | Auto-set by deploy script |
| `AWS_REGION` | Default: `us-east-1` |

## Architecture

- **Frontend**: Next.js on ECS Fargate (AMD64)
- **Backend**: Python agents on Bedrock AgentCore (ARM64)
- **AI**: Amazon Bedrock (Claude) for intelligent assistance
- **Auth**: Cognito User Pool on ALB (HTTPS listener with authenticate-cognito action)
- **Networking**: Separate ALB/ECS security groups, VPC endpoints for AWS services

## Local Development

```bash
# Backend
cd backend && pip install -r ../requirements.txt && uvicorn main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

## Cleanup

```bash
aws ecs delete-service --cluster ai-agent-marketplace --service ai-agent-marketplace --force --region us-east-1
aws elbv2 delete-load-balancer --load-balancer-arn $(aws elbv2 describe-load-balancers --names ai-agent-marketplace-alb --query "LoadBalancers[0].LoadBalancerArn" --output text --region us-east-1) --region us-east-1
```

## License

See [LICENSE](LICENSE) file.
