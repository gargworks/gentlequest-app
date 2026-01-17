#!/bin/bash
# Make all scripts executable
# Run once: ./scripts/update_makefile_permissions.sh

chmod +x scripts/*.sh
chmod +x cron/*.sh
chmod +x scripts/*.py

echo "✅ All scripts are now executable"
