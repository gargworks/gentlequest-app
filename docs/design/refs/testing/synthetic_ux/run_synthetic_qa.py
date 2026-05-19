#!/usr/bin/env python3
"""
run_synthetic_qa.py — CLI entry point for the Synthetic QA Framework.

Usage:
  python3 run_synthetic_qa.py --product gentlequest [options]

Options:
  --uc-ids UC-I2,UC-M1   Comma-separated UC IDs to run (default: all)
  --layer 2,3,4          Which layers to run (default: 2,3,4)
                           Layer 1 = walk + pixel oracle (no LLM required)
                           Layer 2 = LLM behavioral judge
                           Layer 3 = Maya synthetic user mind
                           Layer 4 = prioritized backlog generator
                           Zero-API mode: --layer 1,4  (or omit --layer; oracle
                           auto-activates when no API key is present)
  --dry-run              Walk only; skip all LLM + oracle calls
  --no-walk              Skip simulator walk; use --walk-dir for screenshots
  --walk-dir PATH        Directory with before/after PNG pairs for --no-walk
  --out-dir PATH         Output directory for reports (default: reports/)

Exit codes: 0=no BLOCKERs, 1=BLOCKERs present, 2=walk infrastructure failure
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))

from core.observation_log import (
    JudgeResult, MindResult, Observation, append_observation
)
from core.backlog import generate_backlog


# ── Shared adapter utilities ──────────────────────────────────────────────────

_BRIGHTNESS_PROBES = [
    (0.20, 0.15), (0.50, 0.15), (0.80, 0.15),
    (0.20, 0.35), (0.50, 0.35), (0.80, 0.35),
    (0.20, 0.55), (0.50, 0.55), (0.80, 0.55),
    (0.20, 0.75), (0.50, 0.75), (0.80, 0.75),
]

_ANSI_RE = re.compile(r'\x1b(?:\[[0-9;]*[a-zA-Z]|\][^\x07\x1b]*(?:\x07|\x1b\\))')


class _LLMContent:
    def __init__(self, text: str):
        self.text = text


class _LLMUsage:
    input_tokens: int = 0
    output_tokens: int = 0


class _LLMResponse:
    def __init__(self, text: str):
        self.content = [_LLMContent(text)]
        self.usage = _LLMUsage()


def _extract_images_and_text(
    messages: list | None, system: str | list | None
) -> tuple[list[str], str]:
    """Pull base64 image data and text from an Anthropic-style messages list.

    system may be a plain string or a list of Anthropic content blocks
    (as user_mind.py passes it for cache_control). Both are normalised to str.
    """
    images_b64: list[str] = []
    text = ""
    for msg in (messages or []):
        for block in msg.get("content", []):
            if isinstance(block, dict):
                if block.get("type") == "image":
                    images_b64.append(block["source"]["data"])
                elif block.get("type") == "text":
                    text = block["text"]
    if system:
        if isinstance(system, list):
            # Extract text from Anthropic content-block list (ignores cache_control)
            system_text = "\n".join(
                b.get("text", "") for b in system
                if isinstance(b, dict) and b.get("type") == "text"
            )
        else:
            system_text = system
        text = f"{system_text}\n\n{text}"
    return images_b64, text


def _b64_to_tempfiles(images_b64: list[str]) -> list[str]:
    """Decode base64 PNG strings to temp files. Returns list of paths to clean up."""
    paths = []
    for b64 in images_b64:
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.write(base64.standard_b64decode(b64))
        tmp.close()
        paths.append(tmp.name)
    return paths


def _cleanup_tempfiles(paths: list[str]) -> None:
    for p in paths:
        try:
            os.unlink(p)
        except OSError:
            pass


# ── Provider factory ──────────────────────────────────────────────────────────

def _get_anthropic_client():
    """Return anthropic.Anthropic client or None if key not available."""
    key = (
        os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("NUCLEUS_ANTHROPIC_API_KEY")
    )
    if not key:
        return None
    try:
        import anthropic
        return anthropic.Anthropic(api_key=key)
    except ImportError:
        return None


def _get_gemini_client():
    """Return DualEngineLLM or None if key not available."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return None
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent
                            / "mcp-server-nucleus/src"))
        from mcp_server_nucleus.runtime.llm_client import DualEngineLLM
        return DualEngineLLM(api_key=key)
    except (ImportError, Exception):
        return None


