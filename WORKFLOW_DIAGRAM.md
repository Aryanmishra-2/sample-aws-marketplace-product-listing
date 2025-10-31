# AI Agent Marketplace - Workflow Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                          │
│  Customer ──► Natural Language Queries ──► AI Orchestrator     │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI ORCHESTRATION LAYER                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Bedrock LLM   │  │ Knowledge Base  │  │ Workflow State  │ │
│  │   Nova Pro      │  │      RAG        │  │   Tracking      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        AGENT LAYER                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │CreateSaas   │ │Deployment   │ │  Metering   │ │ Visibility  ││
│  │   Agent     │ │   Agent     │ │   Agent     │ │   Agent     ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
│                          │                                      │
│                  ┌─────────────┐                               │
│                  │ Validation  │                               │
│                  │   Agent     │                               │
│                  └─────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AWS SERVICES                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │CloudFormation│ │  DynamoDB   │ │     SNS     │ │ Marketplace ││
│  │   Stack     │ │   Tables    │ │Notifications│ │ Catalog API ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
│                          │                                      │
│                  ┌─────────────┐                               │
│                  │   Lambda    │                               │
│                  │ Functions   │                               │
│                  └─────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
```

## Workflow Steps

### 1. Configuration Phase
```
User Input → CreateSaasAgent → Product Configuration
├── Product ID: prod-a2lcytlwv2acq
├── Pricing Model: Contract-based-pricing  
├── Email: admin@example.com
└── Usage Dimensions: [metered_1_id, metered_2_id]
```

### 2. Deployment Phase
```
Deployment Agent → CloudFormation Stack
├── DynamoDB Tables (Subscribers, Metering Records)
├── Lambda Functions (Hourly Metering)
├── API Gateway (Customer Registration)
├── SNS Topics (Marketplace Notifications)
└── IAM Roles & Policies
```

### 3. Validation Phase
```
SNS Confirmation → Email Verification → Proceed
├── Check email inbox
├── Confirm subscription
└── Enable notifications
```

### 4. Metering Phase
```
Metering Agent → Usage Records → AWS Marketplace
├── Scan Subscribers Table
├── Create Metering Records
├── Trigger Hourly Lambda
└── Validate BatchMeterUsage Response
```

### 5. Visibility Phase
```
Visibility Agent → Public Request → Marketplace Catalog
├── Validate Metering Success
├── Collect Pricing Dimensions
├── Submit Change Set
└── Monitor Request Status
```

## Error Handling Flow

```
Error Detected → Validation Agent → Knowledge Base Query → LLM Response
├── Input Validation Errors
├── AWS API Errors  
├── Configuration Issues
└── Deployment Failures
                │
                ▼
        Contextual Guidance
├── Error Explanation
├── Correction Steps
├── Format Examples
└── Retry Instructions
```

## AI Integration Points

### LLM Usage:
- **Intent Analysis**: Understanding user requests
- **Error Explanation**: Converting technical errors to user-friendly language
- **Response Generation**: Natural language guidance and instructions

### Knowledge Base Usage:
- **Documentation Search**: AWS Marketplace guides and procedures
- **Troubleshooting**: Error resolution steps and best practices
- **Validation Rules**: Input format requirements and examples