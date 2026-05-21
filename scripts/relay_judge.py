#!/usr/bin/env python3
"""Relay judge — fires auto_generated=true ack receipts on closed relay threads.

Phase E enabler. Watches the 3 live relay buckets (cowork, claude_code_main,
claude_code_peer) and auto-acks human-authored replies that close question
threads. Combined with Step 4.5 on /to-cc + /to-cowork and Step 5.5 on
/check-inbox (PR #76), multi-hop autonomous flows terminate deterministically.

Heuristic v1 (no LLM):
    M closes thread T iff all of:
        - M.body.auto_generated == false (human-authored)
        - M.body.in_reply_to == T.id (or context.in_reply_to)
        - T exists in .brain/relay/{M.from}/ (T was originally sent TO M's sender)
        - T.from == M.to (M's sender is replying to M.to's question)
        - No prior auto-ack from M.to exists for M.id

When the heuristic matches, the judge fires:
    relay_post(
        to=M.from,
        subject=f"ack: {M.subject[:60]}",
        body=<json>{summary:"", tags:["ack"], auto_generated:true,
                    in_reply_to:M.id, from_session_id:T.from_session_id}</json>,
        sender=M.to,
        from_session_id=T.from_session_id,
        to_session_id=M.from_session_id,
        context={"in_reply_to": M.id},
    )

Step 4.5 is enforced implicitly: the judge never acks a message whose own
body.auto_generated is true, so it cannot generate ack-of-ack traffic.

Usage:
    python3 scripts/relay_judge.py [--dry-run] [--lookback-min 10]
                                   [--poll-secs 5] [--once]
                                   [--brain-path PATH]

Env:
    NUCLEUS_BRAIN_PATH — overrides --brain-path (symmetric with watchdog).
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# Import relay_post + brain-path resolver so we don't fork the relay schema/env contract.
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "mcp-server-nucleus" / "src"))
from mcp_server_nucleus.runtime.common import get_brain_path  # noqa: E402
from mcp_server_nucleus.runtime.relay_ops import relay_post  # noqa: E402

LIVE_BUCKETS = ("cowork", "claude_code_main", "claude_code_peer", "claude_code")

# Mirror of brain_telegram.KNOWN_NOTIFY_TRIGGERS. Duplicated here so the judge
# stays process-decoupled from brain_telegram (no flask/requests import).
# When adding a trigger to brain_telegram.KNOWN_NOTIFY_TRIGGERS, add it here too.
_NOTIFY_INFO_TRIGGERS = ("convergence-call", "founder-scope-stuck")

logger = logging.getLogger("relay_judge")


def resolve_brain_path(cli_value: Optional[str]) -> Path:
    """Resolve brain path with the same precedence as Nucleus runtime.

    Order: --brain-path arg → NUCLEUS_BRAIN_PATH env → cwd-walk fallback
    (via common.get_brain_path). Critical: the judge MUST use the same
    resolver as relay_post or the scan-bucket and ack-write paths will
    diverge (e.g. scan tempdir but write to real bucket — see 2026-04-18 leak).
    """
    if cli_value:
        os.environ["NUCLEUS_BRAIN_PATH"] = cli_value
        return Path(cli_value)
    return get_brain_path()


def _parse_body(raw: Any) -> Optional[Dict[str, Any]]:
    """Relay body is a JSON string per /to-cc + /to-cowork skill contract."""
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _extract_in_reply_to(msg: Dict[str, Any]) -> Optional[str]:
    """Pull in_reply_to from body JSON (v2.3) or context (v2.2 envelope)."""
    body = _parse_body(msg.get("body"))
    if body and body.get("in_reply_to"):
        return str(body["in_reply_to"])
    ctx = msg.get("context") or {}
    if ctx.get("in_reply_to"):
        return str(ctx["in_reply_to"])
    return None


def _find_relay_by_id(bucket_dir: Path, relay_id: str) -> Optional[Dict[str, Any]]:
    """Load the relay file matching relay_id from bucket_dir, or None."""
    if not bucket_dir.is_dir():
        return None
    for p in bucket_dir.glob(f"*{relay_id}.json"):
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
    return None


def _existing_auto_ack(bucket_dir: Path, in_reply_to: str) -> bool:
    """True iff bucket_dir already has an auto_generated=true relay acking in_reply_to."""
    if not bucket_dir.is_dir():
        return False
    for p in bucket_dir.glob("*.json"):
        try:
            msg = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        body = _parse_body(msg.get("body"))
        if not body:
            continue
        if body.get("auto_generated") is not True:
            continue
        if str(body.get("in_reply_to") or "") == in_reply_to:
            return True
    return False


def _should_ack(msg: Dict[str, Any], relay_root: Path) -> Optional[Dict[str, Any]]:
    """Return the question relay T if msg M should be auto-acked, else None.

    Judge heuristic v1. Returns T so caller can extract T.from_session_id.
    """
    body = _parse_body(msg.get("body"))
    if not body:
        return None
    if body.get("auto_generated") is True:
        return None  # never ack an auto-ack — implicit Step 4.5 enforcement
    in_reply_to = _extract_in_reply_to(msg)
    if not in_reply_to:
        return None  # fresh thread, nothing to close
    m_from = msg.get("from")
    m_to = msg.get("to")
    if not m_from or not m_to:
        return None

    # T lives in the sender's inbox bucket (it was originally sent TO M.from).
    t_bucket = relay_root / str(m_from)
    t = _find_relay_by_id(t_bucket, in_reply_to)
    if not t:
        return None
    if t.get("from") != m_to:
        return None  # M isn't replying to M.to's question — skip

    # Dedupe: has m_to already fired an auto-ack for M?
    msg_id = msg.get("id")
    if not msg_id:
        return None
    ack_bucket = relay_root / str(m_from)  # ack goes back to m_from
    if _existing_auto_ack(ack_bucket, msg_id):
        return None

    return t


def _should_notify_info(msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Decide whether to fire `notify --info` for this message (v1 whitelist).

    Matches when tags contain ANY entry in _NOTIFY_INFO_TRIGGERS AND
    to == 'claude_code_main'. brain_telegram.cmd_notify_info gates again on
    opt-in + already-fired state, so this returns metadata for every match
    and lets the downstream gate own the actual fire/skip decision.
    """
    if msg.get("to") != "claude_code_main":
        return None
    body = _parse_body(msg.get("body"))
    if not body:
        return None
    tags = body.get("tags")
    if not isinstance(tags, list):
        return None
    matched = next((t for t in tags if t in _NOTIFY_INFO_TRIGGERS), None)
    if matched is None:
        return None
    return {
        "trigger": matched,
        "relay_id": msg.get("id"),
        "subject": msg.get("subject") or "",
        "from": msg.get("from") or "",
    }


