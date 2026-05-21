"""Nucleus-Delegate v0.3 — singular MCP tool for the integrated delegation stack.

Exposes 15 actions across 6 groups under one tool name (`nucleus_delegate`):

  Execution:    fire_sync, fire_pair, fire_doc
  Pair:         pair_start, pair_stop, pair_status
  Telemetry:    audit_cost, audit_utilization, audit_events
  Authority:    authority_check, authority_keywords
  Identity:     identify_agent, resolve_identity, heartbeat   (v0.2 forward-compat;
                                                              real registry per ADR 0006 builds at M1)
  Bootstrap:    init                                          (v0.3 — cold-start unblock)

v0.3 adds: cold-start auto-bootstrap (workspace + charter fallback) so vibe coders
without a pre-existing `.brain/` or `docs/org/charters/` can call any action and
have it work or fail honestly with a path hint.

Compound-before-build: every handler wraps an existing primitive
(`cli.init_brain_solo`, `_pair_actions`, `audit_token_cost`, etc.).
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from importlib import resources as _ir
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import _pair_actions as _pa


# ─── envelope helpers ────────────────────────────────────────────────────


def _ok(data: Dict[str, Any], **extra: Any) -> str:
    """Success envelope. `extra` keys merge into the top-level (alongside
    `ok` + `data`) for forward-compat metadata like `auto_initialized`,
    `workspace`, `translated_from` (v0.3+)."""
    payload = {"ok": True, "data": data, **extra}
    return json.dumps(payload, indent=2, default=str)


def _err(code: str, message: str, **extra: Any) -> str:
    payload = {"ok": False, "error": {"code": code, "message": message}, **extra}
    return json.dumps(payload, indent=2, default=str)


def _repo_root() -> Path:
    return Path.cwd()


# ─── v0.3 — workspace resolution + auto-bootstrap (capability A) ─────────


def _try_write_probe(parent: Path) -> bool:
    """Belt-and-suspenders write-probe per [TWEAK 6]. `os.access` lies on
    macOS SIP-protected paths and certain network mounts. Try the actual
    write to be sure."""
    try:
        parent.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError):
        return False
    probe = parent / ".write_probe"
    try:
        probe.write_text("ok")
        probe.unlink(missing_ok=True)
        return True
    except (PermissionError, OSError):
        return False


def _resolve_workspace() -> Path:
    """Pick where `.brain/` should live for the current call.

    Priority: cwd-with-.git → writable cwd (not $HOME) → ~/.nucleus/brain.
    Returns the resolved `.brain` path. Caller checks `_try_write_probe`
    on the parent before initializing.
    """
    cwd = Path.cwd()
    if (cwd / ".git").exists():
        return cwd / ".brain"
    if cwd.resolve() != Path.home().resolve() and os.access(cwd, os.W_OK):
        return cwd / ".brain"
    return Path.home() / ".nucleus" / "brain"


def _ensure_workspace() -> Dict[str, Any]:
    """Resolve + bootstrap workspace if missing. Idempotent.

    Returns metadata dict {workspace: <abs path>, auto_initialized: bool}
    OR {error: "WORKSPACE_NOT_WRITABLE", workspace: <attempted path>} if
    even the home fallback rejects the write-probe (read-only home, etc.).
    """
    workspace = _resolve_workspace()
    state = workspace / "ledger" / "state.json"
    if state.exists():
        return {"workspace": str(workspace), "auto_initialized": False}

    if not _try_write_probe(workspace.parent):
        # Try home fallback explicitly even if cwd was the picked default
        fallback = Path.home() / ".nucleus" / "brain"
        if fallback != workspace and _try_write_probe(fallback.parent):
            workspace = fallback
            state = workspace / "ledger" / "state.json"
            if state.exists():
                return {"workspace": str(workspace), "auto_initialized": False}
        else:
            return {
                "error": "WORKSPACE_NOT_WRITABLE",
                "workspace": str(workspace),
            }

    # Bootstrap silently (init_brain_solo emits prints which would corrupt
    # JSON-RPC stdio frame).
    try:
        from ..cli import init_brain_solo
        with contextlib.redirect_stdout(io.StringIO()):
            init_brain_solo(workspace)
        _stamp_template_marker(workspace, "solo")
    except Exception as e:
        return {
            "error": "BOOTSTRAP_FAILED",
            "workspace": str(workspace),
            "detail": str(e),
        }

    return {"workspace": str(workspace), "auto_initialized": True}


def _stamp_template_marker(workspace: Path, template: str) -> None:
    """Write `template` field into state.json so subsequent init calls
    can detect mismatch. init_brain_* doesn't do this natively.
    Non-fatal if it fails — mismatch detection just won't work for that brain.
    """
    state_file = workspace / "ledger" / "state.json"
    try:
        existing = json.loads(state_file.read_text())
        if existing.get("template") != template:
            existing["template"] = template
            state_file.write_text(json.dumps(existing, indent=2))
    except (OSError, json.JSONDecodeError):
        pass


# ─── v0.3 — charter resolution (capability E) ────────────────────────────


def _resolve_charter(lane: str) -> Path:
    """Filesystem first, packaged default on miss. Returns a real Path
    (cross-platform via importlib.resources.as_file).

    For pair lanes ('peer', 'main'), prefer 'sonnet_helper_<lane>.md' on
    the filesystem; on miss, fall back to packaged 'sonnet_helper_<lane>.md'
    or finally to packaged 'sonnet_helper_default.md'.
    """
    fs_path = _repo_root() / "docs" / "org" / "charters" / f"sonnet_helper_{lane}.md"
    if fs_path.exists():
        return fs_path

    # Try lane-specific packaged default
    for name in (f"sonnet_helper_{lane}.md", "sonnet_helper_default.md"):
        try:
            ref = _ir.files("mcp_server_nucleus.templates.charters") / name
            if ref.is_file():
                # importlib.resources.as_file materializes to a real Path
                # cross-platform (handles zip-imports, etc.). Returns a
                # context manager; we need a stable Path so dump to temp.
                with _ir.as_file(ref) as p:
                    # Copy to a stable temp path that outlives the context
                    import tempfile
                    tmp = Path(tempfile.gettempdir()) / f"nucleus_charter_{lane}.md"
                    tmp.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
                    return tmp
        except (FileNotFoundError, ModuleNotFoundError):
            continue

    # Last-resort: return the would-be filesystem path so the caller errors
    # with CHARTER_MISSING (preserves v0.2 behavior).
    return fs_path


# ─── v0.3 — init action ──────────────────────────────────────────────────


def init(template: str = "solo", brain_path: Optional[str] = None) -> str:
    """Explicit cold-start bootstrap. Wraps `cli.init_brain_solo` /
    `init_brain_default` / `init_brain_v0`. Bypasses the interactive
    `init_brain` (which has `input()` calls).

    Idempotent: re-init on existing brain with the same template = no-op.
    Per [TWEAK 5]: re-init with a DIFFERENT template returns
    INIT_TEMPLATE_MISMATCH instead of silent overwrite.
    """
    if template not in ("solo", "default", "v0"):
        return _err("INVALID_TEMPLATE",
                    f"template must be solo|default|v0; got {template!r}")

    workspace = Path(brain_path) if brain_path else _resolve_workspace()
    state_file = workspace / "ledger" / "state.json"

    if state_file.exists():
        try:
            existing = json.loads(state_file.read_text())
            persisted_template = existing.get("template")  # may be None
        except (OSError, json.JSONDecodeError):
            persisted_template = None
        # If no template marker exists, this brain pre-dates v0.3 marker-stamping.
        # Accept any template request, stamp the marker now (forward-compat),
        # and report already_initialized. Mismatch detection only fires when
        # the marker is explicitly present and conflicts.
        if persisted_template is not None and persisted_template != template:
            return _err("INIT_TEMPLATE_MISMATCH",
                        f"existing brain at {workspace} was initialized with "
                        f"template={persisted_template!r}; refusing to overwrite "
                        f"with template={template!r}",
                        hint=f"remove {workspace} to re-init with a different template",
                        existing_template=persisted_template,
                        requested_template=template)
        # Stamp marker on legacy brains so future calls can detect mismatch.
        if persisted_template is None:
            _stamp_template_marker(workspace, template)
        return _ok({
            "workspace": str(workspace),
            "template": template,
            "already_initialized": True,
        })

    if not _try_write_probe(workspace.parent):
        return _err("WORKSPACE_NOT_WRITABLE",
                    f"cannot write to parent of {workspace}",
                    workspace=str(workspace))

    try:
        from ..cli import (
            init_brain_solo, init_brain_default, init_brain_v0,
        )
        with contextlib.redirect_stdout(io.StringIO()):
            if template == "solo":
                init_brain_solo(workspace)
            elif template == "default":
                init_brain_default(workspace)
            else:  # v0
                init_brain_v0(workspace, _repo_root())
    except Exception as e:
        return _err("BOOTSTRAP_FAILED",
                    f"{type(e).__name__}: {e}",
                    workspace=str(workspace))

    _stamp_template_marker(workspace, template)
    return _ok({
        "workspace": str(workspace),
        "template": template,
        "initialized": True,
    })


# ─── Execution: fire_sync ────────────────────────────────────────────────


def fire_sync(brief: str, lane: Optional[str] = None,
              model: str = "sonnet",
              charter: Optional[str] = None,
              parent_session_id: Optional[str] = None,
              timeout_s: int = 300) -> str:
    """L1 ephemeral fire — runs Sonnet/Haiku via Claude Code subprocess
    synchronously, returns the result inline.

    Reuses the same subprocess shape as the L3 pair daemon (no proxy URL,
    --no-session-persistence, charter via --append-system-prompt-file).
    """
    if model not in ("haiku", "sonnet"):
        return _err("INVALID_MODEL", f"model must be haiku|sonnet; got {model!r}")
    if not brief or not brief.strip():
        return _err("EMPTY_BRIEF", "brief cannot be empty")

    role = lane or os.environ.get("CC_SESSION_ROLE", "main")
    if role not in ("peer", "main", "cowork", "cc_tb", "gq"):
        return _err("INVALID_LANE", f"unknown lane {role!r}")

    if charter:
        charter_path = Path(charter)
        if not charter_path.exists():
            return _err("CHARTER_MISSING", f"expected {charter_path}")
    else:
        # v0.3: filesystem first, packaged default on miss (capability E).
        charter_path = _resolve_charter(role)
        if not charter_path.exists():
            return _err("CHARTER_MISSING", f"expected {charter_path}")

    model_full = "claude-haiku-4-5" if model == "haiku" else "claude-sonnet-4-6"
    parent_lane = f"claude_code_{role}"
    full_brief = (
        f"From: {parent_lane}\n"
        f"Brief: {brief.strip()}\n"
    )

    cmd = [
        "claude", "--print",
        "--model", model_full,
        "--append-system-prompt-file", str(charter_path),
        "--no-session-persistence",
        full_brief,
    ]
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_BASE_URL"}
    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout_s, cwd=str(_repo_root()),
            env=env, stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return _err("TIMEOUT", f"subprocess exceeded {timeout_s}s")
    except FileNotFoundError:
        return _err("CLAUDE_CLI_MISSING", "claude binary not on PATH")

    duration_s = time.time() - t0
    if proc.returncode != 0:
        return _err("SUBPROCESS_FAILED",
                    f"claude rc={proc.returncode}",
                    stderr=proc.stderr[:500])

    return _ok({
        "result": proc.stdout.strip(),
        "duration_ms": int(duration_s * 1000),
        "model": model_full,
        "model_key": model,
        "parent": parent_lane,
        "charter_path": str(charter_path),
    })


# ─── Execution: fire_pair (rename of v0.1 pair_fire) ─────────────────────


def fire_pair(lane: str, brief: str, model: str = "sonnet",
              subject: Optional[str] = None,
              parent_session_id: Optional[str] = None) -> str:
    """L3 async fire — relays to running pair daemon for the lane. Result
    arrives as [DELEGATE-RESULT] in caller's relay inbox ~30-60s later."""
    return _pa.pair_fire(lane, brief, model, subject, parent_session_id)


