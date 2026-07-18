FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Make the start script executable
RUN chmod +x start.sh

# The platform (Railway/Render/…) injects $PORT; documented for local Docker use.
EXPOSE 8000

# Health check (uses $PORT, defaulting to 8000)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD sh -c 'python -c "import os,urllib.request; urllib.request.urlopen(\"http://localhost:%s/health\" % os.environ.get(\"PORT\",\"8000\"))"'

# Run migrations + seed + server
CMD ["bash", "start.sh"]
