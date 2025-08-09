#!/bin/bash
# deploy_heroku.sh - Heroku deployment script

set -e

echo "🚀 Deploying Coffee Shop AI to Heroku..."

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI not found. Please install it first:"
    echo "https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Login to Heroku
echo "🔐 Logging in to Heroku..."
heroku login

# Create app
APP_NAME=${1:-coffee-shop-ai-$(date +%s)}
echo "📦 Creating Heroku app: $APP_NAME"
heroku create $APP_NAME

# Add Redis addon
echo "📊 Adding Redis addon..."
heroku addons:create heroku-redis:mini -a $APP_NAME

# Set environment variables
echo "⚙️ Setting environment variables..."
heroku config:set ENVIRONMENT=production -a $APP_NAME
heroku config:set LOG_LEVEL=INFO -a $APP_NAME
heroku config:set SECRET_KEY=$(openssl rand -hex 32) -a $APP_NAME
heroku config:set ALLOWED_HOSTS=$APP_NAME.herokuapp.com -a $APP_NAME
heroku config:set ALLOWED_ORIGINS=https://$APP_NAME.herokuapp.com -a $APP_NAME

echo "Please set your API keys:"
echo "heroku config:set GEMINI_API_KEY=your_key -a $APP_NAME"
echo "heroku config:set WEATHER_API_KEY=your_key -a $APP_NAME"

# Deploy
echo "🚀 Deploying to Heroku..."
git push heroku main

# Scale dynos
echo "⚖️ Scaling web dyno..."
heroku ps:scale web=1 -a $APP_NAME

# Open app
echo "✅ Deployment complete!"
heroku open -a $APP_NAME

---