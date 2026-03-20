FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (for psycopg, etc.)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Application Code
COPY . .

# Environment
ENV PORT=5055
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose the port
EXPOSE 5055

# Run the application
# Using custom entrypoint to handle creation of DATABASE_URL from secrets
COPY scripts/cloud_run_entrypoint.sh .
RUN chmod +x cloud_run_entrypoint.sh
CMD ["./cloud_run_entrypoint.sh"]
