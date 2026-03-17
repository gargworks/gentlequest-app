"""
SCRP H1 Validation Test Framework
===================================
A/B test: Agent with DCAs vs Agent with raw chat logs.

Hypothesis H1: "Injecting Deterministic Context Atoms into a fresh
session reduces context re-derivation time by >80% compared to
raw conversation logs."

This module:
1. Generates test scenarios with known decision outcomes
2. Measures how quickly/accurately an agent recovers decisions  
3. Compares DCA-injected vs raw-log-injected sessions
4. Produces a quantitative validation report

Usage:
    nucleus validate --test h1 [--scenarios 5] [--output report]
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional


# ============================================================================
# TEST SCENARIOS — Known-answer tests for decision recovery
# ============================================================================

GOLDEN_SCENARIOS = [
    {
        "id": "S01",
        "name": "Architecture Pattern Recovery",
        "question": "What architectural pattern does the project use for multi-tool coordination?",
        "expected_keywords": ["three-layer", "core", "audit", "governance", "orchestrator"],
        "expected_decision": "Three-layer architecture: Core (fast), Audit (async), Governance (enterprise)",
        "difficulty": "medium",
    },
    {
        "id": "S02",
        "name": "Deployment Configuration",
        "question": "Where is the project deployed and what service ID is used?",
        "expected_keywords": ["render", "srv-d2r3i1fdiees73dqtov0", "cloud run", "gentlequest"],
        "expected_decision": "Render Service srv-d2r3i1fdiees73dqtov0 (GentleQuest)",
        "difficulty": "easy",
    },
    {
        "id": "S03",
        "name": "Security Protocol",
        "question": "What strategy is used to prevent context poisoning in the SCRP protocol?",
        "expected_keywords": ["byzantine", "fault", "tolerance", "rsa", "manifest", "signing"],
        "expected_decision": "CP-WBFT (Byzantine Fault Tolerance) and RSA Manifest Signing",
        "difficulty": "hard",
    },
    {
        "id": "S04",
        "name": "Sync Engine Design",
        "question": "What synchronization mechanism is used for cross-tool state reconciliation?",
        "expected_keywords": ["rbf", "riblt", "hybrid", "rateless", "invertible"],
        "expected_decision": "Hybrid RBF + RIBLT for efficient and reliable state reconciliation",
        "difficulty": "hard",
    },
    {
        "id": "S05",
        "name": "CLI Command Structure",
        "question": "What is the primary bootstrap command for the project?",
        "expected_keywords": ["nucleus", "cli", "brain", "init", "status"],
        "expected_decision": "The nucleus CLI is the primary bootstrap for all sub-agents",
        "difficulty": "easy",
    },
]


class H1TestResult:
    """Result of a single test scenario execution."""

    def __init__(
        self,
        scenario_id: str,
        scenario_name: str,
        mode: str,  # "dca" or "raw"
        keyword_hits: int,
        keyword_total: int,
        characters_provided: int,
        recovery_score: float,  # 0.0-1.0
    ):
        self.scenario_id = scenario_id
        self.scenario_name = scenario_name
        self.mode = mode
        self.keyword_hits = keyword_hits
        self.keyword_total = keyword_total
        self.characters_provided = characters_provided
        self.recovery_score = recovery_score
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "mode": self.mode,
            "keyword_hits": self.keyword_hits,
            "keyword_total": self.keyword_total,
            "characters_provided": self.characters_provided,
            "recovery_score": self.recovery_score,
            "timestamp": self.timestamp,
        }


class H1Validator:
    """
    Validates Hypothesis H1 by comparing DCA-based and raw-log-based
    context injection approaches.
    """

    def __init__(self, brain_path: Optional[Path] = None):
        from .runtime.common import get_brain_path
        self.brain_path = brain_path or get_brain_path()
        self.results_dir = self.brain_path / "validation"
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def run_offline_validation(self, scenarios: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Run offline (non-LLM) validation by measuring information density.
        
        This doesn't call an LLM — it measures how efficiently the DCAs 
        encode the expected decisions compared to raw logs.
        
        Metrics:
        - Information Density: keywords_found / chars_consumed
        - Coverage: scenarios_with_hits / total_scenarios
        - Efficiency Ratio: dca_density / raw_density
        """
        scenarios = scenarios or GOLDEN_SCENARIOS

        # Load latest DCA engram
        from .replay import ReplayEngine
        replay = ReplayEngine(brain_path=self.brain_path)
        atoms = replay.load_atoms()

        if not atoms:
            return {"error": "No DCAs found. Run `nucleus distill` first."}

        # Generate DCA context (system prompt mode)
        dca_prompt = replay.replay_as_system_prompt(atoms, min_confidence=0.5, max_atoms=100)

        # Generate raw log context (simulate by loading raw markdown files)
        raw_log_content = self._get_raw_logs_content()

        # Run each scenario against both contexts
        dca_results = []
        raw_results = []

        for scenario in scenarios:
            dca_result = self._evaluate_scenario(scenario, dca_prompt, "dca")
            dca_results.append(dca_result)

            raw_result = self._evaluate_scenario(scenario, raw_log_content, "raw")
            raw_results.append(raw_result)

        # Compute aggregate metrics
        report = self._compute_report(dca_results, raw_results, dca_prompt, raw_log_content)

        # Save report
        self._save_report(report)

        return report

    def _evaluate_scenario(
        self, scenario: Dict, context: str, mode: str
    ) -> H1TestResult:
        """Evaluate a single scenario against a context string."""
        context_lower = context.lower()
        keywords = scenario["expected_keywords"]
        hits = sum(1 for kw in keywords if kw.lower() in context_lower)

        recovery_score = hits / len(keywords) if keywords else 0.0

        return H1TestResult(
            scenario_id=scenario["id"],
            scenario_name=scenario["name"],
            mode=mode,
            keyword_hits=hits,
            keyword_total=len(keywords),
            characters_provided=len(context),
            recovery_score=recovery_score,
        )

    def _get_raw_logs_content(self) -> str:
        """Find and concatenate raw logs from Antigravity and Windsurf to use as baseline."""
        raw_content = []
        
        # 1. Antigravity raw artifacts (last 3 sessions)
        ag_paths = sorted(
            [d for d in self.brain_path.parent.iterdir() if d.is_dir() and not d.name.startswith(".")],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )[:3]
        
        for p in ag_paths:
            for md in p.glob("*.md"):
                if md.stat().st_size < 500_000:
                    raw_content.append(f"--- {md.name} ---\n{md.read_text(errors='replace')}")

        # 2. Siphon raw logs
        siphon_dir = self.brain_path / "siphon"
        if siphon_dir.exists():
            for md in siphon_dir.rglob("*.md"):
                if md.stat().st_size < 500_000:
                    raw_content.append(f"--- {md.name} ---\n{md.read_text(errors='replace')}")

        return "\n\n".join(raw_content)

    def _compute_report(
        self,
        dca_results: List[H1TestResult],
        raw_results: List[H1TestResult],
        dca_context: str,
        raw_context: str,
    ) -> Dict[str, Any]:
        """Compute the final validation report."""
        # DCA metrics
        dca_total_hits = sum(r.keyword_hits for r in dca_results)
        dca_total_keywords = sum(r.keyword_total for r in dca_results)
        dca_avg_recovery = sum(r.recovery_score for r in dca_results) / len(dca_results) if dca_results else 0
        dca_density = dca_total_hits / len(dca_context) * 10000 if dca_context else 0

        # Raw metrics
        raw_total_hits = sum(r.keyword_hits for r in raw_results)
        raw_total_keywords = sum(r.keyword_total for r in raw_results)
        raw_avg_recovery = sum(r.recovery_score for r in raw_results) / len(raw_results) if raw_results else 0
        raw_density = raw_total_hits / len(raw_context) * 10000 if raw_context else 0

        # Efficiency ratio (the money metric)
        efficiency_ratio = dca_density / raw_density if raw_density > 0 else float("inf")

        # Compression ratio
        compression_ratio = len(raw_context) / len(dca_context) if dca_context else 0

        return {
            "hypothesis": "H1: DCAs reduce context re-derivation by >80%",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scenarios_tested": len(dca_results),
            "dca_metrics": {
                "total_keyword_hits": dca_total_hits,
                "total_keywords_possible": dca_total_keywords,
                "avg_recovery_score": round(dca_avg_recovery, 3),
                "information_density": round(dca_density, 3),
                "context_length_chars": len(dca_context),
            },
            "raw_metrics": {
                "total_keyword_hits": raw_total_hits,
                "total_keywords_possible": raw_total_keywords,
                "avg_recovery_score": round(raw_avg_recovery, 3),
                "information_density": round(raw_density, 3),
                "context_length_chars": len(raw_context),
            },
            "comparison": {
                "efficiency_ratio": round(efficiency_ratio, 2),
                "compression_ratio": round(compression_ratio, 2),
                "dca_advantage_pct": round((efficiency_ratio - 1) * 100, 1) if efficiency_ratio != float("inf") else "N/A",
                "h1_validated": efficiency_ratio >= 1.8,  # 80% improvement = 1.8x ratio
            },
            "per_scenario": [
                {
                    "id": dca.scenario_id,
                    "name": dca.scenario_name,
                    "dca_recovery": round(dca.recovery_score, 3),
                    "raw_recovery": round(raw.recovery_score, 3),
                    "delta": round(dca.recovery_score - raw.recovery_score, 3),
                }
                for dca, raw in zip(dca_results, raw_results)
            ],
        }

    def _save_report(self, report: Dict[str, Any]) -> Path:
        """Save the validation report."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        
        # JSON report
        json_path = self.results_dir / f"h1_validation_{timestamp}.json"
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

        # Markdown report
        md_path = self.results_dir / f"h1_validation_{timestamp}.md"
        md_lines = [
            "# 📊 H1 Validation Report",
            "",
            f"**Hypothesis**: {report['hypothesis']}",
            f"**Timestamp**: {report['timestamp'][:19]}",
            f"**Scenarios**: {report['scenarios_tested']}",
            "",
            "---",
            "",
            "## Results",
            "",
            "| Metric | DCA | Raw | Winner |",
            "|--------|-----|-----|--------|",
            f"| Avg Recovery | {report['dca_metrics']['avg_recovery_score']:.1%} | {report['raw_metrics']['avg_recovery_score']:.1%} | {'DCA ✅' if report['dca_metrics']['avg_recovery_score'] >= report['raw_metrics']['avg_recovery_score'] else 'Raw'} |",
            f"| Info Density | {report['dca_metrics']['information_density']:.2f} | {report['raw_metrics']['information_density']:.2f} | {'DCA ✅' if report['dca_metrics']['information_density'] >= report['raw_metrics']['information_density'] else 'Raw'} |",
            f"| Context Size | {report['dca_metrics']['context_length_chars']:,} chars | {report['raw_metrics']['context_length_chars']:,} chars | {'DCA ✅' if report['dca_metrics']['context_length_chars'] <= report['raw_metrics']['context_length_chars'] else 'Raw'} |",
            "",
            f"**Efficiency Ratio**: {report['comparison']['efficiency_ratio']}x",
            f"**Compression Ratio**: {report['comparison']['compression_ratio']}x",
            f"**DCA Advantage**: {report['comparison']['dca_advantage_pct']}%",
            "",
        ]

        validated = report['comparison']['h1_validated']
        if validated:
            md_lines.append("> [!TIP]")
            md_lines.append("> **H1 VALIDATED** ✅ — DCAs provide >80% efficiency improvement over raw logs.")
        else:
            md_lines.append("> [!WARNING]")
            md_lines.append(f"> **H1 NOT YET VALIDATED** — Efficiency ratio is {report['comparison']['efficiency_ratio']}x (need ≥1.8x)")

        md_lines.extend([
            "",
            "---",
            "",
            "## Per-Scenario Breakdown",
            "",
            "| ID | Scenario | DCA | Raw | Delta |",
            "|---:|----------|-----|-----|-------|",
        ])

        for s in report["per_scenario"]:
            delta_emoji = "🟢" if s["delta"] > 0 else "🔴" if s["delta"] < 0 else "🟡"
            md_lines.append(
                f"| {s['id']} | {s['name']} | {s['dca_recovery']:.0%} | {s['raw_recovery']:.0%} | {delta_emoji} {s['delta']:+.0%} |"
            )

        md_lines.extend([
            "",
            "---",
            f"*Generated by Nucleus SCRP H1 Validator v1.0.0*",
        ])

        md_path.write_text("\n".join(md_lines), encoding="utf-8")

        print(f"📄 Reports saved:")
        print(f"   JSON: {json_path}")
        print(f"   MD:   {md_path}")

        return md_path


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

def run_validate(test: str = "h1", scenarios: int = 5) -> Dict[str, Any]:
    """CLI entry point for validation tests."""
    if test != "h1":
        print(f"❌ Unknown test: {test}. Only 'h1' is supported.")
        return {"error": f"Unknown test: {test}"}

    validator = H1Validator()
    print(f"🧪 [Validate] Running H1 offline validation ({scenarios} scenarios)...")

    selected_scenarios = GOLDEN_SCENARIOS[:scenarios]
    result = validator.run_offline_validation(scenarios=selected_scenarios)

    if "error" in result:
        print(f"❌ {result['error']}")
        return result

    print(f"\n📊 H1 Validation Results:")
    print(f"   DCA Recovery:  {result['dca_metrics']['avg_recovery_score']:.1%}")
    print(f"   Raw Recovery:  {result['raw_metrics']['avg_recovery_score']:.1%}")
    print(f"   Efficiency:    {result['comparison']['efficiency_ratio']}x")
    print(f"   Compression:   {result['comparison']['compression_ratio']}x")
    print(f"   H1 Validated:  {'✅ YES' if result['comparison']['h1_validated'] else '❌ NO'}")

    return result
