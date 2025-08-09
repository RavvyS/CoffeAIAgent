#!/bin/bash
# backup_data.sh - Data backup script

set -e

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
REDIS_URL=${REDIS_URL:-redis://localhost:6379}

echo "💾 Creating backup in $BACKUP_DIR..."
mkdir -p $BACKUP_DIR

# Backup Redis data
echo "📊 Backing up Redis data..."
redis-cli --rdb $BACKUP_DIR/redis_backup.rdb

# Backup configuration
echo "⚙️ Backing up configuration..."
cp -r data/ $BACKUP_DIR/
cp .env $BACKUP_DIR/ 2>/dev/null || echo "No .env file found"

# Create archive
echo "📦 Creating archive..."
tar -czf "$BACKUP_DIR.tar.gz" $BACKUP_DIR/
rm -rf $BACKUP_DIR/

echo "✅ Backup created: $BACKUP_DIR.tar.gz"

---