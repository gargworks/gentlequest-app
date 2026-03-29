#!/usr/bin/env python3
"""
RAFT Training Data Export Pipeline
===================================
Converts driver shadow_log.jsonl into fine-tuning datasets (SFT + DPO).
With --combined, merges all training sources (loop_turns, preference_pairs,
shadow logs) into unified datasets.

Usage:
    python3 scripts/export_raft_training.py              # export SFT + DPO
    python3 scripts/export_raft_training.py --combined   # merge all sources
    python3 scripts/export_raft_training.py --stats      # show stats only
    python3 scripts/export_raft_training.py --out DIR    # custom output dir
"""

import json
import argparse
import hashlib
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SHADOW_LOG = PROJECT_ROOT / ".brain" / "driver" / "shadow_log.jsonl"
DEFAULT_OUT = PROJECT_ROOT / ".brain" / "training"

# All training data sources
SOURCES = {
    "loop_turns": PROJECT_ROOT / ".brain" / "training" / "loop_turns.jsonl",
    "preference_pairs": PROJECT_ROOT / ".brain" / "training" / "preference_pairs.jsonl",
    "driver_shadow": PROJECT_ROOT / ".brain" / "driver" / "shadow_log.jsonl",
    "training_shadow": PROJECT_ROOT / ".brain" / "training" / "shadow_log.jsonl",
    "human_verdicts": PROJECT_ROOT / ".brain" / "driver" / "human_verdicts.jsonl",
}


def load_shadow_log(path: Path) -> list:
    """Load all entries from shadow_log.jsonl."""
    if not path.exists():
        return []
    entries = []
    for lineno, line in enumerate(path.read_text().strip().split("\n"), 1):
        if line.strip():
            try:
                entry = json.loads(line)
                entry["_source_file"] = str(path)
                entry["_source_line"] = lineno
                entries.append(entry)
            except json.JSONDecodeError:
                pass
    return entries


def _format_chunk(c) -> str:
    """Format a chunk regardless of whether it's a dict or string."""
    if isinstance(c, dict):
        source = c.get("source", "")
        content = c.get("content", "")
        return f"[{source}] {content}" if source else content
    return str(c) if c else ""


def compute_quality_score(entry: dict) -> float:
    """Score a shadow-log entry from 0.0-1.0 based on heuristics."""
    score = 0.0
    if len(entry.get("query", "")) > 20:
        score += 0.2
    if len(entry.get("response", "")) > 100:
        score += 0.2
    oracle = entry.get("oracle_chunks", [])
    if isinstance(oracle, list) and oracle and all(isinstance(c, dict) for c in oracle):
        score += 0.2
    if entry.get("outcome") == "completed":
        score += 0.2
    resp_lower = entry.get("response", "").lower()
    if "error" not in resp_lower and "failed" not in resp_lower:
        score += 0.2
    # RAFT bonus: distractors present means harder training signal
    distractors = entry.get("distractor_chunks", [])
    if isinstance(distractors, list) and distractors:
        score += 0.1
    # Frontier 1 (GROUND): execution verification signal
    meta = entry.get("metadata", entry)
    if meta.get("execution_verified") is True:
        score += 0.2  # machine-verified truth
    elif meta.get("execution_verified") is False:
        score -= 0.3  # machine-verified failure
    # Frontier 2 (ALIGN): human review = platinum
    if meta.get("source") == "human_review" or meta.get("quality") == "platinum":
        score = 1.0  # max — human truth overrides heuristics
    return round(min(max(score, 0.0), 1.0), 2)


def stamp_provenance(example: dict, source_entry: dict, quality: float) -> dict:
    """Attach provenance metadata to an exported example for traceability."""
    content = json.dumps(example.get("messages", example), sort_keys=True)
    example["provenance"] = {
        "source_file": source_entry.get("_source_file", ""),
        "line_number": source_entry.get("_source_line", 0),
        "processing_timestamp": datetime.now(timezone.utc).isoformat(),
        "quality_score": quality,
        "hash": hashlib.sha256(content.encode()).hexdigest(),
    }
    return example


