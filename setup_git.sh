#!/bin/bash
# Git and GitLab Setup Script

echo "=========================================="
echo "Git and GitLab Setup"
echo "=========================================="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first:"
    echo "   brew install git"
    exit 1
fi

echo "✅ Git is installed"
echo ""

# Configure Git user
echo "Step 1: Configure Git Identity"
echo "--------------------------------"
read -p "Enter your name (e.g., John Doe): " git_name
read -p "Enter your email (e.g., john@example.com): " git_email

git config --global user.name "$git_name"
git config --global user.email "$git_email"

echo "✅ Git identity configured"
echo "   Name: $git_name"
echo "   Email: $git_email"
echo ""

# Create .gitignore if it doesn't exist
echo "Step 2: Create .gitignore"
echo "-------------------------"

if [ ! -f .gitignore ]; then
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# AWS
.aws/
*.pem

# Environment
.env
.env.local

# Logs
*.log

# Test files
test_output/
*.tmp

# Streamlit
.streamlit/secrets.toml
EOF
    echo "✅ Created .gitignore"
else
    echo "✅ .gitignore already exists"
fi
echo ""

# Add GitLab remote
echo "Step 3: Add GitLab Remote"
echo "-------------------------"
echo ""
echo "Do you have a GitLab repository URL?"
echo "Examples:"
echo "  HTTPS: https://gitlab.com/username/repo-name.git"
echo "  SSH:   git@gitlab.com:username/repo-name.git"
echo ""
read -p "Enter GitLab repository URL (or press Enter to skip): " gitlab_url

if [ -n "$gitlab_url" ]; then
    git remote add origin "$gitlab_url"
    echo "✅ GitLab remote added: $gitlab_url"
else
    echo "⏭️  Skipped - You can add it later with:"
    echo "   git remote add origin <your-gitlab-url>"
fi
echo ""

# Initial commit
echo "Step 4: Create Initial Commit"
echo "------------------------------"
read -p "Create initial commit? (y/n): " do_commit

if [ "$do_commit" = "y" ] || [ "$do_commit" = "Y" ]; then
    git add .
    git commit -m "feat: initial commit - AWS Marketplace SaaS Listing Creator

- Implement AI-powered listing creation
- Support all 3 pricing models (Usage, Contract, Hybrid)
- Add comprehensive documentation
- Include testing utilities
- Complete 8-stage workflow"
    
    echo "✅ Initial commit created"
    echo ""
    
    # Push to GitLab
    if [ -n "$gitlab_url" ]; then
        read -p "Push to GitLab now? (y/n): " do_push
        if [ "$do_push" = "y" ] || [ "$do_push" = "Y" ]; then
            echo ""
            echo "Pushing to GitLab..."
            git branch -M main
            git push -u origin main
            echo "✅ Pushed to GitLab!"
        else
            echo "⏭️  Skipped - Push later with: git push -u origin main"
        fi
    fi
else
    echo "⏭️  Skipped - Commit later with: git add . && git commit -m 'your message'"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. If you haven't created a GitLab repo yet:"
echo "   - Go to https://gitlab.com"
echo "   - Click 'New Project'"
echo "   - Copy the repository URL"
echo "   - Run: git remote add origin <url>"
echo ""
echo "2. To commit changes:"
echo "   git add ."
echo "   git commit -m 'your message'"
echo "   git push origin main"
echo ""
echo "3. Check status anytime:"
echo "   git status"
echo ""
