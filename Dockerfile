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

# Create non-root user and set ownership
RUN groupadd --system --gid 1001 appuser && \
    useradd --system --uid 1001 --gid appuser appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port for AgentCore runtime
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Run the AgentCore app
CMD ["python", "agentcore_app.py"]
