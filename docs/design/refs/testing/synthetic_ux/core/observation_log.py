"""
observation_log.py — JSONL observation persistence.

Append-safe: each UC observation is written atomically as one JSON line.
A run interrupted at UC 18/35 still has 17 complete observations on disk.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Literal, Optional


@dataclass
class JudgeResult:
    verdict: Literal["PASS", "FAIL", "UNCERTAIN", "WALK_FAIL", "JUDGE_ERROR"]
    confidence: int            # 0-100
    reason: str
    raw_response: str
    issues: list[str] = field(default_factory=list)
    model: str = "claude-sonnet-4-6"
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class MindResult:
    first_reaction: str
    emotional_state: str
    expected: str
    actual: str
    gap: str
    unspoken_frustration: str
    unspoken_delight: str
    continue_or_abandon: Literal["continue", "abandon", "hesitate"]
    abandon_risk_score: int    # 0-100
    heuristic_violated: str
    design_verdict: Literal["BLOCKER", "HIGH", "MEDIUM", "LOW", "DELIGHT"]
    refinement_suggestion: str
    raw_response: str = ""
    model: str = "claude-sonnet-4-6"
    input_tokens: int = 0
    output_tokens: int = 0

    @classmethod
    def parse_error(cls) -> "MindResult":
        return cls(
            first_reaction="parse_error",
            emotional_state="parse_error",
            expected="", actual="", gap="",
            unspoken_frustration="", unspoken_delight="",
            continue_or_abandon="hesitate",
            abandon_risk_score=0,
            heuristic_violated="",
            design_verdict="MEDIUM",
            refinement_suggestion="",
        )


@dataclass
class Observation:
    run_id: str
    product: str
    uc_id: str
    uc_title: str
    flow_position: str
    screenshots: dict                    # {"before": path, "after": path}
    layer2_judge: Optional[JudgeResult]
    layer3_user_mind: Optional[MindResult]
    timestamp_iso: str
    schema_version: str = "1.0"


def append_observation(log_path: Path, obs: Observation) -> None:
    """Append one observation as a JSON line. Creates file if absent."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = asdict(obs)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def load_observations(log_path: Path) -> list[Observation]:
    """Load all observations from a JSONL file."""
    if not log_path.exists():
        return []
    observations = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        data = json.loads(line)
        # Reconstruct nested dataclasses
        j2 = data.get("layer2_judge")
        j3 = data.get("layer3_user_mind")
        obs = Observation(
            run_id=data["run_id"],
            product=data["product"],
            uc_id=data["uc_id"],
            uc_title=data.get("uc_title", data["uc_id"]),
            flow_position=data["flow_position"],
            screenshots=data.get("screenshots", {}),
            layer2_judge=JudgeResult(**j2) if j2 else None,
            layer3_user_mind=MindResult(**j3) if j3 else None,
            timestamp_iso=data["timestamp_iso"],
            schema_version=data.get("schema_version", "1.0"),
        )
        observations.append(obs)
    return observations
