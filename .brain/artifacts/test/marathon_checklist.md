# 3-Hour Marathon Checklist
> **Created:** December 28, 2025, 9:55 AM  
> **Status:** Ready when you return

---

## Hour 1: Cold Start Test & Validation

- [ ] Run cold start test in DOGFOOD thread (5 tests)
- [ ] Verify all 5 pass
- [ ] Switch MCP config back to warm brain
- [ ] Run warm test to confirm
- [ ] Log results in dogfood_log.md

---

## Hour 2: GentleQuest Development

- [ ] Review current sprint focus
- [ ] Pick top priority task from state.json
- [ ] Use SYNTH thread for coordination
- [ ] Complete one feature or fix
- [ ] Test on production

---

## Hour 3: Nucleus Documentation

- [ ] Update README with FastMCP fix notes
- [ ] Prepare v0.2.4 changelog
- [ ] Review MCP submission status (PulseMCP, mcp.so)
- [ ] Plan launch video content

---

## Quick Commands

**Switch to cold brain:**
```bash
# In mcp_config.json
"NUCLEAR_BRAIN_PATH": "/Users/lokeshgarg/dogfood-brain/.brain"
```

**Switch to warm brain:**
```bash
# In mcp_config.json  
"NUCLEAR_BRAIN_PATH": "/Users/lokeshgarg/ai-mvp-backend/.brain"
```

**Kill MCP servers before switch:**
```bash
pkill -f mcp_server_nucleus
```

---

*Return to TECH-DIRECTOR thread to continue*
