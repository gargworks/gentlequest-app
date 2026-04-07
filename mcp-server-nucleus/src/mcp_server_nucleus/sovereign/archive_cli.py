"""Sovereign: Archive CLI — training data flywheel for the Third Brother.

Extracted from cli.py to enable structural separation.
This file is excluded from public builds via .gitattributes export-ignore.
"""

def register_archive_subparser(subparsers):
    """Register the archive command and all its subcommands."""
    archive_parser = subparsers.add_parser('archive', help='📊 Training data archive — the Third Brother flywheel')
    archive_subparsers = archive_parser.add_subparsers(dest='archive_command')
    archive_subparsers.add_parser('status', help='Retrain readiness check — should you train now?')
    archive_subparsers.add_parser('stats', help='Show archive statistics')
    archive_subparsers.add_parser('recent', help='Show recent loop turns')
    archive_export = archive_subparsers.add_parser('export', help='Export training data for fine-tuning')
    archive_export.add_argument('--format', choices=['gemini', 'openai', 'anthropic', 'all'], default='all', help='Export format (default: all)')
    archive_export.add_argument('--output', type=str, default=None, help='Output directory (default: .brain/training/exports/)')
    archive_record = archive_subparsers.add_parser('record', help='Manually record a loop turn')
    archive_record.add_argument('--brother', choices=['code', 'cowork', 'father'], default='father', help='Who is recording')
    archive_record.add_argument('--intent', type=str, required=True, help='What this turn set out to do')
    archive_record.add_argument('--outcome', type=str, required=True, help='What happened')
    archive_record.add_argument('--decisions', type=str, nargs='*', default=[], help='Key decisions made')
    archive_train = archive_subparsers.add_parser('train', help='Prepare or launch fine-tuning for the Third Brother')
    archive_train.add_argument('--target', choices=['gemini', 'openai', 'local'], default='local',
                               help='Training target: gemini (Vertex AI), openai (API), local (Ollama/unsloth)')
    archive_train.add_argument('--dry-run', action='store_true', help='Export data only, do not launch training')
    archive_ingest = archive_subparsers.add_parser('ingest', help='Bulk import conversations from Gemini/Claude transcripts')
    archive_ingest.add_argument('paths', nargs='+', help='Paths to conversation files (Gemini .json or Claude .md)')
    archive_ingest.add_argument('--brother', choices=['code', 'cowork'], default='code', help='Which brother had this conversation')
    archive_subparsers.add_parser('ingest-threads', help='Bridge thread.jsonl (chat history) into training archive')
    archive_subparsers.add_parser('mark-trained', help='Mark current archive as trained (resets retrain counter)')
    archive_subparsers.add_parser('dpo-status', help='Show DPO preference pair statistics')
    archive_dpo_export = archive_subparsers.add_parser('dpo-export', help='Export DPO preference pairs for training')
    archive_dpo_export.add_argument('--output', type=str, default=None, help='Output path (default: .brain/training/exports/dpo_training.jsonl)')
    archive_dpo_export.add_argument('--balanced', action='store_true', help='Balance DPO sources (prevent shadow drowning corrections)')
    archive_dpo_export.add_argument('--exclude-unjudged', action='store_true', help='Drop shadow pairs without LLM judge verification')
    archive_subparsers.add_parser('cot-status', help='Show reasoning chain (Chain-of-Thought) statistics')
    archive_cot_export = archive_subparsers.add_parser('cot-export', help='Export reasoning chains as <think>-tagged training data')
    archive_cot_export.add_argument('--output', type=str, default=None, help='Output path (default: .brain/training/exports/reasoning_training.jsonl)')
    archive_subparsers.add_parser('mine', help='Mine DPO + CoT data from existing archive (retroactive extraction)')
    archive_eval = archive_subparsers.add_parser('eval', help='Generate eval benchmark from archive (measure before/after training)')
    archive_eval.add_argument('--count', type=int, default=50, help='Number of eval cases (default: 50)')
    archive_eval.add_argument('--export', type=str, default=None, help='Export eval suite to JSONL')
    archive_eval.add_argument('--run', type=str, default=None, help='Run eval against a provider (gemini/anthropic/groq/local)')
    archive_eval.add_argument('--judge', type=str, default=None, help='LLM provider for scoring (accurate). Omit for fast offline heuristic.')
    archive_synth = archive_subparsers.add_parser('synthesize', help='Self-play: manufacture DPO pairs from existing prompts via LLM')
    archive_synth.add_argument('--provider', type=str, default='gemini', help='LLM provider for generation (default: gemini)')
    archive_synth.add_argument('--count', type=int, default=100, help='Number of pairs to synthesize (default: 100)')
    archive_synth.add_argument('--judge', type=str, default=None, help='LLM provider for judging (enables LLM-as-Judge instead of heuristic)')
    archive_spin = archive_subparsers.add_parser('spin', help='Iterative self-play: trained model vs base model (SPIN)')
    archive_spin.add_argument('--current', type=str, required=True, help='Current trained model provider (e.g., local)')
    archive_spin.add_argument('--base', type=str, default='gemini', help='Base model provider (default: gemini)')
    archive_spin.add_argument('--judge', type=str, default=None, help='LLM judge provider (default: heuristic)')
    archive_spin.add_argument('--count', type=int, default=100, help='Number of comparisons (default: 100)')
    archive_spin.add_argument('--round', type=int, default=1, help='SPIN round number (default: 1)')
    archive_active = archive_subparsers.add_parser('active-learn', help='Active learning: generate targeted data for model weaknesses')
    archive_active.add_argument('--provider', type=str, default='gemini', help='LLM provider for generation')
    archive_active.add_argument('--eval-provider', type=str, default=None, help='Run eval first against this provider to find weaknesses')
    archive_active.add_argument('--count', type=int, default=20, help='Pairs per weakness (default: 20)')
    archive_conductor = archive_subparsers.add_parser('conductor', help='Training conductor: show status + next recommended action')
    archive_pipeline = archive_subparsers.add_parser('pipeline', help='Run full training pipeline (mine → synthesize → export)')
    archive_pipeline.add_argument('--provider', type=str, default=None, help='LLM provider for synthesis (omit to skip synthesis)')
    archive_pipeline.add_argument('--judge', type=str, default=None, help='LLM provider for judging (enables LLM-as-Judge)')
    archive_pipeline.add_argument('--dry-run', action='store_true', help='Show what would happen without executing')
    archive_constitutional = archive_subparsers.add_parser('constitutional', help='Constitutional AI: self-critique → self-revision → DPO pairs')
    archive_constitutional.add_argument('--provider', type=str, default='gemini', help='LLM for critique and revision')
    archive_constitutional.add_argument('--count', type=int, default=100, help='Number of turns to process (default: 100)')
    archive_quality = archive_subparsers.add_parser('quality', help='Score training data quality and show distribution')
    archive_quality.add_argument('--export', type=str, default=None, help='Export filtered data to path')
    archive_quality.add_argument('--min-quality', type=float, default=0.4, help='Minimum quality threshold (default: 0.4)')
    archive_quality.add_argument('--format', choices=['openai', 'gemini', 'anthropic'], default='openai', help='Export format')
    archive_quality.add_argument('--curriculum', action='store_true', help='Sort training data easy→hard (curriculum learning)')
    archive_register = archive_subparsers.add_parser('register', help='Register a trained model version in the registry')
    archive_register.add_argument('version', help='Version string (e.g., v1, v2.1)')
    archive_register.add_argument('--base', type=str, default='llama3.2:3b', help='Base model used (default: llama3.2:3b)')
    archive_subparsers.add_parser('registry', help='Show all registered model versions')
    archive_promote = archive_subparsers.add_parser('promote', help='Promote a model version (shadow → canary → primary)')
    archive_promote.add_argument('version', help='Version to promote')
    archive_promote.add_argument('--to', type=str, required=True, choices=['shadow', 'canary', 'primary', 'retired'], help='Target status')
    archive_subparsers.add_parser('shadow-stats', help='Show shadow mode performance (Third Brother vs primary)')
    archive_subparsers.add_parser('graduation', help='Check if Third Brother should be promoted')
    archive_vault = archive_subparsers.add_parser('vault', help='List all model versions stored in the vault (SSD)')  # noqa: F841
    archive_vault_restore = archive_subparsers.add_parser('vault-restore', help='Restore a model version from the vault')
    archive_vault_restore.add_argument('version', help='Version to restore (e.g., v1)')
    archive_rollback = archive_subparsers.add_parser('rollback', help='Rollback to a previous model version (retire current, restore target)')
    archive_rollback.add_argument('version', help='Version to rollback to (e.g., v1)')


