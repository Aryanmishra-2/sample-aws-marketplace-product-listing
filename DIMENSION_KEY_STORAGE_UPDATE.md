# Dimension Key Storage and Usage Enhancement

## Overview
Enhanced the metering system to store and use the exact usage dimension keys that users enter during listing creation, ensuring consistency between user input and metering records.

## Key Changes

### 1. Enhanced Dimension Storage (Backend)
- **File**: `backend/main.py`
- **Enhancement**: Added fallback mechanism to load stored pricing dimensions when not provided in request
- **Location**: `/run-metering` endpoint
- **Behavior**: 
  - First tries to use dimensions from request data
  - If not available, loads from stored file `pricing_dimensions_{product_id}.json`
  - Falls back to marketplace API if neither available
  - **NO HARDCODED DEFAULTS** - metering is skipped if no user dimensions found

### 2. Enhanced Dimension Retrieval (CreateSaaSAgent)
- **File**: `agents/create_saas.py`
- **New Method**: `_load_stored_dimensions()`, `_load_stored_pricing_model()`
- **Enhanced Method**: `get_usage_dimensions()`, `get_pricing_model_dimension()`
- **Dimension Priority Order**:
  1. In-memory dimensions (from create listing process)
  2. Stored dimensions (from file system)
  3. Marketplace API dimensions
  4. **EMPTY LIST** (no hardcoded fallbacks)
- **Pricing Model Priority Order**:
  1. In-memory pricing model
  2. Stored pricing model (from file system)
  3. Marketplace API pricing model
  4. Fallback to "Usage-based-pricing"

### 3. Enhanced Metering Agent
- **File**: `agents/metering.py`
- **New Method**: `_load_stored_dimensions_for_stack()`
- **Enhanced Behavior**:
  - Automatically loads stored dimensions if not already set
  - Extracts product ID from stack name format: `saas-integration-{product_id}`
  - **Skips metering entirely** if no user dimensions found
  - Comprehensive debugging logs to verify dimension source

### 4. Enhanced Metering Records
- **New Fields Added**:
  - `dimension_keys`: String set containing exact dimension keys used
  - `record_source`: Tracks source of dimensions ("user_entered_dimensions" or "marketplace_api_or_storage")
  - `usage_pending`: Indicates actual usage values need to be populated by SaaS application
- **Sample Usage Values**: Uses hardcoded value "10" for testing purposes
- **Enhanced Debugging**: Comprehensive logs showing dimension journey from user input to DynamoDB

## Data Flow

### During Listing Creation
1. User enters pricing dimensions in frontend
2. Backend stores dimensions in `backend/storage/pricing_dimensions_{product_id}.json`
3. File contains:
   ```json
   {
     "product_id": "prod-123",
     "pricing_dimensions": [
       {"key": "api_calls", "name": "API Calls", "type": "Metered"},
       {"key": "users", "name": "Active Users", "type": "Metered"}
     ],
     "pricing_model": "usage",
     "stack_name": "saas-integration-prod-123",
     "timestamp": 1234567890
   }
   ```

### During Metering
1. Metering agent extracts product ID from stack name
2. Loads stored dimensions from file
3. **FILTERS** to only include "Metered" type dimensions (excludes "Entitled" dimensions)
4. **VERIFIES** user-entered metered dimensions are available (skips metering if not)
5. Uses exact user-entered metered dimension keys in metering records
5. Creates DynamoDB record with structure:
   ```json
   {
     "create_timestamp": {"N": "1234567890"},
     "customerIdentifier": {"S": "customer-123"},
     "dimension_usage": {
       "L": [
         {"M": {"dimension": {"S": "api_calls"}, "value": {"N": "10"}}},
         {"M": {"dimension": {"S": "users"}, "value": {"N": "10"}}}
       ]
     },
     "metering_pending": {"S": "true"},
     "dimension_keys": {"SS": ["api_calls", "users"]},
     "record_source": {"S": "user_entered_dimensions"}
   }
   ```
6. **Comprehensive verification logs** confirm dimension keys are properly stored

## Benefits

1. **Consistency**: Exact same dimension keys used throughout the entire workflow
2. **Traceability**: Clear tracking of dimension source and keys used
3. **No Hardcoded Values**: System only uses user-entered dimensions, never defaults
4. **Comprehensive Debugging**: Detailed logs track dimension journey from user input to DynamoDB
5. **Verification**: System confirms dimension keys are properly stored in DynamoDB
6. **Graceful Handling**: Metering is skipped if no user dimensions are available (no fake data)
7. **Persistence**: Dimensions survive across different workflow stages and sessions

## File Locations

- **Storage**: `backend/storage/pricing_dimensions_{product_id}.json`
- **Loading Logic**: `agents/create_saas.py` and `agents/metering.py`
- **Backend Integration**: `backend/main.py` `/run-metering` endpoint

## Testing & Verification

The system now ensures that:
- **NO hardcoded dimension values** are ever used in DynamoDB records
- **Hardcoded usage values** of "10" for testing purposes in DynamoDB records
- **ONLY "Metered" type dimensions** are used for metering (excludes "Entitled" dimensions)
- **User-entered pricing model** is preserved and used (not hardcoded "Usage-based-pricing")
- User-entered metered dimension keys like "api_calls", "users", "storage_gb" are preserved exactly
- Metering records use ONLY the metered keys and pricing model the user originally entered
- **Comprehensive debugging logs** show:
  - Source of dimensions (user-entered vs marketplace API)
  - Original user dimension names and converted keys
  - Final dimension keys stored in DynamoDB
  - Verification that keys were successfully stored
- System **skips metering entirely** if no user dimensions are found (no fake data)
- All dimension usage is logged for debugging and verification

## Debug Log Example

```
[METERING AGENT] ===== DIMENSION DEBUGGING =====
[METERING AGENT] → Total dimensions found: 2
[METERING AGENT] → ✓ Dimensions source: USER-ENTERED during listing creation
[METERING AGENT] → Original user dimensions:
[CREATE_SAAS] → ✓ Added METERED dimension: api_calls (name: API Calls)
[CREATE_SAAS] → ✗ Skipped NON-METERED dimension: Users (type: Entitled)
[METERING AGENT] → Final METERED dimension keys for DynamoDB:
[METERING AGENT]     1. 'api_calls' (will be stored in DynamoDB)
[METERING AGENT] ===== END DIMENSION DEBUGGING =====

[METERING AGENT] → VERIFICATION: Dimension keys stored in DynamoDB:
[METERING AGENT]     1. 'api_calls' ✓ CONFIRMED in DynamoDB
[METERING AGENT] ✓ SUCCESS: User-entered METERED dimension keys are properly stored in DynamoDB!
```