def build_sft_examples(entries: list, min_quality: float = 0.4) -> list:
    """Convert completed entries into SFT chat-format examples.

    Format: {messages: [{role: system, content: context},
                        {role: user, content: instruction},
                        {role: assistant, content: response}]}
    """
    examples = []
    for e in entries:
        if e.get("outcome") != "completed":
            continue
        if not e.get("query") or not e.get("response"):
            continue

        quality = compute_quality_score(e)
        if quality < min_quality:
            continue

        # Build system context with oracle + distractor chunks (RAFT format)
        oracle = e.get("oracle_chunks", [])
        distractors = e.get("distractor_chunks", [])
        system_ctx = "You are an expert software engineer working on the Nucleus project."
        if oracle:
            oracle_formatted = [_format_chunk(c) for c in oracle if c]
            distractor_formatted = [_format_chunk(c) for c in distractors if c]

            if distractor_formatted:
                # RAFT P=0.8: 20% of examples have distractor-only context
                import random
                RAFT_ORACLE_P = 0.8
                if random.random() >= RAFT_ORACLE_P:
                    oracle_formatted = []
                all_chunks = oracle_formatted + distractor_formatted
                random.shuffle(all_chunks)
                chunks_text = "\n\n".join(
                    f"Document {i+1}:\n{c}" for i, c in enumerate(all_chunks)
                )
                system_ctx += (
                    f"\n\nThe following documents may or may not be relevant. "
                    f"Use only what helps answer the question.\n\n{chunks_text}"
                )
            else:
                chunks_text = "\n".join(f"- {c}" for c in oracle_formatted)
                system_ctx += f"\n\nRelevant context:\n{chunks_text}"

        example = {
            "messages": [
                {"role": "system", "content": system_ctx},
                {"role": "user", "content": e["query"]},
                {"role": "assistant", "content": e["response"]},
            ],
            "quality_score": quality,
            "metadata": {
                "task_id": e.get("task_id", ""),
                "session_id": e.get("session_id", ""),
                "turns": e.get("total_turns", 0),
                "latency_ms": e.get("latency_ms", 0),
                "rag_context_words": e.get("rag_context_words", 0),
                "format": e.get("format", "raft_v2"),
                "ts": e.get("ts", ""),
            },
        }
        stamp_provenance(example, e, quality)
        examples.append(example)

    return examples


def build_dpo_pairs(entries: list) -> list:
    """Build DPO preference pairs from retry sequences.

    When the same task_id has a failed attempt followed by a successful one,
    that's a natural (rejected, chosen) pair.
    """
    # Group by task_id
    by_task = defaultdict(list)
    for e in entries:
        tid = e.get("task_id", "")
        if tid:
            by_task[tid].append(e)

    pairs = []
    for task_id, task_entries in by_task.items():
        # Sort by timestamp
        task_entries.sort(key=lambda x: x.get("ts", ""))

        failed = []
        succeeded = []
        for e in task_entries:
            if e.get("outcome") == "completed" and e.get("response"):
                succeeded.append(e)
            elif e.get("outcome") in ("blocked", "error", "timeout") and e.get("response"):
                failed.append(e)

        # Pair each failed attempt with the next successful one
        for f in failed:
            for s in succeeded:
                if s.get("ts", "") > f.get("ts", ""):
                    pair = {
                        "prompt": f.get("query", ""),
                        "chosen": s.get("response", ""),
                        "rejected": f.get("response", ""),
                        "metadata": {
                            "task_id": task_id,
                            "failed_ts": f.get("ts", ""),
                            "succeeded_ts": s.get("ts", ""),
                        },
                    }
                    pairs.append(pair)
                    break  # One pair per failure

    return pairs


