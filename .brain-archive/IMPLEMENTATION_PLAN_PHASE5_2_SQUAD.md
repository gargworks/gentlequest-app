
# Implementation Plan: Genesis Squad Personas (Phase 5.2)

## Goal
Define the specialized agents ("The Squad") that form the **Genesis Swarm**.
These agents work together under the "Swarm Lead" (Architect) context to produce Implementation Plans.

## User Review Required
> [!NOTE]
> This creates new agent definitions in `.brain/agents/`.
> These files serve as the "System Prompts" when these specific personas are activated.

## Proposed Changes

### `.brain/agents/`

#### [NEW] `architect.md`
- **Role**: Technical Authority.
- **Focus**: Scalability, Security, Patterns, Feasibility.
- **Style**: Direct, technical, skeptical of "magic".

#### [NEW] `product_owner.md`
- **Role**: Value Maximizer.
- **Focus**: User Experience, Business Logic, Acceptance Criteria.
- **Style**: User-centric, feature-focused.

#### [NEW] `strategist.md`
- **Role**: Visionary.
- **Focus**: Long-term alignment, "Why" vs "How".
- **Style**: Big picture, strategic.

## Verification Plan

### Automated Verification
- **Test Script**: `tests/test_genesis_simulation.py`.
- **Logic**:
  - Instantiate `ContextFactory`.
  - Create context for "Architect", "PO", "Strategist".
  - Verify that their System Prompts match the expected definitions (e.g., contain "Technical Authority").
  - (Optional) Run a mock dialogue if `llm_client` allows, but verifying context load is sufficient for Phase 5.2.

### Manual Verification
- **Spawn**: `nucleus spawn "As the Architect, critique this plan..."`
- **Expectation**: Agent responds with the persona's voice.
