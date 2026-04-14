#!/bin/bash
# ─── AARKAAI Backend – Production Startup Script ─────────────────────────────
#
# Usage:
#   chmod +x start.sh
#   ./start.sh
#
# Or with PM2:
#   pm2 start start.sh --name aarkaai-backend

set -e

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Defaults
HOST="${AARKAAI_HOST:-0.0.0.0}"
PORT="${AARKAAI_PORT:-5000}"
WORKERS="${AARKAAI_WORKERS:-1}"
LOG_LEVEL="${AARKAAI_LOG_LEVEL:-info}"

echo "============================================================"
echo "  AARKAAI Backend – Production Mode"
echo "  Host: ${HOST}:${PORT}"
echo "  Workers: ${WORKERS}"
echo "  Log Level: ${LOG_LEVEL}"
echo "============================================================"

# Create workspace directory
mkdir -p workspace

# Run with uvicorn directly (recommended for llama.cpp single-model process)
exec python -m uvicorn main:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --log-level "$LOG_LEVEL" \
    --access-log \
    --no-use-colors
