#!/usr/bin/env python3
"""TB Telegram Bot — Telegram surface for the TB endpoint.

Polling-mode bot (no public IP / tunnel needed). Reads CHAT messages from
Telegram, forwards to the local TB endpoint as /tb/turn, replies with the
TB output + two inline buttons:

  👍  → POST /tb/align (verdict=good)
  👎 Correct → prompts for correction text, then POST /tb/align (verdict=bad)

Per-chat state (in-process): scope, rerank, mode, pending_correction flag,
last_session_id, last_verdict_chat (for align). Stays alive across messages
so /scope life persists.

Slash commands:
  /start, /help                show usage
  /scope auto|code|life|...    set RAG scope (default auto)
  /mode code|life|business|... set mode tag (default code)
  /rerank on|off               toggle cross-encoder rerank
  /engrams <query>             direct engram tool-call
  /reset                       clear conversation history for this chat
  /stats                       endpoint health + chat state

Env:
  TB_TELEGRAM_BOT_TOKEN   bot token from @BotFather (required)
  TB_ENDPOINT_URL         endpoint base (default http://127.0.0.1:7878)
  TB_ALLOWED_CHAT_IDS     comma-separated chat IDs to allow (default: any)

Run:
  TB_TELEGRAM_BOT_TOKEN=<token> python3 scripts/tb_telegram_bot.py
"""
import json
import os
import pathlib
import sys
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

TOKEN = os.environ.get("TB_TELEGRAM_BOT_TOKEN", "").strip()
ENDPOINT = os.environ.get("TB_ENDPOINT_URL", "http://127.0.0.1:7878").rstrip("/")
ALLOWED_CHAT_IDS = {s.strip() for s in
                    os.environ.get("TB_ALLOWED_CHAT_IDS", "").split(",")
                    if s.strip()}
TG_API = f"https://api.telegram.org/bot{TOKEN}"
LONG_POLL_TIMEOUT = 30
MAX_MESSAGE_LEN = 4000
DEFAULT_MODE = "auto"   # endpoint runs _auto_mode when bot omits mode field
DEFAULT_SCOPE = "auto"

# Persistence: chat state JSON survives bot restarts (launchd KeepAlive,
# crash, login). Without this, every restart loses /scope, /mode, and
# session_id continuity — bad for "phone-driver" trust.
STATE_PATH = pathlib.Path.home() / ".config/tb_bot/state.json"

chat_state: Dict[str, Dict[str, Any]] = {}


def _load_state() -> None:
    """Restore chat_state from disk on startup. Best-effort — corrupt or
    missing file → start fresh, never crash."""
    global chat_state
    try:
        if STATE_PATH.exists():
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                chat_state = json.load(f) or {}
            print(f"[state] restored {len(chat_state)} chats from {STATE_PATH}")
    except Exception as e:
        print(f"[state] restore failed ({type(e).__name__}: {e}); starting fresh")
        chat_state = {}


def _save_state() -> None:
    """Atomic write: tmp file + rename. Survives mid-write crash."""
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = STATE_PATH.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(chat_state, f, indent=2)
        tmp.replace(STATE_PATH)
    except Exception as e:
        print(f"[state] save failed: {type(e).__name__}: {e}")


def _http_post(url: str, payload: Dict[str, Any], timeout: int = 60) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8")
            return json.loads(body)
        except Exception:
            return {"ok": False, "error": f"http {e.code}"}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def _http_get(url: str, timeout: int = 60) -> Dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def tg_send(chat_id: str, text: str,
            reply_markup: Optional[Dict] = None,
            reply_to_message_id: Optional[int] = None) -> Dict[str, Any]:
    text = text or "(empty response)"
    if len(text) > MAX_MESSAGE_LEN:
        text = text[:MAX_MESSAGE_LEN - 30] + "\n…[truncated]"
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id
    return _http_post(f"{TG_API}/sendMessage", payload, timeout=15)


def tg_answer_callback(callback_query_id: str, text: str = "") -> None:
    _http_post(f"{TG_API}/answerCallbackQuery",
               {"callback_query_id": callback_query_id, "text": text},
               timeout=10)


def tg_get_updates(offset: int) -> list:
    url = (f"{TG_API}/getUpdates"
           f"?offset={offset}&timeout={LONG_POLL_TIMEOUT}")
    r = _http_get(url, timeout=LONG_POLL_TIMEOUT + 10)
    if r.get("ok"):
        return r.get("result", [])
    return []


