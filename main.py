#!/usr/bin/env python3
"""
Simple AgentCore entrypoint wrapper.
This file imports and runs the main agentcore_app.
"""

# Import everything from agentcore_app
from agentcore_app import app, handle_request

if __name__ == "__main__":
    app.run(port=8080)
