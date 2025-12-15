# SaaS Integration Status Detection

## Date: December 2, 2025

## Overview
Enhanced the SaaS integration status detection to accurately reflect whether a product has SaaS infrastructure deployed by checking for the existence of CloudFormation stacks.

## Problem
Previously, the SaaS integration status was only inferred from product visibility:
- DRAFT → PENDING
- LIMITED → REQUIRED
- PUBLIC → COMPLETED

This was inaccurate because:
- A LIMITED product might already have SaaS integration complete
- A PUBLIC product might not have SaaS integration (if it's not a SaaS product)
- There was no way to know if deployment was in progress or failed

## Solution

### Backend Enhancement
Added CloudFormation stack checking to determine actual SaaS integration status:

```python
# Check if CloudFormation stack exists for this product
stack_name = f"saas-integration-{product_id}"
stack_response = cf_client.describe_stacks(StackName=stack_name)
stack_status = stack_response['Stacks'][0]['StackStatus']
```

### Status Values

**PENDING** - SaaS integration not started
- No CloudFormation stack exists
- Product needs SaaS integration
- Action: "Configure SaaS" button shown

**REQUIRED** - SaaS integration needed but not complete
- Product is in LIMITED visibility
- No CloudFormation stack exists
- Must complete before going public
- Action: "Configure SaaS" button shown

**IN_PROGRESS** - SaaS integration deploying
- CloudFormation stack status: CREATE_IN_PROGRESS or UPDATE_IN_PROGRESS
- Infrastructure is being deployed
- Action: Wait for completion

**COMPLETED** - SaaS integration complete
- CloudFormation stack status: CREATE_COMPLETE
- Infrastructure is deployed and ready
- Product can be made public
- Action: "View Console" button shown

**FAILED** - SaaS integration deployment failed
- CloudFormation stack status: CREATE_FAILED or ROLLBACK_COMPLETE
- Deployment encountered errors
- Action: "Configure SaaS" button to retry

### Frontend Display

Status indicators in the product table:
- ✓ **SaaS: Complete** (green) - Ready to use
- ⚠ **SaaS: Required** (orange) - Must configure before public
- ℹ **SaaS: Not Started** (blue) - Can configure anytime
- ⟳ **SaaS: Deploying** (blue, spinning) - In progress
- ✗ **SaaS: Failed** (red) - Deployment error

## Benefits

1. **Accurate Status**: Shows real deployment state, not just inferred from visibility
2. **Better UX**: Users know exactly what action to take
3. **Prevents Confusion**: Clear distinction between "not started" and "required"
4. **Deployment Tracking**: Can see when deployment is in progress
5. **Error Detection**: Shows when deployment failed

## Technical Details

### Stack Naming Convention
CloudFormation stacks are named: `saas-integration-{product_id}`

Example: `saas-integration-prod-lih6cy56chuq4`

### Stack Status Mapping

| CloudFormation Status | SaaS Integration Status |
|----------------------|------------------------|
| CREATE_COMPLETE | COMPLETED |
| CREATE_IN_PROGRESS | IN_PROGRESS |
| UPDATE_IN_PROGRESS | IN_PROGRESS |
| CREATE_FAILED | FAILED |
| ROLLBACK_COMPLETE | FAILED |
| Stack not found | PENDING or REQUIRED |

### Performance Consideration

Checking CloudFormation stacks adds ~100-200ms per product to the list operation. For 20 products, this adds ~2-4 seconds total.

This is acceptable because:
- The check is done in parallel for all products
- It provides accurate, real-time status
- Users only see this page once per session
- The alternative (describe_entity) would be much slower

### Error Handling

If the CloudFormation check fails (permissions, network, etc.):
- Status defaults to PENDING or REQUIRED based on visibility
- No error is shown to user
- Product can still be managed via AWS Console

## Recommendations Logic

Based on the detected status:

**DRAFT + No Stack**
- "Resume listing creation to publish"

**LIMITED + No Stack**
- "Complete SaaS integration before going public"
- Shows "Configure SaaS" button

**LIMITED + Stack Complete**
- "SaaS integration complete - ready for public visibility"
- No "Configure SaaS" button (already done)

**PUBLIC + Stack Complete**
- "Product is live on AWS Marketplace"

## Testing

To test the status detection:

1. **PENDING Status**
   - Create a new SaaS product
   - Don't deploy SaaS integration
   - Should show "SaaS: Not Started"

2. **REQUIRED Status**
   - Publish product to LIMITED
   - Don't deploy SaaS integration
   - Should show "SaaS: Required" with "Configure SaaS" button

3. **IN_PROGRESS Status**
   - Start SaaS deployment
   - Refresh page during deployment
   - Should show "SaaS: Deploying"

4. **COMPLETED Status**
   - Complete SaaS deployment
   - Refresh page
   - Should show "SaaS: Complete"

5. **FAILED Status**
   - Cause deployment to fail (invalid parameters, etc.)
   - Should show "SaaS: Failed" with "Configure SaaS" button to retry

## Future Enhancements

1. **Real-time Updates**: Use WebSocket or polling to update status without page refresh
2. **Stack Details**: Show stack outputs (fulfillment URL, etc.) in the UI
3. **Deployment History**: Track deployment attempts and failures
4. **Auto-retry**: Automatically retry failed deployments
5. **Validation**: Check if fulfillment URL is actually configured in product
