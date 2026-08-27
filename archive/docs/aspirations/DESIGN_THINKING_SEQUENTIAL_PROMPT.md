# Design Thinking via Sequential Thinking MCP — Enforcing Prompt

**Purpose:** Summon rigorous design thinking using Sequential Thinking MCP. This prompt forces convergence through iterative loops, research injection, and mandatory checkpoints.

**Status:** Production Template  
**Last Updated:** Feb 16, 2026 1:14 AM IST

---

## USAGE INSTRUCTIONS

### Step 1: Choose Your Rigor Level

Select ONE before starting:

```
LEVEL 1 — SPRINT (Fast, shallow)
- 3-5 loops per stage
- 50-100 searches total
- Est. 200-400 turns
- Est. 50k-100k tokens
- Use for: Quick validation, early exploration

LEVEL 2 — STANDARD (Balanced)
- 5-10 loops per stage  
- 100-300 searches total
- Est. 400-800 turns
- Est. 100k-200k tokens
- Use for: Production features, validated concepts

LEVEL 3 — DEEP (Rigorous, thorough)
- 10-20 loops per stage
- 300-600 searches total  
- Est. 800-1500 turns
- Est. 200k-400k tokens
- Use for: Critical decisions, new product launches

LEVEL 4 — EXHAUSTIVE (Research-grade)
- 20-50 loops per stage
- 600-1000+ searches total
- Est. 1500-3000+ turns  
- Est. 400k-800k+ tokens
- Use for: Breakthrough innovation, PhD-level rigor
```

### Step 2: Copy/Paste This Prompt

Replace `[RIGOR_LEVEL]`, `[YOUR_PROBLEM]`, `[YOUR_CONTEXT]` with actual values.

---

## THE PROMPT (Copy from here)

```markdown
You are operating in DESIGN THINKING MODE using Sequential Thinking MCP.

## MANDATORY OPERATING PARAMETERS

**RIGOR LEVEL:** [RIGOR_LEVEL]  
(Choose: SPRINT | STANDARD | DEEP | EXHAUSTIVE)

**PROBLEM STATEMENT:**  
[YOUR_PROBLEM]

**CONTEXT:**  
[YOUR_CONTEXT]  
(Include: workspace path, repo links, relevant docs, existing research)

**CONVERGENCE THRESHOLD:** <1% delta between consecutive loop outputs  
**RESEARCH MANDATE:** Every loop MUST include new search/repo/doc queries  
**EXECUTION GATE:** Show complete plan BEFORE any implementation

---

## DESIGN THINKING FRAMEWORK (IIP-Derived)

You will execute these stages sequentially. Each stage requires convergence before proceeding.

### STAGE 1: Problem Finding & POV Statement
**Loops required:** [3-5 SPRINT | 5-10 STANDARD | 10-20 DEEP | 20-50 EXHAUSTIVE]

**Objectives:**
1. Generate wide set of problem ideas (solo brainstorm)
2. Filter through three categories:
   - Is it real? (search for evidence)
   - Can you observe it? (identify research methods)
   - Is it a good fit? (assess feasibility)
3. Converge on POV statement:
   - Users (Who)
   - Need (What)  
   - Why it matters (Why)

**Per-loop requirements:**
- Run 2-5 search queries (web/repo/docs)
- Identify at least 1 new problem dimension
- Challenge previous loop's assumptions
- Document evidence sources
- Calculate delta from previous loop

**Convergence criteria:**
- POV statement unchanged for 2+ consecutive loops
- Evidence base covers 3+ independent sources
- <1% change in problem framing

**Output format:**
```
## STAGE 1 — Loop [N]/[MAX]

### Searches conducted:
1. [query] → [key findings] [source]
2. [query] → [key findings] [source]
...

### New problem dimensions identified:
- [dimension 1]: [evidence]
- [dimension 2]: [evidence]

