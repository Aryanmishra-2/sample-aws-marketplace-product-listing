# AI Agent Marketplace

An AI-powered assistant system that guides AWS customers through the complete AWS Marketplace SaaS integration process with intelligent error handling and troubleshooting.

## 🚀 Quick Start

### Option 1: Streamlit Web UI (Recommended)

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Run the Streamlit App**
```bash
streamlit run streamlit_app_with_seller_registration.py
```

3. **Access the Web Interface**
- Open your browser to `http://localhost:8501`
- Enter your AWS credentials (Access Key, Secret Key, Region)
- The app will automatically detect your seller registration status
- Follow the guided workflow for marketplace listing creation

### Option 2: CLI Assistant

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

### Streamlit Web UI Features:
- **Seller Registration Detection**: Automatically detects if your AWS account is registered as a marketplace seller
- **Three-Scenario Handling**:
  - Not Registered: Guides you through seller registration process
  - Registered without Products: Validates account capabilities before proceeding
  - Registered with Products: Skips validation and proceeds directly to listing creation
- **AI-Guided Listing Creation**: Uses LLMs to generate marketplace listings from product documentation
- **Visual Workflow**: Step-by-step guided interface with progress tracking
- **Credential Management**: Secure AWS credential input with masked fields

### CLI Natural Language Commands:
- "Deploy my SaaS integration"
- "Test metering functionality" 
- "Make my product public"
- "What's my current status?"
- "Help me troubleshoot this error"

### Complete Workflow:
1. **Validate** seller registration status
2. **Deploy** CloudFormation template with SaaS integration
3. **Update** fulfillment URL automatically via AWS Marketplace Catalog API
4. **Confirm** SNS subscription for notifications
5. **Test** metering with usage records
6. **Validate** metering success
7. **Request** public visibility

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
1. **Enable Bedrock Models** (for CLI assistant):
   - Amazon Nova Pro
   - Amazon Titan Text Embeddings V2

2. **Create Knowledge Base** (Optional but recommended for CLI):
   - Deploy `knowledge_base_setup.yaml`
   - Upload AWS Marketplace documentation
   - Update `knowledge_base_id` in orchestrator

3. **AWS Credentials**:
   - IAM user with marketplace, CloudFormation, and Catalog API permissions
   - Required permissions:
     - `marketplace-catalog:StartChangeSet`
     - `marketplace-catalog:DescribeEntity`
     - `marketplace-catalog:ListChangeSets`
     - `marketplace-catalog:ListEntities`
     - `aws-marketplace:DescribeEntity` (for seller registration detection)
   - Temporary credentials recommended for security

### Streamlit App Requirements:
- Python 3.8+
- AWS credentials with marketplace access
- Internet connection for AWS API calls
- Browser for accessing the web interface

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

## 🌐 Streamlit Web UI

### Features:
- **Automatic Seller Detection**: Detects your AWS Marketplace seller registration status
- **Smart Validation**: Three-scenario handling based on registration and product ownership
- **Guided Workflow**: Step-by-step interface for listing creation
- **Secure Credentials**: Masked input fields for AWS credentials
- **Visual Progress**: Clear indication of current step and completion status

### Seller Registration Scenarios:

#### Scenario 1: Not Registered
- **Detection**: Empty changesets AND empty entities
- **Action**: Displays registration guidance with AWS Marketplace Management Portal link
- **Next Steps**: Complete seller registration before proceeding

#### Scenario 2: Registered Without Products
- **Detection**: Has changesets OR entities, but no owned products
- **Action**: Requires manual validation via checkboxes
- **Validation**: Confirms tax info, banking info, and disbursement method
- **Next Steps**: Complete validation to proceed with listing creation

#### Scenario 3: Registered With Products
- **Detection**: Has owned products (verified via EntityArn)
- **Action**: Automatically skips validation
- **Next Steps**: Proceeds directly to listing creation workflow

### Running the App:
```bash
# Activate virtual environment (if using one)
source venv/bin/activate

# Run the Streamlit app
streamlit run streamlit_app_with_seller_registration.py

# Access in browser
# Local: http://localhost:8501
# Network: http://<your-ip>:8501
```

### Stopping the App:
```bash
# Press Ctrl+C in the terminal where Streamlit is running
```

## 🚦 CLI Usage Examples

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
├── streamlit_app_with_seller_registration.py # Web UI (Recommended)
├── agents/                           # Core marketplace agents
│   ├── create_saas.py               # Product configuration
│   ├── serverless_saas_integration.py # CloudFormation deployment
│   ├── metering.py                  # Usage tracking
│   ├── public_visibility.py         # Visibility management
│   ├── buyer_experience.py          # Buyer simulation
│   ├── workflow_orchestrator.py     # Complete workflow
│   ├── validation_helper.py         # Input validation
│   └── status_checker.py            # Infrastructure verification
├── agent/                           # Streamlit app agents
│   ├── orchestrator.py              # Listing workflow orchestrator
│   ├── tools/
│   │   ├── listing_tools.py         # Marketplace listing operations
│   │   └── seller_registration_tools.py # Seller status detection
│   └── sub_agents/
│       └── seller_registration_agent.py # Registration workflow
├── bedrock_agent/                   # AI and infrastructure files
│   ├── ai_marketplace_orchestrator.py # CLI AI assistant
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