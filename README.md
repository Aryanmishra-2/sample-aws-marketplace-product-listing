# AWS Marketplace Seller Portal

A modern, AI-powered web application for AWS Marketplace sellers to create and manage product listings with intelligent automation.

## 🚀 Features

### Core Capabilities
- **AI-Powered Product Analysis** - Analyze product websites and documentation using Amazon Bedrock
- **Intelligent Content Generation** - Auto-generate listing titles, descriptions, and highlights
- **Smart Pricing Recommendations** - Get AI-suggested pricing models and dimensions
- **Real-Time CloudFormation Monitoring** - Track SaaS infrastructure deployment with live updates
- **Seller Registration** - Check seller status and manage AWS Marketplace accounts
- **Complete Listing Workflow** - End-to-end product listing creation with validation

### Technical Features
- **Next.js 14** with App Router and Server Components
- **AWS Cloudscape Design System** for consistent AWS UI/UX
- **FastAPI Backend** with Python 3.13
- **Amazon Bedrock Integration** for AI capabilities
- **AWS SDK Integration** for Marketplace and CloudFormation APIs
- **Real-time Status Updates** with polling and event tracking
- **Type-Safe** with TypeScript

## 📋 Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.13+
- **AWS Account** with appropriate permissions
- **AWS Credentials** (Access Key, Secret Key, optional Session Token)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd ai-agent-marketplace
```

### 2. Backend Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r reference/streamlit-app/requirements.txt
```

### 3. Frontend Setup
```bash
cd frontend
npm install
```

### 4. Environment Configuration
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration (if needed)
```

## 🚀 Running the Application

### Start Backend Server
```bash
# From project root
cd backend
../venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`

### Start Frontend Development Server
```bash
# From project root
cd frontend
npm run dev
```

Frontend will be available at: `http://localhost:3000`

## 📖 Usage Guide

### 1. Authentication
- Enter your AWS credentials (Access Key, Secret Key, optional Session Token)
- System validates credentials and checks seller registration status

### 2. Product Information
- Provide product website URL and documentation
- AI analyzes your product and extracts key information

### 3. AI Analysis
- Review AI-generated product analysis
- Edit and refine the analysis as needed

### 4. Content Generation
- AI generates listing content (title, descriptions, highlights)
- Review and customize generated content

### 5. Pricing Configuration
- Get AI-recommended pricing model
- Configure pricing dimensions and contract durations
- Set up refund policy and EULA

### 6. Review & Submit
- Review all listing details
- Submit to create AWS Marketplace listing
- Get Product ID and Offer ID

### 7. SaaS Integration (Optional)
- Deploy serverless infrastructure for SaaS products
- Real-time CloudFormation deployment monitoring
- Track resource creation and handle failures

## 🏗️ Architecture

### Frontend (Next.js)
```
frontend/
├── src/
│   ├── app/              # App Router pages
│   │   ├── page.tsx      # Home/Login
│   │   ├── welcome/      # Welcome page
│   │   ├── product-info/ # Product input
│   │   ├── ai-analysis/  # AI analysis
│   │   ├── create-listing/ # Content generation
│   │   ├── review-suggestions/ # Pricing & review
│   │   ├── listing-success/ # Success page
│   │   └── saas-integration/ # SaaS deployment
│   ├── components/       # Reusable components
│   ├── lib/             # Utilities and store
│   └── types/           # TypeScript types
```

### Backend (FastAPI)
```
backend/
└── main.py              # FastAPI application with endpoints
```

### Reference Implementation
```
reference/streamlit-app/
├── agent/               # Marketplace agent system
├── agents/              # Specialized agents
└── config/              # Configuration files
```

## 🔌 API Endpoints

### Backend API (`http://localhost:8000`)

- `GET /health` - Health check
- `POST /validate-credentials` - Validate AWS credentials
- `POST /check-seller-status` - Check seller registration
- `POST /list-agents` - List Bedrock agents
- `POST /analyze-product` - AI product analysis
- `POST /generate-content` - Generate listing content
- `POST /suggest-pricing` - Get pricing recommendations
- `POST /create-listing` - Create marketplace listing
- `POST /deploy-saas` - Deploy SaaS infrastructure
- `POST /get-stack-status` - Get CloudFormation status

## 🔧 Configuration

### AWS Permissions Required

The AWS credentials need permissions for:
- **AWS Marketplace Catalog API** - Create and manage listings
- **Amazon Bedrock** - AI model access (Claude 3.5 Sonnet)
- **AWS CloudFormation** - Deploy SaaS infrastructure
- **AWS STS** - Validate credentials
- **IAM** - Create roles for SaaS integration
- **DynamoDB** - Create tables for subscriptions
- **Lambda** - Deploy metering functions
- **API Gateway** - Create fulfillment APIs
- **SNS** - Configure notifications

### Bedrock Models Used
- `us.anthropic.claude-3-5-sonnet-20241022-v2:0` (primary)
- `anthropic.claude-3-5-sonnet-20240620-v1:0` (fallback)
- `anthropic.claude-3-sonnet-20240229-v1:0` (fallback)

## 🐛 Troubleshooting

### Backend Issues
```bash
# Check backend logs
tail -f /tmp/backend.log

# Restart backend
pkill -f "uvicorn main:app"
cd backend && ../venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend Issues
```bash
# Clear Next.js cache
cd frontend
rm -rf .next
npm run dev
```

### Common Issues

1. **Port Already in Use**
   ```bash
   # Kill process on port 8000
   lsof -ti:8000 | xargs kill -9
   
   # Kill process on port 3000
   lsof -ti:3000 | xargs kill -9
   ```

2. **Bedrock Access Denied**
   - Ensure your AWS account has Bedrock enabled
   - Request model access in AWS Console (Bedrock > Model access)

3. **CloudFormation Deployment Fails**
   - Check AWS credentials have CloudFormation permissions
   - Verify region supports all required services
   - Review CloudFormation events in the UI

## 📚 Documentation

- `PROJECT_STRUCTURE.md` - Detailed project structure
- `DEPLOYMENT_SUMMARY.md` - Deployment guide
- `SAAS_STATUS_FIXES.md` - SaaS monitoring implementation
- `frontend/QUICK_START.md` - Frontend quick start guide
- `frontend/README.md` - Frontend documentation

## 🔐 Security Notes

- Never commit AWS credentials to version control
- Use IAM roles with least privilege principle
- Rotate credentials regularly
- Use session tokens for temporary access
- Review CloudFormation templates before deployment

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## 📝 License

[Your License Here]

## 🆘 Support

For issues and questions:
- Check the troubleshooting section
- Review documentation files
- Check AWS service status
- Verify credentials and permissions

## 🎯 Roadmap

- [ ] Multi-region support
- [ ] Batch listing creation
- [ ] Advanced analytics dashboard
- [ ] Listing templates
- [ ] Automated testing suite
- [ ] Docker containerization
- [ ] CI/CD pipeline

---

Built with ❤️ using Next.js, FastAPI, and AWS Services
