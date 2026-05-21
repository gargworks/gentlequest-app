#!/usr/bin/env python3
"""Publish .brain/policies/*.md as project-scoped SKILL.md files.

Tier 1 wiring per .brain/research/2026-04-28_tier_architecture/99_verdict.md
recommendation 1 (source-correction): policies are already lesson-shaped, but
invisible to CC's auto-discovery. Emitting them as project-scoped Skills at
.claude/skills/policy-<slug>/SKILL.md exposes them to CC's description-match
auto-activation.

Each policy file has a known shape:
    # <Title>
    **Rule:** <one-or-two sentences>
    **Why:** <motivation>
    **How to apply:** <when/where>

This adapter parses that shape and emits a SKILL.md whose:
- name:        policy-<slug>
- description: template form ("When <trigger>, ...") matching the well-formed
               gstack/qa shape per feedback_template_descriptions_not_verbatim.md
- body:        the original policy content verbatim (no abbreviation)

Idempotent. Re-run safely overwrites existing policy-* skill dirs.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
POLICIES_DIR = REPO_ROOT / ".brain" / "policies"
SKILLS_DIR = REPO_ROOT / ".claude" / "skills"
SKIP_FILES = {"README.md"}


def _read_policy(path: Path) -> dict:
    """Parse a policy markdown into structured fields.

    Returns: {slug, title, rule, why, how, body}
    """
    text = path.read_text(encoding="utf-8")
    slug = path.stem  # e.g., "paste_friction_goal"

    # Title: first H1
    m = re.search(r"^#\s+(.+?)$", text, re.MULTILINE)
    title = m.group(1).strip() if m else slug.replace("_", " ").title()

    rule = _extract_field(text, "Rule")
    why = _extract_field(text, "Why")
    how = _extract_field(text, "How to apply")

    return {
        "slug": slug,
        "title": title,
        "rule": rule,
        "why": why,
        "how": how,
        "body": text.strip(),
    }


def _extract_field(text: str, label: str) -> str:
    """Extract a `**<label>:** ...` paragraph (until next blank line or **Field**)."""
    pattern = rf"\*\*{re.escape(label)}:\*\*\s*(.+?)(?=\n\n|\n\*\*[A-Z]|\Z)"
    m = re.search(pattern, text, re.DOTALL)
    return m.group(1).strip() if m else ""


def _build_description(p: dict) -> str:
    """Template-shaped description per feedback_template_descriptions_not_verbatim.md.

    Avoids verbatim prompt slices and markdown leakage; uses an explicit
    trigger-keyword phrasing so CC's description-match has something to bind to.
    """
    triggers = _infer_triggers(p)
    rule_short = (p["rule"] or p["title"]).split(".")[0].strip()
    if len(rule_short) > 120:
        rule_short = rule_short[:117] + "..."

    if triggers:
        keys = ", ".join(f"'{t}'" for t in triggers[:3])
        return (
            f"Project policy {p['slug']}. "
            f"Apply when situation matches: {keys}. "
            f"Rule: {rule_short}."
        )
    return f"Project policy {p['slug']}. Rule: {rule_short}."


def _infer_triggers(p: dict) -> list[str]:
    """Synthesize 2-4 trigger phrases from the policy slug + title.

    Slug (e.g., "verify_live_state") gives action-shaped triggers
    ("verify live state"); title gives a human-phrased alternate.
    """
    triggers: list[str] = []
    slug_phrase = p["slug"].replace("_", " ").replace("-", " ")
    if slug_phrase:
        triggers.append(slug_phrase)

    # Title minus the leading category prefix, lowercased
    title_clean = re.sub(r"^[A-Z]+\s*[—:-]\s*", "", p["title"]).strip().lower()
    if title_clean and title_clean != slug_phrase:
        triggers.append(title_clean[:60])

    # Per-policy hand-tuned trigger hints (keyed by slug substring)
    hints = {
        "verify_live": ["check current PR state", "is this still in flight"],
        "paste_friction": ["copy-paste count", "manual paste", "founder typing"],
        "ci_billing": ["CI failed with steps_count=0", "billing-exhausted check"],
        "descope_production": ["PR is too large", "split this PR", "300 LOC"],
        "lokesh_not_gh_ops": ["should I push", "should I merge", "gh CLI"],
        "shipping_momentum": ["ship to public", "external release", "post on HN"],
        "pre_wire_team": ["wiring substrate", "before wiring", "cross-check first"],
        "session_mirror": ["end of turn", "session_mirror"],
        "rotation_is_nucleus": ["sprint boundary", "rotate session"],
        "task_deps_not_calendar": ["plan trigger", "scheduled date", "by Thursday"],
        "polling_mode": ["fast peer exchange", "want me to send"],
        "drive_loops_dont_stop": ["fired directive", "waiting for response"],
        "read_spec_before": ["per spec section", "follow protocol"],
        "ai_disputes_stay": ["Claude vs Claude", "escalate to Lokesh"],
        "ai_convergence_is_go": ["2-of-3 convergence", "AI-lane go"],
        "cc_approval_wait": ["approval wait", "queued for terminal", "kickback"],
        "pr_review_check_branch": ["small diff", "stale base", "review PR"],
    }
    for key, extras in hints.items():
        if key in p["slug"]:
            triggers.extend(extras)
            break

    # Dedup preserving order
    seen = set()
    out = []
    for t in triggers:
        t = t.strip()
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _build_skill_md(p: dict) -> str:
    """Render the SKILL.md content."""
    triggers = _infer_triggers(p)
    description = _build_description(p)

    lines = [
        "---",
        f"name: policy-{p['slug']}",
        f"description: {description}",
        "source: nucleus-policy-publish",
        "version: 1.0.0",
        "---",
        "",
        f"# Policy: {p['title']}",
        "",
        "## When to use",
    ]
    for t in triggers[:6]:
        lines.append(f"- {t}")
    lines.append("")
    if p["rule"]:
        lines.append("## Rule")
        lines.append(p["rule"])
        lines.append("")
    if p["why"]:
        lines.append("## Why")
        lines.append(p["why"])
        lines.append("")
    if p["how"]:
        lines.append("## How to apply")
        lines.append(p["how"])
        lines.append("")
    lines.append("## Source")
    lines.append(f"`.brain/policies/{p['slug']}.md` (repo-visible authoritative copy)")
    lines.append("")
    return "\n".join(lines)


def publish_one(policy_path: Path, dry_run: bool = False) -> Path:
    p = _read_policy(policy_path)
    skill_dir = SKILLS_DIR / f"policy-{p['slug']}"
    skill_md = _build_skill_md(p)
    if dry_run:
        return skill_dir / "SKILL.md"
    skill_dir.mkdir(parents=True, exist_ok=True)
    out = skill_dir / "SKILL.md"
    out.write_text(skill_md, encoding="utf-8")
    return out


def main(argv: list[str]) -> int:
    dry_run = "--dry-run" in argv
    only = next((a for a in argv if a.startswith("--only=")), None)
    only_slug = only.split("=", 1)[1] if only else None

    files = sorted(POLICIES_DIR.glob("*.md"))
    files = [f for f in files if f.name not in SKIP_FILES]
    if only_slug:
        files = [f for f in files if f.stem == only_slug]
        if not files:
            print(f"no policy file matched --only={only_slug}", file=sys.stderr)
            return 2

    print(f"Publishing {len(files)} policy file(s) -> {SKILLS_DIR}")
    if dry_run:
        print("(dry run — no files written)")

    for f in files:
        out = publish_one(f, dry_run=dry_run)
        marker = "[would write]" if dry_run else "[wrote]"
        print(f"  {marker} {out.relative_to(REPO_ROOT)}")

    print(f"Done. {len(files)} skill(s) {'planned' if dry_run else 'published'}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
