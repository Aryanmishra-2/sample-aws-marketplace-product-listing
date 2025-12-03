# Agent Architecture

This document describes the AI agent architecture for **Listing Products in AWS Marketplace**, including the current implementation and the future migration to Amazon Bedrock AgentCore.

## Overview

The application uses an AI-powered system to automate the product listing workflow. The architecture consists of:

1. **Frontend Layer** - Next.js 14 with CloudScape UI
2. **Backend Layer** - FastAPI with AI agent integration
3. **Tools Layer** - Modular AWS service integrations
4. **AWS Services Layer** - Bedrock, Marketplace, CloudFormation, etc.

## Current Architecture

### 1. Frontend Layer

**Location:** `frontend/src/`

The frontend provides a modern, AWS-themed user interface with a 7-stage workflow.

**Key Pages:**
- `app/page.tsx` - Credentials validation
- `app/seller-registration/page.tsx` - Seller status verification
- `app/product-info/page.tsx` - Product information input
- `app/ai-analysis/page.tsx` - AI analysis results display
- `app/review-suggestions/page.tsx` - Content review and editing
- `app/create-listing/page.tsx` - Listing creation and submission
- `app/saas-integration/page.tsx` - SaaS infrastructure deployment

**Key Components:**
- `components/GlobalHeader.tsx` - AWS-themed navigation header
- `components/WorkflowNav.tsx` - Sidebar workflow navigation
- `components/ProgressBar.tsx` - Visual progress tracking
- `components/Chatbot.tsx` - Floating AI help assistant

**State Management:**
- Zustand store (`lib/store.ts`) for global state
- Session management
- Workflow progress tracking
- User data persistence

### 2. Backend Layer

**Location:** `backend/main.py`

The FastAPI backend orchestrates AI agents and AWS service integrations.

**Core API Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/validate-credentials` | POST | AWS credential validation via STS |
| `/check-seller-status` | POST | Marketplace seller registration check |
| `/analyze-product` | POST | AI-powered product analysis |
| `/generate-content` | POST | AI content generation for listings |
| `/suggest-pricing` | POST | AI pricing model recommendations |
| `/create-listing` | POST | Create marketplace listing |
| `/deploy-saas` | POST | Deploy SaaS CloudFormation stack |
| `/get-stack-status` | POST | Monitor CloudFormation deployment |
| `/chat` | POST | AI help assistant interaction |

**Agent Integration:**
The backend integrates AI capabilities through:
- Amazon Bedrock Claude 3.5 Sonnet for analysis and generation
- Workflow orchestration logic
- State management across stages
- Error handling and retry logic

### 3. AI Agent System

The application uses AI agents to automate complex tasks:

#### Help Agent
**Purpose:** Provide contextual help and guidance

**Implementation:** `/chat` endpoint in `backend/main.py`

**Capabilities:**
- AWS Marketplace documentation search
- Troubleshooting common issues
- Workflow stage guidance
- Best practices recommendations

**Use Cases:**
- "How do I create a SaaS product listing?"
- "What pricing model should I use?"
- "Why is my seller registration failing?"

#### Marketplace Agent
**Purpose:** Orchestrate the product listing workflow

**Implementation:** Multiple endpoints in `backend/main.py`

**Workflow Stages:**
1. **Credentials Stage** - Validates AWS access keys and permissions
2. **Seller Stage** - Verifies marketplace seller registration
3. **Product Stage** - Gathers product information from user
4. **Analysis Stage** - AI analyzes product features and benefits
5. **Content Stage** - AI generates optimized listing content
6. **Pricing Stage** - AI recommends pricing models and dimensions
7. **Listing Stage** - Creates product and offer in marketplace
8. **SaaS Stage** - Deploys serverless infrastructure (optional)

**AI Capabilities:**
- Product feature extraction
- Competitive analysis
- Content optimization for SEO
- Pricing strategy recommendations
- Technical requirement identification

### 4. Tools Layer

**Location:** `tools/` directory

Modular tools for AWS service interactions.

#### Marketplace Tools (`marketplace_tools.py`)

```python
validate_credentials(access_key, secret_key, session_token, region)
# Validates AWS credentials using STS GetCallerIdentity

