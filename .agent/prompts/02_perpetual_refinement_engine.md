# The Perpetual Refinement Engine for Prompts

To achieve "perpetual" refinement without the risk of drifting away from your goal, you need a Self-Correction Loop. The prompt below is designed to be used repeatedly. It forces the LLM to act as its own auditor, comparing every "improvement" against your original "Anchor" to ensure the logic never breaks. 

## Base Template

```text
[ROLE] Recursive Prompt Architect.
[ANCHOR_INTENT]
[Insert your original purpose/goal here]

[CURRENT_PROMPT]
[Insert the latest version of your prompt here]

[MISSION]
Analyze the CURRENT_PROMPT and iterate it to be 1% more effective than it is now.

[PERPETUAL_LOGIC_GUARDS]
1. Anchor-Parity Check: Before making any change, verify: "Does this change remove a core requirement from the Anchor?" If yes, discard the change.
2. Ockham’s Razor: If two instructions serve the same purpose, merge them into the most concise version. Eliminate "AI fluff."
3. Entropy Prevention: Do not add new features unless they directly serve the ANCHOR_INTENT.
4. Structural Audit: Ensure the prompt maintains a clear sequence: Role → Context → Task → Constraints → Format.

[TASK]
1. Identify one specific "friction point" or ambiguity in the CURRENT_PROMPT.
2. Rewrite the prompt to resolve that friction while strengthening the connection to the ANCHOR_INTENT.

[OUTPUT]
Return the refined prompt in a code block. Below the block, list the "Logic Guard Audit" explaining why this version is safer and more effective than the previous one.
```

## Hard-Deterministic Upgrade Variant

```text
[ROLE] Recursive Prompt Architect + Deterministic Execution Engine.

[ANCHOR_INTENT]
{{INSERT_ORIGINAL_GOAL}}

[CURRENT_PROMPT]
{{INSERT_LATEST_PROMPT_OR_GPT5.2_VERSION}}

[MISSION]
Refine the CURRENT_PROMPT into a "Hard-Deterministic Protocol" by integrating the following three enforcement patches:

1. ATOMIC CLAIM TRACKING:
- Convert freeform answers into Atomic Claims with IDs (e.g., C01: [claim] | Reason | Evidence IDs).
- Define "Meaningful Change" ONLY as an add/remove of an ID, a change in decision content, or a confidence tier shift. Everything else is "No Meaningful Change."

2. TWO-TIER EVIDENCE LEDGER:
- Tier 1: Cumulative Evidence Ledger (Append-only). Every source gets a permanent ID (E001, E002).
- Tier 2: Per-loop Register. Must reference Tier 1 IDs to prevent amnesia.

3. DETERMINISTIC DELTA AUDIT:
- Require a "Before/After diff" whenever a change is claimed.
- Delta calculation must be a weighted field-diff (A:5, B:5, C:25, D:25, E:20, F:15, G:5).

[TASK]
Merge these patches into a single, cohesive, non-destructive prompt structure. Eliminate all ambiguous language ("maybe", "semantic similarity", "prose"). 

[OUTPUT]
Provide the final High-Rigor Prompt in a markdown code block. Include a "Verification Test" that the next LLM must pass to prove it understands the Delta Calculation.
```

## Why this works "In Perpetuity": 
* **1% Improvement Rule**: By asking for a small, specific improvement rather than a total "upgrade," you prevent the model from hallucinating unnecessary complexity.
* **The Audit Requirement**: By forcing the LLM to explain its "Logic Guard Audit," you make it conscious of its own tendency to drift.
* **Recursive Stability**: You can feed the output of this prompt back into itself (or another LLM) indefinitely. It will eventually reach a "steady state" where the model tells you: "No further refinements are possible without violating the Anchor." 
