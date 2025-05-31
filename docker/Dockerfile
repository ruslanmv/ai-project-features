# docker/Dockerfile
# ────────────────────────────────────────────────────────────────────────────
# Base image with Python 3.11 slim
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy only pyproject.toml and requirements.txt first (to leverage Docker layer caching)
COPY pyproject.toml .
COPY requirements.txt .

# Install system dependencies (if needed) and Python packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       git \
    && pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get remove -y build-essential \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Copy the rest of the application source code
COPY . .

# Make the entrypoint script executable
RUN chmod +x /app/docker/entrypoint.sh

# Expose port for the Flask API (default: 9000)
EXPOSE 9000

# Use our custom entrypoint
ENTRYPOINT ["/app/docker/entrypoint.sh"]