check_seller_status(session)
# Checks AWS Marketplace seller registration status

create_product_listing(session, product_data)
# Creates product listing via Marketplace Catalog API

get_listing_status(session, product_id)
# Retrieves listing status and details
```

#### Bedrock Tools (`bedrock_tools.py`)

```python
analyze_product(session, product_name, website, description, docs)
# AI-powered product analysis using Claude 3.5 Sonnet

generate_listing_content(session, product_analysis)
# Generates title, descriptions, and highlights

suggest_pricing_model(session, product_type, analysis)
# Recommends pricing model and dimensions

optimize_content(session, content)
# Optimizes content for SEO and marketplace guidelines
```

#### SaaS Tools (`saas_tools.py`)

```python
deploy_saas_stack(session, stack_config)
# Deploys CloudFormation stack for SaaS infrastructure

monitor_stack_status(session, stack_name)
# Monitors CloudFormation deployment progress

create_fulfillment_api(session, config)
# Creates API Gateway fulfillment endpoints

setup_metering(session, config)
# Configures usage metering Lambda function
```

#### Help Tools (`help_tools.py`)

```python
search_documentation(query)
# Searches AWS Marketplace documentation

troubleshoot_issue(issue_description)
# Provides troubleshooting guidance

get_workflow_guidance(stage)
# Returns stage-specific instructions
```

### 5. AWS Services Integration

The application integrates with multiple AWS services:

**Amazon Bedrock:**
- Model: Claude 3.5 Sonnet (`us.anthropic.claude-3-5-sonnet-20241022-v2:0`)
- Use: Product analysis, content generation, pricing recommendations
- API: `bedrock-runtime:InvokeModel`

**AWS Marketplace Catalog:**
- Use: Seller verification, product creation, offer management
- APIs: `DescribeEntity`, `ListEntities`, `StartChangeSet`, `DescribeChangeSet`

**AWS CloudFormation:**
- Use: SaaS infrastructure deployment
- Resources: Lambda, DynamoDB, API Gateway, SNS
- Template: `deployment/cloudformation/Integration.yaml`

**AWS IAM/STS:**
- Use: Credential validation, permission checking
- APIs: `GetCallerIdentity`, `GetUser`, `GetRole`

**Amazon DynamoDB:**
- Use: Subscription management, state storage
- Tables: Created by CloudFormation for SaaS products

**AWS Lambda:**
- Use: Fulfillment functions, metering functions
- Triggers: API Gateway, scheduled events

**Amazon API Gateway:**
- Use: Fulfillment endpoints for SaaS products
- Endpoints: `/register`, `/unregister`

**Amazon CloudWatch:**
- Use: Logging, monitoring, metrics
- Logs: Application logs, Lambda logs, API Gateway logs

## Data Flow

### Product Listing Creation Flow

```
1. User enters credentials
   ↓
2. Backend validates via STS
   ↓
3. Frontend checks seller status
   ↓
4. Backend queries Marketplace Catalog API
   ↓
5. User provides product information
   ↓
6. Backend sends to Bedrock for analysis
   ↓
7. Claude 3.5 analyzes and returns insights
   ↓
8. Backend generates content via Bedrock
   ↓
9. User reviews and edits content
   ↓
10. Backend creates listing via Marketplace API
    ↓
11. (Optional) Deploy SaaS stack via CloudFormation
```

### Help Agent Flow

```
1. User asks question in chatbot
   ↓
2. Frontend sends to /chat endpoint
   ↓
3. Backend processes with context
   ↓
4. Bedrock generates response
   ↓
5. Backend returns formatted answer
   ↓
