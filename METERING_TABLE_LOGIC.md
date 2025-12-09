# Metering Agent Table Logic

## Overview

The MeteringAgent now correctly searches for DynamoDB tables by keywords only, without filtering by product ID. This ensures it finds the correct tables regardless of the naming convention used by CloudFormation.

## Table Search Logic

### Tables Required

1. **NewSubscribers** - Contains customer identifiers from buyer subscriptions
2. **AWSMarketplaceMeteringRecords** - Stores metering records to be reported to AWS Marketplace

### Search Algorithm

```python
# Search for tables by keywords only (not by product ID)
for table in tables:
    # Look for NewSubscribers table (to get customer identifier)
    if 'NewSubscribers' in table and not subscribers_table:
        subscribers_table = table
        print(f"[METERING AGENT] ✓ Found NewSubscribers table: {table}")
    
    # Look for AWSMarketplaceMeteringRecords table (to insert metering records)
    if 'AWSMarketplaceMeteringRecords' in table and not metering_table:
        metering_table = table
        print(f"[METERING AGENT] ✓ Found metering table: {table}")
```

## Workflow

### Step 1: Locate Tables
- Search all DynamoDB tables
- Find table containing "NewSubscribers" keyword
- Find table containing "AWSMarketplaceMeteringRecords" keyword

### Step 2: Get Customer Identifier
- Scan the **NewSubscribers** table
- Retrieve `customerIdentifier` from the first item
- If no customers exist, create a test customer

### Step 3: Prepare Metering Record
- Get usage dimensions from product configuration
- Create metering record with:
  - `create_timestamp`: Current timestamp
  - `customerIdentifier`: From NewSubscribers table
  - `dimension_usage`: Array of dimensions with usage values
  - `metering_pending`: "true" (will be processed by Lambda)

### Step 4: Insert Metering Record
- Insert the record into **AWSMarketplaceMeteringRecords** table
- Record includes `metering_pending: "true"` flag

### Step 5: Verify Metering Record
- Query the table to find the inserted record
- Verify `metering_pending` is set to "true"
- Confirm record is ready for Lambda processing
- Lambda function will process records hourly
- Lambda calls BatchMeterUsage API to report to AWS Marketplace

## Table Purposes

### NewSubscribers Table
**Purpose:** Stores customer subscription information

**Used For:**
- Getting customer identifiers for metering
- Tracking active subscriptions
- Buyer experience workflow

**Sample Item:**
```json
{
  "customerIdentifier": "test-customer-123",
  "productCode": "prod-xxx",
  "subscriptionStatus": "ACTIVE"
}
```

### AWSMarketplaceMeteringRecords Table
**Purpose:** Stores metering records to be reported to AWS Marketplace

**Used For:**
- Tracking customer usage
- Aggregating consumption data
- Reporting to AWS Marketplace via BatchMeterUsage API

**Sample Item:**
```json
{
  "create_timestamp": 1678672031,
  "customerIdentifier": "test-customer-123",
  "dimension_usage": [
    {
      "dimension": "requests",
      "value": 10
    },
    {
      "dimension": "users",
      "value": 10
    }
  ],
  "metering_pending": "true"
}
```

## Why Not Search by Product ID?

The CloudFormation stack creates tables with various naming conventions:
- Some tables may include the product ID
- Some tables may use generic names
- Table names may vary by deployment

By searching only by keywords, the agent:
- Works with any naming convention
- Is more flexible and robust
- Doesn't depend on specific product ID format
- Finds the correct functional tables

## Error Handling

### NewSubscribers Table Not Found
```
Error: "NewSubscribers table not found. Make sure the CloudFormation stack is deployed."
```

**Solution:**
- Verify CloudFormation stack is deployed
- Check stack status is CREATE_COMPLETE
- Verify DynamoDB tables were created

### AWSMarketplaceMeteringRecords Table Not Found
```
Error: "AWSMarketplaceMeteringRecords table not found. Make sure the CloudFormation stack is deployed."
```

**Solution:**
- Verify CloudFormation stack is deployed
- Check stack status is CREATE_COMPLETE
- Verify metering table was created

### No Customers Found
```
Info: "No customers found - creating test customer..."
```

**Action:**
- Agent automatically creates a test customer
- Test customer ID: "test-customer-123"
- Can be used for testing metering workflow

## Testing

### Verify Tables Exist
```bash
aws dynamodb list-tables --region us-east-1 | grep -E "NewSubscribers|AWSMarketplaceMeteringRecords"
```

### Check NewSubscribers Table
```bash
aws dynamodb scan --table-name <NewSubscribers-table-name> --region us-east-1
```

### Check Metering Records Table
```bash
aws dynamodb scan --table-name <AWSMarketplaceMeteringRecords-table-name> --region us-east-1
```

### Verify Metering Record
After running the metering agent, check that a record was inserted:
```bash
aws dynamodb scan \
  --table-name <AWSMarketplaceMeteringRecords-table-name> \
  --filter-expression "metering_pending = :pending" \
  --expression-attribute-values '{":pending":{"S":"true"}}' \
  --region us-east-1
```

## Lambda Processing

The hourly Lambda function:
1. Scans AWSMarketplaceMeteringRecords table
2. Finds records with `metering_pending = "true"`
3. Aggregates usage by customer and dimension
4. Calls BatchMeterUsage API
5. Updates records with `metering_pending = "false"`
6. Adds `metering_failed` flag if API call fails

## Summary

The updated metering agent:
- ✅ Searches by keywords only (NewSubscribers, AWSMarketplaceMeteringRecords)
- ✅ Does not filter by product ID
- ✅ Works with any CloudFormation naming convention
- ✅ Gets customer identifier from NewSubscribers table
- ✅ Inserts metering records into AWSMarketplaceMeteringRecords table
- ✅ Provides detailed error messages with available tables
- ✅ Automatically creates test customer if needed
- ✅ Follows AWS Marketplace metering best practices
