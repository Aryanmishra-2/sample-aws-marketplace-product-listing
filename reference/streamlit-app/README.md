# Streamlit Reference Implementation

This folder contains the original Streamlit implementation of the AWS Marketplace Seller Portal.

## ⚠️ Note

This is a **reference implementation only**. The main application has been migrated to Next.js with AWS Cloudscape Design System.

## Files

- `streamlit_app_with_seller_registration.py` - Original Streamlit application
- `utils.py` - Utility functions

## Why Migrated?

The application was migrated from Streamlit to Next.js for:

1. **Better UX** - AWS Cloudscape Design System provides authentic AWS Console look
2. **Performance** - Next.js offers better performance and SEO
3. **Scalability** - Modern React architecture is more maintainable
4. **Features** - Better state management, routing, and component reusability
5. **Professional** - Production-ready with TypeScript and modern tooling

## Using the Main Application

See the main README.md in the project root for instructions on running the Next.js application.

## Running This Reference (Not Recommended)

If you need to run the Streamlit version for reference:

```bash
# Install dependencies
pip install streamlit boto3

# Run the app
streamlit run streamlit_app_with_seller_registration.py
```

**Note**: The Streamlit version may not have all the latest features and enhancements.