def _state(chat_id: str) -> Dict[str, Any]:
    """Get-or-init chat state. Restored entries from disk are guaranteed
    to have all required keys via the setdefault chain below — older
    state.json files with missing fields stay backwards-compat."""
    s = chat_state.setdefault(chat_id, {})
    s.setdefault("scope", DEFAULT_SCOPE)
    s.setdefault("mode", DEFAULT_MODE)
    s.setdefault("rerank", False)
    s.setdefault("pending_correction", False)
    s.setdefault("session_id", f"tg:{chat_id}")
    s.setdefault("last_user_msg", "")
    s.setdefault("last_pref_id", None)
    s.setdefault("verbose", False)         # short replies by default
    s.setdefault("temperature", "med")     # low|med|high → 0.2|0.7|0.9
    s.setdefault("quality", "good")        # fast|good|verified|ultra — TB Quality Compound
    s.setdefault("raw", False)             # /raw on|off — strip ALL preambles (Phase 1 §1.8)
    s.setdefault("sovereignty", "public")  # public|guarded|sovereign
    s.setdefault("sov_breach_pending", False)  # /sov breach — one-shot, decays after next turn
    return s


# TB Quality Compound — /quality tier resolution. fast = TB-only, free,
# sovereign-safe; good = Sonnet composer for life-mode (default daily-driver);
# verified = good + Haiku grounding verifier post-pass for high-stakes turns;
# ultra = Opus 4.7 composer + Haiku verifier for hardest reasoning.
# All external-composer tiers route via Max plan (claude -p subprocess),
# no direct API billing. Sovereign queries override toggle: endpoint
# hard-gates principal=tb regardless of tier.
_QUALITY_PRINCIPAL = {"fast": "tb", "good": "auto", "verified": "auto",
                     "ultra": "opus"}
_QUALITY_VERIFIER  = {"fast": "off", "good": "off", "verified": "haiku",
                     "ultra": "haiku"}


def _quality_payload_fields(quality: str) -> Dict[str, Any]:
    """Resolve /quality state into endpoint payload kwargs."""
    q = (quality or "good").lower()
    if q not in _QUALITY_PRINCIPAL:
        q = "good"
    return {
        "quality_tier": q,
        "principal_model": _QUALITY_PRINCIPAL[q],
        "verifier": _QUALITY_VERIFIER[q],
    }


_TEMP_MAP = {"low": 0.2, "med": 0.7, "high": 0.9,
             "l": 0.2, "m": 0.7, "h": 0.9}
# Phase 1: verbose=on bumped 1200 → 4000 tokens. Charter commitment #2:
# token-budget — deep life-mode threads (relationship strategy, career
# decisions, big ideas) need room without truncation. Previous cap was
# demo-mode caution. /verbose off still defaults short (400) for quick
# recall queries.
_VERBOSE_NUM_PREDICT = {True: 4000, False: 400}


def _resolve_temperature(value) -> float:
    """Map word or number to Ollama temperature float."""
    if isinstance(value, (int, float)):
        return max(0.0, min(float(value), 2.0))
    s = (value or "med").lower().strip()
    if s in _TEMP_MAP:
        return _TEMP_MAP[s]
    try:
        return max(0.0, min(float(s), 2.0))
    except ValueError:
        return 0.7


def _align_buttons(session_id: str) -> Dict[str, Any]:
    """Three-button verdict row: approve, correct-with-text, reject-only.

    👎 Correct → bot waits for correction text → DPO pair (chosen=text).
    ❌ Bad → verdict-only via /tb/align verdict=reject. No DPO pair, so
    no need for follow-up correction text. Use when "this was bad and I
    don't have a better answer" — captures the negative signal cleanly
    without polluting the DPO archive with junk chosen text.
    """
    return {
        "inline_keyboard": [[
            {"text": "👍 Good",
             "callback_data": f"align:good:{session_id}"},
            {"text": "👎 Correct",
             "callback_data": f"align:bad:{session_id}"},
            {"text": "❌ Bad",
             "callback_data": f"align:reject:{session_id}"},
        ]]
    }


