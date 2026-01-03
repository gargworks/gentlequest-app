# Discovered Patterns

> Patterns that emerge from repeated experience.
> Used by agents to make better decisions.

---

## Agent Patterns

### Pattern: Batch Over Individual
**Context:** Content generation (Reddit posts, emails)
**Pattern:** Always generate 5-10 variants, let founder select best 2-3
**Reason:** Higher quality through selection vs single-shot generation

### Pattern: Spec Before Code
**Context:** Feature development
**Pattern:** Architect writes spec first, Developer implements second
**Reason:** Reduces rework, ensures alignment with strategy

### Pattern: Artifact First
**Context:** All cross-agent communication
**Pattern:** Write to ledger/artifacts before verbal explanation
**Reason:** Persistence, auditability, no context drift

---

## Technical Patterns

### Pattern: Native Over Framework
**Context:** AI integrations
**Pattern:** Prefer native API (Gemini) over frameworks (LangChain)
**Reason:** Simpler, fewer dependencies, easier to debug

### Pattern: pgvector Over External
**Context:** Vector storage
**Pattern:** Use PostgreSQL pgvector instead of ChromaDB/Pinecone
**Reason:** Single database, no new infra, already on Render

---

## Product Patterns

### Pattern: Actions Over Advice
**Context:** Luna's responses
**Pattern:** Luna should DO things (log mood) not just SAY things
**Reason:** Differentiates from generic chatbots

### Pattern: Gentle Over Aggressive
**Context:** User engagement
**Pattern:** "Progress without pressure" - never shame or push
**Reason:** Core brand identity, mental health sensitivity

---

*Updated by Synthesizer during meta-optimization cycles*