def load_jsonl(path: Path) -> list:
    """Load any JSONL file."""
    if not path.exists():
        return []
    entries = []
    for lineno, line in enumerate(path.read_text().strip().split("\n"), 1):
        if line.strip():
            try:
                entry = json.loads(line)
                entry["_source_file"] = str(path)
                entry["_source_line"] = lineno
                entries.append(entry)
            except json.JSONDecodeError:
                pass
    return entries


def sft_from_loop_turns(entries: list) -> list:
    """Convert loop_turns.jsonl entries into SFT chat format.

    Schema: {turn_id, brother, intent, actions[], decisions[], outcome,
             tools_used[], confidence, context}
    """
    examples = []
    for e in entries:
        intent = e.get("intent", "")
        if not intent:
            continue

        # Skip exhausted/error outcomes — low-quality training signal
        outcome = e.get("outcome", "")
        if any(k in outcome.lower() for k in ("exhausted", "error")):
            continue

        # Build assistant response from actions + decisions + outcome
        parts = []
        actions = e.get("actions", [])
        if actions:
            parts.append("Actions taken:\n" + "\n".join(f"- {a}" for a in actions))
        decisions = e.get("decisions", [])
        if decisions:
            parts.append("Key decisions:\n" + "\n".join(f"- {d}" for d in decisions))
        if outcome:
            parts.append(f"Outcome: {outcome}")

        response = "\n\n".join(parts)
        if not response.strip():
            continue

        # System context from brother role + context field + tools_used
        brother = e.get("brother", "code")
        ctx = e.get("context", "")
        tools_used = e.get("tools_used", [])
        system_ctx = f"You are {brother} brother — an AI agent working on the Nucleus project."
        if ctx:
            system_ctx += f"\n\nContext: {ctx}"
        if tools_used:
            system_ctx += f"\n\nAvailable tools: {', '.join(tools_used)}"

        confidence = e.get("confidence", 0.5)

        example = {
            "messages": [
                {"role": "system", "content": system_ctx},
                {"role": "user", "content": intent},
                {"role": "assistant", "content": response},
            ],
            "metadata": {
                "source": "loop_turns",
                "turn_id": e.get("turn_id", ""),
                "brother": brother,
                "confidence": confidence,
                "sampling_weight": max(confidence, 0.1),
                "tools_used": tools_used,
                "ts": e.get("timestamp", ""),
            },
        }
        stamp_provenance(example, e, confidence)
        examples.append(example)

    return examples


def dpo_from_preference_pairs(entries: list) -> list:
    """Convert preference_pairs.jsonl into DPO format.

    Schema: {pref_id, prompt, chosen, rejected, source, metadata}
    Already in the right shape — just normalize.
    """
    pairs = []
    for e in entries:
        prompt = e.get("prompt", "")
        chosen = e.get("chosen", "")
        rejected = e.get("rejected", "")
        if not (prompt and chosen and rejected):
            continue

        pair = {
            "prompt": prompt,
            "chosen": chosen,
            "rejected": rejected,
            "metadata": {
                "source": "preference_pairs",
                "pref_id": e.get("pref_id", ""),
                "mined_from": e.get("metadata", {}).get("mined_from", ""),
                "ts": e.get("timestamp", ""),
            },
        }
        pairs.append(pair)

    return pairs