def cmd_help(chat_id: str) -> None:
    s = _state(chat_id)
    tg_send(chat_id, (
        "TB Telegram bot — local Third Brother on the phone.\n\n"
        "Just type to chat. Each turn pulls full RAG + brain context.\n"
        "Buttons under each reply:\n"
        "  👍 Good   = approve (verdict only)\n"
        "  👎 Correct = give correction text → DPO pair\n"
        "  ❌ Bad    = verdict-only reject (no DPO, no follow-up needed)\n"
        "Or type \"no, that's wrong, actually X\" inline → auto-DPO fires.\n\n"
        "Steering levers:\n"
        "  /scope auto|code|life|work       (now: " + s["scope"] + ")\n"
        "  /mode auto|code|life|work        (now: " + s["mode"] + ")\n"
        "    auto = endpoint derives mode from query (default)\n"
        "  /rerank on|off                   (now: "
        + ("on" if s["rerank"] else "off") + ") — slower, sharper recall\n"
        "  /verbose on|off                  (now: "
        + ("on" if s.get("verbose") else "off") + ") — long vs short replies\n"
        "  /temperature low|med|high        (now: "
        + str(s.get("temperature", "med"))
        + ") — deterministic vs creative\n\n"
        "Data surfaces:\n"
        "  /remember <fact>     save a personal fact (engram write)\n"
        "  /undo                remove the most recent DPO pair\n"
        "  /engrams <query>     search saved engrams\n"
        "  /stats               corpus + endpoint state\n"
        "  /reset               new session (clears history)\n"
        "  /help                this message\n\n"
        "Legacy modes business|design still accepted via explicit /mode."
    ))


def cmd_stats(chat_id: str) -> None:
    h = _http_get(f"{ENDPOINT}/tb/health", timeout=10)
    st = _http_get(f"{ENDPOINT}/tb/stats", timeout=15)
    s = _state(chat_id)

    by_mode = st.get("by_mode", {}) or {}
    by_mode_str = ", ".join(f"{k}={v}" for k, v in sorted(by_mode.items())) or "(none)"

    by_source = st.get("by_source", {}) or {}
    by_source_str = ", ".join(f"{k}={v}" for k, v in sorted(by_source.items())) or "(none)"

    tg_send(chat_id, (
        f"Endpoint: {ENDPOINT}\n"
        f"  ollama: {h.get('ollama')}\n"
        f"  model:  {h.get('model')}\n"
        f"  brain:  {h.get('brain_exists')}\n"
        f"  active sessions: {h.get('sessions_active')}\n\n"
        f"Corpus:\n"
        f"  pref_pairs: {st.get('pref_pairs_total','?')} total, "
        f"{st.get('pref_pairs_today','?')} today, "
        f"{st.get('pref_pairs_24h','?')} last 24h\n"
        f"  engrams:    {st.get('engrams_total','?')} total\n"
        f"  shadow_log: {st.get('shadow_log_total','?')} total, "
        f"{st.get('shadow_log_today','?')} today\n"
        f"  by mode:    {by_mode_str}\n"
        f"  by source:  {by_source_str}\n\n"
        f"Chat state:\n"
        f"  session_id: {s['session_id']}\n"
        f"  scope:  {s['scope']}\n"
        f"  mode:   {s['mode']}\n"
        f"  rerank: {'on' if s['rerank'] else 'off'}"
    ))


def cmd_remember(chat_id: str, fact: str) -> None:
    if not fact:
        tg_send(chat_id, "usage: /remember <fact>")
        return
    s = _state(chat_id)
    payload = {"fact": fact}
    if s["mode"] != "auto":
        payload["mode"] = s["mode"]
    r = _http_post(f"{ENDPOINT}/tb/remember", payload, timeout=15)
    if not (r.get("ok") or r.get("success")):
        tg_send(chat_id, f"remember failed: {r.get('error','?')}")
        return
    data = r.get("data", {}) or {}
    tg_send(chat_id, (
        f"✓ saved to engrams\n"
        f"  key:     {data.get('stored_key','?')}\n"
        f"  context: {data.get('stored_context','?')}\n"
        f"  mode:    {data.get('mode','?')}\n"
        f"  ADUN:    {(data.get('adun') or {}).get('mode','?')}"
    ))


