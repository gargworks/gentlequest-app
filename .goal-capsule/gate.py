#!/usr/bin/env python3
"""
gate.py -- enforcement for a repo's own .goal-capsule.md, adapted from this
codebase's proven alignment_gate.py (see
.brain/strategy/north_star/agent_integration/alignment_gate.py for the
original -- same mark/check shape, same kill-switch-before-stdin order, same
fail-open policy, same 24h stale self-rescue). The logic is NOT rewritten
here, only re-pointed: alignment_gate.py enforces re-entry through a
memory-substrate capsule reachable at a fixed $HOME path on one machine;
this file enforces re-entry through a capsule that lives INSIDE the target
repo (.goal-capsule.md) and stores its own state inside the repo's own .git
directory, so it needs no HOME writes and works for a stranger who has never
heard of this codebase.

WHY THIS EXISTS: a person runs a long AI session toward a real goal; every
compaction or session restart loses the alignment even though the summary
still carries the facts (files touched, commands run). "Re-read the capsule
first" as a voluntary instruction is exactly the failure family this
discipline refuses -- a correct instruction, silently skipped, reads
identical to one that was followed. This script is an external process,
outside the model's own judgment, structurally unable to be talked out of
the check.

DEFECT FIXES (peer review under production stakes, 2026-08-09 -- see
hook_design.md's "## ALIGNMENT GATE" section, "Defect fixes" subsection, for
the full writeup): two real bugs were found and closed here.

  DEFECT 1 (substring unlock): the unlock used to be
  `_CAPSULE_FILENAME in file_path` -- any path merely CONTAINING the capsule
  filename as a substring unlocked, without the capsule ever being read
  ("an instrument satisfiable without doing the thing", the reviewer's own
  words). Fixed: resolved-PATH EQUALITY (`Path(file_path).resolve() ==
  capsule_path.resolve()`). A resolve failure on either side counts as
  NO-match, never as a match -- see `_matches_capsule_path()`.

  DEFECT 2 (shared marker, per-session condition): the marker file used to
  be a single per-repo path -- `mark()` wrote `session_id` into its payload
  but `check()` never read it, so concurrent sessions shared ONE marker.
  Session A reading the capsule unlocked session B, which had re-read
  nothing ("Session B is now unblocked having re-read nothing -- and B is
  the session that most needed the gate"). Fixed: the marker FILENAME is
  now keyed by session id (`capsule_unread.<session_id>`); `mark()` uses the
  SessionStart event's session_id, `check()` uses the PreToolUse event's
  session_id, and each only ever consults/clears its OWN marker. An event
  with a missing or unsafe session_id fails OPEN with a stderr warning
  (infra ambiguity, not a block) -- see `_valid_session_id()`. Every unlock
  now also logs the session_id to stderr, so a false pass leaves a
  greppable trace (the reviewer's own suggested mitigation). The 24h stale
  sweep now reaps ANY session's leftover marker files (a session that died
  without ever re-reading would otherwise leak its marker forever, since
  only that session's own `check()` calls would ever look at it) without
  touching -- reading, deleting, or otherwise disturbing -- any other
  session's still-fresh marker.

TWO MODES, selected by argv[1]:

  mark  -- wired as a SessionStart hook (matcher: source in
           startup|resume|compact -- see settings_snippet.json in this
           directory). Reads the SessionStart hook stdin JSON and writes a
           session-keyed marker file at
           <state_dir>/capsule_unread.<session_id>. SessionStart hooks
           CANNOT block a session from starting -- this mode ALWAYS exits 0,
           no matter what happens internally (bad stdin, unwritable state
           dir, missing session_id, anything). Breaking session start would
           be strictly worse than a missed mark.

  check -- wired as a PreToolUse hook (all tools -- see the settings
           snippet). If THIS session's own marker is present, every tool
           call except reading the capsule file itself (matched by resolved
           path, see DEFECT 1 above) is BLOCKED (exit 2) with a stderr
           message telling the agent exactly what to do. The unlock action
           deletes the marker, logs the session_id, and exits 0.

CAPSULE PATH: <repo root>/.goal-capsule.md. Repo root is resolved at
runtime -- never hardcoded -- from $CLAUDE_PROJECT_DIR if set (the
convention Claude Code hooks already use to locate the project), else via
`git rev-parse --show-toplevel` run from the current working directory,
else the current working directory itself as a last resort. Override with
GOAL_GATE_CAPSULE_PATH if the capsule needs to live somewhere else.

The capsule path is DETERMINISTIC (it does not depend on the file actually
existing on disk) -- which is what lets a Read ATTEMPT of the correct path
unlock even when the capsule file itself is missing (DEFECT 3, see the
comment at the unlink site in check() and controls.sh case (k)). This was
true before the review too, but incidentally (a lucky consequence of
comparing strings), not by design; it is now an explicit, tested property
of `_matches_capsule_path()`, which never requires the target file to
exist.

STATE DIR: <repo root>/.git/goal-gate/ (created on demand) -- inside the
repo's own git metadata, so this needs no writes outside the repo and no
$HOME at all. Override with GOAL_GATE_STATE_DIR.

KILL SWITCH (check mode only): GOAL_GATE_DISABLED=1 -> exit 0, checked
BEFORE stdin is read, mirroring alignment_gate.py's
NUCLEUS_ALIGNMENT_GATE_DISABLED convention exactly.

FAIL-OPEN POLICY -- same reasoning as alignment_gate.py, restated for this
repo-local context: this gate sits in front of EVERY tool call for the rest
of the session once triggered. A bug here does not miss one thing, it can
brick an entire session's ability to do any work at all. Bricking a live
session over this script's own infra hiccup (garbage stdin, an
unwritable/unreadable state dir, a stale marker nobody will ever clear, a
missing/unsafe session_id) is a worse failure than occasionally missing the
enforcement, so EVERY infra-shaped failure in `check` mode fails OPEN with a
stderr WARNING -- never silent, always logged, but never blocking.

Grace / self-rescue: a marker older than 24h is treated as stale (the
session that set it is long gone, or the gate itself is stuck) -- deleted,
exit 0, stderr WARNING. Since DEFECT 2's fix, this sweep runs across every
session's marker files in the state dir (not just the current session's
own), so a session that dies mid-block does not leak its marker forever --
but it only ever DELETES markers found to be stale; a fresh marker
belonging to a different, still-live session is never read for a gating
decision and never touched.

WHAT THIS GATE STILL CANNOT ENFORCE: it can force the RE-READ (a Read tool
call actually reaching .goal-capsule.md) -- it cannot force the WEIGHT to
land. An agent can satisfy this gate with a fast, distracted skim and
immediately resume drifting; syntactic compliance is not semantic
re-alignment. That gap is named here, not papered over -- see this kit's
README.md "the honest limit" section.

macOS BSD-safe: pure stdlib (json / os / re / subprocess / sys / time /
pathlib) -- no GNU-only CLI flags, no third-party packages, no network
calls.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

_KILL_SWITCH_ENV = "GOAL_GATE_DISABLED"
_STATE_DIR_ENV = "GOAL_GATE_STATE_DIR"
_CAPSULE_PATH_ENV = "GOAL_GATE_CAPSULE_PATH"
_PROJECT_DIR_ENV = "CLAUDE_PROJECT_DIR"
_MARKER_NAME = "capsule_unread"
_CAPSULE_FILENAME = ".goal-capsule.md"
_STALE_SECONDS = 24 * 60 * 60  # 24h self-rescue window

# Session ids are expected to be UUID-ish strings (Claude Code's own hook
# stdin JSON), but this is also a filename component (DEFECT 2 fix: the
# marker filename is keyed by session_id), so it is validated against a safe
# allow-list charset before ever touching a path -- no "/", no raw ".." as a
# whole segment (it can never BE a whole path segment here because it is
# always concatenated after the literal "capsule_unread." prefix), bounded
# length. A session_id that fails this check is treated exactly like a
# missing one -- infra ambiguity, fail open with a warning, never a block
# and never a silent shared/default bucket (that would just reintroduce
# DEFECT 2 at a smaller scale).
_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,256}$")


def _valid_session_id(session_id: Optional[str]) -> bool:
    return isinstance(session_id, str) and bool(_SESSION_ID_RE.match(session_id))


def _repo_root() -> Path:
    """Resolve the target repo root without ever hardcoding a path. Prefers
    $CLAUDE_PROJECT_DIR (the variable Claude Code hooks already export for
    this exact purpose), falls back to `git rev-parse --show-toplevel` from
    the current working directory, falls back to the cwd itself so this
    never raises -- an unresolved root just means state/capsule land under
    the process's own cwd, which fail-open handling downstream tolerates."""
    env_dir = os.environ.get(_PROJECT_DIR_ENV)
    if env_dir:
        return Path(env_dir)
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        top = result.stdout.strip()
        if result.returncode == 0 and top:
            return Path(top)
    except Exception:
        pass
    return Path.cwd()


