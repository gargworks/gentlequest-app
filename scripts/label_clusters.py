#!/usr/bin/env python3
"""Phase 3 §3.9 — interactive cluster labeling CLI.

Reads `cluster_proposal.jsonl` (produced by scripts/cluster_topics.py),
presents each cluster + 5 sample chunks, prompts Lokesh for a name.
Persists Lokesh-confirmed labels to `cluster_labels.json` and to
`cluster_centroids.json` (the file thread_topic_resolver consumes).

Resumable: re-running picks up where Lokesh stopped (skips clusters
already labeled in cluster_labels.json).

Usage:
    python3 scripts/label_clusters.py [--proposal PATH] [--auto-accept-proposed]
    python3 scripts/label_clusters.py --reset    # clear prior labels + relabel
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.thread_topic_resolver import write_centroids


DEFAULT_BRAIN = Path(os.environ.get(
    "NUCLEUS_BRAIN_PATH",
    str(ROOT / ".brain"),
))
DEFAULT_TB_DIR = DEFAULT_BRAIN / "tb_personal_ai"

DEFAULT_PROPOSAL_PATH = DEFAULT_TB_DIR / "cluster_proposal.jsonl"
DEFAULT_LABELS_PATH = DEFAULT_TB_DIR / "cluster_labels.json"
DEFAULT_CENTROIDS_PATH = DEFAULT_TB_DIR / "cluster_centroids.json"


# ── Proposal + labels persistence ────────────────────────────────────

def load_proposals(path: Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Read cluster_proposal.jsonl. Returns (meta, [cluster, ...])."""
    if not path.exists():
        return {}, []
    meta: Dict[str, Any] = {}
    clusters: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if "_meta" in row:
                meta = row["_meta"]
            else:
                clusters.append(row)
    return meta, clusters


def load_labels(path: Path) -> Dict[str, Dict[str, Any]]:
    """Restore prior label decisions for resumable workflow."""
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def save_labels(labels: Dict[str, Dict[str, Any]], path: Path) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(labels, f, indent=2, ensure_ascii=False)
        tmp.replace(path)
        return True
    except OSError as e:
        print(f"[label_clusters] save failed: {e}", file=sys.stderr)
        return False


# ── Interactive prompt ───────────────────────────────────────────────

def _format_cluster(cluster: Dict[str, Any]) -> str:
    keywords = ", ".join(cluster.get("keywords", []) or [])
    samples = cluster.get("top_chunks", []) or []
    sample_eids = cluster.get("sample_external_ids", []) or []
    lines = [
        f"  cluster_id: {cluster['cluster_id']}",
        f"  proposed:   {cluster.get('label_proposed', 'unlabeled')}",
        f"  size:       {cluster.get('n_chunks', 0)} chunks",
        f"  keywords:   {keywords}",
        f"  samples:",
    ]
    for i, (sample, eid) in enumerate(zip(samples, sample_eids)):
        truncated = sample[:200].replace("\n", " ")
        lines.append(f"    [{i+1}] ({eid}) {truncated}")
    return "\n".join(lines)


