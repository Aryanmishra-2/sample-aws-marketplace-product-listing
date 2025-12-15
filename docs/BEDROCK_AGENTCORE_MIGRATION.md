# Bedrock AgentCore Runtime Migration Plan

## Overview

This application is designed to eventually run on **Amazon Bedrock AgentCore Runtime** with other AWS primitives. All architectural decisions and code implementations should support this migration path.

## Current State vs. Target State

### Current Architecture
```
Frontend (Next.js) → Backend (FastAPI) → Strands Agents → AWS APIs
```

### Target Architecture (Bedrock AgentCore)
```
Frontend (Next.js) → API Gateway → Bedrock AgentCore Runtime
                                    ├── Help Agent (AgentCore)
                                    ├── Marketplace Agent (AgentCore)
                                    ├── Orchestrator (AgentCore)
                                    └── Sub-Agents (AgentCore)
                                    
AgentCore Runtime integrates with:
├── Amazon Bedrock (LLM)
├── AWS Lambda (Tool execution)
├── DynamoDB (State management)
├── S3 (Document storage)
├── CloudWatch (Logging/Monitoring)
└── AWS Marketplace APIs
```

## Bedrock AgentCore Primitives

### 1. Agent Definition
Agents in AgentCore are defined with:
- **Instructions**: System prompts and behavior guidelines
- **Action Groups**: Collections of tools/functions
- **Knowledge Bases**: RAG-enabled document repositories
- **Guardrails**: Safety and compliance controls

### 2. Core Components (See [BEDROCK_AGENTCORE_COMPONENTS.md](./BEDROCK_AGENTCORE_COMPONENTS.md))
- **Browser Tool**: Web scraping and research capabilities
- **Memory**: Conversation and session persistence
- **Identity**: User context and permission management
- **Knowledge Base**: RAG for AWS Marketplace documentation
- **Observability**: Monitoring, tracing, and analytics

### 2. Action Groups (Tools)
Current Strands `@tool` decorators map to AgentCore Action Groups:
```python
# Current (Strands)
@tool
def search_documentation(query: str) -> dict:
    """Search AWS Marketplace documentation"""
    pass

# Future (AgentCore)
# Defined in OpenAPI schema, executed via Lambda
```

### 3. Knowledge Bases
Current knowledge base dictionaries will become:
- **Amazon Bedrock Knowledge Bases**
- Backed by S3 + Vector DB (OpenSearch/Pinecone)
- Automatic RAG integration

### 4. State Management
Current in-memory state will use:
- **DynamoDB** for session state
- **S3** for workflow artifacts
- **Parameter Store** for configuration

## Migration Strategy

### Phase 1: Preparation (Current)
✅ Use Strands SDK (compatible with AgentCore patterns)
✅ Modular agent architecture
✅ Tool-based design
✅ API-first approach
✅ Stateless operations where possible

### Phase 2: AgentCore Compatibility Layer
- [ ] Create AgentCore-compatible tool definitions (OpenAPI schemas)
- [ ] Implement Lambda functions for tool execution
- [ ] Set up DynamoDB for state management
- [ ] Create S3 buckets for document storage
- [ ] Define agent instructions in AgentCore format

### Phase 3: Hybrid Deployment
- [ ] Run agents in both Strands and AgentCore
- [ ] Gradual traffic migration
- [ ] Performance comparison
- [ ] Feature parity validation

### Phase 4: Full Migration
- [ ] Deprecate FastAPI backend
- [ ] Use API Gateway + Lambda
- [ ] All agents on AgentCore runtime
- [ ] CloudWatch monitoring
- [ ] Cost optimization

## Design Principles for AgentCore Compatibility

### 1. Stateless Tool Functions
**Current Design:**
```python
@tool
def check_seller_status(credentials: dict) -> dict:
    """Check seller status - stateless, idempotent"""
    client = boto3.client('marketplace-catalog', **credentials)
    response = client.list_entities(...)
    return {"status": "APPROVED", "products": [...]}
```

**Why:** AgentCore tools are Lambda functions - must be stateless

### 2. Explicit State Management
**Current Design:**
```python
class ListingOrchestrator:
    def __init__(self):
        self.current_stage = WorkflowStage.PRODUCT_INFO
        self.all_data = {}
    
    def save_state(self, session_id: str):
        """Save to DynamoDB"""
        dynamodb.put_item(
            TableName='workflow-state',
            Item={'session_id': session_id, 'state': self.all_data}
        )
```

**Why:** AgentCore doesn't maintain in-memory state between invocations

### 3. Tool Input/Output Schemas
**Current Design:**
```python
@tool
def create_product(
    product_name: str,
    description: str,
    logo_url: str
) -> dict:
    """
    Create AWS Marketplace product.
    
    Args:
        product_name: Product name (required)
        description: Product description (required)
        logo_url: S3 URL to product logo (required)
    
    Returns:
        dict: {"product_id": "prod-xxx", "status": "CREATED"}
    """
    pass
```

