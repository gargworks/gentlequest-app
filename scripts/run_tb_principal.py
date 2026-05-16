#!/usr/bin/env python3
"""TB-as-Principal headless wrapper.

TB v14 (local Ollama) reads a plan + brain context, decides what to
delegate, and emits structured markers. This wrapper parses those markers,
fires `claude -p` worker subprocesses (Sonnet or Haiku) for delegated
work, feeds results back to TB, and loops until TB emits DONE/BLOCKED or
caps trigger.

Charter: docs/org/charters/tb_principal.md (read first if you're poking
at the protocol or thinking of touching the marker format).

Cost shape: principal turns FREE (local Ollama). Workers paid via
`claude -p --model {sonnet|haiku}`. Realistic 10-delegation cycle <$1.

Run:
    python3 scripts/run_tb_principal.py \\
        --plan .brain/plans/agent_organization_expansion_2026Q2.md \\
        --max-delegations 10 \\
        --dry-run            # parse markers, print briefs, no worker fires

Stop:
    touch .brain/driver/tb_principal.stop

Output:
    Last synthesis / DONE block written to .brain/driver/tb_principal_<ts>.md
    Telemetry events emitted to .brain/ledger/events.jsonl via spawn_and_emit
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import uuid
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "mcp-server-nucleus" / "src"))

TB_ENDPOINT = os.environ.get("TB_ENDPOINT_URL",
                             "http://127.0.0.1:7878").rstrip("/")
TB_MODEL = os.environ.get("TB_MODEL", "third-brother:latest")
BRAIN = Path(os.environ.get("NUCLEUS_BRAIN_PATH", str(ROOT / ".brain")))
STOP_FILE = BRAIN / "driver" / "tb_principal.stop"
RESULT_DIR = BRAIN / "driver"

DELEGATE_PATTERN = re.compile(
    r"DELEGATE:\s*(sonnet|haiku)\s*::\s*(.+?)\n(.*?)\nEND_DELEGATE",
    re.IGNORECASE | re.DOTALL,
)
SYNTHESIZE_PATTERN = re.compile(
    r"SYNTHESIZE:\s*\n(.*?)\nEND_SYNTHESIZE",
    re.IGNORECASE | re.DOTALL,
)
DONE_PATTERN = re.compile(
    r"DONE:\s*\n(.*?)\nEND_DONE",
    re.IGNORECASE | re.DOTALL,
)
BLOCKED_PATTERN = re.compile(
    r"BLOCKED:\s*\n(.*?)\nEND_BLOCKED",
    re.IGNORECASE | re.DOTALL,
)


def _emit_event(event_type: str, payload: dict) -> None:
    """Append a telemetry event to .brain/ledger/events.jsonl. Best-effort."""
    try:
        path = BRAIN / "ledger" / "events.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            "source": "tb_principal",
            **payload,
        }
        with open(path, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    except Exception:
        pass


def fetch_tb_advice(query: str, session_id: str,
                    sovereignty: str = "guarded",
                    timeout: int = 240) -> str:
    """Get TB's RAG-grounded read on a query for context-injection.

    Best-effort. Failure returns empty string — Sonnet principal then
    proceeds without TB context. Sonnet decides what to do with TB's
    answer; the caveat banner makes the alpha/beta status explicit.

    Used in advisory mode (principal=sonnet). The principal sees both
    the original query AND TB's read prepended as a prefix block.
    """
    payload = {
        "input": query,
        "session_id": f"{session_id}-advice",
        "scope": "auto",
        "mode": "work",
        "sovereignty": sovereignty,
        "rerank": False,
        "num_predict": 800,    # short read, not long-form
        "temperature": 0.5,
    }
    try:
        req = urllib.request.Request(
            f"{TB_ENDPOINT}/tb/turn",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode())
            if not resp.get("ok"):
                return ""
            text = (resp.get("output") or "").strip()
            if "</think>" in text:
                text = text.split("</think>", 1)[1].strip()
            return text
    except Exception:
        return ""


# wrap_tb_advice moved to providers.composers.sonnet_principal — import
# from there if needed. Kept here as a re-export for backwards-compat
# with any external caller that referenced run_tb_principal.wrap_tb_advice.
from providers.composers.sonnet_principal import wrap_tb_advice  # noqa: E402,F401


def call_tb(prompt: str, session_id: str, sovereignty: str = "guarded",
            mode: str = "work", num_predict: int = 2048,
            temperature: float = 0.5, timeout: int = 600) -> tuple:
    """Call TB via /tb/turn endpoint. Returns (text, duration_ms, full_response_dict).

    Endpoint inherits RAG + sovereignty gate + mode tagging + shadow log +
    auto-correction-detector — all the substrate work from PRs
    #219/#221/#223/#224/#225/#226. Principal-specific session_id keeps
    this run isolated from the bot's chat sessions.
    """
    payload = {
        "input": prompt,
        "session_id": session_id,
        "scope": "auto",
        "mode": mode,
        "sovereignty": sovereignty,
        "rerank": False,
        "num_predict": num_predict,
        "temperature": temperature,
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{TB_ENDPOINT}/tb/turn", data=data,
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode())
            duration_ms = int((time.time() - t0) * 1000)
            if not resp.get("ok"):
                err = resp.get("error", "unknown")
                return (f"[TB_ENDPOINT_ERROR] {err}", duration_ms, resp)
            text = (resp.get("output") or "").strip()
            # Endpoint already strips <think>, but defensive double-check
            if "</think>" in text:
                text = text.split("</think>", 1)[1].strip()
            elif text.startswith("<think>"):
                text = text[len("<think>"):].strip()
            return text, duration_ms, resp
    except Exception as e:
        duration_ms = int((time.time() - t0) * 1000)
        return (f"[TB_ENDPOINT_ERROR] {type(e).__name__}: {e}",
                duration_ms, {})


def endpoint_health() -> bool:
    try:
        with urllib.request.urlopen(f"{TB_ENDPOINT}/tb/health",
                                    timeout=5) as r:
            return json.loads(r.read().decode()).get("ok", False)
    except Exception:
        return False


def call_sonnet_principal(prompt: str, query_summary: str,
                          tb_advice: str = "",
                          timeout: int = 600) -> tuple:
    """Call Sonnet principal via `claude -p --model sonnet` subprocess.

    Thin shim over providers.composers.sonnet_principal.compose_with_sonnet —
    same subprocess + fallback pattern, now shared with tb_endpoint.py so
    both the wrapper and the endpoint take the same code path. Behavior
    unchanged from the pre-refactor inline implementation.

    Returns (text, duration_ms, response_dict_or_empty).
    """
    from providers.composers.sonnet_principal import compose_with_sonnet
    return compose_with_sonnet(
        prompt=prompt, query_summary=query_summary,
        tb_advice=tb_advice, timeout=timeout, model="sonnet",
    )


def fire_worker(model: str, label: str, brief: str,
                dry_run: bool = False, timeout: int = 600) -> dict:
    """Fire a `claude -p --model {model}` worker subprocess. Returns dict
    with keys: ok, output, duration_ms, model, label, error."""
    spawn_id = f"spawn-{int(time.time())}-{uuid.uuid4().hex[:6]}"
    _emit_event("agent_spawn", {
        "spawn_id": spawn_id, "model": model, "label": label,
        "brief_chars": len(brief), "dry_run": dry_run,
    })
    if dry_run:
        print(f"\n[DRY-RUN] would fire {model} :: {label}")
        print(f"[DRY-RUN] brief ({len(brief)} chars):")
        print("  " + brief.replace("\n", "\n  ")[:800])
        _emit_event("agent_return", {
            "spawn_id": spawn_id, "ok": True, "dry_run": True,
            "response_chars": 0,
        })
        return {"ok": True, "output": "[DRY-RUN, not executed]",
                "duration_ms": 0, "model": model, "label": label,
                "spawn_id": spawn_id}

    t0 = time.time()
    try:
        proc = subprocess.run(
            ["claude", "-p", "--model", model],
            input=brief, capture_output=True, text=True,
            timeout=timeout,
        )
        duration_ms = int((time.time() - t0) * 1000)
        output = (proc.stdout or "").strip()
        if proc.returncode != 0:
            err = (proc.stderr or "").strip()[:500]
            _emit_event("agent_return", {
                "spawn_id": spawn_id, "ok": False, "model": model,
                "duration_ms": duration_ms, "error": err,
            })
            return {"ok": False, "output": output, "error": err,
                    "duration_ms": duration_ms, "model": model,
                    "label": label, "spawn_id": spawn_id}
        _emit_event("agent_return", {
            "spawn_id": spawn_id, "ok": True, "model": model,
            "duration_ms": duration_ms, "response_chars": len(output),
        })
        return {"ok": True, "output": output,
                "duration_ms": duration_ms, "model": model,
                "label": label, "spawn_id": spawn_id}
    except subprocess.TimeoutExpired:
        _emit_event("agent_return", {
            "spawn_id": spawn_id, "ok": False, "model": model,
            "error": "timeout", "duration_ms": timeout * 1000,
        })
        return {"ok": False, "output": "", "error": "timeout",
                "duration_ms": timeout * 1000, "model": model,
                "label": label, "spawn_id": spawn_id}


def parse_markers(text: str) -> dict:
    """Parse TB output for the four markers. Returns dict with the first
    matching marker; if multiple delegates, returns all in `delegates`
    list. None if no marker found."""
    delegates = [
        {"model": m.group(1).lower(), "label": m.group(2).strip(),
         "brief": m.group(3).strip()}
        for m in DELEGATE_PATTERN.finditer(text)
    ]
    if delegates:
        return {"kind": "delegate", "delegates": delegates}

    syn = SYNTHESIZE_PATTERN.search(text)
    if syn:
        return {"kind": "synthesize", "content": syn.group(1).strip()}

    done = DONE_PATTERN.search(text)
    if done:
        return {"kind": "done", "content": done.group(1).strip()}

    blocked = BLOCKED_PATTERN.search(text)
    if blocked:
        return {"kind": "blocked", "content": blocked.group(1).strip()}

    return {"kind": "none", "raw": text}


def build_initial_prompt(plan_path: Path, charter_path: Path,
                         sovereignty: str, haiku_only: bool) -> str:
    """Compose the system + user prompt for TB's first turn."""
    plan_text = plan_path.read_text() if plan_path.exists() else "(plan not found)"
    charter_text = charter_path.read_text() if charter_path.exists() else "(charter not found)"

    # Truncate if huge — TB has 32K context, leave room for synthesis
    plan_text = plan_text[:20000]
    charter_text = charter_text[:8000]

    haiku_note = (
        "\n\nNOTE: --haiku-only flag is set. Always emit DELEGATE: haiku "
        "regardless of brief complexity. The wrapper will reject sonnet."
        if haiku_only else ""
    )

    return f"""You are TB-as-Principal. Read the charter, then read the plan, \
then decide.

[CHARTER]
{charter_text}

[PLAN]
{plan_text}

[SOVEREIGNTY: {sovereignty}]
[ITERATION: 1]
{haiku_note}

Your first turn: read the plan, identify the next concrete buildable \
slice, and either:
  (a) DELEGATE the slice to a worker (most slices fit this), OR
  (b) SYNTHESIZE if you need to think out loud first, OR
  (c) DONE if there's nothing to do, OR
  (d) BLOCKED if you need a founder-tap.

Use the marker protocol from the charter. No prose outside markers.
"""


