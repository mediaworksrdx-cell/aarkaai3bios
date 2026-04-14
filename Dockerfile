# ─── AARKAAI Backend ──────────────────────────────────────────────────────────
# Multi-stage build optimized for CPU inference

FROM python:3.11-slim AS base

# System dependencies for llama-cpp-python compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security
RUN useradd --create-home --shell /bin/bash aarkaai
WORKDIR /home/aarkaai/app

# Install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create workspace directory for sandboxed tools
RUN mkdir -p workspace && chown -R aarkaai:aarkaai /home/aarkaai

# Switch to non-root user
USER aarkaai

# Environment defaults
ENV AARKAAI_ENV=production \
    AARKAAI_HOST=0.0.0.0 \
    AARKAAI_PORT=5000 \
    AARKAAI_SAFE_DIR=/home/aarkaai/app/workspace \
    AARKAAI_LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

EXPOSE 5000

CMD ["python", "main.py"]
