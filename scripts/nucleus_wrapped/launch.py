"""Nucleus-wrapped claude launcher — scaffold per phase2_experiment_design.md §2.1.

This is a SCAFFOLD, not an implementation. Each step function has the §2.x
anchor it serves + a NotImplementedError stub. The scaffold freezes the shape
of the launcher so §3 (fairness-diff) and §4 (paired-run harness) have a
stable contract to reference.

Do not wire real execution into these stubs until §2 is founder-locked and
§3/§4 drafts have ratified the integration points.

Spec anchors: .brain/plans/phase2_experiment_design.md §§2.1-2.6.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import os
import pathlib
import queue
import signal
import socket
import subprocess
import sys
import threading
import time
import uuid
from typing import Any


SPEC = "phase2_experiment_design.md"


@dataclasses.dataclass
class LaunchArgs:
    condition: str
    workload_recording: pathlib.Path
    replay_worktree: pathlib.Path
    surface: str
    out: pathlib.Path
    fairness_config: pathlib.Path | None
    run_id: str


@dataclasses.dataclass
class Manifest:
    run_id: str
    path: pathlib.Path

    def write(self, step: str, payload: dict[str, Any]) -> None:
        record = {
            "run_id": self.run_id,
            "step": step,
            "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
            **payload,
        }
        with self.path.open("a") as fh:
            fh.write(json.dumps(record) + "\n")


def parse_args(argv: list[str] | None = None) -> LaunchArgs:
    p = argparse.ArgumentParser(prog="nucleus_wrapped.launch")
    p.add_argument("--condition", choices=["experimental", "baseline"], required=True)
    p.add_argument("--workload-recording", type=pathlib.Path, required=True)
    p.add_argument("--replay-worktree", type=pathlib.Path, required=True)
    p.add_argument("--surface", default="cc_peer")
    p.add_argument("--out", type=pathlib.Path, required=True)
    p.add_argument("--fairness-config", type=pathlib.Path, default=None)
    p.add_argument("--run-id", default=None)
    ns = p.parse_args(argv)
    run_id = ns.run_id or f"run_{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    return LaunchArgs(
        condition=ns.condition,
        workload_recording=ns.workload_recording,
        replay_worktree=ns.replay_worktree,
        surface=ns.surface,
        out=ns.out,
        fairness_config=ns.fairness_config,
        run_id=run_id,
    )


def _sha256_hex(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _run_git(args: list[str], *, cwd: pathlib.Path | None = None) -> subprocess.CompletedProcess:
    """Thin git wrapper. Raises CalledProcessError on non-zero exit so the launcher
    fails loud per §2.5 — silent worktree corruption is the worst failure mode."""
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd is not None else None,
        capture_output=True,
        text=True,
        check=True,
    )


def step_1_worktree_freeze(args: LaunchArgs, m: Manifest) -> None:
    """§2.1 step 1 + §2.5 row 'Filesystem mutations'.

    Inputs: recording.manifest.json {git_sha, uncommitted_patch}.
    Action: create worktree at args.replay_worktree, checkout git_sha, apply patch,
            chdir into it. All subsequent steps operate on frozen tree.
    Output: manifest row {step: worktree_freeze, git_sha, patch_hash, worktree_path}.

    Fails loud on:
      - missing recording.manifest.json sibling
      - git_sha not reachable from current repo (recording references unknown SHA)
      - replay_worktree path already exists (refuses to reuse — could be stale state)
      - git apply failure on uncommitted_patch (recording's patch doesn't apply
        cleanly to git_sha — recording is defective per §2.5 'recording must
        cover all tool-calls' principle extended to filesystem state)

    Deferred (call out in manifest, don't block):
      - mtime reset to recording-time (§2.5 row 1 fine print; needs recording
        to capture mtime snapshot, not yet in manifest contract)
    """
    recording_manifest_path = _resolve_recording_manifest(args.workload_recording)
    if not recording_manifest_path.exists():
        raise FileNotFoundError(
            f"§2.1 step 1: recording manifest not found at {recording_manifest_path} "
            f"(sibling of {args.workload_recording}); §2.5 contract requires it"
        )
    recording_manifest = json.loads(recording_manifest_path.read_text())
    git_sha = str(recording_manifest["git_sha"])
    uncommitted_patch = str(recording_manifest.get("uncommitted_patch", "") or "")

    if args.replay_worktree.exists():
        raise FileExistsError(
            f"§2.1 step 1: replay worktree path {args.replay_worktree} already exists; "
            f"refusing to reuse (could be stale state from aborted prior run)"
        )

    try:
        _run_git(["rev-parse", "--verify", f"{git_sha}^{{commit}}"])
    except subprocess.CalledProcessError as exc:
        raise ValueError(
            f"§2.1 step 1: recording git_sha {git_sha} not reachable from current repo: "
            f"{exc.stderr.strip()}"
        ) from exc

    args.replay_worktree.parent.mkdir(parents=True, exist_ok=True)
    _run_git(["worktree", "add", "--detach", str(args.replay_worktree), git_sha])

    patch_applied = False
    if uncommitted_patch.strip():
        patch_path = args.replay_worktree / ".nucleus_wrapped_recording.patch"
        patch_path.write_text(uncommitted_patch)
        try:
            _run_git(["apply", str(patch_path)], cwd=args.replay_worktree)
            patch_applied = True
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(
                f"§2.1 step 1: recording's uncommitted_patch failed to apply on top of "
                f"{git_sha} — recording defective: {exc.stderr.strip()}"
            ) from exc

    os.chdir(args.replay_worktree)

    m.write(
        "worktree_freeze",
        {
            "git_sha": git_sha,
            "patch_hash": _sha256_hex(uncommitted_patch),
            "patch_applied": patch_applied,
            "patch_size_bytes": len(uncommitted_patch.encode("utf-8")),
            "worktree_path": str(args.replay_worktree),
            "recording_manifest_path": str(recording_manifest_path),
            "mtime_reset_deferred": True,
        },
    )


def step_2_proxy_spawn(args: LaunchArgs, m: Manifest) -> int:
    """§2.1 step 2 + §2.4 (baseline skips rewriter install in step 3).

    Action: spawn scripts/measurement_proxy/proxy.py on an ephemeral loopback port
            with --condition {args.condition} --surface {args.surface}
            --fairness-config {args.fairness_config} --out {args.out}.
    Blocks until proxy logs 'listening on ...' on stderr.
    Returns port.

    Fails loud on:
      - fairness_config absent (proxy refuses to start; --skip-fairness would
        invalidate baseline-comparison validity per §2.6 fairness gate)
      - proxy exits before logging 'listening on' within 30s (captures stderr tail)
      - proxy never logs 'listening on' within 30s (captures stderr tail)

    Thread-based stderr drainage avoids blocking readline when the proxy is
    still starting. PID stored in manifest so step_8 can SIGTERM by PID without
    in-memory plumbing across step boundaries.
    """
    if args.fairness_config is None:
        raise ValueError(
            "§2.1 step 2: --fairness-config required (proxy refuses to start "
            "without it; --skip-fairness invalidates baseline-comparison validity)"
        )

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]

    args.out.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m", "scripts.measurement_proxy",
        "--port", str(port),
        "--condition", args.condition,
        "--surface", args.surface,
        "--fairness-config", str(args.fairness_config),
        "--out", str(args.out),
    ]
    proc = subprocess.Popen(
        cmd,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    stderr_q: queue.Queue[str] = queue.Queue()

    def _drain() -> None:
        try:
            for line in iter(proc.stderr.readline, ""):
                stderr_q.put(line)
        except Exception:
            pass

    threading.Thread(target=_drain, daemon=True).start()

    captured: list[str] = []
    deadline = time.monotonic() + 30.0
    listening_seen = False
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            while not stderr_q.empty():
                try:
                    captured.append(stderr_q.get_nowait())
                except queue.Empty:
                    break
            raise RuntimeError(
                f"§2.1 step 2: proxy exited before listening with code {proc.returncode}: "
                f"{''.join(captured)[-1000:]}"
            )
        try:
            line = stderr_q.get(timeout=0.5)
        except queue.Empty:
            continue
        captured.append(line)
        if "listening on" in line:
            listening_seen = True
            break

    if not listening_seen:
        proc.terminate()
        try:
            proc.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            proc.kill()
        raise RuntimeError(
            f"§2.1 step 2: proxy did not log 'listening on' within 30s; "
            f"stderr tail: {''.join(captured)[-500:]}"
        )

    m.write(
        "proxy_spawn",
        {
            "port": port,
            "pid": proc.pid,
            "fairness_config": str(args.fairness_config),
            "condition": args.condition,
            "surface": args.surface,
            "out": str(args.out),
            "startup_log_lines": len(captured),
            "cmd": cmd,
        },
    )
    return port


def step_3_cache_rewriter_install(args: LaunchArgs, port: int, m: Manifest) -> None:
    """§2.1 step 3 + §2.4 rewrite contract.

    Experimental only. The rewriter itself lives in the proxy (§2.4); this step
    documents the contract in the manifest and verifies the proxy subprocess is
    still alive and bound to the expected port. It does NOT mutate the running
    proxy — the rewriter is gated inside proxy.py on ``--condition=experimental``.

    Baseline: skip with reason. Manifest row documents skip.

    Experimental (current scope): emit a ``cache_rewriter_install`` manifest row
    carrying the full §2.4 contract (block order, cache_control placement,
    header pin) + a ``rewriter_code_status`` field. When §2.4's rewriter code
    lands in proxy.py, flip ``rewriter_code_status`` to ``installed`` (today
    it's ``scaffold_only`` — proxy forwards request bodies verbatim). The §2.6
    cache-preservation gate in step_8 will correctly fail while status is
    ``scaffold_only``, which is the right signal.
    """
    if args.condition == "baseline":
        m.write("cache_rewriter_install", {"skipped": True, "reason": "baseline condition"})
        return

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            s.connect(("127.0.0.1", port))
        proxy_reachable = True
    except (OSError, socket.timeout):
        proxy_reachable = False

    if not proxy_reachable:
        raise RuntimeError(
            f"§2.1 step 3: proxy on port {port} not reachable — cannot install "
            f"cache rewriter on a dead process (step_2 should have fail-loud'd first)"
        )

    rewriter_source = "scripts/measurement_proxy/proxy.py (pending §2.4 implementation)"
    rewriter_code_status = _detect_rewriter_code_status()

    m.write(
        "cache_rewriter_install",
        {
            "skipped": False,
            "proxy_reachable": proxy_reachable,
            "port": port,
            "rewriter_source": rewriter_source,
            "rewriter_code_status": rewriter_code_status,
            "contract": {
                "block_order": [
                    "CLAUDE.md",
                    "engram_prefix",
                    "relay_digest",
                    "tool_manifest",
                    "skills_manifest",
                ],
                "cache_boundary": "last block of system-prompt segment",
                "cache_control_type": "ephemeral",
                "strip_cache_control_from": "conversation-history blocks",
                "header_pin": "anthropic-beta: prompt-caching-2024-07-31 (fairness pin cache_beta_header)",
                "unknown_block_policy": "proxy returns 400; manifest flags unknown_system_block",
            },
            "downstream_gate": (
                "§2.6 cache-preservation gate fails while rewriter_code_status=scaffold_only — "
                "correct signal, not a regression"
            ),
        },
    )


def _detect_rewriter_code_status() -> str:
    """Return ``installed`` if proxy.py carries the §2.4 rewriter, else ``scaffold_only``.

    Detection is intentionally shallow — it looks for a sentinel function name
    the §2.4 implementation will export. Until that function exists, the
    launcher correctly flags the status so step_8's §2.6 gate can report cause.
    """
    try:
        from scripts.measurement_proxy import proxy as _proxy

        if hasattr(_proxy, "rewrite_system_blocks") or hasattr(_proxy, "_cache_preservation_rewriter"):
            return "installed"
    except ImportError:
        return "unknown_import_error"
    return "scaffold_only"


def _resolve_recording_manifest(workload_recording: pathlib.Path) -> pathlib.Path:
    """Convention: <recording>.jsonl → <recording>.manifest.json (sibling)."""
    return workload_recording.with_name(workload_recording.stem + ".manifest.json")


def _resolve_memory_index() -> pathlib.Path:
    """Auto-memory MEMORY.md location for hard-rule predicate.

    Path is derived per Claude Code's per-project memory layout — the project
    directory name is a slug of the working directory. Override with
    NUCLEUS_WRAPPED_MEMORY_INDEX env var if running outside the canonical
    workspace (test fixtures, ephemeral worktree replay).
    """
    import os

    override = os.environ.get("NUCLEUS_WRAPPED_MEMORY_INDEX")
    if override:
        return pathlib.Path(override)
    return (
        pathlib.Path.home()
        / ".claude"
        / "projects"
        / "-Users-lokeshgarg-ai-mvp-backend"
        / "memory"
        / "MEMORY.md"
    )


def step_4_engram_prematerialize(args: LaunchArgs, m: Manifest) -> pathlib.Path | None:
    """§2.1 step 4 + §2.2 4-predicate selector + 12K budget ceiling.

    Experimental only. Predicates (stable concat order):
      1. hard-rule memories (unfiltered by intensity)
      2. top-N=20 highest-intensity Feature/Architecture/Decision engrams from last 14d
      3. task-tag BM25 match top-10 (index regenerated from frozen snapshot — self-review crack #3)
      4. last 3 end_of_day captures
    Budget: 12K tokens. Overflow: drop (2) then (3); never (1) or (4).
    Output: .brain/nucleus_wrapped/engram_prefix.<run_id>.md
    Baseline: returns None, manifest row documents skip.

    Snapshot contract: step_1 (worktree freeze) materializes the snapshot at
    .brain/nucleus_wrapped/engram_snapshot.<run_id>.jsonl. If the snapshot is
    absent at this point, the selector renders only the hard-rule section
    (still useful) and the manifest flags ``snapshot_present=false`` for
    downstream gates to inspect.
    """
    if args.condition == "baseline":
        m.write("engram_prematerialize", {"skipped": True, "reason": "baseline condition"})
        return None

    from . import engram_selector

    snapshot_path = pathlib.Path(".brain/nucleus_wrapped") / f"engram_snapshot.{args.run_id}.jsonl"
    memory_index = _resolve_memory_index()
    recording_manifest_path = _resolve_recording_manifest(args.workload_recording)

    task_tags: list[str] = []
    if recording_manifest_path.exists():
        try:
            recording_manifest = json.loads(recording_manifest_path.read_text())
            task_tags = list(recording_manifest.get("task_tags", []))
        except (json.JSONDecodeError, OSError):
            pass

    result = engram_selector.select_engram_prefix(
        snapshot_path=snapshot_path,
        memory_index=memory_index,
        task_tags=task_tags,
    )
    out_path = pathlib.Path(".brain/nucleus_wrapped") / f"engram_prefix.{args.run_id}.md"
    engram_selector.write_prefix(result, out_path)

    m.write(
        "engram_prematerialize",
        {
            "out_path": str(out_path),
            "estimated_tokens": result.estimated_tokens,
            "sections": result.sections,
            "overflow_dropped": result.overflow_dropped,
            "engram_budget_exceeded": "budget_exceeded" in result.overflow_dropped,
            "task_tags_count": len(task_tags),
            "snapshot_present": snapshot_path.exists(),
            "memory_index_present": memory_index.exists(),
        },
    )
    return out_path


_SURFACE_TO_RELAY_FOLDER = {
    "cc_peer": "claude_code_peer",
    "cc_main": "claude_code_main",
    "cowork": "cowork",
}


def _parse_relay_body(body: Any) -> dict[str, Any]:
    if isinstance(body, dict):
        return body
    if not isinstance(body, str) or not body.strip():
        return {}
    try:
        parsed = json.loads(body)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _load_relay_envelopes(
    folder: pathlib.Path, window_start: str, window_end: str
) -> list[dict[str, Any]]:
    """Load + window-filter envelopes. Normalizes ``in_reply_to`` from the
    body JSON onto the envelope (per to-cowork skill v2.2 the field lives
    in the body, not on the envelope) so downstream thread-chain logic can
    stay envelope-level."""
    out: list[dict[str, Any]] = []
    if not folder.exists():
        return out
    for path in sorted(folder.glob("*.json")):
        try:
            env = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(env, dict):
            continue
        ts = env.get("created_at", "")
        if not isinstance(ts, str):
            continue
        if not (window_start <= ts <= window_end):
            continue
        if not env.get("in_reply_to"):
            body = _parse_relay_body(env.get("body"))
            irt = body.get("in_reply_to")
            if isinstance(irt, str) and irt:
                env["in_reply_to"] = irt
        out.append(env)
    return out


def _render_open_asks(envelopes: list[dict[str, Any]]) -> tuple[str, int]:
    asks = [e for e in envelopes if not e.get("read") and e.get("priority") == "high"]
    if not asks:
        return ("", 0)
    parts = ["## (a) Open asks (unread, priority=high)\n"]
    for e in asks:
        body = _parse_relay_body(e.get("body"))
        summary = body.get("summary", "") if isinstance(body, dict) else ""
        first_line = summary.split("\n", 1)[0][:200] if isinstance(summary, str) else ""
        subject = (e.get("subject") or "(no subject)")[:200]
        parts.append(
            f"- **{e.get('id', '?')}** from {e.get('from', '?')} — {subject}"
        )
        if first_line:
            parts.append(f"  {first_line}")
        parts.append("")
    return ("\n".join(parts).rstrip() + "\n", len(asks))


def _render_thread_context(envelopes: list[dict[str, Any]]) -> tuple[str, int]:
    """Group envelopes into in_reply_to chains. Root may be outside window
    (label keeps the parent id so the chain is still reconstructable)."""
    by_id = {e.get("id"): e for e in envelopes if e.get("id")}
    is_replied_to: set[str] = set()
    for e in envelopes:
        irt = e.get("in_reply_to")
        if irt:
            is_replied_to.add(irt)

    def _root_of(env: dict[str, Any]) -> str:
        cur = env
        seen: set[str] = set()
        while True:
            cid = cur.get("id", "?")
            if cid in seen:
                return cid
            seen.add(cid)
            irt = cur.get("in_reply_to")
            if not irt:
                return cid
            parent = by_id.get(irt)
            if parent is None:
                return irt
            cur = parent

    chains: dict[str, list[dict[str, Any]]] = {}
    for e in envelopes:
        is_thread_member = bool(e.get("in_reply_to")) or e.get("id") in is_replied_to
        if not is_thread_member:
            continue
        root = _root_of(e)
        chains.setdefault(root, []).append(e)

    if not chains:
        return ("", 0)
    parts = ["## (b) Thread context (in_reply_to chains)\n"]
    for root in sorted(chains.keys()):
        members = chains[root]
        parts.append(f"### Thread root: {root}")
        for env in sorted(members, key=lambda x: x.get("created_at", "")):
            subject = (env.get("subject") or "(no subject)")[:150]
            parts.append(
                f"- {env.get('id', '?')} "
                f"({env.get('from', '?')}, {env.get('priority', 'normal')}): {subject}"
            )
        parts.append("")
    return ("\n".join(parts).rstrip() + "\n", len(chains))


def _render_artifact_refs(envelopes: list[dict[str, Any]]) -> tuple[str, int]:
    refs: list[str] = []
    seen: set[str] = set()
    for e in envelopes:
        body = _parse_relay_body(e.get("body"))
        for ref in body.get("artifact_refs", []) or []:
            if isinstance(ref, str) and ref and ref not in seen:
                seen.add(ref)
                refs.append(ref)
    if not refs:
        return ("", 0)
    parts = ["## (c) Artifact refs (deduplicated)\n"]
    for ref in refs:
        parts.append(f"- {ref}")
    return ("\n".join(parts) + "\n", len(refs))


def step_5_relay_prematerialize(args: LaunchArgs, m: Manifest) -> pathlib.Path | None:
    """§2.1 step 5 + §2.3 three-section digest.

    Experimental only. Reads .brain/relay/<own_role>/*.json filtered by
    recording.relay_freeze_window. Renders:
      (a) open asks (unread + priority=high)
      (b) thread context (in_reply_to chains within window)
      (c) artifact refs (deduplicated)
    Output: .brain/nucleus_wrapped/relay_digest.<run_id>.md
    Placement contract: concatenated to system prompt BEFORE cache boundary.
    Anti-pattern: NOT injected via UserPromptSubmit hook (lands after boundary,
    defeats warmth — §2.3 line 137).

    Fails loud on:
      - missing recording.manifest.json
      - missing/malformed relay_freeze_window (pin #20, required for experimental)

    Tolerant of:
      - relay folder absent (folder may not exist for surfaces with no inbound
        traffic in the window — manifest flags relay_folder_present=false,
        digest renders as empty)
    """
    if args.condition == "baseline":
        m.write("relay_prematerialize", {"skipped": True, "reason": "baseline condition"})
        return None

    recording_manifest_path = _resolve_recording_manifest(args.workload_recording)
    if not recording_manifest_path.exists():
        raise FileNotFoundError(
            f"§2.1 step 5: recording manifest not found at {recording_manifest_path}"
        )
    recording_manifest = json.loads(recording_manifest_path.read_text())

    window = recording_manifest.get("relay_freeze_window")
    if not isinstance(window, dict):
        raise ValueError(
            "§2.1 step 5 / §2.3: recording manifest missing relay_freeze_window "
            "(pin #20 — required for experimental condition)"
        )
    window_start = window.get("start")
    window_end = window.get("end")
    if not isinstance(window_start, str) or not isinstance(window_end, str):
        raise ValueError(
            f"§2.1 step 5: relay_freeze_window must carry start and end ISO "
            f"timestamp strings; got {window!r}"
        )

    own_role = recording_manifest.get("own_role") or args.surface
    folder_name = _SURFACE_TO_RELAY_FOLDER.get(own_role, own_role)
    relay_folder = pathlib.Path(".brain/relay") / folder_name

    envelopes = _load_relay_envelopes(relay_folder, window_start, window_end)

    open_asks_md, n_asks = _render_open_asks(envelopes)
    thread_md, n_threads = _render_thread_context(envelopes)
    artifact_md, n_refs = _render_artifact_refs(envelopes)

    sections = [s for s in (open_asks_md, thread_md, artifact_md) if s]
    rendered = ("\n".join(sections).rstrip() + "\n") if sections else ""

    out_path = pathlib.Path(".brain/nucleus_wrapped") / f"relay_digest.{args.run_id}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(rendered)

    digest_size_tokens = max(1, len(rendered) // 4) if rendered else 0

    m.write(
        "relay_prematerialize",
        {
            "skipped": False,
            "out_path": str(out_path),
            "own_role": own_role,
            "relay_folder": str(relay_folder),
            "relay_folder_present": relay_folder.exists(),
            "window_start": window_start,
            "window_end": window_end,
            "envelopes_in_window": len(envelopes),
            "open_asks_count": n_asks,
            "thread_chains_count": n_threads,
            "artifact_refs_count": n_refs,
            "relay_digest_size_tokens": digest_size_tokens,
        },
    )
    return out_path


_HOST_LEAK_UNSET_EXACT = (
    "CLAUDE_CODE_SESSION_ID",
    "CLAUDE_CODE_ENTRYPOINT",
    "ANTHROPIC_LOG",
)
_HOST_LEAK_UNSET_PREFIXES = (
    "CC_OVERRIDE_",
    "CLAUDE_CODE_",  # catches session-state that bleeds across runs
)


def step_6_environment_pin(args: LaunchArgs, port: int, m: Manifest) -> dict[str, str]:
    """§2.1 step 6 — build the step_7 env dict.

    Pins (per §2.1 line 110):
      - ANTHROPIC_BASE_URL=http://127.0.0.1:<port>
      - CC_SESSION_ROLE=peer
      - NUCLEUS_BRAIN_PATH=<worktree>/.brain
      - NUCLEUS_WRAPPED_RUN_ID=<run_id>

    Unset host-leak vars:
      - CLAUDE_CODE_SESSION_ID (reuse across runs would taint warm prefix)
      - CC_OVERRIDE_* (runtime feature flags that could diverge baseline vs experimental)
      - CLAUDE_CODE_* prefix sweep (anything the CLI stores in env for cross-session state)
      - CLAUDE_CODE_ENTRYPOINT, ANTHROPIC_LOG (verbosity knobs that could affect latency)
      - ANTHROPIC_API_KEY: conditional — only unset if an OAuth session is detected
        (presence of CLAUDE_CODE_OAUTH_TOKEN or similar). Unset blindly would
        break API-key-only test setups; §2.6 fairness gate flags cross-run key diff.

    PRESERVES (does not touch) — needed by Python/uv/CC to function:
      - PATH, HOME, USER, LANG, LC_*, TERM, TMPDIR, SHELL, PWD
      - PYTHONPATH, VIRTUAL_ENV, UV_* (venv invariance across baseline vs experimental
        is a fairness guarantee, not a leak — §3 pin)

    Returns the pinned env dict (a copy — does NOT mutate os.environ, so the
    launcher itself keeps host env for orchestration while step_7 gets the
    frozen dict).

    Manifest row: {step: environment_pin, pinned: {...}, unset_exact: [...],
                    unset_by_prefix: [...], preserved_oauth_key: bool}
    """
    worktree_brain = args.replay_worktree / ".brain"

    pinned = {
        "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{port}",
        "CC_SESSION_ROLE": "peer",
        "NUCLEUS_BRAIN_PATH": str(worktree_brain),
        "NUCLEUS_WRAPPED_RUN_ID": args.run_id,
    }

    env = dict(os.environ)

    unset_exact_hit: list[str] = []
    for k in _HOST_LEAK_UNSET_EXACT:
        if k in env:
            del env[k]
            unset_exact_hit.append(k)

    unset_by_prefix_hit: list[str] = []
    for k in list(env.keys()):
        for prefix in _HOST_LEAK_UNSET_PREFIXES:
            if k.startswith(prefix):
                del env[k]
                unset_by_prefix_hit.append(k)
                break

    oauth_detected = any(
        k in os.environ
        for k in ("CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_OAUTH_TOKEN")
    )
    preserved_oauth_key = False
    if oauth_detected and "ANTHROPIC_API_KEY" in env:
        del env["ANTHROPIC_API_KEY"]
        unset_exact_hit.append("ANTHROPIC_API_KEY")
    elif "ANTHROPIC_API_KEY" in env:
        preserved_oauth_key = True

    env.update(pinned)

    m.write(
        "environment_pin",
        {
            "pinned": dict(pinned),
            "unset_exact": unset_exact_hit,
            "unset_by_prefix": unset_by_prefix_hit,
            "preserved_oauth_key": preserved_oauth_key,
            "oauth_session_detected": oauth_detected,
            "env_size_after": len(env),
        },
    )
    return env


def _detect_replay_driver_status() -> tuple[str, pathlib.Path | None]:
    """Look for scripts/nucleus_wrapped/replay_driver.py; return status +
    resolved path. Mirrors step_3's _detect_rewriter_code_status pattern —
    when the driver lands as code, status flips automatically with no
    launcher changes."""
    candidate = pathlib.Path("scripts/nucleus_wrapped/replay_driver.py")
    if not candidate.exists():
        return ("missing", None)
    try:
        from scripts.nucleus_wrapped import replay_driver as _drv  # type: ignore[import-not-found]

        if hasattr(_drv, "drive_replay") or hasattr(_drv, "main"):
            return ("installed", candidate)
        return ("scaffold_only", candidate)
    except ImportError:
        return ("scaffold_only", candidate)


def step_7_workload_replay(args: LaunchArgs, env: dict[str, str], port: int, m: Manifest) -> None:
    """§2.1 step 7 + §2.5 replay-determinism.

    Launcher's responsibility (this function):
      - resolve the replay driver (scripts/nucleus_wrapped/replay_driver.py)
      - subprocess.run the driver with env from step_6 + proxy port + recording path
      - capture exit code + stdout/stderr tails
      - fail loud on stub-miss exit code (§2.5 'Tool-call responses' row)
      - emit per-turn progress lines from the driver to the manifest

    Driver's responsibility (scripts/nucleus_wrapped/replay_driver.py):
      - feed recorded prompts into ONE claude session (--resume chaining or
        SDK in-process driver — driver chooses; subprocess-per-turn would
        defeat session-warmth, see runbook §Run "subprocess != session")
      - intercept tool-calls at MCP-deferred boundary
      - stub with recording.tool_calls[turn_index].response when
        (name, args-hash) matches
      - fail loud on stub-miss

    Today (driver_status=missing or scaffold_only): manifest emits a
    ``workload_replay`` row with status flagged. §2.6 replay-determinism
    gate in step_8 will correctly fail — same signal as step_3 / §2.4.
    """
    driver_status, driver_path = _detect_replay_driver_status()

    if not args.workload_recording.exists():
        raise FileNotFoundError(
            f"§2.1 step 7: recording {args.workload_recording} not found"
        )

    contract = {
        "session_continuity": (
            "driver MUST drive ONE session (--resume chain or SDK), NOT "
            "subprocess-per-turn (defeats cache warmth; runbook §Run)"
        ),
        "tool_call_stubbing": (
            "driver intercepts at MCP-deferred boundary; matches "
            "(name, args_sha256) against recording.tool_calls[turn_index]; "
            "fail-loud on stub-miss with exit code 13"
        ),
        "per_turn_emission": (
            "driver emits one JSON line per turn to stdout: "
            "{turn_index, prompt_hash, exit_code, duration_s, stub_hits, stub_misses}"
        ),
    }

    if driver_status in ("missing", "scaffold_only"):
        m.write(
            "workload_replay",
            {
                "skipped": True,
                "driver_status": driver_status,
                "driver_path": str(driver_path) if driver_path else None,
                "contract": contract,
                "recording": str(args.workload_recording),
                "proxy_port": port,
                "downstream_gate": (
                    "§2.6 replay-determinism gate fails while driver_status "
                    f"in (missing, scaffold_only) — currently '{driver_status}'; "
                    "correct signal, not a regression"
                ),
            },
        )
        return

    cmd = [
        sys.executable,
        "-m", "scripts.nucleus_wrapped.replay_driver",
        "--recording", str(args.workload_recording),
        "--proxy-port", str(port),
        "--run-id", args.run_id,
        "--out", str(args.out),
    ]
    start = time.monotonic()
    proc = subprocess.run(
        cmd, env=env, capture_output=True, text=True, check=False,
    )
    duration_s = round(time.monotonic() - start, 3)

    turn_lines: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
            if isinstance(row, dict) and "turn_index" in row:
                turn_lines.append(row)
        except json.JSONDecodeError:
            continue

    if proc.returncode == 13:
        raise RuntimeError(
            f"§2.1 step 7 / §2.5: driver reported stub-miss (exit 13). "
            f"stderr tail: {proc.stderr[-1000:]}"
        )
    if proc.returncode != 0:
        raise RuntimeError(
            f"§2.1 step 7: driver exited non-zero ({proc.returncode}). "
            f"stderr tail: {proc.stderr[-1000:]}"
        )

    m.write(
        "workload_replay",
        {
            "skipped": False,
            "driver_status": driver_status,
            "driver_path": str(driver_path),
            "contract": contract,
            "recording": str(args.workload_recording),
            "proxy_port": port,
            "duration_s": duration_s,
            "turn_count": len(turn_lines),
            "turns": turn_lines,
            "stderr_len": len(proc.stderr),
        },
    )


def _read_manifest_rows(path: pathlib.Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
            if isinstance(row, dict):
                rows.append(row)
        except json.JSONDecodeError:
            continue
    return rows


def _kill_proxy(pid: int, *, grace_s: float = 5.0) -> str:
    """SIGTERM with grace, SIGKILL fallback. Returns terminal status string."""
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return "already_dead"
    except OSError as exc:
        return f"kill_error: {exc}"

    deadline = time.monotonic() + grace_s
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return "terminated"
        time.sleep(0.1)

    try:
        os.kill(pid, signal.SIGKILL)
        return "killed_after_term_timeout"
    except ProcessLookupError:
        return "terminated_during_grace"
    except OSError as exc:
        return f"sigkill_error: {exc}"


def _evaluate_gates(
    args: LaunchArgs,
    rows: list[dict[str, Any]],
    proxy_kill_result: str,
    worktree_remove_result: str,
) -> dict[str, Any]:
    """§2.6 gate evaluator. Each gate returns {pass, reason}. Overall PASS
    requires all four. While substrate components are scaffold_only / missing,
    the corresponding gates correctly FAIL — that's the right signal."""
    rewriter_row = next((r for r in rows if r.get("step") == "cache_rewriter_install"), None)
    env_row = next((r for r in rows if r.get("step") == "environment_pin"), None)
    replay_row = next((r for r in rows if r.get("step") == "workload_replay"), None)
    proxy_row = next((r for r in rows if r.get("step") == "proxy_spawn"), None)

    fairness_pin_present = bool(proxy_row and proxy_row.get("fairness_config"))
    pinned = (env_row or {}).get("pinned", {}) or {}
    pinned_env_complete = all(
        pinned.get(k)
        for k in ("ANTHROPIC_BASE_URL", "CC_SESSION_ROLE", "NUCLEUS_BRAIN_PATH", "NUCLEUS_WRAPPED_RUN_ID")
    )
    fairness_pass = fairness_pin_present and pinned_env_complete

    if args.condition == "baseline":
        cache_preservation_pass = True
        cache_preservation_reason = "baseline condition skips rewriter"
    else:
        rewriter_status = (rewriter_row or {}).get("rewriter_code_status", "missing")
        cache_preservation_pass = rewriter_status == "installed"
        cache_preservation_reason = f"rewriter_code_status={rewriter_status}"

    driver_status = (replay_row or {}).get("driver_status", "missing")
    turns = (replay_row or {}).get("turns", []) or []
    stub_misses = sum(int(t.get("stub_misses", 0)) for t in turns if isinstance(t, dict))
    turn_count = (replay_row or {}).get("turn_count", 0)
    if (replay_row or {}).get("skipped"):
        replay_determinism_pass = False
        replay_determinism_reason = f"driver skipped (status={driver_status})"
    else:
        replay_determinism_pass = (
            driver_status == "installed" and stub_misses == 0 and turn_count > 0
        )
        replay_determinism_reason = (
            f"driver_status={driver_status}, stub_misses={stub_misses}, turn_count={turn_count}"
        )

    teardown_pass = (
        proxy_kill_result in (
            "terminated", "already_dead",
            "terminated_during_grace", "killed_after_term_timeout",
            "no_proxy_row",
        )
        and worktree_remove_result in ("removed", "absent", "no_worktree_row")
    )

    overall_pass = (
        fairness_pass
        and cache_preservation_pass
        and replay_determinism_pass
        and teardown_pass
    )

    return {
        "overall_pass": overall_pass,
        "condition": args.condition,
        "run_id": args.run_id,
        "gates": {
            "fairness": {
                "pass": fairness_pass,
                "fairness_pin_present": fairness_pin_present,
                "pinned_env_complete": pinned_env_complete,
            },
            "cache_preservation": {
                "pass": cache_preservation_pass,
                "reason": cache_preservation_reason,
            },
            "replay_determinism": {
                "pass": replay_determinism_pass,
                "reason": replay_determinism_reason,
            },
            "teardown": {
                "pass": teardown_pass,
                "proxy_kill_result": proxy_kill_result,
                "worktree_remove_result": worktree_remove_result,
            },
        },
    }


def step_8_teardown(args: LaunchArgs, original_cwd: pathlib.Path, m: Manifest) -> None:
    """§2.1 step 8 + §2.6 verification gates.

    Sequence:
      1. Read manifest rows back (recovers PID + worktree path without
         needing in-memory plumbing across step boundaries).
      2. SIGTERM proxy by PID; grace period; SIGKILL fallback. Tolerant
         of already-dead.
      3. chdir to original_cwd (step_1 chdir'd INTO worktree; can't remove
         a tree we're sitting in), then `git worktree remove --force`.
      4. Evaluate §2.6 gates: fairness, cache_preservation, replay_determinism,
         teardown. Overall PASS requires all four.
      5. Write gate_results.json to .brain/nucleus_wrapped/runs/<run_id>/.
      6. Emit teardown manifest row.

    Today's expected result on experimental condition: cache_preservation
    + replay_determinism FAIL while §2.4 rewriter + replay driver remain
    scaffold_only / missing — this is the correct signal to §3 (paired-run
    harness) that the experiment is not yet runnable end-to-end.
    """
    rows = _read_manifest_rows(m.path)
    proxy_row = next((r for r in rows if r.get("step") == "proxy_spawn"), None)
    worktree_row = next((r for r in rows if r.get("step") == "worktree_freeze"), None)

    proxy_kill_result = "no_proxy_row"
    if proxy_row and isinstance(proxy_row.get("pid"), int):
        proxy_kill_result = _kill_proxy(proxy_row["pid"])

    worktree_remove_result = "no_worktree_row"
    if worktree_row and worktree_row.get("worktree_path"):
        wt_path = pathlib.Path(worktree_row["worktree_path"])
        try:
            os.chdir(original_cwd)
        except OSError:
            os.chdir("/")
        if not wt_path.exists():
            worktree_remove_result = "absent"
        else:
            try:
                _run_git(["worktree", "remove", "--force", str(wt_path)])
                worktree_remove_result = "removed"
            except subprocess.CalledProcessError as exc:
                worktree_remove_result = f"remove_failed: {exc.stderr.strip()[:200]}"

    gates = _evaluate_gates(args, rows, proxy_kill_result, worktree_remove_result)

    ship_dir = pathlib.Path(".brain/nucleus_wrapped/runs") / args.run_id
    ship_dir.mkdir(parents=True, exist_ok=True)
    gate_results_path = ship_dir / "gate_results.json"
    gate_results_path.write_text(json.dumps(gates, indent=2))

    m.write(
        "teardown",
        {
            "proxy_kill_result": proxy_kill_result,
            "worktree_remove_result": worktree_remove_result,
            "gate_results_path": str(gate_results_path),
            "gates_passed": gates["overall_pass"],
            "gates": gates["gates"],
        },
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    original_cwd = pathlib.Path.cwd()
    manifest_path = pathlib.Path(".brain/nucleus_wrapped") / f"manifest.{args.run_id}.jsonl"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    m = Manifest(run_id=args.run_id, path=manifest_path)
    m.write("launch_start", {"args": dataclasses.asdict(args) | {k: str(v) for k, v in dataclasses.asdict(args).items() if isinstance(v, pathlib.Path)}})

    step_1_worktree_freeze(args, m)
    port = step_2_proxy_spawn(args, m)
    step_3_cache_rewriter_install(args, port, m)
    step_4_engram_prematerialize(args, m)
    step_5_relay_prematerialize(args, m)
    env = step_6_environment_pin(args, port, m)
    step_7_workload_replay(args, env, port, m)
    step_8_teardown(args, original_cwd, m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
