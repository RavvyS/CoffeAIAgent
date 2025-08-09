#!/bin/bash
# deploy_railway.sh - Railway deployment script

set -e

echo "🚀 Deploying Coffee Shop AI to Railway..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Login to Railway
echo "🔐 Logging in to Railway..."
railway login

# Create project if it doesn't exist
echo "📦 Setting up Railway project..."
if ! railway status &> /dev/null; then
    railway login
    railway init
fi

# Set environment variables
echo "⚙️ Setting environment variables..."
echo "Please set the following environment variables in Railway dashboard:"
echo "GEMINI_API_KEY=your_gemini_api_key"
echo "REDIS_URL=your_redis_cloud_url"
echo "WEATHER_API_KEY=your_openweather_api_key"
echo "SECRET_KEY=$(openssl rand -hex 32)"
echo "ALLOWED_HOSTS=\${{RAILWAY_PUBLIC_DOMAIN}}"
echo "ALLOWED_ORIGINS=https://\${{RAILWAY_PUBLIC_DOMAIN}}"

# Deploy
echo "🚀 Deploying to Railway..."
railway up

echo "✅ Deployment complete!"
echo "📊 View logs: railway logs"
echo "🌐 Open app: railway open"

---