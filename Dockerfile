# =============================================================================
# Aetheris UI v1.0.0 - Production Dockerfile
# Multi-stage build with dual-mode support (Headless CI / Interactive Dev)
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Builder - Install and pin all dependencies
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2: Runtime - Minimal image with only what's needed
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

# --- Build-time arguments for mode selection ---
ARG RUN_MODE=headless
ARG MESA_GL_VERSION_OVERRIDE=3.3

# --- Environment: Global portability ---
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    MESA_GL_VERSION_OVERRIDE=${MESA_GL_VERSION_OVERRIDE}

# Headless mode is the default; override with --env RUN_MODE=interactive
ENV RUN_MODE=${RUN_MODE} \
    MGL_WINDOW_BACKEND=headless

# --- System dependencies: OpenGL + Xvfb + Tkinter (conditional) ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-dri \
    libgl1 \
    libegl1 \
    libgles2 \
    xvfb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Tkinter only for interactive mode (saves ~40MB in headless)
RUN if [ "${RUN_MODE}" = "interactive" ]; then \
    apt-get update && apt-get install -y --no-install-recommends \
    python3-tk \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*; \
    fi

# --- Copy pinned Python packages from builder stage ---
COPY --from=builder /install /usr/local

# --- Working directory ---
WORKDIR /app

# --- Copy project files ---
COPY . .

# --- Health check (headless validation) ---
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "from core.engine import AetherEngine; e = AetherEngine(); print('OK')" || exit 1

# --- Entrypoint script for dual-mode ---
RUN printf '#!/bin/bash\n\
set -e\n\
if [ "$RUN_MODE" = "interactive" ]; then\n\
    exec "$@"\n\
else\n\
    exec xvfb-run -a --server-args="-screen 0 1920x1080x24" "$@"\n\
fi\n' /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

# Default: run core test suite
CMD ["python3", "-m", "pytest", "tests/", "-v", "-m", "core"]
