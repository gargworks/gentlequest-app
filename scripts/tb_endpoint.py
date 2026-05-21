#!/usr/bin/env python3
"""TB Endpoint — single HTTP service exposing TB to all surfaces.

One endpoint, many surfaces. Telegram bot, iOS Shortcut, Claude tool, REPL,
web UI — all POST to the same handlers. Each turn through the endpoint
auto-runs the full compound stack:

  - Build hybrid-RAG context (working state + live session + brain knowledge)
  - Optional cross-encoder rerank
  - Auto-correction-detector on the prior turn
  - Generate via TB v14
  - Shadow-log for RAFT
  - Write ALIGN verdict (auto-detected or explicit)
  - DPO pair on every confirmed correction

Sovereignty + mode gating:
  Each /tb/turn (and /tb/align, /tb/polish) accepts:
    - mode: code | life | business | design   (default: code)
    - sovereignty: public | guarded | sovereign  (default: public)
  sovereign → corpus writes are skipped (no shadow_log, no DPO pair, no
  ALIGN verdict). Output still returns; nothing compounds.
  guarded/public → writes proceed, mode + sovereignty tagged into source
  field for downstream filters. Default flipped to public 2026-05-02 per
  founder direction: collect everything, filter at training time via mode
  tag. sovereign remains as an explicit escape hatch.

Endpoints:
  POST /tb/turn       chat turn (input → output, with full scaffolding)
  POST /tb/align      explicit verdict (good|bad) on a prior turn
  POST /tb/polish     log a cross-LLM polish exchange as a DPO pair
  POST /tb/engrams    direct engram tool-call (search by query)
  POST /tb/remember   write a personal fact into the engram ledger
  POST /tb/undo       remove the most recent preference_pair (typo retract)
  GET  /tb/stats      corpus accumulation snapshot (pairs/engrams by mode)
  GET  /tb/health     health probe (model / brain / warm)

Run:
    python3 scripts/tb_endpoint.py
    TB_ENDPOINT_PORT=7878 python3 scripts/tb_endpoint.py

Smoke:
    curl -s localhost:7878/tb/health
    curl -s localhost:7878/tb/turn -d '{"input":"what is third brother?"}'
"""
import argparse
import json
import os
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "mcp-server-nucleus" / "src"))

from providers.brain_rag import build_full_context, format_rag_context, BUDGET_COLD
from providers.reranker import rerank as cross_rerank
from providers.correction_detector import detect_correction
from providers.composers import (
    compose_with_sonnet, verify_grounding, templates as composer_templates,
)
from providers.composers.sonnet_principal import is_principal_error, detect_refusal
from providers.composers.haiku_verifier import banner_for_verdict
from providers.composers.voice import (
    build_voice_preamble, strip_assistant_tone, NO_MORALIZE_SYSPROMPT,
    append_voice_candidate, voice_status,
)
from persist_sessions import SessionStore, migrate_in_memory
from thread_storage import ThreadStorage, migrate_from_sessions
from thread_router import route_message, update_centroid, embed_text, RouteDecision
from thread_slash import handle_thread_slash
import third_brother_driver as tb

BRAIN_PATH = Path(os.environ.get("NUCLEUS_BRAIN_PATH", str(ROOT / ".brain")))
DEFAULT_MODEL = os.environ.get("TB_MODEL", "third-brother:latest")
DEFAULT_PORT = int(os.environ.get("TB_ENDPOINT_PORT", "7878"))
DEFAULT_NUM_PREDICT = int(os.environ.get("TB_CHAT_NUM_PREDICT", "2048"))  # bumped 1024→2048 per "comprehensive" direction 2026-05-10
DEFAULT_TIMEOUT = int(os.environ.get("TB_CHAT_TIMEOUT", "600"))
# Phase 1 (DEC-009 + charter commitment #2): no LIFE_NUM_PREDICT cap.
# The previous cap (600) prevented life-mode answers from going long.
# Citation-loop bug from PR #298 is now mitigated by ANTI_CITATION_STOPS,
# so the cap is redundant. Trust caller's num_predict (clamped only at
# upper safety bound 4096 below).
# Token-budget for conversation history. Sonnet 4.6 + Opus 4.7 have
# 200K-token context windows; reserve ~25K for response+RAG+safety,
# leaving 175K for prompt. History budget = 60K tokens (~45K words),
# generous for any conversation that fits in working memory before
# Phase 4 conversation-RAG retrieves topical history from disk.
HISTORY_TOKEN_BUDGET = int(os.environ.get("TB_HISTORY_TOKEN_BUDGET", "60000"))
# Anti-citation-loop stop sequences. v14 falls into runaway "[1][2][3]...[N]"
# patterns on long-context life-mode prompts. These triggers fire as soon as
# the bracket chain reaches double digits, killing the loop early. Plain prose
# answers never emit these strings, so collateral damage is negligible.
ANTI_CITATION_STOPS = [
    "[10][", "[15][", "[20][",
    "][10]", "][15]", "][20]",
]
# HISTORY_TURNS retired Phase 1 — replaced by token-budget trim.
# Conversations grow unbounded in `_sessions[id]["turns"]`; prompt-build
# trims the most-recent turns that fit in HISTORY_TOKEN_BUDGET. Older
# turns persist in working memory and (Phase 4+) are retrieved by topic
# from conversation-RAG when relevant. See `_format_history` below.

# ── TB Quality Compound (2026-05-08) ───────────────────────────────────
# Six env-flag-gated levers that compound. See docs/tb_stack_build_spec.md
# and plan file valiant-mixing-nebula.md for the flywheel rationale.
#
# Defaults chosen so the headline win (Sonnet-as-composer for life-mode
# via /quality good) ships on by default; opt-in features stay opt-in.
# Each lever can be flipped off without redeploy via env. Sovereign mode
# overrides ALL of these (HARD GATE in handle_turn): sovereign data stays
# local, never reaches Anthropic API.
TB_VOICE = os.environ.get("TB_VOICE", "on")  # on|off — Phase 1 §1.4
TB_VOICE_STRIP = os.environ.get("TB_VOICE_STRIP", "on")  # on|off — Phase 1 §1.5
TB_NO_MORALIZE = os.environ.get("TB_NO_MORALIZE", "on")  # on|off — Phase 1 §1.7
# Phase 1 §1.8: moralizing preambles default OFF (charter commitment #6).
# The Opus-parroting-DO-NOT bug from 2026-05-08 morning was the cautionary
# tale — hard "DO NOT X" rules in preambles get echoed verbatim by composer
# under context pressure. Voice anchor (§1.4) handles tone steering with
# soft style guidance; explicit anti-mix preambles are now opt-in only.
TB_GROUNDING_ONLY = os.environ.get("TB_GROUNDING_ONLY", "off")  # on|off
TB_PRINCIPAL_MODE = os.environ.get("TB_PRINCIPAL_MODE", "auto")  # auto|tb|sonnet
TB_PROMPT_TEMPLATE = os.environ.get("TB_PROMPT_TEMPLATE", "auto")  # auto|free|constrained
TB_RAG_MIN_DENSE = float(os.environ.get("TB_RAG_MIN_DENSE", "0.0"))
TB_VERIFIER_DEFAULT = os.environ.get("TB_VERIFIER", "off")  # off|haiku
TB_ANTIMIX = os.environ.get("TB_ANTIMIX", "off")  # on|off — Phase 1 §1.8: opt-in
TB_SELF_VERIFY_DEFAULT = os.environ.get("TB_SELF_VERIFY", "off")  # off|on (opt-in)
TB_QUALITY_BUDGET_USD = float(os.environ.get("TB_QUALITY_BUDGET_USD", "5.0"))
TB_SONNET_TIMEOUT = int(os.environ.get("TB_SONNET_TIMEOUT", "600"))
TB_HAIKU_TIMEOUT = int(os.environ.get("TB_HAIKU_TIMEOUT", "60"))

os.environ.setdefault("NUCLEAR_BRAIN_PATH", str(BRAIN_PATH))

# Mode taxonomy
# -------------
# 2026-05-02: Simplified to 3 primary modes (code | life | work) per founder
# direction. Original 4-mode schema (code | life | business | design) was
# retained as legacy so existing callers keep working; new fallback when
# scope auto-detect is ambiguous is `work` (was `code`). Rationale: 3 fits
# in head; if downstream training ever wants a finer split, do it via
# corpus content-classifier at training time (consistent retroactive
# labels) rather than asking the human to make a per-turn judgment call.
#
# To re-enable the 4-mode schema, set RESIDUAL_MODE = "code" and treat
# business/design as primary tags surfaced in /help. To re-collapse to 2
# (code | life), drop "work" from VALID_MODES and route fallback to
# "code". Both are reversible single-line changes.
VALID_MODES = {"code", "life", "work", "business", "design"}
PRIMARY_MODES = {"code", "life", "work"}  # surfaced in /help, auto-derived
RESIDUAL_MODE = "work"                     # fallback when scope is ambiguous

VALID_SOVEREIGNTY = {"public", "guarded", "sovereign"}