**Why:** AgentCore requires explicit schemas for tool invocation

### 4. Idempotent Operations
**Current Design:**
```python
@tool
def deploy_saas_integration(product_id: str, email: str) -> dict:
    """Deploy SaaS integration - idempotent with stack name"""
    stack_name = f"marketplace-saas-{product_id}"
    
    # Check if stack exists
    try:
        cfn.describe_stacks(StackName=stack_name)
        return {"status": "ALREADY_EXISTS", "stack_name": stack_name}
    except:
        # Create new stack
        cfn.create_stack(StackName=stack_name, ...)
        return {"status": "CREATING", "stack_name": stack_name}
```

**Why:** AgentCore may retry operations - must be safe to retry

### 5. Structured Logging
**Current Design:**
```python
import json
import logging

logger = logging.getLogger(__name__)

@tool
def execute_api_call(params: dict) -> dict:
    logger.info(json.dumps({
        "event": "api_call_start",
        "tool": "execute_api_call",
        "params": params,
        "timestamp": datetime.utcnow().isoformat()
    }))
    
    result = make_api_call(params)
    
    logger.info(json.dumps({
        "event": "api_call_complete",
        "tool": "execute_api_call",
        "result": result,
        "timestamp": datetime.utcnow().isoformat()
    }))
    
    return result
```

**Why:** AgentCore integrates with CloudWatch - structured logs enable better monitoring

### 6. Error Handling with Retry Logic
**Current Design:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@tool
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def call_aws_api(params: dict) -> dict:
    """Call AWS API with automatic retry"""
    try:
        response = client.api_call(**params)
        return {"success": True, "data": response}
    except ClientError as e:
        if e.response['Error']['Code'] in ['ThrottlingException', 'TooManyRequestsException']:
            raise  # Retry
        return {"success": False, "error": str(e)}
```

**Why:** AgentCore expects tools to handle transient failures gracefully

## AgentCore-Specific Implementations

### 1. Agent Instructions (System Prompts)

**Help Agent Instructions:**
```yaml
# bedrock-agents/help-agent/instructions.yaml
name: AWS Marketplace Help Agent
description: Provides guidance and documentation for AWS Marketplace sellers

instructions: |
  You are an AWS Marketplace Help Assistant. Your role is to help sellers navigate 
  the AWS Marketplace seller journey.
  
  You have access to:
  - AWS Marketplace documentation via Knowledge Base
  - Troubleshooting tools
  - Seller registration guides
  - SaaS integration documentation
  
  Always:
  - Be concise and actionable
  - Provide specific steps when possible
  - Include relevant documentation links
  - Use examples to clarify concepts
  
  When users ask questions:
  1. Search the knowledge base for relevant information
  2. Provide clear, structured answers
  3. Include links to official AWS documentation
  4. Offer next steps or related topics

action_groups:
  - name: documentation_search
    description: Search AWS Marketplace documentation
  - name: troubleshooting
    description: Provide troubleshooting assistance
  - name: guides
    description: Access step-by-step guides

knowledge_bases:
  - kb_id: KB-MARKETPLACE-DOCS
    description: AWS Marketplace seller documentation
```

### 2. Action Group Definitions (OpenAPI)

**Example: Documentation Search Action Group**
```yaml
# bedrock-agents/help-agent/action-groups/documentation-search.yaml
openapi: 3.0.0
info:
  title: Documentation Search Actions
  version: 1.0.0

paths:
  /search-documentation:
    post:
      summary: Search AWS Marketplace documentation
      operationId: searchDocumentation
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                query:
                  type: string
                  description: Search query or topic
              required:
                - query
      responses:
        '200':
          description: Search results
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  results:
                    type: array
                    items:
                      type: object
                  count:
                    type: integer
      x-amazon-bedrock-agent-action:
        lambda_arn: arn:aws:lambda:us-east-1:ACCOUNT:function:marketplace-help-search
