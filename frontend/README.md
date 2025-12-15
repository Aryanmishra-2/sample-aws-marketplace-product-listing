# AWS Marketplace Seller Portal - Next.js Frontend

Modern, user-friendly interface for AWS Marketplace seller registration and listing creation, built with Next.js and AWS Cloudscape Design System.

## 🎯 Features

- **Complete Workflow**: From AWS credentials to listing creation
- **AI-Powered**: Automatic content generation using Amazon Bedrock
- **AWS Cloudscape**: Authentic AWS Console design
- **Type-Safe**: Full TypeScript support
- **State Management**: Persistent state with Zustand
- **Responsive**: Works on all screen sizes

## 📋 Prerequisites

- Node.js 18+ and npm
- FastAPI backend running on port 8000
- AWS credentials with appropriate permissions

## 🚀 Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

The application will be available at http://localhost:3000

### 3. Start Backend (Required)

In the root directory:

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── app/                          # Next.js App Router pages
│   │   ├── page.tsx                  # Credentials page (/)
│   │   ├── welcome/                  # Welcome page
│   │   ├── product-info/             # Product information
│   │   ├── ai-analysis/              # AI analysis progress
│   │   ├── review-suggestions/       # Review & edit
│   │   ├── create-listing/           # Listing creation
│   │   ├── listing-success/          # Success page
│   │   ├── saas-integration/         # SaaS deployment
│   │   └── api/                      # API routes
│   │       ├── validate-credentials/
│   │       ├── check-seller-status/
│   │       ├── analyze-product/
│   │       ├── generate-content/
│   │       ├── suggest-pricing/
│   │       ├── create-listing/
│   │       └── deploy-saas/
│   ├── components/                   # Reusable components
│   │   └── DimensionManager.tsx      # Pricing dimensions
│   ├── lib/
│   │   ├── store.ts                  # Zustand store
│   │   └── utils.ts                  # Utilities
│   └── types/
│       └── workflow.ts               # TypeScript types
├── package.json
├── tsconfig.json
└── next.config.js
```

## 🔄 Complete Workflow

### 1. Credentials (`/`)
- Enter AWS credentials
- Validate account
- Check seller status

### 2. Welcome (`/welcome`)
- View seller status
- Start listing creation

### 3. Product Info (`/product-info`)
- Enter product URLs
- Provide description

### 4. AI Analysis (`/ai-analysis`)
- AI analyzes product
- Generates content
- Suggests pricing

### 5. Review Suggestions (`/review-suggestions`)
- Edit product title (max 72 chars)
- Configure logo, descriptions
- Set highlights (1-3)
- Select categories (1-3)
- Add keywords
- Configure support info
- Set pricing model
- Add dimensions
- Configure EULA
- Set availability
- Auto-publish option

### 6. Create Listing (`/create-listing`)
- Execute 8-stage workflow
- Track progress
- Handle errors

### 7. Success (`/listing-success`)
- View product/offer IDs
- Next steps guide
- Deploy SaaS option

### 8. SaaS Integration (`/saas-integration`)
- Deploy CloudFormation
- Configure SNS
- Monitor deployment

## 🎨 AWS Cloudscape Components

### Used Components
- `AppLayout` - Main layout
- `ContentLayout` - Page content
- `Container` - Content sections
- `Header` - Page/section headers
- `Form` - Form wrapper
- `FormField` - Form fields
- `Input` - Text input
- `Textarea` - Multi-line input
- `Select` - Dropdown
- `Multiselect` - Multiple selection
- `Button` - Action buttons
- `Alert` - Notifications
- `ProgressBar` - Progress tracking
- `BreadcrumbGroup` - Navigation
- `SpaceBetween` - Layout spacing
- `ColumnLayout` - Multi-column
- `Box` - Generic container
- `Checkbox` - Checkboxes
- `ExpandableSection` - Collapsible sections
- `Spinner` - Loading indicator
- `Link` - External links

## 🔧 State Management

### Zustand Store

```typescript
{
  // Authentication
  isAuthenticated: boolean
  credentials: Credentials | null
  sessionId: string | null
  
  // Seller Status
  sellerStatus: SellerStatus | null
  
  // Workflow
  currentStep: WorkflowStep
  completedSteps: WorkflowStep[]
  
  // Product Context
  productContext: ProductContext | null
  
  // Analysis
  analysisResult: AnalysisResult | null
  
  // Listing
  listingData: AnalysisResult | null
  productId: string | null
  
  // Deployment
  stackId: string | null
  deploymentStatus: string | null
}
```

## 🌐 API Routes

All API routes proxy to the FastAPI backend on port 8000:

- `POST /api/validate-credentials` - Validate AWS credentials
- `POST /api/check-seller-status` - Check seller registration
- `POST /api/analyze-product` - AI product analysis
- `POST /api/generate-content` - Generate listing content
- `POST /api/suggest-pricing` - Suggest pricing model
- `POST /api/create-listing` - Create marketplace listing
- `POST /api/deploy-saas` - Deploy SaaS infrastructure

## 🔐 Security

- Credentials stored in session storage (not localStorage)
- API routes validate all inputs
- HTTPS required for production
- No credentials in client-side code

## 🧪 Testing

### Manual Testing Checklist

1. **Credentials Flow**
   - [ ] Enter valid credentials
   - [ ] Validate credentials
   - [ ] Check seller status
   - [ ] Clear data works

2. **Product Info**
   - [ ] Enter website URL
   - [ ] Add optional URLs
   - [ ] Provide description
   - [ ] Navigate back/forward

3. **AI Analysis**
   - [ ] Analysis starts automatically
   - [ ] Progress updates
   - [ ] Results displayed
   - [ ] Re-analyze works

4. **Review Suggestions**
   - [ ] All fields populated
   - [ ] Edit product title (72 char limit)
   - [ ] Add dimensions
   - [ ] Select pricing model
   - [ ] Validate form

5. **Create Listing**
   - [ ] 8 stages execute
   - [ ] Progress tracking
   - [ ] Error handling
   - [ ] Success display

6. **Success Page**
   - [ ] Product ID shown
   - [ ] Links work
   - [ ] Deploy SaaS option

7. **SaaS Integration**
   - [ ] Form validation
   - [ ] Deployment works
   - [ ] Stack ID returned

## 🐛 Troubleshooting

### Backend Not Responding
```bash
# Check if backend is running
curl http://localhost:8000/health