def _normalize_mode(value):
    """Normalize mode tag. Unknown/empty values fall to RESIDUAL_MODE."""
    v = (value or RESIDUAL_MODE).lower()
    return v if v in VALID_MODES else RESIDUAL_MODE


def _auto_mode(resolved_scope, explicit_mode):
    """Derive mode when caller didn't pass one explicitly.

    Piggybacks on the scope auto-detect (code/life routed via keyword +
    semantic similarity in providers.brain_rag._infer_scope_*). If scope
    landed on a known bucket, mirror it. Otherwise fall to RESIDUAL_MODE.

    Explicit caller-set mode always wins.
    """
    if explicit_mode:
        return _normalize_mode(explicit_mode)
    if resolved_scope == "life":
        return "life"
    if resolved_scope == "code":
        return "code"
    return RESIDUAL_MODE


def _normalize_sovereignty(value):
    v = (value or "public").lower()
    return v if v in VALID_SOVEREIGNTY else "public"


def _should_write_corpus(sovereignty: str) -> bool:
    """SOVEREIGN content never reaches DPO/shadow_log. Guarded + public write+tag."""
    return sovereignty != "sovereign"


def _tagged_source(base: str, mode: str, sovereignty: str) -> str:
    """Encode mode+sovereignty into the `source` field for downstream filters."""
    return f"{base}:mode={mode}:sov={sovereignty}"


_sessions = {}
_sessions_lock = threading.Lock()

# Phase 1 Subsystem 1.1: persistent session store.
# Sessions survive endpoint restart, daemon kickstart, Mac reboot.
# Without this, every `git pull && launchctl kickstart` (the compounding
# flow) wiped all conversations. See scripts/persist_sessions.py for the
# atomic-write + rotation + validation contract.
_session_store = SessionStore()

# Phase 2 — multi-thread storage. Sits alongside _sessions and shares the
# atomic-write pattern. _threads_data is keyed by chat_id (the surface
# session namespace e.g. "tg:7575125475") and each value is
# {"active_thread_id": str, "threads": {thread_id: thread_dict}}.
# When a turn comes in with `chat_id` set, we route to a thread and
# combine with the chat_id to produce the underlying _sessions key
# (`{chat_id}:{thread_id}`) — Phase 1 storage stays the source of truth
# for `turns` history; threads_data carries the routing + ceiling +
# centroid metadata.
_thread_store = ThreadStorage()
_threads_data = {}
_threads_lock = threading.Lock()


def _persist_threads():
    """Save current _threads_data snapshot to disk. Best-effort —
    failures log but don't fail the turn (response was already composed
    and the user got it; next save will retry)."""
    with _threads_lock:
        snapshot = json.loads(json.dumps(_threads_data, default=list))
    _thread_store.save(snapshot)


def _restore_threads():
    """Load persisted threads on startup. If threads.json doesn't exist
    yet, run Phase 1 → Phase 2 migration: walk current _sessions and
    materialize each `surface:chat_id` key as a chat namespace with one
    `default` thread carrying the existing turns. Returns count of
    chat-namespaces restored."""
    restored = _thread_store.load()
    with _threads_lock:
        if not restored:
            # First-run migration from Phase 1 sessions (charter #9)
            with _sessions_lock:
                sessions_snapshot = dict(_sessions)
            n_migrated = migrate_from_sessions(sessions_snapshot, _threads_data)
            if n_migrated:
                # Persist the migrated state so next restart sees a real
                # threads.json (not re-running migration each boot)
                snapshot = json.loads(json.dumps(_threads_data, default=list))
            else:
                snapshot = {}
            if snapshot:
                _thread_store.save(snapshot)
            return n_migrated
        _threads_data.update(restored)
    return len(restored)


def _resolve_thread(chat_id, user_input, payload):
    """Route the message to a thread. Returns (thread_id, thread_label,
    decision_action, prompt_text_or_none).

    - If payload['thread_id'] is explicitly set, honor it (after checking
      it exists + is active). Caller is overriding auto-routing.
    - Otherwise embed the input + run route_message() against the chat
      namespace's active thread centroids.
    - On action="prompt_user" we return prompt_text so the caller can
      surface the question (does NOT auto-route).
    - On action="hard_ceiling" we return prompt_text describing the
      refusal; caller should error out.
    """
    explicit_thread = (payload.get("thread_id") or "").strip()
    with _threads_lock:
        # Ensure the chat namespace + canonical buckets exist
        _thread_store.initialize_chat(_threads_data, chat_id)
        chat = _threads_data[chat_id]
        if explicit_thread:
            if explicit_thread in chat["threads"]:
                tdata = chat["threads"][explicit_thread]
                if tdata.get("status") == "active":
                    return (
                        explicit_thread,
                        tdata.get("label", explicit_thread),
                        "explicit",
                        None,
                    )
            # Falls through to auto-route if explicit thread doesn't exist
            # or is archived

    query_emb = embed_text(user_input)
    with _threads_lock:
        decision = route_message(
            chat_id=chat_id,
            text=user_input,
            query_embedding=query_emb,
            threads_data=_threads_data,
            storage=_thread_store,
        )
        if decision.action in ("routed", "cold_start"):
            tid = decision.thread_id
            chat = _threads_data[chat_id]
            tdata = chat["threads"].get(tid, {})
            return tid, tdata.get("label", tid), decision.action, None

        if decision.action == "prompt_user":
            label = decision.candidate_label or decision.candidate_id
            score = decision.candidate_score
            # Auto-route at the upper end of the prompt band (>= 0.65)
            # to keep dogfood frictionless while still creating new
            # threads for low-similarity inputs. Tunable post-deploy.
            if score >= 0.65 and decision.candidate_id:
                tid = decision.candidate_id
                tdata = _threads_data[chat_id]["threads"].get(tid, {})
                return tid, tdata.get("label", tid), "routed_borderline", None
            # Otherwise fall through to creating a new thread (auto-name)
            # Below the auto-route bar but above prompt-only — we'd rather
            # auto-create than block on user confirmation. Lokesh dogfood.
            from scripts.thread_router import auto_name
            new_id = auto_name(user_input)
            existing = set(_threads_data[chat_id]["threads"].keys())
            base = new_id
            counter = 2
            while new_id in existing:
                new_id = f"{base}_{counter}"
                counter += 1
            allowed, reason = _thread_store.can_create_thread(
                _threads_data, chat_id
            )
            if not allowed:
                return None, None, "hard_ceiling", (
                    f"max active threads ({_thread_store.hard_ceiling}) "
                    f"reached. Archive or merge before creating new."
                )
            thread, _ = _thread_store.create_thread(
                _threads_data, chat_id, new_id, label=new_id,
                embedding=query_emb,
            )
            return new_id, new_id, "confirmed_new", None

        if decision.action == "confirmed_new":
            new_id = decision.thread_id
            allowed, reason = _thread_store.can_create_thread(
                _threads_data, chat_id
            )
            if not allowed:
                return None, None, "hard_ceiling", (
                    f"max active threads ({_thread_store.hard_ceiling}) "
                    f"reached. Archive or merge before creating new."
                )
            thread, _ = _thread_store.create_thread(
                _threads_data, chat_id, new_id, label=new_id,
                embedding=query_emb,
            )
            return new_id, new_id, "confirmed_new", None

        if decision.action == "hard_ceiling":
            return None, None, "hard_ceiling", (
                f"max active threads ({_thread_store.hard_ceiling}) "
                f"reached. Archive or merge before creating new."
            )

    return None, None, "error", "thread routing failed"


def _record_thread_turn(chat_id, thread_id, user_input, response_text,
                        query_embedding):
    """Update thread metadata after a turn: turn_count, last_activity,
    centroid via EMA. Switches active_thread_id to the resolved thread.
    Best-effort — caller already returned the response."""
    with _threads_lock:
        chat = _threads_data.get(chat_id)
        if not chat or thread_id not in chat.get("threads", {}):
            return
        thread = chat["threads"][thread_id]
        # Append to thread.turns (mirrors session.turns; keeps thread
        # self-contained for Phase 4 conversation-RAG)
        thread.setdefault("turns", []).append((user_input, response_text))
        thread["turn_count"] = int(thread.get("turn_count", 0)) + 1
        from datetime import datetime, timezone
        thread["last_activity"] = datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        if query_embedding:
            new_centroid = update_centroid(
                thread.get("embedding") or [], query_embedding,
            )
            thread["embedding"] = new_centroid
            thread["embedding_n_messages"] = int(
                thread.get("embedding_n_messages", 0)
            ) + 1
        chat["active_thread_id"] = thread_id
    _persist_threads()


def _persist_sessions() -> None:
    """Save current `_sessions` snapshot to disk. Best-effort — failures
    log but don't crash the endpoint (next save attempt will retry)."""
    with _sessions_lock:
        snapshot = dict(_sessions)
    _session_store.save(snapshot)


