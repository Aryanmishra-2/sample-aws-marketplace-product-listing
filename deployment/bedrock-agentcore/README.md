# Bedrock AgentCore Deployment

Deploy AWS Marketplace Seller Portal agents to Amazon Bedrock AgentCore Runtime.

## Account Information
- **AWS Account**: 797583073197
- **Region**: us-east-1 (primary)
- **Environment**: Development/Testing

## Prerequisites

1. AWS CLI configured with credentials for account 797583073197
2. Sufficient permissions:
   - `bedrock:*` (Bedrock full access)
   - `iam:CreateRole`, `iam:AttachRolePolicy`
   - `lambda:CreateFunction`, `lambda:UpdateFunctionCode`
   - `s3:CreateBucket`, `s3:PutObject`
   - `dynamodb:CreateTable`
   - `logs:CreateLogGroup`

3. Python 3.11+ installed
4. Node.js 18+ installed (for frontend)

## Deployment Steps

### 1. Infrastructure Setup
```bash
cd deployment/bedrock-agentcore
./scripts/01-setup-infrastructure.sh
```

This creates:
- S3 bucket for Knowledge Base documents
- DynamoDB table for agent memory
- IAM roles for agents and Lambda functions
- CloudWatch log groups

### 2. Deploy Knowledge Base
```bash
./scripts/02-deploy-knowledge-base.sh
```

This:
- Uploads documentation to S3
- Creates OpenSearch Serverless collection
- Creates Bedrock Knowledge Base
- Starts ingestion job

### 3. Deploy Lambda Functions (Action Groups)
```bash
./scripts/03-deploy-lambda-functions.sh
```

This deploys Lambda functions for:
- Documentation search
- Seller registration tools
- Product listing tools
- SaaS integration tools

### 4. Deploy Help Agent
```bash
./scripts/04-deploy-help-agent.sh
```

Creates Bedrock Agent with:
- Agent instructions
- Action groups
- Knowledge Base association
- Agent alias

### 5. Deploy Marketplace Agent
```bash
./scripts/05-deploy-marketplace-agent.sh
```

Creates Bedrock Agent with:
- Orchestrator logic
- Sub-agent action groups
- Workflow management
- Agent alias

### 6. Test Deployment
```bash
./scripts/06-test-agents.sh
```

Runs integration tests to verify:
- Agent invocation
- Tool execution
- Knowledge Base retrieval
- Memory persistence

## Quick Deploy (All Steps)
```bash
./scripts/deploy-all.sh
```

## Configuration

Edit `config/deployment-config.json` to customize:
- AWS region
- Resource names
- Model IDs
- Memory retention
- Observability settings

## Monitoring

After deployment, view:
- CloudWatch Dashboard: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=BedrockAgents-Marketplace
- Agent Console: https://console.aws.amazon.com/bedrock/home?region=us-east-1#/agents
- Lambda Functions: https://console.aws.amazon.com/lambda/home?region=us-east-1

## Cleanup

To remove all resources:
```bash
./scripts/cleanup.sh
```

## Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues and solutions.