def _invoke_notify_info(brain: Path, trigger: str, relay_id: str, text: str) -> int:
    """Subprocess shell-out to brain_telegram.py notify --info.

    Decoupled-by-process: judge stays light (no flask/requests import) and
    inherits all opt-in + dedup gating from cmd_notify_info.
    """
    import subprocess
    repo_root = Path(__file__).resolve().parent.parent
    cmd = [
        sys.executable,
        str(repo_root / "brain_telegram.py"),
        "notify", "--info",
        "--text", text,
        "--trigger", trigger,
        "--relay-id", relay_id,
    ]
    env = os.environ.copy()
    env["NUCLEUS_BRAIN_PATH"] = str(brain)
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            logger.warning("notify --info exited %d: %s", result.returncode, result.stderr[:200])
        return result.returncode
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        logger.warning("notify --info subprocess failed: %s", exc)
        return 1


def _within_lookback(msg: Dict[str, Any], lookback_sec: float, now: float) -> bool:
    """True iff msg.created_at is within the lookback window from now."""
    created = msg.get("created_at")
    if not created:
        return True  # no created_at → process it (safer)
    try:
        ts = datetime.fromisoformat(str(created).replace("Z", "+00:00")).timestamp()
    except (ValueError, AttributeError):
        return True
    return (now - ts) <= lookback_sec


