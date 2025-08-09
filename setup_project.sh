#!/bin/bash
# setup_project.sh - Complete Coffee Shop AI Project Setup

set -e

echo "☕ Setting up Coffee Shop AI Project Structure..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create main directories
echo -e "${BLUE}📁 Creating directories...${NC}"
mkdir -p app/routers app/services app/models app/utils
mkdir -p static/css static/js static/icons static/images
mkdir -p data scripts docs ssl logs backups

# Create Python package files
echo -e "${BLUE}🐍 Creating Python package files...${NC}"
touch app/routers/__init__.py

# Create analytics files
echo -e "${BLUE}📊 Creating analytics files...${NC}"
cat > app/services/analytics_service.py << 'EOF'
# app/services/analytics_service.py
# TODO: Copy content from "Analytics Service" artifact
import redis.asyncio as redis
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from app.utils.config import settings

class AnalyticsService:
    """Analytics service for tracking coffee shop metrics"""
    
    def __init__(self):
        self.redis_client = None
        print("📊 Analytics service initialized - TODO: Add full implementation")
    
    async def track_conversation_start(self, session_id: str, context: Dict = None):
        """Track new conversation start"""
        print(f"📊 Tracking conversation start: {session_id}")
    
    async def track_message(self, session_id: str, role: str, message_length: int, 
                          response_time: float = None):
        """Track individual message"""
        print(f"📊 Tracking message: {role} - {message_length} chars")
    
    async def track_session_end(self, session_id: str, duration: float, 
                               messages_count: int, order_completed: bool):
        """Track conversation end"""
        print(f"📊 Tracking session end: {session_id} - {duration:.2f}s")
    
    async def get_dashboard_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get dashboard metrics - mock data for now"""
        return {
            "overview": {
                "total_conversations": 1247,
                "total_orders": 342,
                "conversion_rate": 27.4,
                "customer_satisfaction": 4.2
            }
        }
EOF

cat > app/routers/analytics.py << 'EOF'
# app/routers/analytics.py
# TODO: Copy content from "Analytics API Routes" artifact
from fastapi import APIRouter, Query
from datetime import datetime

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/dashboard")
async def get_dashboard_metrics(days: int = Query(7, ge=1, le=30)):
    """Get dashboard metrics - placeholder"""
    return {
        "success": True,
        "data": {"overview": {"total_conversations": 100}},
        "period": f"Last {days} days"
    }
EOF

# Create production config
echo -e "${BLUE}🔧 Creating production config...${NC}"
cat > production_config.py << 'EOF'
# production_config.py
# TODO: Copy content from "Production Configuration" artifact
import os
from app.utils.config import Settings

class ProductionSettings(Settings):
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    def validate_production_settings(self):
        return {"valid": True, "issues": [], "warnings": []}

production_settings = ProductionSettings()
EOF

# Create main production file
echo -e "${BLUE}🚀 Creating production main...${NC}"
cat > app/main_production.py << 'EOF'
# app/main_production.py
# TODO: Copy content from "Production Main Application" artifact
from fastapi import FastAPI
from app.main import *  # Import everything from development main
from production_config import production_settings

# This is a placeholder - copy the full production main from artifacts
print("🚀 Production main loaded - TODO: Add full implementation")
EOF

# Create frontend files
echo -e "${BLUE}🌐 Creating frontend files...${NC}"
cat > static/analytics.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analytics Dashboard</title>
</head>
<body>
    <h1>📊 Analytics Dashboard</h1>
    <p>TODO: Copy content from "Analytics Dashboard" artifact</p>
    <div id="dashboard-content">
        Loading analytics...
    </div>
</body>
</html>
EOF

cat > static/manifest.json << 'EOF'
{
  "name": "Coffee Shop AI",
  "short_name": "Coffee AI",
  "description": "Intelligent coffee shop assistant",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#FAFAFA",
  "theme_color": "#8B4513",
  "icons": [
    {
      "src": "/static/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/static/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
EOF

cat > static/sw.js << 'EOF'
// Service Worker - TODO: Copy content from "Service Worker" artifact
const CACHE_NAME = 'coffee-shop-v1.0.0';

self.addEventListener('install', (event) => {
    console.log('🔧 Service Worker installing...');
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    console.log('🚀 Service Worker activating...');
    event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
    // Basic fetch handling - TODO: Add full caching strategies
    event.respondWith(fetch(event.request));
});

console.log('🎯 Coffee Shop Service Worker loaded');
EOF

cat > static/js/pwa-manager.js << 'EOF'
// PWA Manager - TODO: Copy content from "PWA Install Manager" artifact
class PWAManager {
    constructor() {
        console.log('📱 PWA Manager initialized');
        this.registerServiceWorker();
    }
    
    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                await navigator.serviceWorker.register('/static/sw.js');
                console.log('✅ Service Worker registered');
            } catch (error) {
                console.error('❌ Service Worker registration failed:', error);
            }
        }
    }
}

// Initialize when DOM loads
document.addEventListener('DOMContentLoaded', () => {
    window.pwaManager = new PWAManager();
});
EOF

# Create deployment files
echo -e "${BLUE}🚀 Creating deployment files...${NC}"

# Heroku files
cat > Procfile << 'EOF'
web: python -m uvicorn app.main_production:app --host 0.0.0.0 --port $PORT --workers 2
EOF

cat > runtime.txt << 'EOF'
python-3.13.0
EOF

cat > .slugignore << 'EOF'
*.pyc
__pycache__/
.git/
.env
.env.*
*.log
.DS_Store
.vscode/
.idea/
tests/
docs/
README.md
*.md
.gitignore
EOF

cat > app.json << 'EOF'
{
  "name": "Coffee Shop AI Agent",
  "description": "Intelligent conversational agent for coffee shop ordering",
  "keywords": ["fastapi", "ai", "chatbot", "coffee", "websocket", "pwa"],
  "stack": "heroku-22",
  "formation": {
    "web": {
      "quantity": 1,
      "size": "basic"
    }
  },
  "addons": [
    {
      "plan": "heroku-redis:mini",
      "as": "REDIS"
    }
  ],
  "buildpacks": [
    {
      "url": "heroku/python"
    }
  ],
  "env": {
    "ENVIRONMENT": {
      "value": "production"
    },
    "GEMINI_API_KEY": {
      "description": "Google Gemini API key",
      "required": true
    },
    "SECRET_KEY": {
      "generator": "secret"
    }
  }
}
EOF

# Railway file
cat > railway.toml << 'EOF'
[build]
builder = "nixpacks"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "python -m uvicorn app.main_production:app --host 0.0.0.0 --port $PORT --workers 2"
healthcheckPath = "/health"

[env]
ENVIRONMENT = "production"
PYTHON_VERSION = "3.13"
EOF

# Docker files
cat > Dockerfile << 'EOF'
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
EOF

cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
EOF

# Create deployment scripts
echo -e "${BLUE}📜 Creating deployment scripts...${NC}"
cat > scripts/deploy_railway.sh << 'EOF'
#!/bin/bash
# Railway deployment script
echo "🚀 Deploying to Railway..."
# TODO: Copy full content from "Deployment Scripts" artifact

if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

echo "🔐 Please login to Railway and set environment variables:"
echo "GEMINI_API_KEY=your_key"
echo "REDIS_URL=your_redis_url"

railway login
railway up
EOF

cat > scripts/deploy_heroku.sh << 'EOF'
#!/bin/bash
# Heroku deployment script
echo "🚀 Deploying to Heroku..."
# TODO: Copy full content from "Deployment Scripts" artifact

APP_NAME=${1:-coffee-shop-ai-$(date +%s)}
heroku create $APP_NAME
heroku addons:create heroku-redis:mini -a $APP_NAME
git push heroku main
EOF

cat > scripts/deploy_docker.sh << 'EOF'
#!/bin/bash
# Docker deployment script
echo "🐳 Deploying with Docker..."
# TODO: Copy full content from "Deployment Scripts" artifact

docker-compose up -d
echo "✅ Docker deployment complete!"
EOF

cat > scripts/health_check.sh << 'EOF'
#!/bin/bash
# Health check script
URL=${1:-http://localhost:8000}
echo "🏥 Checking health of $URL..."

if curl -f "$URL/health" > /dev/null 2>&1; then
    echo "✅ Health check passed!"
else
    echo "❌ Health check failed!"
    exit 1
fi
EOF

# Create documentation
echo -e "${BLUE}📚 Creating documentation...${NC}"
cat > docs/deployment-guide.md << 'EOF'
# 🚀 Coffee Shop AI - Deployment Guide

TODO: Copy content from "Complete Deployment Guide" artifact

## Quick Start

1. Set up environment variables
2. Choose deployment platform
3. Run deployment script

## Platforms

- Railway: `./scripts/deploy_railway.sh`
- Heroku: `./scripts/deploy_heroku.sh`  
- Docker: `./scripts/deploy_docker.sh`
EOF

# Create placeholder files
echo -e "${BLUE}📄 Creating placeholder files...${NC}"
touch logs/.gitkeep
touch backups/.gitkeep

# Create icon placeholders
echo -e "${BLUE}🖼️ Creating icon placeholders...${NC}"
for size in 72 96 128 144 152 192 384 512; do
    touch "static/icons/icon-${size}x${size}.png"
done

# Make scripts executable
chmod +x scripts/*.sh

# Update .gitignore
echo -e "${BLUE}📝 Updating .gitignore...${NC}"
cat >> .gitignore << 'EOF'

# Production files
production_config.py
ssl/
logs/
backups/

# Environment files
.env.production
.env.local

# Deployment
.railway/
EOF

# Create environment template
cat > .env.production.example << 'EOF'
# Production Environment Variables
ENVIRONMENT=production
GEMINI_API_KEY=your_gemini_api_key_here
REDIS_URL=your_redis_url_here
WEATHER_API_KEY=your_weather_api_key_here
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=your-domain.com
ALLOWED_ORIGINS=https://your-domain.com
LOG_LEVEL=INFO
EOF

# Create a simple TODO list
cat > TODO.md << 'EOF'
# 📋 Coffee Shop AI - Implementation TODO

## ✅ Project Structure Created
- [x] Directories and files created
- [x] Placeholder code added
- [x] Deployment configurations ready

## 🔄 Next Steps (Copy Artifact Content)

### High Priority
- [ ] Copy Analytics Service code to `app/services/analytics_service.py`
- [ ] Copy Analytics Routes to `app/routers/analytics.py`
- [ ] Copy Analytics Dashboard HTML to `static/analytics.html`
- [ ] Copy Production Main to `app/main_production.py`
- [ ] Copy Service Worker to `static/sw.js`
- [ ] Copy PWA Manager to `static/js/pwa-manager.js`

### Medium Priority
- [ ] Copy Deployment Scripts to `scripts/` directory
- [ ] Copy Deployment Guide to `docs/deployment-guide.md`
- [ ] Create/generate PWA icons for `static/icons/`
- [ ] Update `requirements.txt` with new dependencies

### Low Priority
- [ ] Customize PWA manifest colors and names
- [ ] Add SSL certificates to `ssl/` directory
- [ ] Set up monitoring and logging
- [ ] Configure backup scripts

## 🚀 Deployment Checklist
- [ ] Choose platform (Railway/Heroku/Docker)
- [ ] Set up API keys (Gemini, Redis, Weather)
- [ ] Run deployment script
- [ ] Test production deployment
- [ ] Configure custom domain (optional)

## 📊 Testing Checklist
- [ ] Analytics dashboard loads
- [ ] PWA can be installed
- [ ] WebSocket connections work
- [ ] Health checks pass
- [ ] Mobile experience works
EOF

echo ""
echo -e "${GREEN}✅ Coffee Shop AI Project Structure Created!${NC}"
echo ""
echo -e "${YELLOW}📋 What was created:${NC}"
echo "   📁 Complete directory structure"
echo "   🐍 Python package files with placeholders"
echo "   🌐 Frontend files with basic content"
echo "   🚀 Deployment configurations for Railway/Heroku/Docker"
echo "   📜 Deployment scripts"
echo "   📚 Documentation templates"
echo ""
echo -e "${BLUE}🔄 Next Steps:${NC}"
echo "   1. Copy artifact content into corresponding files"
echo "   2. Create PWA icons (use online generator)"
echo "   3. Update requirements.txt if needed"
echo "   4. Test locally: python -m uvicorn app.main:app --reload"
echo "   5. Deploy: Choose platform and run deployment script"
echo ""
echo -e "${GREEN}📄 See TODO.md for detailed checklist${NC}"
echo ""
echo -e "${YELLOW}🎯 Key files to update with artifact content:${NC}"
echo "   • app/services/analytics_service.py"
echo "   • app/routers/analytics.py"
echo "   • static/analytics.html"
echo "   • app/main_production.py"
echo "   • static/sw.js"
echo "   • static/js/pwa-manager.js"
echo "   • scripts/*.sh"
echo "   • docs/deployment-guide.md"
echo ""
echo -e "${GREEN}🚀 Ready to build something amazing!${NC}"