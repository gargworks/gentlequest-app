# Deferred iOS Automation Tooling — install on next Wi-Fi window

Captured 2026-05-09 during GentleQuest dogfood walk. Both items below would have made AI-driven iOS automation 100–500× cheaper in tokens and 10× faster wall-clock vs the current pixel-coord approach. Blocked today by Xcode version + mobile data budget.

## 1. idb_companion — Meta's iOS Development Bridge

**Why:** Sends taps/text/swipes directly to Simulator runtime via XCTest. Bypasses macOS Spaces entirely (cross-Space taps work). Returns iOS accessibility tree (~10 tokens) instead of screenshots (~5 K tokens). Stable element-by-label targeting instead of pixel coords that break on layout shifts.

**Install:**
```bash
brew tap facebook/fb
brew install idb-companion
pip3 install fb-idb
```

**Blocker today:** `idb-companion` formula requires Xcode 26.3; current Xcode is 16.4. Updating Xcode = ~10 GB download. Defer to Wi-Fi.

**Verify after install:**
```bash
idb_companion --version
idb list-targets   # should show booted iPhone Sim
idb ui describe-all   # should return JSON accessibility tree
```

## 2. joshuayoes/ios-simulator-mcp — MCP server

**Why:** Wraps idb + simctl as typed MCP tools. Claude calls `mcp__ios_simulator__tap_element({label: "Mood"})` instead of bash invocations. Discoverable via `ToolSearch`. Zero context-window burn for typical tap-by-label flows. Depends on idb_companion being present.

**Install:**
```bash
npm install -g @joshuayoes/ios-simulator-mcp
```

Then add to `~/.claude/.mcp.json` (or whichever Claude Code MCP config Lokesh uses):
```json
{
  "mcpServers": {
    "ios-simulator": {
      "command": "ios-simulator-mcp",
      "env": {}
    }
  }
}
```

Restart Claude Code session; verify tools appear:
```
ToolSearch query: "ios-simulator"
```

**Blocker today:** depends on idb_companion (#1) which needs Xcode 26.

## What we're losing today by not having these

- Pixel-coord clicks via computer-use MCP: ~5 K tokens/screen × ~30 taps = ~150 K vision tokens for one dogfood walk
- Each tap: ~3 s wall-clock (screenshot → analyze → coord → click)
- Layout-fragile: sim's Update App? prompt or notification banner shifts everything down by ~50 px, all pre-computed coords break
- macOS Spaces friction (Sim must be visible on active Space for clicks)

**With idb + MCP installed:**
- ~10 tokens per `describe_ui` + ~50 tokens per `tap_element({label})` = ~2 K tokens for full walk
- ~300 ms per tap
- Survives layout shifts (label-targeted)
- Cross-Space (sim can stay parked anywhere)

**ROI estimate:** ~5–10 min one-time install (after Xcode update lands) → 100×+ token savings on every future iOS dogfood / QA / sub-agent automation pass. Pays back instantly for any further Flutter widget rebuild iteration.

## Trigger for re-activation

When ANY of these is true:
- About to do another dogfood pass (R2 of GentleQuest, or any other Flutter app)
- About to start Flutter widget rebuild work (Tier 1–13 from REVIEW.md)
- Starting Round 6+ of design iteration
- On Wi-Fi for any reason and have 30 min idle

Steps in order:
1. Update Xcode to 26.x via App Store (~10 GB)
2. Run install commands above
3. Verify both work
4. Update DOGFOOD_LOG.md / REVIEW.md to note the new tooling is live
5. Re-do whatever current automation flow at ~100× lower cost

## References

- [Accessibility Automation | idb](https://fbidb.io/docs/accessibility/)
- [idb GitHub repo](https://github.com/facebook/idb)
- [joshuayoes/ios-simulator-mcp](https://github.com/joshuayoes/ios-simulator-mcp)
- [Tristan Manchester's iOS Simulator skill](https://github.com/openclaw/skills/blob/main/skills/tristanmanchester/ios-simulator/SKILL.md) (skill, not MCP — alternative wrapping)
- [Conor Luddy's ios-simulator-skill](https://github.com/conorluddy/ios-simulator-skill) (build-side wrapper, also useful when starting Flutter rebuilds)
