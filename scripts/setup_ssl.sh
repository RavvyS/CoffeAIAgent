#!/bin/bash
# setup_ssl.sh - SSL certificate setup script

set -e

echo "🔒 Setting up SSL certificates..."

DOMAIN=${1:-localhost}

if [ "$DOMAIN" == "localhost" ]; then
    echo "📝 Creating self-signed certificate for development..."
    mkdir -p ssl
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/key.pem \
        -out ssl/cert.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"
else
    echo "📝 For production, use Let's Encrypt:"
    echo "1. Install certbot: sudo apt-get install certbot"
    echo "2. Get certificate: sudo certbot certonly --standalone -d $DOMAIN"
    echo "3. Copy certificates to ./ssl/ directory"
fi

echo "✅ SSL setup instructions provided!"

---