"""
Nucleus Agent Runtime (NAR)
===========================
Serverless Cognitive Threads for LLM Applications.

This is the open-source "Agent Operating System" portion of the Nucleus ecosystem.
"""

from .runtime.factory import ContextFactory
from .runtime.agent import EphemeralAgent

__version__ = "0.1.0"
__all__ = ["ContextFactory", "EphemeralAgent"]