def handle_archive_command(args) -> int:
    """Handle nucleus archive — training data flywheel for the Third Brother."""
    try:
        from .runtime.archive_pipeline import ArchivePipeline
    except ImportError:
        print("Archive commands are not available in this build.")
        print("Install the full version: pip install nucleus-mcp[full]")
        return 1

    archive = ArchivePipeline()
    cmd = getattr(args, 'archive_command', None)

    if cmd == 'stats':
        stats = archive.get_stats()
        print("=" * 50)
        print("📊 ARCHIVE STATS — Third Brother Training Data")
        print("=" * 50)
        print(f"  Total turns:  {stats.get('total_turns', 0)}")
        by_bro = stats.get('by_brother', {})
        for bro, count in sorted(by_bro.items()):
            print(f"  {bro:12s}:  {count}")
        print(f"  First turn:   {stats.get('first_turn', 'n/a')}")
        print(f"  Last turn:    {stats.get('last_turn', 'n/a')}")
        print()
        print(f"  Archive:  {archive.turns_file}")
        return 0

    elif cmd == 'recent':
        turns = archive.get_turns(limit=10)
        if not turns:
            print("No turns recorded yet. Start a chat session or run an agent.")
            return 0
        print("=" * 50)
        print(f"📜 RECENT LOOP TURNS (last {len(turns)})")
        print("=" * 50)
        for t in turns:
            ts = t.get('timestamp', '')[:19]
            bro = t.get('brother', '?')
            intent = t.get('intent', '')[:60]
            has_conv = "💬" if t.get('conversation') else "📝"
            print(f"  {has_conv} [{ts}] {bro:7s} — {intent}")
        print()
        total = archive.get_stats().get('total_turns', len(turns))
        print(f"  Showing {len(turns)} of {total} total turns.")
        return 0

    elif cmd == 'export':
        fmt = getattr(args, 'format', 'all')
        out_dir = args.output or str(archive.training_dir / "exports")
        Path(out_dir).mkdir(parents=True, exist_ok=True)

        results = {}
        eval_results = {}
        if fmt in ('gemini', 'all'):
            p = str(Path(out_dir) / "gemini_training.jsonl")
            ep = str(Path(out_dir) / "gemini_eval.jsonl")
            results['gemini'] = archive.export_gemini(p, eval_path=ep)
            eval_results['gemini'] = sum(1 for _ in open(ep)) if Path(ep).exists() else 0
        if fmt in ('openai', 'all'):
            p = str(Path(out_dir) / "openai_training.jsonl")
            ep = str(Path(out_dir) / "openai_eval.jsonl")
            results['openai'] = archive.export_openai(p, eval_path=ep)
            eval_results['openai'] = sum(1 for _ in open(ep)) if Path(ep).exists() else 0
        if fmt in ('anthropic', 'all'):
            p = str(Path(out_dir) / "anthropic_training.jsonl")
            ep = str(Path(out_dir) / "anthropic_eval.jsonl")
            results['anthropic'] = archive.export_anthropic(p, eval_path=ep)
            eval_results['anthropic'] = sum(1 for _ in open(ep)) if Path(ep).exists() else 0

        print("=" * 50)
        print("📦 EXPORTED TRAINING DATA")
        print("=" * 50)
        for name, count in results.items():
            ev = eval_results.get(name, 0)
            print(f"  {name:12s}: {count} train + {ev} eval pairs")
        print(f"\n  Output: {out_dir}")
        return 0

    elif cmd == 'record':
        turn = archive.record_turn(
            brother=args.brother,
            intent=args.intent,
            actions=[],
            tools_used=[],
            decisions=args.decisions or [],
            outcome=args.outcome,
            signal_absorbed=[],
            signal_produced=[],
            confidence=1.0,
            context="Manual CLI recording",
        )
        print(f"✅ Recorded turn {turn.turn_id} ({args.brother})")
        return 0

    elif cmd == 'status':
        stats = archive.get_stats()
        retrain = archive.should_retrain()
        total = stats.get('total_turns', 0)

        print("=" * 50)
        print("🧬 THIRD BROTHER — Training Status")
        print("=" * 50)

        # SFT data
        print(f"  ── SFT (Supervised Fine-Tuning) ──")
        print(f"  Archive turns:    {total}")
        by_bro = stats.get('by_brother', {})
        for bro, count in sorted(by_bro.items()):
            print(f"    {bro:12s}:  {count}")
        pair_count = archive.count_quality_pairs()
        print(f"  Quality pairs:    {pair_count}")
        print(f"  Last trained at:  {retrain['last_trained_at']} turns")
        print(f"  New turns:        {retrain['new_turns']}")
        print()

        # DPO data
        dpo_count = archive.count_preferences()
        print(f"  ── DPO (Direct Preference Optimization) ──")
        print(f"  Preference pairs: {dpo_count}")
        if dpo_count > 0:
            pref_stats = archive.get_preference_stats()
            by_src = pref_stats.get('by_source', {})
            for src, count in sorted(by_src.items(), key=lambda x: -x[1]):
                print(f"    {src:12s}:  {count}")
        else:
            print(f"    (accumulates from /retry, corrections, outcomes)")
        print()

        # CoT data
        cot_count = archive.count_reasoning_chains()
        print(f"  ── CoT (Chain-of-Thought Reasoning) ──")
        print(f"  Reasoning chains: {cot_count}")
        if cot_count > 0:
            cot_stats = archive.get_reasoning_stats()
            print(f"    Total steps:    {cot_stats.get('total_steps', 0)}")
            print(f"    Avg steps:      {cot_stats.get('avg_steps', 0)}")
        else:
            print(f"    (accumulates from multi-step tool use in chat)")
        print()

        # Retrain recommendation
        if retrain['should_retrain']:
            print(f"  ✅ RETRAIN RECOMMENDED — {retrain['reason']}")
            print(f"     Phase 1: nucleus archive train          (SFT)")
            if dpo_count >= 50:
                print(f"     Phase 2: nucleus archive dpo-export     (DPO)")
            if cot_count >= 20:
                print(f"     Phase 3: nucleus archive cot-export     (CoT)")
        else:
            print(f"  ⏳ {retrain['reason']}")
        print()
        return 0

    elif cmd == 'train':
        stats = archive.get_stats()
        total = stats.get('total_turns', 0)
        target = getattr(args, 'target', 'local')
        dry_run = getattr(args, 'dry_run', False)
        retrain = archive.should_retrain()

        print("=" * 50)
        print("🧬 THIRD BROTHER — Fine-Tuning Pipeline")
        print("=" * 50)
        print(f"  Archive turns:  {total}")
        print(f"  Target:         {target}")
        if retrain['last_trained_at'] > 0:
            print(f"  New since last:  {retrain['new_turns']} turns")
            if retrain['should_retrain']:
                print(f"  Status:         RETRAIN RECOMMENDED")
            else:
                print(f"  Status:         {retrain['reason']}")

        # Minimum viable training set
        MIN_TURNS = 50
        if total < MIN_TURNS:
            print(f"\n  ⚠️  Need at least {MIN_TURNS} turns for meaningful training.")
            print(f"     Current: {total} ({MIN_TURNS - total} more needed)")
            print(f"\n  How to accumulate:")
            print(f"     • Run nucleus brother sessions (auto-recorded)")
            print(f"     • Run agent missions (auto-recorded)")
            print(f"     • nucleus archive record --intent '...' --outcome '...'")
            if total > 0 and dry_run:
                print(f"\n  Proceeding with export (dry-run)...")
            else:
                return 0

        # Export training data
        out_dir = str(archive.training_dir / "exports")
        Path(out_dir).mkdir(parents=True, exist_ok=True)

        if target == 'gemini':
            p = str(Path(out_dir) / "gemini_training.jsonl")
            count = archive.export_gemini(p)
            print(f"\n  Exported: {count} pairs → {p}")
            if not dry_run:
                print(f"\n  One-command cloud fine-tuning (no GPU needed):")
                print(f"    python scripts/train_gemini.py")
                print(f"\n  Or upload manually:")
                print(f"    https://aistudio.google.com/tuning")

        elif target == 'openai':
            p = str(Path(out_dir) / "openai_training.jsonl")
            count = archive.export_openai(p)
            print(f"\n  Exported: {count} pairs → {p}")
            if not dry_run:
                print(f"\n  To launch OpenAI fine-tuning:")
                print(f"    openai api fine_tuning.jobs.create \\")
                print(f"      -t {p} -m gpt-4o-mini-2024-07-18")

        elif target == 'local':
            # Export both OpenAI format (for unsloth/axolotl) and raw
            p = str(Path(out_dir) / "openai_training.jsonl")
            ep = str(Path(out_dir) / "openai_training.eval.jsonl")
            count = archive.export_openai(p, eval_path=ep)
            ev = sum(1 for _ in open(ep)) if Path(ep).exists() else 0
            print(f"\n  Exported: {count} train + {ev} eval pairs → {p}")
            if not dry_run:
                print(f"\n  One-shot training script:")
                print(f"    python scripts/train_third_brother.py")
                print(f"\n  Or manual options:")
                print(f"    1. Unsloth (fastest, free Colab T4):")
                print(f"       → Upload {p}")
                print(f"       → Base: unsloth/Qwen2.5-7B-Instruct → GGUF")
                print(f"    2. Ollama (from Modelfile):")
                print(f"       → ollama create nucleus-brother -f scripts/Modelfile")
                print(f"    3. axolotl (full control):")
                print(f"       → axolotl train config.yaml")
                print(f"\n  After training:")
                print(f"    nucleus brother --provider local")

        print()
        return 0

    elif cmd == 'ingest':
        paths = getattr(args, 'paths', [])
        brother = getattr(args, 'brother', 'code')
        total_ingested = 0

        print("=" * 50)
        print("📥 INGESTING CONVERSATIONS INTO ARCHIVE")
        print("=" * 50)

        for path in paths:
            p = Path(path)
            if not p.exists():
                print(f"  ⚠️  Not found: {path}")
                continue

            if p.suffix == '.json':
                count = archive.ingest_gemini_conversation(str(p), brother=brother)
                print(f"  ✅ {p.name}: {count} turns (Gemini)")
            elif p.suffix == '.md':
                count = archive.ingest_claude_markdown(str(p), brother=brother)
                print(f"  ✅ {p.name}: {count} turns (Claude)")
            else:
                print(f"  ⚠️  Unknown format: {p.name} (expected .json or .md)")
                count = 0

            total_ingested += count

        stats = archive.get_stats()
        print(f"\n  Ingested: {total_ingested} new turns")
        print(f"  Total archive: {stats.get('total_turns', 0)} turns")
        return 0

    elif cmd == 'ingest-threads':
        count = archive.ingest_thread_archive()
        stats = archive.get_stats()
        if count > 0:
            print(f"✅ Ingested {count} new turns from thread.jsonl")
        else:
            print(f"  No new data to ingest (already up to date or thread.jsonl empty)")
        print(f"   Total archive: {stats.get('total_turns', 0)} turns")
        return 0

    elif cmd == 'mark-trained':
        archive.mark_trained()
        stats = archive.get_stats()
        print(f"✅ Marked archive as trained at {stats.get('total_turns', 0)} turns.")
        print(f"   Retrain counter reset. New data will accumulate from here.")
        return 0

    elif cmd == 'dpo-status':
        pref_stats = archive.get_preference_stats()
        total_prefs = pref_stats.get('total_preferences', 0)
        print("=" * 50)
        print("🎯 DPO PREFERENCE PAIRS — Training the Third Brother's Taste")
        print("=" * 50)
        print(f"  Total pairs:   {total_prefs}")
        by_src = pref_stats.get('by_source', {})
        if by_src:
            print(f"  By source:")
            for src, count in sorted(by_src.items(), key=lambda x: -x[1]):
                label = {
                    "retry": "/retry (explicit rejection)",
                    "correction": "Correction pattern (no, instead...)",
                    "outcome": "Outcome signal (deploy/escalation)",
                    "review": "Code review (issues found)",
                    "manual": "Manual recording",
                }.get(src, src)
                print(f"    {src:12s}: {count:4d}  — {label}")
        if pref_stats.get('first'):
            print(f"  First pair:    {pref_stats['first'][:19]}")
            print(f"  Last pair:     {pref_stats['last'][:19]}")
        print()
        if total_prefs < 50:
            print(f"  ⏳ Need ~50+ pairs for meaningful DPO. Keep chatting!")
            print(f"     DPO pairs accumulate automatically from:")
            print(f"       • /retry (previous answer = rejected)")
            print(f"       • Corrections ('no, do X instead')")
            print(f"       • Deploy success/failure events")
            print(f"       • Task escalations")
        else:
            print(f"  ✅ Ready for DPO training!")
            print(f"     → nucleus archive dpo-export")
        print()
        return 0

    elif cmd == 'dpo-export':
        out_dir = args.output or str(archive.training_dir / "exports")
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        use_balanced = getattr(args, 'balanced', False)
        exclude_unjudged = getattr(args, 'exclude_unjudged', False)

        print("=" * 50)
        print("🎯 DPO EXPORT — Preference Training Data")
        print("=" * 50)

        if use_balanced:
            p = str(Path(out_dir) / "dpo_training_balanced.jsonl")
            result = archive.export_dpo_balanced(
                p, exclude_unjudged=exclude_unjudged
            )
            if result["exported"] == 0:
                print(f"  No preference pairs to export yet.")
                print(f"  Use /retry and corrections in chat to accumulate DPO data.")
            else:
                print(f"  ⚖️  Balanced export: {result['exported']}/{result['total']} pairs")
                print(f"     Max per source: {result.get('max_per_source', '?')}")
                for src, cnt in result.get("by_source", {}).items():
                    print(f"     {src}: {cnt}")
                if result.get("excluded_unjudged"):
                    print(f"     Excluded unjudged: {result['excluded_unjudged']}")
                print(f"  Output: {p}")
        else:
            p = str(Path(out_dir) / "dpo_training.jsonl")
            ep = str(Path(out_dir) / "dpo_eval.jsonl")
            count = archive.export_dpo(p, eval_path=ep)
            ev = sum(1 for _ in open(ep)) if Path(ep).exists() else 0
            if count == 0:
                print(f"  No preference pairs to export yet.")
                print(f"  Use /retry and corrections in chat to accumulate DPO data.")
            else:
                print(f"  Exported: {count} train + {ev} eval pairs")
                print(f"  Output:   {p}")
                print(f"\n  💡 For source-balanced export: nucleus archive dpo-export --balanced")

        print(f"\n  To train with DPO (after SFT):")
        print(f"    python scripts/train_third_brother.py --dpo {p}")
        print()
        return 0

    elif cmd == 'cot-status':
        cot_stats = archive.get_reasoning_stats()
        total_chains = cot_stats.get('total_chains', 0)
        print("=" * 50)
        print("🧠 REASONING CHAINS — Chain-of-Thought Training Data")
        print("=" * 50)
        print(f"  Total chains:     {total_chains}")
        print(f"  Total steps:      {cot_stats.get('total_steps', 0)}")
        print(f"  Avg steps/chain:  {cot_stats.get('avg_steps', 0)}")
        by_src = cot_stats.get('by_source', {})
        if by_src:
            print(f"  By source:")
            for src, count in sorted(by_src.items(), key=lambda x: -x[1]):
                label = {
                    "react_loop": "ReAct tool-use chains",
                    "dual_review": "Dual-agent review reasoning",
                    "decision": "Brain ledger decisions",
                    "manual": "Manual recording",
                }.get(src, src)
                print(f"    {src:12s}: {count:4d}  — {label}")
        if cot_stats.get('first'):
            print(f"  First chain:      {cot_stats['first'][:19]}")
            print(f"  Last chain:       {cot_stats['last'][:19]}")
        print()
        if total_chains < 20:
            print(f"  Chains accumulate automatically from multi-step tool use.")
            print(f"  Every ReAct loop with 2+ tool calls = 1 reasoning chain.")
        else:
            # Count quality chains
            quality = sum(1 for c in archive.get_reasoning_chains() if archive._is_quality_chain(c))
            print(f"  Quality chains:   {quality} (2+ steps, real reasoning)")
            if quality >= 20:
                print(f"  Ready for CoT training!")
                print(f"     → nucleus archive cot-export")
        print()
        return 0

    elif cmd == 'cot-export':
        out_dir = args.output or str(archive.training_dir / "exports")
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        p = str(Path(out_dir) / "reasoning_training.jsonl")
        ep = str(Path(out_dir) / "reasoning_eval.jsonl")
        count = archive.export_reasoning(p, eval_path=ep)
        ev = sum(1 for _ in open(ep)) if Path(ep).exists() else 0
        print("=" * 50)
        print("🧠 COT EXPORT — Reasoning Training Data")
        print("=" * 50)
        if count == 0:
            print(f"  No quality reasoning chains to export yet.")
            print(f"  Chains accumulate from multi-step tool use in chat.")
        else:
            print(f"  Exported: {count} train + {ev} eval chains")
            print(f"  Output:   {p}")
            print(f"  Format:   <think>step 1...step N</think> + final answer")
            print(f"\n  To train (mix with SFT data):")
            print(f"    Combine {p} with openai_training.jsonl")
            print(f"    Both use the same OpenAI chat format.")
        print()
        return 0

    elif cmd == 'mine':
        print("=" * 50)
        print("⛏️  MINING DPO + CoT FROM EXISTING ARCHIVE")
        print("=" * 50)

        # Mine DPO from corrections
        dpo_before = archive.count_preferences()
        print(f"\n  Mining DPO preference pairs from corrections...")
        dpo_mined = archive.mine_preferences_from_archive()
        dpo_after = archive.count_preferences()
        print(f"  ✅ Mined {dpo_mined} new DPO pairs (total: {dpo_after})")

        # Mine CoT from conversations
        cot_before = archive.count_reasoning_chains()
        print(f"\n  Mining CoT reasoning chains from conversations...")
        cot_mined = archive.mine_reasoning_from_archive()
        cot_after = archive.count_reasoning_chains()
        print(f"  ✅ Mined {cot_mined} new CoT chains (total: {cot_after})")

        print(f"\n  Summary:")
        print(f"    DPO:  {dpo_before} → {dpo_after} (+{dpo_mined})")
        print(f"    CoT:  {cot_before} → {cot_after} (+{cot_mined})")

        if dpo_mined + cot_mined == 0:
            print(f"\n  No new data to mine (already extracted or insufficient signal).")
        else:
            print(f"\n  Next steps:")
            if dpo_after >= 50:
                print(f"    nucleus archive dpo-export   — export for DPO training")
            cot_quality = sum(1 for c in archive.get_reasoning_chains() if archive._is_quality_chain(c))
            if cot_quality >= 20:
                print(f"    nucleus archive cot-export   — export for CoT training")
            print(f"    nucleus archive train        — SFT + mixed training")
        print()
        return 0

    elif cmd == 'eval':  # EVAL_BLOCK_START
        eval_count = getattr(args, 'count', 50)
        export_path = getattr(args, 'export', None)
        run_provider = getattr(args, 'run', None)
        judge_provider = getattr(args, 'judge', None)

        print("=" * 50)
        print("📏 EVAL BENCHMARK — Measure the Third Brother")
        print("=" * 50)

        suite = archive.generate_eval_suite(eval_count)
        if not suite:
            print(f"  Not enough data to generate eval suite (need 20+ quality pairs).")
            return 0

        # Category breakdown
        from collections import Counter
        cats = Counter(c["category"] for c in suite)
        diffs = Counter(c["difficulty"] for c in suite)
        print(f"  Generated {len(suite)} eval cases:")
        print(f"    Categories:  {dict(cats)}")
        print(f"    Difficulty:  {dict(diffs)}")

        if export_path:
            exported = archive.export_eval_suite(export_path, eval_count)
            print(f"\n  Exported {exported} cases to: {export_path}")

        if run_provider:
            scoring = "LLM-as-Judge" if judge_provider else "heuristic (word-overlap)"
            print(f"\n  Running eval against {run_provider} (scoring: {scoring})...")
            try:
                from .runtime.llm_client import get_llm_client
                llm = get_llm_client(run_provider)
                model_fn = lambda p: llm.generate_content(p).text

                # LLM-as-Judge for accurate scoring
                judge_fn = None
                if judge_provider:
                    judge_llm = get_llm_client(judge_provider)
                    judge_fn = lambda p: judge_llm.generate_content(p).text

                results = archive.run_eval(model_fn, eval_count, judge_fn=judge_fn)
                print(f"\n  {'='*40}")
                print(f"  EVAL RESULTS ({run_provider})")
                print(f"  {'='*40}")
                print(f"  Overall score:  {results['avg_score']}")
                print(f"  By category:")
                for cat, score in sorted(results.get('by_category', {}).items()):
                    print(f"    {cat:12s}: {score}")
                print(f"  By difficulty:")
                for diff, score in sorted(results.get('by_difficulty', {}).items()):
                    print(f"    {diff:12s}: {score}")

                # Save results
                eval_results_path = archive.training_dir / "eval_results.json"
                eval_results_path.write_text(json.dumps(results, indent=2))
                print(f"\n  Results saved: {eval_results_path}")
            except Exception as e:
                print(f"  ❌ Eval failed: {e}")

        if not export_path and not run_provider:
            # Default: export to standard location
            out = str(archive.training_dir / "exports" / "eval_suite.jsonl")
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            exported = archive.export_eval_suite(out, eval_count)
            print(f"\n  Exported {exported} cases to: {out}")
            print(f"\n  Usage:")
            print(f"    nucleus archive eval --run gemini    — benchmark against Gemini")
            print(f"    nucleus archive eval --run local     — benchmark the Third Brother")
            print(f"    Compare scores to measure training improvement.")
        print()
        return 0  # EVAL_BLOCK_END

    elif cmd == 'synthesize':  # SYNTH_BLOCK_START
        synth_provider = getattr(args, 'provider', 'gemini')
        synth_count = getattr(args, 'count', 100)
        judge_provider = getattr(args, 'judge', None)

        print("=" * 50)
        print("🧪 SELF-PLAY SYNTHESIS — Manufacturing DPO Pairs")
        print("=" * 50)
        print(f"  Provider:  {synth_provider}")
        print(f"  Judge:     {judge_provider or 'heuristic (quality comparison)'}")
        print(f"  Target:    {synth_count} pairs")
        if not judge_provider:
            print(f"\n  ⚠️  No --judge. Using quality heuristic (length/specificity).")
            print(f"     For accurate DPO pairs, add: --judge gemini")

        dpo_before = archive.count_preferences()

        try:
            from .runtime.llm_client import get_llm_client
            llm = get_llm_client(synth_provider)
            model_fn = lambda p: llm.generate_content(p).text

            # LLM-as-Judge if provider specified
            judge_fn = None
            if judge_provider:
                judge_llm = get_llm_client(judge_provider)
                judge_model_fn = lambda p: judge_llm.generate_content(p).text
                judge_fn = archive.build_judge_fn(judge_model_fn)
                print(f"  Using LLM-as-Judge ({judge_provider})")

            print(f"\n  Generating alternative responses...")
            synthesized = archive.synthesize_preferences(
                model_fn=model_fn,
                judge_fn=judge_fn,
                count=synth_count,
            )
            dpo_after = archive.count_preferences()

            print(f"\n  ✅ Synthesized {synthesized} new DPO pairs")
            print(f"     DPO total: {dpo_before} → {dpo_after}")

            if dpo_after >= 50:
                print(f"\n  Ready for DPO training!")
                print(f"    nucleus archive dpo-export")
        except Exception as e:
            print(f"\n  ❌ Synthesis failed: {e}")
            print(f"     Ensure {synth_provider.upper()}_API_KEY is set.")
        print()
        return 0  # SYNTH_BLOCK_END

    elif cmd == 'spin':  # SPIN_BLOCK_START
        current_provider = getattr(args, 'current', 'local')
        base_provider = getattr(args, 'base', 'gemini')
        judge_provider = getattr(args, 'judge', None)
        spin_count = getattr(args, 'count', 100)
        spin_round = getattr(args, 'round', 1)

        print("=" * 50)
        print("🔄 ITERATIVE SELF-PLAY (SPIN) — The Flywheel")
        print("=" * 50)
        print(f"  Current model:  {current_provider}")
        print(f"  Base model:     {base_provider}")
        print(f"  Judge:          {judge_provider or 'REQUIRED'}")
        print(f"  Round:          {spin_round}")
        print(f"  Target:         {spin_count} comparisons")

        if not judge_provider:
            print(f"\n  ❌ SPIN requires --judge <provider>.")
            print(f"     Without a judge, the trained model always 'wins' — even when")
            print(f"     it's wrong. This teaches the model that mistakes are correct.")
            print(f"\n     Fix: nucleus archive spin --current local --judge gemini")
            print()
            return 1

        dpo_before = archive.count_preferences()

        try:
            from .runtime.llm_client import get_llm_client
            current_llm = get_llm_client(current_provider)
            base_llm = get_llm_client(base_provider)
            current_fn = lambda p: current_llm.generate_content(p).text
            base_fn = lambda p: base_llm.generate_content(p).text

            judge_llm = get_llm_client(judge_provider)
            judge_model_fn = lambda p: judge_llm.generate_content(p).text
            judge_fn = archive.build_judge_fn(judge_model_fn)

            print(f"\n  Running SPIN round {spin_round}...")
            stats = archive.iterative_self_play(
                current_model_fn=current_fn,
                base_model_fn=base_fn,
                judge_fn=judge_fn,
                count=spin_count,
                round_num=spin_round,
            )

            dpo_after = archive.count_preferences()
            print(f"\n  ✅ SPIN Round {spin_round} Complete")
            print(f"     Generated:    {stats['generated']} DPO pairs")
            print(f"     Current wins: {stats['current_wins']}")
            print(f"     Base wins:    {stats['base_wins']}")
            print(f"     Ties:         {stats['ties']}")
            print(f"     DPO total:    {dpo_before} → {dpo_after}")

            if stats['current_wins'] > stats['base_wins']:
                print(f"\n  Current model is winning — training is working!")
            elif stats['base_wins'] > stats['current_wins']:
                print(f"\n  Base model still better — need more training data.")
            print(f"\n  Next: retrain with new DPO data, then run round {spin_round + 1}")
        except Exception as e:
            print(f"\n  ❌ SPIN failed: {e}")
        print()
        return 0  # SPIN_BLOCK_END

    elif cmd == 'active-learn':  # ACTIVE_LEARN_BLOCK_START
        al_provider = getattr(args, 'provider', 'gemini')
        eval_provider = getattr(args, 'eval_provider', None)
        al_count = getattr(args, 'count', 20)

        print("=" * 50)
        print("🎯 ACTIVE LEARNING — Target Weaknesses")
        print("=" * 50)

        try:
            from .runtime.llm_client import get_llm_client

            # Step 1: Get or run eval results
            eval_results_path = archive.training_dir / "eval_results.json"
            eval_results = None

            if eval_provider:
                print(f"\n  Running eval against {eval_provider} first...")
                eval_llm = get_llm_client(eval_provider)
                eval_fn = lambda p: eval_llm.generate_content(p).text
                eval_results = archive.run_eval(eval_fn, 50)
                eval_results_path.parent.mkdir(parents=True, exist_ok=True)
                eval_results_path.write_text(json.dumps(eval_results, indent=2))
                print(f"  Eval score: {eval_results['avg_score']}")
            elif eval_results_path.exists():
                eval_results = json.loads(eval_results_path.read_text())
                print(f"  Using cached eval results (score: {eval_results.get('avg_score', '?')})")
            else:
                print(f"  No eval results found. Run eval first:")
                print(f"    nucleus archive eval --run gemini")
                print(f"    nucleus archive active-learn --provider gemini")
                return 0

            # Step 2: Identify weaknesses
            weaknesses = archive.identify_weaknesses(eval_results)
            if not weaknesses:
                print(f"\n  No significant weaknesses found. Model is balanced.")
                return 0

            print(f"\n  Found {len(weaknesses)} weaknesses:")
            for w in weaknesses[:5]:
                print(f"    [{w['priority']:8s}] {w['name']:15s} score={w['score']} gap={w['gap']}")

            # Step 3: Generate targeted training data
            print(f"\n  Generating targeted training data ({al_count} per weakness)...")
            gen_llm = get_llm_client(al_provider)
            gen_fn = lambda p: gen_llm.generate_content(p).text

            turns_before = archive.get_stats().get('total_turns', 0)
            dpo_before = archive.count_preferences()

            al_stats = archive.synthesize_for_weaknesses(
                model_fn=gen_fn,
                eval_results=eval_results,
                count_per_weakness=al_count,
            )

            turns_after = archive.get_stats().get('total_turns', 0)
            dpo_after = archive.count_preferences()

            print(f"\n  ✅ Active Learning Complete")
            print(f"     Generated: {al_stats['total_generated']} targeted pairs")
            print(f"     SFT turns: {turns_before} → {turns_after}")
            print(f"     DPO pairs: {dpo_before} → {dpo_after}")
            for wb in al_stats.get('by_weakness', []):
                print(f"       {wb['name']:15s}: +{wb['generated']} pairs")

            print(f"\n  Re-export and retrain to close the gaps:")
            print(f"    nucleus archive export")
            print(f"    nucleus archive eval --run {eval_provider or 'local'}")
        except Exception as e:
            print(f"\n  ❌ Active learning failed: {e}")
        print()
        return 0  # ACTIVE_LEARN_BLOCK_END

    elif cmd == 'conductor':  # CONDUCTOR_BLOCK_START
        print("=" * 50)
        print("🎼 TRAINING CONDUCTOR — Pipeline Status")
        print("=" * 50)

        status = archive.training_status()

        # SFT
        sft = status["sft"]
        sft_icon = "✅" if sft["ready"] else "⏳"
        print(f"\n  {sft_icon} SFT:  {sft['turns']} turns {'(ready)' if sft['ready'] else '(need 50+)'}")

        # DPO
        dpo = status["dpo"]
        dpo_icon = "✅" if dpo["ready"] else "⏳"
        print(f"  {dpo_icon} DPO:  {dpo['total']} pairs {'(ready)' if dpo['ready'] else '(need 20+)'}")
        if dpo["by_source"]:
            for src, cnt in sorted(dpo["by_source"].items()):
                print(f"         {src:15s}: {cnt}")

        # CoT
        cot = status["cot"]
        cot_icon = "✅" if cot["ready"] else "⏳"
        print(f"  {cot_icon} CoT:  {cot['quality']} quality chains {'(ready)' if cot['ready'] else '(need 20+)'}")

        # Eval
        ev = status["eval"]
        if ev["has_baseline"]:
            print(f"  ✅ Eval: baseline score = {ev['baseline_score']}")
        else:
            print(f"  ⏳ Eval: no baseline yet")

        # Training history
        tr = status["training"]
        if tr["last_trained"]:
            print(f"\n  Last trained: {tr['last_trained'][:10]} ({tr['trained_at_turns']} turns)")
            print(f"  New since:    {tr['new_since_train']} turns")
        else:
            print(f"\n  Never trained.")

        # Next action
        na = status["next_action"]
        priority_icon = {"critical": "🔴", "high": "🟡", "medium": "🔵", "low": "⚪"}.get(na["priority"], "⚪")
        print(f"\n  {priority_icon} Next action: {na['action'].upper()}")
        print(f"     {na['reason']}")
        if na.get("command"):
            print(f"\n     $ {na['command']}")

        print()
        return 0  # CONDUCTOR_BLOCK_END

    elif cmd == 'pipeline':  # PIPELINE_BLOCK_START
        pipe_provider = getattr(args, 'provider', None)
        pipe_judge = getattr(args, 'judge', None)
        pipe_dry_run = getattr(args, 'dry_run', False)

        print("=" * 50)
        print("🚂 TRAINING PIPELINE — Full Autonomous Run")
        print("=" * 50)
        if pipe_dry_run:
            print("  [DRY RUN — no changes will be made]")
        print(f"  Synthesis: {pipe_provider or 'disabled'}")
        print(f"  Judge:     {pipe_judge or 'heuristic'}")

        model_fn = None
        judge_fn = None

        if pipe_provider:
            try:
                from .runtime.llm_client import get_llm_client
                llm = get_llm_client(pipe_provider)
                model_fn = lambda p: llm.generate_content(p).text
                if pipe_judge:
                    judge_llm = get_llm_client(pipe_judge)
                    judge_model_fn = lambda p: judge_llm.generate_content(p).text
                    judge_fn = archive.build_judge_fn(judge_model_fn)
            except Exception as e:
                print(f"\n  ❌ Failed to initialize LLM: {e}")
                return 1

        print(f"\n  Running pipeline...")
        report = archive.run_full_pipeline(
            model_fn=model_fn,
            judge_fn=judge_fn,
            dry_run=pipe_dry_run,
        )

        for step in report.get("steps", []):
            step_name = step.get("step", "?")
            if "status" in step:
                print(f"  [{step_name:12s}] {step['status']}")
            elif step_name == "mine":
                print(f"  [{step_name:12s}] +{step.get('mined_dpo', 0)} DPO, +{step.get('mined_cot', 0)} CoT")
            elif step_name == "synthesize":
                print(f"  [{step_name:12s}] +{step.get('new_pairs', 0)} DPO pairs")
            elif step_name == "export":
                sft_n = step.get('sft_exported', 0)
                dpo_n = step.get('dpo_exported', 0)
                cot_n = step.get('cot_chains', 0)
                eval_n = step.get('eval_cases', 0)
                print(f"  [{step_name:12s}] {sft_n} SFT, {dpo_n} DPO, {cot_n} CoT, {eval_n} eval")
                print(f"                 → {step.get('output_dir', '')}")
                if step.get('sft_eval_excluded'):
                    print(f"                 🛡️  {step['sft_eval_excluded']} eval prompts excluded (contamination firewall)")
                if step.get('sft_filtered_out'):
                    print(f"                 🔬 {step['sft_filtered_out']} low-quality pairs filtered")
                if step.get('sft_curriculum'):
                    print(f"                 📚 Curriculum: easy→hard")
                if step.get('dpo_by_source'):
                    sources = ", ".join(f"{k}={v}" for k, v in step['dpo_by_source'].items())
                    print(f"                 ⚖️  DPO balanced: {sources}")
                if step.get('sft_snapshot'):
                    print(f"                 📸 Snapshot: {step['sft_snapshot']}")

        na = report.get("next_action", {})
        if na:
            priority_icon = {"critical": "🔴", "high": "🟡", "medium": "🔵", "low": "⚪"}.get(na.get("priority", ""), "⚪")
            print(f"\n  {priority_icon} Next: {na.get('action', '').upper()} — {na.get('reason', '')}")
            if na.get("command"):
                print(f"     $ {na['command']}")

        print()
        return 0  # PIPELINE_BLOCK_END

    elif cmd == 'constitutional':  # CONSTITUTIONAL_BLOCK_START
        const_provider = getattr(args, 'provider', 'gemini')
        const_count = getattr(args, 'count', 100)

        print("=" * 50)
        print("📜 CONSTITUTIONAL AI — Self-Critique → Self-Revision")
        print("=" * 50)
        print(f"  Provider:    {const_provider}")
        print(f"  Target:      {const_count} turns")
        print(f"  Principles:  {len(archive.CONSTITUTION)}")
        for i, p in enumerate(archive.CONSTITUTION, 1):
            print(f"    {i}. {p}")

        dpo_before = archive.count_preferences()

        try:
            from .runtime.llm_client import get_llm_client
            llm = get_llm_client(const_provider)
            model_fn = lambda p: llm.generate_content(p).text

            print(f"\n  Running critique + revision loop...")
            created = archive.constitutional_revise(
                model_fn=model_fn,
                count=const_count,
            )
            dpo_after = archive.count_preferences()

            print(f"\n  ✅ Constitutional AI Complete")
            print(f"     Created: {created} DPO pairs (critique → revision)")
            print(f"     DPO total: {dpo_before} → {dpo_after}")

            if created == 0:
                print(f"\n  All reviewed responses passed — no revisions needed.")
        except Exception as e:
            print(f"\n  ❌ Constitutional revision failed: {e}")
        print()
        return 0  # CONSTITUTIONAL_BLOCK_END

    elif cmd == 'quality':  # QUALITY_BLOCK_START
        export_path = getattr(args, 'export', None)
        min_quality = getattr(args, 'min_quality', 0.4)
        export_format = getattr(args, 'format', 'openai')

        print("=" * 50)
        print("🔬 DATA QUALITY SCORING")
        print("=" * 50)

        quality = archive.score_training_data()
        if quality["total"] == 0:
            print("  No training data to score.")
            return 0

        print(f"\n  Total pairs:   {quality['total']}")
        print(f"  Avg quality:   {quality['avg_quality']}")
        print(f"  High (≥0.6):   {quality['high_quality']}")
        print(f"  Low (<0.3):    {quality['low_quality']}")

        dist = quality["quality_distribution"]
        print(f"\n  Distribution:")
        print(f"    Excellent (≥0.8): {dist['excellent']}")
        print(f"    Good (0.6-0.8):   {dist['good']}")
        print(f"    Fair (0.3-0.6):   {dist['fair']}")
        print(f"    Poor (<0.3):      {dist['poor']}")

        if quality.get("worst_5"):
            print(f"\n  Worst 5:")
            for w in quality["worst_5"]:
                print(f"    q={w['quality']} ulen={w.get('user_len', '?')} alen={w.get('assistant_len', '?')} | {w['prompt_preview'][:60]}")

        if export_path:
            curriculum = getattr(args, 'curriculum', False)
            print(f"\n  Exporting filtered data (min_quality={min_quality})...")
            if curriculum:
                print(f"  📚 Curriculum learning: sorting easy→hard")
            result = archive.export_filtered(
                export_path, min_quality, export_format, curriculum=curriculum
            )
            print(f"  ✅ Exported {result['exported']}/{result['total']} pairs")
            print(f"     Filtered out: {result['filtered_out']} low-quality")
            if result.get('eval_excluded', 0) > 0:
                print(f"     🛡️  Eval excluded: {result['eval_excluded']} (contamination firewall)")
            if result.get('snapshot'):
                print(f"     📸 Snapshot: {result['snapshot']}")
            print(f"     Output: {export_path}")
        else:
            print(f"\n  To export filtered data:")
            print(f"    nucleus archive quality --export training_filtered.jsonl --min-quality 0.5")

        print()
        return 0  # QUALITY_BLOCK_END

    elif cmd == 'register':  # REGISTRY_BLOCK_START
        version = getattr(args, 'version', 'v1')
        base_model = getattr(args, 'base', 'llama3.2:3b')

        entry = archive.register_model(version=version, base_model=base_model)
        print(f"✅ Registered model {version}")
        print(f"   Base: {base_model}")
        print(f"   SFT turns: {entry['data']['sft_turns']}")
        print(f"   DPO pairs: {entry['data']['dpo_pairs']}")
        print(f"   CoT chains: {entry['data']['cot_chains']}")
        print(f"   Status: {entry['status']}")
        print(f"\n   Next: nucleus archive promote {version} --to shadow")
        return 0

    elif cmd == 'registry':
        registry = archive.get_registry()
        if not registry:
            print("No models registered. Train first, then:")
            print("  nucleus archive register v1 --base llama3.2:3b")
            return 0

        print("=" * 60)
        print("📋 MODEL REGISTRY")
        print("=" * 60)
        for entry in registry:
            status_icon = {
                "registered": "⬜", "shadow": "👻", "canary": "🐤",
                "primary": "🟢", "retired": "⬛",
            }.get(entry.get("status", ""), "?")
            v = entry.get("version", "?")
            base = entry.get("base_model", "?")
            s = entry.get("status", "?")
            data = entry.get("data", {})
            scores = entry.get("eval_scores", {})
            score_str = f" score={scores.get('avg_score', '?')}" if scores else ""
            print(f"  {status_icon} {v:8s} | {base:20s} | {s:12s} | "
                  f"sft={data.get('sft_turns', 0)} dpo={data.get('dpo_pairs', 0)}{score_str}")
        return 0

    elif cmd == 'promote':
        version = getattr(args, 'version', '')
        target = getattr(args, 'to', '')
        if archive.update_model_status(version, target):
            print(f"✅ {version} → {target}")
            if target == "shadow":
                print(f"   Shadow mode active. Third Brother will generate alongside primary.")
                print(f"   DPO pairs created automatically from comparisons.")
            elif target == "canary":
                print(f"   Canary mode active. Logging comparisons for graduation check.")
            elif target == "primary":
                print(f"   🎓 GRADUATED. Third Brother is now the primary model.")
        else:
            print(f"❌ Version {version} not found in registry.")
        return 0  # REGISTRY_BLOCK_END

    elif cmd == 'shadow-stats':  # SHADOW_BLOCK_START
        stats = archive.get_shadow_stats()
        if stats["total"] == 0:
            print("No shadow comparisons yet.")
            print("Shadow mode generates Third Brother responses alongside the primary LLM.")
            print("Enable: nucleus archive promote <version> --to shadow")
            return 0

        print("=" * 50)
        print("👻 SHADOW MODE — Third Brother vs Primary")
        print("=" * 50)
        print(f"  Total comparisons: {stats['total']}")
        print(f"  Shadow wins:       {stats['shadow_wins']}")
        print(f"  Primary wins:      {stats['primary_wins']}")
        print(f"  Shadow win rate:   {stats['win_rate']:.1%}")

        if stats['win_rate'] >= 0.5:
            print(f"\n  Third Brother is winning! Consider promotion:")
            print(f"    nucleus archive graduation")
        elif stats['win_rate'] >= 0.3:
            print(f"\n  Third Brother is competitive. Keep accumulating.")
        else:
            print(f"\n  Third Brother needs more training. Check:")
            print(f"    nucleus archive conductor")
        return 0  # SHADOW_BLOCK_END

    elif cmd == 'graduation':  # GRADUATION_BLOCK_START
        grad = archive.graduation_check()

        print("=" * 50)
        print("🎓 GRADUATION PROTOCOL — Promotion Check")
        print("=" * 50)
        print(f"  Current status: {grad['current_status']}")

        stats = grad.get("shadow_stats", {})
        if stats.get("total", 0) > 0:
            print(f"  Shadow comparisons: {stats['total']}")
            print(f"  Win rate: {stats.get('win_rate', 0):.1%}")

        # Regression gate
        regression = grad.get("regression", {})
        if regression.get("regressed"):
            print(f"\n  🚨 REGRESSION DETECTED")
            print(f"     {regression['details']}")
            if regression.get("category_regressions"):
                for cr in regression["category_regressions"]:
                    print(f"     - {cr}")
        elif regression.get("category_regressions"):
            print(f"\n  ⚠️  Category regressions (overall OK):")
            for cr in regression["category_regressions"]:
                print(f"     - {cr}")

        rec = grad["recommendation"]
        reason = grad["reason"]
        rec_icon = {
            "start_shadow": "👻", "promote_canary": "🐤",
            "promote_primary": "🟢", "retrain": "🔄",
            "hold": "⏳", "monitor": "✅",
            "blocked_regression": "🚨",
        }.get(rec, "❓")

        print(f"\n  {rec_icon} Recommendation: {rec.upper()}")
        print(f"     {reason}")

        if rec == "promote_canary":
            active = archive.get_active_model()
            if active:
                print(f"\n     $ nucleus archive promote {active['version']} --to canary")
        elif rec == "promote_primary":
            active = archive.get_active_model()
            if active:
                print(f"\n     $ nucleus archive promote {active['version']} --to primary")
        elif rec == "retrain":
            print(f"\n     $ nucleus archive conductor")
        return 0  # GRADUATION_BLOCK_END

    # VAULT_BLOCK_START
    elif cmd == 'vault':
        vault_versions = archive.vault_list()
        vault_path = archive.get_vault_path()
        ssd_mounted = archive.DEFAULT_VAULT_PATH.parent.exists()

        print("=" * 50)
        print("🏦 MODEL VAULT — Versioned Artifact Storage")
        print("=" * 50)
        print(f"  Location: {vault_path}")
        print(f"  Storage:  {'SSD (Samsung 990 PRO 2TB)' if ssd_mounted else 'LOCAL (⚠️ SSD not mounted)'}")

        if not ssd_mounted:
            print(f"\n  ⚠️  SSD not connected. Models stored on SSD won't appear.")
            print(f"     Plug in Samsung SSD to see all versions.")

        if not vault_versions:
            print(f"\n  No models in vault{' (locally)' if not ssd_mounted else ''}.")
            print(f"  Train with --register to auto-vault:")
            print(f"    python scripts/train_third_brother.py --register --auto-shadow")
        else:
            print(f"\n  Versions: {len(vault_versions)}")
            for v in vault_versions:
                arts = len(v.get("artifacts", []))
                size = v.get("total_size_bytes", 0)
                size_str = f"{size // 1024 // 1024}MB" if size else "?"
                stored = v.get("stored_at", "?")[:10]
                loc = v.get("_location", "?")
                loc_icon = "💾" if loc == "ssd" else "💻"
                print(f"    {loc_icon} {v.get('version', '?'):8s}  {arts} artifacts  {size_str:>8s}  {stored}")
        print()
        return 0

    elif cmd == 'vault-restore':
        version = args.version
        print(f"  Restoring {version} from vault...")
        result = archive.vault_restore(version)
        if "error" in result:
            print(f"  ❌ {result['error']}")
            return 1
        print(f"  ✅ Restored to: {result['restored_to']}")
        for a in result.get("artifacts", []):
            print(f"     - {a}")
        print(f"\n  Deploy: {result.get('ollama_command', '')}")
        return 0

    elif cmd == 'rollback':
        version = args.version
        print("=" * 50)
        print(f"⏪ ROLLBACK — Restoring {version}")
        print("=" * 50)
        result = archive.rollback_model(version)
        if "error" in result:
            print(f"  ❌ {result['error']}")
            return 1
        print(f"  From: {result.get('from_version', 'none')}")
        print(f"  To:   {result['to_version']} (status: {result.get('new_status', '?')})")
        print(f"\n  {result.get('instructions', '')}")
        return 0
    # VAULT_BLOCK_END

    else:
        # bare `nucleus archive` — show stats + retrain indicator + DPO + CoT
        stats = archive.get_stats()
        total = stats.get('total_turns', 0)
        retrain = archive.should_retrain()
        retrain_flag = " | RETRAIN READY" if retrain['should_retrain'] else ""
        dpo_count = archive.count_preferences()
        dpo_flag = f" | {dpo_count} DPO" if dpo_count > 0 else ""
        cot_count = archive.count_reasoning_chains()
        cot_flag = f" | {cot_count} CoT" if cot_count > 0 else ""
        print(f"📊 Archive: {total} turns{retrain_flag}{dpo_flag}{cot_flag}")
        print(f"   nucleus archive status      — training readiness")
        print(f"   nucleus archive stats       — full stats breakdown")
        print(f"   nucleus archive recent      — see last 10 turns")
        print(f"   nucleus archive export      — export SFT training data")
        print(f"   nucleus archive dpo-status  — DPO preference pairs")
        print(f"   nucleus archive dpo-export  — export DPO data")
        print(f"   nucleus archive cot-status  — reasoning chain stats")
        print(f"   nucleus archive cot-export  — export <think> data")
        print(f"   nucleus archive eval        — generate eval benchmark")
        print(f"   nucleus archive synthesize  — self-play DPO manufacturing")
        print(f"   nucleus archive spin        — iterative self-play (SPIN)")
        print(f"   nucleus archive active-learn — target model weaknesses")
        print(f"   nucleus archive constitutional — self-critique DPO pairs")
        print(f"   nucleus archive quality     — score data quality")
        print(f"   nucleus archive conductor   — what should I do next?")
        print(f"   nucleus archive pipeline    — run full loop automatically")
        print(f"   nucleus archive registry    — model version history")
        print(f"   nucleus archive graduation  — promotion check")
        print(f"   nucleus archive train       — fine-tuning pipeline")
        print(f"   nucleus archive ingest      — bulk import conversations")
        return 0