def _prompt_for_label(
    cluster: Dict[str, Any],
    *,
    auto_accept_proposed: bool = False,
    input_fn=input,
) -> Tuple[str, str]:
    """Returns (label, status). status ∈ {"approved", "skipped", "dropped"}."""
    proposed = cluster.get("label_proposed", "unlabeled")

    if auto_accept_proposed:
        return proposed, "approved"

    print(_format_cluster(cluster))
    prompt = (f"\n  label> [Enter=keep '{proposed}'  s=skip  "
              f"d=drop (mark as noise)  or type new label]: ")
    try:
        raw = input_fn(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return proposed, "skipped"

    if not raw or raw == "k":
        return proposed, "approved"
    if raw.lower() == "s":
        return proposed, "skipped"
    if raw.lower() == "d":
        return proposed, "dropped"
    # Treat anything else as a custom label
    return raw, "approved"


# ── Centroids file build ─────────────────────────────────────────────

def build_centroids_from_labels(
    labels: Dict[str, Dict[str, Any]],
    clusters: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """Combine Lokesh's label decisions with the cluster centroid data
    to produce the cluster_centroids.json file thread_topic_resolver
    consumes. Skips clusters labeled "skipped" or "dropped"."""
    cluster_by_id = {str(c["cluster_id"]): c for c in clusters}
    out: Dict[str, Dict[str, Any]] = {}
    for cid, decision in labels.items():
        if decision.get("status") not in ("approved",):
            continue
        c = cluster_by_id.get(cid)
        if not c:
            continue
        label = decision.get("label") or c.get("label_proposed", f"cluster_{cid}")
        out[label] = {
            "embedding": c["centroid"],
            "n_chunks": c.get("n_chunks", 0),
            "label_status": "approved",
            "cluster_id": int(cid),
        }
    return out


# ── Main loop ────────────────────────────────────────────────────────

def label_clusters_interactive(
    proposal_path: Path = DEFAULT_PROPOSAL_PATH,
    labels_path: Path = DEFAULT_LABELS_PATH,
    centroids_path: Path = DEFAULT_CENTROIDS_PATH,
    *,
    auto_accept_proposed: bool = False,
    input_fn=input,
) -> Dict[str, int]:
    """Run the interactive labeling pass. Returns counts dict."""
    meta, clusters = load_proposals(proposal_path)
    if not clusters:
        print(f"[label_clusters] no clusters in {proposal_path}",
              file=sys.stderr)
        return {"total": 0, "approved": 0, "skipped": 0, "dropped": 0,
                "already_labeled": 0}

    print(f"[label_clusters] {len(clusters)} clusters to review "
          f"(algorithm={meta.get('algorithm')}, "
          f"silhouette={meta.get('silhouette')})")

    prior = load_labels(labels_path)
    counts = {"total": len(clusters), "approved": 0, "skipped": 0,
              "dropped": 0, "already_labeled": 0}
    decisions = dict(prior)

    for c in clusters:
        cid = str(c["cluster_id"])
        if cid in prior:
            counts["already_labeled"] += 1
            continue
        print(f"\n--- cluster {cid} ({len(decisions)+1} of {len(clusters)}) ---")
        label, status = _prompt_for_label(
            c, auto_accept_proposed=auto_accept_proposed, input_fn=input_fn,
        )
        decisions[cid] = {"label": label, "status": status}
        counts[status] = counts.get(status, 0) + 1
        # Persist after each decision so an interrupt doesn't lose work
        save_labels(decisions, labels_path)

    # Build centroids file from approved labels
    centroids = build_centroids_from_labels(decisions, clusters)
    write_centroids(centroids, centroids_path)
    print(f"\n[label_clusters] {len(centroids)} approved centroids → "
          f"{centroids_path}")

    return counts


# ── CLI ──────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposal", default=str(DEFAULT_PROPOSAL_PATH),
                        help="cluster_proposal.jsonl path")
    parser.add_argument("--labels", default=str(DEFAULT_LABELS_PATH),
                        help="cluster_labels.json path")
    parser.add_argument("--centroids", default=str(DEFAULT_CENTROIDS_PATH),
                        help="cluster_centroids.json output path")
    parser.add_argument("--auto-accept-proposed", action="store_true",
                        help="non-interactive mode — accept all proposals as-is")
    parser.add_argument("--reset", action="store_true",
                        help="clear prior cluster_labels.json + relabel from scratch")
    args = parser.parse_args(argv)

    if args.reset and Path(args.labels).exists():
        Path(args.labels).unlink()
        print(f"[label_clusters] cleared {args.labels}")

    counts = label_clusters_interactive(
        proposal_path=Path(args.proposal),
        labels_path=Path(args.labels),
        centroids_path=Path(args.centroids),
        auto_accept_proposed=args.auto_accept_proposed,
    )
    print(f"\n[label_clusters] result: {json.dumps(counts)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
