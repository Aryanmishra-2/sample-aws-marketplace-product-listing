# AWS Marketplace Seller Portal

A modern Next.js application with AWS Cloudscape Design System for creating and managing AWS Marketplace SaaS listings with AI-powered assistance.

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+ (for backend)
- AWS Account with Marketplace access
- AWS Credentials (Access Key, Secret Key)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd ai-agent-marketplace
```

2. **Install Backend Dependencies**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install fastapi uvicorn boto3 pydantic
```

3. **Install Frontend Dependencies**
```bash
cd frontend
npm install
```

### Running the Application

1. **Start the Backend** (Terminal 1)
```bash
source venv/bin/activate
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. **Start the Frontend** (Terminal 2)
```bash
cd frontend
npm run dev
```

3. **Access the Application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Health Check: http://localhost:8000/health

## ✨ Features

### 🎨 AWS Standard Design
- Official AWS Cloudscape Design System
- AWS standard colors (Squid Ink, Smile Orange, Pacific Blue)
- Authentic AWS Console look and feel

### 📊 Global Header
- AWS Account ID display
- IAM User Name
- Organization Type (AWS Inc vs AWS India)
- Current Product ID
- Overall Progress Bar (0-100%)

### 🔄 Enhanced Progress Tracking
- **8-Stage Listing Creation** with real-time updates
- **8-Stage CloudFormation Deployment** with detailed progress
- Elapsed time tracking
- Color-coded status indicators
- Individual stage completion times

### 🏢 Seller Registration
- Automatic seller status detection
- Organization type identification
- Existing products listing
- Resume from any stage
- Bedrock agents listing

### 🤖 AI-Powered Features
- Product analysis using Amazon Bedrock
- Automatic content generation
- Pricing model suggestions
- Smart form pre-filling

## 📁 Project Structure

```
ai-agent-marketplace/
├── backend/                    # FastAPI backend
│   └── main.py                # API endpoints
├── frontend/                   # Next.js frontend
│   ├── src/
│   │   ├── app/               # Next.js pages
│   │   │   ├── page.tsx       # Credentials page
│   │   │   ├── welcome/       # Welcome page
│   │   │   ├── product-info/  # Product information
│   │   │   ├── ai-analysis/   # AI analysis
│   │   │   ├── review-suggestions/ # Review & edit
│   │   │   ├── create-listing/     # Listing creation
│   │   │   ├── listing-success/    # Success page
│   │   │   ├── saas-integration/   # SaaS deployment
│   │   │   ├── globals.css    # AWS standard colors
│   │   │   └── layout.tsx     # Root layout
│   │   ├── components/        # React components
│   │   │   ├── GlobalHeader.tsx    # Global header
│   │   │   └── DimensionManager.tsx # Pricing dimensions
│   │   ├── lib/
│   │   │   └── store.ts       # Zustand state management
│   │   └── types/             # TypeScript types
│   ├── package.json
│   └── README.md
├── reference/                  # Reference implementations
│   └── streamlit-app/         # Original Streamlit app
├── venv/                      # Python virtual environment
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```bash
# AWS Configuration (optional - can be entered in UI)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
```

### AWS Permissions Required

Your IAM user/role needs these permissions:
- `sts:GetCallerIdentity` - Validate credentials
- `aws-marketplace:DescribeEntity` - Check seller status
- `aws-marketplace:ListEntities` - List products
- `marketplace-catalog:*` - Manage listings
- `bedrock:InvokeModel` - AI analysis
- `bedrock-agent:ListAgents` - List Bedrock agents
- `cloudformation:*` - Deploy SaaS infrastructure
- `s3:*` - Upload logos and EULAs

## 📖 User Guide

### 1. Enter AWS Credentials
- Provide your AWS Access Key ID and Secret Access Key
- Optional: Session Token for temporary credentials
- System validates credentials and detects organization type

### 2. Check Seller Status
- Automatic detection of seller registration
- View existing products
- See Bedrock agents in your account

### 3. Provide Product Information
- Enter product website URL
- Add documentation URL
- Provide product description

### 4. AI Analysis
- AI analyzes your product
- Generates listing content
- Suggests pricing model

### 5. Review & Edit
- Review AI-generated content
- Edit product title, descriptions
- Configure pricing dimensions
- Set refund policy and EULA
- Configure geographic availability

### 6. Create Listing
- 8-stage automated creation
- Real-time progress updates
- Automatic API calls to AWS Marketplace

### 7. Deploy SaaS Integration (Optional)
- CloudFormation stack deployment
- 8-stage deployment tracking
- Creates DynamoDB, Lambda, API Gateway, SNS

## 🎨 AWS Standard Colors

The application uses official AWS colors:

- **Squid Ink** (#232f3e) - Headers and navigation
- **Smile Orange** (#ff9900) - Primary actions and accents
- **Pacific Blue** (#0073bb) - Progress and info states
- **Success Green** (#037f0c) - Success states
- **Warning Yellow** (#f89406) - Warning states
- **Error Red** (#d13212) - Error states

## 🔐 Security

- No credentials stored permanently
- Credentials only in memory during session
- HTTPS recommended for production
- CORS configured for localhost development
- Sensitive data masked in UI

## 📚 API Endpoints

### Backend API (Port 8000)

- `GET /health` - Health check
- `POST /validate-credentials` - Validate AWS credentials
- `POST /check-seller-status` - Check seller registration
- `POST /list-agents` - List Bedrock agents
- `POST /analyze-product` - AI product analysis
- `POST /generate-content` - Generate listing content
- `POST /suggest-pricing` - Suggest pricing model
- `POST /create-listing` - Create marketplace listing
- `POST /deploy-saas` - Deploy SaaS infrastructure

## 🧪 Development

### Build for Production

```bash
cd frontend
npm run build
npm start
```

### Run Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📦 Dependencies

### Backend
- FastAPI - Modern web framework
- Uvicorn - ASGI server
- Boto3 - AWS SDK
- Pydantic - Data validation

### Frontend
- Next.js 14 - React framework
- AWS Cloudscape - Design system
- Zustand - State management
- Axios - HTTP client
- TypeScript - Type safety

## 🐛 Troubleshooting

### Backend won't start
- Check Python version: `python3 --version`
- Verify dependencies: `pip list`
- Check port 8000 is available

### Frontend won't start
- Check Node version: `node --version`
- Clear cache: `rm -rf .next`
- Reinstall: `rm -rf node_modules && npm install`

### API errors
- Verify AWS credentials are valid
- Check IAM permissions
- Review backend logs
- Check CORS settings

## 📞 Support

For issues or questions:
1. Check the documentation in `frontend/README.md`
2. Review `ENHANCEMENTS_COMPLETE.md` for recent changes
3. See `NEXTJS_MIGRATION_COMPLETE_GUIDE.md` for migration details
4. Check reference Streamlit app in `reference/streamlit-app/`

## 📄 License

[Your License Here]

## 🙏 Acknowledgments

- AWS Cloudscape Design System
- Next.js Team
- AWS Marketplace Team

---

**Note**: The original Streamlit implementation is available in `reference/streamlit-app/` for reference purposes only. The Next.js application is the recommended and actively maintained version.
