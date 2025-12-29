# syntax=docker/dockerfile:1

# Multi-stage build for smaller image size
FROM python:3.14-slim AS builder

# OCI Labels
LABEL org.opencontainers.image.source="https://github.com/SyafiqHadzir/orst-scrapper"
LABEL org.opencontainers.image.description="ORST Dictionary Scraper - Production-grade tool to sync Thai Royal Institute Dictionary"
LABEL org.opencontainers.image.licenses="GPL-3.0"
LABEL org.opencontainers.image.authors="Syafiq Hadzir <inquiry@syafiqhadzir.dev>"
LABEL org.opencontainers.image.version="1.1.0"

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Final stage
FROM python:3.14-slim

# OCI Labels (repeated for final image)
LABEL org.opencontainers.image.source="https://github.com/SyafiqHadzir/orst-scrapper"
LABEL org.opencontainers.image.description="ORST Dictionary Scraper"
LABEL org.opencontainers.image.licenses="GPL-3.0"
LABEL org.opencontainers.image.version="1.1.0"

WORKDIR /app

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy wheels from builder
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

# Install dependencies
RUN pip install --no-cache /wheels/*

# Copy source code
COPY . .

# Change ownership
RUN chown -R appuser:appuser /app

# Create data and reports directories
RUN mkdir -p /app/data /app/reports && chown -R appuser:appuser /app/data /app/reports

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import scripts.config; print('healthy')" || exit 1

# Default command
ENTRYPOINT ["python", "update_royin_dictionary.py"]
