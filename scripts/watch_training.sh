#!/usr/bin/env bash
# Watch MLX training and auto-deploy when done.
#
# Usage:
#   bash scripts/watch_training.sh              # watch + deploy
#   bash scripts/watch_training.sh --no-deploy  # watch only
#
set -euo pipefail

SSD=""
for name in "Samsung SSD 990 PRO 2TB Media" "Samsung T7"; do
    if [ -d "/Volumes/$name" ]; then SSD="/Volumes/$name"; break; fi
done

if [ -z "$SSD" ]; then echo "No SSD found."; exit 1; fi

ADAPTER_DIR="$SSD/training-output/mlx-adapter-v2"
LOG_FILE="$SSD/training-output/train_v2.log"
DEPLOY="${1:-deploy}"

echo "=== Training Monitor ==="
echo "Adapter: $ADAPTER_DIR"
echo "Log:     $LOG_FILE"
echo ""

LAST_CHECKPOINT=""
while true; do
    # Check if process is still running
    if ! pgrep -f "mlx_lm.lora.*mlx-adapter-v2" > /dev/null 2>&1; then
        echo ""
        echo "[$(date +%H:%M)] Training process finished."

        # Check if we have a final adapter
        if [ -f "$ADAPTER_DIR/adapters.safetensors" ]; then
            echo "Final adapter found: $(du -h "$ADAPTER_DIR/adapters.safetensors" | cut -f1)"

            if [ "$DEPLOY" != "--no-deploy" ]; then
                echo ""
                echo "=== Auto-deploying ==="
                bash .brain/training/deploy_model.sh "$ADAPTER_DIR"
            else
                echo "Deploy skipped (--no-deploy). Run manually:"
                echo "  bash .brain/training/deploy_model.sh $ADAPTER_DIR"
            fi
        else
            echo "WARNING: No final adapter found. Training may have failed."
            echo "Check log: $LOG_FILE"
        fi
        break
    fi

    # Show latest checkpoint
    LATEST=$(ls -t "$ADAPTER_DIR"/*.safetensors 2>/dev/null | head -1)
    if [ -n "$LATEST" ] && [ "$LATEST" != "$LAST_CHECKPOINT" ]; then
        LAST_CHECKPOINT="$LATEST"
        CKPT_NAME=$(basename "$LATEST")
        echo "[$(date +%H:%M)] Checkpoint: $CKPT_NAME ($(du -h "$LATEST" | cut -f1))"
    fi

    # Show latest loss from log (grep for Iter lines)
    LAST_ITER=$(grep -o "Iter [0-9]*.*loss [0-9.]*" "$LOG_FILE" 2>/dev/null | tail -1)
    if [ -n "$LAST_ITER" ]; then
        echo -ne "\r  $LAST_ITER  "
    fi

    sleep 30
done
