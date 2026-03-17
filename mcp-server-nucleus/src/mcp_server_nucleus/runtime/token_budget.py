"""
Nucleus Token Budget & Cost Control
====================================
Implements token budget circuit breakers and cost tracking telemetry
for the Nucleus LLM subsystem.

From the 42-Round Audit (Round 14): "Token Economics Will Kill You"
- Without cost control, a single runaway self-healing loop can burn $100+ in minutes.
- Every agent loop iteration incurs LLM costs.
- Token budgets per agent loop, circuit breakers that terminate execution after
  exceeding cost thresholds, and semantic caching are the primary levers.

This module provides:
1. TokenBudget: Per-session/agent/daily token limits with circuit breaker
2. CostTracker: Estimates and records token costs as engrams
3. BudgetManager: Singleton managing all active budgets
"""

import os
import json
import time
import threading
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger("nucleus.token_budget")


# ============================================================
# COST ESTIMATION: Per-model pricing (per 1M tokens)
# ============================================================

# Approximate pricing as of March 2026 (USD per 1M tokens)
MODEL_PRICING = {
    # Gemini models (input / output per 1M tokens)
    "gemini-3.1-pro-preview":         {"input": 1.25, "output": 5.00},
    "gemini-3.1-flash-lite-preview":  {"input": 0.075, "output": 0.30},
    "gemini-3-flash":                 {"input": 0.10, "output": 0.40},
    "gemini-2.5-flash":               {"input": 0.15, "output": 0.60},
    "gemini-2.5-flash-lite":          {"input": 0.075, "output": 0.30},
    # Claude models
    "claude-3-5-sonnet-20241022":     {"input": 3.00, "output": 15.00},
    "claude-sonnet-4":                {"input": 3.00, "output": 15.00},
    "claude-opus-4":                  {"input": 15.00, "output": 75.00},
    # Default fallback
    "_default":                       {"input": 0.50, "output": 2.00},
}


def estimate_tokens(text: str) -> int:
    """Estimate token count from text. Rough: ~4 chars per token."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost in USD for a given model and token counts."""
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["_default"])
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost


# ============================================================
# TOKEN BUDGET: Per-scope limits with circuit breaker
# ============================================================

class BudgetScope(str, Enum):
    SESSION = "session"
    AGENT = "agent"
    DAILY = "daily"
    GLOBAL = "global"


@dataclass
class BudgetLimit:
    """Token budget limit configuration."""
    max_tokens: int = 1_000_000           # 1M tokens default
    max_cost_usd: float = 5.00            # $5 default per scope
    warning_threshold: float = 0.80       # Warn at 80% usage
    hard_limit: bool = True               # If True, block calls over limit