# ─── Execution: fire_doc ──────────────────────────────────────────────────


def fire_doc(path: str, phase: str = "scout",
             model: str = "haiku") -> str:
    """L1-USING fire — scout (cheap-tier enrichment) or synthesize
    (strong-tier code-from-doc). v0.2 returns a CLI invocation hint;
    v0.3 will run the skill flow internally."""
    if phase not in ("scout", "synthesize"):
        return _err("INVALID_PHASE",
                    f"phase must be scout|synthesize; got {phase!r}")
    p = _repo_root() / path
    if not p.exists():
        return _err("DOC_MISSING", f"expected {p}")
    skill = "/scout-doc" if phase == "scout" else "/synthesize-doc"
    return _ok({
        "phase": phase,
        "doc_path": str(p),
        "model": model,
        "instructions": (
            f"Run from a Claude Code session: `{skill} {path}` "
            f"(L1-USING skills are CC-session-shaped today; v0.3 exposes "
            f"a self-contained subprocess path here)."
        ),
    })


# ─── Pair lifecycle (renames of v0.1 pair_*) ──────────────────────────────


def pair_start(lane: str, charter_path: Optional[str] = None) -> str:
    return _pa.pair_register(lane, charter_path)


def pair_stop(lane: str) -> str:
    return _pa.pair_stop(lane)