```

### 3. Lambda Function for Tool Execution

**Example: Documentation Search Lambda**
```python
# lambda/help-agent/search-documentation/handler.py
import json
import boto3
from typing import Dict, Any

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function for documentation search tool.
    Called by Bedrock AgentCore when tool is invoked.
    """
    # Extract parameters from AgentCore event
    parameters = event.get('parameters', [])
    query = next((p['value'] for p in parameters if p['name'] == 'query'), '')
    
    # Execute search logic
    results = search_knowledge_base(query)
    
    # Return in AgentCore format
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': event['actionGroup'],
            'function': event['function'],
            'functionResponse': {
                'responseBody': {
                    'TEXT': {
                        'body': json.dumps({
                            'success': True,
                            'results': results,
                            'count': len(results)
                        })
                    }
                }
            }
        }
    }

def search_knowledge_base(query: str) -> list:
    """Search Bedrock Knowledge Base"""
    bedrock_agent = boto3.client('bedrock-agent-runtime')
    
    response = bedrock_agent.retrieve(
        knowledgeBaseId='KB-MARKETPLACE-DOCS',
        retrievalQuery={'text': query}
    )
    
    return [
        {
            'content': result['content']['text'],
            'source': result['location']['s3Location']['uri']
        }
        for result in response['retrievalResults']
    ]
```

### 4. State Management with DynamoDB

**Session State Schema:**
```python
# models/session_state.py
from typing import Dict, Any, Optional
from datetime import datetime
import boto3

class SessionState:
    """Manage agent session state in DynamoDB"""
    
    def __init__(self, table_name: str = 'marketplace-agent-sessions'):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
    
    def save_state(self, session_id: str, state: Dict[str, Any]):
        """Save session state"""
        self.table.put_item(
            Item={
                'session_id': session_id,
                'state': state,
                'updated_at': datetime.utcnow().isoformat(),
                'ttl': int((datetime.utcnow() + timedelta(days=7)).timestamp())
            }
        )
    
    def load_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session state"""
        response = self.table.get_item(Key={'session_id': session_id})
        return response.get('Item', {}).get('state')
    
    def update_workflow_stage(self, session_id: str, stage: str):
        """Update current workflow stage"""
        self.table.update_item(
            Key={'session_id': session_id},
            UpdateExpression='SET #state.current_stage = :stage, updated_at = :timestamp',
            ExpressionAttributeNames={'#state': 'state'},
            ExpressionAttributeValues={
                ':stage': stage,
                ':timestamp': datetime.utcnow().isoformat()
            }
        )
```

## Code Guidelines for AgentCore Compatibility

### ✅ DO

1. **Use type hints everywhere**
   ```python
   def process_data(input: str, config: Dict[str, Any]) -> Dict[str, Any]:
       pass
   ```

2. **Make tools stateless**
   ```python
   @tool
   def calculate(a: int, b: int) -> int:
       return a + b  # No instance variables
   ```

3. **Use explicit schemas**
   ```python
   from pydantic import BaseModel
   
   class ToolInput(BaseModel):
       query: str
       max_results: int = 10
   ```

4. **Handle errors gracefully**
   ```python
   try:
       result = api_call()
       return {"success": True, "data": result}
   except Exception as e:
       return {"success": False, "error": str(e)}
   ```

5. **Log structured data**
   ```python
   logger.info(json.dumps({"event": "tool_start", "tool": "search"}))
   ```

### ❌ DON'T

1. **Don't use global state**
   ```python
   # BAD
   global_cache = {}
   
   def get_data():
       return global_cache.get('key')
   ```

2. **Don't assume execution context**
   ```python
   # BAD
   def process():
       # Assumes running in FastAPI
       request = get_current_request()
   ```

3. **Don't use long-running operations**
   ```python
   # BAD
   def process():
       time.sleep(300)  # Lambda timeout!
   ```

4. **Don't hardcode credentials**
   ```python
   # BAD
   client = boto3.client('s3', 
       aws_access_key_id='AKIAIOSFODNN7EXAMPLE')
   ```

5. **Don't use file system for persistence**
   ```python
   # BAD
   with open('/tmp/state.json', 'w') as f:
       json.dump(state, f)
   ```

## Migration Checklist

### Code Preparation
- [ ] All tools are stateless functions
- [ ] Type hints on all functions
- [ ] Pydantic models for complex inputs
- [ ] Structured logging implemented
- [ ] Error handling with retries
- [ ] No global state dependencies
- [ ] No file system persistence
- [ ] Idempotent operations

### Infrastructure
- [ ] DynamoDB table for session state
- [ ] S3 buckets for documents/artifacts
- [ ] Lambda functions for each tool
- [ ] API Gateway for frontend
- [ ] CloudWatch log groups
- [ ] IAM roles and policies
- [ ] VPC configuration (if needed)

### AgentCore Setup
- [ ] Agent definitions created
- [ ] Action groups defined (OpenAPI)
- [ ] Knowledge bases configured
- [ ] Guardrails configured
- [ ] Agent aliases created
- [ ] Testing environment set up

### Testing
- [ ] Unit tests for all tools
- [ ] Integration tests with AgentCore
- [ ] Load testing
- [ ] Cost analysis
- [ ] Performance benchmarks

## Benefits of AgentCore Runtime

1. **Scalability**: Automatic scaling with Lambda
2. **Cost**: Pay per invocation, no idle costs
3. **Reliability**: AWS-managed infrastructure
4. **Security**: IAM-based access control
5. **Monitoring**: Built-in CloudWatch integration
6. **Maintenance**: No server management
7. **Integration**: Native AWS service integration
8. **Compliance**: AWS compliance certifications

## Timeline

- **Q1 2025**: Code preparation and compatibility layer
- **Q2 2025**: Infrastructure setup and Lambda migration
- **Q3 2025**: AgentCore deployment and testing
- **Q4 2025**: Full production migration

## Resources

- [Amazon Bedrock Agents Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [AgentCore Runtime Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-runtime.html)
- [Action Groups (Tools) Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-action-groups.html)
- [Knowledge Bases Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)
