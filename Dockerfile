# Use a lightweight Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy the server directory
COPY mcp-server-nucleus/ /app/mcp-server-nucleus/

# Install dependencies
WORKDIR /app/mcp-server-nucleus
RUN pip install --no-cache-dir .

# Expose no ports (stdio based)
# Glama environment uses stdio for inspection

# Labels
LABEL version="1.0.7"
LABEL maintainer="Nucleus Team <hello@nucleusos.dev>"

# Set the command to run the server
ENTRYPOINT ["nucleus-mcp"]