def pair_status(lane: Optional[str] = None) -> str:
    return _pa.pair_status(lane)


# ─── Telemetry: split audit_pair into 3 cleaner actions ──────────────────


def _import_audit_module():
    script = _repo_root() / "scripts" / "audit_token_cost.py"
    if not script.exists():
        raise FileNotFoundError(str(script))
    spec_root = str(_repo_root() / "scripts")
    if spec_root not in sys.path:
        sys.path.insert(0, spec_root)
    import audit_token_cost  # type: ignore
    return audit_token_cost


def audit_cost(window_hours: float = 24.0,
               group_by: str = "pair") -> str:
    """Proxy-token rollup over the requested window.
    group_by ∈ {"pair", "role"}: pair = (parent, role), role = role-only."""
    if group_by not in ("pair", "role"):
        return _err("INVALID_GROUP_BY",
                    f"group_by must be pair|role; got {group_by!r}")
    try:
        atc = _import_audit_module()
    except FileNotFoundError as e:
        return _err("AUDIT_MODULE_MISSING", str(e))

    events_path = _repo_root() / ".brain" / "ledger" / "events.jsonl"
    since = datetime.now(timezone.utc) - timedelta(hours=float(window_hours))
    events, malformed = atc.read_events(events_path, since)

    if group_by == "pair":
        rollup = atc.summarize_by_pair(events)
        rows = [
            {"parent": p, "role": r, **stats}
            for (p, r), stats in sorted(rollup.items())
        ]
    else:
        rollup = atc.summarize(events)
        rows = [{"role": r, **stats} for r, stats in sorted(rollup.items())]

    return _ok({
        "window_hours": window_hours,
        "group_by": group_by,
        "events_in_window": len(events),
        "malformed_skipped": malformed,
        "rollup": rows,
    })