# Phase 1 §1.9: sovereign breach audit log.
# `.brain/ledger/breach_log.jsonl` is append-only; every breach gets a
# full-provenance entry. Charter commitment #8: no silent breaches.
# Path resolves at call-time so tests can override via env.
BREACH_LOG_PATH = BRAIN_PATH / "ledger" / "breach_log.jsonl"

# Phase 1 §1.11: refusal capture log.
# `.brain/ledger/refusal_log.jsonl` is append-only; every detected
# Anthropic refusal gets logged with full context for v15 anti-refusal
# corpus assembly. File scaffold landed M2 (charter #5 — compounding
# hooks day 1); M5 wires the actual capture from composer responses.
REFUSAL_LOG_PATH = BRAIN_PATH / "ledger" / "refusal_log.jsonl"


def _append_breach_log(entry: dict) -> None:
    """Append a breach record to .brain/ledger/breach_log.jsonl.

    Best-effort: file-write failures log but don't crash the turn (the
    breach already happened — audit-log loss is a separate failure
    mode). Caller should check the returned bool only for monitoring.
    """
    try:
        BREACH_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with BREACH_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except OSError as e:
        # Don't raise; audit-log loss shouldn't break the turn.
        # But DO log to stderr so the user/operator notices.
        try:
            print(f"[breach_log] WARN: append failed ({e}). "
                  f"Entry: {entry.get('id', '?')} "
                  f"session={entry.get('session_id', '?')}",
                  file=sys.stderr)
        except Exception:
            pass


def _append_refusal_log(entry: dict) -> None:
    """Append a refusal record to .brain/ledger/refusal_log.jsonl.

    Best-effort, mirror of _append_breach_log. Captures Anthropic-typical
    refusals from Sonnet/Opus composer output. Used by v15 anti-refusal
    corpus assembly.
    """
    try:
        REFUSAL_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with REFUSAL_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except OSError as e:
        try:
            print(f"[refusal_log] WARN: append failed ({e}). "
                  f"Entry: {entry.get('id', '?')} "
                  f"session={entry.get('session_id', '?')}",
                  file=sys.stderr)
        except Exception:
            pass


def _restore_sessions() -> int:
    """Load persisted sessions on startup. Migrates in-memory state if
    the persistent file doesn't exist yet (first run after Phase 1
    deploy). Returns count restored."""
    restored = _session_store.load()
    with _sessions_lock:
        if not restored and _sessions:
            # No persistent file but we have in-memory state (rare —
            # only on first boot after Phase 1 deploy). Migrate.
            migrate_in_memory(dict(_sessions), _session_store)
            return 0
        _sessions.update(restored)
    return len(restored)


def _get_session(session_id):
    if not session_id:
        session_id = f"anon-{uuid.uuid4().hex[:8]}"
    with _sessions_lock:
        s = _sessions.setdefault(session_id, {
            "turns": [],
            "last_verdict_id": None,
            "created": time.time(),
            "mode": "code",
            "sovereignty": "guarded",
        })
    return session_id, s


