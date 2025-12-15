# Delete and Redeploy Functionality

## Overview

Products with "SaaS Ready" status (completed SaaS integration) now have a "Redeploy" button that allows users to delete the existing CloudFormation stack and deploy a fresh one.

## Implementation

### 1. Seller Registration Page
**File**: `frontend/src/app/seller-registration/page.tsx`

**Added**: "Redeploy" button for products with `saas_integration_status === 'COMPLETED'`

```typescript
{item.saas_integration_status === 'COMPLETED' && (
  <Button
    variant="normal"
    onClick={() => {
      useStore.getState().setProductId(item.product_id);
      useStore.getState().setCurrentStep('saas_deployment');
      router.push(`/saas-integration?productId=${item.product_id}`);
    }}
  >
    Redeploy
  </Button>
)}
```

### 2. SaaS Integration Page
**File**: `frontend/src/app/saas-integration/page.tsx`

**Existing Functionality** (reused):
- Automatically checks if CloudFormation stack exists when user clicks "Deploy Stack"
- Shows delete confirmation alert if stack exists
- Provides "Delete and Redeploy" button to remove existing stack and deploy new one

## Complete Flow

### User Journey

```
┌─────────────────────────────────────────────────────────────┐
│  1. Seller Registration Page                                │
│     - User sees products table                              │
│     - Product with "SaaS Ready" status shows "Redeploy"     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼ Click "Redeploy"
┌─────────────────────────────────────────────────────────────┐
│  2. Navigate to SaaS Integration Page                       │
│     - Product ID passed via URL parameter                   │
│     - Page loads with product context                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼ User clicks "Deploy Stack"
┌─────────────────────────────────────────────────────────────┐
│  3. Check for Existing Stack                                │
│     - Call checkStackExists()                               │
│     - Query CloudFormation for stack with product ID        │
└────────────────────────┬────────────────────────────────────┘
                         │
                    ┌────┴────┐
                    │ Stack   │
                    │ Exists? │
                    └────┬────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼ No            ▼ Yes           │
    ┌─────────┐    ┌──────────────┐     │
    │ Deploy  │    │ Show Delete  │     │
    │ Stack   │    │ Confirmation │     │
    └─────────┘    └──────┬───────┘     │
                          │              │
                          ▼              │
                   ┌──────────────┐      │
                   │ User Chooses │      │
                   └──────┬───────┘      │
                          │              │
              ┌───────────┼──────────┐   │
              │           │          │   │
              ▼           ▼          ▼   │
         ┌────────┐  ┌────────┐  ┌─────┐│
         │ Cancel │  │ Delete │  │     ││
         │        │  │   &    │  │     ││
         │        │  │Redeploy│  │     ││
         └────────┘  └───┬────┘  └─────┘│
                         │               │
                         ▼               │
                   ┌──────────────┐      │
                   │ Delete Stack │      │
                   │ (10 min max) │      │
                   └──────┬───────┘      │
                          │              │
                          ▼              │
                   ┌──────────────┐      │
                   │ Deploy New   │      │
                   │    Stack     │      │
                   └──────────────┘      │
                                         │
                                         │
└────────────────────────────────────────┘
```

## Key Components

### Delete Confirmation Alert

Shows when existing stack is detected:

```typescript
<Alert
  type="warning"
  header="⚠️ Stack Already Exists"
  action={
    <SpaceBetween direction="horizontal" size="xs">
      <Button onClick={() => router.push('/seller-registration')} disabled={deleting}>
        Cancel
      </Button>
      <Button variant="primary" onClick={handleDeleteStack} loading={deleting}>
        Delete and Redeploy
      </Button>
    </SpaceBetween>
  }
>
  <SpaceBetween size="s">
    <Box>A CloudFormation stack with this product ID already exists:</Box>
    <Box fontWeight="bold">{existingStackId}</Box>
    <Box>Would you like to delete the existing stack and deploy a new one?</Box>
    <Box color="text-status-warning" fontSize="body-s">
      ⚠️ Warning: This will delete all existing resources including DynamoDB tables, 
      Lambda functions, and API Gateway endpoints.
    </Box>
  </SpaceBetween>
</Alert>
```

### Delete Handler

```typescript
const handleDeleteStack = async () => {
  setDeleting(true);
  setError('');
  
  try {
    const response = await axios.post('/api/delete-stack', {
      stack_name: existingStackId,
      region: region.value,
      credentials: {
        aws_access_key_id: accessKey,
        aws_secret_access_key: secretKey,
        aws_session_token: sessionToken || undefined,
      },
    });
    
    if (response.data.success) {
      setShowDeleteConfirm(false);
      setDeleting(false);
      // Now proceed with deployment
      await deployStack();
    } else {
      throw new Error(response.data.error || 'Failed to delete stack');
    }
  } catch (err: any) {
    setError(err.response?.data?.error || err.message || 'Failed to delete stack');
    setDeleting(false);
  }
};
```

### Stack Check

```typescript
const checkStackExists = async () => {
  const actualStackName = `saas-integration-${productId}`;
  
  try {
    const response = await axios.post('/api/check-stack-exists', {
      stack_name: actualStackName,
      region: region.value,
      credentials: {
        aws_access_key_id: accessKey,
        aws_secret_access_key: secretKey,
        aws_session_token: sessionToken || undefined,
      },
    });
    
    return response.data;
  } catch (err) {
    console.error('Error checking stack:', err);
    return { exists: false };
  }
};
```

## Backend Endpoints

### `/check-stack-exists`
**Purpose**: Check if a CloudFormation stack exists

**Input**:
- `stack_name`: Name of the stack to check
- `region`: AWS region
- `credentials`: AWS credentials

**Output**:
- `exists`: Boolean indicating if stack exists
- `stack_name`: Name of the stack
- `stack_id`: Full stack ID (if exists)
- `status`: Current stack status (if exists)

### `/delete-stack`
**Purpose**: Delete a CloudFormation stack and wait for completion

**Input**:
- `stack_name`: Name of the stack to delete
- `region`: AWS region
- `credentials`: AWS credentials

**Output**:
- `success`: Boolean indicating if deletion succeeded
- `message`: Status message
- `error`: Error message (if failed)

**Process**:
1. Initiates stack deletion
2. Polls status every 10 seconds
3. Waits up to 10 minutes for completion
4. Returns success when stack is deleted

## Benefits

✅ **Reuses Existing Code**: No duplication, leverages existing delete/deploy logic
✅ **Consistent UX**: Same confirmation flow whether deploying fresh or redeploying
✅ **Safe**: Clear warning about resource deletion
✅ **Automatic**: Seamlessly transitions from delete to deploy
✅ **Simple**: Single button click from products table

## User Experience

1. User sees "SaaS Ready" status on product
2. Clicks "Redeploy" button
3. Navigates to SaaS Integration page
4. Clicks "Deploy Stack" button
5. Sees warning about existing stack
6. Clicks "Delete and Redeploy"
7. Stack is deleted (with progress indication)
8. New stack is automatically deployed
9. User continues with SNS confirmation and buyer experience

## Error Handling

- **Stack deletion timeout**: Shows error after 10 minutes
- **Stack deletion failure**: Shows specific error message
- **Network errors**: Graceful error handling with retry option
- **Permission errors**: Clear error messages about required permissions
