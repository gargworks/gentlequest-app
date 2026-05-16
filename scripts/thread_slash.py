"""Slash command dispatcher for /thread (Phase 2 §2.7).

Pure dispatcher — no I/O of its own. The Telegram bot and the REPL both
import handle_thread_slash() and pass the parsed sub-command + thread
storage state. The dispatcher returns:

    SlashResult(text=<reply>, mutated=<bool>, switched_to=<id|None>)

Caller persists if mutated, updates local active-thread tracking if
switched_to is set, and prints/sends `text` to the user.

Subcommands (parity bot + REPL):
    /thread                        list top 5 active
    /thread list                   same
    /thread switch <name>          activate (prefix match accepted)
    /thread new <name>             force-create (subject to hard ceiling)
    /thread archive <name>         flip to archived
    /thread merge <a> <b>          merge b into a; b is archived
    /thread rename <old> <new>     change label
    /thread suggest-merge          high-similarity pair candidates
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from scripts.thread_cron import find_merge_candidates
from scripts.thread_storage import ThreadStorage


# ── Result type ──────────────────────────────────────────────────────

@dataclass
class SlashResult:
    text: str
    mutated: bool = False           # caller should persist if True
    switched_to: Optional[str] = None  # caller updates local active-thread
    ok: bool = True                 # False → error / refusal


# ── Helpers ──────────────────────────────────────────────────────────

def _resolve_thread_id(
    threads_data: Dict[str, Dict[str, Any]],
    chat_id: str,
    name: str,
    *,
    active_only: bool = False,
) -> Optional[str]:
    """Resolve a user-typed name to a real thread id. Tries exact match
    first, then case-insensitive prefix match. Returns None if no
    unambiguous match.
    """
    threads = threads_data.get(chat_id, {}).get("threads", {})
    if active_only:
        candidates = {tid: t for tid, t in threads.items()
                      if t.get("status") == "active"}
    else:
        candidates = dict(threads)
    if not candidates or not name:
        return None
    # Exact id match
    if name in candidates:
        return name
    # Case-insensitive prefix match on id OR label
    n_lower = name.lower()
    matches = [
        tid for tid, t in candidates.items()
        if tid.lower().startswith(n_lower)
        or t.get("label", "").lower().startswith(n_lower)
    ]
    if len(matches) == 1:
        return matches[0]
    return None


def _format_thread_line(thread: Dict[str, Any], is_active: bool = False) -> str:
    marker = "★ " if is_active else "  "
    label = thread.get("label", thread["id"])
    turn_count = thread.get("turn_count", 0)
    last = thread.get("last_activity", "")
    last_short = last.split("T")[0] if "T" in last else last
    return f"{marker}{label} (id={thread['id']}, turns={turn_count}, last={last_short})"


# ── Subcommand handlers ──────────────────────────────────────────────

def _cmd_list(
    storage: ThreadStorage,
    threads_data: Dict[str, Dict[str, Any]],
    chat_id: str,
    args: List[str],
) -> SlashResult:
    storage.initialize_chat(threads_data, chat_id)
    active = storage.list_active(threads_data, chat_id)
    if not active:
        return SlashResult(text="(no active threads)")
    active_id = threads_data[chat_id].get("active_thread_id")
    # Sort by last_activity desc
    active_sorted = sorted(
        active, key=lambda t: t.get("last_activity", ""), reverse=True
    )[:5]
    lines = ["Active threads (top 5):"]
    for t in active_sorted:
        lines.append(_format_thread_line(t, is_active=(t["id"] == active_id)))
    return SlashResult(text="\n".join(lines))


def _cmd_switch(
    storage: ThreadStorage,
    threads_data: Dict[str, Dict[str, Any]],
    chat_id: str,
    args: List[str],
) -> SlashResult:
    if not args:
        return SlashResult(text="usage: /thread switch <name>", ok=False)
    name = " ".join(args)
    storage.initialize_chat(threads_data, chat_id)
    tid = _resolve_thread_id(threads_data, chat_id, name, active_only=True)
    if not tid:
        return SlashResult(
            text=f"thread '{name}' not found (or ambiguous, or archived)",
            ok=False,
        )
    if not storage.set_active(threads_data, chat_id, tid):
        return SlashResult(text=f"could not activate '{tid}'", ok=False)
    return SlashResult(
        text=f"[switched to {tid}]",
        mutated=True,
        switched_to=tid,
    )


def _cmd_new(
    storage: ThreadStorage,
    threads_data: Dict[str, Dict[str, Any]],
    chat_id: str,
    args: List[str],
) -> SlashResult:
    if not args:
        return SlashResult(text="usage: /thread new <name>", ok=False)
    name = "_".join(args).lower()
    storage.initialize_chat(threads_data, chat_id)
    thread, reason = storage.create_thread(
        threads_data, chat_id, name, label=" ".join(args),
    )
    if reason == "hard_ceiling":
        merge_c, archive_c = storage.suggest_consolidation(
            threads_data, chat_id
        )
        hint = ""
        if merge_c and archive_c:
            hint = (
                f"\n  consolidation hint: archive '{archive_c['id']}' "
                f"or merge '{merge_c['id']}' into another thread first"
            )
        return SlashResult(
            text=(f"hard ceiling ({storage.hard_ceiling}) reached; "
                  f"cannot create '{name}'{hint}"),
            ok=False,
        )
    if reason == "exists":
        return SlashResult(
            text=f"thread '{name}' already exists",
            ok=False,
        )
    # Auto-switch to the new thread
    storage.set_active(threads_data, chat_id, name)
    body = [f"[created thread '{name}' and switched]"]
    # Soft-ceiling warning
    n_active = len(storage.list_active(threads_data, chat_id))
    if n_active >= storage.soft_ceiling:
        merge_c, archive_c = storage.suggest_consolidation(
            threads_data, chat_id
        )
        body.append(
            f"⚠ {n_active} active threads (soft ceiling = "
            f"{storage.soft_ceiling}). consider archiving "
            f"'{archive_c['id']}' or merging '{merge_c['id']}'."
        )
    return SlashResult(
        text="\n".join(body),
        mutated=True,
        switched_to=name,
    )


def _cmd_archive(
    storage: ThreadStorage,
    threads_data: Dict[str, Dict[str, Any]],
    chat_id: str,
    args: List[str],
) -> SlashResult:
    if not args:
        return SlashResult(text="usage: /thread archive <name>", ok=False)
    name = " ".join(args)
    tid = _resolve_thread_id(threads_data, chat_id, name, active_only=True)
    if not tid:
        return SlashResult(
            text=f"active thread '{name}' not found", ok=False
        )
    if not storage.archive(threads_data, chat_id, tid):
        return SlashResult(text=f"could not archive '{tid}'", ok=False)
    new_active = threads_data[chat_id].get("active_thread_id")
    body = f"[archived '{tid}']"
    if new_active and new_active != tid:
        body += f"\n[active now: {new_active}]"
    return SlashResult(
        text=body, mutated=True,
        switched_to=new_active if new_active else None,
    )


def _cmd_merge(
    storage: ThreadStorage,
    threads_data: Dict[str, Dict[str, Any]],
    chat_id: str,
    args: List[str],
) -> SlashResult:
    if len(args) < 2:
        return SlashResult(text="usage: /thread merge <winner> <loser>",
                           ok=False)
    winner_in = args[0]
    loser_in = args[1]
    winner_id = _resolve_thread_id(threads_data, chat_id, winner_in)
    loser_id = _resolve_thread_id(threads_data, chat_id, loser_in)
    if not winner_id:
        return SlashResult(text=f"thread '{winner_in}' not found", ok=False)
    if not loser_id:
        return SlashResult(text=f"thread '{loser_in}' not found", ok=False)
    if winner_id == loser_id:
        return SlashResult(text="cannot merge a thread into itself", ok=False)
    if not storage.merge(threads_data, chat_id, winner_id, loser_id):
        return SlashResult(text="merge failed", ok=False)
    new_active = threads_data[chat_id].get("active_thread_id")
    return SlashResult(
        text=f"[merged '{loser_id}' → '{winner_id}'; '{loser_id}' archived]",
        mutated=True,
        switched_to=new_active if new_active else None,
    )


def _cmd_rename(
    storage: ThreadStorage,
    threads_data: Dict[str, Dict[str, Any]],
    chat_id: str,
    args: List[str],
) -> SlashResult:
    if len(args) < 2:
        return SlashResult(
            text="usage: /thread rename <old> <new label>", ok=False,
        )
    old = args[0]
    new_label = " ".join(args[1:])
    tid = _resolve_thread_id(threads_data, chat_id, old)
    if not tid:
        return SlashResult(text=f"thread '{old}' not found", ok=False)
    if not storage.rename(threads_data, chat_id, tid, new_label):
        return SlashResult(text=f"rename failed for '{tid}'", ok=False)
    return SlashResult(
        text=f"[renamed '{tid}' → label='{new_label}']",
        mutated=True,
    )


def _cmd_suggest_merge(
    storage: ThreadStorage,
    threads_data: Dict[str, Dict[str, Any]],
    chat_id: str,
    args: List[str],
) -> SlashResult:
    pairs = find_merge_candidates(threads_data, chat_id)
    if not pairs:
        return SlashResult(text="(no merge candidates found)")
    lines = ["Merge candidates (descending similarity):"]
    for a, b, sim in pairs[:5]:
        lines.append(
            f"  {a['id']} ↔ {b['id']} ({sim:.2f}): "
            f"'{a.get('label', '?')}' vs '{b.get('label', '?')}'"
        )
    return SlashResult(text="\n".join(lines))


# ── Dispatcher ───────────────────────────────────────────────────────

_HANDLERS: Dict[str, Callable[..., SlashResult]] = {
    "list": _cmd_list,
    "": _cmd_list,           # bare /thread
    "switch": _cmd_switch,
    "new": _cmd_new,
    "archive": _cmd_archive,
    "merge": _cmd_merge,
    "rename": _cmd_rename,
    "suggest-merge": _cmd_suggest_merge,
    "suggest_merge": _cmd_suggest_merge,  # accept underscore variant
}


_USAGE = (
    "usage:\n"
    "  /thread                          list top 5 active\n"
    "  /thread list                     same as /thread\n"
    "  /thread switch <name>            switch active (prefix match ok)\n"
    "  /thread new <name>               create + switch\n"
    "  /thread archive <name>           archive (active only)\n"
    "  /thread merge <winner> <loser>   merge loser into winner\n"
    "  /thread rename <old> <new label> change label\n"
    "  /thread suggest-merge            high-similarity pairs"
)


def handle_thread_slash(
    storage: ThreadStorage,
    threads_data: Dict[str, Dict[str, Any]],
    chat_id: str,
    raw_arg: str,
) -> SlashResult:
    """Top-level dispatcher.

    raw_arg: everything after "/thread " (may be empty for bare `/thread`).
    Splits on whitespace; first token is sub-command.
    """
    parts = raw_arg.strip().split()
    if not parts:
        return _HANDLERS[""](storage, threads_data, chat_id, [])
    sub = parts[0].lower()
    rest = parts[1:]
    handler = _HANDLERS.get(sub)
    if handler is None:
        return SlashResult(text=f"unknown subcommand: {sub}\n{_USAGE}",
                           ok=False)
    return handler(storage, threads_data, chat_id, rest)
