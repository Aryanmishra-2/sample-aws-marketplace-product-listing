# SaaS Integration CloudFormation Issue - Resolution

## Problem Summary

The CloudFormation stack `saas-integration-prod-cyxse6dkyvfo4` failed during deployment with the error:

```
SubscriptionSQSHandlerMySQSEvent: Resource handler returned message: 
"Invalid request provided: AWS::Lambda::EventSourceMapping: The event source arn 
and function name provided mapping already exists."
```

This occurred because an event source mapping already existed between the SQS queue and Lambda function, causing the stack creation to fail and rollback.

## Root Cause

The issue was caused by a duplicate event source mapping that wasn't properly cleaned up from a previous deployment attempt. When CloudFormation tried to create the mapping again, AWS rejected it because it already existed.

## Resolution Steps Taken

### 1. Cleaned Up Failed Stack
```bash
# Deleted the failed stack
aws cloudformation delete-stack \
    --stack-name saas-integration-prod-cyxse6dkyvfo4 \
    --region us-east-1

# Waited for deletion to complete
aws cloudformation wait stack-delete-complete \
    --stack-name saas-integration-prod-cyxse6dkyvfo4 \
    --region us-east-1
```

### 2. Verified Infrastructure Cleanup
Created `check_saas_status.py` script to verify all components were removed:
- CloudFormation stack: ✗ Not found (correctly deleted)
- DynamoDB tables: ✗ Not found (correctly deleted)
- Lambda functions: ✗ Not found (correctly deleted)

### 3. Improved Backend Logging
Updated `backend/main.py` to add better error handling and logging when checking for CloudFormation stacks:
- Added debug logging for stack checks
- Improved error handling to distinguish between "stack not found" vs other errors
- Added handling for DELETE_COMPLETE status

### 4. Created Deployment Tools

#### check_saas_status.py
A diagnostic script that checks:
- CloudFormation stack status
- DynamoDB tables
- Lambda functions
- Provides actionable recommendations

Usage:
```bash
python3 check_saas_status.py prod-cyxse6dkyvfo4 us-east-1
```

#### deploy_saas_integration.sh
An automated deployment script that:
- Checks if stack already exists
- Deploys or updates the CloudFormation stack
- Waits for completion
- Shows stack outputs

Usage:
```bash
# Edit the script to set ADMIN_EMAIL
./deploy_saas_integration.sh
```

Or set environment variable:
```bash
ADMIN_EMAIL="your-email@example.com" ./deploy_saas_integration.sh
```

## Current Status

**SaaS Integration Status: NOT DEPLOYED**

The stack has been completely removed and is ready for a fresh deployment.

## Next Steps to Redeploy

### Option 1: Using the UI (Recommended)
1. Start the backend: `cd backend && uvicorn main:app --reload`
2. Start the frontend: `cd frontend && npm run dev`
3. Navigate to the SaaS Integration page
4. Fill in the required information:
   - Email for SNS notifications
   - AWS credentials
   - Stack name (auto-populated)
5. Click "Deploy Stack 🚀"
6. Monitor the deployment progress in real-time

### Option 2: Using the Deployment Script
1. Edit `deploy_saas_integration.sh` and set your admin email
2. Run: `./deploy_saas_integration.sh`
3. Wait for deployment to complete (~3-5 minutes)
4. Copy the fulfillment URL from the stack outputs

### Option 3: Manual AWS Console Deployment
1. Open AWS CloudFormation console
2. Create new stack
3. Upload `deployment/cloudformation/Integration.yaml`
4. Set parameters:
   - ProductId: `prod-cyxse6dkyvfo4`
   - PricingModel: `Contract-based-pricing` (or your model)
   - MarketplaceTechAdminEmail: Your email
5. Create stack and wait for completion

## How the Orchestrator Works

The workflow orchestrator checks SaaS integration status by:

1. **Backend Check** (`backend/main.py`):
   - Queries CloudFormation for stack: `saas-integration-{product_id}`
   - Checks stack status (CREATE_COMPLETE, IN_PROGRESS, FAILED, etc.)
   - Sets `saas_integration_status` based on findings

2. **Frontend Display** (`frontend/src/app/saas-integration/page.tsx`):
   - Polls `/api/get-stack-status` every 3 seconds during deployment
   - Shows real-time progress with deployment stages
   - Updates UI based on CloudFormation events

3. **Status Mapping**:
   - `CREATE_COMPLETE` → Status: COMPLETED (✓ Ready)
   - `CREATE_IN_PROGRESS` → Status: IN_PROGRESS (⏳ Deploying)
   - `CREATE_FAILED` / `ROLLBACK_COMPLETE` → Status: FAILED (✗ Needs redeployment)
   - Stack not found → Status: PENDING (Deploy required)

## Prevention

To avoid this issue in the future:

1. **Always clean up failed stacks** before redeploying:
   ```bash
   aws cloudformation delete-stack --stack-name <stack-name> --region us-east-1
   ```

2. **Use the status checker** before deploying:
   ```bash
   python3 check_saas_status.py <product-id> us-east-1
   ```

3. **Monitor CloudFormation events** during deployment to catch issues early

4. **Check for orphaned resources** if a stack fails:
   - Event source mappings
   - Lambda functions
   - DynamoDB tables
   - IAM roles

## Verification After Redeployment

After successfully redeploying, verify:

1. **Stack Status**:
   ```bash
   python3 check_saas_status.py prod-cyxse6dkyvfo4 us-east-1
   ```
   Should show: Status: READY

2. **Stack Outputs**:
   - AWSMarketplaceFulfillmentURL
   - LandingPagePreviewURL
   - WebsiteS3Bucket

3. **Infrastructure Components**:
   - DynamoDB tables created
   - Lambda functions deployed
   - API Gateway configured
   - SNS topic created

4. **Frontend Status**:
   - Navigate to the product listing page
   - Should show: `saas_integration_status: COMPLETED`
   - "Configure SaaS" button should be disabled/hidden

## Related Files

- `backend/main.py` - Stack status checking logic
- `frontend/src/app/saas-integration/page.tsx` - Deployment UI
- `agents/workflow_orchestrator.py` - Workflow coordination
- `agents/status_checker.py` - Infrastructure status checks
- `deployment/cloudformation/Integration.yaml` - CloudFormation template
- `check_saas_status.py` - Status diagnostic tool (NEW)
- `deploy_saas_integration.sh` - Automated deployment script (NEW)

## Support

If issues persist:
1. Check CloudFormation console for detailed error messages
2. Review CloudWatch logs for Lambda functions
3. Verify IAM permissions for CloudFormation and related services
4. Run the status checker for detailed diagnostics
5. Check the backend logs for stack checking errors

