# =============================================================================
# pivona — Production Dockerfile
# python:3.11-slim base
# Tag: ghcr.io/onebyjorah/pivona:latest
# =============================================================================

FROM python:3.14-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user --upgrade pip && \
    pip install --no-cache-dir --user gunicorn && \
    pip install --no-cache-dir --user -r requirements.txt

# ---- Runtime Stage ----
FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1

# Create non-root user
RUN groupadd -r pivona && useradd -r -g pivona -d /app -s /sbin/nologin pivona

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /usr/local

# Create application and data directories
RUN mkdir -p /app /var/lib/pivona

# Copy application code
COPY . /app
WORKDIR /app

# Ensure template directory exists
RUN mkdir -p /app/template

# Set ownership
RUN chown -R pivona:pivona /app /var/lib/pivona

# Switch to non-root user
USER pivona

# Expose application port
EXPOSE 5000

# Healthcheck — verify the app responds
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/healthz')" || exit 1

# Run with gunicorn (production WSGI server)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "wsgi:app"]
