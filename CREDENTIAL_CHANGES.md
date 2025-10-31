# AWS Credentials Flow - Updated Implementation

## Summary of Changes

The project has been updated to **require explicit AWS credentials at the start** instead of using environment/config credentials. Both Phase 1 (Listing Creation) and Phase 2 (Infrastructure Deployment) now use the same credentials provided by the user.

## What Changed

### 1. **Streamlit App - New Credentials Screen**
- Added a new `credentials_screen()` as the first step in the workflow
- Users must provide AWS credentials before accessing any features
- Credentials are validated immediately using AWS STS
- Stored securely in session state (browser memory only)

### 2. **Session-Based Authentication**
- Created `boto3.Session` object with user credentials
- Session is passed to all AWS service clients
- No more reliance on environment variables or `~/.aws/credentials`

### 3. **Updated Components**

#### `streamlit_app_complete.py`
- New `credentials_screen()` function for credential input
- Updated `init_session_state()` to start at credentials screen
- New `init_agents_with_credentials()` to initialize agents with session
- Updated `call_bedrock_llm()` to use session-based client
- Added credential status display in sidebar

#### `agent/tools/listing_tools.py`
- Updated `__init__()` to accept and use `boto3.Session`
- Improved `update_credentials()` method
- All Marketplace Catalog API calls now use session-based client

#### `agent/strands_marketplace_agent.py`
- Updated `deploy_aws_integration` tool to use stored session (no parameters needed)
- Updated `execute_marketplace_workflow` tool to use stored session
- Removed credential parameters from Phase 2 tools

#### `agents/serverless_saas_integration.py`
- Added new `deploy_integration_with_session()` method
- Old `deploy_integration()` method kept for backward compatibility
- All boto3 clients now created from session

## New Workflow

```
1. User opens Streamlit app
   ↓
2. Credentials Screen (FIRST STEP - ONLY ONCE)
   - Enter AWS Access Key
   - Enter AWS Secret Key
   - Enter Session Token (optional)
   - Select Region
   - Validate credentials
   ↓
3. Welcome Screen
   - Shows connected AWS account
   - Option to change credentials
   ↓
4. Product Information Gathering
   - Provide product URLs and details
   ↓
5. AI Analysis & Review
   - AI generates listing content
   ↓
6. Create Listing (Phase 1)
   - Uses session-based Marketplace Catalog client
   - Creates limited listing
   ↓
7. Infrastructure Deployment (Phase 2)
   - Uses same session for CloudFormation, Lambda, etc.
   - No need to re-enter credentials
```

**Key Improvement:** Credentials are requested ONLY ONCE at the beginning, not twice!

## Security Improvements

✅ **Explicit credential management** - No hidden credential sources
✅ **Immediate validation** - Credentials tested before proceeding
✅ **Session-only storage** - Credentials never written to disk
✅ **Single source of truth** - Same credentials for all operations
✅ **Temporary credential support** - Session tokens fully supported

## Required Permissions

The provided AWS credentials need these permissions:

**Phase 1 (Listing Creation):**
- `marketplace-catalog:StartChangeSet`
- `marketplace-catalog:DescribeEntity`
- `marketplace-catalog:DescribeChangeSet`
- `bedrock:InvokeModel` (for AI features)

**Phase 2 (Infrastructure Deployment):**
- `cloudformation:*`
- `dynamodb:*`
- `lambda:*`
- `apigateway:*`
- `sns:*`
- `iam:CreateRole`, `iam:AttachRolePolicy`, etc.

## Testing the Changes

1. Start the Streamlit app:
   ```bash
   cd ai-agent-marketplace
   source venv/bin/activate
   streamlit run streamlit_app_complete.py
   ```

2. You'll see the credentials screen first
3. Enter your AWS credentials
4. Click "Validate & Continue"
5. If valid, you'll proceed to the Welcome screen
6. Your credentials are now used for all AWS operations

## Backward Compatibility

The old credential-passing methods are still available but deprecated:
- `deploy_integration(access_key, secret_key, session_token)` - still works
- New preferred method: `deploy_integration_with_session(session)`

## Migration Notes

If you were using environment variables before:
1. Remove `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` from `.env`
2. The app will now prompt for credentials on startup
3. Consider using temporary credentials (with session token) for better security

## Future Enhancements

Potential improvements:
- [ ] Add credential encryption at rest
- [ ] Support AWS SSO login flow
- [ ] Add credential expiration warnings
- [ ] Support multiple AWS profiles
- [ ] Add audit logging for credential usage
