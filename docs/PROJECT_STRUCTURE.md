# Project Structure

## Quick Navigation

```
MPAgent/
│
├── 🚀 START HERE
│   └── streamlit_launcher.py          # Choose your workflow
│
├── 📱 Applications
│   ├── streamlit_guided_app.py        # AI-guided (5-10 min)
│   ├── streamlit_form_app.py          # Manual form (20-30 min)
│   └── create_product_simple.py       # CLI tool
│
├── 🔧 Utilities
│   ├── check_changeset_status.py      # Check API status
│   ├── check_bedrock_models.py        # Check model access
│   ├── test_setup.py                  # Verify setup
│   └── setup_aws_credentials.sh       # AWS setup
│
├── 🤖 Agent System
│   └── agent/
│       ├── marketplace_agent_v2.py    # Main agent
│       ├── orchestrator.py            # Workflow manager
│       ├── sub_agents/                # 8 specialized agents
│       │   ├── product_information_agent.py
│       │   ├── fulfillment_agent.py
│       │   ├── pricing_config_agent.py
│       │   ├── price_review_agent.py
│       │   ├── refund_policy_agent.py
│       │   ├── eula_config_agent.py
│       │   ├── offer_availability_agent.py
│       │   └── allowlist_agent.py
│       ├── tools/
│       │   ├── listing_tools.py       # AWS API integration
│       │   ├── knowledge_base_tools.py
│       │   └── stage_completion_tools.py
│       └── agentcore/                 # Runtime components
│           ├── runtime.py
│           ├── gateway.py
│           ├── identity.py
│           └── memory.py
│
├── ⚙️ Configuration
│   └── config/
│       ├── agent_config.yaml          # Agent settings
│       ├── marketplace_config.yaml    # Validation rules
│       └── multi_agent_config.yaml    # Multi-agent config
│
└── 📚 Documentation
    ├── README.md                      # Main documentation
    ├── QUICK_START.md                 # Getting started
    ├── GUIDE.md                       # Technical guide
    ├── END_TO_END_TEST_GUIDE.md       # Testing guide
    ├── TROUBLESHOOTING.md             # Problem solving
    ├── AI_GUIDED_WORKFLOW.md          # AI workflow details
    ├── WORKFLOWS_COMPARISON.md        # Workflow comparison
    ├── GUIDED_APP_COMPLETE.md         # Guided app docs
    ├── CLEANUP_SUMMARY.md             # Cleanup details
    └── PROJECT_STRUCTURE.md           # This file
```

## File Count Summary

- **Applications:** 3 files
- **Utilities:** 4 files
- **Agent System:** 20+ files
- **Configuration:** 3 files
- **Documentation:** 10 files

**Total:** ~40 essential files (down from 50+)

## Usage Patterns

### For New Users
```bash
# 1. Setup
python3 test_setup.py

# 2. Launch
streamlit run streamlit_launcher.py

# 3. Choose AI-Guided workflow
```

### For Experienced Users
```bash
# Direct to manual form
streamlit run streamlit_form_app.py
```

### For Developers
```bash
# Check agent imports
python3 -c "from agent import MarketplaceListingAgentV2; print('OK')"

# Run diagnostics
python3 check_bedrock_models.py
```

## Key Components

### 1. Streamlit Apps (User Interface)
- **streamlit_launcher.py** - Workflow selector with comparison
- **streamlit_guided_app.py** - AI-powered automation
- **streamlit_form_app.py** - Manual step-by-step forms

### 2. Agent System (Backend)
- **marketplace_agent_v2.py** - Main orchestrator
- **orchestrator.py** - Workflow state management
- **sub_agents/** - 8 specialized agents for each stage
- **tools/** - AWS API integration and utilities

### 3. Configuration
- **agent_config.yaml** - Bedrock model, KB settings
- **marketplace_config.yaml** - Validation rules, categories
- **multi_agent_config.yaml** - Sub-agent configurations

### 4. Documentation
- **README.md** - Start here
- **QUICK_START.md** - 3-step setup
- **GUIDE.md** - Complete technical reference
- **END_TO_END_TEST_GUIDE.md** - Testing with sample data

## Dependencies

```
boto3              # AWS SDK
streamlit          # Web UI
pyyaml             # Config files
pydantic           # Data validation
python-dotenv      # Environment variables
```

## AWS Services Used

- **AWS Bedrock** - Claude AI models
- **AWS Bedrock Knowledge Bases** - Documentation retrieval
- **AWS Marketplace Catalog API** - Listing creation

## Development Status

✅ **Production Ready**
- All 8 stages implemented
- AWS API integration complete
- Real-time validation working
- End-to-end tested
- Documentation complete

## Next Steps

1. **Setup:** Run `python3 test_setup.py`
2. **Configure:** Update `config/agent_config.yaml`
3. **Launch:** Run `streamlit run streamlit_launcher.py`
4. **Create:** Follow the guided workflow

## Support

- **Issues:** Check TROUBLESHOOTING.md
- **Testing:** See END_TO_END_TEST_GUIDE.md
- **Architecture:** See docs/MULTI_AGENT_ARCHITECTURE.md
