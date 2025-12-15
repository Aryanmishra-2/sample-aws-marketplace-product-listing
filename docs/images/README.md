# Architecture Diagrams

This directory contains architecture diagrams for the AWS Marketplace Seller Portal.

## Creating the Architecture Diagram

To create the `marketplace-seller-portal-architecture.png` diagram:

### Option 1: Using draw.io (Recommended)

1. Go to [draw.io](https://app.diagrams.net/)
2. Create a new diagram
3. Use the following structure:

```
┌─────────────────────────────────────────────────────────────────┐
│              AWS Marketplace Seller Portal                      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Frontend - Next.js 14 + CloudScape UI                  │  │
│  │  • 7-Stage Workflow                                     │  │
│  │  • Real-time Updates                                    │  │
│  │  • AI Chatbot                                           │  │
│  └─────────────────────────────────────────────────────────┘  │
│                           ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Backend - FastAPI Python                               │  │
│  │  • REST API (9 endpoints)                               │  │
│  │  • Agent Orchestration                                  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                           ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  AI Agents - Strands Framework                          │  │
│  │  • Marketplace Agent (8 Sub-Agents)                     │  │
│  │  • Help Agent                                           │  │
│  │  • Claude 3.5 Sonnet                                    │  │
│  └─────────────────────────────────────────────────────────┘  │
│                           ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Amazon Bedrock AgentCore (Future)                      │  │
│  │  Runtime • Gateway • Memory • Identity • Tools • Obs    │  │
│  └─────────────────────────────────────────────────────────┘  │
│                           ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  AWS Services                                           │  │
│  │  Bedrock • Marketplace • CloudFormation • Lambda        │  │
│  │  DynamoDB • S3 • OpenSearch • API Gateway • CloudWatch  │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

4. Use AWS Architecture Icons from: https://aws.amazon.com/architecture/icons/
5. Color scheme:
   - AWS Orange: #FF9900
   - AWS Dark Blue: #232F3E
   - CloudScape Blue: #146EB4
   - Background: White or light gray

6. Export as PNG with name: `marketplace-seller-portal-architecture.png`

### Option 2: Using Mermaid to PNG

1. Use [Mermaid Live Editor](https://mermaid.live/)
2. Paste the Mermaid diagram from README.md
3. Export as PNG
4. Save as `marketplace-seller-portal-architecture.png`

### Option 3: Using AWS Architecture Tool

1. Use [AWS Architecture Icons](https://aws.amazon.com/architecture/icons/)
2. Create diagram in PowerPoint, Visio, or Lucidchart
3. Include:
   - Frontend layer (Next.js)
   - Backend layer (FastAPI)
   - Agent layer (Strands)
   - AgentCore layer (Future)
   - AWS Services layer
4. Export as PNG

## Diagram Requirements

- **Format**: PNG
- **Resolution**: At least 1200x800 pixels
- **File size**: Under 500KB
- **Style**: Clean, professional, AWS-branded
- **Colors**: AWS orange (#FF9900) and dark blue (#232F3E)
- **Icons**: Use official AWS service icons where possible

## Current Status

⚠️ **Placeholder**: The architecture diagram image needs to be created.

The image should be named: `marketplace-listing-architecture.png`

Until the image is created, the text-based architecture diagram in the README.md provides the same information.