def _capsule_path() -> Path:
    override = os.environ.get(_CAPSULE_PATH_ENV)
    if override:
        return Path(override)
    return _repo_root() / _CAPSULE_FILENAME


def _state_dir() -> Path:
    override = os.environ.get(_STATE_DIR_ENV)
    if override:
        return Path(override)
    return _repo_root() / ".git" / "goal-gate"


def _marker_path(state_dir: Path, session_id: str) -> Path:
    # DEFECT 2 fix: filename keyed by session_id, not a single shared name.
    return state_dir / f"{_MARKER_NAME}.{session_id}"


def _matches_capsule_path(file_path: str) -> bool:
    """DEFECT 1 fix: resolved-path EQUALITY, not substring containment. A
    decoy path that merely CONTAINS ".goal-capsule.md" as a substring (e.g.
    "notes-on-.goal-capsule.md-design.txt") must NOT match. A resolve
    failure on either side (permission error walking a parent dir, symlink
    loop, etc.) is treated as NO-match -- it falls through to BLOCK, never
    to a false unlock.

    DEFECT 3, made designed rather than lucky: Path.resolve() defaults to
    strict=False, which does NOT raise when the target does not exist on
    disk -- it resolves as far as it can and appends the rest literally.
    That is what lets a Read ATTEMPT of the correct capsule path unlock even
    when .goal-capsule.md has never been written or was deleted -- see the
    explicit test for this in controls.sh case (k)."""
    if not file_path:
        return False
    try:
        candidate = Path(file_path).resolve()
    except Exception:
        return False
    try:
        target = _capsule_path().resolve()
    except Exception:
        return False
    return candidate == target


