# ==============================================================================
# Stage 1: Builder
# ==============================================================================
FROM python:3.12-slim AS builder

# Set environment variables to optimize Python for building
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy project configuration for hatchling dependency resolution
COPY pyproject.toml README.md ./

# Create an isolated virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install production dependencies. We omit the [test] extra.
RUN pip install --upgrade pip && pip install .

# ==============================================================================
# Stage 2: Production
# ==============================================================================
FROM python:3.12-slim AS production

# Set production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Install curl for the Docker healthcheck and ffmpeg for metadata extraction
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root system user (UID/GID 10001) for security
RUN groupadd -g 10001 captiondb && \
    useradd -u 10001 -g captiondb -s /bin/false -m captiondb

# Create volume mount points and assign permissions to the non-root user
RUN mkdir -p /app/data/storage /app/data/temp /app/data/logs && \
    chown -R captiondb:captiondb /app/data

WORKDIR /app

# Copy the pre-built virtual environment from the builder stage
COPY --from=builder --chown=captiondb:captiondb /opt/venv /opt/venv

# Copy the application source code
COPY --chown=captiondb:captiondb app ./app

# Drop root privileges immediately
USER captiondb

EXPOSE 8000

# Liveness probe targeting the Phase 1.6 health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/v1/health/live || exit 1
# Start the application via Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]
