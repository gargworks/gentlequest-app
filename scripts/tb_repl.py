#!/usr/bin/env python3
"""TB REPL — terminal dogfood surface for the HTTP endpoint.

Unlike scripts/tb_chat.py (direct in-process Ollama call), this REPL hits
the same /tb/turn HTTP contract the Telegram bot uses. That means every
quality lever (TB-grounds-Sonnet-composes, Haiku verifier, sovereign hard-
gate, anti-citation stops, mode anti-mixing preamble) is available from
the terminal too. Use this when you want to test the compound flow before
firing on phone.

Slash commands (parity with @tb_lokesh_bot):
  /quality fast|good|verified|ultra  set quality tier (default: good)
                                ultra = Opus 4.7 composer + Haiku verifier
  /scope auto|code|life|work    set RAG scope (default: auto)
  /mode auto|code|life|work     pin mode tag (default: auto)
  /sov public|guarded|sovereign set sovereignty (default: public)
  /rerank on|off                toggle cross-encoder rerank
  /verbose on|off               toggle long outputs (1200 vs 400 num_predict)
  /reset                        clear conversation history (new session_id)
  /show                         show current state
  /exit, /quit                  leave

Run:
    python3 scripts/tb_repl.py
    TB_ENDPOINT_URL=http://127.0.0.1:7878 python3 scripts/tb_repl.py
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

ENDPOINT = os.environ.get("TB_ENDPOINT_URL", "http://127.0.0.1:7878").rstrip("/")
TIMEOUT = int(os.environ.get("TB_REPL_TIMEOUT", "900"))


def post_turn(payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{ENDPOINT}/tb/turn",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            resp = json.loads(r.read().decode("utf-8"))
            resp["_wall_ms"] = int((time.time() - t0) * 1000)
            return resp
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"HTTP {e.code}: {e.reason}",
                "_wall_ms": int((time.time() - t0) * 1000)}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}",
                "_wall_ms": int((time.time() - t0) * 1000)}


def get_health() -> dict:
    try:
        with urllib.request.urlopen(f"{ENDPOINT}/tb/health", timeout=5) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


_QUALITY_PRINCIPAL = {"fast": "tb", "good": "auto", "verified": "auto",
                      "ultra": "opus"}
_QUALITY_VERIFIER = {"fast": "off", "good": "off", "verified": "haiku",
                     "ultra": "haiku"}


def quality_payload_fields(quality: str) -> dict:
    q = (quality or "good").lower()
    if q not in _QUALITY_PRINCIPAL:
        q = "good"
    return {
        "quality_tier": q,
        "principal_model": _QUALITY_PRINCIPAL[q],
        "verifier": _QUALITY_VERIFIER[q],
    }


def fmt_footer(resp: dict) -> str:
    bits = [
        f"mode={resp.get('mode')}",
        f"sov={resp.get('sovereignty')}",
        f"rag={resp.get('rag_chunks')}",
        f"{resp.get('duration_ms')}ms",
    ]
    pm = resp.get("principal_model")
    if pm:
        bits.append(f"principal={pm}")
    qt = resp.get("quality_tier")
    if qt:
        bits.append(f"q={qt}")
    vf = resp.get("verifier_used")
    if vf and vf != "none":
        verdict = resp.get("verifier_verdict") or "?"
        bits.append(f"verifier={vf}/{verdict}")
    if resp.get("sonnet_fell_back"):
        bits.append("sonnet=fellback")
    if resp.get("sovereign_gate_fired"):
        bits.append("sov-gate=fired")
    if resp.get("sovereign_breach_active"):
        bid = resp.get("breach_id") or "?"
        bits.append(f"⚠breach={bid}")
    # Phase 2 §2.8: thread surfacing
    tlabel = resp.get("thread_label")
    if tlabel:
        action = resp.get("thread_decision_action") or ""
        if action == "confirmed_new":
            bits.append(f"thread=⊕{tlabel}")
        elif action in ("routed_borderline", "explicit"):
            bits.append(f"thread={tlabel}*")
        else:
            bits.append(f"thread={tlabel}")
    return "— " + " ".join(bits)


def print_state(state: dict) -> None:
    print(f"  endpoint: {ENDPOINT}")
    print(f"  session:  {state['session_id']}")
    print(f"  scope:    {state['scope']}")
    print(f"  mode:     {state['mode']}")
    print(f"  sov:      {state['sovereignty']}")
    q = state['quality']
    print(f"  quality:  {q}  → "
          f"principal={_QUALITY_PRINCIPAL.get(q, '?')}, "
          f"verifier={_QUALITY_VERIFIER.get(q, '?')}")
    print(f"  rerank:   {'on' if state['rerank'] else 'off'}")
    print(f"  verbose:  {'on' if state['verbose'] else 'off'}")


def main() -> int:
    health = get_health()
    if not health.get("ok"):
        print(f"[tb_repl] /tb/health failed: {health.get('error')}", file=sys.stderr)
        print(f"[tb_repl] is the endpoint running? "
              f"check launchctl list | grep tb_endpoint")
        return 2

    state = {
        "session_id": f"repl-{int(time.time())}",
        "scope": "auto",
        "mode": "auto",
        "sovereignty": "public",
        "sov_breach_pending": False,  # Phase 1 §1.9
        "quality": "good",
        "raw": False,
        "rerank": False,
        "verbose": False,
    }

    print(f"TB REPL — endpoint={ENDPOINT}  model={health.get('model')}")
    print("Slash: /quality, /scope, /mode, /sov, /rerank, /verbose, /reset, /show, /exit")
    print()

    while True:
        try:
            line = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue

        if line.startswith("/"):
            parts = line.split(maxsplit=1)
            cmd = parts[0]
            arg = (parts[1] if len(parts) > 1 else "").lower().strip()

            if cmd in ("/exit", "/quit"):
                break
            elif cmd == "/quality":
                if arg in ("fast", "good", "verified", "ultra"):
                    state["quality"] = arg
                    f = quality_payload_fields(arg)
                    print(f"[quality={arg}  principal={f['principal_model']}  "
                          f"verifier={f['verifier']}]")
                else:
                    print("usage: /quality fast|good|verified|ultra")
            elif cmd == "/scope":
                if arg in ("auto", "code", "life", "work", "business", "design"):
                    state["scope"] = arg
                    print(f"[scope={arg}]")
                else:
                    print("usage: /scope auto|code|life|work")
            elif cmd == "/mode":
                if arg in ("auto", "code", "life", "work", "business", "design"):
                    state["mode"] = arg
                    print(f"[mode={arg}]")
                else:
                    print("usage: /mode auto|code|life|work")
            elif cmd == "/sov":
                # Phase 1 §1.9: sovereignty + breach knob
                if arg in ("public", "guarded", "sovereign"):
                    state["sovereignty"] = arg
                    state["sov_breach_pending"] = False
                    print(f"[sov={arg}]")
                elif arg == "breach":
                    if state["sovereignty"] != "sovereign":
                        state["sovereignty"] = "sovereign"
                    state["sov_breach_pending"] = True
                    print("[⚠ NEXT TURN: sovereign+breach — sent to Anthropic, audit-logged, decays after this turn]")
                else:
                    print("usage: /sov public|guarded|sovereign|breach")
            elif cmd == "/rerank":
                if arg in ("on", "off"):
                    state["rerank"] = (arg == "on")
                    print(f"[rerank={arg}]")
                else:
                    print("usage: /rerank on|off")
            elif cmd == "/verbose":
                if arg in ("on", "off"):
                    state["verbose"] = (arg == "on")
                    print(f"[verbose={arg}]")
                else:
                    print("usage: /verbose on|off")
            elif cmd == "/raw":
                if arg in ("on", "off"):
                    state["raw"] = (arg == "on")
                    print(f"[raw={arg}]"
                          + (" — preambles stripped" if state["raw"] else ""))
                else:
                    print("usage: /raw on|off  (strip ALL preambles)")
            elif cmd == "/reset":
                state["session_id"] = f"repl-{int(time.time())}"
                print(f"[history cleared. session_id={state['session_id']}]")
            elif cmd == "/show":
                print_state(state)
            elif cmd == "/thread":
                # Phase 2 §2.7 — delegate to endpoint /tb/thread
                req = urllib.request.Request(
                    f"{ENDPOINT}/tb/thread",
                    data=json.dumps({
                        "chat_id": state["session_id"],
                        "command": arg,
                    }).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                try:
                    with urllib.request.urlopen(req, timeout=30) as r:
                        resp = json.loads(r.read().decode("utf-8"))
                    print(resp.get("text") or "(no output)")
                except Exception as e:
                    print(f"[thread error: {type(e).__name__}: {e}]")
            else:
                print(f"unknown: {cmd}")
            continue

        payload = {
            "input": line,
            "session_id": state["session_id"],
            "chat_id": state["session_id"],  # Phase 2: thread routing
            "scope": state["scope"],
            "sovereignty": state["sovereignty"],
            "rerank": state["rerank"],
            "num_predict": 1200 if state["verbose"] else 400,
        }
        if state["mode"] != "auto":
            payload["mode"] = state["mode"]
        payload.update(quality_payload_fields(state["quality"]))
        if state.get("raw"):
            payload["raw"] = True
        # Phase 1 §1.9: one-shot breach pass-through + auto-decay
        if state.get("sov_breach_pending"):
            payload["anthropic_breach"] = True
            state["sov_breach_pending"] = False

        print("(thinking…)")
        resp = post_turn(payload)
        if not resp.get("ok"):
            print(f"[error] {resp.get('error')}")
            continue

        print()
        print(resp.get("output") or "(empty)")
        print()
        print(fmt_footer(resp))
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
