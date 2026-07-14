# ==============================================================================
# CaptionDB Production Dockerfile
# ==============================================================================

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

# ------------------------------------------------------------------------------
# System dependencies
# ------------------------------------------------------------------------------

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------------------------
# Copy project metadata first
# ------------------------------------------------------------------------------

COPY pyproject.toml ./
COPY README.md ./

# ------------------------------------------------------------------------------
# Copy application
# ------------------------------------------------------------------------------

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./

# ------------------------------------------------------------------------------
# Install Python dependencies
# ------------------------------------------------------------------------------

RUN pip install --upgrade pip
RUN pip install .

# ------------------------------------------------------------------------------
# Create non-root user
# ------------------------------------------------------------------------------

RUN useradd -m captiondb

RUN mkdir -p \
    /app/data/storage \
    /app/data/temp \
    /app/data/logs

RUN chown -R captiondb:captiondb /app

USER captiondb

# ------------------------------------------------------------------------------
# Render exposes PORT
# ------------------------------------------------------------------------------

EXPOSE 8000

# ------------------------------------------------------------------------------
# Healthcheck
# ------------------------------------------------------------------------------

COPY --chown=captiondb:captiondb migrations ./migrations
COPY --chown=captiondb:captiondb alembic.ini ./

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
CMD curl -f http://localhost:${PORT}/api/v1/health/live || exit 1

# ------------------------------------------------------------------------------
# Startup
# ------------------------------------------------------------------------------

CMD sh -c "python -m alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"