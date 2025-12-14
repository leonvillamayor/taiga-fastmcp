# Dockerfile for Taiga MCP Server
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install uv for fast dependency management
RUN pip install uv

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user BEFORE installing dependencies
USER appuser

# Copy dependency files first for better caching
COPY --chown=appuser:appuser pyproject.toml uv.lock README.md ./

# Install dependencies (no-editable to avoid build issues)
RUN uv sync --frozen --no-dev --no-editable

# Copy application code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser main.py ./

# Expose MCP HTTP port
EXPOSE 8000

# Default environment variables for HTTP transport
ENV MCP_TRANSPORT=http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; req = urllib.request.Request('http://localhost:8000/mcp', headers={'Accept': 'application/json, text/event-stream'}, method='POST'); urllib.request.urlopen(req, timeout=5)" || exit 1

# Run the MCP server using the virtual environment created by uv
CMD [".venv/bin/python", "-m", "src.server"]
