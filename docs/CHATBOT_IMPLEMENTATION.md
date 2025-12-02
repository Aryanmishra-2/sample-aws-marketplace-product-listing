# AWS Marketplace Chatbot Implementation

## Date: December 2, 2025

## Overview
Implemented an AI-powered chatbot assistant similar to the AWS website's support chat to help users navigate the AWS Marketplace seller registration and listing creation process.

## Features

### 1. Floating Chat Button
- **Position**: Fixed bottom-right corner
- **Design**: Orange circular button with chat icon
- **Animation**: Scales on hover with glow effect
- **Always Accessible**: Available on all pages

### 2. Chat Interface
- **Size**: 380px × 600px
- **Position**: Bottom-right, above the button
- **Design**: AWS-themed with dark header
- **Responsive**: Adapts to mobile screens

### 3. Header
- **Bot Avatar**: Orange circular icon with robot emoji
- **Status**: "Online" indicator
- **Title**: "AWS Assistant"
- **Close Button**: X to minimize chat

### 4. Message Display
- **User Messages**: Orange bubbles, right-aligned
- **Bot Messages**: White bubbles, left-aligned
- **Timestamps**: Small text below each message
- **Auto-scroll**: Scrolls to latest message
- **Typing Indicator**: Shows when bot is responding

### 5. Quick Actions
- Displayed when conversation starts
- Pre-defined common questions
- One-click to get instant answers
- Hover effect with orange highlight

### 6. Input Area
- Text input field
- Send button (primary AWS orange)
- Enter key support
- Disabled while bot is typing

## Quick Actions

### 1. How do I register as a seller?
Explains the 5-step seller registration process:
- Credential validation
- Business profile creation
- Tax information
- Payment setup
- AWS review

### 2. What is SaaS integration?
Describes SaaS integration features:
- Infrastructure deployment
- Subscription management
- Metering and billing
- Fulfillment endpoint

### 3. How to create a product listing?
Walks through the listing creation process:
- Product information entry
- AI analysis
- Content review
- Submission

### 4. Pricing models explained
Explains available pricing options:
- Usage-based pricing
- Contract-based pricing
- Hybrid models
- Free trials

## Intelligent Responses

The chatbot uses keyword matching to provide relevant responses:

### Keywords → Responses
- **"register", "seller"** → Registration guide
- **"saas", "integration"** → SaaS integration info
- **"listing", "product", "create"** → Listing creation steps
- **"pricing", "price", "cost"** → Pricing models
- **Default** → General help menu

## Design Specifications

### Colors
- **Bot Avatar**: #ff9900 (AWS Orange)
- **User Messages**: #ff9900 background, white text
- **Bot Messages**: White background, #16191f text
- **Header**: #232f3e (AWS Squid Ink)
- **Border Accent**: #ff9900 (3px)

### Typography
- **Header Title**: 16px, bold
- **Status**: 12px, regular
- **Messages**: 14px, line-height 1.5
- **Timestamps**: 11px, 70% opacity
- **Quick Actions**: 12px

### Spacing
- **Chat Padding**: 16px
- **Message Gap**: 12px (medium)
- **Quick Action Gap**: 8px
- **Input Gap**: 8px

### Animations
- **Button Hover**: Scale 1.1, enhanced shadow
- **Quick Action Hover**: Orange background
- **Typing Indicator**: Loading animation
- **Message Entry**: Smooth scroll

### Shadows
- **Chat Window**: `0 8px 24px rgba(0, 0, 0, 0.15)`
- **Messages**: `0 2px 4px rgba(0, 0, 0, 0.1)`
- **Button**: `0 4px 12px rgba(255, 153, 0, 0.4)`
- **Button Hover**: `0 6px 16px rgba(255, 153, 0, 0.6)`

## User Experience Flow

### Initial State
1. User sees orange chat button in bottom-right
2. Button pulses subtly to draw attention
3. Hover shows scale animation

### Opening Chat
1. Click button to open chat window
2. Welcome message from bot appears
3. Quick actions displayed below
4. Input field ready for typing

### Conversation
1. User types message or clicks quick action
2. User message appears in orange bubble
3. Bot shows "Typing..." indicator
4. Bot response appears after 1 second
5. Auto-scrolls to show new messages

### Closing Chat
1. Click X button in header
2. Chat minimizes to button
3. Conversation history preserved
4. Can reopen to continue

## Technical Implementation

