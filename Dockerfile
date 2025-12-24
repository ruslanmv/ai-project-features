# ═══════════════════════════════════════════════════════════════════════════
# Aurora AI Refactor Assistant - Production Dockerfile
# ═══════════════════════════════════════════════════════════════════════════
# Multi-stage build optimized for production deployment with minimal image size
# and maximum security using distroless Python base.
#
# Author: Ruslan Magana (ruslanmv.com)
# License: Apache 2.0
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
# Stage 1: Builder - Install dependencies and build application
# ═══════════════════════════════════════════════════════════════════════════
FROM python:3.11-slim as builder

# Set build-time environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Set working directory
WORKDIR /build

# Copy dependency files
COPY pyproject.toml ./
COPY README.md ./

# Install dependencies using uv
RUN uv pip install --system -e .

# Copy application source
COPY src/ ./src/

# Install the application
RUN uv pip install --system -e .

# ═══════════════════════════════════════════════════════════════════════════
# Stage 2: Runtime - Minimal production image with distroless base
# ═══════════════════════════════════════════════════════════════════════════
FROM python:3.11-slim as runtime

# Create non-root user for security
RUN groupadd -r aurora && useradd -r -g aurora aurora

# Set runtime environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/aurora/.local/bin:$PATH" \
    AURORA_HOME=/app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/aurora /usr/local/bin/aurora

# Copy application source
COPY --chown=aurora:aurora src/ ./src/

# Switch to non-root user
USER aurora

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD aurora validate-config || exit 1

# Set entrypoint
ENTRYPOINT ["aurora"]

# Default command shows help
CMD ["--help"]

# ═══════════════════════════════════════════════════════════════════════════
# Build and Run Instructions:
# ═══════════════════════════════════════════════════════════════════════════
# Build:
#   docker build -t aurora-refactor:latest .
#
# Run CLI:
#   docker run --rm -it --env-file .env -v $(pwd):/workspace aurora-refactor:latest refactor /workspace/project.zip "Add logging"
#
# Run Server:
#   docker run --rm -p 8000:8000 --env-file .env aurora-refactor:latest server
#
# Interactive Shell:
#   docker run --rm -it --entrypoint /bin/bash aurora-refactor:latest
# ═══════════════════════════════════════════════════════════════════════════
