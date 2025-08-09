# 🚀 Coffee Shop AI - Production Deployment Guide

Complete guide to deploy your Coffee Shop AI Agent to production with Railway, Heroku, or Docker.

## 📋 Pre-Deployment Checklist

### ✅ Required API Keys
- [ ] **Gemini API Key** - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- [ ] **Redis Cloud URL** - Get from [Redis Cloud](https://redis.com/try-free/) (free tier)
- [ ] **Weather API Key** - Get from [OpenWeatherMap](https://openweathermap.org/api) (optional, free tier)

### ✅ Code Preparation
- [ ] All features tested locally
- [ ] Environment variables configured
- [ ] Production settings reviewed
- [ ] Dependencies updated in `requirements.txt`

---

## 🛤️ Option 1: Railway Deployment (Recommended)

Railway offers the easiest deployment with great developer experience.

### Step 1: Setup Railway Account
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login
```

### Step 2: Initialize Project
```bash
# In your project directory
railway init

# Or connect to existing project
railway link [project-id]
```

### Step 3: Configure Environment Variables
In Railway dashboard or via CLI:

```bash
# Required variables
railway variables set GEMINI_API_KEY=your_gemini_api_key
railway variables set REDIS_URL=your_redis_cloud_url
railway variables set SECRET_KEY=$(openssl rand -hex 32)

# Optional variables
railway variables set WEATHER_API_KEY=your_weather_api_key
railway variables set LOG_LEVEL=INFO
railway variables set ENVIRONMENT=production

# Auto-configured by Railway
railway variables set ALLOWED_HOSTS=$RAILWAY_PUBLIC_DOMAIN
railway variables set ALLOWED_ORIGINS=https://$RAILWAY_PUBLIC_DOMAIN
```

### Step 4: Deploy
```bash
# Deploy using Railway CLI
railway up

# Or connect to GitHub for auto-deploys
# Go to Railway dashboard > Connect GitHub repo
```

### Step 5: Configure Domain (Optional)
```bash
# Add custom domain in Railway dashboard
# Settings > Domains > Add Domain
```

---

## 🟣 Option 2: Heroku Deployment

Heroku provides a robust platform with many add-ons.

### Step 1: Setup Heroku
```bash
# Install Heroku CLI
# Download from: https://devcenter.heroku.com/articles/heroku-cli

# Login
heroku login
```

### Step 2: Create Application
```bash
# Create app with unique name
heroku create your-coffee-shop-ai

# Add Redis addon
heroku addons:create heroku-redis:mini
```

### Step 3: Configure Environment Variables
```bash
APP_NAME=your-coffee-shop-ai

# Required variables
heroku config:set GEMINI_API_KEY=your_gemini_api_key -a $APP_NAME
heroku config:set SECRET_KEY=$(openssl rand -hex 32) -a $APP_NAME
heroku config:set ENVIRONMENT=production -a $APP_NAME

# Optional variables
heroku config:set WEATHER_API_KEY=your_weather_api_key -a $APP_NAME
heroku config:set LOG_LEVEL=INFO -a $APP_NAME

# Auto-configured
heroku config:set ALLOWED_HOSTS=$APP_NAME.herokuapp.com -a $APP_NAME
heroku config:set ALLOWED_ORIGINS=https://$APP_NAME.herokuapp.com -a $APP_NAME

# Redis URL is automatically set by addon
```

### Step 4: Deploy
```bash
# Deploy via Git
git push heroku main

# Scale dynos
heroku ps:scale web=1 -a $APP_NAME

# Open application
heroku open -a $APP_NAME
```

### Step 5: Monitor
```bash
# View logs
heroku logs --tail -a $APP_NAME

# Check status
heroku ps -a $APP_NAME
```

---

## 🐳 Option 3: Docker Deployment

For full control and self-hosting.

### Step 1: Setup Environment
```bash
# Create .env file
cat > .env << EOF
ENVIRONMENT=production
GEMINI_API_KEY=your_gemini_api_key
WEATHER_API_KEY=your_weather_api_key
SECRET_KEY=$(openssl rand -hex 32)
REDIS_URL=redis://redis:6379/0
ALLOWED_HOSTS=localhost,your-domain.com
ALLOWED_ORIGINS=http://localhost:8000,https://your-domain.com
LOG_LEVEL=INFO
EOF
```

### Step 2: Build and Deploy
```bash
# Build and start services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f web
```

### Step 3: Setup SSL (Production)
```bash
# For Let's Encrypt SSL
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./ssl/key.pem
sudo chown $USER:$USER ./ssl/*.pem
```

---

## 🔧 Environment Variables Reference

### Required Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | `AIzaSy...` |
| `SECRET_KEY` | Session encryption key | `abc123...` |
| `ENVIRONMENT` | Environment name | `production` |

### Optional Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `WEATHER_API_KEY` | OpenWeatherMap API key | None |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `ALLOWED_HOSTS` | Allowed hostnames | `*` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `*` |

### Auto-configured Variables
These are automatically set by the platform:
- `PORT` - Application port
- `DATABASE_URL` - Database connection (if using PostgreSQL)
- `REDIS_URL` - Redis connection (Heroku addon)

---

## 📊 Monitoring and Health Checks

### Health Check Endpoints
- `/health` - Detailed health status
- `/health/live` - Simple liveness check
- `/health/ready` - Readiness check
- `/metrics` - Prometheus metrics

### Example Health Check
```bash
# Check application health
curl https://your-app.com/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "redis": "healthy",
    "ai": "healthy",
    "websocket": "healthy"
  },
  "metrics": {
    "active_connections": 5,
    "uptime": 3600
  }
}
```

### Monitoring Setup
```bash
# Set up monitoring alerts (example with curl)
#!/bin/bash
# monitor.sh
while true; do
    if ! curl -f https://your-app.com/health > /dev/null 2>&1; then
        echo "🚨 Health check failed!" | mail -s "App Down" your-email@domain.com
    fi
    sleep 300  # Check every 5 minutes
done
```

---

## 🔒 Security Checklist

### ✅ Before Going Live
- [ ] Change default `SECRET_KEY`
- [ ] Restrict `ALLOWED_HOSTS` and `ALLOWED_ORIGINS`
- [ ] Enable HTTPS/SSL
- [ ] Set up rate limiting
- [ ] Configure firewall rules
- [ ] Enable error monitoring (Sentry)
- [ ] Set up log aggregation
- [ ] Configure backups

### Security Headers
The application automatically includes:
- CORS protection
- Request ID tracking
- Rate limiting middleware
- Trusted host validation
- Gzip compression

---

## 🚨 Troubleshooting

### Common Issues

#### 1. Redis Connection Failed
```bash
# Check Redis URL format
echo $REDIS_URL
# Should be: redis://user:pass@host:port/db

# Test Redis connection
redis-cli -u $REDIS_URL ping
```

#### 2. AI Service Errors
```bash
# Check API key
echo $GEMINI_API_KEY
# Should start with: AIza...

# Test API access
curl -H "Authorization: Bearer $GEMINI_API_KEY" \
  https://generativelanguage.googleapis.com/v1/models
```

#### 3. WebSocket Connection Issues
```bash
# Check WebSocket URL in browser console
# Should be: wss://your-app.com/ws/session_id

# Test WebSocket endpoint
curl -i -N -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Key: test" \
  -H "Sec-WebSocket-Version: 13" \
  https://your-app.com/ws/test
```

#### 4. High Memory Usage
```bash
# Check memory usage
docker stats  # For Docker
heroku ps -a your-app  # For Heroku

# Optimize if needed:
# - Reduce MAX_CONVERSATION_HISTORY
# - Lower SESSION_TIMEOUT_HOURS
# - Scale down worker processes
```

### Log Analysis
```bash
# Railway logs
railway logs

# Heroku logs
heroku logs --tail -a your-app

# Docker logs
docker-compose logs -f web

# Look for these patterns:
# ✅ "Service Worker registered"
# ✅ "Redis connection established"
# ✅ "AI service initialized"
# ❌ "Connection failed"
# ❌ "Rate limit exceeded"
```

---

## 📈 Performance Optimization

### Scaling Configuration

#### Railway Scaling
```bash
# In Railway dashboard:
# Settings > Resources > Scale up
# Recommended: 512MB RAM, 0.5 vCPU
```

#### Heroku Scaling
```bash
# Scale web dynos
heroku ps:scale web=2 -a your-app

# Upgrade dyno type
heroku ps:resize web=standard-1x -a your-app
```

#### Docker Scaling
```yaml
# docker-compose.prod.yml
services:
  web:
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
```

### Performance Monitoring
```bash
# Add performance monitoring
# 1. Application Performance Monitoring (APM)
pip install sentry-sdk[fastapi]

# 2. Custom metrics endpoint
curl https://your-app.com/metrics

# 3. Load testing
pip install locust
# Create load test scenarios
```

---

## 💾 Backup and Recovery

### Automated Backups
```bash
# Create backup script
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/$DATE"

# Backup Redis data
redis-cli --rdb $BACKUP_DIR/redis_backup.rdb

# Backup configuration
cp -r data/ $BACKUP_DIR/
tar -czf "backup_$DATE.tar.gz" $BACKUP_DIR/

# Upload to cloud storage (example)
aws s3 cp "backup_$DATE.tar.gz" s3://your-backup-bucket/
```

### Scheduled Backups
```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /path/to/backup.sh

# Weekly full backup
0 3 * * 0 /path/to/full_backup.sh
```

---

## 🎯 Production Checklist

### Pre-Launch
- [ ] All environment variables set
- [ ] Health checks passing
- [ ] SSL certificate configured
- [ ] Domain configured
- [ ] Monitoring set up
- [ ] Backups configured
- [ ] Error tracking enabled
- [ ] Performance tested
- [ ] Security reviewed

### Post-Launch
- [ ] Monitor health dashboard
- [ ] Check error rates
- [ ] Verify analytics working
- [ ] Test PWA installation
- [ ] Monitor resource usage
- [ ] Check backup integrity
- [ ] Review security logs

### Ongoing Maintenance
- [ ] Weekly health check review
- [ ] Monthly security updates
- [ ] Quarterly performance review
- [ ] Annual disaster recovery test

---

## 📞 Support and Resources

### Quick Deploy Commands
```bash
# Railway one-liner
railway login && railway init && railway up

# Heroku one-liner
heroku create your-app && git push heroku main

# Docker one-liner
docker-compose up -d
```

### Useful Resources
- [Railway Documentation](https://docs.railway.app/)
- [Heroku Dev Center](https://devcenter.heroku.com/)
- [Docker Documentation](https://docs.docker.com/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Redis Cloud](https://redis.com/cloud/)

### Getting Help
- Check application logs first
- Review health check endpoints
- Test individual components
- Compare with working local setup
- Check API key permissions
- Verify network connectivity

---

## 🏆 Success Metrics

Your deployment is successful when:
- ✅ Health checks return 200 OK
- ✅ WebSocket connections work
- ✅ AI responses are generated
- ✅ Analytics dashboard loads
- ✅ PWA can be installed
- ✅ All error rates < 1%
- ✅ Response times < 2 seconds
- ✅ Uptime > 99.9%

**🎉 Congratulations! Your Coffee Shop AI Agent is now live in production!**

---

*This deployment guide ensures your application is production-ready with proper monitoring, security, and scalability. Update the guide as you add new features or deployment targets.*