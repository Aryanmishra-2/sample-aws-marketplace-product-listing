# Metering Agent with Strands Framework

Complete implementation of AWS Marketplace metering functionality using the MeteringAgent with the strands framework.

## 🚀 Quick Start

```bash
# 1. Install strands
cd ai-agent-marketplace/backend
pip install strands

# 2. Start backend
uvicorn main:app --reload

# 3. Start frontend (in another terminal)
cd ai-agent-marketplace/frontend
npm run dev

# 4. Navigate to http://localhost:3000 and complete the workflow
```

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [METERING_QUICK_START.md](METERING_QUICK_START.md) | Quick start guide with installation and testing |
| [METERING_AGENT_IMPLEMENTATION.md](METERING_AGENT_IMPLEMENTATION.md) | Complete technical documentation |
| [METERING_ARCHITECTURE.md](METERING_ARCHITECTURE.md) | System architecture and data flow diagrams |
| [METERING_IMPLEMENTATION_SUMMARY.md](METERING_IMPLEMENTATION_SUMMARY.md) | Summary of what was implemented |
| [METERING_CHECKLIST.md](METERING_CHECKLIST.md) | Pre-deployment and testing checklist |

## 🎯 What's Implemented

### Backend (`backend/main.py`)
- **Endpoint:** `POST /run-metering`
- Uses MeteringAgent with strands framework
- Returns detailed step-by-step progress with substeps
- Comprehensive error handling

### Frontend API (`frontend/src/app/api/run-metering/route.ts`)
- Forwards requests to FastAPI backend
- Handles timeouts (120 seconds)
- Returns detailed step information

### Frontend UI (`frontend/src/app/saas-workflow/page.tsx`)
- Displays main steps with status indicators
- Shows substeps for each main step
- Displays detailed information (customer, tables, dimensions)
- Shows Lambda function information

### MeteringAgent (`agents/metering.py`)
- Uses strands framework with `@tool` decorators
- Three main tools:
  1. `check_entitlement_and_add_metering` - 7 substeps
  2. `trigger_hourly_metering` - 3 substeps
  3. `insert_test_customer` - Helper tool

## 🔄 Workflow

```
1. Initialize MeteringAgent
   └─ Set product ID

2. Check Entitlement & Create Metering Records
   ├─ Check pricing model
   ├─ Connect to DynamoDB
   ├─ Locate DynamoDB tables
   ├─ Retrieve customer from subscribers
   ├─ Get usage dimensions
   ├─ Prepare metering record
   └─ Insert metering record

3. Trigger Lambda to Process Metering
   ├─ Find hourly metering Lambda
   ├─ Invoke Lambda function
   └─ Process metering records
```

## 📊 UI Display

The UI shows:
- ✅ Completed steps
- ❌ Failed steps
- ⚠️ Warning steps
- ⊘ Skipped steps
- ⏳ In-progress steps
- Detailed substeps with individual status
- Key information (customer ID, tables, dimensions)
- Lambda function details

## 🧪 Testing

### Quick Test
```bash
# Test the full workflow through the UI
npm run dev  # Frontend
uvicorn main:app --reload  # Backend
# Navigate to http://localhost:3000
```

### API Test
```bash
curl -X POST http://localhost:8000/run-metering \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "prod-xxx",
    "credentials": {
      "aws_access_key_id": "xxx",
      "aws_secret_access_key": "xxx",
      "aws_session_token": "xxx"
    }
  }'
```

### Direct Agent Test
```python
from agents.metering import MeteringAgent

agent = MeteringAgent()
agent.create_saas_agent.set_product_id("prod-xxx")

result = agent.check_entitlement_and_add_metering(
    access_key="xxx",
    secret_key="xxx",
    session_token="xxx"
)
print(result)
```

## 🎨 Features

### Strands Framework Integration
- Structured agent with `@tool` decorators
- Clear separation of concerns
- Reusable tools
- Detailed logging

