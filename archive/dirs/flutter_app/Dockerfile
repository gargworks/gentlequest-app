# Stage 1: Build Flutter Web App
FROM debian:bullseye-slim AS build

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Flutter SDK
WORKDIR /usr/local
RUN git clone https://github.com/flutter/flutter.git -b stable
ENV PATH="/usr/local/flutter/bin:/usr/local/flutter/bin/cache/dart-sdk/bin:${PATH}"

# Run flutter doctor
RUN flutter doctor

# Copy app source
WORKDIR /app
COPY . .

# Build web release
# Note: We rely on build-args or env-vars for configuration if needed at build time
# But for runtime URL injection in Nginx, we might need a different strategy.
# For now, we will assume the API URL is injected at build time via --dart-define.
ARG API_URL
RUN flutter build web --release --dart-define=BASE_URL=${API_URL}

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy built assets
COPY --from=build /app/build/web /usr/share/nginx/html

# Copy Nginx config (optional, default works for simple static)
# But we need to handle handling the single-page app routing (redirect 404 to index.html)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port (Cloud Run sets PORT env, Nginx needs verification or template subs)
# Usually Nginx listens on 80 by default. Cloud Run maps 8080 -> 80 internally if configured?
# Actually Cloud Run sends requests to $PORT. We need Nginx to listen on $PORT.
# We'll use a template script to substitute PORT.

COPY 10-listen-on-port.sh /docker-entrypoint.d/
RUN chmod +x /docker-entrypoint.d/10-listen-on-port.sh

EXPOSE 8080
