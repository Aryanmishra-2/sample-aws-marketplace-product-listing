# AWS Marketplace Seller Portal

AI-powered portal for AWS Marketplace seller registration and product listing creation.

## Quick Start

### Prerequisites

- AWS CLI configured with credentials
- Docker Desktop running
- Node.js 18+
- Python 3.10+

### Deploy

```bash
./deploy.sh
```

This deploys:
1. **Backend**: Bedrock AgentCore Runtime (AI agents)
2. **Frontend**: ECS Fargate with Application Load Balancer

### Options

```bash
./deploy.sh --skip-backend   # Deploy frontend only
./deploy.sh --skip-frontend  # Deploy backend only
```

## Architecture

- **Frontend**: Next.js on ECS Fargate
- **Backend**: Python agents on Bedrock AgentCore
- **AI**: Amazon Bedrock (Claude) for intelligent assistance

## Local Development

```bash
# Backend
cd backend && pip install -r ../requirements.txt && uvicorn main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

## Cleanup

```bash
# Delete ECS service
aws ecs delete-service --cluster ai-agent-marketplace --service ai-agent-marketplace --force --region us-east-1

# Delete ALB
aws elbv2 delete-load-balancer --load-balancer-arn $(aws elbv2 describe-load-balancers --names ai-agent-marketplace-alb --query "LoadBalancers[0].LoadBalancerArn" --output text --region us-east-1) --region us-east-1
```

## License

See [LICENSE](LICENSE) file.
