# Use Existing Stack Feature

## Overview

When users click "Redeploy" and a stack already exists, they now have three options:
1. **Cancel** - Go back to seller registration
2. **Delete and Redeploy** - Delete existing stack and deploy fresh (10-20 minutes)
3. **Use Existing Stack** - Skip deletion and go directly to SNS confirmation workflow (instant)

## Updated Alert

### Before
```
⚠️ Stack Already Exists

A CloudFormation stack with this product ID already exists:
saas-integration-prod-abc123

Would you like to delete the existing stack and deploy a new one?

⚠️ Warning: This will delete all existing resources...

[Cancel]  [Delete and Redeploy]
```

### After
```
⚠️ Stack Already Exists

A CloudFormation stack with this product ID already exists:
saas-integration-prod-abc123

Choose an option:
• Delete and Redeploy
  Delete the existing stack and deploy a fresh one (10-20 minutes)
  
• Use Existing Stack
  Keep the existing stack and proceed to SNS confirmation and 
  buyer experience workflow (instant)

⚠️ Warning: "Delete and Redeploy" will delete all existing resources...

[Cancel]  [Delete and Redeploy]  [Use Existing Stack →]
```

## Three Options Explained

### Option 1: Cancel
**Action**: Returns to seller registration page
**Use When**: Changed your mind, don't want to proceed

### Option 2: Delete and Redeploy
**Action**: 
1. Deletes existing stack (5-10 minutes)
2. Deploys new stack (5-10 minutes)
3. Shows success alert
4. Proceeds to SNS confirmation workflow

**Use When**:
- Need infrastructure updates
- Stack is in failed state
- Want fresh deployment
- Configuration changes required

**Time**: 10-20 minutes + workflow

### Option 3: Use Existing Stack (NEW)
**Action**:
1. Skips deletion
2. Skips deployment
3. Goes directly to SNS confirmation workflow

**Use When**:
- Stack is already deployed and working
- Want to test buyer experience
- Want to verify metering/visibility
- No infrastructure changes needed

**Time**: Instant + workflow

## Implementation

### Button Handler

```typescript
<Button 
  variant="normal" 
  onClick={() => {
    // Skip deletion, go directly to SNS confirmation workflow
    setShowDeleteConfirm(false);
    setSuccess(true);
    setDeployedStackName(`saas-integration-${productId}`);
    setCurrentSubStep(1);
    setShowSnsConfirmation(true);
  }}
>
  Use Existing Stack →
</Button>
```

### State Changes

When "Use Existing Stack" is clicked:
- `showDeleteConfirm = false` - Hide delete confirmation
- `success = true` - Mark as successful (no deployment needed)
- `deployedStackName = saas-integration-{productId}` - Set stack name
- `currentSubStep = 1` - Move to SNS Confirmation step
- `showSnsConfirmation = true` - Show SNS confirmation alert

## User Flow

### Flow 1: Use Existing Stack (Instant)
```
Click "Redeploy"
    ↓
See delete confirmation alert
    ↓
Click "Use Existing Stack →"
    ↓
SNS Confirmation (instant)
    ↓
Buyer Experience
    ↓
Complete Testing
    ↓
Metering or Visibility Guide
```

### Flow 2: Delete and Redeploy (10-20 min)
```
Click "Redeploy"
    ↓
See delete confirmation alert
    ↓
Click "Delete and Redeploy"
    ↓
Delete stack (5-10 min)
    ↓
Deploy new stack (5-10 min)
    ↓
Show success alert
    ↓
Click "Continue"
    ↓
SNS Confirmation
    ↓
Buyer Experience
    ↓
Complete Testing
    ↓
Metering or Visibility Guide
```

## Sidebar Progress

When "Use Existing Stack" is clicked, sidebar shows:

```
🔧 SaaS Integration
   Deploy Infrastructure
   ● In Progress
   
   ┃ ☁️ Stack Deployment ✓  (Existing stack)
   ┃ 📧 SNS Confirmation ●  (Current)
   ┃ 🛒 Buyer Experience
   ┃ ✅ Testing Complete
```

## Benefits

✅ **Flexibility**: Three clear options for different scenarios
✅ **Time Saving**: Instant access to workflow with existing stack
✅ **Safety**: Clear warning about deletion consequences
✅ **User Choice**: Users decide based on their needs
✅ **Clear Labels**: Descriptive button text and explanations

## Comparison Table

| Feature | Cancel | Delete & Redeploy | Use Existing Stack |
|---------|--------|-------------------|-------------------|
| **Time** | Instant | 10-20 min | Instant |
| **Stack** | No change | Creates new | Uses existing |
| **Data** | Preserved | Deleted | Preserved |
| **Workflow** | None | Full | Full |
| **Use Case** | Changed mind | Infrastructure updates | Testing only |

## Complete Workflow (Options 2 & 3)

Both "Delete and Redeploy" and "Use Existing Stack" lead to the same workflow:

1. **SNS Confirmation** - Confirm email subscription
2. **Buyer Experience** - Follow 8-step guide
3. **Complete Testing** - Run buyer experience agent
4. **Pricing-Based Routing** - Automatic routing
5. **Final Guide** - Metering or Visibility guide

The only difference is:
- **Delete and Redeploy**: Takes 10-20 minutes before workflow
- **Use Existing Stack**: Starts workflow immediately

## Testing

To test the feature:

1. Deploy a stack for a product
2. Go to seller registration page
3. Click "Redeploy" on a SaaS-Ready product
4. See three-option alert
5. Click "Use Existing Stack →"
6. Verify:
   - ✓ Delete confirmation disappears
   - ✓ SNS confirmation appears immediately
   - ✓ Sidebar shows step 1 (SNS Confirmation)
   - ✓ Can proceed through entire workflow
   - ✓ No stack deletion or deployment occurs