def _estimate_tokens(text: str) -> int:
    """Rough token estimator. ~4 chars/token for English+code mix.

    Phase 1: simple heuristic, no extra dependency. If a future phase
    needs higher accuracy (model-specific tokenization), replace with
    tiktoken for OpenAI-style or anthropic.tokenize for exact Anthropic.
    Heuristic is conservative-low, so trim is gentler than truth.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


def _should_skip_tb_grounding(payload, principal_model):
    """Decide whether to skip the TB grounding pass for composer-tier turns.

    Phase 5 prep (2026-05-10). Resolution order:
      1. payload['skip_tb_grounding']  (per-turn override)
      2. env TB_GROUND_FOR_COMPOSER = on | off | auto (default 'auto')
      3. auto = skip when psutil.virtual_memory().percent > TB_GROUND_RAM_THRESHOLD_PCT (85)

    Only fires for sonnet/opus principals. TB-only / sovereign always runs TB.
    """
    if principal_model not in ("sonnet", "opus"):
        return False
    if "skip_tb_grounding" in payload:
        return bool(payload["skip_tb_grounding"])
    mode = os.environ.get("TB_GROUND_FOR_COMPOSER", "auto").lower()
    if mode == "off":
        return True
    if mode == "on":
        return False
    try:
        import psutil
        threshold = float(os.environ.get("TB_GROUND_RAM_THRESHOLD_PCT", "85"))
        return psutil.virtual_memory().percent > threshold
    except ImportError:
        return False


def _today_anchor() -> str:
    """Return a single-line [TODAY] block for prompt injection.

    Phase 3.5 temporal-context (2026-05-10) — TB v14 + Sonnet/Opus don't
    know the current date by default. Without this anchor, models treat
    "tomorrow" / "next week" / "last month" inside retrieved chunks as
    relative to TODAY (which they can't see), not relative to the chunk's
    own send-time. The Anjali-meetup-yesterday bug from 2026-05-10
    dogfood is the canonical example.

    Format: "[TODAY] 2026-05-10 (Saturday). Treat any 'tomorrow / yesterday /
    last week' inside retrieved BRAIN KNOWLEDGE chunks as relative to that
    chunk's [|when] tag, NOT this date."
    """
    now = datetime.now(timezone.utc).astimezone()
    return (
        f"[TODAY] {now.strftime('%Y-%m-%d (%A, %H:%M %Z')}). "
        f"Treat any 'tomorrow / yesterday / last week' inside retrieved "
        f"BRAIN KNOWLEDGE chunks as relative to that chunk's [|when] tag, "
        f"NOT this date."
    )


def _format_history(turns, token_budget: int = HISTORY_TOKEN_BUDGET,
                    assistant_label: str = "TB"):
    """Token-budget-aware history formatter.

    Walks turns most-recent-first, accumulating until budget exhausted.
    Older turns drop out of THIS prompt — but they remain in
    `_sessions[id]["turns"]` indefinitely for Phase 4+ conversation-RAG
    retrieval by topical match.

    assistant_label: "TB" for TB-side prompts (original behavior),
                     "Assistant" for composer prompts (Sonnet/Opus see
                     a clean dialog without TB role-play).

    Charter commitment #2: token-budget, never count-budget. The previous
    HISTORY_TURNS=4 cap is retired. Fresh sessions can run 1000+ turns
    in working memory without artificial truncation.
    """
    if not turns:
        return ""
    header = "[CONVERSATION HISTORY]"
    overhead = _estimate_tokens(header)
    selected = []
    used = 0
    # Walk newest → oldest, include each that fits
    for u, a in reversed(turns):
        u = u or ""
        a = a or ""
        block_text = f"User: {u}\n{assistant_label}: {a}"
        cost = _estimate_tokens(block_text)
        if used + cost + overhead > token_budget:
            break
        selected.append((u, a))
        used += cost
    selected.reverse()
    if not selected:
        return ""
    out = [header]
    for u, a in selected:
        out.append(f"User: {u}")
        out.append(f"{assistant_label}: {a}")
    return "\n".join(out)


def _auto_correction_pass(session, user_input, model, use_llm_judge=False,
                           mode="code", sovereignty="guarded",
                           quality_meta=None):
    """If prior turn exists and user_input looks like a correction, write it.

    Default: heuristic-only (use_llm_judge=False). v14 LLM-judge unreliable;
    bias toward capture — false positives filter at training time, false
    negatives lose signal forever.

    SOVEREIGN turns short-circuit BEFORE the corpus write; we still report
    the detection so caller knows the regex fired, but no DPO pair lands.

    quality_meta: dict of TB-quality-compound fields to merge into the DPO
    pair's extra_metadata (principal_model, quality_tier, verifier_used,
    template_used, min_dense_score, rag_chunks_pre/post). When the prior
    turn was generated under one quality tier and the correction lands in
    another, these fields tag the prior turn's settings so v15 training
    can weight pairs by source quality.
    """
    if not session["turns"]:
        return None
    last_user, last_tb = session["turns"][-1]
    verdict = detect_correction(user_input, last_tb, model=model,
                                use_llm=use_llm_judge)
    if verdict not in ("yes", "partial", "heuristic"):
        return None
    if not _should_write_corpus(sovereignty):
        return {"detected": verdict, "skipped": "sovereign"}
    try:
        from mcp_server_nucleus.runtime.align_ops import record_correction
        meta = {
            "mode": mode, "sovereignty": sovereignty,
            "surface": "tb_endpoint", "source_kind": "auto_correction",
        }
        if quality_meta:
            meta.update(quality_meta)
        r = record_correction(
            context=last_tb,
            correction=user_input,
            expected=last_user,
            severity="medium" if verdict == "yes" else "low",
            extra_metadata=meta,
        )
        return {
            "detected": verdict,
            "verdict_id": r.get("verdict_id"),
            "delta_id": r.get("delta_id"),
            "pref_id": r.get("pref_id"),
            "mode": mode,
            "sovereignty": sovereignty,
        }
    except Exception as e:
        return {"detected": verdict, "error": f"{type(e).__name__}: {e}"}


def handle_turn(payload):
    user_input = (payload.get("input") or "").strip()
    if not user_input:
        return {"ok": False, "error": "missing 'input'"}
    session_id = payload.get("session_id")
    # Phase 2 — multi-thread routing. Caller (bot/REPL) passes chat_id
    # (the surface namespace e.g. "tg:7575125475"). The endpoint routes
    # the message to a thread and uses {chat_id}:{thread_id} as the
    # underlying _sessions key — Phase 1 storage continues to track the
    # `turns` history, threads_data carries routing/ceiling/centroid.
    # Without chat_id, the endpoint falls back to Phase 1 behavior.
    chat_id = (payload.get("chat_id") or "").strip()
    thread_id = None
    thread_label = None
    thread_decision_action = None
    query_embedding_for_thread = []
    if chat_id:
        if not session_id:
            session_id = chat_id  # legacy alignment for /tb/stats etc.
        thread_id, thread_label, thread_decision_action, prompt_text = (
            _resolve_thread(chat_id, user_input, payload)
        )
        if thread_decision_action == "hard_ceiling":
            return {
                "ok": False,
                "error": prompt_text,
                "chat_id": chat_id,
                "thread_decision_action": "hard_ceiling",
            }
        if thread_id:
            # Re-derive session_id to be the threaded variant. Phase 1
            # _sessions keeps independent turns history per thread.
            session_id = f"{chat_id}:{thread_id}"
            # Embed once for both routing + post-turn centroid update
            if not query_embedding_for_thread:
                query_embedding_for_thread = embed_text(user_input)
    scope = payload.get("scope") or "auto"
    do_rerank = bool(payload.get("rerank", False))
    rerank_explicit = "rerank" in payload
    model = payload.get("model") or DEFAULT_MODEL
    polish_mode = payload.get("polish_mode") or "tb_only"
    external_draft = payload.get("external_draft") or ""
    use_llm_judge = bool(payload.get("use_llm_judge", False))
    explicit_mode = payload.get("mode")
    sovereignty = _normalize_sovereignty(payload.get("sovereignty"))

    # ── TB Quality Compound — payload kwargs ──────────────────────────
    # principal_model: tb | sonnet | auto. auto resolves to env default
    #   (mode=life → sonnet by default; code/work → tb). HARD GATE: when
    #   sovereignty=sovereign, always tb regardless of payload/env.
    # prompt_template: free | constrained | auto. auto = constrained for
    #   life+tb path; free elsewhere.
    # min_dense_score: float threshold for RAG chunks. Default from env
    #   TB_RAG_MIN_DENSE.
    # verifier: off | haiku. Off by default (opt-in via /quality verified).
    # quality_tier: fast | good | verified. Echoed back; bot supplies it
    #   from /quality state. DPO pairs get tagged with this field for
    #   v15 training weighting.
    principal_explicit = "principal_model" in payload
    template_explicit = "prompt_template" in payload
    verifier_explicit = "verifier" in payload
    requested_principal = (payload.get("principal_model") or "auto").lower()
    requested_template = (payload.get("prompt_template") or "auto").lower()
    requested_verifier = (payload.get("verifier") or TB_VERIFIER_DEFAULT).lower()
    quality_tier = (payload.get("quality_tier") or "good").lower()
    if quality_tier not in ("fast", "good", "verified", "ultra"):
        quality_tier = "good"
    try:
        req_min_dense = float(payload.get("min_dense_score", TB_RAG_MIN_DENSE))
    except (TypeError, ValueError):
        req_min_dense = TB_RAG_MIN_DENSE
    req_min_dense = max(0.0, min(req_min_dense, 1.0))
    # UNUSED until lever-4 rewire — see build_full_context call site below.
    # Env-flag plumbing kept wired so re-activation is a one-line restore.
    # Per-turn inference levers; defaults preserve existing behavior.
    # temperature: 0.0 (deterministic) → 1.0+ (creative). Default 0.7.
    # num_predict: max output tokens. Default DEFAULT_NUM_PREDICT (env-tunable).
    try:
        req_temperature = float(payload.get("temperature", 0.7))
    except (TypeError, ValueError):
        req_temperature = 0.7
    req_temperature = max(0.0, min(req_temperature, 2.0))
    num_predict_explicit = "num_predict" in payload
    try:
        req_num_predict = int(payload.get("num_predict", DEFAULT_NUM_PREDICT))
    except (TypeError, ValueError):
        req_num_predict = DEFAULT_NUM_PREDICT
    req_num_predict = max(8, min(req_num_predict, 4096))

    # Resolve scope. scope=auto → None lets brain_rag run full keyword +
    # semantic detect downstream. For the mode-auto hint, peek at the
    # cheap keyword-only detector here (instant regex, no embedding call)
    # so /scope auto on a clearly-life or clearly-code prompt still flows
    # to the matching mode tag instead of falling to RESIDUAL_MODE.
    resolved_scope = None if scope == "auto" else scope
    mode_hint_scope = resolved_scope
    if mode_hint_scope is None:
        try:
            from providers.brain_rag import _infer_scope
            mode_hint_scope = _infer_scope(user_input)  # "code" | "life" | None
        except Exception:
            mode_hint_scope = None
    # mode-auto: caller's explicit mode wins; else mirror keyword-detected
    # scope; else fall to RESIDUAL_MODE. See _auto_mode comments above.
    mode = _auto_mode(mode_hint_scope, explicit_mode)

    # Phase 1: LIFE_NUM_PREDICT cap removed (DEC-009). Citation-loop
    # protection is now handled by ANTI_CITATION_STOPS, not by truncating
    # output length. Caller's num_predict is honored (clamped only by
    # the upper safety bound 4096).
    # Rerank-off-for-life still useful: rerank picks "best" of bad pool
    # when corpus skews code-dominated. Stays unless caller explicitly sets.
    if mode == "life" and not rerank_explicit:
        do_rerank = False

    # ── Resolve effective principal_model + verifier + template ───────
    # Sovereign HARD GATE: data must stay local. Sonnet/Haiku via
    # `claude -p` route through Anthropic API. Mirror of PR #231's
    # _should_write_corpus gate applied to the inference path.
    #
    # BREACH KNOB (Phase 1 §1.9): explicit `anthropic_breach=true` payload
    # field bypasses the gate FOR THIS TURN ONLY. Required for uncensored
    # deep reasoning today (until v15 closes the local-quality gap). Every
    # breach is audit-logged to .brain/ledger/breach_log.jsonl with full
    # provenance — charter commitment #8: no silent breaches.
    # corpus_written stays False on sovereign turns regardless of breach
    # (breach unlocks composer routing, NOT corpus persistence).
    sovereign_gate_fired = False
    sovereign_breach_active = False
    breach_requested = bool(payload.get("anthropic_breach"))

    if sovereignty == "sovereign" and not breach_requested:
        # Standard sovereign hard-gate
        principal_model = "tb"
        verifier = "off"
        sovereign_gate_fired = True
    else:
        if sovereignty == "sovereign" and breach_requested:
            sovereign_breach_active = True
        if requested_principal == "auto":
            # env may force; otherwise: life → sonnet, others → tb
            if TB_PRINCIPAL_MODE == "auto":
                principal_model = "sonnet" if mode == "life" else "tb"
            else:
                principal_model = TB_PRINCIPAL_MODE
        else:
            principal_model = requested_principal
        if principal_model not in ("tb", "sonnet", "opus"):
            principal_model = "tb"
        verifier = requested_verifier if verifier_explicit else TB_VERIFIER_DEFAULT
        if verifier not in ("off", "haiku"):
            verifier = "off"

    # /quality verified implies verifier=haiku unless caller overrode.
    if quality_tier == "verified" and not verifier_explicit and not sovereign_gate_fired:
        verifier = "haiku"
    # /quality fast implies principal=tb unless caller overrode.
    if quality_tier == "fast" and not principal_explicit and not sovereign_gate_fired:
        principal_model = "tb"
    # /quality ultra implies principal=opus + verifier=haiku unless caller
    # overrode. Defense-in-depth: the bot/REPL also resolve this client-side
    # via _QUALITY_PRINCIPAL/_QUALITY_VERIFIER, but a direct curl/iOS Shortcut
    # that only sends quality_tier=ultra would otherwise default to good.
    if quality_tier == "ultra" and not sovereign_gate_fired:
        if not principal_explicit:
            principal_model = "opus"
        if not verifier_explicit:
            verifier = "haiku"

    # Resolve prompt template. constrained applies only to TB-only path
    # (Sonnet handles its own composition shape).
    if requested_template == "auto":
        if principal_model == "tb" and mode == "life" and TB_PROMPT_TEMPLATE != "free":
            template_used = "constrained"
        else:
            template_used = "free"
    else:
        template_used = requested_template if requested_template in ("free", "constrained") else "free"

    session_id, sess = _get_session(session_id)
    sess["mode"] = mode
    sess["sovereignty"] = sovereignty
    write_corpus = _should_write_corpus(sovereignty)

    # quality_meta packs the new TB-quality-compound fields so they ride
    # along on every DPO pair this turn produces (auto_correction,
    # polish_external_then_tb, explicit reject/correction).
    quality_meta = {
        "principal_model": principal_model,
        "quality_tier": quality_tier,
        "verifier_used": verifier if verifier != "off" else "none",
        "template_used": template_used,
        "min_dense_score": req_min_dense,
    }

    auto_corr = _auto_correction_pass(sess, user_input, model,
                                      use_llm_judge=use_llm_judge,
                                      mode=mode, sovereignty=sovereignty,
                                      quality_meta=quality_meta)
    rag_chunks_pre_filter = 0
    # NOTE(valiant-mixing-nebula:lever-4): min_dense_score kwarg dropped from
    # this call on 2026-05-17. tb_endpoint.py was restored from `main` during
    # TB-revive mid-Eidetic-pause, but providers/brain_rag.py on release/v1.3.0
    # does not accept the kwarg — passing it raised TypeError silently caught
    # below, emptying RAG every turn. Plan: lever-4 defaults to off in
    # valiant-mixing-nebula.md; today's drop matches plan's default state.
    # Re-activation: ship bundled-levers PR post-2026-08-08 gate, which rewires
    # brain_rag.build_full_context to accept the kwarg; then restore the line.
    try:
        context, results = build_full_context(
            user_input, brain_path=BRAIN_PATH, scope=resolved_scope,
        )
        # rag_chunks_pre_filter is not exposed by build_full_context's API
        # (it returns post-filter results); the post-count below is the
        # value v15 training will actually want. We track post here and
        # leave pre as 0 unless a future API change surfaces it.
    except Exception as e:
        context, results = "", []
        rag_error = f"{type(e).__name__}: {e}"
    else:
        rag_error = None

    if do_rerank and results:
        results = cross_rerank(user_input, results, top_n=8, model=model)
        cold = format_rag_context(results, max_words=BUDGET_COLD)
        if cold:
            context = (context or "") + "\n\n[RERANKED COLD KNOWLEDGE]\n" + cold

    if polish_mode == "external_then_tb" and external_draft:
        prompt_extra = (
            f"\n\n[EXTERNAL DRAFT — polish/ground this against the brain context above]\n"
            f"{external_draft}\n\n[Polished version]:"
        )
    else:
        prompt_extra = ""

    # ── Inject quality preambles (Phase 1 §1.8: ALL opt-in) ──────────
    # Charter #6: hard "DO NOT" preambles get echoed by composer under
    # pressure (the Opus-parroting bug from 2026-05-08 morning). All
    # preambles default OFF; opt-in via env flag or per-turn payload.
    # /raw=true payload field strips ALL preambles regardless of env.
    raw_mode = bool(payload.get("raw"))
    preambles = []
    if not raw_mode:
        if TB_ANTIMIX == "on":
            if mode == "life":
                preambles.append(composer_templates.ANTIMIX_LIFE_PREAMBLE)
            elif mode == "code":
                preambles.append(composer_templates.ANTIMIX_CODE_PREAMBLE)
        if TB_GROUNDING_ONLY == "on" and principal_model in ("sonnet", "opus"):
            preambles.append(composer_templates.GROUNDING_ONLY_PREAMBLE)
        elif template_used == "constrained":
            # Constrained template still gates on prompt_template payload/env,
            # not on TB_ANTIMIX. It's a different signal (output-shape, not
            # tone-anti-mix). User can opt-in via prompt_template=constrained.
            preambles.append(composer_templates.CONSTRAINED_LIFE_PREAMBLE)
    preamble_block = "\n".join(preambles)

    history = _format_history(sess["turns"], token_budget=HISTORY_TOKEN_BUDGET)
    # Phase 3.5 temporal-context (2026-05-10): inject today's date so TB +
    # composer can reason about staleness in retrieved chunks. Without this,
    # the model treats "tomorrow" inside a 30-day-old chunk as if today.
    # Anjali-meetup bug from 2026-05-10 dogfood.
    today_anchor = _today_anchor()
    parts = [p for p in [today_anchor, context, preamble_block, history,
                         prompt_extra, f"User: {user_input}", "TB:"] if p]
    prompt = "\n\n".join(parts)

    # ── TB call ──────────────────────────────────────────────────
    # Phase 5 prep (2026-05-10): for sonnet/opus tiers, TB grounding
    # pass is skippable (Anjali-meetup dogfood proved TB biases Opus
    # toward stale "tomorrow" reads). Skip is opt-in via payload OR
    # env TB_GROUND_FOR_COMPOSER=off, OR auto when RAM > 85%.
    # TB-only / sovereign paths always run TB.
    skip_tb_grounding = _should_skip_tb_grounding(payload, principal_model)
    tb_text = ""
    tb_ms = 0
    if not skip_tb_grounding:
        tb_text, tb_ms = tb._ollama_generate(
            prompt, model,
            timeout=DEFAULT_TIMEOUT,
            num_predict=req_num_predict,
            temperature=req_temperature,
            stop=ANTI_CITATION_STOPS,
        )

        if tb_text is None:
            return {
                "ok": False,
                "error": "tb_generate_failed",
                "duration_ms": tb_ms,
                "auto_correction": auto_corr,
                "rag_error": rag_error,
            }

    # ── Sonnet branch (when principal_model=sonnet) ───────────────────
    # TB just produced a grounding summary; Sonnet now composes the
    # actual answer using TB's text as a caveat-banner-wrapped advice
    # block. On Sonnet error, fall back to TB-only with banner.
    sonnet_ms = 0
    sonnet_meta = {}
    sonnet_fell_back = False
    if principal_model in ("sonnet", "opus"):
        # Compose a clean prompt for Sonnet/Opus. Phase 1:
        #   §1.3 composer sees the full conversation history (token-budget)
        #   §1.4 voice anchor preamble + selected exemplars per turn
        #   §1.7 no-moralize system message strips assistant framing
        composer_history = _format_history(
            sess["turns"],
            token_budget=HISTORY_TOKEN_BUDGET,
            assistant_label="Assistant",
        )
        sonnet_prompt_parts = []
        # Phase 3.5 temporal-context (2026-05-10): today's date FIRST so
        # composer reasoning anchors to it before consuming retrieved
        # chunks (which now carry their own [|when] tags via Phase 3.5
        # format_rag_context).
        sonnet_prompt_parts.append(_today_anchor())
        # Voice preamble first (priming the composer's tone before content)
        if TB_VOICE == "on":
            try:
                voice_block = build_voice_preamble(query=user_input)
                if voice_block:
                    sonnet_prompt_parts.append(voice_block)
            except Exception:
                # Voice subsystem failures don't break the turn
                pass
        # No-moralize system instruction
        if TB_NO_MORALIZE == "on":
            sonnet_prompt_parts.append(
                "[SYSTEM]\n" + NO_MORALIZE_SYSPROMPT.strip()
            )
        # Conversation history
        if composer_history:
            sonnet_prompt_parts.append(composer_history)
        # Current query
        sonnet_prompt_parts.append(f"[CURRENT USER QUERY]\n{user_input}")
        # Composition instruction (kept short; voice preamble carries
        # the bigger style guidance)
        sonnet_prompt_parts.append(
            "Compose the answer in the voice above. Use TB's grounding as "
            "personalized context where relevant; ignore it where it doesn't "
            "fit. Refer to history naturally. No manufactured markdown headers "
            "unless the answer truly needs them."
        )
        sonnet_prompt = "\n\n".join(sonnet_prompt_parts)
        # principal_model is "sonnet" or "opus" here (tb branch handled above).
        # compose_with_sonnet accepts any --model alias the claude CLI knows;
        # name kept for back-compat with run_tb_principal callers.
        sonnet_text, sonnet_ms, sonnet_meta = compose_with_sonnet(
            prompt=sonnet_prompt,
            query_summary=user_input[:140],
            tb_advice=tb_text,
            timeout=TB_SONNET_TIMEOUT,
            model=principal_model,
        )
        if is_principal_error(sonnet_text):
            sonnet_fell_back = True
            # Phase 5 prep: if skip-TB-grounding was active, tb_text is
            # empty. Fall back to running TB now (full principal mode)
            # so user gets a real answer, not empty-string + banner.
            if not tb_text and skip_tb_grounding:
                fb_text, fb_ms = tb._ollama_generate(
                    prompt, model,
                    timeout=DEFAULT_TIMEOUT,
                    num_predict=req_num_predict,
                    temperature=req_temperature,
                    stop=ANTI_CITATION_STOPS,
                )
                tb_text = fb_text or ""
                tb_ms += fb_ms
            text = tb_text + (
                f"\n\n— [SONNET FALLBACK — TB-only output; "
                f"reason: {sonnet_text[:200]}]"
            )
        else:
            text = sonnet_text
    else:
        text = tb_text

    ms = tb_ms + sonnet_ms

    # ── Breach audit log (Phase 1 §1.9) ──────────────────────────────
    # If sovereign+breach was active AND composer (sonnet/opus) ran
    # successfully, append full provenance to breach_log.jsonl and
    # prepend banner to user-visible output. corpus_written is already
    # False on sovereign turns (existing _should_write_corpus gate);
    # breach unlocks composer routing only, NOT corpus persistence.
    breach_id = None
    if sovereign_breach_active and principal_model in ("sonnet", "opus"):
        # Build chunk-confidentiality summary (Phase 4 will populate
        # actual confidentiality tags; Phase 1 records what we know now)
        chunk_sources = []
        for r in (results or []):
            src = r.get("source", "")
            if src:
                top_dir = src.split("/", 1)[0] if "/" in src else src
                chunk_sources.append(top_dir)
        chunk_sources_unique = sorted(set(chunk_sources))
        breach_id = f"breach-{int(time.time() * 1000)}-{uuid.uuid4().hex[:6]}"
        breach_entry = {
            "id": breach_id,
            "ts": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "thread_id": session_id,  # Phase 2 will distinguish thread from session
            "sovereignty_before": "sovereign",
            "sovereignty_after": "sovereign+breach",
            "principal_model": principal_model,
            "verifier": verifier,
            "quality_tier": quality_tier,
            "mode": mode,
            "chunks_count": len(results or []),
            "chunk_source_dirs": chunk_sources_unique,
            "query_chars": len(user_input),
            "query_summary": user_input[:200],
            "tb_duration_ms": tb_ms,
            "composer_duration_ms": sonnet_ms,
            "composer_fell_back": sonnet_fell_back,
            "user_consent_explicit": True,  # `anthropic_breach=true` is opt-in
        }
        _append_breach_log(breach_entry)
        # Banner prepended (visible in every surface)
        breach_banner = (
            "⚠ BREACH: turn data sent to Anthropic (sovereignty waived). "
            f"Audit: {breach_id}\n\n"
        )
        text = breach_banner + text

    # ── Refusal capture (Phase 1 §1.11) ──────────────────────────────
    # When composer (Sonnet/Opus) refuses content, capture full context
    # to refusal_log.jsonl. Feeds v15 anti-refusal corpus. Detection is
    # lightweight regex — Phase 5+ refines with haiku LLM-judge for
    # borderline cases.
    refusal_id = None
    refusal_detected = False
    if (principal_model in ("sonnet", "opus") and not sonnet_fell_back
            and text):
        try:
            verdict = detect_refusal(text)
            if verdict.get("refused"):
                refusal_detected = True
                refusal_id = (
                    f"refusal-{int(time.time() * 1000)}-{uuid.uuid4().hex[:6]}"
                )
                _append_refusal_log({
                    "id": refusal_id,
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "session_id": session_id,
                    "principal_model": principal_model,
                    "quality_tier": quality_tier,
                    "mode": mode,
                    "sovereignty": sovereignty,
                    "sovereign_breach_active": sovereign_breach_active,
                    "query": user_input,
                    "refusal_text": text[:1000],
                    "pattern_matched": verdict.get("pattern"),
                    "snippet": verdict.get("snippet"),
                    # Phase 5+ will populate user_reaction when align
                    # button arrives (👎 with correction → linked here)
                })
        except Exception as e:
            print(f"[refusal_log] WARN: detection failed ({e})",
                  file=sys.stderr)

    # ── Voice post-pass strip (Phase 1 §1.5) ─────────────────────────
    # Deterministic regex layer that removes assistant boilerplate
    # ("I'm here to help", "let me know if", "I hope that helps", etc.).
    # Conservative: only strips phrases that almost never appear in
    # Lokesh's voice. Won't damage legitimate Lokesh-toned output.
    # Skipped on TB-only path where TB already speaks short.
    if TB_VOICE_STRIP == "on" and principal_model in ("sonnet", "opus") and not sonnet_fell_back:
        try:
            text = strip_assistant_tone(text)
        except Exception:
            pass

    # ── Verifier post-pass (when verifier=haiku) ──────────────────────
    verifier_outcome = {"verdict": "skipped", "reason": "off"}
    if verifier == "haiku" and not sovereign_gate_fired and text:
        verifier_outcome = verify_grounding(
            answer=text,
            retrieved_chunks=results or [],
            query=user_input,
            timeout=TB_HAIKU_TIMEOUT,
        )
        banner = banner_for_verdict(verifier_outcome)
        if banner:
            text = text + banner

    try:
        tb.log_ollama_call("ENDPOINT", model, prompt, text,
                           exit_code=0, duration_ms=ms,
                           task_id=f"endpoint:{session_id}")
    except Exception:
        pass

    if write_corpus:
        try:
            from providers.brain_rag import log_shadow_turn
            log_shadow_turn(
                query=user_input, response=text, model=model,
                rag_results=results, rag_context=context,
                session_id=f"{session_id}:mode={mode}:sov={sovereignty}",
                latency_ms=ms,
            )
        except Exception:
            pass

    if polish_mode == "external_then_tb" and external_draft and write_corpus:
        try:
            from mcp_server_nucleus.runtime.align_ops import record_correction
            polish_meta = {
                "mode": mode, "sovereignty": sovereignty,
                "surface": "tb_endpoint",
                "source_kind": "polish_external_then_tb",
            }
            polish_meta.update(quality_meta)
            r = record_correction(
                context=external_draft, correction=text,
                expected=user_input, severity="low",
                extra_metadata=polish_meta,
            )
            polish_pref_id = r.get("pref_id")
        except Exception:
            polish_pref_id = None
    else:
        polish_pref_id = None

    # Phase 5 prep (2026-05-10): TB-vs-composer DPO pair logger.
    # Every composer-tier turn where TB grounding ran AND composer
    # succeeded produces a comparison: rejected=tb_text (TB v14 read),
    # chosen=sonnet_text (Sonnet/Opus output). Estimated 5-10x training
    # corpus growth on /quality good|verified|ultra usage.
    tb_vs_composer_pref_id = None
    if (write_corpus
        and principal_model in ("sonnet", "opus")
        and not sonnet_fell_back
        and not skip_tb_grounding
        and tb_text and len(tb_text.strip()) >= 50
        and sonnet_text and not is_principal_error(sonnet_text)):
        try:
            from mcp_server_nucleus.runtime.align_ops import record_correction
            composer_meta = {
                "mode": mode, "sovereignty": sovereignty,
                "surface": "tb_endpoint",
                "source_kind": "tb_vs_composer",
            }
            composer_meta.update(quality_meta)
            r = record_correction(
                context=user_input,
                correction=sonnet_text,
                expected=tb_text,
                severity="info",
                extra_metadata=composer_meta,
            )
            tb_vs_composer_pref_id = r.get("pref_id")
        except Exception:
            tb_vs_composer_pref_id = None

    sess["turns"].append((user_input, text))
    # Stash quality_meta so subsequent /tb/align (button presses) tag the
    # explicit-correction DPO pair with the same fields the auto pair got.
    sess["last_quality_meta"] = dict(quality_meta)
    # Phase 1: persist after every turn. Endpoint restart no longer
    # wipes conversations. _persist_sessions is best-effort — a failed
    # save logs but doesn't fail the turn (the response was already
    # composed and the user gets it; next turn's save will retry).
    _persist_sessions()
    # Phase 2: also update thread metadata (turn_count, last_activity,
    # centroid EMA) when chat_id was provided. Best-effort same as
    # _persist_sessions; turn already returned to the caller.
    if chat_id and thread_id:
        try:
            _record_thread_turn(
                chat_id, thread_id, user_input, text,
                query_embedding_for_thread,
            )
        except Exception as e:
            logging.warning("thread state update failed (%s)", e)

    return {
        "ok": True,
        "output": text,
        "session_id": session_id,
        "duration_ms": ms,
        "rag_chunks": len(results),
        "context_chars": len(context or ""),
        "scope_requested": scope,
        "rerank_used": do_rerank,
        "polish_mode": polish_mode,
        "polish_pref_id": polish_pref_id,
        "auto_correction": auto_corr,
        "rag_error": rag_error,
        "mode": mode,
        "sovereignty": sovereignty,
        "corpus_written": write_corpus,
        "temperature": req_temperature,
        "num_predict": req_num_predict,
        # TB Quality Compound fields
        "principal_model": principal_model,
        "quality_tier": quality_tier,
        "verifier_used": verifier if verifier != "off" else "none",
        "verifier_verdict": verifier_outcome.get("verdict") if verifier == "haiku" else None,
        "verifier_unsupported_claims": verifier_outcome.get("claims_unsupported") if verifier == "haiku" else None,
        "template_used": template_used,
        "min_dense_score": req_min_dense,
        "sonnet_fell_back": sonnet_fell_back,
        "sonnet_duration_ms": sonnet_ms,
        "tb_duration_ms": tb_ms,
        "skip_tb_grounding": skip_tb_grounding,
        "tb_vs_composer_pref_id": tb_vs_composer_pref_id,
        "sovereign_gate_fired": sovereign_gate_fired,
        # Phase 1 §1.9: breach provenance in response (audit-trail handle)
        "sovereign_breach_active": sovereign_breach_active,
        "breach_id": breach_id,
        # Phase 1 §1.11: refusal capture
        "refusal_detected": refusal_detected,
        "refusal_id": refusal_id,
        # Phase 2 §2.8: multi-thread surfacing
        "chat_id": chat_id or None,
        "thread_id": thread_id,
        "thread_label": thread_label,
        "thread_decision_action": thread_decision_action,
    }


def handle_align(payload):
    session_id = payload.get("session_id")
    verdict = (payload.get("verdict") or "").lower()
    correction = payload.get("correction") or ""
    note = payload.get("note") or ""
    reason = payload.get("reason") or ""
    mode_override = payload.get("mode")
    sov_override = payload.get("sovereignty")

    if not session_id:
        return {"ok": False, "error": "missing 'session_id'"}

    with _sessions_lock:
        sess = _sessions.get(session_id)
    if not sess or not sess["turns"]:
        return {"ok": False, "error": "no prior turn for session"}

    mode = _normalize_mode(mode_override or sess.get("mode"))
    sovereignty = _normalize_sovereignty(sov_override or sess.get("sovereignty"))
    if not _should_write_corpus(sovereignty):
        return {"ok": True, "verdict": verdict or "noop",
                "skipped": "sovereign",
                "mode": mode, "sovereignty": sovereignty}

    last_user, last_tb = sess["turns"][-1]
    try:
        from mcp_server_nucleus.runtime.align_ops import (
            record_correction, record_approval, record_rejection,
        )
        if verdict in ("good", "approve", "ok"):
            r = record_approval(context=last_tb, notes=note or last_user)
            # Phase 1 §1.6: 👍 turns become voice-corpus candidates.
            # Phase 5 will: cron promote diversity-sampled candidates →
            # trusted pool. Phase 1 just appends to candidates_live.jsonl.
            try:
                prior_q = sess.get("last_quality_meta") or {}
                append_voice_candidate(
                    turn_text=last_tb,
                    mode=mode,
                    quality_tier=prior_q.get("quality_tier", ""),
                    source="thumbs_up",
                )
            except Exception:
                pass
            return {"ok": True, "verdict": "approved",
                    "verdict_id": r.get("verdict_id")}
        # NB: "reject" was previously aliased with bad/correct (DPO write).
        # Now it routes to verdict-only — closes the gap where 👎 without
        # a correction either lost the signal or polluted DPO.
        # Pull the last turn's quality_meta so explicit-correction pairs
        # carry the same TB-quality-compound fields the auto pair did.
        prior_quality = sess.get("last_quality_meta") or {}
        if verdict in ("reject", "reject_only", "just_bad"):
            reject_meta = {
                "mode": mode, "sovereignty": sovereignty,
                "surface": "tb_endpoint",
                "source_kind": "explicit_reject_no_correction",
            }
            reject_meta.update(prior_quality)
            r = record_rejection(
                context=last_tb, reason=reason or note,
                severity="medium",
                extra_metadata=reject_meta,
            )
            return {"ok": True, "verdict": "rejected",
                    "verdict_id": r.get("verdict_id"),
                    "mode": mode, "sovereignty": sovereignty}
        if verdict in ("bad", "correct"):
            if not correction:
                return {"ok": False,
                        "error": "verdict=bad requires 'correction'"}
            corr_meta = {
                "mode": mode, "sovereignty": sovereignty,
                "surface": "tb_endpoint", "source_kind": "explicit_align",
            }
            corr_meta.update(prior_quality)
            r = record_correction(
                context=last_tb, correction=correction,
                expected=last_user, severity="medium",
                extra_metadata=corr_meta,
            )
            return {"ok": True, "verdict": "corrected",
                    "verdict_id": r.get("verdict_id"),
                    "delta_id": r.get("delta_id"),
                    "pref_id": r.get("pref_id")}
        else:
            return {"ok": False,
                    "error": f"unknown verdict '{verdict}' — use good|bad"}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def handle_polish(payload):
    """Log a cross-LLM polish exchange. Both directions write a DPO pair.

    Direction `external_polishes_tb`: external (Claude/Perplexity) polished
    TB's draft. chosen=external_polished (richer), rejected=tb_raw.

    Direction `tb_polishes_external`: TB ground-corrected an external draft.
    chosen=tb_polished (brain-grounded), rejected=external_raw.
    """
    original = payload.get("original") or ""
    polished = payload.get("polished") or ""
    query = payload.get("query") or ""
    direction = payload.get("direction") or "external_polishes_tb"
    metadata = payload.get("metadata") or {}
    mode = _normalize_mode(payload.get("mode"))
    sovereignty = _normalize_sovereignty(payload.get("sovereignty"))

    if not original or not polished:
        return {"ok": False, "error": "need both 'original' and 'polished'"}
    if not _should_write_corpus(sovereignty):
        return {"ok": True, "skipped": "sovereign",
                "direction": direction, "mode": mode,
                "sovereignty": sovereignty}
    metadata = dict(metadata)
    metadata.setdefault("mode", mode)
    metadata.setdefault("sovereignty", sovereignty)

    try:
        from mcp_server_nucleus.runtime.align_ops import record_correction
        polish_meta = dict(metadata)
        polish_meta["surface"] = "tb_endpoint"
        polish_meta["source_kind"] = f"polish_{direction}"
        # tb_polishes_external and external_polishes_tb both write
        # chosen=polished, rejected=original — the direction tag in
        # source_kind preserves which side was the "correct" one for
        # downstream filtering.
        r = record_correction(
            context=original, correction=polished,
            expected=query, severity="low",
            extra_metadata=polish_meta,
        )
        return {
            "ok": True,
            "direction": direction,
            "verdict_id": r.get("verdict_id"),
            "delta_id": r.get("delta_id"),
            "pref_id": r.get("pref_id"),
            "metadata": metadata,
            "mode": mode,
            "sovereignty": sovereignty,
        }
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def handle_engrams(payload):
    query = payload.get("query") or ""
    limit = int(payload.get("limit") or 8)
    case_sensitive = bool(payload.get("case_sensitive", False))
    if not query:
        return {"ok": False, "error": "missing 'query'"}
    try:
        from mcp_server_nucleus.runtime.engram_ops import (
            _brain_search_engrams_impl,
        )
        raw = _brain_search_engrams_impl(query, case_sensitive=case_sensitive,
                                         limit=limit)
        data = json.loads(raw)
        if "ok" not in data:
            data["ok"] = bool(data.get("success"))
        return data
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


# Mode → engram-context mapping for /tb/remember.
# Engrams have a hardcoded context whitelist (Feature/Architecture/Brand/
# Strategy/Decision); we map our 3-mode taxonomy onto it. life→Decision
# captures personal-decision substrate; code→Feature captures repo work;
# work→Decision is the safe residual; legacy modes mapped per intent.
_MODE_TO_CONTEXT = {
    "code": "Feature",
    "life": "Decision",
    "work": "Decision",
    "business": "Strategy",
    "design": "Brand",
}


def handle_remember(payload):
    """Write a personal fact into the engram ledger.

    Phone-driver path: user types "/remember <fact>" or POSTs
    {fact, key?, intensity?, mode?, sovereignty?}. Auto-generates key from
    first 4 alphanumeric words if not given. Maps mode → engram context.
    """
    fact = (payload.get("fact") or payload.get("value") or "").strip()
    if not fact:
        return {"ok": False, "error": "missing 'fact'"}
    explicit_key = (payload.get("key") or "").strip()
    intensity = int(payload.get("intensity") or 5)
    mode = _normalize_mode(payload.get("mode"))
    sovereignty = _normalize_sovereignty(payload.get("sovereignty"))

    if not _should_write_corpus(sovereignty):
        return {"ok": True, "skipped": "sovereign",
                "mode": mode, "sovereignty": sovereignty}

    if explicit_key:
        key = explicit_key
    else:
        # Auto-key: first 4 alphanumeric words, joined by underscores.
        # Prefix with mode to avoid cross-mode key collisions.
        import re
        words = re.findall(r"[a-zA-Z0-9]+", fact.lower())[:4]
        if not words:
            words = ["fact"]
        key = f"{mode}_{'_'.join(words)}"
        # Truncate to engram_ops key length budget (~64 chars)
        key = key[:60]

    context = _MODE_TO_CONTEXT.get(mode, "Decision")

    try:
        from mcp_server_nucleus.runtime.engram_ops import (
            _brain_write_engram_impl,
        )
        # Tag mode + sovereignty into the value so retroactive filters can
        # split the corpus even though context taxonomy is fixed.
        tagged_value = f"[mode={mode}|sov={sovereignty}] {fact}"
        raw = _brain_write_engram_impl(
            key=key, value=tagged_value,
            context=context, intensity=intensity,
        )
        data = json.loads(raw)
        if "ok" not in data:
            data["ok"] = bool(data.get("success"))
        # Echo what got stored so caller can confirm
        data.setdefault("data", {})["stored_key"] = key
        data["data"]["stored_context"] = context
        data["data"]["mode"] = mode
        data["data"]["sovereignty"] = sovereignty
        return data
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def handle_undo(payload):
    """Remove the most recent preference_pair for this session.

    Used when the user typo'd a correction and wants to retract it before
    it pollutes the DPO corpus. Atomic rewrite: read all pairs, drop the
    last matching one, write back.
    """
    session_id = payload.get("session_id") or ""
    pair_id = payload.get("pref_id") or ""

    pairs_path = BRAIN_PATH / "training" / "preference_pairs.jsonl"
    if not pairs_path.exists():
        return {"ok": False, "error": "no preference_pairs.jsonl yet"}

    try:
        lines = pairs_path.read_text().splitlines()
    except Exception as e:
        return {"ok": False, "error": f"read failed: {e}"}

    # Find the LAST matching line. Match by pref_id if given, else by the
    # most recent pair regardless of session — sessions don't always make
    # it into the pair metadata, but pair_id is always known to caller
    # (returned in /tb/turn or /tb/align response).
    target_idx = None
    target_obj = None
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if pair_id and obj.get("pref_id") == pair_id:
            target_idx, target_obj = i, obj
            break
        if not pair_id and target_idx is None:
            target_idx, target_obj = i, obj
            break

    if target_idx is None:
        return {"ok": False,
                "error": "no matching pref pair found"}

    # Atomic rewrite: drop the line, write back via tmp-file rename
    new_lines = lines[:target_idx] + lines[target_idx + 1:]
    tmp = pairs_path.with_suffix(pairs_path.suffix + ".tmp")
    try:
        tmp.write_text("\n".join(new_lines) + ("\n" if new_lines else ""))
        tmp.replace(pairs_path)
    except Exception as e:
        return {"ok": False, "error": f"rewrite failed: {e}"}

    return {
        "ok": True,
        "removed_pref_id": target_obj.get("pref_id"),
        "removed_source": target_obj.get("source"),
        "removed_chosen_preview": (target_obj.get("chosen") or "")[:80],
    }


def handle_stats(payload=None):
    """Corpus accumulation snapshot. Counts pref_pairs, engrams, shadow_log.

    Parses :mode=X suffix from session_id field on shadow_log entries and
    from source field (`source=...:mode=X`) on pref_pairs to surface the
    by-mode breakdown — confirms compounding is real and tagged correctly.
    """
    import re
    from datetime import datetime, timezone, timedelta

    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    yesterday_start = today_start - timedelta(days=1)

    out = {
        "ok": True,
        "pref_pairs_total": 0,
        "pref_pairs_today": 0,
        "pref_pairs_24h": 0,
        "by_mode": {},
        "by_source": {},
        "engrams_total": 0,
        "shadow_log_total": 0,
        "shadow_log_today": 0,
        "sessions_active": len(_sessions),
    }

    pairs_path = BRAIN_PATH / "training" / "preference_pairs.jsonl"
    if pairs_path.exists():
        for line in pairs_path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            out["pref_pairs_total"] += 1

            ts_str = obj.get("timestamp") or obj.get("ts") or ""
            try:
                if ts_str.endswith("Z"):
                    ts_str = ts_str[:-1] + "+00:00"
                ts = datetime.fromisoformat(ts_str) if ts_str else None
            except Exception:
                ts = None
            if ts is not None:
                if ts >= today_start:
                    out["pref_pairs_today"] += 1
                if ts >= yesterday_start:
                    out["pref_pairs_24h"] += 1

            src = obj.get("source") or "unknown"
            base_src = src.split(":", 1)[0]
            out["by_source"][base_src] = out["by_source"].get(base_src, 0) + 1

            # Mode tag may be in source (`base:mode=X`) or in metadata
            mode_tag = None
            m = re.search(r"mode=([a-z]+)", src)
            if m:
                mode_tag = m.group(1)
            elif isinstance(obj.get("metadata"), dict):
                mode_tag = obj["metadata"].get("mode")
            mode_tag = mode_tag or "untagged"
            out["by_mode"][mode_tag] = out["by_mode"].get(mode_tag, 0) + 1

    engram_path = BRAIN_PATH / "engrams" / "ledger.jsonl"
    if engram_path.exists():
        out["engrams_total"] = sum(
            1 for line in engram_path.read_text().splitlines()
            if line.strip()
        )

    shadow_path = BRAIN_PATH / "training" / "shadow_log.jsonl"
    if shadow_path.exists():
        for line in shadow_path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            out["shadow_log_total"] += 1
            try:
                obj = json.loads(line)
                ts_str = obj.get("timestamp") or obj.get("ts") or ""
                if ts_str.endswith("Z"):
                    ts_str = ts_str[:-1] + "+00:00"
                ts = datetime.fromisoformat(ts_str) if ts_str else None
                if ts and ts >= today_start:
                    out["shadow_log_today"] += 1
            except Exception:
                pass

    return out


def handle_health():
    import urllib.request
    ollama_up = False
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags",
                                    timeout=3) as r:
            ollama_up = r.status == 200
    except Exception:
        ollama_up = False
    return {
        "ok": True,
        "model": DEFAULT_MODEL,
        "ollama": "up" if ollama_up else "down",
        "brain": str(BRAIN_PATH),
        "brain_exists": BRAIN_PATH.exists(),
        "sessions_active": len(_sessions),
    }


def handle_thread(payload):
    """Phase 2 §2.7: /thread slash command dispatch.

    Payload:
        chat_id: str (required) — surface namespace
        command: str (required) — e.g. "list" or "switch code" or
                 "" for bare /thread

    Returns dispatcher result + persists threads_data on mutation.
    """
    chat_id = (payload.get("chat_id") or "").strip()
    if not chat_id:
        return {"ok": False, "error": "missing 'chat_id'"}
    command = payload.get("command") or ""
    with _threads_lock:
        result = handle_thread_slash(
            _thread_store, _threads_data, chat_id, command,
        )
        active_id = _threads_data.get(chat_id, {}).get("active_thread_id")
    if result.mutated:
        _persist_threads()
    return {
        "ok": result.ok,
        "text": result.text,
        "mutated": result.mutated,
        "switched_to": result.switched_to,
        "active_thread_id": active_id,
    }


ROUTES = {
    ("POST", "/tb/turn"): handle_turn,
    ("POST", "/tb/align"): handle_align,
    ("POST", "/tb/polish"): handle_polish,
    ("POST", "/tb/engrams"): handle_engrams,
    ("POST", "/tb/remember"): handle_remember,
    ("POST", "/tb/undo"): handle_undo,
    ("POST", "/tb/thread"): handle_thread,
    ("GET", "/tb/stats"): lambda payload=None: handle_stats(payload),
    ("GET", "/tb/health"): lambda payload=None: handle_health(),
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write(
            f"[tb_endpoint] {self.address_string()} {fmt % args}\n"
        )

    def _route(self):
        return (self.command, self.path.split("?", 1)[0])

    def _read_payload(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        try:
            return json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return None

    def _respond(self, status, body):
        data = json.dumps(body, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        handler = ROUTES.get(self._route())
        if not handler:
            self._respond(404, {"ok": False, "error": "not found"})
            return
        self._respond(200, handler())

    def do_POST(self):
        handler = ROUTES.get(self._route())
        if not handler:
            self._respond(404, {"ok": False, "error": "not found"})
            return
        payload = self._read_payload()
        if payload is None:
            self._respond(400, {"ok": False, "error": "invalid JSON"})
            return
        try:
            result = handler(payload)
        except Exception as e:
            self._respond(500, {
                "ok": False,
                "error": f"{type(e).__name__}: {e}",
            })
            return
        status = 200 if result.get("ok") else 400
        self._respond(status, result)


def main():
    ap = argparse.ArgumentParser(
        description="TB Endpoint — universal HTTP service for all TB surfaces"
    )
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--no-warmup", action="store_true")
    args = ap.parse_args()

    if not args.no_warmup:
        try:
            tb._ollama_warmup(DEFAULT_MODEL)
        except Exception as e:
            print(f"[warmup skipped: {e}]")

    # Phase 1: restore persisted sessions on startup. Survives daemon
    # restart, kickstart, Mac reboot. See scripts/persist_sessions.py.
    try:
        n = _restore_sessions()
        if n:
            print(f"  sessions: restored {n} from {_session_store.path}")
    except Exception as e:
        print(f"[session restore skipped: {type(e).__name__}: {e}]")

    # Phase 2: restore persisted threads OR migrate Phase 1 sessions on
    # first run after Phase 2 deploy. See scripts/thread_storage.py.
    try:
        n = _restore_threads()
        if n:
            print(f"  threads: restored {n} chat-namespaces "
                  f"(or migrated from sessions) from {_thread_store.path}")
    except Exception as e:
        print(f"[thread restore skipped: {type(e).__name__}: {e}]")

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"TB Endpoint listening on http://{args.host}:{args.port}")
    print(f"  model={DEFAULT_MODEL} brain={BRAIN_PATH}")
    print(f"  routes: " + ", ".join(f"{m} {p}" for (m, p) in ROUTES))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")
        server.shutdown()


if __name__ == "__main__":
    main()
