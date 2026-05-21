#!/usr/bin/env python3
"""TB Chat — interactive shell for Third Brother with full RAG scaffolding.

Each turn pulls hybrid-RAG context (working state + live session + retrieved
chunks + commitments) before hitting v14. Slash-commands let you steer scope,
do direct engram tool-calls, and write back ALIGN verdicts on every turn.

Closes four gaps in the existing scaffolding:
  - Scope toggle (was hardcoded "code" in the driver)
  - LLM cross-encoder rerank pass on top of RRF
  - Direct nucleus_engrams tool-call loop (not just RAG context-injection)
  - ALIGN write-back as a single keystroke per turn (not session-level opt-in)

Usage:
    python3 scripts/tb_chat.py
    python3 scripts/tb_chat.py --scope life
    python3 scripts/tb_chat.py --rerank on

Slash commands:
    /scope code|life|auto    Toggle RAG scope (default: auto)
    /rerank on|off           Toggle cross-encoder rerank pass
    /engrams <query>         Direct engram tool-call, inject results
    /align good|bad [note]   Write ALIGN verdict on last turn
    /show-context            Print last RAG context
    /reset                   Clear in-process turn history
    /exit, /quit             Leave
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "mcp-server-nucleus" / "src"))

from providers.brain_rag import build_full_context, format_rag_context, BUDGET_COLD
from providers.reranker import rerank as cross_rerank
import third_brother_driver as tb

BRAIN_PATH = Path(os.environ.get("NUCLEUS_BRAIN_PATH", str(ROOT / ".brain")))
DEFAULT_MODEL = os.environ.get("TB_MODEL", "third-brother:latest")
HISTORY_TURNS = 4
DEFAULT_NUM_PREDICT = int(os.environ.get("TB_CHAT_NUM_PREDICT", "1024"))
DEFAULT_TIMEOUT = int(os.environ.get("TB_CHAT_TIMEOUT", "600"))


class ChatSession:
    def __init__(self, scope="auto", rerank=False, model=DEFAULT_MODEL):
        self.scope = scope
        self.rerank = rerank
        self.model = model
        self.turns = []
        self.last_context = ""
        self.last_results = []

    def _resolved_scope(self):
        return None if self.scope == "auto" else self.scope

    def _format_history(self):
        if not self.turns:
            return ""
        recent = self.turns[-HISTORY_TURNS:]
        out = ["[CONVERSATION HISTORY]"]
        for u, a in recent:
            out.append(f"User: {u}")
            out.append(f"TB: {a}")
        return "\n".join(out)

    def _engram_inject(self, query: str) -> str:
        try:
            from mcp_server_nucleus.runtime.engram_ops import _brain_search_engrams_impl
            os.environ.setdefault("NUCLEAR_BRAIN_PATH", str(BRAIN_PATH))
            raw = _brain_search_engrams_impl(query, case_sensitive=False, limit=8)
            data = json.loads(raw)
            if not (data.get("ok") or data.get("success")):
                return f"[engram tool-call returned not-ok: {data.get('error','?')}]"
            engrams = data.get("data", {}).get("engrams", [])
            if not engrams:
                return "[no engrams matched]"
            lines = [f"[ENGRAM TOOL-CALL — {len(engrams)} matches for '{query}']"]
            for e in engrams:
                ctx = e.get("context", "?")
                inten = e.get("intensity", "?")
                key = e.get("key", "?")
                val = e.get("value", "")[:200]
                lines.append(f"- [{ctx}/i{inten}] {key}: {val}")
            return "\n".join(lines)
        except Exception as e:
            return f"[engram tool-call failed: {type(e).__name__}: {e}]"

    def turn(self, user_msg: str) -> str:
        try:
            context, results = build_full_context(
                user_msg, brain_path=BRAIN_PATH, scope=self._resolved_scope()
            )
        except Exception as e:
            print(f"[CHAT] build_full_context failed: {e} — proceeding without RAG")
            context, results = "", []

        if self.rerank and results:
            print(f"[CHAT] Reranking {len(results)} candidates via LLM cross-encoder...")
            results = cross_rerank(user_msg, results, top_n=8, model=self.model)
            cold = format_rag_context(results, max_words=BUDGET_COLD)
            if cold:
                context = context + "\n\n[RERANKED COLD KNOWLEDGE]\n" + cold

        history = self._format_history()
        prompt_parts = [p for p in [context, history, f"User: {user_msg}", "TB:"] if p]
        prompt = "\n\n".join(prompt_parts)

        self.last_context = context
        self.last_results = results

        text, ms = tb._ollama_generate(prompt, self.model,
                                       timeout=DEFAULT_TIMEOUT,
                                       num_predict=DEFAULT_NUM_PREDICT)
        if text is None:
            return "[TB call failed — see [OLLAMA] line above]"

        try:
            tb.log_ollama_call("CHAT", self.model, prompt, text,
                               exit_code=0, duration_ms=ms, task_id="tb_chat_repl")
        except Exception:
            pass

        self.turns.append((user_msg, text))
        return text

    def align(self, verdict: str, note: str = "") -> str:
        if not self.turns:
            return "[no turn to align]"
        last_user, last_tb = self.turns[-1]
        try:
            from mcp_server_nucleus.runtime.align_ops import record_correction, record_approval
            os.environ.setdefault("NUCLEAR_BRAIN_PATH", str(BRAIN_PATH))
            if verdict in ("good", "approve", "ok"):
                r = record_approval(context=last_tb, notes=note or last_user)
                return f"[ALIGN] approved verdict_id={r.get('verdict_id','?')}"
            elif verdict in ("bad", "correct", "reject"):
                r = record_correction(
                    context=last_tb,
                    correction=note or "(no correction provided)",
                    expected=last_user,
                    severity="medium",
                )
                return (f"[ALIGN] corrected verdict_id={r.get('verdict_id','?')} "
                        f"delta={r.get('delta_id','?')} pref={r.get('pref_id','?')}")
            else:
                return f"[ALIGN] unknown verdict '{verdict}' — use good|bad"
        except Exception as e:
            return f"[ALIGN] failed: {type(e).__name__}: {e}"


def main():
    ap = argparse.ArgumentParser(description="TB Chat — interactive REPL with full scaffolding")
    ap.add_argument("--scope", choices=["code", "life", "auto"], default="auto")
    ap.add_argument("--rerank", choices=["on", "off"], default="off")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    args = ap.parse_args()

    sess = ChatSession(scope=args.scope, rerank=(args.rerank == "on"), model=args.model)

    print(f"TB Chat — model={sess.model} scope={sess.scope} rerank={'on' if sess.rerank else 'off'}")
    print(f"Brain: {BRAIN_PATH}")
    print("Slash: /scope, /rerank, /engrams, /align, /show-context, /reset, /exit")
    print()

    try:
        tb._ollama_warmup(sess.model)
    except Exception as e:
        print(f"[warmup skipped: {e}]")

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
            arg = parts[1] if len(parts) > 1 else ""

            if cmd in ("/exit", "/quit"):
                break
            elif cmd == "/scope":
                if arg in ("code", "life", "auto"):
                    sess.scope = arg
                    print(f"[scope={arg}]")
                else:
                    print("usage: /scope code|life|auto")
            elif cmd == "/rerank":
                if arg in ("on", "off"):
                    sess.rerank = (arg == "on")
                    print(f"[rerank={arg}]")
                else:
                    print("usage: /rerank on|off")
            elif cmd == "/engrams":
                if not arg:
                    print("usage: /engrams <query>")
                else:
                    print(sess._engram_inject(arg))
            elif cmd == "/align":
                aparts = arg.split(maxsplit=1) if arg else []
                v = aparts[0] if aparts else ""
                note = aparts[1] if len(aparts) > 1 else ""
                print(sess.align(v, note))
            elif cmd == "/show-context":
                print("--- LAST CONTEXT ---")
                print(sess.last_context[:4000] or "(empty)")
                print("--- END ---")
            elif cmd == "/reset":
                sess.turns = []
                print("[history cleared]")
            else:
                print(f"unknown: {cmd}")
            continue

        try:
            response = sess.turn(line)
        except Exception as e:
            print(f"[error] {type(e).__name__}: {e}")
            continue

        print()
        print(response)
        print()


if __name__ == "__main__":
    main()
