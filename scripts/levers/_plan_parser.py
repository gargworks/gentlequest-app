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
    r"## (?:\d+\.\s+)?(?:Files Modified|Files Changed|Affected Files)\s*\n"
    r"((?:(?!^## ).*\n?)*)",
    re.MULTILINE,
)
_VERIFICATION_HEADER_RE = re.compile(
    r"## (?:\d+\.\s+)?Verification[^\n]*\n", re.MULTILINE
)
_PATH_SHAPE_RE = re.compile(r"[\w./\-]+\.\w+")
_TABLE_BACKTICK_RE = re.compile(r"`([\w./\-]+\.\w+)`")
_LINE_STRIP_RE = re.compile(r"^[-*]\s*`?|`?\s*[—|].*$|`")


def extract_modified_files(plan_text: str) -> List[str]:
    """Return paths listed under `## Files Modified` or `## Affected Files`.

    Mirrors TB's stripping rules:
      1. Strip leading bullet markers `^[-*]\\s*`, optional backticks, and
         everything after an em-dash or table cell separator.
      2. If that produces a non-path-shaped string, look for a backtick-
         wrapped path inside the line (table-row case).
      3. Drop lines that don't end with a `.ext` shape.

    Returns an empty list when the section is missing or contains no
    parseable paths (R2: empty section is the same observable signal as
    missing section to downstream classifiers).
    """
    files_match = _FILES_HEADER_RE.search(plan_text)
    if not files_match:
        return []
    paths: List[str] = []
    for line in files_match.group(1).splitlines():
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
