'use client';

import { useState, useRef, useEffect } from 'react';
import { Box, Button, Input, SpaceBetween, StatusIndicator } from '@cloudscape-design/components';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

const QUICK_ACTIONS = [
  { label: 'How do I register as a seller?', value: 'register' },
  { label: 'What is SaaS integration?', value: 'saas' },
  { label: 'How to create a product listing?', value: 'listing' },
  { label: 'Pricing models explained', value: 'pricing' },
];

const BOT_RESPONSES: Record<string, string> = {
  register: "To register as an AWS Marketplace seller:\n\n1. Validate your AWS credentials on the home page\n2. If you see 'NOT_REGISTERED' status, click 'Create Business Profile'\n3. Complete tax information (W-9 or W-8 form)\n4. Set up payment information\n5. Submit for AWS review (2-3 business days)\n\nOnce approved, you can create product listings!",
  saas: "SaaS Integration connects your SaaS product to AWS Marketplace:\n\n• Deploys serverless infrastructure (DynamoDB, Lambda, API Gateway)\n• Handles subscription management\n• Processes metering and billing\n• Provides fulfillment endpoint\n\nFor LIMITED products, click 'Configure SaaS' to deploy the integration automatically.",
  listing: "Creating a product listing is easy:\n\n1. Click 'Create New Product' from the seller registration page\n2. Enter product information (name, description, URLs)\n3. AI analyzes your product and generates content\n4. Review and edit the suggestions\n5. Submit to create the listing\n\nThe AI handles all the marketplace-specific formatting!",
  pricing: "AWS Marketplace supports multiple pricing models:\n\n• Usage-based: Pay per use (hourly, API calls, etc.)\n• Contract-based: Fixed price for a term\n• Contract with consumption: Hybrid model\n• Free trial: Let customers try before buying\n\nChoose the model that fits your business during listing creation.",
  default: "I'm here to help with AWS Marketplace seller registration and listing creation! You can ask me about:\n\n• Seller registration process\n• SaaS integration\n• Creating product listings\n• Pricing models\n• Product management\n\nWhat would you like to know?",
};