def training_from_human_verdicts(entries: list) -> tuple[list, list]:
    """Convert human_verdicts.jsonl into training signals.

    Produces:
      - Platinum SFT from accepted verdicts (human says correct)
      - Platinum DPO from rejected/corrected verdicts
        (machine output = rejected, human correction = chosen)

    Skips entries still pending review.
    """
    sft_examples = []
    dpo_pairs = []

    for e in entries:
        verdict = e.get("verdict", "pending")
        if verdict == "pending":
            continue

        task_desc = e.get("task_description", "")
        if not task_desc:
            continue

        receipt = e.get("verification_receipt", {})
        failed_checks = [s.get("check", "") for s in receipt.get("signals", [])
                         if not s.get("passed", True)]

        if verdict == "accepted":
            # Human verified the output is correct despite GROUND failure
            # → platinum SFT (GROUND was wrong / too strict)
            sft_examples.append({
                "messages": [
                    {"role": "system", "content": "You are an expert engineer. The automated verification flagged issues, but human review confirmed the output is correct."},
                    {"role": "user", "content": task_desc},
                    {"role": "assistant", "content": e.get("human_notes", "Output accepted after review.")},
                ],
                "metadata": {
                    "source": "human_verdict",
                    "quality": "platinum",
                    "verdict": "accepted",
                    "task_id": e.get("task_id", ""),
                    "failed_checks": failed_checks,
                    "ts": e.get("ts", ""),
                },
            })

        elif verdict in ("rejected", "corrected"):
            # Human provided correction → DPO pair
            correction = e.get("correction", e.get("human_notes", ""))
            original = e.get("original_output", "")
            if correction and original:
                dpo_pairs.append({
                    "prompt": task_desc,
                    "chosen": correction,
                    "rejected": original,
                    "metadata": {
                        "source": "human_verdict",
                        "quality": "platinum",
                        "verdict": verdict,
                        "task_id": e.get("task_id", ""),
                        "failed_checks": failed_checks,
                        "ts": e.get("ts", ""),
                    },
                })
            elif correction:
                # No original to reject against, but correction is platinum SFT
                sft_examples.append({
                    "messages": [
                        {"role": "system", "content": "You are an expert engineer. This is a human-corrected response after automated verification failure."},
                        {"role": "user", "content": task_desc},
                        {"role": "assistant", "content": correction},
                    ],
                    "metadata": {
                        "source": "human_verdict",
                        "quality": "platinum",
                        "verdict": verdict,
                        "task_id": e.get("task_id", ""),
                        "ts": e.get("ts", ""),
                    },
                })

    return sft_examples, dpo_pairs


def load_all_sources() -> dict:
    """Load all training data sources and return counts + data."""
    data = {}
    for name, path in SOURCES.items():
        entries = load_jsonl(path)
        data[name] = entries
    return data


def build_combined(data: dict, min_quality: float = 0.4) -> tuple:
    """Build combined SFT + DPO from all sources."""
    all_sft = []
    all_dpo = []

    # 1. Loop turns → SFT (821 entries)
    loop_sft = sft_from_loop_turns(data.get("loop_turns", []))
    all_sft.extend(loop_sft)

    # 2. Shadow logs → SFT + DPO (driver + training)
    for key in ("driver_shadow", "training_shadow"):
        entries = data.get(key, [])
        shadow_sft = build_sft_examples(entries, min_quality=min_quality)
        shadow_dpo = build_dpo_pairs(entries)
        all_sft.extend(shadow_sft)
        all_dpo.extend(shadow_dpo)

    # 3. Preference pairs → DPO (51 entries)
    pref_dpo = dpo_from_preference_pairs(data.get("preference_pairs", []))
    all_dpo.extend(pref_dpo)

    # 4. Human verdicts → platinum SFT + DPO (GROUND → ALIGN → COMPOUND loop)
    verdict_sft, verdict_dpo = training_from_human_verdicts(
        data.get("human_verdicts", []))
    all_sft.extend(verdict_sft)
    all_dpo.extend(verdict_dpo)

    return all_sft, all_dpo


def compute_stats(entries: list, sft: list, dpo: list) -> dict:
    """Compute summary statistics."""
    outcomes = defaultdict(int)
    total_turns = 0
    total_latency = 0
    total_ctx_words = 0

    for e in entries:
        outcomes[e.get("outcome", "unknown")] += 1
        total_turns += e.get("total_turns", 0)
        total_latency += e.get("latency_ms", 0)
        total_ctx_words += e.get("rag_context_words", 0)

    n = len(entries) or 1
    return {
        "total_entries": len(entries),
        "outcomes": dict(outcomes),
        "sft_examples": len(sft),
        "dpo_pairs": len(dpo),
        "avg_turns": round(total_turns / n, 1),
        "avg_latency_ms": round(total_latency / n),
        "avg_context_words": round(total_ctx_words / n),
        "unique_tasks": len(set(e.get("task_id", "") for e in entries)),
        "unique_sessions": len(set(e.get("session_id", "") for e in entries)),
    }


