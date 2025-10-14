#!/bin/bash
# AWS Credentials Setup Helper

echo "=========================================="
echo "AWS Credentials Setup"
echo "=========================================="
echo ""

# Check if credentials file exists
if [ ! -f ~/.aws/credentials ]; then
    echo "Creating ~/.aws directory..."
    mkdir -p ~/.aws
fi

echo "Choose your authentication method:"
echo ""
echo "1) IAM User (Access Key + Secret Key)"
echo "2) SSO / Temporary Credentials (with Session Token)"
echo "3) Use existing credentials (test only)"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "IAM User Credentials"
        echo "--------------------"
        read -p "AWS Access Key ID: " access_key
        read -p "AWS Secret Access Key: " secret_key
        read -p "Default region [us-east-1]: " region
        region=${region:-us-east-1}
        
        cat > ~/.aws/credentials << EOF
[default]
aws_access_key_id = $access_key
aws_secret_access_key = $secret_key
EOF
        
        cat > ~/.aws/config << EOF
[default]
region = $region
output = json
EOF
        
        echo ""
        echo "✓ Credentials saved!"
        ;;
        
    2)
        echo ""
        echo "Temporary Credentials (SSO/STS)"
        echo "-------------------------------"
        read -p "AWS Access Key ID: " access_key
        read -p "AWS Secret Access Key: " secret_key
        read -p "AWS Session Token: " session_token
        read -p "Default region [us-east-1]: " region
        region=${region:-us-east-1}
        
        cat > ~/.aws/credentials << EOF
[default]
aws_access_key_id = $access_key
aws_secret_access_key = $secret_key
aws_session_token = $session_token
EOF
        
        cat > ~/.aws/config << EOF
[default]
region = $region
output = json
EOF
        
        echo ""
        echo "✓ Credentials saved!"
        echo "⚠️  Note: Session tokens expire. You'll need to refresh them."
        ;;
        
    3)
        echo ""
        echo "Testing existing credentials..."
        ;;
        
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "Testing AWS access..."
if aws sts get-caller-identity 2>/dev/null; then
    echo ""
    echo "✓ AWS credentials are working!"
    echo ""
    echo "Next steps:"
    echo "  1. Enable Bedrock model access in AWS Console"
    echo "  2. Run: python3 test_setup.py"
    echo "  3. Run: python3 main.py"
else
    echo ""
    echo "✗ AWS credentials test failed"
    echo ""
    echo "Common issues:"
    echo "  - Expired session token (if using temporary credentials)"
    echo "  - Incorrect access key or secret key"
    echo "  - No internet connection"
    echo ""
    echo "To get fresh credentials:"
    echo "  - IAM User: Get from AWS Console → IAM → Users → Security Credentials"
    echo "  - SSO: Run your SSO login command to get fresh tokens"
    echo "  - AWS Academy: Get credentials from AWS Academy Learner Lab"
fi
