# Dockerfile — Diwanic Python Application
# Multi-stage build for a lean production image

# ──────────────────────────────────────────────
# Stage 1: Builder — install dependencies
# ──────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies needed for our packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifests
COPY pyproject.toml ./

# Install Python packages into an isolated venv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && \
    pip install -e ".[dev]"

# ──────────────────────────────────────────────
# Stage 2: Runtime — minimal production image
# ──────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtualenv from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code (exclude .venv, tests, docs, etc.)
COPY diwanic/ ./diwanic/
COPY .env.example ./

# Create tests directory if needed (for golden_set.jsonl)
RUN mkdir -p tests

# Non-root user for security
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

# Expose Gradio default port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860')" || exit 1

# Run the Gradio UI
CMD ["python", "-m", "diwanic.app.ui"]