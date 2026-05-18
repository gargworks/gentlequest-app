"""Prompt preambles for TB quality-compound deployment.

These strings are injected into TB prompts (when principal_model=tb) or
Sonnet prompts (when principal_model=sonnet) to constrain output shape
and prevent the failure modes diagnosed in the 2026-05-07 tb-log Manju
run: free-form composition produces confabulated facts, mode-mixing leaks
infra trivia into life answers, and templates-without-grounding mimic
shape without substance.
"""

# Mode anti-mixing — applied to TB-only path when mode=life. Catches the
# residual cross-domain leak that the brain_rag.py hard-filter (PR #298)
# can't reach (e.g., topic drift inside a single answer).
ANTIMIX_LIFE_PREAMBLE = (
    "[MODE: LIFE — personal/relational/journal context only]\n"
    "Do NOT suggest infrastructure, code, file paths, scheduling, devops, "
    "snapshots, ports, cron jobs, deployment, or technical configuration. "
    "If your answer drifts technical, stop and re-anchor on the human topic. "
    "If you find yourself writing about ports/files/cron/snapshots/launchd/"
    "API/.py/.sh/.json/.plist/launchctl, that is a sign you've drifted — "
    "delete and start over.\n"
)

ANTIMIX_CODE_PREAMBLE = (
    "[MODE: CODE — engineering/technical context only]\n"
    "Do NOT inject relationship advice, journal framing, emotional coaching, "
    "or strategy soft-talk into engineering answers. Stay technical, "
    "specific, file-path-aware.\n"
)

# Constrained-output template — applied to TB-only path when principal=tb
# AND mode=life. Forces TB into a strict 3-section structure that makes
# confabulation visible (anything not in [FACTS] is tagged uncertain).
CONSTRAINED_LIFE_PREAMBLE = (
    "[OUTPUT FORMAT — STRICT]\n"
    "You MUST respond in exactly these three sections, no markdown headers, "
    "no numbered lists:\n"
    "\n"
    "FACTS_FROM_BRAIN:\n"
    "  Quote ONLY information that appears verbatim in [BRAIN KNOWLEDGE] "
    "above. If a claim isn't in brain, do not put it here.\n"
    "\n"
    "GAPS:\n"
    "  List what you'd need from the user to answer fully. If brain has "
    "nothing relevant, say 'brain doesn't have this'.\n"
    "\n"
    "TENTATIVE (TB-guess):\n"
    "  Up to 3 short sentences of inference. Tag this section as guess. "
    "Do not invent biographical details, dates, names, or numbers.\n"
)

# TB-as-grounding instruction — applied when principal_model=sonnet. TB's
# job in this path is retrieval + summary, not composition. Sonnet handles
# the writing.
GROUNDING_ONLY_PREAMBLE = (
    "[ROLE: GROUNDING ONLY]\n"
    "Your job is to summarize what the brain knows about this query in 5-8 "
    "short bullet points. Do NOT compose a full answer — a stronger model "
    "will write the answer using your bullets. Pull from [BRAIN KNOWLEDGE] "
    "above. If brain has nothing relevant to the query, say 'brain has no "
    "relevant context'.\n"
)