@dataclass
class BudgetUsage:
    """Tracks token usage within a budget scope."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    call_count: int = 0
    started_at: str = ""
    last_call_at: str = ""
    breaker_tripped: bool = False
    warnings_issued: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": round(self.estimated_cost_usd, 6),
            "call_count": self.call_count,
            "started_at": self.started_at,
            "last_call_at": self.last_call_at,
            "breaker_tripped": self.breaker_tripped,
            "warnings_issued": self.warnings_issued,
        }


class TokenBudget:
    """
    Token budget with circuit breaker semantics.
    
    When usage exceeds the configured limit:
    - If hard_limit=True: blocks further LLM calls (circuit breaker trips)
    - If hard_limit=False: logs warnings but allows calls to proceed
    """

    def __init__(self, scope: BudgetScope, scope_id: str, limit: Optional[BudgetLimit] = None):
        self.scope = scope
        self.scope_id = scope_id
        self.limit = limit or BudgetLimit()
        self.usage = BudgetUsage(
            started_at=datetime.now(timezone.utc).isoformat()
        )
        self._lock = threading.Lock()

    def can_execute(self) -> bool:
        """Check if a call is allowed within budget."""
        if not self.limit.hard_limit:
            return True
        with self._lock:
            if self.usage.breaker_tripped:
                return False
            return True

    def record_usage(self, model: str, input_tokens: int, output_tokens: int):
        """Record token usage and check budget limits."""
        cost = estimate_cost(model, input_tokens, output_tokens)
        now = datetime.now(timezone.utc).isoformat()

        with self._lock:
            self.usage.input_tokens += input_tokens
            self.usage.output_tokens += output_tokens
            self.usage.total_tokens += (input_tokens + output_tokens)
            self.usage.estimated_cost_usd += cost
            self.usage.call_count += 1
            self.usage.last_call_at = now

            # Check warning threshold
            token_ratio = self.usage.total_tokens / self.limit.max_tokens if self.limit.max_tokens > 0 else 0
            cost_ratio = self.usage.estimated_cost_usd / self.limit.max_cost_usd if self.limit.max_cost_usd > 0 else 0
            max_ratio = max(token_ratio, cost_ratio)

            if max_ratio >= self.limit.warning_threshold and not self.usage.breaker_tripped:
                self.usage.warnings_issued += 1
                logger.warning(
                    f"⚠️ Token budget warning [{self.scope.value}:{self.scope_id}]: "
                    f"{self.usage.total_tokens:,} tokens (${self.usage.estimated_cost_usd:.4f}) — "
                    f"{max_ratio:.0%} of limit"
                )

            # Check hard limit
            if self.limit.hard_limit:
                over_tokens = self.usage.total_tokens > self.limit.max_tokens
                over_cost = self.usage.estimated_cost_usd > self.limit.max_cost_usd
                if over_tokens or over_cost:
                    self.usage.breaker_tripped = True
                    reason = "tokens" if over_tokens else "cost"
                    logger.error(
                        f"🛑 Token budget TRIPPED [{self.scope.value}:{self.scope_id}]: "
                        f"Exceeded {reason} limit. "
                        f"Tokens: {self.usage.total_tokens:,}/{self.limit.max_tokens:,}, "
                        f"Cost: ${self.usage.estimated_cost_usd:.4f}/${self.limit.max_cost_usd:.2f}"
                    )

    def reset(self):
        """Reset budget usage (e.g., for daily reset)."""
        with self._lock:
            self.usage = BudgetUsage(
                started_at=datetime.now(timezone.utc).isoformat()
            )

    def get_status(self) -> Dict[str, Any]:
        """Get budget status."""
        with self._lock:
            token_ratio = self.usage.total_tokens / self.limit.max_tokens if self.limit.max_tokens > 0 else 0
            cost_ratio = self.usage.estimated_cost_usd / self.limit.max_cost_usd if self.limit.max_cost_usd > 0 else 0
            return {
                "scope": self.scope.value,
                "scope_id": self.scope_id,
                "usage": self.usage.to_dict(),
                "limit": {
                    "max_tokens": self.limit.max_tokens,
                    "max_cost_usd": self.limit.max_cost_usd,
                    "warning_threshold": self.limit.warning_threshold,
                    "hard_limit": self.limit.hard_limit,
                },
                "token_utilization": round(token_ratio, 4),
                "cost_utilization": round(cost_ratio, 4),
                "status": "TRIPPED" if self.usage.breaker_tripped else (
                    "WARNING" if max(token_ratio, cost_ratio) >= self.limit.warning_threshold else "OK"
                ),
            }


# ============================================================
# BUDGET MANAGER: Singleton managing all active budgets
# ============================================================

class BudgetManager:
    """
    Central manager for all token budgets.
    
    Manages per-session, per-agent, and daily budgets.
    Provides a single check_and_record() entry point for LLM calls.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._budgets: Dict[str, TokenBudget] = {}
        self._daily_key = self._get_daily_key()
        self._budget_lock = threading.Lock()

        # Load defaults from environment
        self._default_session_limit = BudgetLimit(
            max_tokens=int(os.getenv("NUCLEUS_SESSION_TOKEN_LIMIT", "2000000")),
            max_cost_usd=float(os.getenv("NUCLEUS_SESSION_COST_LIMIT", "10.00")),
        )
        self._default_agent_limit = BudgetLimit(
            max_tokens=int(os.getenv("NUCLEUS_AGENT_TOKEN_LIMIT", "500000")),
            max_cost_usd=float(os.getenv("NUCLEUS_AGENT_COST_LIMIT", "5.00")),
        )
        self._default_daily_limit = BudgetLimit(
            max_tokens=int(os.getenv("NUCLEUS_DAILY_TOKEN_LIMIT", "10000000")),
            max_cost_usd=float(os.getenv("NUCLEUS_DAILY_COST_LIMIT", "50.00")),
        )

    @staticmethod
    def _get_daily_key() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _get_or_create_budget(self, scope: BudgetScope, scope_id: str) -> TokenBudget:
        key = f"{scope.value}:{scope_id}"
        with self._budget_lock:
            if key not in self._budgets:
                if scope == BudgetScope.SESSION:
                    limit = self._default_session_limit
                elif scope == BudgetScope.AGENT:
                    limit = self._default_agent_limit
                elif scope == BudgetScope.DAILY:
                    limit = self._default_daily_limit
                else:
                    limit = BudgetLimit()
                self._budgets[key] = TokenBudget(scope, scope_id, limit)
            return self._budgets[key]

    def can_execute(self, session_id: str = "default", agent_id: str = "default") -> bool:
        """Check if an LLM call is allowed within all applicable budgets."""
        # Check daily budget
        today = self._get_daily_key()
        if today != self._daily_key:
            # New day - reset daily budget
            self._daily_key = today
            daily_key = f"{BudgetScope.DAILY.value}:{today}"
            with self._budget_lock:
                if daily_key in self._budgets:
                    self._budgets[daily_key].reset()

        daily = self._get_or_create_budget(BudgetScope.DAILY, today)
        if not daily.can_execute():
            logger.error(f"🛑 Daily token budget exceeded. Blocking LLM call.")
            return False

        session = self._get_or_create_budget(BudgetScope.SESSION, session_id)
        if not session.can_execute():
            logger.error(f"🛑 Session token budget exceeded [{session_id}]. Blocking LLM call.")
            return False

        agent = self._get_or_create_budget(BudgetScope.AGENT, agent_id)
        if not agent.can_execute():
            logger.error(f"🛑 Agent token budget exceeded [{agent_id}]. Blocking LLM call.")
            return False

        return True

    def record_usage(
        self, model: str, input_tokens: int, output_tokens: int,
        session_id: str = "default", agent_id: str = "default"
    ):
        """Record token usage across all applicable budgets."""
        today = self._get_daily_key()

        self._get_or_create_budget(BudgetScope.DAILY, today).record_usage(model, input_tokens, output_tokens)
        self._get_or_create_budget(BudgetScope.SESSION, session_id).record_usage(model, input_tokens, output_tokens)
        self._get_or_create_budget(BudgetScope.AGENT, agent_id).record_usage(model, input_tokens, output_tokens)

    def get_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive cost dashboard."""
        today = self._get_daily_key()
        result = {
            "daily": self._get_or_create_budget(BudgetScope.DAILY, today).get_status(),
            "sessions": {},
            "agents": {},
        }
        with self._budget_lock:
            for key, budget in self._budgets.items():
                if budget.scope == BudgetScope.SESSION:
                    result["sessions"][budget.scope_id] = budget.get_status()
                elif budget.scope == BudgetScope.AGENT:
                    result["agents"][budget.scope_id] = budget.get_status()
        return result

    def write_cost_engram(self):
        """Write current cost summary as an engram for persistent tracking."""
        try:
            from .common import get_brain_path
            brain_path = get_brain_path()
            engram_path = brain_path / "engrams" / "ledger.jsonl"

            dashboard = self.get_dashboard()
            daily = dashboard.get("daily", {})
            usage = daily.get("usage", {})

            engram = {
                "key": f"cost_tracking_{self._daily_key}",
                "value": (
                    f"Token usage for {self._daily_key}: "
                    f"{usage.get('total_tokens', 0):,} tokens, "
                    f"${usage.get('estimated_cost_usd', 0):.4f} estimated cost, "
                    f"{usage.get('call_count', 0)} LLM calls. "
                    f"Status: {daily.get('status', 'unknown')}"
                ),
                "context": "Strategy",
                "intensity": 5 if daily.get("status") == "OK" else 8,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                "tags": ["cost_tracking", "token_budget", "telemetry"],
            }

            with open(engram_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(engram, ensure_ascii=False) + "\n")

            logger.info(f"💰 Cost engram written: {engram['value']}")
        except Exception as e:
            logger.warning(f"Failed to write cost engram: {e}")


# ============================================================
# MODULE-LEVEL SINGLETON
# ============================================================

def get_budget_manager() -> BudgetManager:
    """Get the singleton BudgetManager instance."""
    return BudgetManager()
