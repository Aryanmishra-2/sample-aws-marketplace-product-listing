# AI Agent Marketplace

An AI-powered AWS Marketplace Seller Portal that helps sellers create and manage SaaS product listings using Amazon Bedrock AgentCore.

## Features

- **AI-Powered Listing Creation**: Automatically generates product titles, descriptions, and categories
- **SaaS Integration**: Deploys CloudFormation stack for subscription management, metering, and fulfillment
- **Multi-Stage Workflow**: Guides sellers through registration, listing creation, and public visibility
- **Chat Assistant**: AI help agent with AWS documentation integration
- **Real-time Progress Tracking**: Monitors AWS Marketplace changeset status

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        App Runner                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Next.js Frontend                            │   │
│  │  - Seller Registration    - SaaS Integration            │   │
│  │  - Product Listing        - Chat Assistant              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Bedrock AgentCore                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           marketplaceAgent Runtime                       │   │
│  │  - Workflow Orchestrator  - Listing Tools               │   │
│  │  - Metering Agent         - Visibility Agent            │   │
│  │  - Buyer Experience Agent - SaaS Integration Agent      │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AWS Services                                │
│  - AWS Marketplace Catalog API                                  │
│  - Amazon Bedrock (Claude 3 Sonnet)                             │
│  - CloudFormation (SaaS Integration Stack)                      │
│  - DynamoDB, Lambda, API Gateway, SNS                           │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- AWS Account with Marketplace Seller registration
- AWS CLI configured with appropriate permissions
- Docker installed
- Node.js 18+
- Python 3.12+
- AgentCore CLI (`pip install bedrock-agentcore-cli`)

## Project Structure

```
ai-agent-marketplace/
├── frontend/                    # Next.js frontend application
│   ├── src/app/                # App router pages and API routes
│   ├── src/components/         # React components
│   ├── src/lib/                # Utilities and AgentCore client
│   └── Dockerfile              # Frontend container
├── agents/                      # Python agent implementations
│   ├── workflow_orchestrator.py
│   ├── metering.py
│   ├── public_visibility.py
│   ├── buyer_experience.py
│   └── create_saas.py
├── backend/                     # Backend agent tools
│   └── agents/                 # Listing subagents and tools
├── deployment/
│   ├── apprunner/              # App Runner deployment scripts
│   └── cloudformation/         # SaaS integration template
├── agentcore_app.py            # AgentCore runtime entrypoint
├── .bedrock_agentcore.yaml     # AgentCore configuration
└── requirements.txt            # Python dependencies
```

## Deployment

### 1. Deploy AgentCore Agent

```bash
cd ai-agent-marketplace

# Install AgentCore CLI
pip install bedrock-agentcore-cli

# Deploy the agent
agentcore deploy --agent marketplaceAgent --auto-update-on-conflict
```

This will:
- Build the agent container using CodeBuild
- Deploy to Bedrock AgentCore Runtime
- Create memory resources for the agent

### 2. Deploy Frontend to App Runner

```bash
cd ai-agent-marketplace

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Build for AMD64 (App Runner requirement)
cd frontend
docker buildx build --platform linux/amd64 -t ai-agent-marketplace:latest --load .

# Tag and push to ECR
docker tag ai-agent-marketplace:latest <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/ai-agent-marketplace:latest
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/ai-agent-marketplace:latest

# Deploy to App Runner (or use the deploy script)
cd ../deployment/apprunner
./deploy.sh
```

### 3. Update AgentCore Runtime ARN

After deploying AgentCore, update the runtime ARN in `frontend/src/lib/agentcore.ts`:

```typescript
const RUNTIME_ARN = 'arn:aws:bedrock-agentcore:us-east-1:<ACCOUNT_ID>:runtime/marketplaceAgent-<ID>';
```

Rebuild and redeploy the frontend.

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `AGENTCORE_RUNTIME_ARN` | AgentCore runtime ARN |
| `AWS_REGION` | AWS region (default: us-east-1) |
| `BEDROCK_KNOWLEDGE_BASE_ID` | Optional Bedrock KB for chat |

### AgentCore Configuration

The `.bedrock_agentcore.yaml` file configures the agent:

```yaml
agents:
  marketplaceAgent:
    entry_point: agentcore_app.py
    deployment_type: container
    memory:
      type: short_term
```

## Usage

1. **Validate Credentials**: Enter AWS credentials on the home page
2. **Check Seller Status**: Verify Marketplace seller registration
3. **Create Listing**: Enter product info, AI generates content
4. **Review & Submit**: Edit suggestions and create the listing
5. **SaaS Integration**: Deploy CloudFormation stack for fulfillment
6. **Test & Publish**: Run buyer experience tests, request public visibility

## IAM Permissions Required

The application requires these permissions:
- `aws-marketplace:*` - Marketplace Catalog operations
- `bedrock:*` - Bedrock model invocation
- `cloudformation:*` - Stack deployment
- `dynamodb:*` - Subscription/metering tables
- `lambda:*` - Metering functions
- `apigateway:*` - Fulfillment API
- `sns:*` - Notifications
- `sts:GetCallerIdentity` - Credential validation

## License

See [LICENSE](LICENSE) file.
