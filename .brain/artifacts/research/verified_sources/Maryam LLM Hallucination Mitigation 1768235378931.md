LLMs hallucinate. 
AI agents compound hallucinations across reasoning, tools, and memory.
I Analyzed 𝟮𝟱+ ArXiv Papers to Extract These 𝟯𝟭 Mitigation Strategies ⬇️

𝟭. Chain-of-Verification (CoVe): generate answer → create verification questions → revise (28% improvement).
𝟮. Parent-Child topology: One agent drafts, a second specifically critiques.
𝟯. Blind Critics: Reviewers shouldn't see reasoning, only the output.
𝟰. Debate: Two agents arguing a point beats one thinking twice.
𝟱. Personas: A "Skeptical Reviewer" detects 20% more errors.
𝟲. Cross-Model: Use small models to draft, SOTA models (GPT-4o) to verify.
𝟳. Watchdogs: Non-LLM scripts (regex/code) must validate outputs.
𝟴. Fractal Sampling: Query 3x—high variance equals hallucination.
𝟵. HalMit: Define "generalization bounds" to flag unknown data.
𝟭𝟬. Structure: Enforce JSON. Parse failure is a hallucination.
𝟭𝟭. ReAct: Thought-Action loops prevent blind guessing.
𝟭𝟮. Pre-Check: Validate API args against schema before sending.
𝟭𝟯. Reflexion: Store past errors in memory to prevent repeats.
𝟭𝟰. Editor Pattern: Dedicated agent removes unverified claims.
𝟭𝟱. No Source, No Output: Require URLs/IDs for every claim.
𝟭𝟲. Specialization: SQL + Python agents beat one "Generalist."
𝟭𝟳. Human-in-loop: Force approval for high-stakes (POST/DELETE) actions.
𝟭𝟴. Negative Constraints: Explicitly prompt what not to do.
𝟭𝟵. Scoring: Reviewer rates 1-10; discard anything <8.
𝟮𝟬. Voting: Run 3 instances; take the majority answer.
𝟮𝟭. Grounding: "Observe" state immediately before "Acting."
𝟮𝟮. Fuzzy Logic: Validate text where exact string matches fail.
𝟮𝟯. Sanity Checks: Hard-code bounds (e.g., max refund limits).
𝟮𝟰. Clean Context: Summarize often; long history breeds errors.
𝟮𝟱. Isolation: Critic sends feedback, Creator fixes it (don't mix).
𝟮𝟲. Sensitivity: If a comma changes the decision, it's hallucinating.
𝟮𝟳. Fact-Checker: Give agents a Google tool specifically to self-verify.
𝟮𝟴. Kill Switch: Stop process after 3 failed retries to prevent spiraling.
𝟮𝟵. RAG Critic: Give the reviewer a "Truth" DB the creator lacks.
𝟯𝟬. Protocols: Standardize messaging to prevent misinterpretation.
𝟯𝟭. Red Teaming: Test against known triggers, not happy path.
