# Nucleus vs. The Alternatives

Choosing a persistence layer for your AI agents is a critical decision. Here is how Nucleus compares to current alternatives like **ContextStream** and **mem0**.

## At a Glance

| Feature | Nucleus MCP | ContextStream | mem0 |
|---------|-------------|---------------|------|
| **Deployment** | 100% Local | SaaS (Cloud) | SaaS / Self-Host |
| **Identity** | Anonymous (Rotating) | Account-based | Account-based |
| **Architecture** | Git-Native (`.brain/`) | Cloud Database | Cloud Database |
| **Governance** | Hypervisor / File Locks | None / ACLs | None |
| **Audit Logs**| Core Feature | Enterprise Only | Basic |
| **License** | MIT | Proprietary | Apache 2.0 |
| **API Keys** | None Required | Required | Required |

---

## Why Nucleus?

### 🛡️ Governance-First
Most memory servers focus only on "remembering". Nucleus focuses on **Control**. 
The built-in **Hypervisor Layer** ensures that your agent doesn't just have context, but it also has boundaries. You can lock critical infrastructure files or entire directories, and Nucleus will enforce those limits at the MCP protocol level.

### 🧠 Engrams over Memories
We use the term **Engrams** because these aren't just strings in a database. They are version-controlled units of knowledge. 
Because Nucleus stores its state in your project's `.brain/` directory, your agent's context is:
- **Git-Native:** Diffs, branches, and merges work on your memory.
- **Offline-First:** No round-trips to a cloud server.
- **Portable:** Your repo contains everything the agent needs to continue work on any machine.

### 🔒 Privacy by Design
Nucleus doesn't want your data. There is no cloud sync (unless you explicitly configure a private relay), no tracking, and no persistent identity. 
- **Rotating Pulse IDs:** Your telemetry identity self-destructs every 30 days.
- **Local Hashing:** We proxy machine identity through your project path, not your hardware.

---

## When to use others?

- **ContextStream:** If you want a managed SaaS experience and don't mind sending your code context to a third party for the sake of zero-setup sync across teams.
- **mem0:** If you need a more traditional "Memory-as-a-Service" with high-level Python APIs and managed hosting.