# ── Walk executor ─────────────────────────────────────────────────────────────

def _md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest() if path.exists() else ""


def _idb_tap(udid: str, x: int, y: int) -> bool:
    r = subprocess.run(
        ["idb", "ui", "tap", str(x), str(y), "--udid", udid],
        capture_output=True, timeout=10,
    )
    return r.returncode == 0


def _idb_type(udid: str, text: str) -> bool:
    r = subprocess.run(
        ["idb", "ui", "text", text, "--udid", udid],
        capture_output=True, timeout=10,
    )
    return r.returncode == 0


def _idb_screenshot(udid: str, out_path: Path) -> bool:
    r = subprocess.run(
        ["idb", "screenshot", str(out_path), "--udid", udid],
        capture_output=True, timeout=15,
    )
    return r.returncode == 0 and out_path.exists()


def _bypass_compliance(udid: str, bundle: str) -> None:
    """Set SharedPreferences keys to skip Welcome + ComplianceGuard screens."""
    script = (
        "import Foundation; "
        "let d = UserDefaults.standard; "
        "d.set(true, forKey: \"flutter.age_verified\"); "
        "d.set(true, forKey: \"flutter.has_seen_welcome_v1\"); "
        "d.synchronize()"
    )
    subprocess.run(
        ["idb", "ui", "exec", "--udid", udid, script],
        capture_output=True, timeout=10,
    )


def _launch_app(udid: str, bundle: str) -> None:
    subprocess.run(
        ["xcrun", "simctl", "launch", udid, bundle],
        capture_output=True, timeout=20,
    )
    time.sleep(1.5)


def _terminate_app(udid: str, bundle: str) -> None:
    try:
        subprocess.run(
            ["xcrun", "simctl", "terminate", udid, bundle],
            capture_output=True, timeout=6,
        )
    except subprocess.TimeoutExpired:
        pass  # App may not be running; safe to continue


def execute_walk(
    uc: dict,
    config: dict,
    out_dir: Path,
    dry_run: bool = False,
) -> tuple[Path | None, Path | None, bool]:
    """
    Execute the walk_steps for a UC and return (before_path, after_path, ok).
    Returns (None, None, False) on infrastructure failure.
    """
    udid = config["walk_config"]["udid"]
    bundle = config["walk_config"]["bundle"]
    uc_id = uc["id"]

    before_path = out_dir / f"{uc_id}_before.png"
    after_path = out_dir / f"{uc_id}_after.png"

    if dry_run:
        # In dry-run, just create placeholder files
        before_path.write_bytes(b"DRY_RUN_PLACEHOLDER")
        after_path.write_bytes(b"DRY_RUN_PLACEHOLDER")
        return before_path, after_path, True

    try:
        # Terminate + relaunch for clean state
        _terminate_app(udid, bundle)
        if uc.get("bypass_compliance"):
            _bypass_compliance(udid, bundle)
        _launch_app(udid, bundle)

        for step in uc.get("walk_steps", []):
            action = step["action"]
            if action == "screenshot":
                name = step.get("screen_name", "unknown")
                dest = before_path if name == "before" else after_path
                md5_before = _md5(dest)
                if not _idb_screenshot(udid, dest):
                    return None, None, False
                if _md5(dest) == md5_before and dest.exists() and md5_before:
                    print(f"    ⚠ [{uc_id}] screenshot no-op detected for '{name}'")
            elif action == "tap":
                x, y = step["x"], step["y"]
                hash_before = _md5(before_path) if before_path.exists() else ""
                _idb_tap(udid, x, y)
                time.sleep(0.1)
                if hash_before and before_path.exists() and _md5(before_path) == hash_before:
                    pass  # tap no-op — noted but continue
            elif action == "type":
                _idb_type(udid, step["text"])
            elif action == "wait":
                time.sleep(step.get("duration_ms", 500) / 1000)

        if not before_path.exists() or not after_path.exists():
            return None, None, False
        return before_path, after_path, True

    except Exception as e:
        print(f"    ✗ [{uc_id}] walk error: {e}", file=sys.stderr)
        return None, None, False


