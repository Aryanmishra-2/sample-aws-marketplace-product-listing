# Chatbot AWS Documentation Integration

## Date: December 2, 2025

## Overview
Enhanced the chatbot to provide comprehensive AWS Marketplace documentation and guidance using a backend knowledge base that can be extended with the AWS MCP server.

## Architecture

### Components

```
┌─────────────────┐
│  User Interface │
│   (Chatbot)     │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Next.js API    │
│  /api/chat      │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  FastAPI        │
│  /chat          │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Knowledge Base │
│  (AWS Docs)     │
└─────────────────┘
```

### Data Flow

1. **User Input**: User types question or clicks quick action
2. **Frontend**: Sends POST request to `/api/chat`
3. **Next.js API**: Forwards to backend `/chat` endpoint
4. **Backend**: Processes question and generates response
5. **Response**: Returns formatted markdown with documentation
6. **Display**: Chatbot shows response with proper formatting

## Knowledge Base Topics

### 1. Seller Registration
**Keywords**: register, seller, account, business profile

**Content Includes:**
- 5-step registration process
- Required documents (W-9/W-8)
- Payment setup
- AWS review timeline
- Links to official guides

**Example Response:**
```
To register as an AWS Marketplace seller:

1. Validate Credentials: Enter your AWS credentials
2. Check Status: System checks registration status
3. Create Business Profile: Click "Create Business Profile"
4. Complete Tax Information: Submit W-9 or W-8 form
5. Set Up Payment: Configure bank account
6. Submit for Review: AWS reviews (2-3 business days)

[Link to AWS Marketplace Seller Guide]
```

### 2. SaaS Integration
**Keywords**: saas, integration, infrastructure, deployment

**Content Includes:**
- Architecture overview
- Infrastructure components
- Deployment process
- Configuration steps
- Fulfillment URL setup

**Example Response:**
```
SaaS Integration connects your product to AWS Marketplace:

Architecture:
• DynamoDB: Subscription and metering data
• Lambda: Usage metering processing
• API Gateway: Fulfillment endpoint
• SNS: Marketplace notifications

Deployment Steps:
1. Click "Configure SaaS" on product
2. Enter email for notifications
3. Deploy CloudFormation stack (3-5 min)
4. Copy fulfillment URL from outputs
5. Update product with URL

[Link to SaaS Integration Guide]
```

### 3. Product Listing
**Keywords**: listing, product, create, publish

**Content Includes:**
- Step-by-step creation process
- Product types (SaaS, AMI, Container, Data)
- AI-assisted content generation
- Review and submission
- Publishing workflow

### 4. Pricing Models
**Keywords**: pricing, price, cost, billing

**Content Includes:**
- Usage-based pricing
- Contract-based pricing
- Hybrid models
- Free trials
- Pricing dimensions

### 5. Product Visibility
**Keywords**: limited, public, draft, visibility, publish

**Content Includes:**
- DRAFT status explanation
- LIMITED testing phase
- PUBLIC availability
- Publishing process
- Review timeline

### 6. Metering & Billing
**Keywords**: metering, billing, usage, payment

**Content Includes:**
- Metering API usage
- Billing cycle
- Disbursement schedule
- AWS fees
- Usage reporting

### 7. Private Offers
**Keywords**: private offer, custom, negotiate, enterprise

**Content Includes:**
- Private offer benefits
- Use cases
- Creation process
- Custom terms
- Payment flexibility

## Response Format

### Structure
```markdown
# Main Topic

**What it does:**
• Bullet point 1
• Bullet point 2

**How to use:**
1. Step 1
2. Step 2

**Learn more:** [Link to documentation]
```

### Features
- **Markdown formatting**: Bold, bullets, numbered lists
- **Code blocks**: For technical examples
- **Links**: Direct links to AWS documentation
- **Sections**: Clear topic separation
- **Examples**: Practical use cases

## Backend Implementation

### Endpoint: POST /chat

**Request:**
```json
{
  "question": "How do I register as a seller?"
}
```

**Response:**
```json
{
  "success": true,
  "response": "To register as an AWS Marketplace seller...",
  "sources": []
}
```

### Error Handling
- Invalid request: 400 Bad Request
- Server error: 500 Internal Server Error
- Fallback: Frontend uses local responses

### Response Generation

```python
def generate_chat_response(question: str) -> str:
    """Generate response based on keywords"""
    question_lower = question.lower()
    
    if "register" in question_lower:
        return REGISTRATION_GUIDE
    elif "saas" in question_lower:
        return SAAS_INTEGRATION_GUIDE
    # ... more conditions
    else:
        return DEFAULT_HELP_MENU
```

