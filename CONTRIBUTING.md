# Contributing to AWS Marketplace Seller Portal

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## 🚀 Getting Started

1. **Fork the repository**
2. **Clone your fork**
   ```bash
   git clone https://github.com/your-username/ai-agent-marketplace.git
   cd ai-agent-marketplace
   ```
3. **Set up development environment** (see README.md)
4. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 📋 Development Guidelines

### Code Style

#### TypeScript/JavaScript (Frontend)
- Use TypeScript for all new code
- Follow ESLint configuration
- Use functional components with hooks
- Prefer `const` over `let`
- Use meaningful variable names
- Add JSDoc comments for complex functions

#### Python (Backend)
- Follow PEP 8 style guide
- Use type hints for function parameters and returns
- Add docstrings for all functions and classes
- Keep functions focused and small
- Use meaningful variable names

### Project Structure

```
frontend/src/
├── app/              # Next.js pages (one per route)
├── components/       # Reusable React components
├── lib/             # Utilities, store, helpers
└── types/           # TypeScript type definitions

backend/
└── main.py          # FastAPI application with agent integration

tools/
├── __init__.py           # Tool exports
├── marketplace_tools.py  # AWS Marketplace operations
├── bedrock_tools.py      # AI analysis and generation
├── saas_tools.py         # SaaS infrastructure
└── help_tools.py         # Documentation and help
```

### Commit Messages

Use conventional commit format:
```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(frontend): add real-time CloudFormation monitoring
fix(backend): handle stack not found error gracefully
docs(readme): update installation instructions
```

## 🧪 Testing

### Frontend Testing
```bash
cd frontend
npm run test        # Run tests
npm run test:watch  # Watch mode
npm run lint        # Lint code
```

### Backend Testing
```bash
# From project root
source venv/bin/activate
pytest tests/       # Run tests
pytest --cov        # With coverage
```

### Manual Testing Checklist
- [ ] Test with valid AWS credentials
- [ ] Test with invalid credentials
- [ ] Test all workflow steps
- [ ] Test error handling
- [ ] Test CloudFormation deployment
- [ ] Test on different browsers
- [ ] Test responsive design

## 🐛 Bug Reports

When reporting bugs, include:
1. **Description** - Clear description of the issue
2. **Steps to Reproduce** - Detailed steps
3. **Expected Behavior** - What should happen
4. **Actual Behavior** - What actually happens
5. **Environment** - OS, browser, Node/Python versions
6. **Screenshots** - If applicable
7. **Logs** - Relevant error logs

## ✨ Feature Requests

When requesting features, include:
1. **Use Case** - Why is this needed?
2. **Proposed Solution** - How should it work?
3. **Alternatives** - Other approaches considered
4. **Additional Context** - Any other relevant info

## 🔄 Pull Request Process

1. **Update Documentation**
   - Update README.md if needed
   - Add/update comments in code
   - Update CHANGELOG.md

2. **Test Your Changes**
   - Run all tests
   - Test manually
   - Check for console errors

3. **Create Pull Request**
   - Use descriptive title
   - Reference related issues
   - Describe changes made
   - Include screenshots if UI changes

4. **Code Review**
   - Address review comments
   - Keep PR focused and small
   - Be responsive to feedback

5. **Merge Requirements**
   - All tests passing
   - Code review approved
   - No merge conflicts
   - Documentation updated

## 📝 Documentation

### Code Documentation
- Add JSDoc/docstrings for public APIs
- Comment complex logic
- Keep comments up to date
- Use clear, concise language

### User Documentation
- Update README.md for user-facing changes
- Add examples for new features
- Update troubleshooting section
- Keep documentation accurate

## 🏗️ Architecture Decisions

When making significant architectural changes:
1. Open an issue for discussion first
2. Explain the problem and proposed solution
3. Consider backwards compatibility
4. Document the decision

## 🔐 Security

- Never commit credentials or secrets
- Use environment variables for sensitive data
- Follow AWS security best practices
- Report security issues privately

## 📦 Dependencies

### Adding Dependencies

**Frontend:**
```bash
cd frontend
npm install package-name
```

**Backend:**
```bash
pip install package-name
# Add to requirements.txt
```

### Updating Dependencies
- Keep dependencies up to date
- Test after updates
- Document breaking changes

## 🎯 Areas for Contribution

### High Priority
- [ ] Automated testing suite
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Error handling improvements
- [ ] Performance optimizations

### Medium Priority
- [ ] Multi-region support
- [ ] Batch operations
- [ ] Advanced analytics
- [ ] Listing templates
- [ ] Export/import features

### Good First Issues
- [ ] UI/UX improvements
- [ ] Documentation updates
- [ ] Bug fixes
- [ ] Code cleanup
- [ ] Test coverage

## 💬 Communication

- **Issues** - For bugs and feature requests
- **Pull Requests** - For code contributions
- **Discussions** - For questions and ideas

## 📜 Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Assume good intentions
- Help others learn and grow

## ⚖️ License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## 🙏 Recognition

Contributors will be recognized in:
- CHANGELOG.md
- Project documentation
- Release notes

Thank you for contributing! 🎉
