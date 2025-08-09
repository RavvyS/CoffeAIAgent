#!/bin/bash
# health_check.sh - Health monitoring script

set -e

URL=${1:-http://localhost:8000}
RETRIES=${2:-5}
DELAY=${3:-10}

echo "🏥 Health checking $URL..."

for i in $(seq 1 $RETRIES); do
    echo "Attempt $i/$RETRIES..."
    
    if curl -f "$URL/health" > /dev/null 2>&1; then
        echo "✅ Health check passed!"
        
        # Get detailed health info
        echo "📊 Health details:"
        curl -s "$URL/health" | python -m json.tool
        exit 0
    else
        echo "❌ Health check failed"
        if [ $i -lt $RETRIES ]; then
            echo "⏳ Waiting $DELAY seconds before retry..."
            sleep $DELAY
        fi
    fi
done

echo "💀 All health checks failed!"
exit 1

---