### Current POV statement:
**Users:** [who]
**Need:** [what]
**Why it matters:** [why]

### Delta from previous loop: [X]%
### Convergence status: [CONVERGING | NOT CONVERGED | CONVERGED]

### Assumptions challenged:
- [assumption]: [challenge] → [updated view]

### Next loop focus:
[What questions remain? What needs deeper research?]
```

---

### STAGE 2: Research Plan
**Loops required:** [3-5 SPRINT | 5-10 STANDARD | 10-20 DEEP | 20-50 EXHAUSTIVE]

**Objectives:**
1. Design field research plan to maximize variation
2. Identify extreme users (novice, expert, adjacent)
3. Select research methods (interviews, shadowing, POEMS, etc.)
4. Define contexts and environments
5. Plan trust/empathy establishment

**Per-loop requirements:**
- Search for research methodologies
- Find comparable case studies
- Identify potential research participants
- Refine method selection based on evidence
- Calculate delta from previous loop

**Convergence criteria:**
- Research plan stable for 2+ loops
- Methods validated against 3+ academic/industry sources
- User types confirmed through external evidence
- <1% change in research approach

**Output format:**
```
## STAGE 2 — Loop [N]/[MAX]

### Methodology research:
1. [method] → [source] → [applicability]
2. [comparison to similar studies] → [learnings]

### Extreme users identified:
- **Novice:** [who] [why extreme] [evidence]
- **Expert:** [who] [why extreme] [evidence]  
- **Adjacent:** [who] [why extreme] [evidence]

### Methods selected:
- [method 1]: [rationale] [source validation]
- [method 2]: [rationale] [source validation]

### Contexts/environments:
- [context 1]: [access plan] [trust strategy]

### Delta from previous loop: [X]%
### Convergence status: [CONVERGING | NOT CONVERGED | CONVERGED]

### Research plan risks:
- [risk]: [mitigation]

### Next loop focus:
[Gaps in methodology? User access concerns?]
```

---

### STAGE 3: Field Research Synthesis (Persona Development)
**Loops required:** [5-10 SPRINT | 10-20 STANDARD | 20-40 DEEP | 40-100 EXHAUSTIVE]

**Objectives:**
1. Develop 2+ personas per user type
2. Extract isolated insights
3. Document usage scenarios, frustrations, needs
4. Gather supporting evidence/quotations
5. Identify patterns and workarounds

**Per-loop requirements:**
- Search for similar personas in literature
- Find behavioral research supporting observations
- Challenge persona assumptions with data
- Refine persona characteristics
- Calculate delta from previous loop

**Convergence criteria:**
- Personas stable for 3+ loops
- Each persona validated by 3+ external sources
- Patterns confirmed across multiple studies
- <1% change in persona attributes

**Output format:**
```
## STAGE 3 — Loop [N]/[MAX]

### Research conducted:
1. [persona-related search] → [validation/contradiction]
2. [behavioral study] → [supporting evidence]

### Persona [X]: [Name/Type]
**Distinguished characteristics:**
- [trait 1]: [evidence source]
- [trait 2]: [evidence source]

**Usage scenario:**
[Detailed scenario with citations]

**Key tasks:**
1. [task]: [frequency] [importance]

**Key frustrations:**
- [frustration]: [evidence] [workaround observed]

**Key needs:**
- [need]: [why critical] [current gap]

**Supporting evidence:**
> [quotation/data point] [source]

### Isolated insights:
- [insight]: [surprising? expected?] [implications]

### Delta from previous loop: [X]%
### Convergence status: [CONVERGING | NOT CONVERGED | CONVERGED]

### Assumptions challenged:
- [assumption]: [evidence for/against]

