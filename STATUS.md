# Eidetic Works — Live Status

**Last updated:** 2026-05-19 (Day 9)
**Current week:** W2 (Day 8-14)
**Current focus:** Distribution push — 5 X DMs, HN Show HN, Reddit r/ClaudeAI, dev.to post
**Days to next bright-line:** 20 (W4 / 2026-06-08)

---

## What has shipped (Day 0 → Day 9)

### Daemon (`eidetic-works/eidetic-daemon`)

| Version | Shipped | What |
|---|---|---|
| v0.0.1 | Day 3 | Initial scaffold (store, API, tests) |
| v0.0.2 | Day 3 | fsnotify capture (Claude Code, Cursor) |
| v0.0.3-v0.0.5 | Day 4-5 | MCP bridge skeleton, FTS5, edge cases |
| v0.0.6-v0.0.8 | Day 5-6 | `/search`, `/recent`, batch endpoints |
| v0.0.9 | Day 6 | Bearer auth (EIDETIC_AUTH=1), /healthz exempt |
| v0.0.10-v0.0.12 | Day 6-7 | Latency tracker, /metrics P50/P95/P99 |
| v0.0.13-v0.0.18 | Day 7 | Chunk splitter ADR-018, FTS5 snippet, batch-insert |
| v0.0.19-v0.0.23 | Day 7-8 | Cross-compile verify, smoke-test CI gate |
| v0.0.24 | Day 8 | Cloudflare R2 sync (opt-in via sync.json) |
| v0.0.25 | Day 8 | Compliance daemon (`eideticd-compliance`) |
| v0.0.26 | Day 8 | `--stats` flag |
| v0.0.27 | Day 8 | Windows support (TCP mode, install.ps1, eidetic-mcp 0.0.2) |
| v0.0.28 | Day 8 | linux-arm64, FTS5 snippet in MCP, eidetic-mcp 0.0.4 |
| v0.0.29 | Day 9 | `-install` flag (launchd/systemd one-command setup) |
| v0.0.30 | Day 9 | Windows capture paths (`%APPDATA%\Claude\projects`, `%APPDATA%\Cursor`) |
| v0.0.31 | Day 9 | Bridge dual-listener (`-bridge <addr>` TCP alongside UDS, CORS, auth) |

**Current live numbers:** 278,561 engrams, 803 sessions, P95 retrieval 2.09ms, DB 3.3 GB

### Distribution

| Item | Status |
|---|---|
| `eidetic.works` landing | Live (Cloudflare Pages, auto-deploy) |
| `install.sh` | Live at eidetic.works/install.sh |
| `install.ps1` | Live at eidetic.works/install.ps1 |
| Homebrew tap | Live — `brew tap eidetic-works/nucleus && brew install eideticd` |
| `eidetic-mcp` PyPI | v0.0.4 — `pip install eidetic-mcp` |
| Gumroad → Kit webhook | Live (CF Worker) |
| ConvertKit waitlist form | Embedded on landing |
| X DMs (5 targets) | **PENDING Lokesh keyboard** (day8-dm-targets.md) |
| X thread | Drafted, updated to 278K — **PENDING Lokesh post** |
| HN Show HN | Drafted — **PENDING Lokesh post** |
| Reddit r/ClaudeAI | Drafted — **PENDING Lokesh post** |
| dev.to article | Drafted — **PENDING Lokesh post** |

### Sovereign (cc_voice lane)

| Item | Status |
|---|---|
| Gate 4 | Complete — iPhone → Cloudflare → Mac XTTS → WAV → playback |
| TestFlight | Build 1.0(2), invite-only, bundle com.eideticworks.sovereign |
| Cloudflare tunnel | `sovereign.eidetic.works` → localhost:8420 (XTTS) |
| Gate 5 candidates | Streaming XTTS, wake-word, QR onboarding — needs Lokesh pick |

---

## W2 focus (this week)

**Operator-ready now:**
1. Send 5 X DMs (`docs/outreach/day8-dm-targets.md`) from @eidetic_works
2. Post X thread (`docs/posts/x-thread-day8.md`) from @eidetic_works
3. Post HN Show HN (`docs/posts/hn-show-hn-day8.md`)
4. Post Reddit r/ClaudeAI (`docs/posts/reddit-rclaudeai-day8.md`)
5. Pick Gate 5 target for Sovereign mobile

**cc-main working on:**
- CI fix (t.Context() → context.Background(), Go 1.23 compat) — pushed, running
- CORS tests (4 new tests for v0.0.31 bridge feature)
- Architecture doc (docs/SOVEREIGN_BRIDGE_ARCHITECTURE.md)
- Real metrics on landing (278K/803 sessions)

---

## W4 bright-line (2026-06-08)

**Gate:** 5 paid Pro Track A subscribers OR explicit Lokesh hold on the pivot.

**What needs to happen by W4:**
- At least 1 user interview scheduled from DM/HN/Reddit outreach
- Pro tier MVP decision (what does Pro include over free?)
- Gumroad Pro product page live (even if $0 for now)

---

## Peer notes (cc-peer daily review)

_cc-peer: fill in during your daily 3-line review pass_

---

## Open risks

| Risk | Mitigation |
|---|---|
| CI was failing on t.Context() (Go 1.24 API on 1.23 CI) | Fixed — pushed 2026-05-19 |
| Port 8420 conflict (eideticd squatted XTTS port) | Fixed — plist reverted |
| landing metrics were stale (141K → 278K) | Fixed — deployed |
| DM/post copy had stale metrics | Fixed — updated in repo |
| Sovereign tunnel hostname TBD | Resolved — sovereign.eidetic.works |
