#!/bin/bash
# Deploy AWS Marketplace SaaS Integration Stack

set -e

# Configuration
STACK_NAME="saas-integration-prod-cyxse6dkyvfo4"
REGION="us-east-1"
TEMPLATE_FILE="deployment/cloudformation/Integration.yaml"

# Parameters
PRODUCT_ID="prod-cyxse6dkyvfo4"
PRICING_MODEL="${PRICING_MODEL:-Contract-based-pricing}"  # Options: Contract-with-consumption, Contract-based-pricing, Usage-based-pricing
UPDATE_FULFILLMENT_URL="${UPDATE_FULFILLMENT_URL:-true}"  # Set to "true" if you want to auto-update the fulfillment URL

# Prompt for admin email if not provided
if [ -z "$ADMIN_EMAIL" ]; then
    echo "⚠️  Admin email is required for notifications about customer registrations and subscription events."
    read -p "Enter admin email address: " ADMIN_EMAIL
    
    if [ -z "$ADMIN_EMAIL" ]; then
        echo "❌ Admin email is required. Exiting."
        exit 1
    fi
fi

echo "🚀 Deploying AWS Marketplace SaaS Integration Stack"
echo "Stack Name: $STACK_NAME"
echo "Region: $REGION"
echo "Product ID: $PRODUCT_ID"
echo ""

# Check if stack already exists
if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" &>/dev/null; then
    echo "⚠️  Stack already exists. Updating..."
    OPERATION="update-stack"
else
    echo "✨ Creating new stack..."
    OPERATION="create-stack"
fi

# Deploy the stack
aws cloudformation "$OPERATION" \
    --stack-name "$STACK_NAME" \
    --template-body "file://$TEMPLATE_FILE" \
    --parameters \
        ParameterKey=ProductId,ParameterValue="$PRODUCT_ID" \
        ParameterKey=PricingModel,ParameterValue="$PRICING_MODEL" \
        ParameterKey=MarketplaceTechAdminEmail,ParameterValue="$ADMIN_EMAIL" \
        ParameterKey=UpdateFulfillmentURL,ParameterValue="$UPDATE_FULFILLMENT_URL" \
        ParameterKey=SNSAccountID,ParameterValue="287250355862" \
        ParameterKey=SNSRegion,ParameterValue="us-east-1" \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
    --region "$REGION"

echo ""
echo "✅ Stack deployment initiated"
echo ""
echo "📊 Monitoring stack status..."
echo "   You can also check the AWS Console: https://console.aws.amazon.com/cloudformation"
echo ""

# Wait for stack to complete
aws cloudformation wait "stack-${OPERATION//-stack/}-complete" \
    --stack-name "$STACK_NAME" \
    --region "$REGION" || {
    echo ""
    echo "❌ Stack deployment failed or timed out"
    echo ""
    echo "🔍 Recent events:"
    aws cloudformation describe-stack-events \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'StackEvents[?ResourceStatus==`CREATE_FAILED` || ResourceStatus==`UPDATE_FAILED`].[LogicalResourceId,ResourceStatusReason]' \
        --output table
    exit 1
}

echo ""
echo "✅ Stack deployment completed successfully!"
echo ""
echo "📋 Stack Outputs:"
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs' \
    --output table