## Frontend Implementation

### API Call
```typescript
const response = await fetch('/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ question: messageText }),
});

const data = await response.json();
```

### Error Handling
```typescript
try {
  // Call API
  const data = await response.json();
  if (data.success) {
    // Show response
  } else {
    // Fallback to local
  }
} catch (error) {
  // Fallback to local
}
```

### Fallback Strategy
If backend is unavailable:
1. Catch error
2. Use local `getBotResponse()` function
3. Show response from local knowledge base
4. User experience is not interrupted

## MCP Server Integration

### Configuration
File: `.kiro/settings/mcp.json`

```json
{
  "mcpServers": {
    "aws-docs": {
      "command": "uvx",
      "args": ["awslabs.aws-documentation-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": [
        "search_aws_documentation",
        "get_aws_documentation"
      ]
    }
  }
}
```

### Available Tools
1. **search_aws_documentation**: Search AWS docs
2. **get_aws_documentation**: Get specific doc page

### Future Integration
```python
# Search AWS documentation
results = mcp_client.search_aws_documentation(
    search_phrase="AWS Marketplace seller registration"
)

# Get specific documentation
doc = mcp_client.get_aws_documentation(
    url="https://docs.aws.amazon.com/marketplace/..."
)

# Generate response with context
response = generate_response_with_context(
    question=question,
    documentation=doc
)
```

## Benefits

### 1. Accurate Information
- Based on official AWS documentation
- Up-to-date guidance
- Consistent with AWS best practices

### 2. Comprehensive Coverage
- All major seller topics
- Step-by-step instructions
- Links to detailed guides

### 3. User Experience
- Instant responses
- No need to search documentation
- Context-aware help

### 4. Scalability
- Easy to add new topics
- Can integrate with MCP server
- Extensible architecture

## Testing

### Test Cases

1. **Registration Questions**
   - "How do I register?"
   - "What is seller registration?"
   - "How to become a seller?"

2. **SaaS Integration**
   - "What is SaaS integration?"
   - "How to deploy SaaS?"
   - "SaaS architecture?"

3. **Product Listing**
   - "How to create a listing?"
   - "What is a product listing?"
   - "How to publish a product?"

4. **Pricing**
   - "What pricing models are available?"
   - "How does billing work?"
   - "What are pricing dimensions?"

5. **General Questions**
   - "Help"
   - "What can you do?"
   - Random questions

### Expected Behavior
- Relevant response for each topic
- Fallback to general help for unknown questions
- Links to documentation included
- Proper markdown formatting

## Monitoring

### Metrics to Track
1. **Usage**: Number of questions asked
2. **Topics**: Most common question types
3. **Response Time**: API latency
4. **Errors**: Failed requests
5. **Satisfaction**: User feedback (future)

### Logging
```python
print(f"[DEBUG] Chat question: {question}")
print(f"[DEBUG] Response generated: {len(response)} chars")
print(f"[ERROR] Chat error: {str(e)}")
```

## Future Enhancements

### 1. Real-time Documentation Search
- Integrate AWS MCP server
- Search documentation in real-time
- Return most relevant pages
- Extract specific sections

### 2. Context Awareness
- Detect user's current page
- Provide page-specific help
- Remember conversation history
- Personalized responses

### 3. Amazon Bedrock Integration
- Natural language understanding
- More conversational responses
- Multi-turn conversations
- Intent recognition

### 4. Analytics Dashboard
- Track popular questions
- Identify knowledge gaps
- Measure response quality
- User satisfaction scores

### 5. Multi-language Support
- Detect user language
- Translate responses
- Regional documentation

### 6. Rich Media Responses
- Embedded images
- Video tutorials
- Interactive diagrams
- Code snippets with syntax highlighting

## Maintenance

### Adding New Topics
1. Add keyword detection in `generate_chat_response()`
2. Create response content with markdown
3. Include links to documentation
4. Test with various phrasings
5. Update documentation

### Updating Content
1. Review AWS documentation for changes
2. Update response text
3. Verify links are current
4. Test responses
5. Deploy updates

### Performance Optimization
1. Cache common responses
2. Optimize keyword matching
3. Reduce response size
4. Implement rate limiting
5. Monitor API latency

## References

- [AWS Marketplace Seller Guide](https://docs.aws.amazon.com/marketplace/latest/userguide/)
- [AWS MCP Server](https://github.com/awslabs/aws-documentation-mcp-server)
- [SaaS Integration Guide](https://docs.aws.amazon.com/marketplace/latest/userguide/saas-integrate-saas.html)
- [Pricing Guide](https://docs.aws.amazon.com/marketplace/latest/userguide/pricing.html)