export default function Chatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: "👋 Hi! I'm your AWS Marketplace assistant. How can I help you today?",
      sender: 'bot',
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (text?: string) => {
    const messageText = text || inputValue.trim();
    if (!messageText) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      text: messageText,
      sender: 'user',
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    try {
      // Call backend chat endpoint
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: messageText,
        }),
      });

      const data = await response.json();

      if (data.success) {
        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: data.response,
          sender: 'bot',
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, botMessage]);
      } else {
        // Fallback to local response if API fails
        const fallbackResponse = getBotResponse(messageText);
        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: fallbackResponse,
          sender: 'bot',
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, botMessage]);
      }
    } catch (error) {
      console.error('Chat error:', error);
      // Fallback to local response on error
      const fallbackResponse = getBotResponse(messageText);
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: fallbackResponse,
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const getBotResponse = (userMessage: string): string => {
    const lowerMessage = userMessage.toLowerCase();

    if (lowerMessage.includes('register') || lowerMessage.includes('seller')) {
      return BOT_RESPONSES.register;
    }
    if (lowerMessage.includes('saas') || lowerMessage.includes('integration')) {
      return BOT_RESPONSES.saas;
    }
    if (lowerMessage.includes('listing') || lowerMessage.includes('product') || lowerMessage.includes('create')) {
      return BOT_RESPONSES.listing;
    }
    if (lowerMessage.includes('pricing') || lowerMessage.includes('price') || lowerMessage.includes('cost')) {
      return BOT_RESPONSES.pricing;
    }

    return BOT_RESPONSES.default;
  };

  const handleQuickAction = async (action: string) => {
    const quickActionLabel = QUICK_ACTIONS.find((a) => a.value === action)?.label || action;
    
    // Use handleSend to process the quick action
    await handleSend(quickActionLabel);
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          width: '60px',
          height: '60px',
          borderRadius: '50%',
          backgroundColor: '#ff9900',
          color: 'white',
          border: 'none',
          cursor: 'pointer',
          fontSize: '24px',
          boxShadow: '0 4px 12px rgba(255, 153, 0, 0.4)',
          zIndex: 1000,
          transition: 'all 0.3s ease',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'scale(1.1)';
          e.currentTarget.style.boxShadow = '0 6px 16px rgba(255, 153, 0, 0.6)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'scale(1)';
          e.currentTarget.style.boxShadow = '0 4px 12px rgba(255, 153, 0, 0.4)';
        }}
      >
        💬
      </button>
    );
  }

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        width: '380px',
        height: '600px',
        backgroundColor: 'white',
        borderRadius: '12px',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.15)',
        display: 'flex',
        flexDirection: 'column',
        zIndex: 1000,
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          backgroundColor: '#232f3e',
          color: 'white',
          padding: '16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '3px solid #ff9900',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              width: '40px',
              height: '40px',
              borderRadius: '50%',
              backgroundColor: '#ff9900',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '20px',
            }}
          >
            🤖
          </div>
          <div>
            <div style={{ fontWeight: 'bold', fontSize: '16px' }}>AWS Assistant</div>
            <div style={{ fontSize: '12px', color: '#aab7b8' }}>
              <StatusIndicator type="success">Online</StatusIndicator>
            </div>
          </div>
        </div>
        <button
          onClick={() => setIsOpen(false)}
          style={{
            backgroundColor: 'transparent',
            color: 'white',
            border: 'none',
            fontSize: '24px',
            cursor: 'pointer',
            padding: '0',
            width: '32px',
            height: '32px',
          }}
        >
          ×
        </button>
      </div>

      {/* Messages */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px',
          backgroundColor: '#f2f3f3',
        }}
      >
        <SpaceBetween size="m">
          {messages.map((message) => (
            <div
              key={message.id}
              style={{
                display: 'flex',
                justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
              }}
            >
              <div
                style={{
                  maxWidth: '80%',
                  padding: '12px 16px',
                  borderRadius: '12px',
                  backgroundColor: message.sender === 'user' ? '#ff9900' : 'white',
                  color: message.sender === 'user' ? 'white' : '#16191f',
                  boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                <div style={{ fontSize: '14px', lineHeight: '1.5' }}>{message.text}</div>
                <div
                  style={{
                    fontSize: '11px',
                    marginTop: '4px',
                    opacity: 0.7,
                  }}
                >
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          ))}
          {isTyping && (
            <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
              <div
                style={{
                  padding: '12px 16px',
                  borderRadius: '12px',
                  backgroundColor: 'white',
                  boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
                }}
              >
                <StatusIndicator type="loading">Typing...</StatusIndicator>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </SpaceBetween>
      </div>

      {/* Quick Actions */}
      {messages.length <= 2 && (
        <div
          style={{
            padding: '12px 16px',
            backgroundColor: 'white',
            borderTop: '1px solid #d5dbdb',
          }}
        >
          <Box fontSize="body-s" color="text-body-secondary" margin={{ bottom: 'xs' }}>
            Quick actions:
          </Box>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {QUICK_ACTIONS.map((action) => (
              <button
                key={action.value}
                onClick={() => handleQuickAction(action.value)}
                style={{
                  backgroundColor: '#f2f3f3',
                  border: '1px solid #d5dbdb',
                  borderRadius: '16px',
                  padding: '6px 12px',
                  fontSize: '12px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#ff9900';
                  e.currentTarget.style.color = 'white';
                  e.currentTarget.style.borderColor = '#ff9900';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#f2f3f3';
                  e.currentTarget.style.color = '#16191f';
                  e.currentTarget.style.borderColor = '#d5dbdb';
                }}
              >
                {action.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div
        style={{
          padding: '16px',
          backgroundColor: 'white',
          borderTop: '1px solid #d5dbdb',
        }}
      >
        <div style={{ display: 'flex', gap: '8px' }}>
          <Input
            value={inputValue}
            onChange={({ detail }) => setInputValue(detail.value)}
            placeholder="Type your message..."
            onKeyDown={(e) => {
              if (e.detail.key === 'Enter') {
                handleSend();
              }
            }}
          />
          <Button
            variant="primary"
            onClick={() => handleSend()}
            disabled={!inputValue.trim() || isTyping}
          >
            Send
          </Button>
        </div>
      </div>
    </div>
  );
}
