# AI Agent Marketplace - Project Overview

## Project Goal
Create an AI-powered assistant system that guides AWS customers through the complete AWS Marketplace SaaS integration process, from deployment to public visibility, with intelligent error handling and troubleshooting.

## User Journey
1. **Deploy** SaaS integration CloudFormation template
2. **Confirm** SNS subscription for notifications  
3. **Test** metering functionality with usage records
4. **Validate** metering success via BatchMeterUsage API
5. **Request** public visibility for marketplace listing

## Agent Architecture

### Core Agents
- **CreateSaasAgent**: Product configuration (ID, pricing, email, dimensions)
- **ServerlessSaasIntegrationAgent**: CloudFormation deployment + SNS confirmation
- **MeteringAgent**: Entitlement checks + usage record creation + Lambda triggers
- **PublicVisibilityAgent**: Metering validation + visibility request submission
- **ValidationHelperAgent**: Input validation + Knowledge Base guidance

### AI Components  
- **AIMarketplaceOrchestrator**: LLM-powered workflow coordination
- **Knowledge Base**: AWS Marketplace documentation + troubleshooting guides
- **Bedrock LLM**: Natural language understanding + response generation

## Workflow States
```
START → DEPLOYMENT → SNS_CONFIRMATION → METERING → VALIDATION → VISIBILITY → COMPLETE
```

## Error Handling Strategy
- **Input Validation**: Real-time validation with format examples
- **Knowledge Base Lookup**: Context-aware troubleshooting guidance  
- **LLM Explanation**: Natural language error interpretation
- **Retry Mechanisms**: Guided correction with specific instructions

## Technical Integration
- **Strands Framework**: Agent orchestration and tool management
- **AWS APIs**: CloudFormation, DynamoDB, Marketplace Catalog, Bedrock
- **Credential Management**: Temporary AWS credentials for secure access
- **State Tracking**: Workflow progress and error recovery