# Test Suite for AWS Marketplace SaaS Integration

This directory contains individual test scripts for each agent and functionality in the AWS Marketplace SaaS Integration system.

## Quick Start

### Run All Tests
```bash
python tests/run_all_tests.py
```

### Run Individual Tests
```bash
# Test CreateSaasAgent configuration
python tests/test_create_saas_agent.py

# Test automated fulfillment URL update
python tests/test_fulfillment_url_update.py

# Test metering functionality
python tests/test_metering_agent.py

# Test public visibility requests
python tests/test_public_visibility_agent.py

# Test buyer experience simulation
python tests/test_buyer_experience_agent.py

# Test complete workflow orchestration
python tests/test_workflow_orchestrator.py
```

## Test Descriptions

### 1. CreateSaasAgent Test
- **File**: `test_create_saas_agent.py`
- **Purpose**: Validates product configuration (ID, pricing model, email)
- **Requirements**: None (no AWS credentials needed)

### 2. Fulfillment URL Update Test
- **File**: `test_fulfillment_url_update.py`
- **Purpose**: Tests automated fulfillment URL update via AWS Marketplace Catalog API
- **Requirements**: AWS credentials with marketplace-catalog permissions

### 3. MeteringAgent Test
- **File**: `test_metering_agent.py`
- **Purpose**: Tests metering record creation and status checking
- **Requirements**: AWS credentials, existing DynamoDB tables

### 4. PublicVisibilityAgent Test
- **File**: `test_public_visibility_agent.py`
- **Purpose**: Tests public visibility request submission
- **Requirements**: AWS credentials, successful metering records

### 5. BuyerExperienceAgent Test
- **File**: `test_buyer_experience_agent.py`
- **Purpose**: Tests buyer registration simulation
- **Requirements**: AWS credentials, deployed infrastructure

### 6. WorkflowOrchestrator Test
- **File**: `test_workflow_orchestrator.py`
- **Purpose**: Tests complete workflow execution
- **Requirements**: AWS credentials, full infrastructure deployment

## Prerequisites

### AWS Credentials
Most tests require AWS credentials with appropriate permissions:
- `marketplace-catalog:StartChangeSet`
- `marketplace-catalog:DescribeEntity`
- `dynamodb:PutItem`
- `dynamodb:Query`
- `lambda:InvokeFunction`

### Infrastructure
Some tests require existing AWS infrastructure:
- DynamoDB tables (for metering tests)
- Lambda functions (for workflow tests)
- CloudFormation stacks (for integration tests)

## Usage Tips

1. **Start with CreateSaasAgent**: This test requires no AWS resources
2. **Test incrementally**: Run individual tests before the full workflow
3. **Use test credentials**: Use temporary/test AWS credentials for safety
4. **Check prerequisites**: Ensure required infrastructure exists before testing

## Test Output

Each test provides:
- ✓ Success indicators for passed tests
- ✗ Error messages for failed tests
- Detailed output for debugging
- Result summaries

## Troubleshooting

### Common Issues
- **Credential errors**: Verify AWS access keys and permissions
- **Resource not found**: Ensure required infrastructure is deployed
- **API limits**: Some tests may hit AWS API rate limits

### Debug Mode
Add `print()` statements in test files for additional debugging output.