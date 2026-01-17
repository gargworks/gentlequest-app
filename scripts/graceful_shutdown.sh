#!/bin/bash
# Graceful shutdown for planned maintenance

echo "🛑 GRACEFUL SHUTDOWN"
echo "===================="

read -p "Duration of maintenance (hours): " DURATION
read -p "Reason for maintenance: " REASON

echo ""
echo "Planning shutdown for $DURATION hours"
echo "Reason: $REASON"
echo ""

# 1. Notify users (24 hours advance)
echo "1. Notify users (send 24 hours before)..."
# TODO: Email all active users about planned maintenance

# 2. Set maintenance mode
echo "2. Setting maintenance mode..."
# TODO: Set MAINTENANCE_MODE=true in environment

# 3. Wait for active sessions to complete
echo "3. Waiting for active sessions..."
sleep 300  # 5 minutes grace period

# 4. Backup before shutdown
echo "4. Backing up database..."
./scripts/backup_database.sh

# 5. Document
echo "5. Documenting maintenance..."
echo "$(date): Planned maintenance ($DURATION hours) - $REASON" >> logs/maintenance_log.txt

echo ""
echo "✅ Ready for maintenance"
echo ""
echo "After maintenance:"
echo "  1. Run: make deploy"
echo "  2. Verify: make health"
echo "  3. Notify users: Service restored"
