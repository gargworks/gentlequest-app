"""Tier 2 sovereignty pass — strip local-machine state from digest content.

Before any TB-curated digest content lands at the path Claude Code reads (and
ultimately forwards to the Anthropic API), this module strips:

  - Absolute home paths matching ^/Users/<user>/ or ^/home/<user>/ or
    ^/private/var/folders/...
  - Inode numbers (typically appear in `find` / `stat` output)
  - Absolute timestamps in ISO-8601 form (e.g., 2026-05-01T01:23:45.123456Z)
  - UUID-shaped strings (sessions ids, etc.) that aren't part of curated content
  - Git ref SHAs (40- or 7-char hex) unless they're in the curated form
    "PR #N (sha XXXXX)" or "commit `XXXXX`" which Lokesh's memos use

Sovereignty axiom (per project_family_private.md): Tier 2 must not leak
local-machine state to the upstream API even via injected context. This module
is the enforcement.

Per .brain/research/2026-04-28_tier_architecture/08_tier2_design.md
Component 3 sub-step 3a — discrete, testable, named.
"""
from __future__ import annotations

import re

# Absolute home / system paths
_PATH_USER_HOME = re.compile(r"/Users/[a-zA-Z][\w.-]*", re.IGNORECASE)
_PATH_LINUX_HOME = re.compile(r"/home/[a-zA-Z][\w.-]*", re.IGNORECASE)
_PATH_PRIVATE_FOLDERS = re.compile(r"/private/var/folders/[\w/.-]+")

# Inode patterns: `find` / `stat` typically prefixes inode in formats like
# "12345678 ./file.txt" or "ino=12345678". Conservative: match "ino=NNNNNNN"
# and standalone integer ≥7 digits at line start (could be either inode or
# turn-counter; bias toward redaction).
_INODE_FIELD = re.compile(r"\bino=\d{6,}\b")

# Absolute ISO-8601 timestamps (with date, time, optional fractional seconds, optional TZ).
_ISO_TIMESTAMP = re.compile(
    r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?(?:Z|[+\-]\d{2}:?\d{2})\b"
)

# UUID v4-shaped (session ids, relay ids etc.). Match standalone, NOT inside
# the curated phrasing "relay_<timestamp>_<id>" which Lokesh's substrate uses
# legitimately. We strip the bare UUID; we keep relay_* references.
_BARE_UUID = re.compile(
    r"\b(?<!relay_)(?<!relay_\d{8}_\d{6}_)"
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)

# Git SHAs: 40-char or 7-char hex. Curated forms keep the SHA in context
# ("PR #188 (sha d8293e52)" or "commit `61da48e3`"). Bare SHAs not in either
# curated frame get stripped.
_BARE_SHA40 = re.compile(
    r"(?<![`#a-z(])(?<!sha )"
    r"\b[0-9a-f]{40}\b"
)
_BARE_SHA7 = re.compile(
    r"(?<![`#a-z(])(?<!sha )"
    r"\b[0-9a-f]{7,12}\b"
)

# Conservative: leave SHA stripping off by default — too many false positives
# with hex-ish identifiers. Re-enable if leak audits surface SHAs in flight.


def strip_local_state(text: str, *, redact_shas: bool = False) -> str:
    """Apply all strip passes. Returns redacted copy; does not mutate input.

    Each replaced occurrence is substituted with a stable placeholder so the
    digest's structure stays readable.

        /Users/lokesh/foo/bar.py     -> <user-home>/foo/bar.py
        /home/lokesh/foo             -> <user-home>/foo
        /private/var/folders/xx/yyy  -> <macos-tmp>
        ino=12345678                 -> ino=<inode>
        2026-05-01T01:23:45.123Z     -> <iso-timestamp>
        f6b976a1-...-af7d6be2633d    -> <uuid>
        SHAs (if redact_shas=True)   -> <sha>
    """
    if not text:
        return ""
    out = text
    out = _PATH_USER_HOME.sub("<user-home>", out)
    out = _PATH_LINUX_HOME.sub("<user-home>", out)
    out = _PATH_PRIVATE_FOLDERS.sub("<macos-tmp>", out)
    out = _INODE_FIELD.sub("ino=<inode>", out)
    out = _ISO_TIMESTAMP.sub("<iso-timestamp>", out)
    out = _BARE_UUID.sub("<uuid>", out)
    if redact_shas:
        out = _BARE_SHA40.sub("<sha>", out)
        out = _BARE_SHA7.sub("<sha>", out)
    return out