def write_provenance_index(out_dir: Path, sft: list):
    """Write provenance_index.jsonl — one row per SFT example for traceability."""
    index_path = out_dir / "provenance_index.jsonl"
    with open(index_path, "w") as f:
        for i, ex in enumerate(sft):
            prov = ex.get("provenance")
            if not prov:
                continue
            row = {
                "example_index": i,
                "hash": prov["hash"],
                "source_file": prov["source_file"],
                "line_number": prov["line_number"],
                "quality_score": prov["quality_score"],
                "processing_timestamp": prov["processing_timestamp"],
            }
            f.write(json.dumps(row) + "\n")
    return index_path


def export(out_dir: Path, sft: list, dpo: list, stats: dict):
    """Write SFT and DPO datasets to output directory."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # SFT
    sft_path = out_dir / "raft_sft_v1.jsonl"
    with open(sft_path, "w") as f:
        for example in sft:
            f.write(json.dumps(example) + "\n")

    # DPO
    dpo_path = out_dir / "raft_dpo_v1.jsonl"
    with open(dpo_path, "w") as f:
        for pair in dpo:
            f.write(json.dumps(pair) + "\n")

    # Provenance index
    prov_path = write_provenance_index(out_dir, sft)

    # Stats
    stats_path = out_dir / "raft_export_stats.json"
    stats["exported_at"] = datetime.now().isoformat()
    stats["sft_path"] = str(sft_path)
    stats["dpo_path"] = str(dpo_path)
    stats["provenance_path"] = str(prov_path)
    stats_path.write_text(json.dumps(stats, indent=2))

    return sft_path, dpo_path, stats_path


def quality_histogram(sft_examples: list) -> str:
    """Build a quality-score histogram string for SFT examples."""
    buckets = {"0.0-0.2": 0, "0.2-0.4": 0, "0.4-0.6": 0, "0.6-0.8": 0, "0.8-1.0": 0}
    for ex in sft_examples:
        q = ex.get("quality_score", 0.0)
        if q <= 0.2:
            buckets["0.0-0.2"] += 1
        elif q <= 0.4:
            buckets["0.2-0.4"] += 1
        elif q <= 0.6:
            buckets["0.4-0.6"] += 1
        elif q <= 0.8:
            buckets["0.6-0.8"] += 1
        else:
            buckets["0.8-1.0"] += 1
    total = len(sft_examples) or 1
    lines = ["  Quality distribution:"]
    for label, count in buckets.items():
        bar = "#" * int(40 * count / total)
        lines.append(f"    {label:7s} | {bar:40s} {count}")
    return "\n".join(lines)


def print_stats(stats: dict, sft_examples: list | None = None):
    """Pretty-print statistics."""
    print(f"""
RAFT Training Data Export
=========================
  Shadow log entries:  {stats['total_entries']}
  Unique tasks:        {stats['unique_tasks']}
  Unique sessions:     {stats['unique_sessions']}

  Outcomes:""")
    for outcome, count in sorted(stats.get("outcomes", {}).items()):
        print(f"    {outcome:20s} {count}")

    print(f"""
  SFT examples:       {stats['sft_examples']}
  DPO pairs:          {stats['dpo_pairs']}

  Avg turns/task:      {stats['avg_turns']}
  Avg latency:         {stats['avg_latency_ms']}ms
  Avg context words:   {stats['avg_context_words']}
