#!/bin/bash
# Phase A.5 sync-back — pull cross-machine relay state from OCI VM-1 to laptop.
#
# Per .brain/research/2026-04-28_tier_architecture/09_cloud_substrate_and_router_strategy.md
# §A.5: VM-1 (nucleus-webhook) receives relays at /opt/nucleus/brain/relay/.
# Laptop reads from $LOCAL_BRAIN/relay/. This script pulls the VM's relay
# state to the laptop's brain dir, one-way (VM → laptop), idempotent,
# rsync-skips files already present locally.
#
# Strategy doc soft-locks rsync as the v1 sync mechanism (vs syncthing /
# SSHFS / git). Revisit if conflicts emerge or laptop loses connectivity
# faster than the cron interval.
#
# CRON SUGGESTION (Lokesh-keyboard, NOT auto-installed by this script):
#
#   crontab -e
#   # Pull VM relays every minute, log to ~/.cache/nucleus-sync.log
#   * * * * * /Users/lokeshgarg/ai-mvp-backend/scripts/sync_brain_from_oci.sh >> ~/.cache/nucleus-sync.log 2>&1
#
# Or via launchd / systemd timer if cron isn't preferred. This script is
# safe to run by hand any time; idempotent.
#
# Usage:
#     sync_brain_from_oci.sh                   # uses defaults below
#     NUCLEUS_OCI_HOST=brain.nucleusos.dev sync_brain_from_oci.sh
#     NUCLEUS_OCI_USER=ubuntu NUCLEUS_OCI_BRAIN=/opt/nucleus/brain sync_brain_from_oci.sh

set -eu

# --- Config (override via env) ---
NUCLEUS_OCI_HOST="${NUCLEUS_OCI_HOST:-brain.nucleusos.dev}"
NUCLEUS_OCI_USER="${NUCLEUS_OCI_USER:-ubuntu}"
NUCLEUS_OCI_BRAIN="${NUCLEUS_OCI_BRAIN:-/opt/nucleus/brain}"
LOCAL_BRAIN="${NUCLEUS_BRAIN_PATH:-${HOME}/ai-mvp-backend/.brain}"
SSH_KEY="${NUCLEUS_OCI_SSH_KEY:-${HOME}/.ssh/id_ed25519}"
LOCK_FILE="${TMPDIR:-/tmp}/nucleus-sync-back.lock"

# Subdirs to sync (one-way pull, additive). Add more here as cross-machine
# surfaces grow. We deliberately do NOT sync .brain/ledger or .brain/engrams
# from the VM — those are append-only local accumulation; merging them
# bidirectionally is the can-of-worms §A.5 calls out.
SUBDIRS=(
    "relay"
)

# --- Single-instance guard ---
# Prevents overlapping cron fires when network is slow.
if [ -f "${LOCK_FILE}" ]; then
    pid=$(cat "${LOCK_FILE}" 2>/dev/null || echo "")
    if [ -n "${pid}" ] && kill -0 "${pid}" 2>/dev/null; then
        echo "[sync-back] already running (pid ${pid}); skipping" >&2
        exit 0
    fi
fi
echo "$$" > "${LOCK_FILE}"
trap 'rm -f "${LOCK_FILE}"' EXIT

# --- Sanity ---
if ! command -v rsync >/dev/null 2>&1; then
    echo "[sync-back] rsync not found — install via 'brew install rsync' or system pkg manager" >&2
    exit 2
fi
mkdir -p "${LOCAL_BRAIN}"

# --- Pull each subdir ---
ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "[sync-back] ${ts} pulling ${NUCLEUS_OCI_USER}@${NUCLEUS_OCI_HOST}:${NUCLEUS_OCI_BRAIN}/{...} → ${LOCAL_BRAIN}/"

ssh_opts="-o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 -o ServerAliveInterval=5"
[ -f "${SSH_KEY}" ] && ssh_opts="${ssh_opts} -i ${SSH_KEY}"

for sub in "${SUBDIRS[@]}"; do
    src="${NUCLEUS_OCI_USER}@${NUCLEUS_OCI_HOST}:${NUCLEUS_OCI_BRAIN}/${sub}/"
    dst="${LOCAL_BRAIN}/${sub}/"
    mkdir -p "${dst}"
    # --ignore-existing: idempotent — never overwrite locally-present file
    # --partial: keep partial transfers on disconnect, resumable
    # -t: preserve mtime (important for ordering / observability)
    # -e ssh: explicit transport with our opts
    rsync \
        --ignore-existing \
        --partial \
        -rt \
        -e "ssh ${ssh_opts}" \
        "${src}" "${dst}" \
        2>&1 | sed "s|^|[sync-back ${sub}] |"
done

echo "[sync-back] ${ts} done"
