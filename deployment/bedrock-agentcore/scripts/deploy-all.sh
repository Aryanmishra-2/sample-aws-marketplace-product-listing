#!/bin/bash
set -e

echo "========================================="
echo "Deploying AWS Marketplace Agents to Bedrock AgentCore"
echo "Account: 797583073197"
echo "Region: us-east-1"
echo "========================================="
echo ""

# Check AWS credentials
echo "Verifying AWS credentials..."
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
if [ "$AWS_ACCOUNT" != "797583073197" ]; then
  echo "ERROR: Wrong AWS account. Expected 797583073197, got $AWS_ACCOUNT"
  exit 1
fi
echo "✓ Authenticated to account 797583073197"
echo ""

# Make scripts executable
chmod +x ./01-setup-infrastructure.sh
chmod +x ./02-deploy-knowledge-base.sh
chmod +x ./03-deploy-lambda-functions.sh
chmod +x ./04-deploy-help-agent.sh
chmod +x ./05-deploy-marketplace-agent.sh
chmod +x ./06-test-agents.sh

# Run deployment steps
echo "Starting deployment..."
echo ""

./01-setup-infrastructure.sh
echo ""

./02-deploy-knowledge-base.sh
echo ""

./03-deploy-lambda-functions.sh
echo ""

./04-deploy-help-agent.sh
echo ""

./05-deploy-marketplace-agent.sh
echo ""

echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Running tests..."
./06-test-agents.sh
echo ""

echo "========================================="
echo "All Done! 🎉"
echo "========================================="
echo ""
echo "Access your agents:"
echo "  - Bedrock Console: https://console.aws.amazon.com/bedrock/home?region=us-east-1#/agents"
echo "  - CloudWatch Dashboard: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=BedrockAgents-Marketplace"
echo ""
echo "Test the Help Agent:"
echo "  aws bedrock-agent-runtime invoke-agent \\"
echo "    --agent-id <AGENT_ID> \\"
echo "    --agent-alias-id <ALIAS_ID> \\"
echo "    --session-id test-session-1 \\"
echo "    --input-text 'How do I register as a seller?' \\"
echo "    --region us-east-1"
echo ""
