#!/bin/bash
# deploy_docker.sh - Docker deployment script

set -e

echo "🐳 Deploying Coffee Shop AI with Docker..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
ENVIRONMENT=production
GEMINI_API_KEY=your_gemini_api_key_here
WEATHER_API_KEY=your_weather_api_key_here
SECRET_KEY=$(openssl rand -hex 32)
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
ALLOWED_ORIGINS=http://localhost:8000,https://your-domain.com
LOG_LEVEL=INFO
EOF
    echo "Please edit .env file with your API keys"
    echo "Then run: ./deploy_docker.sh"
    exit 0
fi

# Build and deploy
echo "🏗️ Building Docker images..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

echo "🚀 Starting services..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

echo "✅ Deployment complete!"
echo "🌐 App running at: http://localhost"
echo "📊 View logs: docker-compose logs -f"
echo "🛑 Stop: docker-compose down"

---