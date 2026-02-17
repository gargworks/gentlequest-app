# Hacker News Launch (v2 — Sovereign Positioning)

## Show HN Submission

### Title (80 chars max)
```
Show HN: Nucleus MCP – Local-first agent control plane with governance
```

### URL
```
https://github.com/eidetic-works/nucleus-mcp
```

### Text (if self-post, leave blank for link post)

For a Show HN, leave this blank and let the GitHub README speak for itself.

---

## First Comment (Post immediately after submission)

```
Hi HN! Built this because the MCP ecosystem has a security gap (see the OpenClaw crisis: 1.5M API keys leaked, sleeper agents in skills).

Nucleus is an internal tool I've been dogfooding since Dec 2025 (first PyPI release: https://pypi.org/project/mcp-server-nucleus/0.1.0/). It's a local-first agent control plane with:

- Hypervisor: Locks files/folders with WHO/WHEN/WHY metadata
- Audit trail: Every agent action logged to events.jsonl
- Engrams: Persistent knowledge stored locally, Git-native
- Governance: Policy engine for agent access control
- Cross-IDE: One brain syncs Cursor, Claude Desktop, Windsurf

**Demo (3m Sovereign Trilogy):** https://youtu.be/D1B6m_F-h80

Technical details:
- Built on Anthropic's Model Context Protocol (MCP)
- 100% local — no network calls, no API keys, no telemetry
- Python 3.10+, MIT licensed
- Git-native: .brain/ folder lives in your repo

The real competitor is ContextStream, not OpenClaw. ContextStream requires cloud sync; Nucleus keeps everything local with governance + audit logs they don't offer.

Comparison: https://github.com/eidetic-works/nucleus-mcp/blob/main/docs/COMPARISON.md

Looking for feedback on the Hypervisor architecture — is resource locking with intent metadata the right abstraction for agent sandboxing?
```

---

## Best Posting Time

**Best**: Tuesday-Thursday, 8-10am EST (5-7am PST)

HN is US East Coast dominated, so early EST morning catches the morning crowd.

---

## HN Guidelines

1. **Don't ask for upvotes** — against the rules
2. **Be authentic** — HN hates marketing speak
3. **Respond to every comment** — especially critical ones
4. **Be technical** — HN appreciates implementation details
5. **Acknowledge limitations** — honesty wins trust

---

## Potential Criticisms & Responses

**"Why not just use a shared file?"**
> You could! Nucleus adds structure (engrams, events.jsonl), audit logging, hypervisor locking with WHO/WHEN/WHY metadata, governance policies, and auto-configuration. It's opinionated conventions over configuration.

**"MCP is just Anthropic lock-in"**
> MCP is an open protocol. Cursor, Windsurf, and others support it independently. We're betting on it becoming a standard, but Nucleus's .brain/ folder is just JSON files — zero lock-in.

**"What about security?"**
> Everything is local. No network calls. The Hypervisor monitors file-system write attempts. Full audit trail in events.jsonl. No telemetry (that ships in v1.1 with an open Sovereign Metrics approach, default-allow with transparent handshake).

**"This seems over-engineered"**
> Fair criticism. The core engram/audit system is simple. The Hypervisor adds complexity but solves a real problem: preventing agents from silently modifying critical files.

**"How is this different from ContextStream?"**
> Architecture: ContextStream is cloud SaaS. Nucleus is 100% local, Git-native. Key differences: Nucleus has audit logs, policy engine, and resource locking — none of which are in ContextStream's feature set.

---

## Success Metrics

- 50+ points
- Front page for 2+ hours
- 20+ comments with genuine engagement
- 10+ GitHub stars from HN traffic
