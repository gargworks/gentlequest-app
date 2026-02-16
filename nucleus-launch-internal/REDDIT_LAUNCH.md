# Reddit Launch Strategy (v2 — Sovereign Positioning)

## Target Subreddits (Priority Order)

1. **r/LocalLLaMA** - Primary (highest engagement for AI tools)
2. **r/ClaudeAI** - Secondary (Claude users)
3. **r/cursor** - Secondary (Cursor users)
4. **r/selfhosted** - Tertiary (local-first audience)

---

## Post: r/LocalLLaMA

### Title
`The OpenClaw 1.5M key leak was the trigger I needed to open-source my internal agent security layer`

### Body

```markdown
Watched this video on the OpenClaw crisis: https://www.youtube.com/watch?v=ceEUO_i7aW4

TLDR: 1.5M keys leaked, sleeper agents in skills, Docker escapes. It's a mess.

I've been building Nucleus for months as my internal "Agent Control Plane" for production work. It's been my private brain for managing engrams (persistent knowledge), hypervisor locks, and audit logs. When the OpenClaw leaks hit, I realized the most useful thing I could do was wrap this battle-tested security logic into an MCP server so people can keep their keys safe in Cursor/Claude.

**What's already shipped (not a roadmap):**
- 🔒 **Hypervisor** — Locks files/folders with WHO/WHEN/WHY metadata
- 📋 **Audit Trail** — Every single agent action logged to events.jsonl
- 🧠 **Local Engrams** — Persistent knowledge stored locally, never touches the cloud
- 🔄 **Cross-Platform** — One brain syncs Cursor, Claude Desktop, and Windsurf
- 🏛️ **Governance** — Policy engine for agent access control

**How it handles the OpenClaw attack vectors:**

| OpenClaw Vulnerability | Nucleus Defense |
|------------------------|-----------------|
| Sleeper agents in skills | Hypervisor monitors all file-system write attempts |
| API keys in chat logs | Keys never stored in memory or logs |
| Docker escapes | 100% local, no container to escape |
| Blind command execution | Resource locking + manual audit trail |

**How it compares to alternatives:**

| | Nucleus | ContextStream | mem0 |
|---|---------|---------------|------|
| Data | 100% local (Git-native) | Cloud SaaS | Cloud API |
| Security | Hypervisor + audit logs | Cloud-managed | API keys required |
| Governance | ✅ Policy engine | ❌ | ❌ |
| Pricing | Free (MIT) | Freemium → Paid | Freemium → Paid |

**Quick Setup:**
```bash
pip install nucleus-mcp
nucleus-init --scan
```

GitHub: https://github.com/eidetic-works/nucleus-mcp
Detailed comparison: https://github.com/eidetic-works/mcp-server-nucleus/blob/main/docs/COMPARISON.md

MIT licensed. It's early for the public, but it's been my daily driver for production for months (first PyPI release: Dec 27, 2025). If you're looking at sandboxing for agents, check out the hypervisor code — genuinely curious about your take on the resource locking approach.
```

---

## Post: r/ClaudeAI

### Title
`Sharing my internal local-first memory layer for Claude Desktop (Hypervisor + Audit Trail)`

### Body

```markdown
I've been building Nucleus for months as the internal "Agent Control Plane" for my other project (GentleQuest). It's been my private tool for handling engrams (persistent knowledge), hypervisor resource locking, and audit logs inside Cursor and Claude Desktop.

After the recent 1.5M API key leaks in the MCP ecosystem, I realized the security logic I built for myself — resource locking with who/when/why metadata — might be useful for others too.

**What it does:**
✅ Persistent Engrams — Knowledge that survives across Claude sessions
✅ Hypervisor — Agents can't modify protected files without audit trails
✅ Full Audit Log — Every single action logged locally (events.jsonl)
✅ 100% Local — Everything stays on your machine. No cloud, no API keys
✅ Cross-platform — Syncs your brain across Claude/Cursor/Windsurf
✅ Governance — Policy engine controls what agents can access

**vs. ContextStream:** They require cloud sync. Nucleus keeps everything Git-native and local.
**vs. CLAUDE.md:** CLAUDE.md is a static text file. Nucleus is a dynamic knowledge base with audit logs and cross-tool sync.

**Proof of history:**
Not just jumping on the MCP hype — first PyPI release Dec 27, 2025: https://pypi.org/project/mcp-server-nucleus/0.1.0/

```bash
pip install nucleus-mcp
nucleus-init
```

MIT licensed. AMA.
```