def _sweep_stale_markers(state_dir: Path) -> None:
    """Best-effort reap of ANY session's marker file older than the 24h
    self-rescue window. Runs on every check() call (not just when the
    current session's own marker happens to be stale) because -- since
    DEFECT 2 keyed the marker filename by session_id -- a session that dies
    without ever calling check() again would otherwise leak its own marker
    forever; nobody else's check() call ever looks at another session's
    marker for a gating DECISION, but this sweep still needs to clean it up
    eventually. Only STALE files are ever deleted; a fresh marker belonging
    to a different, still-live session is left completely alone. Wrapped so
    that no exception here can ever propagate -- a sweep is a courtesy, not
    part of the authoritative block/pass decision, which is made afterward
    by looking at ONLY the current session's own marker."""
    try:
        if not state_dir.exists():
            return
        for candidate in state_dir.glob(f"{_MARKER_NAME}.*"):
            try:
                age_seconds = time.time() - candidate.stat().st_mtime
                if age_seconds > _STALE_SECONDS:
                    candidate.unlink(missing_ok=True)
                    print(
                        f"goal gate WARNING -- reaped stale marker {candidate} "
                        f"({age_seconds / 3600:.1f}h old, >24h self-rescue window).",
                        file=sys.stderr,
                    )
            except Exception:
                pass  # one bad file must never stop the sweep or block this call
    except Exception:
        pass


def _read_stdin_event() -> Dict[str, Any]:
    """Parse hook stdin JSON. Raises on any failure -- callers decide how to
    handle it (mark: swallow, always exit 0; check: fail OPEN with a
    warning, per this gate's documented fail-open default)."""
    raw = sys.stdin.read()
    event = json.loads(raw)
    if not isinstance(event, dict):
        raise ValueError(f"hook stdin event must be a JSON object, got {type(event).__name__}")
    return event


# ---------------------------------------------------------------------------
# mark -- SessionStart hook. MUST always return 0; every internal failure is
# swallowed after being warned about on stderr, never raised past main().
# ---------------------------------------------------------------------------

