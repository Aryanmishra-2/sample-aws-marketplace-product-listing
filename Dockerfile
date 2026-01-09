# Dockerfile for AgentCore Backend
# Use ECR Public Gallery to avoid Docker Hub rate limits
FROM public.ecr.aws/docker/library/python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install bedrock-agentcore runtime
RUN pip install --no-cache-dir bedrock-agentcore

# Copy application code
COPY agentcore_app.py .
COPY agents/ ./agents/
COPY backend/ ./backend/
COPY tools/ ./tools/

# Expose port for AgentCore runtime
EXPOSE 8080

# Run the AgentCore app
CMD ["python", "agentcore_app.py"]