def cmd_undo(chat_id: str) -> None:
    s = _state(chat_id)
    last_pref = s.get("last_pref_id")
    payload = {"session_id": s["session_id"]}
    if last_pref:
        payload["pref_id"] = last_pref
    r = _http_post(f"{ENDPOINT}/tb/undo", payload, timeout=15)
    if not r.get("ok"):
        tg_send(chat_id, f"undo failed: {r.get('error','?')}")
        return
    s["last_pref_id"] = None
    _save_state()
    tg_send(chat_id, (
        f"✓ removed pref pair\n"
        f"  pref_id: {r.get('removed_pref_id','?')}\n"
        f"  source:  {r.get('removed_source','?')}\n"
        f"  chosen:  {r.get('removed_chosen_preview','?')}"
    ))


def cmd_engrams(chat_id: str, query: str) -> None:
    if not query:
        tg_send(chat_id, "usage: /engrams <query>")
        return
    r = _http_post(f"{ENDPOINT}/tb/engrams",
                   {"query": query, "limit": 6}, timeout=15)
    if not (r.get("ok") or r.get("success")):
        tg_send(chat_id, f"engram tool-call failed: {r.get('error','?')}")
        return
    engrams = r.get("data", {}).get("engrams", [])
    if not engrams:
        tg_send(chat_id, f"no engrams for '{query}'")
        return
    lines = [f"[{len(engrams)} engram matches for '{query}']"]
    for e in engrams:
        ctx = e.get("context", "?")
        inten = e.get("intensity", "?")
        key = e.get("key", "?")
        val = (e.get("value", "") or "")[:200]
        lines.append(f"\n• [{ctx}/i{inten}] {key}\n  {val}")
    tg_send(chat_id, "\n".join(lines))


