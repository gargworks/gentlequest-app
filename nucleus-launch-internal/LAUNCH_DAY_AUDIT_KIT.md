# 🛠️ Launch Day Audit Kit (Strike Monitoring)

Use this guide for real-time verification and monitoring during the Tuesday Strike.

## 🛡️ 1. Registry Heartbeats (The "Mirror" Test)
Ensure all public endpoints are synchronized at **v1.0.5**.

- **Glama**: [Check Listing](https://glama.ai/mcp/servers/@eidetic-works/nucleus-mcp) (Target: v1.0.5)
- **PulseMCP**: [Check Listing](https://www.pulsemcp.com/servers/eidetic-works-nucleus) (Target: Live)
- **PyPI**: `pip install nucleus-mcp` (Target: v1.0.5)

## 🧠 2. Local Diagnostics (The "Health" Test)
Run these commands to verify the local brain state.

```bash
# Check version parity
python3 scripts/sync_registry.py --dry-run

# Run internal health check (Slot 12 Protocol)
python3 -m mcp_server_nucleus.stdio_server --health
```

## 📊 3. Product Hunt Monitoring
- **Main Thread**: [producthunt.com/posts/nucleus-mcp](https://www.producthunt.com/posts/nucleus-mcp)
- **Badge Status**: Visit `nucleusos.dev` and confirm the PH Badge is visible and clickable.

## 🏗️ 4. Show HN Monitoring (Peak hour)
- **Search**: [Hacker News Search 'Nucleus'](https://hn.algolia.com/?q=Nucleus)
- **Survivor Protocol**: If any "security" concerns are raised, refer to the [Show HN Survival Guide](file:///Users/lokeshgarg/ai-mvp-backend/nucleus-launch-internal/SHOW_HN_STRIKE_PLAN.md#L46-51) (The Hypervisor Argument).

---
**Status**: Strike Mode Active. 🛡️🚀