### Next loop focus:
[Which persona needs more depth? What's missing?]
```

---

### STAGE 4: Solution Blueprints (SCAMPER)
**Loops required:** [5-10 SPRINT | 10-20 STANDARD | 20-40 DEEP | 40-100 EXHAUSTIVE]

**Objectives:**
1. Generate 3-5 solution concepts
2. Apply SCAMPER framework to each
3. Evaluate against user needs from Stage 3
4. Search for prior art and similar solutions
5. Identify unique value propositions

**SCAMPER framework:**
- **S**ubstitute: What can be replaced?
- **C**ombine: What can be merged?
- **A**dapt: What can be adjusted?
- **M**odify: What can be amplified/minimized?
- **P**ut to other uses: What else could it do?
- **E**liminate: What can be removed?
- **R**everse: What can be flipped?

**Per-loop requirements:**
- Search for existing solutions in space
- Analyze competitor approaches
- Validate technical feasibility
- Test against persona needs
- Calculate delta from previous loop

**Convergence criteria:**
- Solution concepts stable for 3+ loops
- Each solution validated against 3+ user needs
- Prior art fully researched
- <1% change in solution framing

**Output format:**
```
## STAGE 4 — Loop [N]/[MAX]

### Prior art research:
1. [similar solution] → [strengths/weaknesses] → [differentiation]
2. [competitor approach] → [gap analysis]

### Solution [X]: [Name]
**Core concept:**
[Description with evidence of feasibility]

**SCAMPER analysis:**
- **Substitute:** [what] → [why better]
- **Combine:** [elements] → [synergy]
- **Adapt:** [from what] → [how]
- **Modify:** [what changed] → [impact]
- **Put to other uses:** [alternative applications]
- **Eliminate:** [what removed] → [simplification]
- **Reverse:** [what flipped] → [innovation]

**Persona fit:**
- [Persona 1]: [addresses needs X, Y] [friction points]
- [Persona 2]: [addresses needs Z] [adoption barriers]

**Unique value proposition:**
[What makes this different from existing solutions?] [evidence]

### Delta from previous loop: [X]%
### Convergence status: [CONVERGING | NOT CONVERGED | CONVERGED]

### Solution risks:
- [risk]: [evidence] [mitigation ideas]

### Next loop focus:
[Which solution needs more validation? Technical feasibility concerns?]
```

---

### STAGE 5: Experimentation Plan (Hypothesis Testing)
**Loops required:** [5-10 SPRINT | 10-20 STANDARD | 20-40 DEEP | 40-100 EXHAUSTIVE]

**Objectives:**
1. Define testable hypotheses for each solution
2. Design experiments with clear success metrics
3. Identify riskiest assumptions
4. Plan MVE (Minimum Viable Experiment)
5. Estimate resources and timeline

**Per-loop requirements:**
- Search for experimental methodologies
- Find case studies of similar tests
- Validate metric selection
- Refine hypothesis framing
- Calculate delta from previous loop

**Convergence criteria:**
- Hypotheses stable for 3+ loops
- Experiments validated against research best practices
- Metrics confirmed as measurable and relevant
- <1% change in experimental design

**Output format:**
```
## STAGE 5 — Loop [N]/[MAX]

### Methodology research:
1. [experimental approach] → [validity] → [source]
2. [similar test case] → [learnings applicable to us]

### Hypothesis [X]:
**Statement:** If [action], then [outcome], because [theory]

**Riskiest assumptions:**
1. [assumption]: [why risky] [how to test]
2. [assumption]: [evidence for/against]

**Experiment design:**
- **Method:** [what we'll do]
- **Sample:** [who/what/how many] [how recruited]
- **Duration:** [timeframe] [rationale]
- **Success metrics:**
  - Primary: [metric] [target] [measurement method]
  - Secondary: [metric] [target] [measurement method]

**Resources required:**
- [resource]: [quantity] [estimated cost]

**Risks:**
- [risk]: [probability] [impact] [mitigation]

### Delta from previous loop: [X]%
### Convergence status: [CONVERGING | NOT CONVERGED | CONVERGED]

### Experiment validity concerns:
- [concern]: [how addressed]

### Next loop focus:
[What assumptions need more evidence? Metric concerns?]
```

---

### STAGE 6: Business Model Canvas
**Loops required:** [3-5 SPRINT | 5-10 STANDARD | 10-20 DEEP | 20-50 EXHAUSTIVE]

**Objectives:**
1. Define value proposition
2. Identify customer segments
3. Map channels and relationships
4. Outline revenue streams
5. Detail key resources, activities, partnerships
6. Estimate cost structure

**Per-loop requirements:**
- Search for comparable business models
- Validate pricing assumptions
- Research distribution channels
- Analyze cost structures
- Calculate delta from previous loop

**Convergence criteria:**
- Canvas stable for 2+ loops
- Each element validated with market data
- Financial assumptions backed by evidence
- <1% change in business model

**Output format:**
```
## STAGE 6 — Loop [N]/[MAX]

### Market research:
1. [pricing analysis] → [implications for our model]
2. [competitor business model] → [learnings]

### Business Model Canvas:

**Value Proposition:**
[What unique value] [validated by Stage 4 research]

**Customer Segments:**
- [segment 1]: [size] [willingness to pay] [evidence]
- [segment 2]: [size] [willingness to pay] [evidence]

**Channels:**
- [channel]: [reach] [cost] [evidence of effectiveness]

**Customer Relationships:**
- [relationship type]: [why appropriate] [examples from similar products]

**Revenue Streams:**
- [stream]: [pricing] [volume estimate] [confidence level]

**Key Resources:**
- [resource]: [criticality] [acquisition plan]

**Key Activities:**
- [activity]: [frequency] [cost driver]

**Key Partnerships:**
- [partner]: [value exchange] [risk if unavailable]

**Cost Structure:**
- [cost category]: [amount] [fixed/variable] [source]

### Unit economics:
- CAC: [amount] [calculation]
- LTV: [amount] [assumptions]
- LTV/CAC: [ratio] [benchmark comparison]

### Delta from previous loop: [X]%
### Convergence status: [CONVERGING | NOT CONVERGED | CONVERGED]

### Model risks:
- [risk]: [impact on viability] [mitigation]

### Next loop focus:
[Financial assumptions need validation? Partnership concerns?]
```

---

### STAGE 7: MVE Planning (Minimum Viable Experiment)
**Loops required:** [3-5 SPRINT | 5-10 STANDARD | 10-20 DEEP | 20-50 EXHAUSTIVE]

**Objectives:**
1. Define absolute minimum to test core hypothesis
2. Identify critical path
3. Estimate realistic timeline and budget
4. Plan risk mitigation
5. Define kill criteria

**Per-loop requirements:**
- Search for MVE case studies
- Validate scope decisions
- Refine timeline estimates
- Challenge "minimum" assumptions
- Calculate delta from previous loop

**Convergence criteria:**
- MVE scope stable for 2+ loops
- Timeline validated against similar projects
- Budget confirmed with multiple estimates
- <1% change in plan

**Output format:**
```
## STAGE 7 — Loop [N]/[MAX]

### MVE research:
1. [similar MVE case] → [timeline] → [learnings]
2. [scope creep patterns] → [how to avoid]

### MVE Scope:
**Core hypothesis being tested:**
[Specific, measurable statement]

**In scope:**
- [feature/element]: [why essential] [evidence]

**Out of scope:**
- [feature/element]: [why not essential] [when to revisit]

**Success criteria:**
- [criterion]: [target] [measurement]

**Kill criteria:**
- [criterion]: [threshold] [decision process]

### Critical path:
1. [milestone]: [duration] [dependencies] [risk]
2. [milestone]: [duration] [dependencies] [risk]

### Resource plan:
- **Team:** [roles] [hours] [cost]
- **Tech:** [tools] [licenses] [cost]
- **Marketing:** [channels] [budget]
- **Contingency:** [%] [for what risks]

**Total budget:** [amount] [confidence interval]
**Total timeline:** [duration] [confidence interval]

### Delta from previous loop: [X]%
### Convergence status: [CONVERGING | NOT CONVERGED | CONVERGED]

### Plan risks:
- [risk]: [probability] [impact] [response]

### Next loop focus:
[Timeline concerns? Budget validation needed?]
```

---

### STAGE 8: Reflection & Synthesis
**Loops required:** [2-3 SPRINT | 3-5 STANDARD | 5-10 DEEP | 10-20 EXHAUSTIVE]

**Objectives:**
1. Synthesize learnings across all stages
2. Identify gaps or contradictions
3. Document key assumptions and risks
4. Produce executive summary
5. Define next steps

**Per-loop requirements:**
- Review all previous stages for consistency
- Search for contradictory evidence
- Challenge final synthesis
- Identify blind spots
- Calculate delta from previous loop

**Convergence criteria:**
- Synthesis stable for 2+ loops
- All contradictions resolved or documented
- Executive summary unchanged
- <1% change in recommendations

**Output format:**
```
## STAGE 8 — Loop [N]/[MAX]

### Cross-stage validation:
1. [stage X vs stage Y]: [consistency check] → [resolution]
2. [assumption from stage X]: [validated in stage Y?] → [action]

### Key learnings:
1. [learning]: [confidence level] [supporting evidence across stages]
2. [learning]: [confidence level] [supporting evidence across stages]

### Contradictions identified:
- [contradiction]: [stages involved] → [resolution or flag for investigation]

### Assumptions register:
- [assumption]: [validated? | risky? | needs testing?]

### Executive summary:
**Problem:** [one sentence from Stage 1]
**Users:** [from Stage 3]
**Solution:** [from Stage 4]
**Business model:** [from Stage 6]
**Next step:** [from Stage 7]
**Key risk:** [from Stage 5]

**Recommendation:** [GO | NO-GO | PIVOT] [rationale]

### Delta from previous loop: [X]%
### Convergence status: [CONVERGING | NOT CONVERGED | CONVERGED]

### Final blind spots:
- [potential gap]: [how to address]

### Next loop focus:
[If not converged: what needs more depth?]
```

---

## ENFORCEMENT MECHANISMS

### ANTI-SLACK PROTOCOLS

**You MUST follow these rules. No exceptions. No shortcuts.**

1. **MANDATORY SEARCH REQUIREMENT**
   - EVERY loop requires 2+ new searches (web/repo/docs)
   - Searches must be DIFFERENT from previous loops
   - If you use the same search, I will reject the loop
   - Document EVERY search query and key findings
   - Cite sources with URLs/file paths

2. **MANDATORY DELTA CALCULATION**
   - Calculate % change from previous loop
   - Show calculation method
   - If delta >1%, you have NOT converged
   - You cannot proceed to next stage until delta <1% for 2+ consecutive loops

3. **MANDATORY ASSUMPTION CHALLENGE**
   - Every loop must challenge at least 1 assumption from previous loop
   - Document: [assumption] → [challenge] → [updated view]
   - If you cannot challenge an assumption, explain why it's now validated

4. **MANDATORY EVIDENCE LINKING**
   - Every claim requires citation
   - Format: [claim] [source URL/path]
   - If you make a claim without evidence, I will reject the loop

5. **MANDATORY CONVERGENCE CHECK**
   - At end of EVERY loop, state: CONVERGING | NOT CONVERGED | CONVERGED
   - Provide evidence for your assessment
   - If CONVERGED, you must still run 1 more validation loop

6. **ANTI-AMNESIA PROTOCOL**
   - Every loop must reference findings from previous loops
   - Format: "Building on Loop X where we found [Y]..."
   - If you ignore previous loops, I will reject current loop

7. **MANDATORY PLAN-FIRST RULE**
   - Before ANY implementation/execution, show complete plan
   - Plan must include: stages, loop counts, search strategy, timeline
   - Wait for approval before proceeding

### COMPLIANCE CHECKPOINTS

**After every 5 loops, you MUST:**

1. Summarize progress across all loops so far
2. Calculate overall delta from Loop 1 to current loop
3. Identify if you're on track for convergence
4. Flag any deviation from rigor level requirements
5. Request explicit "CONTINUE" approval before proceeding

**If you violate ANY enforcement mechanism:**
- I will issue: "PROTOCOL VIOLATION: [specific rule broken]"
- You must restart that loop from scratch
- You must explain why violation occurred
- You must add safeguard to prevent repeat

---

## EXECUTION SEQUENCE

**STEP 1: Generate the plan**

Before ANY loops, output:

```
# DESIGN THINKING EXECUTION PLAN

**Rigor level:** [SPRINT | STANDARD | DEEP | EXHAUSTIVE]
**Problem:** [one sentence]
**Context:** [summary]

## Stage breakdown:

### Stage 1: Problem Finding & POV
- Planned loops: [N]
- Searches per loop: [N]
- Estimated turns: [N]
- Convergence criteria: [specific]

### Stage 2: Research Plan
- Planned loops: [N]
- Searches per loop: [N]
- Estimated turns: [N]
- Convergence criteria: [specific]

[... repeat for all 8 stages ...]

## Total estimated:
- Loops: [N]
- Searches: [N]
- Turns: [N]
- Tokens: [N]

## Search strategy:
- Web: [what types of queries]
- Repo: [what files/code to examine]
- Docs: [what documentation to reference]

## Risk mitigation:
- If convergence not reached by loop [N]: [action]
- If contradictory evidence found: [protocol]
- If external blocker encountered: [escalation]

**Awaiting approval to proceed.**
```

**STEP 2: Execute stages sequentially**

- Start with Stage 1, Loop 1
- Follow output format exactly
- Run all required searches
- Calculate delta
- Check convergence
- Only proceed to next loop when approved
- Only proceed to next stage when converged

**STEP 3: Checkpoint every 5 loops**

- Pause execution
- Provide compliance report
- Wait for "CONTINUE" approval

**STEP 4: Final synthesis**

- After Stage 8 converges, provide:
  - Complete findings document
  - Evidence register (all sources used)
  - Assumption register (all assumptions made)
  - Recommendation with confidence level

---

## FINAL REMINDERS

**I don't care if this takes 1000 turns.**  
**I don't care if this takes 500k tokens.**  
**I don't care if you think you already know the answer.**

**You WILL:**
- Run every single loop
- Conduct every single search
- Calculate every single delta
- Challenge every single assumption
- Cite every single source
- Converge to <1% difference

**You WILL NOT:**
- Skip loops
- Reuse searches
- Assume without evidence
- Proceed without convergence
- Ignore previous findings
- Slack off
- Develop amnesia

**This is design thinking done RIGHT.**  
**This is how you build products that matter.**  
**This is how you avoid wasting 6 months building the wrong thing.**

**Now, generate the plan and await my approval.**
```

---

## END OF PROMPT (stop copying here)

---

## USAGE EXAMPLES

### Example 1: GentleQuest Feature Validation

```markdown
**RIGOR LEVEL:** STANDARD

**PROBLEM STATEMENT:**  
GentleQuest users report feeling overwhelmed by tracking multiple habits simultaneously. We need to understand if simplified tracking or gamification is the right solution.

**CONTEXT:**  
- Workspace: /Users/lokeshgarg/gentlequest
- User feedback: [link to feedback doc]
- Current analytics: 60% drop-off after day 3
- Competitor analysis: [link]
```

### Example 2: Nucleus OS Market Positioning

```markdown
**RIGOR LEVEL:** DEEP

**PROBLEM STATEMENT:**  
Nucleus OS needs clear differentiation from AutoGPT, LangChain, and competitor frameworks. We're unsure whether to position as developer tool, enterprise platform, or consumer OS.

**CONTEXT:**  
- Workspace: /Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus
- Existing docs: /Users/lokeshgarg/ai-mvp-backend/docs/architecture/
- Competitive landscape: [links to competitors]
- Current messaging: [Product Hunt draft]
```

### Example 3: New Product Concept

```markdown
**RIGOR LEVEL:** EXHAUSTIVE

**PROBLEM STATEMENT:**  
Developers spend 40% of time context-switching between tools (IDE, terminal, docs, Slack, etc.). Is there a unified workspace opportunity?

**CONTEXT:**  
- Initial research: [link to preliminary study]
- Target users: Full-stack engineers at startups
- Hypothesis: AI-powered context aggregation could save 10+ hours/week
```

---

## ADVANCED CUSTOMIZATION

### Custom Stage Addition

Insert between existing stages as needed:

```markdown
### STAGE X: [Custom Stage Name]
**Loops required:** [based on rigor level]

**Objectives:**
1. [Objective 1]
2. [Objective 2]

**Per-loop requirements:**
- [Requirement 1]
- Calculate delta from previous loop

**Convergence criteria:**
- [Criterion 1]
- <1% change in [metric]

**Output format:**
[Define your format following the same pattern as other stages]
```

### Custom Research Method

Add to Stage 3 persona development:

```markdown
**Method: [Custom Method Name]**
- **Users:** [who]
- **Context:** [where/when]
- **Data collected:** [what]
- **Analysis approach:** [how]
- **Validation:** [against what sources]
```

### Custom Convergence Threshold

Adjust if needed (though <1% is recommended):

```markdown
**CONVERGENCE THRESHOLD:** <[X]% delta between consecutive loops

**Rationale for adjustment:**
[Why you need different threshold]
[What risks this introduces]
[How you'll compensate]
```

---

## TROUBLESHOOTING

### Issue: LLM skips searches

**Response:**
```
PROTOCOL VIOLATION: MANDATORY SEARCH REQUIREMENT

Loop [N] did not include required 2+ new searches.

RESTART Loop [N] with:
- Minimum 2 new search queries
- Document query + key findings + source URLs
- Explain why these searches are critical for this loop
```

### Issue: LLM claims convergence too early

**Response:**
```
CONVERGENCE CLAIM REJECTED

You claimed convergence at Loop [N], but:
- Delta = [X]% (threshold is <1%)
- Only [N] consecutive converged loops (need 2+)
- [Specific element] still changing

CONTINUE with Loop [N+1]
```

### Issue: LLM forgets previous findings

**Response:**
```
PROTOCOL VIOLATION: ANTI-AMNESIA PROTOCOL

Loop [N] did not reference findings from previous loops.

RESTART Loop [N] with:
- Explicit references: "Building on Loop X..."
- Integration of at least 2 previous findings
- Explanation of how current loop builds on previous work
```

### Issue: LLM wants to skip stage

**Response:**
```
STAGE SKIP DENIED

You cannot skip Stage [X] because:
- Rigor level requires [N] loops per stage
- Convergence not yet achieved
- Critical assumptions not yet validated

CONTINUE with Stage [X], Loop [N]
```

---

## SUCCESS METRICS

You'll know this worked when:

✅ **Convergence achieved**: <1% delta for 2+ loops per stage  
✅ **Evidence-based**: Every claim has citation  
✅ **Thorough**: All rigor-level loop requirements met  
✅ **Consistent**: No contradictions across stages  
✅ **Actionable**: Clear recommendation with confidence level  
✅ **Auditable**: Complete evidence trail from problem → solution  

---

**Last Updated:** Feb 16, 2026 1:14 AM IST  
**Status:** Production Ready  
**Validated:** Not yet (awaiting first use)

**Usage:** Copy the prompt section, fill in your values, paste into chat with Sequential Thinking MCP enabled.
