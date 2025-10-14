# Documentation Guide

## 📚 Documentation Structure

This project has a streamlined documentation set focused on getting you productive quickly.

### Essential Documents

#### 1. **[README.md](../README.md)** - Start Here
- Project overview
- Quick start (3 commands)
- Workflow comparison (AI-Guided vs Manual Form)
- What gets created
- Project status

**Read this first** to understand what the project does and how to get started.

---

#### 2. **[QUICK_START.md](QUICK_START.md)** - Get Running in 5 Minutes
- Step-by-step setup
- Choose your workflow
- First listing creation
- Common issues

**Use this** when you want to get up and running immediately.

---

#### 3. **[GUIDE.md](GUIDE.md)** - Technical Reference
- Complete technical guide
- Both workflows explained
- 8-stage workflow details
- Configuration options
- Architecture overview
- API integration details

**Reference this** when you need technical details or want to understand how it works.

---

#### 4. **[END_TO_END_TEST_GUIDE.md](END_TO_END_TEST_GUIDE.md)** - Testing Guide
- Step-by-step testing with sample data
- All 8 stages with example inputs
- Expected results
- Verification steps

**Use this** to test the system with sample data or learn what each stage requires.

---

#### 5. **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Problem Solving
- Common issues and solutions
- AWS credentials problems
- Bedrock access issues
- API errors
- Validation errors
- Quick fixes table

**Check this** when you encounter errors or issues.

---

#### 6. **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Code Organization
- Visual project structure
- File organization
- Component descriptions
- Usage patterns
- Key components

**Reference this** to understand the codebase organization.

---

#### 7. **[MULTI_AGENT_ARCHITECTURE.md](MULTI_AGENT_ARCHITECTURE.md)** - Architecture Deep Dive
- Multi-agent architecture details
- Master orchestrator + 8 sub-agents
- Data flow diagrams
- State management
- Validation framework
- Design decisions

**Read this** to understand the multi-agent architecture and design patterns.

---

## 🎯 Quick Navigation

### I want to...

**Get started quickly**
→ [README.md](../README.md) → [QUICK_START.md](QUICK_START.md)

**Understand the workflows**
→ [README.md](../README.md) (Workflow comparison) → [GUIDE.md](GUIDE.md)

**Test with sample data**
→ [END_TO_END_TEST_GUIDE.md](END_TO_END_TEST_GUIDE.md)

**Fix an error**
→ [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

**Understand the architecture**
→ [MULTI_AGENT_ARCHITECTURE.md](MULTI_AGENT_ARCHITECTURE.md)

**Understand the code**
→ [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) → [GUIDE.md](GUIDE.md)

---

## 📖 Reading Order

### For New Users:
1. README.md - Understand what it does
2. QUICK_START.md - Get it running
3. END_TO_END_TEST_GUIDE.md - Test with sample data
4. TROUBLESHOOTING.md - If you hit issues

### For Developers:
1. README.md - Project overview
2. GUIDE.md - Technical details
3. PROJECT_STRUCTURE.md - Code organization
4. docs/MULTI_AGENT_ARCHITECTURE.md - Architecture deep dive

### For Contributors:
1. All of the above
2. Review code in agent/ directory
3. Check config/ for configuration options

---

## 🔧 Configuration Files

- **config/agent_config.yaml** - Bedrock model, Knowledge Base settings
- **config/marketplace_config.yaml** - AWS Marketplace categories, validation rules
- **config/multi_agent_config.yaml** - Multi-agent system configuration

---

## 📝 What Was Removed

To keep documentation focused, we removed:
- Temporary fix notes (HOTFIX_GUIDED_APP.md)
- Implementation details (GUIDED_APP_COMPLETE.md)
- Cleanup summaries (CLEANUP_SUMMARY.md)
- Archived documentation (docs/archive/)
- Redundant workflow comparisons
- Intermediate development notes

All essential information has been consolidated into the 7 core documents above.

---

## 🎓 Learning Path

### Beginner Path (30 minutes)
1. README.md (5 min)
2. QUICK_START.md (10 min)
3. END_TO_END_TEST_GUIDE.md (15 min)

### Intermediate Path (1 hour)
1. Beginner Path
2. GUIDE.md (20 min)
3. TROUBLESHOOTING.md (10 min)

### Advanced Path (2 hours)
1. Intermediate Path
2. PROJECT_STRUCTURE.md (20 min)
3. docs/MULTI_AGENT_ARCHITECTURE.md (40 min)

---

## 💡 Tips

- **Start with README.md** - It's the entry point
- **Use QUICK_START.md** - Don't skip the setup verification
- **Keep TROUBLESHOOTING.md handy** - Most issues are documented
- **Reference GUIDE.md** - When you need technical details
- **Read ARCHITECTURE.md** - To understand design decisions

---

## 🔄 Documentation Updates

This documentation is maintained to stay current with the codebase. If you find outdated information, please update it or file an issue.

**Last Updated:** October 2025
**Version:** 2.0 (Consolidated)