# ── Gemini adapter (duck-types anthropic.Anthropic for judge/user_mind) ───────

class _GeminiAdapter:
    """Wraps DualEngineLLM.generate_vision() to match the anthropic client interface."""

    def __init__(self, gemini_client):
        self._client = gemini_client
        self.messages = self

    def create(self, model=None, max_tokens=400, messages=None, system=None, **kwargs):
        images_b64, text = _extract_images_and_text(messages, system)
        tmp_paths = _b64_to_tempfiles(images_b64)
        try:
            result = self._client.generate_vision(
                image_paths=tmp_paths,
                text_prompt=text,
                max_tokens=max_tokens,
            )
            return _LLMResponse(getattr(result, "text", str(result)))
        finally:
            _cleanup_tempfiles(tmp_paths)


# ── Claude CLI adapter (Max-plan fallback, no API key needed) ─────────────────

class _ClaudeCliAdapter:
    """
    Calls `claude -p --allowedTools Read` via subprocess using the Max plan
    OAuth session. No separate API key required. Decodes base64 images to
    temp files so the Claude CLI Read tool can access them.
    """

    def __init__(self):
        self.messages = self

    def create(self, model=None, max_tokens=400, messages=None, system=None, **kwargs):
        images_b64, text = _extract_images_and_text(messages, system)
        tmp_paths = _b64_to_tempfiles(images_b64)
        read_lines = [f"Read {p} — this is Image {i+1}" for i, p in enumerate(tmp_paths)]
        full_prompt = ("\n".join(read_lines) + "\n\n" + text) if read_lines else text

        try:
            r = subprocess.run(
                ["claude", "-p", "--allowedTools", "Read",
                 "--output-format", "text", full_prompt],
                capture_output=True, text=True, timeout=120,
            )
            # _ANSI_RE strips terminal-title hook escape sequences from stdout
            response_text = _ANSI_RE.sub("", r.stdout).strip()
        finally:
            _cleanup_tempfiles(tmp_paths)

        return _LLMResponse(response_text)


def _get_claude_cli_client():
    """Return _ClaudeCliAdapter if `claude` CLI is available and authenticated."""
    import shutil
    if not shutil.which("claude"):
        return None
    r = subprocess.run(
        ["claude", "-p", "--output-format", "text", "Say: ok"],
        capture_output=True, text=True, timeout=30,
    )
    if r.returncode != 0:
        return None
    out = (r.stdout + r.stderr).lower()
    if "not logged in" in out or "login" in out:
        return None
    return _ClaudeCliAdapter()


# ── Layer 1: Pixel oracle (zero-API fallback) ─────────────────────────────────

