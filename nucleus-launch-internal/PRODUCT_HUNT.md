# Product Hunt Launch (v2 — Sovereign Positioning)

## Listing Details

### Name
```
Nucleus MCP
```

### Tagline (60 chars max)
```
Local-first agent control plane with governance & audit trail
```

### Description
```
The Sovereign Agent Control Plane

After the OpenClaw security crisis (1.5M API keys leaked), agent security is no longer optional.

Nucleus MCP creates a secure, audited .brain/ folder that all your AI tools can access:

• Tell Claude about a decision → Cursor knows it
• Every agent action logged (full audit trail)
• Hypervisor prevents unauthorized file modifications
• One brain. All your tools. Zero cloud dependency.

What's shipped (not a roadmap):
✅ Hypervisor — File locking with WHO/WHEN/WHY metadata
✅ Audit Trail — Every action logged to events.jsonl
✅ Persistent Engrams — Knowledge that survives sessions
✅ Governance — Policy engine for agent access control
✅ Cross-platform — Cursor, Claude Desktop, Windsurf
✅ 100% local — Git-native, no API keys, no cloud
✅ MIT licensed — no lock-in

How it compares:
• vs. ContextStream: They require cloud sync. Nucleus is 100% local with governance.
• vs. mem0: They require API keys. Nucleus is file-first, no signup.
• vs. OpenClaw: They trade security for capability. Nucleus gives you both.

Quick start:
pip install nucleus-mcp
nucleus-init

Detailed comparison: https://github.com/eidetic-works/mcp-server-nucleus/blob/main/docs/COMPARISON.md
```

### Topics
- Developer Tools
- Artificial Intelligence
- Open Source
- Cybersecurity
- Productivity

### First Comment (Maker's Comment)
```
Hey Product Hunt! 👋

I'm the solo dev behind Nucleus MCP. I built this because the MCP ecosystem has a massive security gap — and the OpenClaw crisis (1.5M API keys leaked, sleeper agents in skills) proved it.

Nucleus started as my internal tool for managing AI agent memory securely. First published to PyPI on Dec 27, 2025 (https://pypi.org/project/mcp-server-nucleus/0.1.0/). After months of dogfooding it in production, I'm open-sourcing the full security layer.

What makes it different from cloud alternatives like ContextStream:
- 100% local: Your .brain/ folder lives in your Git repo
- Audit trail: Every agent action is logged
- Hypervisor: Files are locked with WHO/WHEN/WHY metadata
- Governance: Policy engine controls what agents can access
- No API keys, no signup, no telemetry

Technical bits:
- Built on Anthropic's Model Context Protocol (MCP)
- Python 3.10+, MIT licensed
- Auto-configures Claude Desktop, Cursor, and Windsurf

What I'd love to hear:
- How do you currently manage context across AI tools?
- What security features would make you trust agent tools more?
- Feature requests!

GitHub: https://github.com/eidetic-works/nucleus-mcp

Happy to answer any questions! 🧠
```

---

## Media Assets Needed

### Logo
- 240x240 px
- Brain icon with nucleus symbol
- Clean, modern, dark background

### Gallery Images (1270x760 px)
1. **Hero**: Diagram showing Cursor ↔ Nucleus ↔ Claude ↔ Windsurf (with Hypervisor shield)
2. **Security**: OpenClaw vulnerability table vs Nucleus defense
3. **Terminal**: Screenshot of `nucleus-init` output
4. **Comparison**: Feature matrix vs ContextStream/mem0

### Video (optional)
- Upload the demo video showing governance in action
- Or create a 30-second GIF version

---

## Launch Strategy

### Best Day
**Tuesday** - Historically best for developer tools on PH

### Time
**12:01 AM PST** - Product Hunt resets at midnight PST

### Launch Day
1. Post at 12:01 AM PST
2. Share on Twitter immediately (use the Thread from TWITTER_LAUNCH.md)
3. Post to Reddit communities (staggered, per REDDIT_LAUNCH.md)
4. Monitor and respond to ALL comments

---

## Potential Questions & Answers

**Q: How is this different from just using a shared file?**
> Nucleus adds governance: audit trail (events.jsonl), Hypervisor locking with WHO/WHEN/WHY metadata, policy engine, and auto-configuration for popular tools.

**Q: Does this work with ChatGPT?**
> Not yet — ChatGPT doesn't support MCP. But if OpenAI adds MCP support, Nucleus will work automatically.

**Q: Is my data sent anywhere?**
> Never. 100% local. No telemetry. Full audit trail you can inspect yourself.

**Q: What about ContextStream?**
> ContextStream requires cloud sync — your data lives on their servers. Nucleus is 100% local, Git-native, with governance and audit logs they don't offer.

**Q: What about team collaboration?**
> Currently single-user focused. Team sync (with encryption) is on the roadmap for v1.1. For now, you can git-commit your .brain/ folder.

---

## Success Metrics

- Top 5 of the day
- 200+ upvotes
- 50+ comments
- 100+ GitHub stars from PH traffic
- Featured in "Developer Tools" collection

---

## Post-Launch

- Thank everyone in comments
- Update GitHub README with "Featured on Product Hunt" badge
- Write a "lessons learned" post for the community
