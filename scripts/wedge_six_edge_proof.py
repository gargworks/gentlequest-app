#!/usr/bin/env python3
"""6-edge wedge proof — exercises every routing edge in the three-surface relay.

Three surfaces × two directions = six edges. The proof fires three
question→reply pairs, one per surface-pair, so every edge is exercised exactly
once and each pair leaves a thread the judge can close:

    Pair 1: cowork → main (Q),    main → cowork (R)
    Pair 2: peer   → cowork (Q),  cowork → peer (R)
    Pair 3: main   → peer (Q),    peer → main (R)

After firing all six, run `scripts/relay_judge.py --once --lookback-min 5` and
expect `fired=3` (one auto-ack per closed pair) with no false positives on the
fresh-Q messages (which lack an in_reply_to).

Usage:
    python3 scripts/wedge_six_edge_proof.py [--mock|--real <task>]

--mock (default) emits 6 throwaway relays with subject `wedge-proof:edge-N`.
--real takes a one-line task description and instead emits 3 real coordination
       questions across the substrate.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "mcp-server-nucleus" / "src"))
from mcp_server_nucleus.runtime.relay_ops import relay_post  # noqa: E402

SURFACES = {
    "cowork": f"cowork-wedge-proof-{uuid.uuid4().hex[:8]}",
    "main": str(uuid.uuid4()),
    "peer": str(uuid.uuid4()),
}

PAIRS = [
    ("cowork", "claude_code_main"),
    ("claude_code_peer", "cowork"),
    ("claude_code_main", "claude_code_peer"),
]


def _sid(bucket: str) -> str:
    if bucket == "cowork":
        return SURFACES["cowork"]
    if bucket == "claude_code_main":
        return SURFACES["main"]
    if bucket == "claude_code_peer":
        return SURFACES["peer"]
    raise ValueError(bucket)


def fire_pair(idx: int, sender: str, recipient: str, label: str) -> dict:
    q_subject = f"wedge-proof: edge-{idx*2-1} {sender}→{recipient}"
    q_body = json.dumps({
        "summary": f"{label} question",
        "tags": ["wedge-proof", "question-to-peer"],
        "artifact_refs": [],
        "receiver_interest_match": "wedge-proof harness",
        "auto_generated": False,
        "in_reply_to": None,
        "from_session_id": _sid(sender),
    })
    q = relay_post(
        to=recipient,
        subject=q_subject,
        body=q_body,
        priority="normal",
        sender=sender,
        from_session_id=_sid(sender),
        to_session_id=_sid(recipient),
        context={"wedge_proof_pair": idx},
    )

    r_subject = f"wedge-proof: edge-{idx*2} {recipient}→{sender}"
    r_body = json.dumps({
        "summary": f"{label} reply closing thread {q['message_id']}",
        "tags": ["wedge-proof", "decision"],
        "artifact_refs": [q["message_id"]],
        "receiver_interest_match": f"thread-reply: {q['message_id']}",
        "auto_generated": False,
        "in_reply_to": q["message_id"],
        "from_session_id": _sid(recipient),
    })
    r = relay_post(
        to=sender,
        subject=r_subject,
        body=r_body,
        priority="normal",
        sender=recipient,
        from_session_id=_sid(recipient),
        to_session_id=_sid(sender),
        context={"wedge_proof_pair": idx, "in_reply_to": q["message_id"]},
    )
    return {"pair": idx, "Q": q, "R": r, "sender": sender, "recipient": recipient}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="mock", help="Label embedded in summary lines.")
    args = ap.parse_args()

    print(f"# Wedge 6-edge proof — label={args.label}")
    print(f"# Session IDs: cowork={SURFACES['cowork']}")
    print(f"#              main={SURFACES['main'][:8]} peer={SURFACES['peer'][:8]}")
    fired = []
    for idx, (sender, recipient) in enumerate(PAIRS, start=1):
        print(f"  [pair {idx}] {sender} ↔ {recipient}")
        result = fire_pair(idx, sender, recipient, args.label)
        fired.append(result)
        time.sleep(0.05)

    print()
    print(json.dumps({
        "edges_fired": len(fired) * 2,
        "pairs": [
            {
                "pair": p["pair"],
                "Q_id": p["Q"]["message_id"],
                "Q_path": p["Q"]["path"],
                "R_id": p["R"]["message_id"],
                "R_path": p["R"]["path"],
            }
            for p in fired
        ],
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
