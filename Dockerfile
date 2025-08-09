FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    PORT=8000

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN adduser --disabled-password --gecos '' appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R appuser:appuser /app

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

EXPOSE $PORT

CMD ["python", "-m", "uvicorn", "app.main_production:app", "--host", "0.0.0.0", "--port", "8000"]
a# Dockerfile
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    PORT=8000

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/static /app/data \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE $PORT

# Command to run the application
CMD ["python", "-m", "uvicorn", "app.main_production:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - REDIS_URL=redis://redis:6379/0
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - WEATHER_API_KEY=${WEATHER_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
      - ALLOWED_HOSTS=localhost,127.0.0.1
      - ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
    depends_on:
      redis:
        condition: service_healthy
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
    networks:
      - coffee-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    restart: unless-stopped
    networks:
      - coffee-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./static:/usr/share/nginx/html/static:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - web
    restart: unless-stopped
    networks:
      - coffee-network

volumes:
  redis_data:

networks:
  coffee-network:
    driver: bridge

# docker-compose.prod.yml - Production overrides
version: '3.8'

services:
  web:
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
      - DEBUG=false
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
    restart: always
    
  redis:
    deploy:
      resources:
        limits:
          memory: 256M
        reservations:
          memory: 128M
    restart: always
    
  nginx:
    deploy:
      resources:
        limits:
          memory: 128M
        reservations:
          memory: 64M
    restart: always