def audit_utilization(lane: Optional[str] = None) -> str:
    """Pair busy% + ≥40% utilization gate flag per lane."""
    try:
        atc = _import_audit_module()
    except FileNotFoundError as e:
        return _err("AUDIT_MODULE_MISSING", str(e))
    events_path = _repo_root() / ".brain" / "ledger" / "events.jsonl"
    since = datetime.now(timezone.utc) - timedelta(hours=2.0)  # heartbeat freshness window
    events, _ = atc.read_events(events_path, since)
    util = atc.summarize_pair_utilization(events)

    rows = []
    for ln in sorted(util):
        if lane is not None and ln != lane:
            continue
        u = util[ln]
        rows.append({
            "lane": ln,
            "session_id": u.get("session_id"),
            "busy_pct_1h": u.get("busy_pct_1h"),
            "events_in_window": u.get("events_in_window"),
            "pid": u.get("pid"),
            "gate_pass_at_40_pct": (u.get("busy_pct_1h") or 0.0) >= 40.0,
        })
    return _ok({"utilization": rows})


def audit_events(since: Optional[str] = None,
                 type_filter: Optional[str] = None,
                 limit: int = 100) -> str:
    """Raw events.jsonl filter — read-only. since=ISO timestamp.
    type_filter ∈ {agent_spawn, agent_return, pair_heartbeat, ...}."""
    events_path = _repo_root() / ".brain" / "ledger" / "events.jsonl"
    if not events_path.exists():
        return _ok({"events": []})

    cutoff: Optional[datetime] = None
    if since:
        try:
            cutoff = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            return _err("INVALID_SINCE", f"unparseable ISO timestamp {since!r}")

    out: List[Dict[str, Any]] = []
    try:
        with open(events_path, "r", encoding="utf-8") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    ev = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if type_filter and ev.get("type") != type_filter:
                    continue
                if cutoff:
                    try:
                        ts = datetime.fromisoformat(
                            ev.get("timestamp", "").replace("Z", "+00:00"))
                        if ts < cutoff:
                            continue
                    except ValueError:
                        continue
                out.append({
                    "timestamp": ev.get("timestamp"),
                    "type": ev.get("type"),
                    "emitter": ev.get("emitter"),
                    "data": ev.get("data"),
                })
    except OSError as e:
        return _err("READ_FAILED", str(e))

    if len(out) > limit:
        out = out[-limit:]
    return _ok({"events": out, "count": len(out)})


