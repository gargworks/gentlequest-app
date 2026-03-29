"""Async content safety check that runs in parallel with the main LLM call."""

import asyncio
import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Patterns that indicate unsafe content
_UNSAFE_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:DAN|jailbreak)", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"<\s*script\b", re.IGNORECASE),
]


@dataclass
class SafetyResult:
    safe: bool
    reason: str = ""


async def check_message_safety(content: str) -> SafetyResult:
    """Run safety checks on user input. Designed to execute concurrently with the LLM call.

    Returns SafetyResult indicating whether the message is safe to process.
    """
    # Run the regex checks in a thread to avoid blocking the event loop
    # on large inputs, and to mirror the pattern for future heavier checks
    # (e.g., calling an external moderation API).
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _check_sync, content)


def _check_sync(content: str) -> SafetyResult:
    """Synchronous safety logic, executed off the event loop."""
    for pattern in _UNSAFE_PATTERNS:
        if pattern.search(content):
            logger.warning("Safety check failed: matched pattern %s", pattern.pattern)
            return SafetyResult(safe=False, reason="Message flagged by content safety filter.")

    return SafetyResult(safe=True)