def _oracle_check(png_path: Path) -> tuple[bool, str]:
    """
    Pixel-level sanity check for iOS simulator screenshots.

    Strategy: file size is the primary signal.
    - ≥ 80 KB → real screenshot (PNG compression doesn't shrink real UI below this)
    - < 30 KB → blank capture (a white 390×844 @2x PNG packs to ~2–5 KB)
    - 30–79 KB → ambiguous; fall through to brightness check

    Brightness check catches black-screen crashes only — we skip the color-
    diversity check because light-themed apps (lavender/white bg) naturally
    produce uniform color samples with just 12 probe points.
    """
    if not png_path.exists():
        return False, "screenshot file not found"

    size_kb = png_path.stat().st_size // 1024

    if size_kb >= 80:
        # Large enough to be a real screenshot — skip pixel checks
        return True, f"screen alive (size={size_kb} KB)"

    if size_kb < 30:
        return False, f"file too small ({size_kb} KB) — likely blank capture"

    # Ambiguous size range: probe for black screen (crash indicator)
    try:
        from PIL import Image
    except ImportError:
        return True, f"PIL not installed — size-range check passed (size={size_kb} KB)"

    img = Image.open(png_path).convert("RGB")
    w, h = img.size
    brightnesses = []
    for fx, fy in _BRIGHTNESS_PROBES:
        r, g, b = img.getpixel((int(w * fx), int(h * fy)))
        brightnesses.append((r * 299 + g * 587 + b * 114) // 1000)

    if max(brightnesses) < 15:
        return False, f"screen too dark (max_br={max(brightnesses)}) — black screen"
    return True, f"screen alive (size={size_kb} KB)"


_ORACLE_ABANDON_RISK = {"BLOCKER": 85, "HIGH": 65, "MEDIUM": 45, "LOW": 25, "DELIGHT": 5}


def _synthetic_results_from_oracle(
    before_ok: bool, before_reason: str,
    after_ok: bool, after_reason: str,
    uc: dict,
) -> tuple[JudgeResult, MindResult]:
    """
    Derive Layer 2 + 3 results from pixel oracle without any LLM call.
    Oracle FAIL → UC's severity_floor verdict.  Oracle PASS → LOW (structural only).
    """
    severity_floor = uc.get("severity_floor", "MEDIUM")

    if not after_ok:
        judge = JudgeResult(
            verdict="FAIL", confidence=80,
            reason=f"After-state pixel check failed: {after_reason}",
            raw_response="", issues=[after_reason], model="pixel-oracle-layer1",
        )
        mind = MindResult(
            first_reaction=f"Something went wrong — {after_reason}",
            emotional_state="anxious, confused",
            expected=uc.get("after_state", {}).get("description", ""),
            actual=after_reason,
            gap="Screen appears broken or blank",
            unspoken_frustration="This isn't working. I don't know why.",
            unspoken_delight="",
            continue_or_abandon="abandon" if severity_floor in ("BLOCKER", "HIGH") else "hesitate",
            abandon_risk_score=_ORACLE_ABANDON_RISK.get(severity_floor, 45),
            heuristic_violated="H1 — Visibility of system status",
            design_verdict=severity_floor,
            refinement_suggestion="Fix rendering — after-state appears blank or broken",
            raw_response="", model="pixel-oracle-layer1",
        )
    elif not before_ok:
        judge = JudgeResult(
            verdict="UNCERTAIN", confidence=40,
            reason=f"Before-state oracle warning: {before_reason}",
            raw_response="", issues=[before_reason], model="pixel-oracle-layer1",
        )
        mind = MindResult(
            first_reaction="Before state looked off, hard to judge what changed",
            emotional_state="uncertain",
            expected="", actual=before_reason, gap="Starting state unclear",
            unspoken_frustration="I wasn't sure what I was looking at",
            unspoken_delight="",
            continue_or_abandon="hesitate",
            abandon_risk_score=35,
            heuristic_violated="H1 — Visibility of system status",
            design_verdict="MEDIUM",
            refinement_suggestion="Verify before-state renders correctly",
            raw_response="", model="pixel-oracle-layer1",
        )
    else:
        judge = JudgeResult(
            verdict="PASS", confidence=50,
            reason=f"Pixel oracle passed: {after_reason}",
            raw_response="", issues=[], model="pixel-oracle-layer1",
        )
        mind = MindResult(
            first_reaction="Seems to have worked — screen looks normal",
            emotional_state="neutral, calm",
            expected=uc.get("after_state", {}).get("description", ""),
            actual=after_reason,
            gap="",
            unspoken_frustration="",
            unspoken_delight="Screen rendered without obvious errors",
            continue_or_abandon="continue",
            abandon_risk_score=10,
            heuristic_violated="none",
            design_verdict="LOW",
            refinement_suggestion="",
            raw_response="", model="pixel-oracle-layer1",
        )
    return judge, mind


# ── Layer runners ─────────────────────────────────────────────────────────────

def run_layer2(client, before_path: Path, after_path: Path, uc: dict, product_name: str) -> JudgeResult:
    from core.judge import judge_uc
    return judge_uc(client, before_path, after_path, uc, product_name)


def run_layer3(client, after_path: Path, uc: dict, judge_result: JudgeResult) -> MindResult:
    from core.user_mind import simulate_mind
    return simulate_mind(client, after_path, uc, judge_result)


# ── Main orchestration ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Synthetic QA Framework — AI-driven behavioral + UX testing"
    )
    parser.add_argument("--product", required=True, help="Product ID (e.g. gentlequest)")
    parser.add_argument("--uc-ids", help="Comma-separated UC IDs to run (default: all)")
    parser.add_argument("--layer", default="2,3,4", help="Layers to run (default: 2,3,4)")
    parser.add_argument("--dry-run", action="store_true", help="Walk only; skip LLM calls")
    parser.add_argument("--no-walk", action="store_true", help="Skip simulator walk; use --walk-dir")
    parser.add_argument("--walk-dir", help="Directory with before/after PNGs for --no-walk")
    parser.add_argument("--out-dir", help="Output directory for reports")
    args = parser.parse_args()

    layers = {int(x.strip()) for x in args.layer.split(",") if x.strip().isdigit()}

    # ── Load product config ────────────────────────────────────
    product_dir = _HERE / "products" / args.product
    config_path = product_dir / "config.json"
    uc_spec_path = product_dir / "uc_spec.json"

    if not config_path.exists():
        print(f"✗ Product config not found: {config_path}", file=sys.stderr)
        sys.exit(2)
    config = json.loads(config_path.read_text())
    product_name = config.get("product_name", args.product)

    if not uc_spec_path.exists():
        print(f"✗ UC spec not found: {uc_spec_path}", file=sys.stderr)
        sys.exit(2)
    all_ucs = json.loads(uc_spec_path.read_text())

    # ── Filter UCs ─────────────────────────────────────────────
    if args.uc_ids:
        requested = {x.strip() for x in args.uc_ids.split(",")}
        ucs = [u for u in all_ucs if u["id"] in requested]
        if not ucs:
            print(f"✗ No UCs matched: {args.uc_ids}", file=sys.stderr)
            sys.exit(2)
    else:
        ucs = all_ucs

    # ── Provider auto-detection ────────────────────────────────
    llm_client = None
    if not args.dry_run and (2 in layers or 3 in layers):
        llm_client = _get_anthropic_client()
        if llm_client is None:
            gemini = _get_gemini_client()
            if gemini is not None:
                llm_client = _GeminiAdapter(gemini)
                print("ℹ Using Gemini Vision (ANTHROPIC_API_KEY not set)", file=sys.stderr)
            else:
                cli = _get_claude_cli_client()
                if cli is not None:
                    llm_client = cli
                    print("ℹ Using claude CLI (Max plan) for LLM calls", file=sys.stderr)
                else:
                    print(
                        "⚠ No API key or claude CLI available. "
                        "Oracle fallback will run (pixel-only, no AI judgment).",
                        file=sys.stderr,
                    )

    # ── Output directories ────────────────────────────────────
    run_id = f"{args.product}-{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M-%S')}"
    out_base = Path(args.out_dir) if args.out_dir else _HERE / "reports" / run_id
    out_base.mkdir(parents=True, exist_ok=True)
    screenshots_dir = out_base / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)

    walk_dir = Path(args.walk_dir) if args.walk_dir else screenshots_dir

    # ── JSONL log ──────────────────────────────────────────────
    jsonl_path = out_base / "observations.jsonl"

    # ── Per-UC loop ────────────────────────────────────────────
    all_observations = []
    walk_failed = False

    for uc in ucs:
        uc_id = uc["id"]

        # ── Walk (Layer 1) ──────────────────────────────────
        if args.no_walk:
            before_path = walk_dir / f"{uc_id}_before.png"
            after_path = walk_dir / f"{uc_id}_after.png"
            walk_ok = before_path.exists() and after_path.exists()
            if not walk_ok:
                print(f"  [{uc_id}] walk=SKIP (--no-walk; screenshots not found)")
                judge_result = JudgeResult(
                    verdict="WALK_FAIL", confidence=0,
                    reason="Screenshots not found for --no-walk mode",
                    raw_response="", issues=[], model="",
                )
                walk_failed = True
                obs = Observation(
                    run_id=run_id, product=args.product,
                    uc_id=uc_id, uc_title=uc.get("title", uc_id),
                    flow_position=uc.get("flow_position", "core"),
                    screenshots={},
                    layer2_judge=judge_result, layer3_user_mind=None,
                    timestamp_iso=datetime.now(timezone.utc).isoformat(),
                )
                append_observation(jsonl_path, obs)
                all_observations.append(obs)
                continue
        else:
            before_path, after_path, walk_ok = execute_walk(
                uc, config, screenshots_dir, dry_run=args.dry_run
            )
            if not walk_ok:
                print(f"  [{uc_id}] walk=FAIL ✗")
                judge_result = JudgeResult(
                    verdict="WALK_FAIL", confidence=0,
                    reason="Walk executor failed",
                    raw_response="", issues=[], model="",
                )
                walk_failed = True
                obs = Observation(
                    run_id=run_id, product=args.product,
                    uc_id=uc_id, uc_title=uc.get("title", uc_id),
                    flow_position=uc.get("flow_position", "core"),
                    screenshots={},
                    layer2_judge=judge_result, layer3_user_mind=None,
                    timestamp_iso=datetime.now(timezone.utc).isoformat(),
                )
                append_observation(jsonl_path, obs)
                all_observations.append(obs)
                continue

        screenshots = {
            "before": str(before_path),
            "after": str(after_path),
        }

        # ── Layer 2: Behavioral Judge (or pixel oracle fallback) ────────────
        judge_result = None
        mind_result = None
        if 2 in layers and not args.dry_run and llm_client:
            judge_result = run_layer2(llm_client, before_path, after_path, uc, product_name)
        elif not args.dry_run and (1 in layers or llm_client is None):
            # Pixel oracle: explicit --layer 1,... OR no API key available
            before_ok, before_reason = _oracle_check(before_path)
            after_ok, after_reason = _oracle_check(after_path)
            judge_result, mind_result = _synthetic_results_from_oracle(
                before_ok, before_reason, after_ok, after_reason, uc
            )
        else:
            judge_result = JudgeResult(
                verdict="UNCERTAIN", confidence=0,
                reason="Layer 2 skipped",
                raw_response="", model="",
            )

        # ── Layer 3: Synthetic User Mind ────────────────────
        if mind_result is None and 3 in layers and not args.dry_run and llm_client:
            mind_result = run_layer3(llm_client, after_path, uc, judge_result)

        # ── Status line ─────────────────────────────────────
        is_oracle = getattr(judge_result, "model", "") == "pixel-oracle-layer1"
        mode = "oracle" if is_oracle else "llm"
        judge_str = f"judge={judge_result.verdict}({mode}) conf={judge_result.confidence}"
        mind_str = ""
        if mind_result:
            src = "oracle" if is_oracle else "maya"
            mind_str = f" {src}={mind_result.design_verdict} risk={mind_result.abandon_risk_score}"
        print(f"  [{uc_id}] {judge_str}{mind_str}")

        # ── Append observation ───────────────────────────────
        obs = Observation(
            run_id=run_id, product=args.product,
            uc_id=uc_id, uc_title=uc.get("title", uc_id),
            flow_position=uc.get("flow_position", "core"),
            screenshots=screenshots,
            layer2_judge=judge_result,
            layer3_user_mind=mind_result,
            timestamp_iso=datetime.now(timezone.utc).isoformat(),
        )
        append_observation(jsonl_path, obs)
        all_observations.append(obs)

    # ── Layer 4: Backlog ───────────────────────────────────────
    if 4 in layers and all_observations and not args.dry_run:
        backlog_path, summary_path = generate_backlog(
            all_observations, out_base, product_name, run_id
        )
        summary = json.loads(summary_path.read_text())
        print(f"\n{'─'*60}")
        print(f"Run: {run_id}")
        print(f"UCs: {len(all_observations)} | BLOCKER:{summary['verdict_counts']['BLOCKER']} "
              f"HIGH:{summary['verdict_counts']['HIGH']} "
              f"MEDIUM:{summary['verdict_counts']['MEDIUM']} "
              f"LOW:{summary['verdict_counts']['LOW']} "
              f"DELIGHT:{summary['verdict_counts']['DELIGHT']}")
        if summary["pattern_alerts"]:
            for alert in summary["pattern_alerts"]:
                print(f"  {alert}")
        print(f"BACKLOG: {backlog_path}")
        print(f"JSONL:   {jsonl_path}")
        if summary["has_blockers"]:
            print("Exit 1 — BLOCKERs present")
            sys.exit(1)
    elif args.dry_run:
        print(f"\nDry run complete. Screenshots in: {screenshots_dir}")
        print(f"UCs walked: {len(all_observations)}")

    if walk_failed:
        print("Exit 2 — walk infrastructure failures", file=sys.stderr)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
