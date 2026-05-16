"""Measurement proxy for compounding-multiplier wedge §4.1 harness.

PR-1 chassis: reverse-proxy (ANTHROPIC_BASE_URL target) that forwards requests
to api.anthropic.com and emits one per-turn record to .brain/measurement/turns.jsonl
per round-trip. Schema-validated against
https://nucleusos.dev/schemas/measurement/per_turn_record.v1.json.

PR-1 populates aggregate response-side counters only; per_stream_attribution is
reported as fallback_aggregate until PR-2 (request-side cache_control parser)
wires real per-stream decomposition.
"""

from .fairness_pins import (
    AssertionReport,
    FairnessViolation,
    HygieneMeta,
    PinResult,
    RunConfig,
    assert_fairness,
)
from .writer import PerTurnWriter, SchemaValidationError

__all__ = [
    "AssertionReport",
    "FairnessViolation",
    "HygieneMeta",
    "PerTurnWriter",
    "PinResult",
    "RunConfig",
    "SchemaValidationError",
    "assert_fairness",
]