def handle_slash(chat_id: str, text: str) -> bool:
    parts = text.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""
    s = _state(chat_id)

    if cmd in ("/start", "/help"):
        cmd_help(chat_id)
        return True
    if cmd == "/stats":
        cmd_stats(chat_id)
        return True
    if cmd == "/thread":
        # Phase 2 §2.7 — delegate to endpoint /tb/thread which dispatches
        # via scripts/thread_slash. Bot stays thin.
        sid = s["session_id"]
        r = _http_post(f"{ENDPOINT}/tb/thread", {
            "chat_id": sid, "command": arg,
        }, timeout=30)
        if not r.get("ok") and r.get("error"):
            tg_send(chat_id, f"thread: {r.get('error')}")
        else:
            tg_send(chat_id, r.get("text") or "(no output)")
        return True
    if cmd == "/scope":
        a = arg.lower()
        if a in ("auto", "code", "life", "work", "business", "design"):
            s["scope"] = a
            _save_state()
            tg_send(chat_id, f"scope = {s['scope']}")
        else:
            tg_send(chat_id, "usage: /scope auto|code|life|work")
        return True
    if cmd == "/mode":
        a = arg.lower()
        # auto = bot omits mode field on /tb/turn payload → endpoint runs
        # _auto_mode (scope mirror → work residual). 3-mode primary + auto.
        # Legacy business/design accepted explicitly for backwards-compat.
        if a in ("auto", "code", "life", "work", "business", "design"):
            s["mode"] = a
            _save_state()
            tg_send(chat_id, f"mode = {s['mode']}")
        else:
            tg_send(chat_id, "usage: /mode auto|code|life|work")
        return True
    if cmd == "/rerank":
        a = arg.lower()
        if a in ("on", "off"):
            s["rerank"] = (a == "on")
            _save_state()
            tg_send(chat_id, f"rerank = {'on' if s['rerank'] else 'off'}")
        else:
            tg_send(chat_id, "usage: /rerank on|off")
        return True
    if cmd == "/verbose":
        a = arg.lower()
        if a in ("on", "off"):
            s["verbose"] = (a == "on")
            _save_state()
            np = _VERBOSE_NUM_PREDICT[s["verbose"]]
            tg_send(chat_id, f"verbose = {'on' if s['verbose'] else 'off'} (num_predict={np})")
        else:
            tg_send(chat_id, "usage: /verbose on|off")
        return True
    if cmd == "/raw":
        # Phase 1 §1.8: strip ALL preambles (antimix, constrained,
        # grounding-only) regardless of env defaults. The escape hatch.
        a = arg.lower()
        if a in ("on", "off"):
            s["raw"] = (a == "on")
            _save_state()
            tg_send(chat_id, (
                f"raw = {'on' if s['raw'] else 'off'}"
                f"{' — preambles stripped, no moralizing scaffolding' if s['raw'] else ''}"
            ))
        else:
            tg_send(chat_id, (
                "usage: /raw on|off\n"
                "  on = strip ALL preambles (antimix, constrained,\n"
                "       grounding-only) regardless of env defaults.\n"
                "       Voice anchor + no-moralize sysprompt still apply."
            ))
        return True
    if cmd == "/sov":
        # Phase 1 §1.9: sovereignty toggle + breach knob.
        # public/guarded/sovereign = persistent state.
        # breach = one-shot — next turn ALSO sends anthropic_breach=true,
        #   then auto-decays. Per-turn opt-in is safer than persistent breach.
        a = arg.lower()
        if a in ("public", "guarded", "sovereign"):
            s["sovereignty"] = a
            s["sov_breach_pending"] = False  # changing sov clears breach
            _save_state()
            tg_send(chat_id, f"sovereignty = {a}")
        elif a == "breach":
            # Sovereignty must be sovereign for breach to mean anything;
            # auto-set if user just types /sov breach
            if s["sovereignty"] != "sovereign":
                s["sovereignty"] = "sovereign"
            s["sov_breach_pending"] = True
            _save_state()
            tg_send(chat_id, (
                "⚠ NEXT TURN: sovereign+breach — content will be sent to "
                "Anthropic for composer-quality reasoning. Audit-logged. "
                "Auto-decays after this one turn fires."
            ))
        else:
            tg_send(chat_id, (
                "usage: /sov public|guarded|sovereign|breach\n"
                "  public/guarded = standard\n"
                "  sovereign = TB-only, never reaches Anthropic\n"
                "  breach = one-shot — next turn breaches sovereignty\n"
                "           (composer fires + audit-logged + decays)"
            ))
        return True
    if cmd in ("/temperature", "/temp"):
        a = arg.lower().strip()
        # Accept word (low|med|high) or numeric (0.0-2.0)
        if a in ("low", "med", "high", "l", "m", "h") or a.replace(".", "", 1).isdigit():
            s["temperature"] = a
            _save_state()
            actual = _resolve_temperature(a)
            tg_send(chat_id, f"temperature = {a} ({actual})")
        else:
            tg_send(chat_id, "usage: /temperature low|med|high  (or 0.0-2.0)")
        return True
    if cmd == "/quality":
        a = arg.lower().strip()
        if a in ("fast", "good", "verified", "ultra"):
            s["quality"] = a
            _save_state()
            fields = _quality_payload_fields(a)
            tg_send(chat_id, (
                f"quality = {a}\n"
                f"  principal_model: {fields['principal_model']}\n"
                f"  verifier: {fields['verifier']}"
            ))
        else:
            tg_send(chat_id, (
                "usage: /quality fast|good|verified|ultra\n"
                "  fast = TB-only, sovereign-safe, free\n"
                "  good = Sonnet for life-mode (default)\n"
                "  verified = good + Haiku grounding check\n"
                "  ultra = Opus 4.7 + Haiku verifier (hardest reasoning)"
            ))
        return True
    if cmd == "/engrams":
        cmd_engrams(chat_id, arg)
        return True
    if cmd == "/remember":
        cmd_remember(chat_id, arg)
        return True
    if cmd == "/undo":
        cmd_undo(chat_id)
        return True
    if cmd == "/reset":
        s["session_id"] = f"tg:{chat_id}:{int(time.time())}"
        s["pending_correction"] = False
        s["last_user_msg"] = ""
        s["last_pref_id"] = None
        _save_state()
        tg_send(chat_id, f"history cleared. session_id = {s['session_id']}")
        return True
    return False


