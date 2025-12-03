# AWS Marketplace Seller Portal - Agent Architecture

## Overview

The portal uses a modular, Strands-based agent architecture with clear separation of concerns.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                    │
│  - React Components                                          │
│  - API Client Layer                                          │
│  - State Management (Zustand)                                │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST APIs
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  - API Endpoints                                             │
│  - Request/Response Handling                                 │
│  - Session Management                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌──────────────────┐    ┌──────────────────────┐
│  Help Agent      │    │  Marketplace Agent   │
│  (Strands)       │    │  (Strands)           │
│                  │    │                      │
│  - Chat/Q&A      │    │  - Orchestrator      │
│  - Documentation │    │  - Sub-Agents        │
│  - Troubleshoot  │    │  - Workflow Mgmt     │
└──────────────────┘    └──────────┬───────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
        ┌───────────────────┐         ┌──────────────────┐
        │  Sub-Agents       │         │  Tools Layer     │
        │  (Modular)        │         │                  │
        │                   │         │  - Seller Reg    │
        │  - Product Info   │         │  - Listing       │
        │  - Pricing        │         │  - SaaS Deploy   │
        │  - EULA           │         │  - AWS APIs      │
        │  - Fulfillment    │         │                  │
        └───────────────────┘         └──────────────────┘
```

## Components

### 1. Frontend Layer

**Technology:** Next.js 14, React, TypeScript, CloudScape Design System

**Responsibilities:**
- User interface and interactions
- State management
- API communication
- Real-time updates

**Key Components:**
- `GlobalHeader` - Navigation and account info
- `WorkflowNav` - Workflow stage tracking
- `Chatbot` - Help agent interface
- `ProgressBar` - Visual progress indicator

### 2. Backend API Layer

**Technology:** FastAPI, Python

**File:** `backend/main.py`

**Responsibilities:**
- HTTP endpoint management
- Request validation
- Response formatting
- Session management
- Agent orchestration

**Key Endpoints:**
- `/validate-credentials` - AWS credential validation
- `/check-seller-status` - Seller registration status
- `/chat` - Help agent interaction
- `/analyze-product` - Product analysis
- `/create-listing` - Listing creation
- `/deploy-saas-integration` - SaaS deployment

### 3. Help Agent (Strands-Based)

**File:** `reference/streamlit-app/agent/marketplace_help_agent.py`

**Purpose:** Provide contextual help and guidance for AWS Marketplace sellers

**Architecture:**
```python
MarketplaceHelpAgent
├── Strands Agent Core
├── Knowledge Base
│   ├── Seller Registration
│   ├── SaaS Integration
│   ├── Pricing Models
│   └── Product Listing
└── Tools
    ├── search_documentation()
    ├── get_seller_registration_guide()
    ├── get_saas_integration_guide()
    ├── get_pricing_models_guide()
    └── get_troubleshooting_help()
```

**Features:**
- Intelligent documentation search
- Step-by-step guidance
- Troubleshooting assistance
- Quick help topics
- Conversation history support

**API Integration:**
```python
# Backend initialization
help_agent = MarketplaceHelpAgent()

# Chat endpoint
@app.post("/chat")
async def chat(data: Dict[str, Any]):
    response = await help_agent.chat(question, conversation_history)
    return response

# Topics endpoint
@app.get("/chat/topics")
async def get_chat_topics():
    topics = help_agent.get_quick_help_topics()
    return {"success": True, "topics": topics}
```

### 4. Marketplace Agent (Strands-Based)

**File:** `reference/streamlit-app/agent/strands_marketplace_agent.py`

**Purpose:** Orchestrate the complete product listing workflow

**Architecture:**
```python
StrandsMarketplaceAgent
├── Strands Agent Core
├── ListingOrchestrator
│   ├── Workflow State Management
│   ├── Stage Transitions
│   └── Data Aggregation
├── Sub-Agents (8 stages)
│   ├── ProductInformationAgent
│   ├── FulfillmentAgent
│   ├── PricingConfigAgent
│   ├── PriceReviewAgent
│   ├── RefundPolicyAgent
│   ├── EULAConfigAgent
│   ├── OfferAvailabilityAgent
│   └── AllowlistAgent
└── Tools
    ├── store_field_data()
    ├── get_collected_data()
    ├── complete_stage()
    ├── create_listing()
    ├── add_delivery()
    ├── add_pricing()
    └── deploy_integration()
```

**Workflow Stages:**
1. Product Information
2. Fulfillment Configuration
3. Pricing Configuration
4. Price Review
5. Refund Policy
6. EULA Configuration
7. Offer Availability
8. Allowlist Configuration

### 5. Orchestrator

**File:** `reference/streamlit-app/agent/orchestrator.py`

**Purpose:** Manage workflow state and coordinate sub-agents

**Responsibilities:**
- Track current workflow stage
- Route to appropriate sub-agent
- Validate stage completion
- Aggregate data across stages
- Execute AWS Marketplace API calls
- Manage entity IDs (product_id, offer_id)

**Key Methods:**
```python
class ListingOrchestrator:
    def get_current_agent() -> SubAgent
    def set_stage_data(field: str, value: Any)
    def check_stage_completion() -> bool
    def complete_current_stage() -> Dict
    def advance_to_next_stage() -> WorkflowStage
    def get_workflow_progress() -> Dict
```

### 6. Sub-Agents

**Location:** `reference/streamlit-app/agent/sub_agents/`

**Purpose:** Handle specific workflow stages

**Structure:**
```python
class BaseSubAgent:
    stage_name: str
    required_fields: List[str]
    stage_data: Dict[str, Any]
    
    def is_stage_complete() -> bool
    def get_required_fields() -> List[str]
    def get_stage_prompt() -> str
    def execute_stage_apis() -> Dict
