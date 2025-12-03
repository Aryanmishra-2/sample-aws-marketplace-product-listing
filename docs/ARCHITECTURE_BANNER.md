# Architecture Banner

This document contains the architecture diagrams that can be embedded in presentations and documentation.

## System Overview

```mermaid
%%{init: {'theme':'base', 'themeVariables': { 'primaryColor':'#FF9900','primaryTextColor':'#fff','primaryBorderColor':'#232F3E','lineColor':'#FF9900','secondaryColor':'#146EB4','tertiaryColor':'#01A88D'}}}%%
graph TB
    User([👤 Seller])
    
    subgraph Portal["AWS Marketplace Seller Portal"]
        direction LR
        UI[Next.js Frontend<br/>CloudScape UI]
        API[FastAPI Backend<br/>Python]
        Agents[AI Agents<br/>Strands Framework]
    end
    
    subgraph AWS["Amazon Web Services"]
        direction TB
        Bedrock[Amazon Bedrock<br/>Claude 3.5 Sonnet]
        Marketplace[AWS Marketplace<br/>Catalog API]
        Infrastructure[CloudFormation<br/>Lambda • DynamoDB<br/>S3 • OpenSearch]
    end
    
    User <-->|HTTPS| UI
    UI <-->|REST API| API
    API <--> Agents
    Agents <--> Bedrock
    Agents <--> Marketplace
    Agents <--> Infrastructure
    
    style Portal fill:#146EB4,stroke:#232F3E,stroke-width:3px,color:#fff
    style AWS fill:#FF9900,stroke:#232F3E,stroke-width:3px,color:#fff
    style User fill:#01A88D,stroke:#232F3E,stroke-width:2px,color:#fff
```

## 7-Stage Workflow

```mermaid
graph LR
    S1[1. Credentials]
    S2[2. Seller Reg]
    S3[3. Product Info]
    S4[4. AI Analysis]
    S5[5. Content Gen]
    S6[6. Review]
    S7[7. Create Listing]
    S8[8. SaaS Deploy]
    
    S1 --> S2 --> S3 --> S4 --> S5 --> S6 --> S7 --> S8
    
    S1 -.->|STS/IAM| AWS1[AWS]
    S2 -.->|Marketplace| AWS2[AWS]
    S4 -.->|Bedrock| AWS3[AWS]
    S5 -.->|Bedrock| AWS4[AWS]
    S7 -.->|Marketplace| AWS5[AWS]
    S8 -.->|CloudFormation| AWS6[AWS]
    
    style S1 fill:#146EB4,stroke:#232F3E,stroke-width:2px,color:#fff
    style S2 fill:#146EB4,stroke:#232F3E,stroke-width:2px,color:#fff
    style S3 fill:#146EB4,stroke:#232F3E,stroke-width:2px,color:#fff
    style S4 fill:#01A88D,stroke:#232F3E,stroke-width:2px,color:#fff
    style S5 fill:#01A88D,stroke:#232F3E,stroke-width:2px,color:#fff
    style S6 fill:#01A88D,stroke:#232F3E,stroke-width:2px,color:#fff
    style S7 fill:#527FFF,stroke:#232F3E,stroke-width:2px,color:#fff
    style S8 fill:#527FFF,stroke:#232F3E,stroke-width:2px,color:#fff
```

## Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Next.js 14, React 18, TypeScript, CloudScape, Zustand |
| **Backend** | FastAPI, Python 3.13, Uvicorn, Pydantic, Boto3 |
| **AI/ML** | Amazon Bedrock (Claude 3.5), Strands Agents |
| **AWS** | Marketplace, CloudFormation, Lambda, DynamoDB, S3, OpenSearch, IAM, CloudWatch |
| **Future** | Bedrock AgentCore (Runtime, Gateway, Memory, Identity, Tools, Observability) |
