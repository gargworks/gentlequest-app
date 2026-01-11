
FROM python:3.11-slim

WORKDIR /app

# Install Dependencies
RUN pip install --no-cache-dir firebase-admin google-auth

# Copy Codebase
# We copy specific folders to avoid sending the whole repo (like node_modules)
COPY tools /app/tools
COPY docs /app/docs
COPY .brain /app/.brain

# Create empty log if it doesn't exist (to avoid errors)
RUN touch /app/docs/marketing/marketing_log.md

# Path Helper for server.py which expects to be deep in tools
# server.py finds root via os.path.dirname(os.path.dirname(BASE_DIR))
# If server.py is at /app/tools/marketing-dashboard/server.py
# BASE_DIR = /app/tools/marketing-dashboard
# PROJECT_ROOT = /app
# This matches the container structure.

ENV PORT 8080
EXPOSE 8080

CMD ["python", "tools/marketing-dashboard/server.py"]