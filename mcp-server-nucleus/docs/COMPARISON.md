# How is Nucleus Different?

> A technical comparison for developers choosing an MCP memory/context solution.

## Feature Matrix

| Feature | Nucleus MCP | ContextStream | mem0 | OpenClaw |
|---------|:-----------:|:-------------:|:----:|:--------:|
| **Architecture** | 100% Local (`.brain/` in Git) | Cloud SaaS | Cloud API | Platform ecosystem |
| **Security Model** | Hypervisor + Default-Deny | Cloud-managed | API keys required | ❌ Sleeper agents, key leaks |
| **Audit Trail** | ✅ Full (`events.jsonl`) | ❌ | ❌ | ❌ |
| **Resource Locking** | ✅ WHO/WHEN/WHY metadata | ❌ | ❌ | ❌ |
| **Cross-IDE Sync** | ✅ Cursor + Claude + Windsurf | ⚠️ Partial | ❌ | ❌ |
| **Install** | `pip install nucleus-mcp` | `npx @contextstream/mcp` | API signup | Platform lock-in |
| **Pricing** | Free (MIT) | Freemium → Paid | Freemium → Paid | Free (with risk) |
| **Data Ownership** | You own everything | Their cloud | Their cloud | Their platform |
| **Git-Native** | ✅ Version-control your memory | ❌ | ❌ | ❌ |
| **Policy Engine** | ✅ Governance rules | ❌ | ❌ | ❌ |

## When to Use What

### Choose **Nucleus** if you:
- Need your agent context to stay **on your machine**
- Want an **audit trail** of every agent action
- Work across **multiple IDEs** (Cursor, Claude Desktop, Windsurf)
- Want memory that lives **in your Git repo**
- Need **governance** over what agents can access

### Choose **ContextStream** if you:
- Want managed cloud sync with zero setup
- Are okay with data living on their servers
- Need team collaboration features (coming for Nucleus in v1.1)

### Choose **mem0** if you:
- Want API-first managed memory
- Don't mind API key dependency
- Need hosted infrastructure

## The Security Question

After the [OpenClaw crisis](https://www.youtube.com/watch?v=ceEUO_i7aW4) (1.5M API keys leaked, sleeper agents in skills, Docker escapes), agent security is no longer optional.

| OpenClaw Vulnerability | Nucleus Defense |
|------------------------|-----------------|
| Sleeper agents in skills | Hypervisor monitors all write attempts |
| API keys in chat logs | Keys never stored in memory or logs |
| Docker escapes | 100% local, no container to escape |
| Blind command execution | Resource locking + audit trail |

## Proof of History

Nucleus isn't a response to hype — it's a battle-tested internal tool:

- **Dec 27, 2025**: [First PyPI release](https://pypi.org/project/mcp-server-nucleus/0.1.0/)
- **Jan 2, 2026**: MCP scaffold launched
- **Feb 2026**: v1.0.2 (Sovereign) — Hypervisor, Engrams, Multi-Agent Sync

---

*MIT Licensed. [GitHub →](https://github.com/eidetic-works/nucleus-mcp)*