6. Frontend displays in chat interface
```

## Future: Bedrock AgentCore Migration

### Planned Architecture

The application is designed for migration to Amazon Bedrock AgentCore:

**AgentCore Runtime:**
- Serverless execution environment
- Managed scaling and availability
- Built-in monitoring and logging

**AgentCore Memory:**
- Multi-strategy memory (USER_PREFERENCE + SEMANTIC)
- Persistent seller preferences
- Product template storage
- Conversation history

**AgentCore Gateway:**
- MCP-compatible tool integration
- Automatic API conversion
- Lambda function wrapping

**AgentCore Identity:**
- IAM-based access management
- Seller identity tracking
- Permission management

**AgentCore Tools:**
- Browser Tool for web scraping
- Code Interpreter for data processing
- Built-in tool management

**AgentCore Observability:**
- CloudWatch integration
- X-Ray tracing
- Performance metrics
- Error tracking

### Migration Benefits

1. **Reduced Operational Overhead**
   - No server management
   - Automatic scaling
   - Built-in monitoring

2. **Enhanced Capabilities**
   - Browser tool for product website analysis
   - Advanced memory management
   - Better observability

3. **Improved Reliability**
   - Managed infrastructure
   - Automatic failover
   - Built-in retry logic

4. **Cost Optimization**
   - Pay-per-use pricing
   - No idle costs
   - Efficient resource utilization

### Migration Path

See [BEDROCK_AGENTCORE_MIGRATION.md](./BEDROCK_AGENTCORE_MIGRATION.md) for detailed migration guide.

## Security Considerations

### Credential Management
- Never store AWS credentials in code
- Use environment variables or UI input
- Validate credentials before use
- Implement session timeouts

### API Security
- CORS configuration for production
- Rate limiting on endpoints
- Input validation with Pydantic
- Error handling without exposing internals

### Data Privacy
- Don't log sensitive data
- Encrypt data in transit (HTTPS)
- Use AWS KMS for encryption at rest
- Implement proper access controls

### IAM Permissions
Follow least privilege principle:
- Bedrock: `InvokeModel` only
- Marketplace: Read and write to own products
- CloudFormation: Stack management only
- No admin or root permissions

## Performance Optimization

### Response Times
- API endpoints: < 2s (excluding AI calls)
- AI analysis: 5-15s (Bedrock processing)
- Content generation: 10-20s (Bedrock processing)
- CloudFormation deployment: 5-10 minutes

### Caching Strategy
- Cache Bedrock responses for similar queries
- Cache seller status for session duration
- Cache documentation search results
- Invalidate cache on data changes

### Scalability
- Horizontal scaling with ECS/Lambda
- Bedrock auto-scales automatically
- DynamoDB on-demand scaling
- CloudFront for frontend distribution

## Monitoring and Observability

### Metrics to Track
- API response times
- Bedrock invocation count and latency
- Error rates by endpoint
- Workflow completion rates
- User session duration

### Logging
- Application logs to CloudWatch
- Structured logging with JSON
- Log levels: DEBUG, INFO, WARNING, ERROR
- Correlation IDs for request tracking

### Alerting
- High error rates
- Slow API responses
- Bedrock throttling
- CloudFormation failures
- Cost anomalies

## Testing Strategy

### Unit Tests
- Tool functions
- API endpoint logic
- State management
- Error handling

### Integration Tests
- End-to-end workflow
- AWS service integration
- Bedrock API calls
- CloudFormation deployment

### Manual Testing
- UI/UX testing
- Cross-browser compatibility
- Mobile responsiveness
- Accessibility (WCAG 2.1)

## Deployment

### Development
```bash
# Backend
cd backend && uvicorn main:app --reload

# Frontend
cd frontend && npm run dev
```

### Production
```bash
# Automated deployment
python deploy.py --component all

# Manual deployment
# See deployment/README.md
```

## References

- [Bedrock AgentCore Components](./BEDROCK_AGENTCORE_COMPONENTS.md)
- [Bedrock AgentCore Migration](./BEDROCK_AGENTCORE_MIGRATION.md)
- [SaaS Integration Workflow](./SAAS_INTEGRATION_COMPLETE_WORKFLOW.md)
- [Chatbot Implementation](./CHATBOT_IMPLEMENTATION.md)
- [AWS Theme Implementation](./AWS_THEME_IMPLEMENTATION.md)

---

**Last Updated:** December 2, 2024