### Component Structure
```typescript
Chatbot
├── Floating Button (minimized state)
└── Chat Window (expanded state)
    ├── Header
    │   ├── Avatar
    │   ├── Title & Status
    │   └── Close Button
    ├── Messages Area
    │   ├── Message List
    │   ├── Typing Indicator
    │   └── Auto-scroll Ref
    ├── Quick Actions (conditional)
    └── Input Area
        ├── Text Input
        └── Send Button
```

### State Management
```typescript
- isOpen: boolean (chat visibility)
- messages: Message[] (conversation history)
- inputValue: string (current input)
- isTyping: boolean (bot typing state)
```

### Message Interface
```typescript
interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}
```

## Integration

### Global Layout
Added to `frontend/src/app/layout.tsx`:
```typescript
import Chatbot from '@/components/Chatbot';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Chatbot />
      </body>
    </html>
  );
}
```

### Positioning
- **z-index**: 1000 (above all content)
- **position**: fixed
- **bottom**: 24px
- **right**: 24px

## Accessibility

### Keyboard Support
- Enter key to send messages
- Tab navigation through elements
- Escape key to close (future enhancement)

### Screen Readers
- Semantic HTML structure
- ARIA labels (future enhancement)
- Status announcements (future enhancement)

### Visual
- High contrast text
- Clear focus indicators
- Readable font sizes
- Color-blind friendly (not relying on color alone)

## AWS Documentation Integration

### Backend Implementation
The chatbot now uses a backend endpoint (`/chat`) that provides comprehensive AWS Marketplace documentation:

**Topics Covered:**
- Seller registration process
- SaaS integration architecture
- Product listing creation
- Pricing models (usage-based, contract, hybrid)
- Product visibility (DRAFT, LIMITED, PUBLIC)
- Metering and billing
- Private offers

**Response Format:**
- Structured markdown responses
- Step-by-step instructions
- Links to official AWS documentation
- Code examples where applicable

### MCP Server Configuration
Added AWS documentation MCP server to `.kiro/settings/mcp.json`:
```json
{
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
```

### API Flow
```
User Question
    ↓
Frontend Chatbot
    ↓
/api/chat (Next.js API Route)
    ↓
Backend /chat endpoint
    ↓
AWS Documentation Knowledge Base
    ↓
Formatted Response
    ↓
Display to User
```

## Future Enhancements

### 1. Enhanced AI Integration
- Connect to Amazon Bedrock for natural language
- Use AWS MCP server for real-time documentation search
- Context-aware responses based on user's current page
- Multi-turn conversations with memory

### 2. Advanced Features
- File attachments
- Code snippets
- Links to documentation
- Video tutorials
- Screen sharing

### 3. Personalization
- User preferences
- Conversation history
- Suggested actions based on current page
- Proactive help offers

### 4. Analytics
- Track common questions
- Measure response effectiveness
- User satisfaction ratings
- Conversation analytics

### 5. Multi-language Support
- Detect user language
- Translate responses
- Regional content

### 6. Integration with Backend
- Real-time status updates
- Account-specific help
- Product-specific guidance
- Error troubleshooting

### 7. Rich Media
- Images and diagrams
- Interactive tutorials
- Video responses
- Animated guides

### 8. Notifications
- Unread message count
- Sound alerts (optional)
- Desktop notifications
- Email transcripts

## Testing Recommendations

### Functional Testing
1. Open/close chat
2. Send messages
3. Click quick actions
4. Verify responses
5. Test keyboard navigation

### Visual Testing
1. Check on different screen sizes
2. Verify colors and spacing
3. Test animations
4. Check hover states
5. Verify z-index layering

### Performance Testing
1. Message rendering speed
2. Scroll performance
3. Memory usage
4. Animation smoothness

### Accessibility Testing
1. Keyboard-only navigation
2. Screen reader compatibility
3. Color contrast ratios
4. Focus indicators

## Maintenance

### Adding New Responses
1. Add keyword to `getBotResponse()` function
2. Add response to `BOT_RESPONSES` object
3. Optionally add quick action
4. Test keyword matching

### Updating Styling
1. Modify inline styles in component
2. Consider extracting to CSS module
3. Maintain AWS theme consistency
4. Test across browsers

### Performance Optimization
1. Lazy load chat component
2. Virtualize long message lists
3. Debounce typing indicator
4. Optimize re-renders

## References

- [AWS Website Chat](https://aws.amazon.com/)
- [CloudScape Design System](https://cloudscape.design/)
- [AWS Brand Guidelines](https://aws.amazon.com/architecture/icons/)
