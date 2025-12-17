FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app

# All environment variables in one layer
ENV UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_PROGRESS=1 \
    PYTHONUNBUFFERED=1 \
    DOCKER_CONTAINER=1 \
    AWS_REGION=us-east-1 \
    AWS_DEFAULT_REGION=us-east-1

COPY requirements.txt requirements.txt
# Install from requirements file
RUN uv pip install -r requirements.txt

RUN uv pip install aws-opentelemetry-distro==0.12.2

# Copy entire project BEFORE switching to non-root user (respecting .dockerignore)
COPY . .

# Ensure agents and backend directories are present
RUN ls -la /app && ls -la /app/agents && ls -la /app/backend

# Create non-root user and set ownership
RUN useradd -m -u 1000 bedrock_agentcore && chown -R bedrock_agentcore:bedrock_agentcore /app
USER bedrock_agentcore

EXPOSE 9000
EXPOSE 8000
EXPOSE 8080

# Use the full module path
CMD ["opentelemetry-instrument", "python", "-m", "agentcore_app"]