def build_continuation_prompt(prior_synthesis: list,
                              worker_results: list,
                              iteration: int,
                              sovereignty: str,
                              haiku_only: bool) -> str:
    """Compose the next-turn prompt: prior context + new worker outputs."""
    syn_block = "\n\n".join(prior_synthesis[-3:])  # last 3 syntheses, cap context
    results_block = "\n\n".join(
        f"[WORKER {i+1} — {r['model']} :: {r['label']}]\n"
        f"ok={r['ok']} duration_ms={r['duration_ms']}\n"
        f"{r.get('output', '')[:3000]}"
        + (f"\n[ERROR: {r.get('error')}]" if not r["ok"] else "")
        for i, r in enumerate(worker_results)
    )
    haiku_note = (
        "\nNOTE: --haiku-only flag is set."
        if haiku_only else ""
    )

    return f"""TB principal — continuation turn.

[PRIOR_SYNTHESIS]
{syn_block or '(none)'}

[WORKER_RESULTS]
{results_block or '(none)'}

[ITERATION: {iteration}]
[SOVEREIGNTY: {sovereignty}]
{haiku_note}

Decide next step. Use markers (DELEGATE / SYNTHESIZE / DONE / BLOCKED).
"""


def stop_requested() -> bool:
    return STOP_FILE.exists()


