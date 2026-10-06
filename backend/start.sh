#!/usr/bin/env bash

# ==============================================================================
# start.sh - Interview AI Backend
#
# Responsibilities:
#   1. Wait for PostgreSQL
#   2. Run Alembic migrations
#   3. Start FastAPI (Uvicorn)
# ==============================================================================

set -e

echo ""
echo "=========================================="
echo "Starting Interview AI Backend..."
echo "=========================================="

# ==============================================================================
# Wait for PostgreSQL
# ==============================================================================

echo ""
echo "[1/3] Waiting for PostgreSQL..."

until python - <<EOF
import os
import time
import psycopg2

try:
    psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        dbname=os.environ["DB_NAME"],
    ).close()
except Exception:
    raise SystemExit(1)
EOF
do
    echo "PostgreSQL not ready. Retrying in 2 seconds..."
    sleep 2
done

echo "PostgreSQL is ready."

# ==============================================================================
# Run Alembic Migrations
# ==============================================================================

echo ""
echo "[2/3] Running Alembic migrations..."

alembic upgrade head

echo "Database migrations completed."

# ==============================================================================
# Start FastAPI
# ==============================================================================

echo ""
echo "[3/3] Starting FastAPI..."

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --no-access-log \
    --log-level info