def handle_text(chat_id: str, text: str, message_id: int) -> None:
    s = _state(chat_id)

    if s.get("pending_correction"):
        s["pending_correction"] = False
        align_payload = {
            "session_id": s["session_id"],
            "verdict": "bad",
            "correction": text,
        }
        if s["mode"] != "auto":
            align_payload["mode"] = s["mode"]
        r = _http_post(f"{ENDPOINT}/tb/align", align_payload, timeout=30)
        if r.get("ok"):
            s["last_pref_id"] = r.get("pref_id")
            _save_state()
            tg_send(chat_id, (
                f"✓ correction recorded\n"
                f"  pref_id: {r.get('pref_id')}\n"
                f"  delta_id: {r.get('delta_id')}\n"
                f"  /undo to retract"
            ), reply_to_message_id=message_id)
        else:
            tg_send(chat_id, f"align failed: {r.get('error','?')}",
                    reply_to_message_id=message_id)
        return

    s["last_user_msg"] = text
    _save_state()
    payload = {
        "input": text,
        "session_id": s["session_id"],
        "chat_id": s["session_id"],  # Phase 2: enables thread routing
        "scope": s["scope"],
        "rerank": s["rerank"],
        "temperature": _resolve_temperature(s.get("temperature", "med")),
        "num_predict": _VERBOSE_NUM_PREDICT[bool(s.get("verbose", False))],
    }
    # Only set mode in payload when user has pinned a value. mode="auto"
    # means omit, letting endpoint's _auto_mode derive from scope.
    if s["mode"] != "auto":
        payload["mode"] = s["mode"]
    # TB Quality Compound: /quality tier → principal_model + verifier.
    payload.update(_quality_payload_fields(s.get("quality", "good")))
    # /raw on → strip all preambles (Phase 1 §1.8)
    if s.get("raw"):
        payload["raw"] = True
    # Sovereignty + breach (Phase 1 §1.9). sovereignty default public.
    sov = s.get("sovereignty", "public")
    if sov != "public":
        payload["sovereignty"] = sov
    # /sov breach → one-shot anthropic_breach=true on next turn, auto-decay
    breach_was_pending = bool(s.get("sov_breach_pending"))
    if breach_was_pending:
        payload["anthropic_breach"] = True
        s["sov_breach_pending"] = False  # auto-decay
        _save_state()
    tg_send(chat_id, "thinking…")
    r = _http_post(f"{ENDPOINT}/tb/turn", payload, timeout=900)
    if not r.get("ok"):
        tg_send(chat_id, f"endpoint error: {r.get('error','?')}",
                reply_to_message_id=message_id)
        return
    output = r.get("output") or "(empty)"
    footer_bits = [
        f"mode={r.get('mode')}",
        f"sov={r.get('sovereignty')}",
        f"rag={r.get('rag_chunks')}",
        f"{r.get('duration_ms')}ms",
    ]
    # Surface principal + verifier so user can see when sovereign hard-gate
    # fired (principal=tb on a /quality good|verified turn = gate fired).
    pm = r.get("principal_model")
    if pm:
        footer_bits.append(f"principal={pm}")
    qt = r.get("quality_tier")
    if qt:
        footer_bits.append(f"q={qt}")
    vf = r.get("verifier_used")
    if vf and vf != "none":
        verdict = r.get("verifier_verdict") or "?"
        footer_bits.append(f"verifier={vf}/{verdict}")
    if r.get("sonnet_fell_back"):
        footer_bits.append("sonnet=fellback")
    if r.get("sovereign_gate_fired"):
        footer_bits.append("sov-gate=fired")
    if r.get("sovereign_breach_active"):
        bid = r.get("breach_id") or "?"
        footer_bits.append(f"⚠breach={bid}")
    # Phase 2 §2.8: thread surfacing
    tlabel = r.get("thread_label")
    if tlabel:
        action = r.get("thread_decision_action") or ""
        if action == "confirmed_new":
            footer_bits.append(f"thread=⊕{tlabel}")  # ⊕ = newly created
        elif action in ("routed_borderline", "explicit"):
            footer_bits.append(f"thread={tlabel}*")  # * = noteworthy resolve
        else:
            footer_bits.append(f"thread={tlabel}")
    footer = "\n\n— " + " ".join(footer_bits)
    auto_corr = r.get("auto_correction") or {}
    if auto_corr.get("pref_id"):
        footer += f"\n  auto-correction pair: {auto_corr.get('pref_id')}"
        s["last_pref_id"] = auto_corr.get("pref_id")
        _save_state()
    tg_send(chat_id, output + footer,
            reply_markup=_align_buttons(s["session_id"]),
            reply_to_message_id=message_id)


