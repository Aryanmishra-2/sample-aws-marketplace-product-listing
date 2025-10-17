# Documentation

## Main Documentation
- **[../DOCUMENTATION.md](../DOCUMENTATION.md)** - Complete user guide with quick start, pricing models, and publishing guide
- **[../README.md](../README.md)** - Project overview and quick reference

## Architecture
- **[MULTI_AGENT_ARCHITECTURE.md](MULTI_AGENT_ARCHITECTURE.md)** - Technical architecture and design patterns

## Utilities
- **[../utils.py](../utils.py)** - Testing and debugging utilities
  - `python utils.py test` - Verify setup
  - `python utils.py bedrock` - Check Bedrock models
  - `python utils.py changeset <id>` - Check changeset status

## Quick Start

```bash
# Install
pip install -r requirements.txt
./setup_aws_credentials.sh

# Run
streamlit run streamlit_guided_app.py
```

That's it! The app will guide you through creating your AWS Marketplace listing with auto-publish to Limited stage enabled by default.
