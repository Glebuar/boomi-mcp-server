FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r mcp && useradd -r -g mcp mcp

WORKDIR /app

# Copy only requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY .well-known/ ./.well-known/
COPY LICENSE README.md ./

# Set ownership
RUN chown -R mcp:mcp /app

# Switch to non-root user
USER mcp

# Environment variables with defaults
ENV PYTHONPATH=/app/src \
    BOOMI_ACCOUNT="" \
    BOOMI_USER="" \
    BOOMI_SECRET="" \
    MCP_SERVER_NAME="boomi-mcp-server" \
    PORT=8080

# Health check - verify the process is running
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD pgrep -f "python -m boomi_mcp_server.server" || exit 1

EXPOSE 8080

# Run the server directly with Python
CMD ["python", "-m", "boomi_mcp_server.server", "--transport", "sse", "--port", "8080"]
