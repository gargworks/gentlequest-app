"""Baseline-fairness 14-pin assertion harness (plan §4.1 lines 153-170).

Asserts preconditions at session start. Violation fails the run and logs
the violated pin. Non-blocking measurement hygiene (sub-agent streams,
cache-transition turn, session-restoration counter) is reported via
HygieneMeta → meta fields on the per-turn record, not asserted here.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


@dataclass
class RunConfig:
    prompt_caching_enabled: bool
    compression_enabled: bool
    claudemd_path: Path
    claudemd_ref_hash: str
    tool_set_hash: str
    tool_set_ref_hash: str
    mcp_deferred_config: dict
    mcp_deferred_config_ref: dict
    mcp_state_snapshot_hash: str
    mcp_state_ref_hash: str
    cli_version: str
    cli_version_ref: str
    cli_build_hash: str
    parallelism_pattern: str
    thinking_budget_tokens: int
    tool_result_cache_policy: str
    non_claudemd_injection_sources: list[str]
    streaming_flag: bool
    retry_policy: str
    workload_trace_hash: str | None = None
    workload_trace_ref: str | None = None


@dataclass
class PinResult:
    pin_id: int
    pin_name: str
    status: str  # "pass" | "fail" | "report_only"
    message: str = ""


@dataclass
class AssertionReport:
    all_pass: bool
    results: list[PinResult]
    violations: list[PinResult] = field(default_factory=list)


class FairnessViolation(RuntimeError):
    """Raised when a load-bearing pin fails — aborts the session."""


def _pass(pin_id: int, name: str, message: str = "") -> PinResult:
    return PinResult(pin_id, name, "pass", message)


def _fail(pin_id: int, name: str, message: str) -> PinResult:
    return PinResult(pin_id, name, "fail", message)


def _report(pin_id: int, name: str, message: str) -> PinResult:
    return PinResult(pin_id, name, "report_only", message)


def pin_01_prompt_caching(cfg: RunConfig) -> PinResult:
    if cfg.prompt_caching_enabled:
        return _pass(1, "prompt_caching_on")
    return _fail(1, "prompt_caching_on", "prompt caching disabled — 90% discount missing")


def pin_02_compression(cfg: RunConfig) -> PinResult:
    return _report(2, "compression_on", f"compression_enabled={cfg.compression_enabled}")


def pin_03_claudemd_density(cfg: RunConfig) -> PinResult:
    if not cfg.claudemd_path.exists():
        return _fail(3, "claudemd_density", f"CLAUDE.md missing at {cfg.claudemd_path}")
    actual = hashlib.sha256(cfg.claudemd_path.read_bytes()).hexdigest()
    if actual == cfg.claudemd_ref_hash:
        return _pass(3, "claudemd_density", f"hash={actual[:8]}")
    return _fail(3, "claudemd_density", f"hash {actual[:8]} != ref {cfg.claudemd_ref_hash[:8]}")


def pin_04_tool_set(cfg: RunConfig) -> PinResult:
    if cfg.tool_set_hash == cfg.tool_set_ref_hash:
        return _pass(4, "tool_set_parity", f"hash={cfg.tool_set_hash[:8]}")
    return _fail(4, "tool_set_parity",
                 f"hash {cfg.tool_set_hash[:8]} != ref {cfg.tool_set_ref_hash[:8]}")


def pin_05_mcp_deferred(cfg: RunConfig) -> PinResult:
    if cfg.mcp_deferred_config == cfg.mcp_deferred_config_ref:
        return _pass(5, "mcp_deferred_config_parity")
    return _fail(5, "mcp_deferred_config_parity", "deferred-loading config drift")


def pin_06_mcp_state(cfg: RunConfig) -> PinResult:
    if cfg.mcp_state_snapshot_hash == cfg.mcp_state_ref_hash:
        return _pass(6, "mcp_state_snapshot_parity", f"hash={cfg.mcp_state_snapshot_hash[:8]}")
    return _fail(6, "mcp_state_snapshot_parity",
                 f"snapshot {cfg.mcp_state_snapshot_hash[:8]} != ref {cfg.mcp_state_ref_hash[:8]}")


def pin_07_cli_version(cfg: RunConfig) -> PinResult:
    if cfg.cli_version == cfg.cli_version_ref:
        return _pass(7, "cli_version_pin", f"version={cfg.cli_version}")
    return _fail(7, "cli_version_pin",
                 f"version {cfg.cli_version} != ref {cfg.cli_version_ref}")


def pin_08_workload_trace(cfg: RunConfig) -> PinResult:
    if cfg.workload_trace_hash is None:
        return _report(8, "workload_trace_byte_identical", "live session (non-replay)")
    if cfg.workload_trace_hash == cfg.workload_trace_ref:
        return _pass(8, "workload_trace_byte_identical")
    return _fail(8, "workload_trace_byte_identical", "replay trace hash mismatch")


def pin_09_parallelism(cfg: RunConfig) -> PinResult:
    valid = {"identical_as_baseline", "serialized_adapter_override", "parallel_adapter_override"}
    if cfg.parallelism_pattern not in valid:
        return _fail(9, "parallelism_pattern", f"unknown pattern {cfg.parallelism_pattern}")
    return _pass(9, "parallelism_pattern", cfg.parallelism_pattern)


def pin_10_thinking_budget(cfg: RunConfig) -> PinResult:
    if cfg.thinking_budget_tokens < 0:
        return _fail(10, "thinking_budget_tokens", f"negative budget {cfg.thinking_budget_tokens}")
    return _pass(10, "thinking_budget_tokens", f"budget={cfg.thinking_budget_tokens}")


def pin_11_tool_result_cache(cfg: RunConfig) -> PinResult:
    valid = {"default", "disabled", "engram_pointer_bypass"}
    if cfg.tool_result_cache_policy not in valid:
        return _fail(11, "tool_result_cache_policy", f"unknown policy {cfg.tool_result_cache_policy}")
    return _pass(11, "tool_result_cache_policy", cfg.tool_result_cache_policy)


def pin_12_injection_sources(cfg: RunConfig) -> PinResult:
    valid = {"skills_nudges", "output_styles", "settings_json", "hook_outputs",
             "user_prompt_submit_hook", "post_tool_use_hook", "other"}
    unknown = [s for s in cfg.non_claudemd_injection_sources if s not in valid]
    if unknown:
        return _fail(12, "non_claudemd_injection_sources", f"unknown sources: {unknown}")
    return _pass(12, "non_claudemd_injection_sources",
                 f"sources={cfg.non_claudemd_injection_sources}")


def pin_13_streaming(cfg: RunConfig) -> PinResult:
    if not isinstance(cfg.streaming_flag, bool):
        return _fail(13, "streaming_flag", f"non-bool streaming_flag={cfg.streaming_flag!r}")
    return _pass(13, "streaming_flag", f"streaming={cfg.streaming_flag}")


def pin_14_retry_policy(cfg: RunConfig) -> PinResult:
    valid = {"default", "no_retry"}
    if cfg.retry_policy not in valid:
        return _fail(14, "retry_policy", f"unknown policy {cfg.retry_policy}")
    return _pass(14, "retry_policy", cfg.retry_policy)


_PINS: list[Callable[[RunConfig], PinResult]] = [
    pin_01_prompt_caching, pin_02_compression, pin_03_claudemd_density,
    pin_04_tool_set, pin_05_mcp_deferred, pin_06_mcp_state,
    pin_07_cli_version, pin_08_workload_trace, pin_09_parallelism,
    pin_10_thinking_budget, pin_11_tool_result_cache,
    pin_12_injection_sources, pin_13_streaming, pin_14_retry_policy,
]


def assert_fairness(cfg: RunConfig, abort_on_fail: bool = True) -> AssertionReport:
    results = [pin(cfg) for pin in _PINS]
    violations = [r for r in results if r.status == "fail"]
    report = AssertionReport(
        all_pass=not violations,
        results=results,
        violations=violations,
    )
    if violations and abort_on_fail:
        msg = "; ".join(f"pin {v.pin_id} ({v.pin_name}): {v.message}" for v in violations)
        raise FairnessViolation(f"fairness pins failed: {msg}")
    return report


@dataclass
class HygieneMeta:
    """Non-blocking measurement hygiene reported as meta fields per turn."""
    parent_session_id: str | None = None
    cache_transition_turn: bool = False
    turn_counter_source: str = "wall_clock_harness"

    def to_meta_dict(self) -> dict:
        return {
            "parent_session_id": self.parent_session_id,
            "cache_transition_turn": self.cache_transition_turn,
            "turn_counter_source": self.turn_counter_source,
        }