# Start backend
python -m uvicorn backend.main:app --reload --port 8000
```

### State Not Persisting
- Check browser localStorage is enabled
- Clear browser cache
- Check Zustand persist middleware

### Cloudscape Styles Not Loading
- Verify `@cloudscape-design/global-styles` imported in layout.tsx
- Check CSS import order
- Clear Next.js cache: `rm -rf .next`

### API Errors
- Check FastAPI backend logs
- Verify API route paths
- Check CORS settings
- Validate request/response formats

## 📚 Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [AWS Cloudscape](https://cloudscape.design/)
- [Zustand](https://github.com/pmndrs/zustand)
- [TypeScript](https://www.typescriptlang.org/)
- [AWS Marketplace Seller Guide](https://docs.aws.amazon.com/marketplace/latest/userguide/)

## 🚀 Production Deployment

### Build for Production

```bash
npm run build
```

### Start Production Server

```bash
npm start
```

### Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=https://your-backend-api.com
```

### Deployment Platforms

- **Vercel**: `vercel deploy`
- **AWS Amplify**: Connect GitHub repo
- **Docker**: Use provided Dockerfile
- **Self-hosted**: Build and run with Node.js

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## 📧 Support

For issues or questions:
- GitHub Issues
- AWS Marketplace Seller Support
- Documentation

---

**Built with ❤️ using Next.js and AWS Cloudscape**
