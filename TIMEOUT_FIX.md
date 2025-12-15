# Stack Deletion Timeout Fix

## Problem

The frontend was timing out while waiting for CloudFormation stack deletion to complete. The backend was blocking for up to 10 minutes waiting for deletion, causing the HTTP request to timeout.

## Solution

Changed from **synchronous blocking** to **asynchronous polling** pattern:

### Before (Blocking)
```
Frontend → API Route → Backend (waits 10 min) → Response
                           ↓
                      TIMEOUT ❌
```

### After (Non-Blocking + Polling)
```
Frontend → API Route → Backend (initiates deletion) → Response ✓
    ↓
    Poll every 5s → Check status → DELETE_COMPLETE ✓
    ↓
    Auto-deploy new stack
```

## Changes Made

### 1. Backend (`backend/main.py`)

**Before:**
```python
# Wait for deletion to complete (with timeout)
max_wait = 600  # 10 minutes
while elapsed < max_wait:
    # Check status and wait...
    time.sleep(10)
```

**After:**
```python
# Initiate stack deletion (non-blocking)
cf_client.delete_stack(StackName=stack_name)

# Return immediately
return {
    "success": True, 
    "message": "Stack deletion initiated",
    "stack_name": stack_name,
    "status": "DELETE_IN_PROGRESS"
}
```

### 2. Frontend (`saas-integration/page.tsx`)

**Added polling logic:**
```typescript
const handleDeleteStack = async () => {
  // 1. Initiate deletion (returns immediately)
  const response = await axios.post('/api/delete-stack', {...});
  
  // 2. Poll for completion
  let deleteComplete = false;
  let pollCount = 0;
  const maxPolls = 120; // 10 minutes at 5s intervals
  
  while (!deleteComplete && pollCount < maxPolls) {
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    const statusResponse = await axios.post('/api/get-stack-status', {...});
    
    if (status === 'DELETE_COMPLETE' || status === 'NOT_FOUND') {
      deleteComplete = true;
    }
  }
  
  // 3. Auto-deploy new stack
  await deployStack();
};
```

### 3. API Route (`api/delete-stack/route.ts`)

**Created new route with short timeout:**
```typescript
// Short timeout since deletion is now non-blocking
const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 seconds

const response = await fetch('http://localhost:8000/delete-stack', {
  method: 'POST',
  body: JSON.stringify({ stack_name, region, credentials }),
  signal: controller.signal,
});
```

### 4. UI Feedback

**Added deletion progress indicator:**
```typescript
{deleting && (
  <Alert type="info" header="🗑️ Deleting Existing Stack">
    <Spinner size="large" />
    <Box>Deleting CloudFormation stack: {existingStackId}</Box>
    <Box>This may take 5-10 minutes...</Box>
    <Box>Once deletion is complete, a new stack will be deployed automatically.</Box>
  </Alert>
)}
```

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  1. User clicks "Delete and Redeploy"                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Frontend: Initiate Deletion                             │
│     POST /api/delete-stack                                  │
│     ↓                                                        │
│     Backend: cf_client.delete_stack()                       │
│     ↓                                                        │
│     Returns immediately: "DELETE_IN_PROGRESS"               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Frontend: Show Deletion Progress                        │
│     - Hide delete confirmation                              │
│     - Show spinner with message                             │
│     - "Deleting stack... 5-10 minutes"                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Frontend: Poll for Status (every 5 seconds)             │
│     ┌─────────────────────────────────────┐                │
│     │ POST /api/get-stack-status          │                │
│     │ ↓                                    │                │
│     │ Check: DELETE_IN_PROGRESS?          │                │
│     │   Yes → Wait 5s, check again        │                │
│     │   No  → Continue                    │                │
│     └─────────────────────────────────────┘                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Deletion Complete                                       │
│     Status: DELETE_COMPLETE or NOT_FOUND                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Frontend: Auto-Deploy New Stack                         │
│     await deployStack()                                     │
│     ↓                                                        │
│     Show deployment progress                                │
│     ↓                                                        │
│     Poll for CREATE_COMPLETE                                │
└─────────────────────────────────────────────────────────────┘
```

## Benefits

✅ **No Timeouts**: Backend returns immediately, no long-running HTTP requests
✅ **Better UX**: User sees progress indicator during deletion
✅ **Automatic**: Seamlessly transitions from delete to deploy
✅ **Resilient**: Handles network errors gracefully with retry logic
✅ **Scalable**: Can handle long-running operations without blocking

## Timeout Settings

| Component | Timeout | Purpose |
|-----------|---------|---------|
| Backend `/delete-stack` | None | Returns immediately |
| API Route `/api/delete-stack` | 30s | Just initiates deletion |
| Frontend polling | 10 min | Waits for DELETE_COMPLETE |
| Poll interval | 5s | Check status frequency |

## Error Handling

1. **Deletion Timeout (10 min)**: Shows error, allows retry
2. **Deletion Failed**: Shows error with reason
3. **Network Error**: Continues polling (doesn't fail immediately)
4. **Stack Not Found**: Treats as successful deletion

## Testing

To test the fix:

1. Deploy a stack for a product
2. Click "Redeploy" from products table
3. Click "Delete and Redeploy"
4. Observe:
   - ✓ Delete confirmation disappears
   - ✓ Deletion progress indicator appears
   - ✓ No timeout errors
   - ✓ After 5-10 minutes, deletion completes
   - ✓ New stack deployment starts automatically
   - ✓ Deployment progress shown
   - ✓ Success message after completion

## Architecture Pattern

This implements the **Long-Running Operation Pattern**:

1. **Initiate**: Start operation, return immediately with operation ID
2. **Poll**: Client polls for status at regular intervals
3. **Complete**: Operation completes, client receives final status
4. **Next Action**: Automatically trigger next step in workflow

This pattern is commonly used for:
- CloudFormation stack operations
- Database migrations
- Large file uploads/processing
- Batch job execution
- Any operation taking > 30 seconds
