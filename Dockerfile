# Dockerfile for Contextor MCP Server
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Configure poetry
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy source code
COPY contextor/ ./contextor/

# Create sourcedocs directory
RUN mkdir -p /app/sourcedocs

# Set environment variables
ENV SOURCEDOCS_PATH=/app/sourcedocs
ENV PYTHONPATH=/app

# Expose port for SSE transport
EXPOSE 8080

# Health check endpoint (basic file check)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD test -d /app/sourcedocs || exit 1

# Default command
CMD ["python", "-m", "contextor.mcp_server.server", "--host", "0.0.0.0", "--port", "8080"]
