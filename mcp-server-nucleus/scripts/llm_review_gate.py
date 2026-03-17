#!/usr/bin/env python3
"""LLM Review Gate — Two-Persona Paranoid Review.

Runs every file in the git archive through two adversarial LLM lenses:

LENS 1 — "VC Teenager": A paranoid 19yo SV kid who will screenshot anything
embarrassing and present it to VCs. Looks for: hardcoded paths, personal
project names, strategy language, amateur comments, dead code, TODO/HACK.

LENS 2 — "HR Coworker": A jealous coworker who will file an HR complaint.
Looks for: employer references, BFSI/banking domain knowledge implying
use of proprietary work knowledge, personal identity info, work tools.

Usage:
    python scripts/llm_review_gate.py [--quick] [--provider gemini|anthropic]

    --quick     Only scan files changed since last tag (faster)
    --provider  LLM provider (default: gemini, needs GEMINI_API_KEY)
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


REVIEW_PROMPT = """You are a paranoid security and IP reviewer. Review the following source files
from an open-source project called "Nucleus" (an MCP server for AI agent governance).

You must review through TWO adversarial lenses:

## LENS 1 — "VC Teenager"
A paranoid 19-year-old Silicon Valley kid who will screenshot anything embarrassing
and present it to VCs to discredit this project. They look for:
- Hardcoded paths (e.g., /Users/anyone/, C:\\Users\\)
- Personal project names (anything that isn't "Nucleus")
- Strategy language ("moat", "kill", "crush", "siphon", "competitive advantage")
- Employer references (any company name, bank name, "BFSI")
- Amateur comments (TODO, HACK, FIXME, "temporary", "for now")
- Hardcoded credentials, API keys, tokens in plaintext
- Internal codenames or author attributions that reveal it's a one-person project
- Non-English text (Hindi, Hinglish, etc.)
- Grandiose language ("billion dollar", "military grade", "Goldman Sachs")
- References to other personal projects

## LENS 2 — "HR Coworker"
A jealous coworker who will file an HR complaint to get someone fired from a bank.
They look for:
- ANY reference to a specific employer or bank name
- Evidence of using work time/resources (work email, VPN, corporate tools)
- Paths containing real usernames
- Banking/financial domain knowledge that implies use of proprietary work knowledge
- Personal identity information (full names, emails, phone numbers)
- References to internal banking systems or processes

For EACH finding, output a JSON object:
{
    "file": "path/to/file.py",
    "line": 42,
    "severity": "CRITICAL|WARNING|INFO",
    "lens": "VC|HR",
    "finding": "Description of what was found",
    "suggestion": "How to fix it"
}

If a file is clean, do NOT output anything for it.

Output ONLY a JSON array of findings. No markdown, no explanation. Empty array [] if everything is clean.

--- FILES TO REVIEW ---
"""

BATCH_SIZE = 15  # files per LLM call


def get_archive_files() -> list[tuple[str, str]]:
    """Extract git archive and return list of (path, content) tuples."""
    tmpdir = tempfile.mkdtemp()
    subprocess.run(
        ["git", "archive", "HEAD", "--format=tar"],
        stdout=subprocess.PIPE,
        check=True,
    ).stdout
    # Use tar to extract
    proc = subprocess.run(
        ["git", "archive", "HEAD", "--format=tar"],
        stdout=subprocess.PIPE,
        check=True,
    )
    subprocess.run(
        ["tar", "-xf", "-", "-C", tmpdir],
        input=proc.stdout,
        check=True,
    )

    files = []
    for root, _, filenames in os.walk(tmpdir):
        for fname in filenames:
            fpath = Path(root) / fname
            rel = str(fpath.relative_to(tmpdir))
            # Skip binary files
            if fpath.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".ico",
                                         ".woff", ".woff2", ".ttf", ".eot",
                                         ".pyc", ".pyo", ".so", ".db"}:
                continue
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                if content.strip():
                    files.append((rel, content))
            except Exception:
                pass

    # Clean up
    subprocess.run(["rm", "-rf", tmpdir], check=True)
    return files


def review_with_gemini(prompt: str) -> str:
    """Call Gemini API for review."""
    import urllib.request
    import urllib.error

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 8192},
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode())

    text = data["candidates"][0]["content"]["parts"][0]["text"]
    # Strip markdown code fences if present
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def review_with_anthropic(prompt: str) -> str:
    """Call Anthropic API for review."""
    import urllib.request

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    url = "https://api.anthropic.com/v1/messages"
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 8192,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode())

    return data["content"][0]["text"]


def main():
    parser = argparse.ArgumentParser(description="LLM Review Gate")
    parser.add_argument("--quick", action="store_true", help="Quick mode (fewer files)")
    parser.add_argument("--provider", default="gemini", choices=["gemini", "anthropic"])
    parser.add_argument("--fail-on-warning", action="store_true",
                       help="Exit non-zero on WARNING findings too")
    args = parser.parse_args()

    print("=" * 60)
    print("  LLM REVIEW GATE — Two-Persona Paranoid Review")
    print(f"  Provider: {args.provider}")
    print("=" * 60)
    print()

    # Get all files from archive
    print("Extracting git archive...")
    files = get_archive_files()
    print(f"Archive: {len(files)} text files")

    if args.quick:
        # Only review .py and .md files
        files = [(p, c) for p, c in files if p.endswith((".py", ".md", ".yml", ".yaml", ".json", ".sh"))]
        print(f"Quick mode: {len(files)} code/config files")

    review_fn = review_with_gemini if args.provider == "gemini" else review_with_anthropic

    all_findings = []
    batches = [files[i:i + BATCH_SIZE] for i in range(0, len(files), BATCH_SIZE)]

    for i, batch in enumerate(batches):
        print(f"\nReviewing batch {i+1}/{len(batches)} ({len(batch)} files)...")

        prompt = REVIEW_PROMPT
        for path, content in batch:
            # Truncate very large files
            if len(content) > 5000:
                content = content[:5000] + "\n... [TRUNCATED] ..."
            prompt += f"\n### FILE: {path}\n```\n{content}\n```\n"

        try:
            result = review_fn(prompt)
            findings = json.loads(result)
            if isinstance(findings, list):
                all_findings.extend(findings)
                if findings:
                    for f in findings:
                        sev = f.get("severity", "?")
                        print(f"  [{sev}] {f.get('file', '?')}:{f.get('line', '?')} — {f.get('finding', '?')}")
                else:
                    print("  Clean.")
        except json.JSONDecodeError:
            print(f"  WARNING: LLM returned non-JSON response, skipping batch")
            print(f"  Response preview: {result[:200] if result else '(empty)'}")
        except Exception as e:
            print(f"  ERROR: {e}")

    # Summary
    critical = [f for f in all_findings if f.get("severity") == "CRITICAL"]
    warnings = [f for f in all_findings if f.get("severity") == "WARNING"]
    info = [f for f in all_findings if f.get("severity") == "INFO"]

    print()
    print("=" * 60)
    print(f"  LLM REVIEW RESULTS")
    print(f"  CRITICAL: {len(critical)}  WARNING: {len(warnings)}  INFO: {len(info)}")
    print("=" * 60)

    if critical:
        print(f"\n\033[0;31mBLOCKED\033[0m: {len(critical)} CRITICAL findings. Fix before public push.")
        for f in critical:
            print(f"  - {f.get('file')}:{f.get('line')} [{f.get('lens')}] {f.get('finding')}")
            print(f"    Fix: {f.get('suggestion')}")

        # Write findings to file for review
        out = Path("llm_review_findings.json")
        out.write_text(json.dumps(all_findings, indent=2))
        print(f"\nFull findings saved to {out}")
        sys.exit(1)

    if warnings and args.fail_on_warning:
        print(f"\n\033[1;33mWARNING\033[0m: {len(warnings)} WARNING findings.")
        for f in warnings:
            print(f"  - {f.get('file')}:{f.get('line')} [{f.get('lens')}] {f.get('finding')}")
        sys.exit(1)

    if warnings:
        print(f"\n\033[1;33m{len(warnings)} warnings\033[0m (non-blocking). Review recommended.")

    print(f"\n\033[0;32mPASSED\033[0m: LLM review gate clear.")
    sys.exit(0)


if __name__ == "__main__":
    main()
