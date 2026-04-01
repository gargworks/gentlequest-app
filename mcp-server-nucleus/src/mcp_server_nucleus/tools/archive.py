"""Archive tool — MCP interface for the Third Brother training data flywheel.

Exposes archive operations (stats, record, recent, export) so both brothers
can contribute to the training data through MCP tool calls.
"""

import json

from ._dispatch import dispatch


def register(mcp, helpers):
    """Register the nucleus_archive facade tool with the MCP server."""
    make_response = helpers["make_response"]

    def _h_stats():
        from ..runtime.archive_pipeline import ArchivePipeline
        archive = ArchivePipeline()
        stats = archive.get_stats()
        return make_response(True, data=stats)

    def _h_recent(limit=10):
        from ..runtime.archive_pipeline import ArchivePipeline
        archive = ArchivePipeline()
        turns = archive.get_turns(limit=int(limit))
        return make_response(True, data={"turns": turns, "count": len(turns)})

    def _h_record(brother="code", intent="", outcome="", decisions=None,
                  actions=None, tools_used=None, context="", confidence=0.8,
                  conversation=None):
        from ..runtime.archive_pipeline import ArchivePipeline
        archive = ArchivePipeline()
        turn = archive.record_turn(
            brother=brother,
            intent=intent,
            actions=actions or [],
            tools_used=tools_used or [],
            decisions=decisions or [],
            outcome=outcome,
            signal_absorbed=[],
            signal_produced=[],
            confidence=float(confidence),
            context=context or f"MCP tool call ({brother})",
            conversation=conversation or [],
        )
        return make_response(True, data={
            "turn_id": turn.turn_id,
            "brother": brother,
            "message": f"Recorded turn {turn.turn_id}",
        })

    def _h_export(format="all"):
        from ..runtime.archive_pipeline import ArchivePipeline
        archive = ArchivePipeline()
        out_dir = archive.training_dir / "exports"
        out_dir.mkdir(parents=True, exist_ok=True)
        results = {}
        if format in ("gemini", "all"):
            results["gemini"] = archive.export_gemini(str(out_dir / "gemini_training.jsonl"))
        if format in ("openai", "all"):
            results["openai"] = archive.export_openai(str(out_dir / "openai_training.jsonl"))
        if format in ("anthropic", "all"):
            results["anthropic"] = archive.export_anthropic(str(out_dir / "anthropic_training.jsonl"))
        return make_response(True, data={
            "exported": results,
            "output_dir": str(out_dir),
        })

    def _h_retrain_status():
        from ..runtime.archive_pipeline import ArchivePipeline
        archive = ArchivePipeline()
        rt = archive.should_retrain()
        rt["dpo_pairs"] = archive.count_preferences()
        return make_response(True, data=rt)

    def _h_dpo_status():
        from ..runtime.archive_pipeline import ArchivePipeline
        archive = ArchivePipeline()
        return make_response(True, data=archive.get_preference_stats())

    def _h_record_preference(prompt="", chosen="", rejected="",
                             source="manual", metadata=None):
        from ..runtime.archive_pipeline import ArchivePipeline
        archive = ArchivePipeline()
        pref = archive.record_preference(
            prompt=prompt, chosen=chosen, rejected=rejected,
            source=source, metadata=metadata or {},
        )
        if pref:
            return make_response(True, data={
                "pref_id": pref["pref_id"],
                "source": source,
                "message": f"Recorded preference {pref['pref_id']}",
            })
        return make_response(False, error="Preference pair too short or identical")

    def _h_cot_status():
        from ..runtime.archive_pipeline import ArchivePipeline
        archive = ArchivePipeline()
        return make_response(True, data=archive.get_reasoning_stats())

    # ── Phase 2: Delta Operations ────────────────────────────────

    def _h_record_delta(frontier="GROUND", expected_source="", expected_intent="",
                        actual_source="", actual_outcome="", insight="",
                        corrections=None):
        from ..runtime.delta_ops import record_delta
        delta_id = record_delta(
            frontier=frontier,
            expected_source=expected_source,
            expected_intent=expected_intent,
            actual_source=actual_source,
            actual_outcome=actual_outcome,
            insight=insight,
            corrections=corrections,
        )
        if delta_id:
            return make_response(True, data={
                "delta_id": delta_id,
                "frontier": frontier,
                "message": f"Delta recorded: {delta_id}",
            })
        return make_response(False, error="Failed to record delta (invalid frontier or no brain path)")

    def _h_query_deltas(frontier=None, direction=None, since=None, limit=200):
        from ..runtime.delta_ops import query_deltas
        results = query_deltas(
            frontier=frontier,
            direction=direction,
            since=since,
            limit=int(limit),
        )
        return make_response(True, data={
            "deltas": results,
            "count": len(results),
        })

    def _h_extract_patterns(since=None, frontier=None):
        from ..runtime.delta_ops import extract_patterns
        patterns = extract_patterns(since=since, frontier=frontier)
        return make_response(True, data=patterns)

    def _h_frontier_health(timerange="7d"):
        """Three Frontiers health dashboard — GROUND/ALIGN/COMPOUND metrics."""
        from ..runtime.common import get_brain_path
        from ..runtime.hardening import safe_read_jsonl
        from ..runtime.delta_ops import extract_patterns
        brain = get_brain_path()

        # GROUND: verification receipts
        ground = {"total_verifications": 0, "pass_rate": 0.0, "avg_tier_reached": 0.0}
        try:
            vlog = brain / "verification_log.jsonl"
            if vlog.exists():
                receipts = safe_read_jsonl(vlog)
                if receipts:
                    ground["total_verifications"] = len(receipts)
                    passed = sum(1 for r in receipts if not r.get("tiers_failed"))
                    ground["pass_rate"] = round(passed / len(receipts), 3)
                    ground["avg_tier_reached"] = round(
                        sum(r.get("tier_reached", 0) for r in receipts) / len(receipts), 1
                    )
        except Exception:
            pass

        # ALIGN: human verdicts
        align = {"total_reviews": 0, "accepted": 0, "rejected": 0, "corrected": 0, "redirected": 0}
        try:
            vpath = brain / "driver" / "human_verdicts.jsonl"
            if vpath.exists():
                verdicts = safe_read_jsonl(vpath)
                non_pending = [v for v in verdicts if v.get("verdict") != "pending"]
                align["total_reviews"] = len(non_pending)
                for v in non_pending:
                    vtype = v.get("verdict", "")
                    if vtype in align:
                        align[vtype] += 1
        except Exception:
            pass

        # COMPOUND: delta patterns
        compound = {"total_deltas": 0, "compound_rate": 0.0, "recurring_patterns": 0}
        try:
            patterns = extract_patterns(since=timerange)
            compound["total_deltas"] = patterns.get("total_deltas", 0)
            compound["compound_rate"] = patterns.get("compound_rate", 0.0)
            compound["recurring_patterns"] = len(patterns.get("recurring_negatives", []))
            compound["frontier_health"] = patterns.get("frontier_health", {})
        except Exception:
            pass

        return make_response(True, data={
            "timerange": timerange,
            "GROUND": ground,
            "ALIGN": align,
            "COMPOUND": compound,
        })

    ACTION_MAP = {
        "stats": (_h_stats, "Show archive statistics"),
        "recent": (_h_recent, "Show recent loop turns"),
        "record": (_h_record, "Record a loop turn"),
        "export": (_h_export, "Export training data for fine-tuning"),
        "retrain_status": (_h_retrain_status, "Check if new training is recommended"),
        "dpo_status": (_h_dpo_status, "Show DPO preference pair statistics"),
        "record_preference": (_h_record_preference, "Record a DPO preference pair (prompt, chosen, rejected)"),
        "cot_status": (_h_cot_status, "Show reasoning chain (CoT) statistics"),
        "record_delta": (_h_record_delta, "Record a Delta — measured gap between intent and reality"),
        "query_deltas": (_h_query_deltas, "Query accumulated deltas (filter by frontier, direction, since)"),
        "extract_patterns": (_h_extract_patterns, "Extract meta-patterns from accumulated deltas"),
        "frontier_health": (_h_frontier_health, "Three Frontiers health dashboard — GROUND/ALIGN/COMPOUND metrics"),
    }

    @mcp.tool()
    async def nucleus_archive(action: str, params: dict = None) -> str:
        """📊 Training data archive — the Third Brother flywheel.

        Actions:
        - stats: Show archive statistics (total turns, by brother, timestamps)
        - recent: Show recent loop turns (params: limit=10)
        - record: Record a loop turn (params: brother, intent, outcome, decisions, actions, tools_used, context, confidence, conversation)
        - export: Export training data (params: format=all|gemini|openai|anthropic)
        - retrain_status: Check if enough new data has accumulated to retrain
        - dpo_status: Show DPO preference pair statistics (source breakdown)
        - record_preference: Record a DPO pair (params: prompt, chosen, rejected, source)
        - cot_status: Show reasoning chain (Chain-of-Thought) statistics
        - record_delta: Record a Delta — gap between intent and reality (params: frontier, expected_source, expected_intent, actual_source, actual_outcome, insight, corrections)
        - query_deltas: Query deltas (params: frontier, direction, since, limit)
        - extract_patterns: Extract meta-patterns from accumulated deltas (params: since, frontier)
        - frontier_health: Three Frontiers health dashboard (params: timerange=7d)
        """
        return dispatch("nucleus_archive", action, params or {}, ACTION_MAP, make_response)

    return [("nucleus_archive", nucleus_archive)]
