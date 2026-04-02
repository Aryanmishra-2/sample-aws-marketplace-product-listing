# 🚀 Quick Start Guide

Get your AWS Marketplace Seller Portal running in 3 minutes!

## Prerequisites

- Node.js 18+ installed
- Python 3.8+ installed
- AWS credentials ready

## Step 1: Install Frontend Dependencies

```bash
cd frontend
npm install
```

This will install all required packages including:
- Next.js 14
- AWS Cloudscape components
- Zustand for state management
- Axios for API calls
- TypeScript

## Step 2: Start the Backend

Open a new terminal in the root directory:

```bash
# Install Python dependencies (if not already done)
pip install -r requirements.txt

# Start FastAPI backend
python -m uvicorn backend.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

## Step 3: Start the Frontend

In the frontend directory:

```bash
npm run dev
```

You should see:
```
  ▲ Next.js 14.2.18
  - Local:        http://localhost:3000
  - Ready in 2.1s
```

## Step 4: Open the Application

Open your browser and go to:
```
http://localhost:3000
```

## Step 5: Test the Workflow

### 1. Enter AWS Credentials

> **⚠️ Security Note:** Avoid using long-term access keys (AKIA...) in production.
> Instead, use temporary credentials from [AWS IAM Identity Center (SSO)](https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html)
> or [AWS STS AssumeRole](https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html).
> Temporary credentials include a Session Token and expire automatically, reducing the risk of credential leakage.

- Access Key ID
- Secret Access Key
- Session Token (recommended — required for temporary credentials)
- Click "Validate Credentials"

### 2. Check Seller Status
- View your seller registration status
- See account information
- Click "Start AI-Guided Creation"

### 3. Enter Product Information
- Product website URL (required)
- Documentation URL (optional)
- Product description (optional)
- Click "Continue"

### 4. AI Analysis
- Wait for AI to analyze your product
- Progress bar shows status
- Click "Review Suggestions" when complete

### 5. Review and Edit
- Edit product title (max 72 characters)
- Add logo S3 URL
- Review descriptions and highlights
- Select categories (1-3)
- Add keywords
- Configure support information
- Set pricing model
- Add pricing dimensions
- Configure EULA and availability
- Click "Create Listing"

### 6. Create Listing
- Watch 8-stage workflow execute
- Progress tracked in real-time
- Click "View Results" when complete

### 7. Success!
- View Product ID and Offer ID
- Choose next steps:
  - Deploy SaaS Integration
  - Create Another Listing
  - Go to AWS Portal

## 🎯 Quick Test with Sample Data

### Sample Product Info
```
Website URL: https://example-saas.com
Documentation: https://docs.example-saas.com
Description: A cloud-based project management tool for teams
```

### Sample Logo URL
```
https://your-bucket.s3.amazonaws.com/logo.png
```

### Sample Support Info
```
Email: support@example.com
Fulfillment URL: https://example-saas.com/signup
```

## 🐛 Troubleshooting

### Backend Not Starting
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill process if needed
kill -9 <PID>

# Restart backend
python -m uvicorn backend.main:app --reload --port 8000
```

### Frontend Not Starting
```bash
# Clear Next.js cache
rm -rf .next

# Reinstall dependencies
rm -rf node_modules
npm install

# Start again
npm run dev
```

### API Errors
- Verify backend is running on port 8000
- Check browser console for errors
- Verify AWS credentials are valid
- Check backend logs for errors

### State Not Persisting
- Check browser localStorage is enabled
- Clear browser cache
- Try incognito/private mode

## 📝 Common Commands

### Frontend
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm start            # Start production server
npm run lint         # Run ESLint
```

### Backend
```bash
# Start backend
python -m uvicorn backend.main:app --reload --port 8000

# With specific host
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## 🎨 Features to Try

1. **State Persistence**
   - Fill in credentials
   - Refresh page
   - Data should still be there!

2. **Navigation**
   - Use breadcrumbs to navigate
   - Use back buttons
   - State is preserved

3. **Form Validation**
   - Try submitting empty forms
   - See validation errors
   - Fix and submit

4. **AI Analysis**
   - Watch progress bar
   - See AI-generated content
   - Edit suggestions

5. **Dimension Management**
   - Add pricing dimensions
   - Remove dimensions
   - Validate based on pricing model

## 🚀 Ready to Go!

Your AWS Marketplace Seller Portal is now running!

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

Start creating AWS Marketplace listings with an amazing user experience!

## 📚 Next Steps

1. Read `frontend/README.md` for detailed documentation
2. Check `IMPLEMENTATION_COMPLETE.md` for feature list
3. Review `NEXTJS_MIGRATION_COMPLETE_GUIDE.md` for architecture
4. Test complete workflow end-to-end
5. Deploy to production when ready

## 💡 Pro Tips

- Keep both terminals open (frontend + backend)
- Use browser DevTools to debug
- Check console for errors
- Monitor backend logs
- Save your work frequently

## 🎉 Enjoy!

You're all set! Start creating amazing AWS Marketplace listings with your new modern interface.

---

**Need help?** Check the documentation or review the code comments.
