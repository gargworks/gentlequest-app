---
description: The Sovereign Growth Protocol (Switch to Growth Mode)
---

# /growth: The Sovereign Growth Protocol

**Status:** 🚀 GROWTH_MODE_ACTIVE
**Context Switch:** 🛠️ Dev Mode ➡️ 🏗️ Builder/Growth Mode

This is the definitive "All-Encompassing" protocol for triggering the **Sovereign Growth Engine**. It enforces **Linear Execution Discipline**: while planning is multi-dimensional, execution is strictly sequential and calendar-mapped.

> [!IMPORTANT]
> **Growth Mode Discipline:**
> - **Execution is Linear:** Only one public "strike" per calendar slot.
> - **Account Health (MDR_016):**
>   - **GREEN**: Normal operations.
>   - **YELLOW**: Posts are being HELD/FILTERED. Action: Pause for 24h, run Modmail appeal.
>   - **RED**: Shadowbanned. Action: NO new threads. Switch to "Lurker Mode" (Comments only, no links) for 48h-72h.
> - **Tribal Conflict Check (MDR_018):** Identify "Hostile Overlap." If a community has flagged our content, do not post related content to sister-subreddits for 72h.
> - **Link Discipline:** Delay links in new threads. Post raw text first, wait 5-10 mins, then add UNIQUE links in comments or edits.
> - **Tone:** Technical, transparent, and vulnerable.
> - **Identity (MDR_019):** TOTAL-SAFE (The Nucleus Team). Real names and parent brands are FORBIDDEN in public copy.
- **Casual & DM Engagement (MDR_021):**
  - **Tone:** Builder-casual. strictly lowercase.
  - **Brevity:** Max 3 lines for technical answers.
  - **Directness:** Answer the specific question in the first sentence. No mechanical filler.
  - **Golden Examples:**
    - *"it's basically a central json-based aggregator on your local disk. instead of tool state being session-only, everything goes into a shared engram vault (using sqlite for the local memory store)..."*
    - *"finally got the mcp communication stable and submitted to the registry. doing the official launch on product hunt today..."*

---

## 🛡️ 0. Step 0: The Sovereign Perimeter Audit
// turbo
Before calling any growth sub-tools, you MUST run this audit:
1.  **Anonymity Scrub (MDR_019):** `grep` the draft for the user's real name (Lokesh Garg) and personal paths (e.g., `/Users/lokeshgarg`). If found, REJECT and REWRITE to "We" or "The Nucleus Team".
2.  **Version Lock (MDR_020):** Check `nucleus-launch-internal/VERSION_BUMP_MAP.md`. Verify the draft mentions the CORRECT current version (v1.0.x).
3.  **Account Warmth Check:** Verify account status in `nucleus-launch-internal/LAUNCH_NARRATIVE_HISTORY.md#shadowban-recovery-log`. If RED, switch to Lurker Mode.
4.  **AI-Tell Audit:** Search draft for apostrophes `'`, em-dashes `—`, double-hyphens `--`, or explicit version numbers (e.g. `v1.0.7`) if posting to casual channels. If found, REJECT and return to drafting.

---

## 🏗️ 1. Step 1: Narrative Audit & Continuity
// turbo
Before launching any action, you MUST verify the current "Public Lore" and explicit user directives to prevent amnesia/retcons:
1.  **Read** `nucleus-launch-internal/LAUNCH_NARRATIVE_HISTORY.md`.
2.  **Persistence Audit:** Never delete existing slots. Re-prioritize or append only.
3.  **Media Vitality & Uniqueness:** 
    - Verify target demo link (Loom/YouTube) is LIVE.
    - **Never reuse the exact same URL** across subreddits. Use unlisted timestamps or different Loom chapters to create unique tactical links.
4.  **Content Randomization:** Mandate different titles and lead paragraphs for every channel strike to prevent pattern-matching by anti-spam gangs.
5.  **Relevance & Evolution Audit (MDR_015):** Verify the draft against the current `README.md` and `CHANGELOG.md`.
4.  **Verify Active Orbit:** Where are we live? (Twitter, HN, GitHub).
5.  **Identify Social Proof:** Check for a "hot" thread or high-signal comment to cross-pollinate.
6.  **Audit previous claims:** Ensure new drafts don't contradict existing architecture lore.

---

## 📡 2. Step 2: Multi-Channel Command

### 🐦 Twitter [/twitter]
- **Focus:** Forensic Deep-Dives and "Receipts."
- **Action:** Post code logs, terminal captures, and Loom videos.
- **Reference:** `nucleus-launch-internal/TWITTER_LAUNCH_PHASE_2.md`

### 📰 Hacker News [/hn]
- **Focus:** Systems Engineering Critique.
- **Action:** Ask technical architectural questions (e.g., Policy Engine vs. WASM).
- **Tone:** Peer-level engineering.
- **Reference:** `nucleus-launch-internal/HACKER_NEWS_PHASE_2.md`

### 🧱 Reddit [/reddit]
- **Focus:** The "Micro-Truth" and Pain Points.
- **Protocol:** Run `/reddit-polish` to lowercase and humanize all drafts.
- **Brand Guard:** Ensure narrative follows "The Safety Pivot" (We created a tool that terrified us).
- **Target:** r/ClaudeAI (Context Amnesia), r/selfhosted (Privacy).
- **Reference:** `nucleus-launch-internal/REDDIT_LAUNCH_PHASE_2.md`

### 🌐 Ecosystem Expansion [/registry]
- **Focus:** Canonical Discoverability.
- **Action:** Submit to MCPMarket, OpenTools, and Registry Monitor.
- **Reference:** `nucleus-launch-internal/REGISTRY_CONTENT.md`

### 💬 DMs & Comments (Casual)
- **Focus:** Technical Support & High-Intent Outreach.
- **Protocol:** Enforce **MDR_021**.
- **Action:** Reply directly to the engineering pain point. No marketing fluff.
- **Context:** Anthropic Discord, r/ClaudeAI comments, X replies.

---

## 🔄 3. Step 3: The Cross-Channel Synergy
**Continuity Rule:** Every growth action must reference the success or failure of the last.
- *Bridge Example:* "Just got tore apart on HN for our hypervisor logic (link); trying to see if users here prefer a simpler sandbox..."

---

## 📝 4. Step 4: Ledger Maintenance & Recovery
After ANY engagement:
1.  **Update Lore:** Log the live link/sentiment in `LAUNCH_NARRATIVE_HISTORY.md`.
2.  **Success Gradient Check (MDR_017):** 
    - If the strike achieved zero engagement/was filtered: Mandate a **Strategic Pivot** (Refactor message, change time, or switch platform) for the NEXT slot.
    - Do not execute the next slot with the same logic that failed the last.
3.  **Verify Status:** Check if the post is live in Incognito. If filtered, STOP and update Account Health to YELLOW/RED.
4.  **Sync Progress:** Update `task.md`.

---

**Ready to engage?** 🚀🛸
Run this protocol by performing the Narrative Audit first.
