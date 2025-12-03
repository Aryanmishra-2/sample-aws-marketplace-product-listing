# Release Checklist

Use this checklist before releasing a new version to ensure quality, security, and completeness.

## Pre-Release Checklist

### Code Quality
- [ ] All tests pass (`python test_agent.py`)
- [ ] No linting errors (`ruff check .` or `black --check .`)
- [ ] No TypeScript errors (`cd frontend && npm run build`)
- [ ] Code review completed
- [ ] Documentation updated

### Security
- [ ] No hardcoded credentials in code
- [ ] `.env` file not committed
- [ ] `.gitignore` properly configured
- [ ] Security scan completed (Bandit, npm audit)
- [ ] Dependencies updated to latest secure versions
- [ ] SECURITY.md reviewed and updated
- [ ] IAM permissions follow least privilege
- [ ] CORS origins configured for production

### Functionality
- [ ] All 7 workflow stages tested
- [ ] Credential validation works
- [ ] Seller registration check works
- [ ] Product analysis generates correct output
- [ ] Content generation produces quality results
- [ ] Pricing suggestions are reasonable
- [ ] Listing creation succeeds
- [ ] SaaS deployment works (if enabled)
- [ ] Help chatbot responds correctly

### Documentation
- [ ] README.md is up to date
- [ ] API documentation is current
- [ ] Architecture diagrams are accurate
- [ ] CHANGELOG.md updated with new version
- [ ] Installation instructions tested
- [ ] Troubleshooting guide is complete
- [ ] All links work

### Configuration
- [ ] `.env.example` has all required variables
- [ ] Environment variables documented
- [ ] Default values are sensible
- [ ] Production configuration reviewed
- [ ] Feature flags configured correctly

### Dependencies
- [ ] Python dependencies in `requirements.txt` are pinned
- [ ] Node.js dependencies in `package.json` are up to date
- [ ] No known vulnerabilities (`npm audit`, `safety check`)
- [ ] Unused dependencies removed
- [ ] License compatibility checked

### Frontend
- [ ] Build succeeds without warnings
- [ ] No console errors in browser
- [ ] Responsive design works on mobile
- [ ] All pages load correctly
- [ ] Forms validate properly
- [ ] Error messages are user-friendly
- [ ] Loading states implemented
- [ ] Accessibility checked (WCAG 2.1)

### Backend
- [ ] API endpoints respond correctly
- [ ] Error handling is comprehensive
- [ ] Logging is appropriate (no sensitive data)
- [ ] Rate limiting configured
- [ ] CORS configured correctly
- [ ] Health check endpoint works
- [ ] API documentation (Swagger) is accurate

### AWS Integration
- [ ] Bedrock model access enabled
- [ ] Marketplace Catalog API permissions verified
- [ ] CloudFormation templates validated
- [ ] IAM roles and policies reviewed
- [ ] CloudWatch logging configured
- [ ] Cost estimation completed

### Deployment
- [ ] Deployment scripts tested
- [ ] Rollback procedure documented
- [ ] Monitoring and alerts configured
- [ ] Backup strategy in place
- [ ] Disaster recovery plan documented
- [ ] Performance benchmarks met

### Legal and Compliance
- [ ] LICENSE file present and correct
- [ ] Copyright notices updated
- [ ] Third-party licenses documented
- [ ] Terms of service reviewed (if applicable)
- [ ] Privacy policy updated (if applicable)
- [ ] AWS Marketplace terms compliance verified

## Version Numbering

Follow Semantic Versioning (SemVer): MAJOR.MINOR.PATCH

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

## Release Process

### 1. Prepare Release

```bash
# Update version in files
# - pyproject.toml
# - frontend/package.json
# - CHANGELOG.md

# Create release branch
git checkout -b release/v1.0.0

# Run tests
python test_agent.py
cd frontend && npm test

# Build frontend
cd frontend && npm run build
```

### 2. Update Documentation

```bash
# Update CHANGELOG.md
# Add release notes
# Update README.md if needed
# Update version numbers
```

### 3. Security Check

```bash
# Check for secrets
git secrets --scan

# Check Python dependencies
safety check

# Check Node.js dependencies
cd frontend && npm audit

# Run security linter
bandit -r backend/ tools/
```

### 4. Create Release

```bash
# Commit changes
git add .
git commit -m "chore: prepare release v1.0.0"

# Merge to main
git checkout main
git merge release/v1.0.0

# Tag release
git tag -a v1.0.0 -m "Release version 1.0.0"

# Push to remote
git push origin main
git push origin v1.0.0
```

### 5. Deploy

```bash
# Deploy to production
python deploy.py --component all

# Verify deployment
curl https://your-domain.com/health

# Monitor logs
# Check CloudWatch logs
# Monitor error rates
```

### 6. Post-Release

- [ ] Verify production deployment
- [ ] Monitor error rates for 24 hours
- [ ] Update project board/issues
- [ ] Announce release (if public)
- [ ] Archive release artifacts
- [ ] Update documentation site

## Rollback Procedure

If issues are discovered after release:

1. **Immediate Actions**
   ```bash
   # Revert to previous version
   git revert <commit-hash>
   git push origin main
   
   # Or rollback deployment
   python cleanup.py
   # Deploy previous version
   ```

2. **Communication**
   - Notify users of the issue
   - Provide workaround if available
   - Estimate time to fix

3. **Investigation**
   - Identify root cause
   - Create hotfix branch
   - Test thoroughly
   - Deploy hotfix

## Hotfix Process

For critical bugs in production:

```bash
# Create hotfix branch from main
git checkout -b hotfix/v1.0.1 main

# Fix the issue
# ... make changes ...

# Test thoroughly
python test_agent.py

# Update version (PATCH increment)
# Update CHANGELOG.md

# Commit and merge
git commit -m "fix: critical bug description"
git checkout main
git merge hotfix/v1.0.1

# Tag and deploy
git tag -a v1.0.1 -m "Hotfix version 1.0.1"
git push origin main v1.0.1

# Deploy
python deploy.py
```

## Support

For release-related questions:
- Technical: [tech@yourdomain.com](mailto:tech@yourdomain.com)
- Security: [security@yourdomain.com](mailto:security@yourdomain.com)

---

**Last Updated:** December 2024