# ─── Authority gate ──────────────────────────────────────────────────────


def authority_check(brief: str, subject: str = "") -> str:
    """Preflight: would this brief escalate per the contract? Read-only.
    Caller passes brief + optional subject; result names lateral-OK or escalate
    + the matched keyword if any."""
    try:
        from ..runtime.sonnet_pair_daemon import is_escalate, ALWAYS_ESCALATE_KEYWORDS
    except ImportError as e:
        return _err("DAEMON_IMPORT_FAILED", str(e))
    haystack = f"{subject}\n{brief}".lower()
    matches = [kw for kw in ALWAYS_ESCALATE_KEYWORDS if kw in haystack]
    return _ok({
        "would_escalate": bool(matches),
        "matched_keywords": matches,
        "category": "lateral_ok" if not matches else "always_escalate",
    })


def authority_keywords() -> str:
    """Read-only: full ALWAYS_ESCALATE keyword list. Transparency hook for
    callers that want to preflight or reason about the gate."""
    try:
        from ..runtime.sonnet_pair_daemon import ALWAYS_ESCALATE_KEYWORDS
    except ImportError as e:
        return _err("DAEMON_IMPORT_FAILED", str(e))
    return _ok({
        "keywords": list(ALWAYS_ESCALATE_KEYWORDS),
        "match_mode": "case_insensitive_substring",
        "scope": "subject + body concatenated",
    })


# ─── Identity (v0.2 forward-compat; M1 swap-in pending ADR 0006) ─────────


def identify_agent(role: str,
                   parent_session_id: Optional[str] = None,
                   capabilities: Optional[List[str]] = None,
                   provider: str = "anthropic_claude_code") -> str:
    """Register an agent identity. v0.2: forwards to existing
    `nucleus_sync.identify_agent` legacy implementation (writes
    `.brain/agent_registry/<id>.json`). M1 swaps to registry-of-truth per
    ADR 0006 — same action contract, real schema underneath."""
    try:
        from .sync import _identify_agent  # type: ignore[attr-defined]
    except ImportError:
        # Fallback: manual write for v0.2 forward-compat smoke test
        registry = _repo_root() / ".brain" / "agent_registry"
        registry.mkdir(parents=True, exist_ok=True)
        agent_id = f"{role}_{int(time.time())}"
        record = {
            "agent": role,
            "provider": provider,
            "role": "primary",
            "session_id": parent_session_id or agent_id,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "last_heartbeat": datetime.now(timezone.utc).isoformat(),
            "heartbeat_interval_s": 30,
            "primitive_version": "1",
            "capabilities": capabilities or [],
        }
        path = registry / f"{agent_id}.json"
        path.write_text(json.dumps(record, indent=2))
        return _ok({
            "agent_id": agent_id,
            "session_id": record["session_id"],
            "registry_path": str(path),
            "v0_2_note": "fallback path; forwards to nucleus_sync.identify_agent in production",
        })
    # If the import succeeded, forward to the legacy handler
    raw = _identify_agent(
        agent_id=role,
        environment="claude_code",
        role=role,
    )
    return _ok({"forwarded": True, "raw": raw})


