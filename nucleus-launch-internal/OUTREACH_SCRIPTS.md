# Vanguard Pioneer Outreach Scripts (Sovereign & Human v1.1.0)

These scripts have been audited to remove personal names and "AI tells" (over-polishing, formulaic gratitude, and corporate jargon).

---

## 1. To Arya (Contributor)
**Target**: @aryasadawrate19  
**Risk Level**: Low (Personal context)  
**AI-Tell Fixes**: Removed "Founder" title, "personally thank you," and formulaic "shaping the roadmap."

**Subject**: thanks for the linux xdg fix / nucleus mcp

Hi Arya,

Just sending a quick note to say thanks for that XDG contribution you made to nucleus-init. It actually helped get the linux build stable on my end.

I'm starting a small discord for the few devs using this to help figure out where to take the "engram" persistence stuff next. No marketing, just a place to debug and share setups. Would be cool to have you in there if you're interested.

Link: https://discord.gg/RJuBNNJ5MT

Cheers,
The Nucleus Team

---

## 2. To GitHub Stargazers
**Targets**: Early supporters  
**Risk Level**: Medium (Cold outreach)  
**AI-Tell Fixes**: Removed "In the sea of AI hype," "Claim your role," and structured bullet points.

**Subject**: saw you starred nucleus-mcp

Hey,

I'm one of the devs behind Nucleus MCP. Saw you starred the repo recently—thanks for that.

We're trying to figure out the best way to sync shared memory between Cursor and Claude without it being a mess. If you're actually using it and have feedback (or if it just broke for you), I'd love to hear it.

We've got a small group for the first few users to share how they're using it: https://discord.gg/RJuBNNJ5MT

Thanks again.

Best,
The Nucleus Team

---

## 3. General Response (For Reddit/HN)
**Context**: Defending against "AI Spam" accusations.
**AI-Tell Fixes**: Short sentences, zero emojis, technical focus.

**Draft**:
"This isn't a wrapper or hype-chase. I built this because I was tired of Claude forgetting my project architecture every time I started a new thread. It's a local-first ledger for 'engrams'. Everything stays on your machine, no cloud, and it's been in development since December. Happy to answer any technical questions about the hypervisor logic or how it locks .env files."

---

## 4. Directory: Identified Vanguard Contacts
Use the following emails with the `outreach_cli.py` tool.

| GitHub | Name | Email | Note |
|--------|------|-------|------|
| @aryasadawrate19 | Arya | `aarya.sadawrate@gmail.com` | **ALREADY SENT** |
| @tkersey | Tim Kersey | `tk@functional.cafe` | High-intent stargazer |
| @farazfarid | Faraz Farid | `wrasse-decibel.04@icloud.com` | Pinned AI projects |
| @FiloSvR | Filippo Vimini | `filippo.vimini@ericsson.com` | Researcher / Ericsson |

---

## 🛠️ Outreach CLI Tool (Safe & Handy)
The script at `scripts/outreach_cli.py` uses the `RESEND_API_KEY` from your `.env` file. Do **not** commit the `.env` file.

### Usage:
1. **Send to a Stargazer (with name)**:
   ```bash
   export RESEND_API_KEY=your_key_here  # Or ensure it's in .env
   python3 scripts/outreach_cli.py --to user@example.com --type stargazer --name "Tim"
   ```

2. **Send to a Contributor (Arya template)**:
   ```bash
   python3 scripts/outreach_cli.py --to user@example.com --type arya
   ```

---

---

## 5. The Netscape Event (Aggregator Launch)
**Target**: Technical Influencers / Reddit r/ClaudeAI / Agents in Production
**Risk Level**: High (Broad visibility)
**Vibe**: Recursive Power

**Draft**:
"Most people are treating MCP servers as simple tool-wrappers. We think that’s limiting. 

We just released Nucleus v0.5—the 'Netscape moment' for the agentic web. Instead of manually connecting 20 different servers to your IDE, Nucleus lets you **mount** them recursively. One connection gives your agent a namespaced, governed entry point to your entire tool mesh. 

It turns linear growth into recursive power. Local-first, open-source, and ready for you to break it: https://github.com/eidetic-works/nucleus-mcp"

---

## 📋 AI-Tell Risk Audit: What was removed
| Feature | Risk | Why it was removed |
|---------|------|---------------------|
| **"Founder" Title** | High | Sounds like a startup pitch / "founder mode" buzzword. |
| **"Delighted/Excited"** | High | Classic LLM indicators of forced enthusiasm. |
| **Numbered Lists** | Medium | Can feel like a generated summary template. |
| **Emoji use (🧠, 🔒)** | Medium | Often signals an AI trying to be "engaging." |
| **"Universal Brain"** | High | Marketing jargon that triggers skepticism in technical groups. |
| **Perfect Punctuation** | Low | Slightly loosening the grammar makes it feel more "human-written." |