```

**Examples:**
- `ProductInformationAgent` - Collects product details
- `PricingConfigAgent` - Configures pricing dimensions
- `FulfillmentAgent` - Sets up fulfillment URL

### 7. Tools Layer

**Location:** `reference/streamlit-app/agent/tools/`

**Purpose:** Interact with AWS services and APIs

**Components:**

#### SellerRegistrationTools
```python
class SellerRegistrationTools:
    def check_seller_status() -> Dict
    def get_account_info() -> Dict
    def create_business_profile() -> Dict
    def submit_tax_information() -> Dict
```

#### ListingTools
```python
class ListingTools:
    def create_product() -> Dict
    def add_delivery_options() -> Dict
    def add_pricing_dimensions() -> Dict
    def publish_listing() -> Dict
```

#### ServerlessSaasIntegrationAgent
```python
class ServerlessSaasIntegrationAgent:
    def deploy_infrastructure() -> Dict
    def get_deployment_status() -> Dict
    def get_fulfillment_url() -> str
```

## Data Flow

### 1. User Interaction Flow
```
User Input → Frontend Component → API Call → Backend Endpoint
    → Agent Processing → Tool Execution → AWS API
    → Response → Backend → Frontend → UI Update
```

### 2. Chat Flow (Help Agent)
```
User Question → Chatbot Component → /chat API
    → Help Agent → Tool Selection → Knowledge Base Search
    → Response Generation → Backend → Frontend → Display
```

### 3. Listing Creation Flow (Marketplace Agent)
```
User Input → Product Info Page → /analyze-product API
    → Marketplace Agent → Orchestrator → Current Sub-Agent
    → Field Collection → Stage Completion Check
    → API Execution → AWS Marketplace → Response
    → Next Stage → Repeat
```

## API Contracts

### Help Agent APIs

#### POST /chat
```json
Request:
{
  "question": "How do I register as a seller?",
  "conversation_history": [
    {"role": "user", "content": "previous question"},
    {"role": "assistant", "content": "previous answer"}
  ]
}

Response:
{
  "success": true,
  "response": "To register as an AWS Marketplace seller...",
  "sources": [],
  "conversation_id": "session-123"
}
```

#### GET /chat/topics
```json
Response:
{
  "success": true,
  "topics": [
    {
      "title": "Seller Registration",
      "description": "How to register as an AWS Marketplace seller",
      "query": "How do I register as a seller?"
    }
  ]
}
```

### Marketplace Agent APIs

#### POST /analyze-product
```json
Request:
{
  "product_context": {
    "product_name": "My SaaS Product",
    "product_urls": ["https://example.com"],
    "product_description": "Description"
  },
  "credentials": {
    "aws_access_key_id": "...",
    "aws_secret_access_key": "..."
  }
}

Response:
{
  "success": true,
  "analysis": {
    "product_type": "SaaS",
    "key_features": [...],
    "pricing_model": "usage-based"
  }
}
```

## Modularity Principles

### 1. Separation of Concerns
- **Frontend**: UI/UX only, no business logic
- **Backend**: API orchestration, no UI concerns
- **Agents**: Business logic, workflow management
- **Tools**: AWS API interactions only

### 2. Agent Independence
- Each agent is self-contained
- Agents communicate through well-defined interfaces
- Help Agent operates independently from Marketplace Agent
- Sub-agents are modular and replaceable

### 3. API-First Design
- All agent functionality exposed via REST APIs
- Frontend never directly calls agents
- Backend acts as API gateway
- Enables future mobile/CLI clients

### 4. Strands Framework Benefits
- Consistent agent structure
- Built-in tool management
- LLM integration
- Conversation handling
- Error recovery

## Extension Points

### Adding New Agents
1. Create agent class extending Strands Agent
2. Define tools using `@tool` decorator
3. Implement system prompt
4. Add API endpoints in backend
5. Update frontend to consume APIs

### Adding New Sub-Agents
1. Create sub-agent class extending BaseSubAgent
2. Define required fields
3. Implement stage-specific logic
4. Register with orchestrator
5. Add to workflow stages

### Adding New Tools
1. Create tool function with `@tool` decorator
2. Define clear input/output contracts
3. Implement AWS API interactions
4. Add error handling
5. Register with appropriate agent

## Best Practices

1. **Keep Agents Focused**: Each agent has a single, clear purpose
2. **Use Tools for External Calls**: Never call AWS APIs directly from agents
3. **Maintain State in Orchestrator**: Don't duplicate state across agents
4. **API Versioning**: Version APIs for backward compatibility
5. **Error Handling**: Graceful degradation, clear error messages
6. **Logging**: Comprehensive logging for debugging
7. **Testing**: Unit tests for tools, integration tests for agents
8. **Documentation**: Keep this document updated with changes

## Bedrock AgentCore Migration

**Important**: This application is designed to eventually run on **Amazon Bedrock AgentCore Runtime**. All code follows AgentCore-compatible patterns:

- ✅ Stateless tool functions
- ✅ Explicit state management (DynamoDB-ready)
- ✅ Type-hinted schemas
- ✅ Idempotent operations
- ✅ Structured logging
- ✅ Error handling with retries

See [BEDROCK_AGENTCORE_MIGRATION.md](./BEDROCK_AGENTCORE_MIGRATION.md) for detailed migration plan.

## Future Enhancements

1. **Multi-Agent Collaboration**: Agents working together on complex tasks
2. **Streaming Responses**: Real-time agent output streaming
3. **Agent Memory**: Persistent conversation history
4. **Custom Tools**: User-defined tools for specific workflows
5. **Agent Marketplace**: Shareable agent configurations
6. **Full AgentCore Migration**: Production deployment on Bedrock AgentCore Runtime