def main():
    ap = argparse.ArgumentParser(
        description="TB-as-Principal headless wrapper")
    ap.add_argument("--plan", type=Path, required=True,
                    help="Path to plan markdown file")
    ap.add_argument("--charter", type=Path,
                    default=ROOT / "docs/org/charters/tb_principal.md",
                    help="Path to TB-principal charter")
    ap.add_argument("--max-iterations", type=int, default=30)
    ap.add_argument("--max-delegations", type=int, default=10)
    ap.add_argument("--dry-run", action="store_true",
                    help="Parse markers, print briefs, do NOT fire workers")
    ap.add_argument("--haiku-only", action="store_true",
                    help="Force haiku model on every worker")
    ap.add_argument("--sovereignty",
                    choices=["public", "guarded", "sovereign"],
                    default="guarded")
    ap.add_argument("--worker-timeout", type=int, default=600,
                    help="Per-worker subprocess timeout (seconds)")
    ap.add_argument("--principal-model",
                    choices=["tb", "sonnet"],
                    default="tb",
                    help="Which model orchestrates. 'tb' = TB v14 via "
                         "/tb/turn (sovereign, free, but v14 quality "
                         "iffy as of 2026-05-03). 'sonnet' = Claude "
                         "Sonnet via `claude -p --model sonnet` "
                         "subprocess; TB still injects RAG-grounded "
                         "context as a caveated prefix per turn (TB-as-"
                         "advisor pattern). Default: tb.")
    ap.add_argument("--no-tb-advice", action="store_true",
                    help="When --principal-model=sonnet, skip the TB "
                         "advisory context-injection. Pure Sonnet, no "
                         "brain context. Cheaper but loses local-RAG "
                         "advantage.")
    args = ap.parse_args()

    if not args.plan.exists():
        print(f"ERROR: plan not found: {args.plan}", file=sys.stderr)
        sys.exit(1)

    run_id = f"tbprincipal-{int(time.time())}-{uuid.uuid4().hex[:6]}"
    session_id = f"tbprincipal-{run_id}"
    print(f"[TB-PRINCIPAL] run_id={run_id}")
    print(f"[TB-PRINCIPAL] plan={args.plan}")
    print(f"[TB-PRINCIPAL] charter={args.charter}")
    print(f"[TB-PRINCIPAL] endpoint={TB_ENDPOINT}")
    print(f"[TB-PRINCIPAL] session_id={session_id}")
    print(f"[TB-PRINCIPAL] sovereignty={args.sovereignty}  "
          f"max_iter={args.max_iterations}  max_deleg={args.max_delegations}")
    print(f"[TB-PRINCIPAL] dry_run={args.dry_run}  haiku_only={args.haiku_only}")
    print(f"[TB-PRINCIPAL] principal_model={args.principal_model}  "
          f"tb_advice={'off' if args.no_tb_advice else 'on'}")

    if not endpoint_health():
        print(f"[TB-PRINCIPAL] FATAL: endpoint {TB_ENDPOINT}/tb/health "
              f"not reachable. Start tb_endpoint.py first.")
        sys.exit(2)

    _emit_event("tb_principal_start", {
        "run_id": run_id, "session_id": session_id, "plan": str(args.plan),
        "sovereignty": args.sovereignty, "dry_run": args.dry_run,
        "haiku_only": args.haiku_only,
    })

    prior_synthesis = []
    delegations_used = 0
    worker_results = []
    final_done = None
    final_blocked = None

    prompt = build_initial_prompt(
        args.plan, args.charter, args.sovereignty, args.haiku_only)

    for iteration in range(1, args.max_iterations + 1):
        if stop_requested():
            print(f"[TB-PRINCIPAL] stop file present — exiting at iter {iteration}")
            _emit_event("tb_principal_stop", {"run_id": run_id,
                                              "reason": "stop_file",
                                              "iteration": iteration})
            break

        print(f"\n[TB-PRINCIPAL] --- iter {iteration} ---")

        if args.principal_model == "tb":
            print(f"[TB-PRINCIPAL] calling /tb/turn "
                  f"(session={session_id})...")
            # Mode picks "work" (residual bucket per 3-mode taxonomy) —
            # principal decisions aren't code/life. Sovereignty
            # propagated; endpoint gates corpus writes accordingly.
            text, ms, resp = call_tb(
                prompt, session_id=session_id,
                sovereignty=args.sovereignty, mode="work",
                num_predict=2048, temperature=0.5)
            print(f"[TB-PRINCIPAL] TB responded in {ms}ms "
                  f"({len(text)} chars), "
                  f"rag_chunks={resp.get('rag_chunks', '?')}, "
                  f"corpus_written={resp.get('corpus_written', '?')}")
            if text.startswith("[TB_ENDPOINT_ERROR]"):
                print(f"[TB-PRINCIPAL] endpoint call failed: {text}")
                break
        else:  # principal_model == "sonnet" — TB-as-advisor pattern
            tb_advice = ""
            if not args.no_tb_advice:
                advice_query = (
                    f"Iter {iteration} of plan {args.plan.name}. "
                    f"Recent context: "
                    f"{(prior_synthesis[-1][:400] if prior_synthesis else 'iter 1, no prior synthesis')}. "
                    f"What does the brain know that's relevant?"
                )
                print(f"[TB-PRINCIPAL] fetching TB advice "
                      f"(context-injection)...")
                tb_advice = fetch_tb_advice(
                    advice_query, session_id,
                    sovereignty=args.sovereignty)
                print(f"[TB-PRINCIPAL]   TB advice: "
                      f"{len(tb_advice)} chars")
            print(f"[TB-PRINCIPAL] calling Sonnet principal "
                  f"(claude -p --model sonnet)...")
            text, ms, resp = call_sonnet_principal(
                prompt, query_summary=f"iter {iteration} of {args.plan.name}",
                tb_advice=tb_advice, timeout=args.worker_timeout)
            print(f"[TB-PRINCIPAL] Sonnet responded in {ms}ms "
                  f"({len(text)} chars), "
                  f"tb_advice_chars={resp.get('tb_advice_chars', 0)}")
            if text.startswith("[SONNET_PRINCIPAL_ERROR]"):
                print(f"[TB-PRINCIPAL] Sonnet principal error: {text}")
                break

        marker = parse_markers(text)
        kind = marker["kind"]
        print(f"[TB-PRINCIPAL] marker: {kind}")

        if kind == "done":
            final_done = marker["content"]
            break
        if kind == "blocked":
            final_blocked = marker["content"]
            print(f"[TB-PRINCIPAL] BLOCKED: {final_blocked[:200]}...")
            print(f"[TB-PRINCIPAL] (Telegram tap-decide queueing not "
                  f"implemented in v0; treat blocked as exit.)")
            break
        if kind == "synthesize":
            prior_synthesis.append(marker["content"])
            print(f"[TB-PRINCIPAL] synthesis appended "
                  f"({len(marker['content'])} chars)")
            prompt = build_continuation_prompt(
                prior_synthesis, [], iteration + 1,
                args.sovereignty, args.haiku_only)
            continue
        if kind == "delegate":
            new_results = []
            for d in marker["delegates"]:
                if delegations_used >= args.max_delegations:
                    print(f"[TB-PRINCIPAL] max_delegations reached, "
                          f"skipping further DELEGATE calls this turn")
                    break
                model = "haiku" if args.haiku_only else d["model"]
                print(f"[TB-PRINCIPAL] firing worker: {model} :: {d['label']}")
                result = fire_worker(model, d["label"], d["brief"],
                                     dry_run=args.dry_run,
                                     timeout=args.worker_timeout)
                new_results.append(result)
                delegations_used += 1
                ok_label = "ok" if result["ok"] else "FAIL"
                print(f"[TB-PRINCIPAL]   → {ok_label} ({result['duration_ms']}ms)")
            worker_results.extend(new_results)
            prompt = build_continuation_prompt(
                prior_synthesis, new_results, iteration + 1,
                args.sovereignty, args.haiku_only)
            continue
        # kind == "none" — TB didn't emit a marker
        print(f"[TB-PRINCIPAL] no marker found in TB output; "
              f"first 300 chars: {text[:300]!r}")
        # One retry with explicit-marker prompt
        prompt = (prompt +
                  "\n\n[WRAPPER] Your last reply had no marker. "
                  "You MUST emit one of: DELEGATE / SYNTHESIZE / DONE / "
                  "BLOCKED with the proper END_X closer. Try again.")
        if iteration > 1:  # only allow one retry
            print(f"[TB-PRINCIPAL] aborting after second no-marker turn")
            break
    else:
        print(f"[TB-PRINCIPAL] reached max_iterations={args.max_iterations}")

    # Write result file
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result_path = RESULT_DIR / f"tb_principal_{int(time.time())}.md"
    lines = [f"# TB Principal Run — {run_id}",
             f"timestamp: {datetime.now(timezone.utc).isoformat()}",
             f"plan: {args.plan}",
             f"sovereignty: {args.sovereignty}",
             f"dry_run: {args.dry_run}  haiku_only: {args.haiku_only}",
             f"delegations_used: {delegations_used}",
             "",
             "## Final state",
             ""]
    if final_done:
        lines += ["### DONE", "", final_done]
    elif final_blocked:
        lines += ["### BLOCKED", "", final_blocked]
    elif prior_synthesis:
        lines += ["### Last syntheses", ""] + prior_synthesis[-3:]
    else:
        lines.append("### (no DONE/BLOCKED/SYNTHESIZE captured)")
    lines += ["", "## Worker telemetry", ""]
    for r in worker_results:
        lines.append(f"- {r.get('model','?')} :: {r.get('label','?')}  "
                     f"ok={r['ok']} dur={r['duration_ms']}ms "
                     f"spawn_id={r.get('spawn_id','?')}")
    result_path.write_text("\n".join(lines))
    print(f"\n[TB-PRINCIPAL] result written to {result_path}")
    _emit_event("tb_principal_end", {
        "run_id": run_id, "result_path": str(result_path),
        "delegations_used": delegations_used,
        "done": bool(final_done), "blocked": bool(final_blocked),
    })


if __name__ == "__main__":
    main()