def scan_and_ack(
    relay_root: Path,
    lookback_sec: float,
    dry_run: bool,
) -> Dict[str, Any]:
    """One pass: scan all buckets, identify ack-worthy messages, fire acks.

    Also fires `notify --info` for whitelisted phone-trigger relays
    (convergence-call → claude_code_main). The notify pass is independent
    of the ack pass; one message can trigger both.

    Returns stats dict with counts of scanned / eligible / fired / skipped.
    """
    now = time.time()
    scanned = 0
    eligible = 0
    fired = 0
    notify_eligible = 0
    notify_fired = 0
    errors = 0
    actions: list = []
    brain = relay_root.parent

    for bucket_name in LIVE_BUCKETS:
        bucket_dir = relay_root / bucket_name
        if not bucket_dir.is_dir():
            continue
        for p in bucket_dir.glob("*.json"):
            if p.name == "pending.json":
                continue
            scanned += 1
            try:
                msg = json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                errors += 1
                continue
            if not _within_lookback(msg, lookback_sec, now):
                continue

            n = _should_notify_info(msg)
            if n:
                notify_eligible += 1
                if dry_run:
                    actions.append({"kind": "notify_info", **n, "fired": False, "reason": "dry-run"})
                    logger.info("DRY-RUN would notify --info trigger=%s relay=%s",
                                n["trigger"], n["relay_id"])
                else:
                    text = f"[{n['from']}] {n['subject']}"[:600]
                    rc = _invoke_notify_info(brain, n["trigger"], n["relay_id"], text)
                    if rc == 0:
                        notify_fired += 1
                    actions.append({"kind": "notify_info", **n, "fired": rc == 0, "rc": rc})

            t = _should_ack(msg, relay_root)
            if not t:
                continue
            eligible += 1

            m_id = msg.get("id")
            m_from = msg.get("from")
            m_to = msg.get("to")
            m_subject = msg.get("subject") or ""
            m_from_session = msg.get("from_session_id")
            t_from_session = t.get("from_session_id")

            action = {
                "msg_id": m_id,
                "msg_subject": m_subject[:60],
                "from": m_from,
                "to": m_to,
                "ack_sender": m_to,
                "ack_to": m_from,
                "from_session_id": t_from_session,
                "to_session_id": m_from_session,
            }

            if dry_run:
                actions.append({**action, "fired": False, "reason": "dry-run"})
                logger.info("DRY-RUN would ack %s (%s → %s)", m_id, m_to, m_from)
                continue

            ack_body = json.dumps({
                "summary": "",
                "tags": ["ack"],
                "artifact_refs": [],
                "auto_generated": True,
                "in_reply_to": m_id,
                "from_session_id": t_from_session,
                "receiver_interest_match": f"thread-reply: {m_id}",
            })
            ack_subject = f"ack: {m_subject[:60]}" if m_subject else "ack"

            try:
                result = relay_post(
                    to=str(m_from),
                    subject=ack_subject,
                    body=ack_body,
                    priority="normal",
                    context={"in_reply_to": m_id},
                    sender=str(m_to),
                    from_session_id=t_from_session,
                    to_session_id=m_from_session,
                )
                fired += 1
                actions.append({**action, "fired": True, "ack_id": result.get("message_id")})
                logger.info("acked %s → relay %s (sender=%s to=%s)",
                            m_id, result.get("message_id"), m_to, m_from)
            except Exception as exc:  # noqa: BLE001 — judge must stay up
                errors += 1
                actions.append({**action, "fired": False, "reason": f"error: {exc}"})
                logger.exception("ack failed for %s: %s", m_id, exc)

    return {
        "timestamp": int(now),
        "scanned": scanned,
        "eligible": eligible,
        "fired": fired,
        "notify_eligible": notify_eligible,
        "notify_fired": notify_fired,
        "errors": errors,
        "actions": actions,
        "dry_run": dry_run,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Identify ack-worthy messages but do NOT write.")
    ap.add_argument("--lookback-min", type=int, default=10,
                    help="Only process messages created in the last N minutes.")
    ap.add_argument("--poll-secs", type=float, default=5.0,
                    help="Seconds between scans when running as daemon.")
    ap.add_argument("--once", action="store_true",
                    help="Run one scan and exit (no daemon loop).")
    ap.add_argument("--brain-path", default=None)
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    brain = resolve_brain_path(args.brain_path)
    relay_root = brain / "relay"
    lookback_sec = args.lookback_min * 60

    logger.info("relay_judge start: brain=%s lookback=%dm poll=%.1fs dry_run=%s once=%s",
                brain, args.lookback_min, args.poll_secs, args.dry_run, args.once)

    if args.once:
        report = scan_and_ack(relay_root, lookback_sec, args.dry_run)
        print(json.dumps(report, indent=2, default=str))
        return 0

    try:
        while True:
            report = scan_and_ack(relay_root, lookback_sec, args.dry_run)
            if (report["fired"] or report["eligible"]
                    or report["notify_fired"] or report["notify_eligible"]
                    or args.verbose):
                logger.info("cycle: scanned=%d ack_elig=%d ack_fired=%d notify_elig=%d notify_fired=%d errors=%d",
                            report["scanned"], report["eligible"], report["fired"],
                            report["notify_eligible"], report["notify_fired"],
                            report["errors"])
            time.sleep(args.poll_secs)
    except KeyboardInterrupt:
        logger.info("relay_judge stop: interrupted")
        return 0


if __name__ == "__main__":
    sys.exit(main())
