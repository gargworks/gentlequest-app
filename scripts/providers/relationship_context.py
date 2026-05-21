#!/usr/bin/env python3
"""
Relationship Context Engine — Third Brother's Tone-Adaptive Message Drafting
============================================================================
Loads per-person tone profiles, retrieves recent chat history, and calls TB
via Ollama to draft messages in Lokesh's authentic voice for each relationship.

Usage:
    # Draft a reply to Manju's latest message
    python3 providers/relationship_context.py --person manju \
        --msg "I was thinking about what you said yesterday about taking time for yourself"

    # Draft with extra instruction
    python3 providers/relationship_context.py --person manju \
        --msg "Happy birthday!" --instruction "warm but not over the top"

    # Show recent chat context (no draft)
    python3 providers/relationship_context.py --person manju --history

    # List available profiles
    python3 providers/relationship_context.py --list
"""

import json
import re
import html
import sys
import os
import argparse
import urllib.request
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RELATIONSHIPS_DIR = PROJECT_ROOT / ".brain" / "relationships"
INBOX_DIR = PROJECT_ROOT / ".brain" / "training" / "inbox" / "relationship"

# ── Ollama config ────────────────────────────────────────────
OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
TB_MODEL = "third-brother:latest"
TB_FALLBACK_MODEL = "qwen2.5:3b"  # if TB not available yet

# ── Context limits ───────────────────────────────────────────
MAX_HISTORY_MESSAGES = 30   # max messages to include from chat history
MAX_CONTEXT_CHARS = 4000    # cap on total chat history context


# ═══════════════════════════════════════════════════════════════
# PROFILE LOADING
# ═══════════════════════════════════════════════════════════════

def load_profile(person: str) -> Optional[Dict]:
    """Load a relationship tone profile by name (case-insensitive)."""
    person_lower = person.lower().strip()
    for f in RELATIONSHIPS_DIR.glob("*.json"):
        try:
            with open(f) as fh:
                profile = json.load(fh)
            name = profile.get("name", "").lower()
            aliases = [a.lower() for a in profile.get("aliases", [])]
            if person_lower == name or person_lower in aliases:
                profile["_file"] = str(f)
                return profile
        except (json.JSONDecodeError, IOError):
            continue
    return None


def list_profiles() -> List[Dict]:
    """List all available relationship profiles."""
    profiles = []
    for f in sorted(RELATIONSHIPS_DIR.glob("*.json")):
        try:
            with open(f) as fh:
                p = json.load(fh)
            profiles.append({
                "name": p.get("name", f.stem),
                "relationship": p.get("relationship", ""),
                "platform": p.get("platform", ""),
                "file": f.name,
            })
        except (json.JSONDecodeError, IOError):
            continue
    return profiles


# ═══════════════════════════════════════════════════════════════
# CHAT HISTORY PARSING
# ═══════════════════════════════════════════════════════════════

def _parse_whatsapp_txt(path: Path) -> List[Dict]:
    """Parse WhatsApp text export into message dicts."""
    messages = []
    pattern = re.compile(
        r'^\[(\d+/\d+/\d+,\s*\d+:\d+:\d+\s*[AP]M)\]\s*([^:]+):\s*(.*)'
    )
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except IOError:
        return []

    for line in text.split("\n"):
        m = pattern.match(line.strip())
        if m:
            ts_str, sender, content = m.group(1), m.group(2).strip(), m.group(3).strip()
            if content and "omitted" not in content.lower():
                messages.append({
                    "timestamp": ts_str,
                    "sender": sender,
                    "text": content,
                })
    return messages


def _parse_telegram_html(path: Path) -> List[Dict]:
    """Parse Telegram HTML export into message dicts."""
    messages = []
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except IOError:
        return []

    msg_blocks = re.split(r'<div class="message default clearfix"', content)
    for block in msg_blocks[1:]:  # skip preamble
        # Extract sender
        sender_match = re.search(r'class="from_name"[^>]*>\s*([^<]+)', block)
        sender = html.unescape(sender_match.group(1).strip()) if sender_match else ""

        # Extract text
        text_match = re.search(r'class="text"[^>]*>(.*?)</div>', block, re.DOTALL)
        if not text_match:
            continue
        raw_text = text_match.group(1)
        # Strip HTML tags, decode entities
        text = re.sub(r'<[^>]+>', ' ', raw_text)
        text = html.unescape(text).strip()
        text = re.sub(r'\s+', ' ', text)

        if not text or len(text) < 2:
            continue

        # Extract timestamp
        ts_match = re.search(r'class="date"[^>]*title="([^"]*)"', block)
        ts = ts_match.group(1) if ts_match else ""

        messages.append({
            "timestamp": ts,
            "sender": sender,
            "text": text,
        })
    return messages


