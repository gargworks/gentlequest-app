"""Shared plan-markdown parser for lever + TB code.

Extracts file paths and section presence from plan text. The parsing
contract here MUST match TB's `_auto_verification_commands` byte-for-byte
so the Wave 9 delegation is a behavior-preserving refactor.

R1 (HOLD-scope review, revised 2026-04-13): headers scanned are
`## Files Modified`, `## Files Changed`, and `## Affected Files`, each
with an optional numbered prefix (`## 4. Files Modified`). The
numbered+Changed variants were added after the plan_audit lever's live-
fire surfaced ultraplan-style plans using `## 4. Files Changed` /
`## 6. Verification Sequence` — the prior contract classified them as
`unverifiable` despite carrying the actual sections. Prose `**Files:**`
patterns and the `## Changes` fallback used by TB's task-spawn path are
NOT mirrored here — those are TB's concern, not the lever's.
"""

from __future__ import annotations

import re
from typing import List


_FILES_HEADER_RE = re.compile(
    r"^## (?:\d+\.\s+)?(?:Files Modified|Files Changed|Affected Files)\s*\n"
    r"((?:(?!^## ).*\n?)*)",
    re.MULTILINE,
)
_VERIFICATION_HEADER_RE = re.compile(
    r"^## (?:\d+\.\s+)?Verification[^\n]*\n", re.MULTILINE
)
_VERIFICATION_SECTION_RE = re.compile(
    r"^## (?:\d+\.\s+)?Verification[^\n]*\n((?:(?!^## ).*\n?)*)",
    re.MULTILINE,
)
_PATH_SHAPE_RE = re.compile(r"[\w./\-]+\.\w+")
_TABLE_BACKTICK_RE = re.compile(r"`([\w./\-]+\.\w+)`")
_LINE_STRIP_RE = re.compile(r"^[-*]\s*`?|`?\s*[—|].*$|`")
_BOLD_SUBSECTION_RE = re.compile(r"^\*\*[^*]+\*\*\s*$")
_BASH_FENCE_LANGS = frozenset({"", "bash", "sh", "shell"})


def extract_modified_files(plan_text: str) -> List[str]:
    """Return paths listed under `## Files Modified` or `## Affected Files`.

    Mirrors TB's stripping rules:
      1. Strip leading bullet markers `^[-*]\\s*`, optional backticks, and
         everything after an em-dash or table cell separator.
      2. If that produces a non-path-shaped string, look for a backtick-
         wrapped path inside the line (table-row case).
      3. Drop lines that don't end with a `.ext` shape.
      4. Stop scanning on a bold-only sub-section marker (e.g.
         `**Explicitly NOT touching:**`). Prevents exclusion lists that
         live under the same `## Files Modified` header from leaking
         paths into drift_detected downstream.

    Returns an empty list when the section is missing or contains no
    parseable paths (R2: empty section is the same observable signal as
    missing section to downstream classifiers).
    """
    files_match = _FILES_HEADER_RE.search(plan_text)
    if not files_match:
        return []
    paths: List[str] = []
    for line in files_match.group(1).splitlines():
        if _BOLD_SUBSECTION_RE.match(line.strip()):
            break
        path = _LINE_STRIP_RE.sub("", line).strip()
        if not path or not _PATH_SHAPE_RE.match(path):
            tbl = _TABLE_BACKTICK_RE.search(line)
            if tbl:
                path = tbl.group(1)
            else:
                continue
        if not _PATH_SHAPE_RE.match(path):
            continue
        paths.append(path)
    return paths


def has_files_modified_section(plan_text: str) -> bool:
    """True iff `## Files Modified` or `## Affected Files` header present."""
    return _FILES_HEADER_RE.search(plan_text) is not None


def has_verification_section(plan_text: str) -> bool:
    """True iff `## Verification` header present (any trailing chars)."""
    return _VERIFICATION_HEADER_RE.search(plan_text) is not None


def has_runnable_verification_section(plan_text: str) -> bool:
    """True iff `## Verification` section contains ≥1 fenced bash code block.

    Stricter than :func:`has_verification_section` — the header alone is
    not enough. The section must contain at least one ```...``` fence
    opened with no language marker OR bash/sh/shell, representing a
    block the audit runner can execute as a script.

    Rationale: plans like snowglobe.md carry a rich ``## Verification
    (per wave)`` section full of inline-backticked commands (e.g. ```
    `pytest -q` ``` embedded in numbered prose) but zero fenced blocks.
    Those commands look runnable to a human reader but the audit
    subprocess sees no structured verification and records
    ``verification_quality="none"`` — the silent rubber-stamp path.
    Requiring a fenced block forces the plan author to commit to a
    script the verifier can actually invoke.

    Used by ``third_brother_driver.run_plan_audit_mode``'s UNVERIFIABLE
    short-circuit. :func:`has_verification_section` stays available for
    callers that only need header presence (e.g. the plan_audit lever's
    ``unverifiable`` bucket, which should trip when BOTH sections are
    header-missing — not when one is header-only-but-stubbed).
    """
    m = _VERIFICATION_SECTION_RE.search(plan_text)
    if not m:
        return False
    state = "outside"
    for line in m.group(1).split("\n"):
        stripped = line.strip()
        if not stripped.startswith("```"):
            continue
        if state == "outside":
            lang = stripped[3:].strip().lower()
            state = "inside_bash" if lang in _BASH_FENCE_LANGS else "inside_other"
        else:
            if state == "inside_bash":
                return True
            state = "outside"
    return False
