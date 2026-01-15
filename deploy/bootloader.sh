#!/bin/bash
set -e

echo "🔮 [Genesis] Bootloader initiated..."

BRAIN_DIR="/app/.brain"
SEED_DIR="/app/.brain_seed"

# Check if the persistent volume is empty
if [ -z "$(ls -A $BRAIN_DIR)" ]; then
    echo "⚠️  [Genesis] Persistent Brain is EMPTY. Initiating Genesis copy..."
    echo "📂 [Genesis] Copying seed from $SEED_DIR to $BRAIN_DIR..."
    cp -r $SEED_DIR/* $BRAIN_DIR/
    echo "✅ [Genesis] Seeding complete."
else
    echo "🧠 [Genesis] Persistent Brain found. Resuming memory..."
fi

# Fix permissions if needed (GCS fuse sometimes has weird ownership)
# echo "🔧 [Genesis] Applying permissions..."
# chmod -R 777 $BRAIN_DIR

echo "🚀 [Genesis] Handing over to Supervisor..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
