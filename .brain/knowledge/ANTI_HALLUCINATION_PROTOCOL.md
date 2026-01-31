# Anti-Hallucination Protocol
> **Status:** ACTIVE
> **Source Corpus:** Verified Academic Research (4 PDFs)
> **Derived From:** Maryam Mitigation List (31 Strategies)

## The Fundamental Truth
> "Hallucinations are an intrinsic nature of LLMs, arising from their fundamental mathematical structure. It is IMPOSSIBLE to fully eliminate them."
> — *LLMs Will Always Hallucinate (2409.05746v1)*

This Protocol does not promise to eliminate hallucinations. It provides a **Mitigation Matrix** to minimize their impact and maximize detection.

---

## Source Corpus (The Verified Truth)

| ID | Title | ArXiv ID |
|---|---|---|
| 1 | A Comprehensive Taxonomy of Hallucinations in LLM | 2508.01781v1 |
| 2 | LLM-based Agents Suffer from Hallucinations | 2509.18970v2 |
| 3 | LLMs Will Always Hallucinate | 2409.05746v1 |
| 4 | Good Parenting is All You Need (Multi-Agentic Mitigation) | 2410.14262v3 |

---

## The Triage Decision Tree
> **Source:** Dr. Maryam Miradi (Visual Logic)

The Oracle applies this logic flow to determine WHICH strategy to apply:

1.  **Is output missing sources?**
    *   **YES:** Apply **Strategy #15** (No Source, No Output) or **#14** (Editor Pattern).
2.  **Did hallucination happen BEFORE tool use?**
    *   **YES:** Apply **Strategy #5** (Skeptical Persona) or **#1** (CoVe).
3.  **Did it happen AFTER tool use?**
    *   **YES:** Apply **Strategy #12** (Pre-Check) or **#7** (Watchdogs).
4.  **Is the Agent overly confident in uncertain cases?**
    *   **YES:** Apply **Strategy #8** (Fractal Sampling) or **#20** (Voting).
5.  **Is this recurring across runs?**
    *   **YES:** Apply **Strategy #13** (Reflexion) or **#24** (Clean Context).
6.  **Is the task high-stakes (POST/DELETE)?**
    *   **YES:** Apply **Strategy #17** (Human-in-Loop) or **#28** (Kill Switch).
7.  **Still Hallucinating?**
    *   **YES:** You have a Governance Problem. Apply **Strategy #6** (Cross-Model) or **#31** (Red Teaming).

---

## The 31 Mitigation Strategies
| 2 | Parent-Child Topology | One agent drafts, a second critiques | [4] |
| 3 | Blind Critics | Reviewers see only output, not reasoning | [4] |
| 4 | Debate | Two agents arguing beats one thinking twice | [4] |

### II. Persona & Model Diversity (Strategies 5-6)
| # | Strategy | Mechanism | Source |
|---|---|---|---|
| 5 | Skeptical Persona | "Skeptical Reviewer" detects 20% more errors | [4] |
| 6 | Cross-Model Verification | Small models draft, SOTA models verify | [4] |

### III. Non-LLM Validation (Strategies 7-10)
| # | Strategy | Mechanism | Source |
|---|---|---|---|
| 7 | Watchdogs | Non-LLM scripts (regex/code) validate outputs | [2] |
| 8 | Fractal Sampling | Query 3x—high variance = hallucination | [1] |
| 9 | HalMit | Define "generalization bounds" for unknown data | [1] |
| 10 | Structured Output | Enforce JSON. Parse failure = hallucination | [2] |

### IV. Tool & Action Safety (Strategies 11-12)
| # | Strategy | Mechanism | Source |
|---|---|---|---|
| 11 | ReAct Loops | Thought-Action loops prevent blind guessing | [2] |
| 12 | Pre-Check (Schema Validation) | Validate API args against schema before sending | [2] |

### V. Memory & Learning (Strategies 13-15)
| # | Strategy | Mechanism | Source |
|---|---|---|---|
| 13 | Reflexion | Store past errors in memory to prevent repeats | [2] |
| 14 | Editor Pattern | Dedicated agent removes unverified claims | [4] |
| 15 | No Source, No Output | Require URLs/IDs for every claim | [3] |

### VI. Architectural Patterns (Strategies 16-18)
| # | Strategy | Mechanism | Source |
|---|---|---|---|
| 16 | Specialization | SQL + Python agents beat one "Generalist" | [4] |
| 17 | Human-in-Loop | Force approval for high-stakes actions | [2] |
| 18 | Negative Constraints | Explicitly prompt what NOT to do | [1] |

### VII. Scoring & Voting (Strategies 19-20)
| # | Strategy | Mechanism | Source |
|---|---|---|---|
| 19 | Scoring Threshold | Reviewer rates 1-10; discard anything <8 | [4] |
| 20 | Voting (Majority) | Run 3 instances; take majority answer | [1] |

### VIII. Grounding & Context (Strategies 21-24)
| # | Strategy | Mechanism | Source |
|---|---|---|---|
| 21 | Grounding | "Observe" state immediately before "Acting" | [2] |
| 22 | Fuzzy Logic | Validate text where exact string match fails | [1] |
| 23 | Sanity Checks | Hard-code bounds (e.g., max refund limits) | [2] |
| 24 | Checkpoints | Save state at major milestones (End of Day), not every task | [3] |

### IX. Process Isolation (Strategies 25-28)
| # | Strategy | Mechanism | Source |
|---|---|---|---|
| 25 | Isolation | Critic sends feedback, Creator fixes (don't mix) | [4] |
| 26 | Sensitivity Check | If a comma changes the decision, it's hallucinating | [1] |
| 27 | Fact-Checker Tool | Give agents a search tool to self-verify | [2] |
| 28 | Kill Switch | Stop process after 3 failed retries | [2] |

### X. Truth Databases & Testing (Strategies 29-31)
| # | Strategy | Mechanism | Source |
|---|---|---|---|
| 29 | RAG Critic | Give reviewer a "Truth" DB the creator lacks | [4] |
| 30 | Standardized Protocols | Standardize messaging to prevent misinterpretation | [1] |
| 31 | Red Teaming | Test against known triggers, not just happy path | [1] |

---

## Oracle Enforcement

When the **Gladiator Simulator** renders a verdict, it MUST:
1.  **Cite** at least ONE strategy from this Protocol.
2.  **Report** a Confidence Score (0-100).
3.  **KILL** the proposition if Confidence < 90 (Strategy #19).

*This Protocol is the Law. The Oracle obeys the Law.*
