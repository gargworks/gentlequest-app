"""Skill Generator — Turn a scored cluster into a SKILL.md string.

Deterministic generation. No LLM required.
The DATA is the skill, not a summary of the data.
"""

import re
from collections import Counter
from typing import Dict, List, Tuple

# Patterns for anonymization
_FILE_PATH_RE = re.compile(r"(?:[/\\][\w.-]+){2,}")
_CAMEL_RE = re.compile(r"\b[a-z]+(?:[A-Z][a-z]+){1,}\b")
_PASCAL_RE = re.compile(r"\b(?:[A-Z][a-z]+){2,}\b")
_SNAKE_RE = re.compile(r"\b[a-z]+(?:_[a-z]+){2,}\b")
_URL_RE = re.compile(r"https?://\S+")
_ERROR_RE = re.compile(r"(?:Error|Exception|Traceback|FAILED|error:)\s*[^\n]{10,}")


def _extract_trigger_phrases(intents: List[str], top_n: int = 5) -> List[str]:
    """Extract distinctive trigger phrases from cluster intents.

    Algorithm:
        1. Take first 6 words of each intent (the "verb phrase")
        2. Normalize: lowercase, strip articles
        3. Group by leading 3-gram
        4. Pick most frequent variant from each group
        5. Return top_n most distinctive phrases
    """
    prefixes: Counter = Counter()
    prefix_to_full: Dict[str, str] = {}

    for intent in intents:
        words = intent.lower().split()[:6]
        if not words:
            continue
        phrase = " ".join(words)
        # Normalize: strip leading articles
        phrase = re.sub(r"^(please |can you |could you |i need to |i want to )", "", phrase)
        key = " ".join(phrase.split()[:3])  # 3-gram grouping key
        prefixes[key] += 1
        # Keep the longest variant as representative
        if key not in prefix_to_full or len(phrase) > len(prefix_to_full[key]):
            prefix_to_full[key] = phrase

    # Return top_n most frequent, using the full representative phrase
    top = prefixes.most_common(top_n)
    return [prefix_to_full[key] for key, _ in top if key in prefix_to_full]


def _extract_tool_sequence(turns: List[dict]) -> str:
    """Find most common tool usage pattern across turns.

    Counts tool co-occurrence across turns, builds description like:
        "Read files to understand context -> Edit to make changes -> Bash to verify"
    """
    tool_sequences: Counter = Counter()
    for turn in turns:
        tools = turn.get("tools_used", [])
        if tools:
            # Deduplicate while preserving order
            seen = set()
            ordered = []
            for t in tools:
                if t not in seen:
                    seen.add(t)
                    ordered.append(t)
            key = tuple(ordered)
            tool_sequences[key] += 1

    if not tool_sequences:
        return "No consistent tool pattern detected."

    # Get most common sequence
    best_seq, _ = tool_sequences.most_common(1)[0]

    # Build human-readable description
    tool_descriptions = {
        "Read": "Read files to understand context",
        "Edit": "Edit to make changes",
        "Bash": "Bash to verify",
        "Write": "Write new files",
        "Grep": "Search for patterns",
        "Glob": "Find files",
        "Agent": "Delegate to sub-agents",
    }
    parts = [tool_descriptions.get(t, t) for t in best_seq]
    return " -> ".join(parts)


def _anonymize_text(text: str) -> str:
    """Strip project-specific details from intent/outcome text.

    Replaces:
        - File paths -> <file>
        - Function/class names (camelCase, PascalCase) -> <name>
        - Specific error messages -> <error>
        - URLs -> <url>

    Preserves: action verbs, general descriptions, tool names.
    """
    text = _URL_RE.sub("<url>", text)
    text = _FILE_PATH_RE.sub("<file>", text)
    text = _ERROR_RE.sub("<error>", text)
    text = _CAMEL_RE.sub("<name>", text)
    text = _PASCAL_RE.sub("<name>", text)
    text = _SNAKE_RE.sub("<name>", text)
    # Collapse multiple <name> in a row
    text = re.sub(r"(<name>\s*){2,}", "<name> ", text)
    return text.strip()


