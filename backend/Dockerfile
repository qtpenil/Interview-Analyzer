# ══════════════════════════════════════════════════════════════════════════════
# Dockerfile — Interview AI Backend (Production)
#
# Backend application image used by Docker Compose.
#
# This image is shared by multiple services:
#   • FastAPI API Server
#   • Celery Worker
#
# External services managed by Docker Compose:
#   • PostgreSQL
#   • Redis
#
# Base Image:
#   • python:3.11-slim
# ══════════════════════════════════════════════════════════════════════════════

FROM python:3.11-slim

# ─────────────────────────────────────────────────────────────────────────────
# Environment Variables
# ─────────────────────────────────────────────────────────────────────────────
#
# PYTHONUNBUFFERED
#     Immediately flush stdout/stderr to Docker logs.
#
# PYTHONDONTWRITEBYTECODE
#     Prevent generation of .pyc files.
#
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# ─────────────────────────────────────────────────────────────────────────────
# System Dependencies
# ─────────────────────────────────────────────────────────────────────────────
#
# ffmpeg
#     Audio/video processing.
#
# libchromaprint-tools
#     fpcalc for audio fingerprinting.
#
# build-essential + gcc
#     Required for native Python package compilation.
#
# libffi-dev
#     Required by cffi.
#
# libssl-dev
#     Required by cryptography.
#
# libpq-dev
#     PostgreSQL client libraries (psycopg2).
#
# pkg-config
#     Helps pip locate native libraries.
#
# curl
#     Used by Docker HEALTHCHECK.
#
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libchromaprint-tools \
        build-essential \
        gcc \
        libffi-dev \
        libssl-dev \
        libpq-dev \
        postgresql-client \
        pkg-config \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ─────────────────────────────────────────────────────────────────────────────
# Working Directory
# ─────────────────────────────────────────────────────────────────────────────
WORKDIR /app

# ─────────────────────────────────────────────────────────────────────────────
# Python Dependencies
# ─────────────────────────────────────────────────────────────────────────────
#
# Copy requirements first to maximize Docker layer caching.
#
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ─────────────────────────────────────────────────────────────────────────────
# Application Source
# ─────────────────────────────────────────────────────────────────────────────
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .
COPY start.sh .

# ─────────────────────────────────────────────────────────────────────────────
# Runtime Directories
# ─────────────────────────────────────────────────────────────────────────────
RUN mkdir -p \
    storage/whisper \
    storage/uploads \
    storage/reports \
    uploads \
    logs

# ─────────────────────────────────────────────────────────────────────────────
# Startup Script Permissions
# ─────────────────────────────────────────────────────────────────────────────
RUN chmod +x start.sh

# ─────────────────────────────────────────────────────────────────────────────
# Non-Root User
# ─────────────────────────────────────────────────────────────────────────────
#
# Containers should not run as root.
#
RUN groupadd --gid 1000 appuser \
    && useradd \
        --uid 1000 \
        --gid 1000 \
        --no-create-home \
        --shell /bin/bash \
        appuser \
    && chown -R appuser:appuser /app

USER appuser

# ─────────────────────────────────────────────────────────────────────────────
# Expose FastAPI Port
# ─────────────────────────────────────────────────────────────────────────────
EXPOSE 8000

# ─────────────────────────────────────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────────────────────────────────────
#
# Verifies that the FastAPI service is responding.
#
HEALTHCHECK --interval=30s \
            --timeout=5s \
            --start-period=15s \
            --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# ─────────────────────────────────────────────────────────────────────────────
# Entrypoint
# ─────────────────────────────────────────────────────────────────────────────
#
# start.sh is responsible for:
#
#   1. Waiting for PostgreSQL (optional but recommended)
#   2. Running Alembic migrations
#   3. Starting FastAPI
#
# NOTE:
# Redis and Celery are NOT started here.
# Docker Compose starts them as independent services.
#
CMD ["./start.sh"]