""")
    if sft_examples:
        print(quality_histogram(sft_examples))
        print()


def export_combined(out_dir: Path, sft: list, dpo: list, source_counts: dict):
    """Write combined SFT and DPO datasets."""
    out_dir.mkdir(parents=True, exist_ok=True)

    sft_path = out_dir / "combined_sft_v1.jsonl"
    with open(sft_path, "w") as f:
        for example in sft:
            f.write(json.dumps(example) + "\n")

    dpo_path = out_dir / "combined_dpo_v1.jsonl"
    with open(dpo_path, "w") as f:
        for pair in dpo:
            f.write(json.dumps(pair) + "\n")

    # Provenance index
    prov_path = write_provenance_index(out_dir, sft)

    stats = {
        "exported_at": datetime.now().isoformat(),
        "sft_total": len(sft),
        "dpo_total": len(dpo),
        "source_counts": source_counts,
        "sft_path": str(sft_path),
        "dpo_path": str(dpo_path),
        "provenance_path": str(prov_path),
    }
    stats_path = out_dir / "combined_export_stats.json"
    stats_path.write_text(json.dumps(stats, indent=2))

    return sft_path, dpo_path, stats_path


def main():
    parser = argparse.ArgumentParser(description="RAFT Training Data Export")
    parser.add_argument("--stats", action="store_true", help="Show stats only, no export")
    parser.add_argument("--combined", action="store_true",
                        help="Merge all training sources (loop_turns, preference_pairs, shadow logs)")
    parser.add_argument("--out", type=str, default=str(DEFAULT_OUT),
                        help="Output directory")
    parser.add_argument("--log", type=str, default=str(SHADOW_LOG),
                        help="Path to shadow_log.jsonl")
    parser.add_argument("--min-quality", type=float, default=0.4,
                        help="Minimum quality score threshold (0.0-1.0, default 0.4)")
    parser.add_argument("--verified-only", action="store_true",
                        help="Export only execution-verified or human-reviewed entries")
    args = parser.parse_args()

    if args.combined:
        # Combined mode: merge all sources
        data = load_all_sources()
        source_counts = {name: len(entries) for name, entries in data.items()}
        total = sum(source_counts.values())

        if total == 0:
            print("No training data found in any source.")
            return

        sft, dpo = build_combined(data, min_quality=args.min_quality)

        # Frontier filter: --verified-only
        if getattr(args, 'verified_only', False):
            def _is_verified(entry):
                meta = entry.get("metadata", entry.get("provenance", {}))
                return (meta.get("execution_verified") is True or
                        meta.get("source") == "human_review" or
                        meta.get("quality") == "platinum")
            sft = [e for e in sft if _is_verified(e)]
            dpo = [e for e in dpo if _is_verified(e)]

        print(f"""
Combined Training Data Export
==============================
  Sources:""")
        for name, count in source_counts.items():
            print(f"    {name:25s} {count:5d} entries")
        print(f"    {'TOTAL':25s} {total:5d} entries")
        print(f"""
  Output:
    SFT examples:  {len(sft)}  (min_quality={args.min_quality})
    DPO pairs:     {len(dpo)}
""")
        print(quality_histogram(sft))
        print()

        if not args.stats:
            sft_path, dpo_path, stats_path = export_combined(
                Path(args.out), sft, dpo, source_counts)
            print(f"  Exported:")
            print(f"    SFT:   {sft_path} ({len(sft)} examples)")
            print(f"    DPO:   {dpo_path} ({len(dpo)} pairs)")
            print(f"    Stats: {stats_path}")
        return

    # Original mode: single shadow log
    entries = load_shadow_log(Path(args.log))
    if not entries:
        print("No entries in shadow log.")
        return

    sft = build_sft_examples(entries, min_quality=args.min_quality)
    dpo = build_dpo_pairs(entries)
    stats = compute_stats(entries, sft, dpo)

    print_stats(stats, sft_examples=sft)

    if not args.stats:
        sft_path, dpo_path, stats_path = export(Path(args.out), sft, dpo, stats)
        print(f"  Exported:")
        print(f"    SFT:   {sft_path} ({len(sft)} examples)")
        print(f"    DPO:   {dpo_path} ({len(dpo)} pairs)")
        print(f"    Stats: {stats_path}")


if __name__ == "__main__":
    main()