def load_chat_history(profile: Dict, limit: Optional[int] = None) -> List[Dict]:
    """Load and merge chat history from all files for a person."""
    all_messages = []
    for rel_path in profile.get("chat_history_files", []):
        full_path = PROJECT_ROOT / rel_path
        if not full_path.exists():
            continue
        if full_path.suffix == ".txt":
            all_messages.extend(_parse_whatsapp_txt(full_path))
        elif full_path.suffix == ".html":
            all_messages.extend(_parse_telegram_html(full_path))

    # Return last N messages
    n = limit or profile.get("context_window", MAX_HISTORY_MESSAGES)
    return all_messages[-n:]


# ═══════════════════════════════════════════════════════════════
# CONTEXT BUILDER
# ═══════════════════════════════════════════════════════════════

def _is_lokesh(sender: str, profile: Dict) -> bool:
    """Check if a sender name is Lokesh."""
    lokesh_names = set(profile.get("lokesh_sender_names", ["Lokesh", "Lokesh Garg"]))
    return sender.strip() in lokesh_names


def format_chat_context(messages: List[Dict], profile: Dict) -> str:
    """Format recent chat history into readable context for TB."""
    if not messages:
        return "[No chat history available]"

    lines = []
    total_chars = 0
    person_name = profile["name"]

    for msg in messages:
        sender = msg["sender"]
        text = msg["text"]
        ts = msg.get("timestamp", "")

        if _is_lokesh(sender, profile):
            line = f"Lokesh: {text}"
        else:
            line = f"{person_name}: {text}"

        if total_chars + len(line) > MAX_CONTEXT_CHARS:
            break
        lines.append(line)
        total_chars += len(line)

    return "\n".join(lines)


def build_system_prompt(profile: Dict) -> str:
    """Build TB's system prompt with relationship-specific tone guidance."""
    name = profile["name"]
    tp = profile.get("tone_profile", {})

    works = "\n".join(f"  - {w}" for w in tp.get("works", []))
    avoid = "\n".join(f"  - {a}" for a in tp.get("avoid", []))

    return f"""You are Third Brother — Lokesh's personal AI who knows his relationships intimately.

RELATIONSHIP: {profile.get('relationship', name)}

TONE FOR {name.upper()}:
Style: {tp.get('style', 'warm, authentic')}

What works with {name}:
{works}

What to avoid with {name}:
{avoid}

{tp.get('voice_notes', '')}

RULES:
- Draft messages AS Lokesh, in his exact voice. Not your voice.
- Match the tone and length of how Lokesh actually messages this person (see chat history below).
- If the history shows short messages, keep it short. If it shows longer, more crafted messages, match that.
- Never hedge with "you could say..." — just write the message directly.
- Adapt based on the emotional temperature of the conversation.
- If the other person seems warm, lean in. If they seem distant, don't overcorrect — stay steady.
- Output ONLY the message text. No quotes, no explanation, no "Here's a draft:" prefix."""


def build_full_prompt(
    profile: Dict,
    their_message: str,
    instruction: Optional[str] = None,
    history_limit: Optional[int] = None,
) -> Tuple[str, str]:
    """Build complete system + user prompt for TB.

    Returns (system_prompt, user_prompt).
    """
    system = build_system_prompt(profile)
    name = profile["name"]

    # Load recent chat history
    messages = load_chat_history(profile, limit=history_limit)
    chat_context = format_chat_context(messages, profile)

    # Build user prompt
    parts = []
    parts.append(f"[RECENT CONVERSATION WITH {name.upper()}]")
    parts.append(chat_context)
    parts.append("")
    parts.append(f"[{name.upper()}'S LATEST MESSAGE]")
    parts.append(their_message)
    parts.append("")
    parts.append("Draft my reply.")

    if instruction:
        parts.append(f"\nTone guidance: {instruction}")

    return system, "\n".join(parts)


# ═══════════════════════════════════════════════════════════════
# OLLAMA INFERENCE
# ═══════════════════════════════════════════════════════════════

def _get_available_model() -> Optional[str]:
    """Check which TB model is available in Ollama."""
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags", method="GET")
        resp = urllib.request.urlopen(req, timeout=3)
        data = json.loads(resp.read())
        models = [m["name"] for m in data.get("models", [])]

        # Prefer third-brother:latest
        for m in models:
            if "third-brother" in m:
                return m
        # Fallback to qwen
        for m in models:
            if "qwen" in m.lower():
                return m
        return None
    except Exception:
        return None