def _select_examples(turns: List[dict], n: int = 3) -> List[dict]:
    """Pick highest-quality, most diverse examples from cluster turns.

    Sorts by quality_grade (platinum first), then by intent length
    (longer = more descriptive). Deduplicates by first-5-word prefix.
    Returns anonymized intent->outcome pairs.
    """
    grade_order = {"platinum": 0, "gold": 1, "silver": 2, "copper": 3}

    sorted_turns = sorted(
        turns,
        key=lambda t: (
            grade_order.get(t.get("quality_grade", "copper"), 3),
            -len(t.get("intent", "")),
        ),
    )

    seen_prefixes = set()
    examples = []
    for turn in sorted_turns:
        intent = turn.get("intent", "")
        if not intent:
            continue
        prefix = " ".join(intent.lower().split()[:5])
        if prefix in seen_prefixes:
            continue
        seen_prefixes.add(prefix)
        examples.append({
            "intent": _anonymize_text(intent),
            "outcome": _anonymize_text(turn.get("outcome", "")),
        })
        if len(examples) >= n:
            break

    return examples


def generate_skill_md(cluster: dict) -> str:
    """Generate SKILL.md from a scored cluster.

    SKILL.md output format:
        ---
        name: {domain}
        description: {1-line summary from trigger phrases}
        version: 1.0.0
        source: nucleus-flywheel
        generated_from: {N} conversation turns
        score: {composite_score}
        ---

        # {Domain Title}

        ## When to use
        - {trigger phrase 1}
        - {trigger phrase 2}
        ...

        ## Approach
        {tool sequence description}

        ## Key patterns
        {common decisions/actions extracted from turn data}

        ## Examples
        ### Example 1
        **Intent:** {anonymized intent}
        **Outcome:** {anonymized outcome}
    """
    domain = cluster.get("domain", "unknown")
    score = cluster.get("score", 0)
    size = cluster.get("size", 0)
    intents = cluster.get("intents", [])
    turns = cluster.get("turns", [])

    # Title: capitalize each word
    title = " ".join(word.capitalize() for word in domain.split("-"))

    # Trigger phrases
    triggers = _extract_trigger_phrases(intents)
    if not triggers:
        triggers = [_anonymize_text(intents[0])] if intents else ["(no triggers)"]

    # Description from first trigger
    description = f"When user asks to {triggers[0]}" if triggers else f"Skill for {domain}"

    # Tool sequence
    tool_seq = _extract_tool_sequence(turns)

    # Key patterns from decisions
    decision_counts: Counter = Counter()
    for turn in turns:
        for d in turn.get("decisions", []):
            anon = _anonymize_text(d)
            if len(anon) > 10:
                decision_counts[anon] += 1
    key_patterns = [d for d, _ in decision_counts.most_common(5)]

    # Examples
    examples = _select_examples(turns)

    # Build SKILL.md
    lines = [
        "---",
        f"name: {domain}",
        f"description: {description}",
        "version: 1.0.0",
        "source: nucleus-flywheel",
        f"generated_from: {size} conversation turns",
        f"score: {score}",
        "---",
        "",
        f"# {title}",
        "",
        "## When to use",
    ]
    for trigger in triggers:
        lines.append(f"- {trigger}")
    lines.append("")
    lines.append("## Approach")
    lines.append(tool_seq)
    lines.append("")

    if key_patterns:
        lines.append("## Key patterns")
        for pattern in key_patterns:
            lines.append(f"- {pattern}")
        lines.append("")

    if examples:
        lines.append("## Examples")
        for i, ex in enumerate(examples, 1):
            lines.append(f"### Example {i}")
            lines.append(f"**Intent:** {ex['intent']}")
            lines.append(f"**Outcome:** {ex['outcome']}")
            lines.append("")

    return "\n".join(lines)