def resolve_identity(session_id: Optional[str] = None,
                     agent_role: Optional[str] = None) -> str:
    """Look up identity from `.brain/agent_registry/` (v0.2) or registry-of-truth
    (M1+). Returns first match by `(session_id | agent_role)`. v0.2 caveat:
    the registry is incomplete and stale (audit confirmed 100% of live
    surfaces unregistered) — use this for forward-compat probing only."""
    if not session_id and not agent_role:
        return _err("MISSING_KEY",
                    "supply either session_id or agent_role")
    registry = _repo_root() / ".brain" / "agent_registry"
    if not registry.exists():
        return _ok({"matches": [], "note": "registry empty"})
    matches: List[Dict[str, Any]] = []
    for f in registry.glob("*.json"):
        try:
            d = json.loads(f.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if session_id and d.get("session_id") != session_id:
            continue
        if agent_role and d.get("role") != agent_role and d.get("agent") != agent_role:
            continue
        matches.append({
            "agent": d.get("agent"),
            "role": d.get("role"),
            "provider": d.get("provider"),
            "session_id": d.get("session_id"),
            "last_heartbeat": d.get("last_heartbeat"),
            "registry_path": str(f),
        })
    return _ok({"matches": matches, "count": len(matches)})


def heartbeat(session_id: str) -> str:
    """Touch the matching `.brain/agent_registry/*.json` entry's
    `last_heartbeat`. v0.2: stub — finds entries by `session_id` match
    and rewrites timestamp. M1 swaps to registry transactional update."""
    registry = _repo_root() / ".brain" / "agent_registry"
    if not registry.exists():
        return _err("NO_REGISTRY", "agent_registry not found")
    now_iso = datetime.now(timezone.utc).isoformat()
    touched = []
    for f in registry.glob("*.json"):
        try:
            d = json.loads(f.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if d.get("session_id") != session_id:
            continue
        d["last_heartbeat"] = now_iso
        f.write_text(json.dumps(d, indent=2))
        touched.append(str(f))
    if not touched:
        return _err("NOT_FOUND",
                    f"no registry entry matches session_id={session_id!r}",
                    hint="call identify_agent first")
    return _ok({"updated": touched, "last_heartbeat": now_iso})


# ─── Dispatcher ─────────────────────────────────────────────────────────


_ROUTER = {
    # Execution
    "fire_sync":     lambda brief, lane=None, model="sonnet", charter=None, parent_session_id=None, timeout_s=300:
                       fire_sync(brief, lane, model, charter, parent_session_id, timeout_s),
    "fire_pair":     lambda lane, brief, model="sonnet", subject=None, parent_session_id=None:
                       fire_pair(lane, brief, model, subject, parent_session_id),
    "fire_doc":      lambda path, phase="scout", model="haiku":
                       fire_doc(path, phase, model),
    # Pair lifecycle
    "pair_start":    lambda lane, charter_path=None: pair_start(lane, charter_path),
    "pair_stop":     lambda lane:                    pair_stop(lane),
    "pair_status":   lambda lane=None:               pair_status(lane),
    # Telemetry
    "audit_cost":          lambda window_hours=24.0, group_by="pair":
                              audit_cost(window_hours, group_by),
    "audit_utilization":   lambda lane=None:        audit_utilization(lane),
    "audit_events":        lambda since=None, type_filter=None, limit=100:
                              audit_events(since, type_filter, limit),
    # Authority
    "authority_check":     lambda brief, subject="": authority_check(brief, subject),
    "authority_keywords":  lambda:                    authority_keywords(),
    # Identity (forward-compat stubs; M1 swaps real impl)
    "identify_agent":      lambda role, parent_session_id=None, capabilities=None, provider="anthropic_claude_code":
                              identify_agent(role, parent_session_id, capabilities, provider),
    "resolve_identity":    lambda session_id=None, agent_role=None:
                              resolve_identity(session_id, agent_role),
    "heartbeat":           lambda session_id:        heartbeat(session_id),
    # Bootstrap (v0.3 — cold-start unblock)
    "init":                lambda template="solo", brain_path=None: init(template, brain_path),
}


# Actions that operate on the workspace itself (init) or that should NOT trigger
# the auto-bootstrap pre-dispatch (e.g. read-only inspections that should
# transparently report "no workspace yet" without silently creating one).
_SKIP_AUTO_BOOTSTRAP: set = {"init"}


def dispatch(action: str, params: Optional[Dict[str, Any]] = None) -> str:
    """Single dispatch entrypoint — used by both the MCP tool and
    smoke-test harnesses.

    v0.3: pre-dispatch step ensures `.brain/` exists (auto-bootstrap with
    stdout muted to avoid corrupting JSON-RPC stdio frames). Adds
    `auto_initialized` + `workspace` metadata to the response envelope.
    """
    if action not in _ROUTER:
        valid_actions = sorted(_ROUTER.keys())
        return _err("UNKNOWN_ACTION",
                    f"action {action!r} not in registered actions",
                    valid_actions=", ".join(valid_actions))
    handler = _ROUTER[action]
    params = params or {}

    # v0.3 pre-dispatch: auto-bootstrap workspace unless action handles it itself.
    bootstrap_meta: Dict[str, Any] = {}
    if action not in _SKIP_AUTO_BOOTSTRAP:
        ws_meta = _ensure_workspace()
        if "error" in ws_meta:
            return _err(ws_meta["error"],
                        f"workspace setup failed at {ws_meta.get('workspace')}",
                        workspace=ws_meta.get("workspace"),
                        detail=ws_meta.get("detail"))
        bootstrap_meta = ws_meta  # {workspace, auto_initialized}

    try:
        raw = handler(**params)
    except TypeError as e:
        return _err("INVALID_PARAMS", str(e), action=action)
    except Exception as e:
        return _err("HANDLER_FAILED", f"{type(e).__name__}: {e}", action=action)

    # Stamp bootstrap metadata onto the response envelope (additive, top-level).
    if bootstrap_meta:
        try:
            decoded = json.loads(raw)
            decoded.update(bootstrap_meta)
            return json.dumps(decoded, indent=2, default=str)
        except (json.JSONDecodeError, TypeError):
            return raw  # handler returned non-JSON; pass through unchanged
    return raw


# ─── MCP tool registration ───────────────────────────────────────────────


def register(mcp, helpers):
    """Register the `nucleus_delegate` MCP tool with the server."""
    @mcp.tool()
    def nucleus_delegate(action: str, params: dict = {}) -> str:
        """Singular endpoint for the Nucleus-Delegate substrate.

Actions (15 in 6 groups, v0.3):

  ── Execution ──
  fire_sync         L1 ephemeral sub-agent. params: {brief, lane?, model?, charter?, parent_session_id?, timeout_s?}
  fire_pair         L3 async via running pair. params: {lane, brief, model?, subject?, parent_session_id?}
  fire_doc          L1-USING doc pipeline. params: {path, phase: "scout"|"synthesize", model?}

  ── Pair lifecycle ──
  pair_start        Boot daemon for a lane. params: {lane: "peer"|"main", charter_path?}
  pair_stop         Graceful SIGTERM. params: {lane}
  pair_status       Read pid + heartbeat + queue depth. params: {lane?}

  ── Telemetry ──
  audit_cost        Proxy-token rollup. params: {window_hours?, group_by: "pair"|"role"}
  audit_utilization Pair busy% + ≥40% gate flag. params: {lane?}
  audit_events      Raw events filter. params: {since?, type_filter?, limit?}

  ── Authority ──
  authority_check   Preflight: would this brief escalate? params: {brief, subject?}
  authority_keywords Full keyword list. params: {}

  ── Identity (v0.2 forward-compat; M1 build per ADR 0006 swaps real impl) ──
  identify_agent    Register session identity. params: {role, parent_session_id?, capabilities?, provider?}
  resolve_identity  Look up by session_id or agent_role. params: {session_id?, agent_role?}
  heartbeat         Touch last_heartbeat. params: {session_id}

  ── Bootstrap (v0.3) ──
  init              Cold-start workspace setup. params: {template?: "solo"|"default"|"v0", brain_path?}

Returns JSON envelope: {"ok": bool, "data": {...} | null, "error": {code, message} | null}
plus optional v0.3 metadata: {workspace, auto_initialized}.

Single substrate; multiple ergonomic fronts (CC slash skills, CLI scripts) call through this.
v0.3 auto-bootstraps `.brain/` on cold start so vibe-coder workspaces work out of the box.
"""
        return dispatch(action, params)

    return [("nucleus_delegate", nucleus_delegate)]
