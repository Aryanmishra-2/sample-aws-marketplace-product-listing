# AI Agent Marketplace

An AI-powered assistant system that guides AWS customers through the complete AWS Marketplace SaaS integration process with intelligent error handling and troubleshooting.

## 🚀 Quick Start

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Run the AI Assistant**
```bash
python ai_marketplace_orchestrator.py
```

3. **Provide AWS Credentials**
- Enter your AWS Access Key, Secret Key, and optional Session Token
- The assistant will guide you through the complete workflow

## 🤖 What the Assistant Can Do

### Natural Language Commands:
- "Deploy my SaaS integration"
- "Test metering functionality" 
- "Make my product public"
- "What's my current status?"
- "Help me troubleshoot this error"

### Complete Workflow:
1. **Deploy** CloudFormation template with SaaS integration
2. **Update** fulfillment URL automatically via AWS Marketplace Catalog API
3. **Confirm** SNS subscription for notifications
4. **Test** metering with usage records
5. **Validate** metering success
6. **Request** public visibility

## 🏗️ Architecture

### Core Agents:
- **CreateSaasAgent**: Product configuration
- **ServerlessSaasIntegrationAgent**: CloudFormation deployment
- **MeteringAgent**: Usage tracking and validation
- **PublicVisibilityAgent**: Marketplace visibility management
- **ValidationHelperAgent**: Input validation with Knowledge Base

### AI Components:
- **Bedrock LLM**: Natural language understanding and response generation
- **Knowledge Base**: AWS Marketplace documentation and troubleshooting
- **Orchestrator**: Workflow coordination and state management

## 📋 Prerequisites

### AWS Setup:
1. **Enable Bedrock Models**:
   - Amazon Nova Pro
   - Amazon Titan Text Embeddings V2

2. **Create Knowledge Base** (Optional but recommended):
   - Deploy `knowledge_base_setup.yaml`
   - Upload AWS Marketplace documentation
   - Update `knowledge_base_id` in orchestrator

3. **AWS Credentials**:
   - IAM user with marketplace, CloudFormation, and Catalog API permissions
   - Required permissions: `marketplace-catalog:StartChangeSet`, `marketplace-catalog:DescribeEntity`
   - Temporary credentials recommended for security

## 🔧 Configuration

### Update Product Settings:
Edit `create_saas.py` with your product details:
```python
def get_product_id(self):
    return "your-product-id"

def get_pricing_model_dimension(self):
    return "Contract-based-pricing"  # or Usage-based-pricing

def get_email_dimension(self):
    return "your-email@example.com"
```

### Knowledge Base Integration:
Update `ai_marketplace_orchestrator.py`:
```python
self.knowledge_base_id = "your-actual-kb-id"
```

## 🚦 Usage Examples

### Interactive Session:
```
🤖 AWS Marketplace SaaS Integration Assistant
Enter AWS Access Key: AKIA...
Enter Session Token (optional): 

💬 What would you like to do? Deploy my SaaS integration

🤖 I'll help you deploy your SaaS integration. Starting CloudFormation 
deployment with your product configuration...

✅ Fulfillment URL updated automatically via AWS Marketplace Catalog API

📋 Suggested next actions:
   • Confirm SNS subscription
   • Test metering functionality

📍 Current step: deployment
✅ Completed: None
```

## 🛠️ Error Handling

The assistant provides intelligent error handling:
- **Input Validation**: Real-time format checking with examples
- **AWS API Errors**: Natural language explanation of technical errors
- **Knowledge Base Lookup**: Contextual troubleshooting guidance
- **Retry Mechanisms**: Guided correction with specific instructions

## 📁 File Structure

```
AI_Agent_Marketplace/
├── agents/                           # Core marketplace agents
│   ├── create_saas.py               # Product configuration
│   ├── serverless_saas_integration.py # CloudFormation deployment
│   ├── metering.py                  # Usage tracking
│   ├── public_visibility.py         # Visibility management
│   ├── buyer_experience.py          # Buyer simulation
│   ├── workflow_orchestrator.py     # Complete workflow
│   ├── validation_helper.py         # Input validation
│   └── status_checker.py            # Infrastructure verification
├── bedrock_agent/                   # AI and infrastructure files
│   ├── ai_marketplace_orchestrator.py # Main AI assistant
│   ├── Integration.yaml             # CloudFormation template
│   ├── knowledge_base_setup.yaml    # Knowledge Base infrastructure
│   ├── agent_config.yaml            # Agent configuration
│   └── mcp_config.json              # MCP configuration
├── tests/                           # Test suite
│   ├── test_*.py                    # Individual agent tests
│   └── run_all_tests.py             # Master test runner
└── requirements.txt                 # Dependencies
```

## 🔐 Security

- Uses temporary AWS credentials
- No permanent credential storage
- Least-privilege IAM permissions
- Secure Knowledge Base access

## 📞 Support

For issues or questions:
1. Check the Knowledge Base for troubleshooting guidance
2. Review AWS CloudFormation events for deployment issues
3. Verify IAM permissions for marketplace operations