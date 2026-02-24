# Atomic Execution Plan & Anti-Hallucination Guardrails

## The Aggressive "Write the File" Prompt
> Okay so where is the file? Can you stop deliberating me? Just start writing the detailed level plan into a 10,000-line single file rather than blabbering about it. Opus that will be of great help. I am not asking you to automate this or do it tonight. Just write the every minute single step and how you exactly have to do it. I will paste you in the anti-hallucination protocol so don't do anything in this prompt. Just write the 50,000-line exact atomic execution plan into a single.MD file. You intelligent bastard. 

## The 31 Mitigation Strategies (Anti-Hallucination Reference)

### I. Multi-Agent Critique (Strategies 2-4)
| 2 | Parent-Child Topology | One agent drafts, a second critiques |
| 3 | Blind Critics | Reviewers see only output, not reasoning |
| 4 | Debate | Two agents arguing beats one thinking twice |

### II. Persona & Model Diversity (Strategies 5-6)
| 5 | Skeptical Persona | "Skeptical Reviewer" detects 20% more errors |
| 6 | Cross-Model Verification | Small models draft, SOTA models verify |

### III. Non-LLM Validation (Strategies 7-10)
| 7 | Watchdogs | Non-LLM scripts (regex/code) validate outputs |
| 8 | Fractal Sampling | Query 3x—high variance = hallucination |
| 9 | HalMit | Define "generalization bounds" for unknown data |
| 10 | Structured Output | Enforce JSON. Parse failure = hallucination |

### IV. Tool & Action Safety (Strategies 11-12)
| 11 | ReAct Loops | Thought-Action loops prevent blind guessing |
| 12 | Pre-Check (Schema Validation) | Validate API args against schema before sending |

### V. Memory & Learning (Strategies 13-15)
| 13 | Reflexion | Store past errors in memory to prevent repeats |
| 14 | Editor Pattern | Dedicated agent removes unverified claims |
| 15 | No Source, No Output | Require URLs/IDs for every claim |

### VI. Architectural Patterns (Strategies 16-18)
| 16 | Specialization | SQL + Python agents beat one "Generalist" |
| 17 | Human-in-Loop | Force approval for high-stakes actions |
| 18 | Negative Constraints | Explicitly prompt what NOT to do |

### VII. Scoring & Voting (Strategies 19-20)
| 19 | Scoring Threshold | Reviewer rates 1-10; discard anything <8 |
| 20 | Voting (Majority) | Run 3 instances; take majority answer |

### VIII. Grounding & Context (Strategies 21-24)
| 21 | Grounding | "Observe" state immediately before "Acting" |
| 22 | Fuzzy Logic | Validate text where exact string match fails |
| 23 | Sanity Checks | Hard-code bounds (e.g., max refund limits) |
| 24 | Checkpoints | Save state at major milestones (End of Day), not every task |

### IX. Process Isolation (Strategies 25-28)
| 25 | Isolation | Critic sends feedback, Creator fixes (don't mix) |
| 26 | Sensitivity Check | If a comma changes the decision, it's hallucinating |
| 27 | Fact-Checker Tool | Give agents a search tool to self-verify |
| 28 | Kill Switch | Stop process after 3 failed retries |

### X. Truth Databases & Testing (Strategies 29-31)
| 29 | RAG Critic | Give reviewer a "Truth" DB the creator lacks |
| 30 | Standardized Protocols | Standardize messaging to prevent misinterpretation |
| 31 | Red Teaming | Test against known triggers, not just happy path |