---

## Post: r/cursor

### Title
`Built an MCP server that syncs Cursor with Claude Desktop — shared agent memory with governance [Open Source]`

### Body

```markdown
**Problem**: I use Cursor for coding and Claude Desktop for reasoning. They don't share context, and there's no audit trail of what agents do.

**Solution**: Nucleus MCP — one brain across all your AI tools, with governance built in.

**Setup**:
```bash
pip install nucleus-mcp
nucleus-init  # Auto-configures Cursor + Claude Desktop
```

**What it enables**:
- Architecture decision in Claude → Cursor knows about it
- Every agent action logged (events.jsonl audit trail)
- Hypervisor locks protect critical files from accidental agent edits
- Git-native: your `.brain/` folder lives in your repo

**How it's different**:
- ContextStream = cloud sync (your data on their servers)
- Nucleus = 100% local, Git-native, with governance + audit logs

**Open source**: https://github.com/eidetic-works/nucleus-mcp

Looking for Cursor users to test! What context do you wish persisted between sessions?
```

---

## Post: r/selfhosted

### Title
`Open-sourced my local-first agent control plane with Hypervisor security — no cloud, no API keys, 100% your machine`

### Body

```markdown
After the OpenClaw 1.5M key leak, I'm sharing the security layer I built for my own AI workflow.

**Nucleus MCP** is a local-first agent control plane:
- 🔒 Everything stored in `.brain/` — a plain folder in your Git repo
- 📋 Full audit trail (events.jsonl) of every agent action
- 🛡️ Hypervisor locks files with WHO/WHEN/WHY metadata
- 🏛️ Governance policy engine
- 🚫 Zero cloud dependencies, zero API keys, zero telemetry

Works with Cursor, Claude Desktop, Windsurf, and any MCP-compatible tool.

```bash
pip install nucleus-mcp
nucleus-init --scan
```

MIT licensed. GitHub: https://github.com/eidetic-works/nucleus-mcp

Built for devs who want AI assistance without sending their codebase to the cloud.
```

---

## Engagement Strategy

### First Hour
- Reply to EVERY comment within 30 minutes
- Thank people for feedback
- Answer technical questions thoroughly
- Note feature requests ("great idea, added to roadmap!")

### Common Questions

**Q: How is this different from CLAUDE.md?**
> CLAUDE.md is static text. Nucleus is a dynamic knowledge base with persistent engrams, audit logs, governance, and cross-platform sync.

**Q: Does this work with [tool]?**
> If it supports MCP protocol, yes! Currently tested with Claude Desktop, Cursor, and Windsurf.

**Q: Why should I trust this?**
> 100% local — your data stays in `.brain/`. MIT licensed, audit the code. No telemetry. Full audit trail you can inspect.

**Q: What about ContextStream?**
> ContextStream requires cloud sync — your data lives on their servers. Nucleus is 100% local, Git-native, with governance and audit logs that ContextStream doesn't offer.

**Q: What about OpenClaw?**
> Different problems. OpenClaw trades security for capability. Nucleus gives you both — with Hypervisor controls and audit trails.

---

## Timing

**Best time**: Tuesday-Thursday, 9-11am PST

**Sequence**:
1. r/LocalLLaMA first (largest audience, security angle)
2. Wait 2-3 hours, gauge reception
3. r/ClaudeAI and r/cursor simultaneously
4. r/selfhosted 2 hours later (local-first angle)

---

## Success Metrics

- 100+ upvotes on r/LocalLLaMA
- 50+ GitHub stars in first 24 hours
- 10+ meaningful comments/questions
- 3+ contributors interested