def handle_callback(cq: Dict[str, Any]) -> None:
    chat_id = str(cq["message"]["chat"]["id"])
    cq_id = cq["id"]
    data = cq.get("data", "") or ""
    parts = data.split(":", 2)
    if len(parts) < 3 or parts[0] != "align":
        tg_answer_callback(cq_id, "?")
        return
    _, verdict, sid = parts
    s = _state(chat_id)
    if verdict == "good":
        align_payload = {"session_id": sid, "verdict": "good"}
        if s["mode"] != "auto":
            align_payload["mode"] = s["mode"]
        r = _http_post(f"{ENDPOINT}/tb/align", align_payload, timeout=15)
        if r.get("ok"):
            tg_answer_callback(cq_id, "👍 noted")
            tg_send(chat_id, f"✓ approved verdict_id={r.get('verdict_id')}")
        else:
            tg_answer_callback(cq_id, "align failed")
    elif verdict == "bad":
        s["pending_correction"] = True
        _save_state()
        tg_answer_callback(cq_id, "👎 send the correction")
        tg_send(chat_id, "Send the correction text — your next message becomes the chosen output in a DPO pair against TB's reply above. /undo will retract afterward.")
    elif verdict == "reject":
        # Verdict-only path: no DPO pair, just a "this was bad" signal.
        # Closes the gap where 👎 with no follow-up text either lost
        # the signal (silent) or the next stray message got captured
        # as a correction by accident.
        align_payload = {"session_id": sid, "verdict": "reject"}
        if s["mode"] != "auto":
            align_payload["mode"] = s["mode"]
        r = _http_post(f"{ENDPOINT}/tb/align", align_payload, timeout=15)
        if r.get("ok"):
            tg_answer_callback(cq_id, "❌ rejection logged")
            tg_send(chat_id,
                    f"✗ rejected (verdict-only, no DPO pair)\n"
                    f"  verdict_id: {r.get('verdict_id','?')}")
        else:
            tg_answer_callback(cq_id, "reject failed")


def handle_message(msg: Dict[str, Any]) -> None:
    chat_id = str(msg["chat"]["id"])
    if ALLOWED_CHAT_IDS and chat_id not in ALLOWED_CHAT_IDS:
        tg_send(chat_id, "Not authorized.")
        return
    text = (msg.get("text") or "").strip()
    message_id = msg.get("message_id")
    # Graceful non-text: voice notes, photos, documents, stickers, etc.
    # Bot doesn't transcribe today (whisper is its own scope). Acknowledge
    # so the user knows the input wasn't lost; suggest the available path.
    if not text:
        kind = next((k for k in
                     ("voice", "audio", "photo", "video", "document",
                      "sticker", "video_note", "location", "poll")
                     if k in msg), "non-text")
        if kind == "voice":
            tg_send(chat_id,
                    "voice note received but transcription isn't wired yet. "
                    "Use the iOS keyboard mic button to dictate inline — "
                    "Apple Dictation transcribes locally and sends as text.",
                    reply_to_message_id=message_id)
        else:
            tg_send(chat_id,
                    f"input type '{kind}' not supported yet — send text.",
                    reply_to_message_id=message_id)
        return
    if text.startswith("/"):
        if handle_slash(chat_id, text):
            return
    handle_text(chat_id, text, message_id)


def main():
    if not TOKEN:
        print("ERROR: set TB_TELEGRAM_BOT_TOKEN env var (from @BotFather)")
        sys.exit(1)
    _load_state()
    me = _http_get(f"{TG_API}/getMe", timeout=10)
    if not me.get("ok"):
        print(f"ERROR: telegram getMe failed: {me}")
        sys.exit(2)
    bot = me.get("result", {})
    print(f"TB Telegram bot — @{bot.get('username')} (id={bot.get('id')})")
    print(f"  endpoint: {ENDPOINT}")
    print(f"  allowed_chat_ids: {ALLOWED_CHAT_IDS or '(any)'}")
    print(f"  state file: {STATE_PATH}")
    health = _http_get(f"{ENDPOINT}/tb/health", timeout=5)
    print(f"  endpoint health: {health}")

    offset = 0
    while True:
        try:
            updates = tg_get_updates(offset)
        except KeyboardInterrupt:
            print("\nshutting down")
            break
        except Exception as e:
            print(f"poll error: {type(e).__name__}: {e}")
            time.sleep(3)
            continue
        for u in updates:
            offset = u["update_id"] + 1
            try:
                if "message" in u:
                    handle_message(u["message"])
                elif "callback_query" in u:
                    handle_callback(u["callback_query"])
            except Exception as e:
                print(f"handler error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
