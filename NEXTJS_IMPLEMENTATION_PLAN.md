# Next.js + AWS Cloudscape Implementation Plan

## Overview
Complete migration of Streamlit AWS Marketplace Seller Registration app to Next.js with AWS Cloudscape Design System.

## Complete Workflow Steps

### 1. AWS Credentials & Validation
- Input AWS credentials (Access Key, Secret Key, Session Token)
- Validate credentials and determine organization (AWS Inc vs AWS India)
- Check seller registration status
- Display account information

### 2. Seller Registration (if needed)
- Business profile creation
- Tax information (W-9/W-8)
- Banking information
- Payment setup
- Verification workflow

### 3. Product Information Gathering
- Product website URL
- Documentation URL
- Pricing page URL
- Product description

### 4. AI Analysis
- Analyze product using Bedrock
- Generate product title, descriptions
- Suggest pricing models
- Generate highlights and keywords

### 5. Review & Edit Suggestions
- Edit product title (max 72 chars)
- Logo S3 URL
- Short/long descriptions
- Highlights (1-3)
- Categories (1-3)
- Search keywords
- Support information
- Pricing model selection
- Pricing dimensions
- Contract durations
- Refund policy
- EULA configuration
- Geographic availability
- Account allowlist

### 6. Create Listing
- Execute 8-stage workflow
- Create product
- Add fulfillment
- Configure pricing
- Set refund policy
- Configure EULA
- Set availability
- Configure allowlist
- Auto-publish to Limited (optional)

### 7. SaaS Integration (Optional)
- Deploy CloudFormation template
- Configure SNS notifications
- Set up Lambda functions
- Configure DynamoDB tables

### 8. Complete Workflow (Optional)
- Update fulfillment URL
- Test buyer experience
- Configure usage metering
- Submit for public visibility

## Technology Stack
- **Framework**: Next.js 14 (App Router)
- **UI Library**: AWS Cloudscape Design System
- **State Management**: React Context + Local Storage
- **API**: Next.js API Routes
- **Backend Integration**: Python FastAPI (existing)
- **Styling**: Cloudscape + Tailwind CSS

## Project Structure
```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx                 # Root layout with Cloudscape
│   │   ├── page.tsx                   # Home/Credentials page
│   │   ├── seller-registration/
│   │   │   └── page.tsx              # Seller registration form
│   │   ├── product-info/
│   │   │   └── page.tsx              # Product information input
│   │   ├── ai-analysis/
│   │   │   └── page.tsx              # AI analysis progress
│   │   ├── review-suggestions/
│   │   │   └── page.tsx              # Review & edit AI suggestions
│   │   ├── create-listing/
│   │   │   └── page.tsx              # Listing creation progress
│   │   ├── listing-success/
│   │   │   └── page.tsx              # Success page with next steps
│   │   ├── saas-integration/
│   │   │   └── page.tsx              # SaaS deployment
│   │   └── workflow-orchestrator/
│   │       └── page.tsx              # Complete workflow
│   ├── components/
│   │   ├── Navigation.tsx            # Top navigation with breadcrumbs
│   │   ├── ProgressIndicator.tsx    # Workflow progress sidebar
│   │   ├── CredentialsForm.tsx      # AWS credentials input
│   │   ├── ProductForm.tsx          # Product information form
│   │   ├── PricingConfig.tsx        # Pricing configuration
│   │   ├── DimensionManager.tsx     # Pricing dimensions manager
│   │   └── StatusChecker.tsx        # Seller status checker
│   ├── contexts/
│   │   ├── WorkflowContext.tsx      # Global workflow state
│   │   └── CredentialsContext.tsx   # AWS credentials state
│   ├── lib/
│   │   ├── api.ts                   # API client functions
│   │   ├── validation.ts            # Form validation
│   │   └── utils.ts                 # Utility functions
│   └── types/
│       ├── workflow.ts              # Workflow types
│       ├── listing.ts               # Listing types
│       └── api.ts                   # API response types
├── public/
│   └── aws-logo.svg
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── next.config.js
```

## Key Features to Maintain

### 1. State Management
- Persist workflow state across page refreshes
- Store credentials securely (session storage)
- Track progress through workflow
- Handle back/forward navigation

### 2. Form Validation
- Real-time validation
- AWS-specific constraints (72 char title, etc.)
- Required field indicators
- Error messages

### 3. API Integration
- Call existing Python backend
- Handle async operations
- Progress indicators
- Error handling

### 4. User Experience
- Clear navigation
- Progress tracking
- Helpful tooltips
- Contextual help
- Success/error feedback

### 5. AWS Cloudscape Components
- AppLayout for consistent structure
- Form components (Input, Select, Textarea)
- Button variants (primary, normal)
- Alert for notifications
- Modal for confirmations
- SpaceBetween for layout
- Container for sections
- Header for page titles
- Breadcrumbs for navigation
- ProgressBar for loading states

## Implementation Phases

### Phase 1: Project Setup & Core Layout
- Initialize Next.js project
- Install Cloudscape dependencies
- Create root layout with Cloudscape
- Set up routing structure
- Create workflow context

### Phase 2: Credentials & Validation
- Credentials input form
- AWS validation
- Seller status checker
- Account information display

### Phase 3: Product Information & AI Analysis
- Product info form
- AI analysis integration
- Progress indicators
- Results display

### Phase 4: Review & Configuration
- Editable suggestions
- Pricing configuration
- Dimension management
- EULA & availability settings

### Phase 5: Listing Creation
- Multi-stage workflow execution
- Progress tracking
- Error handling
- Success page

### Phase 6: Advanced Features
- SaaS integration
- Workflow orchestrator
- Testing tools
- Analytics

## Next Steps
1. Create Next.js project structure
2. Install dependencies
3. Implement core components
4. Build page-by-page
5. Integrate with backend
6. Test complete workflow
7. Polish UI/UX
