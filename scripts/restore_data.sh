#!/bin/bash
# restore_data.sh - Data restore script

set -e

BACKUP_FILE=${1:-}

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "🔄 Restoring from $BACKUP_FILE..."

# Extract backup
TEMP_DIR=$(mktemp -d)
tar -xzf "$BACKUP_FILE" -C $TEMP_DIR

# Find backup directory
BACKUP_DIR=$(find $TEMP_DIR -maxdepth 1 -type d -name "backups_*" | head -1)

if [ -z "$BACKUP_DIR" ]; then
    echo "❌ Invalid backup file format"
    exit 1
fi

# Restore Redis data
if [ -f "$BACKUP_DIR/redis_backup.rdb" ]; then
    echo "📊 Restoring Redis data..."
    redis-cli --pipe < "$BACKUP_DIR/redis_backup.rdb"
fi

# Restore configuration
if [ -d "$BACKUP_DIR/data" ]; then
    echo "⚙️ Restoring configuration..."
    cp -r "$BACKUP_DIR/data"/* data/
fi

# Clean up
rm -rf $TEMP_DIR

echo "✅ Restore completed!"