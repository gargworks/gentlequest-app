# ============================================================
# GentleQuest Flask App — Production Dockerfile (Render)
# Multi-stage: Flutter Web build (cached) → Python Flask serve.
# Cache-aware layer order: pubspec → pub get → lib/ → flutter build web.
# Backend-only changes skip Flutter rebuild via Docker layer caching.
# DO NOT replace with Nucleus content.
# Nucleus Dockerfiles: mcp-server-nucleus/Dockerfile, deploy/Dockerfile.nucleus
# ============================================================

# ===== Stage 1: Flutter Web build =====
# Cirrus Labs Flutter image is the canonical Flutter Docker image
# used by most CI pipelines. Stable + maintained.
FROM ghcr.io/cirruslabs/flutter:stable AS flutter-build

USER root
WORKDIR /flutter-app

# Copy dependency manifests first — this layer is cached unless
# pubspec.yaml or pubspec.lock changes (e.g. a `flutter pub add`).
COPY ai_buddy_web/pubspec.yaml ai_buddy_web/pubspec.lock ./
RUN flutter pub get

# Copy Flutter source — this layer is cached unless lib/, web/,
# or assets/ changes. Backend-only PRs skip this rebuild entirely.
COPY ai_buddy_web/lib ./lib
COPY ai_buddy_web/web ./web
COPY ai_buddy_web/assets ./assets
COPY ai_buddy_web/analysis_options.yaml ./analysis_options.yaml

# Compile to release-mode JS + WASM. Cached unless prior layers invalidate.
RUN flutter build web --release


# ===== Stage 2: Python Flask backend =====
FROM python:3.11-slim

WORKDIR /app

# System dependencies (apt cache layer)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies (cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python application code
COPY . .

# Overlay the freshly built Flutter Web bundle on top of static/
# (overrides any pre-committed static/* files). clinical-dashboard.html
# from the repo's static/ is preserved because COPY --from merges into
# the existing directory rather than replacing it.
COPY --from=flutter-build /flutter-app/build/web/ ./static/

# Runtime environment
ENV PORT=5055
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
EXPOSE 5055

# Entrypoint handles DATABASE_URL secret expansion
COPY scripts/cloud_run_entrypoint.sh .
RUN chmod +x cloud_run_entrypoint.sh
CMD ["./cloud_run_entrypoint.sh"]