### Detailed Progress Tracking
- Main steps with substeps
- Individual status for each substep
- Real-time progress updates
- Comprehensive error messages

### Pricing Model Handling
- **Contract-with-consumption:** Full metering workflow
- **Usage-based-pricing:** Full metering workflow
- **Contract:** Skips metering with clear message

### Error Handling
- Initialization errors
- DynamoDB access errors
- Lambda invocation errors
- Timeout handling
- Graceful degradation

## 📁 File Structure

```
ai-agent-marketplace/
├── agents/
│   └── metering.py                    # MeteringAgent with strands
├── backend/
│   └── main.py                        # FastAPI endpoint
├── frontend/
│   ├── src/app/api/run-metering/
│   │   └── route.ts                   # Next.js API route
│   └── src/app/saas-workflow/
│       └── page.tsx                   # UI display
└── docs/
    ├── METERING_README.md             # This file
    ├── METERING_QUICK_START.md        # Quick start guide
    ├── METERING_AGENT_IMPLEMENTATION.md  # Technical docs
    ├── METERING_ARCHITECTURE.md       # Architecture diagrams
    ├── METERING_IMPLEMENTATION_SUMMARY.md  # Summary
    └── METERING_CHECKLIST.md          # Checklist
```

## 🔧 Configuration

### Backend
No additional configuration needed. The endpoint is automatically available at `/run-metering`.

### Frontend
The API route is automatically available at `/api/run-metering`.

### AWS
Requires:
- DynamoDB tables (created by CloudFormation)
- Lambda function (created by CloudFormation)
- IAM permissions for DynamoDB and Lambda

## 🐛 Troubleshooting

### "strands module not found"
```bash
pip install strands
```

### "Subscribers table not found"
Ensure CloudFormation stack is deployed and complete.

### "Lambda function not found"
Verify Lambda function exists with pattern: `{product_id}-HourlyMeteringFunction`

### "Timeout error"
The workflow has a 120-second timeout. If it times out, check:
- AWS credentials are valid
- DynamoDB tables are accessible
- Lambda function exists

## 📈 Monitoring

### Backend Logs
```bash
# Watch backend logs
uvicorn main:app --reload
# Look for [METERING] and [METERING AGENT] messages
```

### Frontend Logs
```bash
# Open browser console (F12)
# Look for [METERING API] messages
```

### AWS CloudWatch
```bash
# Check Lambda logs
aws logs tail /aws/lambda/{product_id}-HourlyMeteringFunction --follow
```

### DynamoDB
```bash
# Check metering records
aws dynamodb scan --table-name AWSMarketplaceMeteringRecords-xxx
```

## 🚀 Deployment

### Backend
1. Update requirements.txt: `pip freeze > requirements.txt`
2. Deploy to AWS Lambda/ECS
3. Configure environment variables
4. Test endpoint

### Frontend
1. Build: `npm run build`
2. Deploy to Vercel/AWS
3. Update API endpoint URLs
4. Test production workflow

## 📚 Additional Resources

- [Strands Framework Documentation](https://github.com/strands-ai/strands)
- [AWS Marketplace Metering API](https://docs.aws.amazon.com/marketplace/latest/userguide/metering-service.html)
- [AWS Marketplace SaaS Integration](https://docs.aws.amazon.com/marketplace/latest/userguide/saas-integration.html)

## 🤝 Contributing

When contributing to the metering functionality:

1. Follow the strands framework patterns
2. Add detailed logging
3. Update documentation
4. Add tests
5. Update the checklist

## 📝 License

See the main project LICENSE file.

## 🎉 Success!

You now have a fully functional metering implementation using the MeteringAgent with strands framework!

**Next Steps:**
1. Install strands: `pip install strands`
2. Test the workflow
3. Deploy to production
4. Monitor execution
5. Celebrate! 🎊

---

**Need Help?**
- Check the documentation files listed above
- Review the code comments
- Check backend and frontend logs
- Verify AWS resources
- Test components individually
