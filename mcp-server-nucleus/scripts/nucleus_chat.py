#!/usr/bin/env python3
"""
Nucleus Interactive Chat — Direct Gemini Conversation via Terminal
==================================================================
The simplest way to interact with Nucleus's LLM infrastructure.
Uses the TierRouter's LOCAL_FREE tier (gemini-3.1-flash-lite-preview, 500 RPD).

Usage:
    python scripts/nucleus_chat.py                       # Default (LOCAL_FREE)
    python scripts/nucleus_chat.py --tier premium        # Use a specific tier
    python scripts/nucleus_chat.py --model gemini-3-flash  # Override model directly

In-Session Commands:
    /reset    Clear conversation history and start fresh
    /tier     Show current model/tier info
    /history  Show conversation turn count
    /exit     Quit (also Ctrl+C or Ctrl+D)
"""

import os
import sys
import signal
import warnings
import readline  # enables arrow-key history in input()
from pathlib import Path
from datetime import datetime

# Suppress noisy SDK warnings (thought_signature, etc.)
warnings.filterwarnings("ignore", message=".*non-text parts.*")

# ── Path Setup ──────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from mcp_server_nucleus.runtime.llm_client import DualEngineLLM, LLMTier, TierRouter


# ── Constants ───────────────────────────────────────────────────
TIER_MAP = {
    "premium": LLMTier.PREMIUM,
    "standard": LLMTier.STANDARD,
    "economy": LLMTier.ECONOMY,
    "local_paid": LLMTier.LOCAL_PAID,
    "local_free": LLMTier.LOCAL_FREE,
}

SYSTEM_PROMPT = """You are Nucleus, an intelligent AI assistant accessed via the terminal.
Be concise, direct, and helpful. Use markdown formatting when it improves clarity.
If the user asks about your capabilities, mention you are running through the Nucleus MCP infrastructure."""

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║               🧠 Nucleus Interactive Chat                    ║
║──────────────────────────────────────────────────────────────║
║  Commands: /reset /tier /history /exit                       ║
║  Quit:     Ctrl+C or Ctrl+D                                  ║
╚══════════════════════════════════════════════════════════════╝"""


def parse_args():
    """Parse CLI arguments without argparse (lightweight)."""
    args = {"tier": "local_free", "model": None, "system": None}
    argv = sys.argv[1:]
    i = 0
    while i < len(argv):
        if argv[i] == "--tier" and i + 1 < len(argv):
            args["tier"] = argv[i + 1]
            i += 2
        elif argv[i] == "--model" and i + 1 < len(argv):
            args["model"] = argv[i + 1]
            i += 2
        elif argv[i] == "--system" and i + 1 < len(argv):
            args["system"] = argv[i + 1]
            i += 2
        elif argv[i] in ("-h", "--help"):
            print(__doc__)
            sys.exit(0)
        else:
            i += 1
    return args


def build_prompt(history: list, system_prompt: str, user_input: str) -> str:
    """Build a multi-turn prompt from conversation history."""
    parts = [f"[SYSTEM]\n{system_prompt}\n"]
    for role, content in history:
        tag = "USER" if role == "user" else "ASSISTANT"
        parts.append(f"[{tag}]\n{content}\n")
    parts.append(f"[USER]\n{user_input}\n")
    parts.append("[ASSISTANT]\n")
    return "\n".join(parts)


def handle_slash_command(cmd: str, llm: DualEngineLLM, history: list, tier_name: str) -> bool:
    """Handle /commands. Returns True if handled, False otherwise."""
    cmd = cmd.strip().lower()

    if cmd in ("/exit", "/quit", "/q"):
        print("\n👋 Goodbye!")
        sys.exit(0)

    elif cmd == "/reset":
        history.clear()
        print("🔄 Conversation history cleared.\n")
        return True

    elif cmd == "/tier":
        config = TierRouter.TIER_CONFIGS.get(TIER_MAP.get(tier_name, LLMTier.LOCAL_FREE), {})
        print(f"📊 Tier: {tier_name}")
        print(f"   Model: {llm.model_name}")
        print(f"   Engine: {llm.engine}")
        print(f"   Platform: {config.get('platform', 'unknown')}")
        print(f"   Description: {config.get('description', 'N/A')}\n")
        return True

    elif cmd == "/history":
        turns = len(history) // 2 if history else 0
        print(f"📜 Conversation: {turns} turn(s), {len(history)} messages\n")
        return True

    return False


def main():
    args = parse_args()
    tier_name = args["tier"]
    model_override = args["model"]
    system_prompt = args["system"] or SYSTEM_PROMPT

    # Resolve tier
    tier = TIER_MAP.get(tier_name)
    if tier is None:
        print(f"❌ Unknown tier '{tier_name}'. Available: {', '.join(TIER_MAP.keys())}")
        sys.exit(1)

    # Initialize LLM
    try:
        if model_override:
            llm = DualEngineLLM(tier=tier, model_name=model_override)
        else:
            llm = DualEngineLLM(tier=tier)
    except Exception as e:
        print(f"❌ Failed to initialize LLM: {e}")
        sys.exit(1)

    # Banner
    print(BANNER)
    print(f"  Model: {llm.model_name} | Tier: {tier_name} | Engine: {llm.engine}")
    print(f"  Time:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    history = []

    # Graceful Ctrl+C
    def handle_sigint(sig, frame):
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    signal.signal(signal.SIGINT, handle_sigint)

    # ── Main Loop ───────────────────────────────────────────────
    while True:
        try:
            user_input = input("You › ").strip()
        except EOFError:
            print("\n\n👋 Goodbye!")
            break

        if not user_input:
            continue

        # Slash commands
        if user_input.startswith("/"):
            if handle_slash_command(user_input, llm, history, tier_name):
                continue

        # Build multi-turn prompt
        prompt = build_prompt(history, system_prompt, user_input)

        # Call LLM
        try:
            response = llm.generate_content(prompt)

            # Extract text
            if hasattr(response, "text"):
                reply = response.text.strip()
            elif hasattr(response, "candidates") and response.candidates:
                parts = response.candidates[0].content.parts
                reply = "".join(p.text for p in parts if hasattr(p, "text")).strip()
            else:
                reply = "(Empty response)"

            # Update history
            history.append(("user", user_input))
            history.append(("assistant", reply))

            # Print
            print(f"\n🧠 {reply}\n")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print(f"\n⚠️  Rate limited. Wait a moment and try again.\n")
            elif "404" in error_str:
                print(f"\n❌ Model '{llm.model_name}' not found. Try --model gemini-3.1-flash-lite-preview\n")
            else:
                print(f"\n❌ Error: {error_str[:200]}\n")


if __name__ == "__main__":
    main()