def draft_message(
    person: str,
    their_message: str,
    instruction: Optional[str] = None,
    history_limit: Optional[int] = None,
    temperature: float = 0.7,
    verbose: bool = False,
) -> Dict:
    """Draft a message for a specific person via TB.

    Returns dict with: draft, model, person, context_messages, error
    """
    result = {
        "draft": "",
        "model": "",
        "person": person,
        "context_messages": 0,
        "error": None,
    }

    # Load profile
    profile = load_profile(person)
    if not profile:
        available = [p["name"] for p in list_profiles()]
        result["error"] = f"No profile found for '{person}'. Available: {', '.join(available)}"
        return result

    # Build prompt
    system_prompt, user_prompt = build_full_prompt(
        profile, their_message, instruction, history_limit
    )

    # Count context
    messages = load_chat_history(profile, limit=history_limit)
    result["context_messages"] = len(messages)

    if verbose:
        print(f"\n--- SYSTEM PROMPT ---\n{system_prompt[:500]}...")
        print(f"\n--- USER PROMPT ---\n{user_prompt[:500]}...")

    # Find model
    model = _get_available_model()
    if not model:
        result["error"] = "Ollama not running or no model available. Start Ollama first."
        return result
    result["model"] = model

    # Call Ollama (chat API — requires model with chat template)
    try:
        payload = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "num_predict": 512,
            },
        }).encode()

        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=60)
        data = json.loads(resp.read())
        result["draft"] = data.get("message", {}).get("content", "").strip()

    except Exception as e:
        result["error"] = f"Ollama call failed: {e}"

    return result


# ═══════════════════════════════════════════════════════════════
# MULTI-DRAFT — generate alternatives with varied temperature
# ═══════════════════════════════════════════════════════════════

def draft_options(
    person: str,
    their_message: str,
    instruction: Optional[str] = None,
    count: int = 3,
) -> List[Dict]:
    """Generate multiple draft options at different temperature levels.

    Returns list of draft results at temperatures [0.5, 0.7, 0.9]
    for safe/balanced/bold options.
    """
    temps = [0.5, 0.7, 0.9][:count]
    labels = ["measured", "balanced", "bold"]
    results = []
    for i, temp in enumerate(temps):
        r = draft_message(person, their_message, instruction, temperature=temp)
        r["style"] = labels[i] if i < len(labels) else f"v{i+1}"
        results.append(r)
    return results


# ═══════════════════════════════════════════════════════════════
# FEEDBACK LOOP — log which draft was sent for future training
# ═══════════════════════════════════════════════════════════════

DRAFT_LOG = PROJECT_ROOT / ".brain" / "relationships" / "draft_log.jsonl"


def log_draft_outcome(
    person: str,
    their_message: str,
    draft_sent: str,
    drafts_rejected: Optional[List[str]] = None,
    notes: Optional[str] = None,
):
    """Log which draft was actually sent — DPO gold for next training cycle.

    The sent draft becomes 'chosen', rejected drafts become 'rejected' candidates.
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "person": person,
        "their_message": their_message,
        "chosen": draft_sent,
        "rejected": drafts_rejected or [],
        "notes": notes or "",
    }
    with open(DRAFT_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Third Brother relationship message drafting"
    )
    parser.add_argument("--person", "-p", help="Person name or alias")
    parser.add_argument("--msg", "-m", help="Their latest message to reply to")
    parser.add_argument("--instruction", "-i", help="Extra tone guidance")
    parser.add_argument("--history", action="store_true", help="Show recent chat context")
    parser.add_argument("--list", action="store_true", help="List available profiles")
    parser.add_argument("--options", action="store_true",
                        help="Generate 3 draft options (measured/balanced/bold)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show prompts")
    parser.add_argument("--limit", type=int, help="Override history message limit")
    args = parser.parse_args()

    if args.list:
        profiles = list_profiles()
        if not profiles:
            print("No profiles found in .brain/relationships/")
            return
        print(f"\nAvailable profiles ({len(profiles)}):\n")
        for p in profiles:
            print(f"  {p['name']:12s}  {p['platform']:10s}  {p['relationship'][:60]}")
        return

    if not args.person:
        parser.print_help()
        return

    profile = load_profile(args.person)
    if not profile:
        available = [p["name"] for p in list_profiles()]
        print(f"No profile for '{args.person}'. Available: {', '.join(available)}")
        sys.exit(1)

    if args.history:
        messages = load_chat_history(profile, limit=args.limit)
        if not messages:
            print(f"No chat history found for {profile['name']}")
            return
        print(f"\nRecent messages with {profile['name']} ({len(messages)} messages):\n")
        chat_ctx = format_chat_context(messages, profile)
        print(chat_ctx)
        return

    if not args.msg:
        print("Need --msg with their latest message. Use --history to see chat context.")
        sys.exit(1)

    if args.options:
        print(f"\nDrafting 3 options for {profile['name']}...\n")
        results = draft_options(args.person, args.msg, args.instruction)
        for r in results:
            if r.get("error"):
                print(f"  [{r['style']}] Error: {r['error']}")
            else:
                print(f"  [{r['style']}] ({r['model']}, {r['context_messages']} msgs context)")
                print(f"  {r['draft']}\n")
    else:
        result = draft_message(
            args.person, args.msg, args.instruction,
            history_limit=args.limit, verbose=args.verbose,
        )
        if result["error"]:
            print(f"Error: {result['error']}")
            sys.exit(1)
        print(f"\n[{result['model']} | {result['context_messages']} messages context]\n")
        print(result["draft"])


if __name__ == "__main__":
    main()
