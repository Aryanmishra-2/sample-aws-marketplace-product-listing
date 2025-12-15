# Quick Start: Deploy to Bedrock AgentCore

## TL;DR

Deploy AWS Marketplace Seller Portal agents to Bedrock AgentCore in account **797583073197**:

```bash
cd deployment/bedrock-agentcore/scripts
./deploy-all.sh
```

## Prerequisites ✅

All verified for account 797583073197:
- ✅ AWS CLI configured
- ✅ Bedrock access enabled
- ✅ Claude 3.5 Sonnet v2 available
- ✅ Sufficient IAM permissions

## What You're Deploying

### 2 Bedrock Agents
1. **Help Agent** - Documentation Q&A assistant
2. **Marketplace Agent** - Product listing orchestrator

### Supporting Infrastructure
- S3 bucket for Knowledge Base
- DynamoDB for agent memory
- Lambda functions for tools
- OpenSearch for vector search
- CloudWatch for monitoring

## Deployment Steps

### 1. Review Configuration (Optional)
```bash
cat config/deployment-config.json
```

### 2. Deploy Everything
```bash
cd scripts
./deploy-all.sh
```

This takes ~15-20 minutes and:
- Creates all infrastructure
- Deploys Knowledge Base
- Deploys Lambda functions
- Creates both agents
- Runs integration tests

### 3. Verify Deployment
```bash
# Check agents in console
open "https://console.aws.amazon.com/bedrock/home?region=us-east-1#/agents"

# Or use CLI
aws bedrock-agent list-agents --region us-east-1
```

### 4. Test Help Agent
```bash
# Get agent ID from console or deployment output
AGENT_ID="<your-agent-id>"
ALIAS_ID="<your-alias-id>"

aws bedrock-agent-runtime invoke-agent \
  --agent-id $AGENT_ID \
  --agent-alias-id $ALIAS_ID \
  --session-id test-123 \
  --input-text "How do I register as a seller?" \
  --region us-east-1 \
  output.txt

cat output.txt
```

## What Happens During Deployment

```
01-setup-infrastructure.sh
├── Create S3 bucket
├── Create DynamoDB table
├── Create IAM roles
└── Create CloudWatch resources
    ⏱️ ~2 minutes

02-deploy-knowledge-base.sh
├── Upload documentation to S3
├── Create OpenSearch collection
├── Create Knowledge Base
└── Start ingestion job
    ⏱️ ~5 minutes

03-deploy-lambda-functions.sh
├── Package Lambda code
├── Deploy 4 Lambda functions
└── Configure permissions
    ⏱️ ~3 minutes

04-deploy-help-agent.sh
├── Create Bedrock Agent
├── Add action groups
├── Associate Knowledge Base
└── Create alias
    ⏱️ ~2 minutes

05-deploy-marketplace-agent.sh
├── Create Bedrock Agent
├── Add action groups
├── Configure orchestrator
└── Create alias
    ⏱️ ~2 minutes

06-test-agents.sh
├── Test Help Agent
├── Test Marketplace Agent
└── Verify integrations
    ⏱️ ~1 minute

Total: ~15 minutes
```

## After Deployment

### Access Your Agents

**Bedrock Console**:
https://console.aws.amazon.com/bedrock/home?region=us-east-1#/agents

**CloudWatch Dashboard**:
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=BedrockAgents-Marketplace

### Update Frontend

Replace FastAPI backend calls with Bedrock Agent Runtime:

```typescript
// Before (FastAPI)
const response = await fetch('/api/chat', {
  method: 'POST',
  body: JSON.stringify({ question: userMessage })
});

// After (Bedrock AgentCore)
import { BedrockAgentRuntimeClient, InvokeAgentCommand } from "@aws-sdk/client-bedrock-agent-runtime";

const client = new BedrockAgentRuntimeClient({ region: "us-east-1" });
const command = new InvokeAgentCommand({
  agentId: "AGENT_ID",
  agentAliasId: "ALIAS_ID",
  sessionId: sessionId,
  inputText: userMessage
});

const response = await client.send(command);
```

## Costs

**Estimated Daily Cost**: ~$7-10/day for development
- Bedrock: ~$0.50
- Lambda: ~$1.00
- DynamoDB: ~$0.25
- S3: ~$0.10
- OpenSearch: ~$5.00
- CloudWatch: ~$0.50

**Monthly**: ~$220-300 for light usage

## Troubleshooting

### Deployment Fails
```bash
# Check logs
aws logs tail /aws/bedrock/agents/marketplace --follow

# Verify permissions
aws iam get-role --role-name BedrockAgentRole-Marketplace
```

### Agent Not Responding
```bash
# Check agent status
aws bedrock-agent get-agent --agent-id <AGENT_ID>

# Check Lambda logs
aws logs tail /aws/lambda/marketplace-help-search --follow
```

### Knowledge Base Issues
```bash
# Check ingestion status
aws bedrock-agent list-ingestion-jobs --knowledge-base-id <KB_ID>
```

## Cleanup

Remove all resources:
```bash
cd scripts
./cleanup.sh
```

## Next Steps

1. ✅ Deploy agents (you are here)
2. Test agent invocations
3. Update frontend to use Bedrock Agent Runtime
4. Configure production settings
5. Set up CI/CD pipeline
6. Enable monitoring and alerts

## Support

- **Documentation**: See `docs/BEDROCK_AGENTCORE_*.md`
- **Status**: See `DEPLOYMENT_STATUS.md`
- **Architecture**: See `docs/AGENT_ARCHITECTURE.md`

---

**Ready to deploy?** Run `./scripts/deploy-all.sh` 🚀