def mark() -> int:
    try:
        event = _read_stdin_event()
    except Exception as exc:
        print(
            f"goal gate WARNING (mark) -- SessionStart stdin did not parse "
            f"({type(exc).__name__}: {exc}); no marker written this session, "
            "but session start is never blocked.",
            file=sys.stderr,
        )
        return 0

    session_id = event.get("session_id")
    source = event.get("source") or "unknown"  # startup | resume | compact | clear

    if not _valid_session_id(session_id):
        # DEFECT 2 fix: do NOT fall back to a shared/default bucket like the
        # old "unknown" -- that would just reintroduce the shared-marker
        # false-pass for every session missing (or with a malformed)
        # session_id. Skip writing a marker instead; session start still
        # always proceeds.
        print(
            f"goal gate WARNING (mark) -- SessionStart event has a missing or "
            f"unsafe session_id ({session_id!r}); no marker written (a marker "
            "without a valid session key would collide with every other "
            "session in the same situation). Session start proceeds unmarked.",
            file=sys.stderr,
        )
        return 0

    try:
        state_dir = _state_dir()
        state_dir.mkdir(parents=True, exist_ok=True)
        marker = _marker_path(state_dir, session_id)
        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "session_id": session_id,
            "source": source,
        }
        marker.write_text(json.dumps(payload) + "\n")
    except Exception as exc:
        print(
            f"goal gate WARNING (mark) -- could not write marker "
            f"({type(exc).__name__}: {exc}); state dir may be unwritable. "
            "Session start proceeds unmarked.",
            file=sys.stderr,
        )
        return 0

    return 0


# ---------------------------------------------------------------------------
# check -- PreToolUse hook. Fails OPEN on every infra-shaped failure (see
# module docstring "FAIL-OPEN POLICY"); the only path that BLOCKS is a fresh
# marker (for THIS session) plus a tool call that isn't the designated
# unlock.
# ---------------------------------------------------------------------------

def check() -> int:
    # Checked before anything else, including before stdin is read -- same
    # convention as alignment_gate.py's NUCLEUS_ALIGNMENT_GATE_DISABLED.
    if os.environ.get(_KILL_SWITCH_ENV) == "1":
        return 0

    try:
        event = _read_stdin_event()
    except Exception as exc:
        print(
            f"goal gate WARNING -- PreToolUse stdin did not parse "
            f"({type(exc).__name__}: {exc}); failing open (this gate fails "
            "open on infra breakage, not closed -- see module docstring).",
            file=sys.stderr,
        )
        return 0

    tool_name = event.get("tool_name") or ""
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}

    session_id = event.get("session_id")
    if not _valid_session_id(session_id):
        # DEFECT 2 fix: with no valid session_id we cannot know which
        # session's marker to consult -- that is infra ambiguity, not a
        # reason to block, and NOT a reason to fall back to a shared marker.
        print(
            f"goal gate WARNING -- PreToolUse event has a missing or unsafe "
            f"session_id ({session_id!r}); cannot resolve which session's "
            "marker to check; failing open.",
            file=sys.stderr,
        )
        return 0

    state_dir = _state_dir()

    # Best-effort stale-marker sweep across ALL sessions (see
    # _sweep_stale_markers docstring) -- runs before the authoritative
    # decision below, which still looks at nothing but this session's own
    # marker.
    _sweep_stale_markers(state_dir)

    marker = _marker_path(state_dir, session_id)

    try:
        marker_exists = marker.exists()
    except Exception as exc:
        print(
            f"goal gate WARNING -- could not stat marker at {marker} "
            f"({type(exc).__name__}: {exc}); failing open.",
            file=sys.stderr,
        )
        return 0

    if not marker_exists:
        return 0

    # The one unlock: the agent is reading the capsule file itself, matched
    # by resolved-path equality (DEFECT 1 fix) -- see _matches_capsule_path().
    if tool_name == "Read":
        file_path = tool_input.get("file_path") or ""
        if _matches_capsule_path(file_path):
            try:
                marker.unlink(missing_ok=True)
            except Exception as exc:
                print(
                    f"goal gate WARNING -- capsule Read matched but could not "
                    f"delete marker at {marker} ({type(exc).__name__}: {exc}); "
                    "allowing this call anyway (failing open), marker may persist.",
                    file=sys.stderr,
                )
            # DEFECT 2 mitigation (reviewer's own suggestion): log the
            # session_id on every unlock, so a false pass still leaves a
            # greppable trace even if the marker-keying logic above has a
            # bug nobody has found yet.
            print(f"goal gate: unlocked session {session_id} via capsule Read", file=sys.stderr)
            return 0

    # No unlock matched, marker fresh: BLOCK.
    print(
        "goal gate: your agent resumed from a context reset -- it must "
        f"re-read {_capsule_path()} before working; summaries carry facts, "
        "not weight.",
        file=sys.stderr,
    )
    return 2


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "mark":
        return mark()
    if mode == "check":
        return check()
    print(
        f"gate.py: unknown or missing mode {mode!r} -- expected 'mark' "
        "(SessionStart) or 'check' (PreToolUse) as argv[1].",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
