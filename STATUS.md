# Eidetic Works — Live Status

**Last updated:** 2026-05-20 (Day 10, mid-compression-sprint)
**Current cycle:** Lokesh "finish 80 days of plan in next 2 days" — ~24h elapsed of 36h
**Days to W4 bright-line:** 19 (W4 = 2026-06-08, target 5 paid Pro = $145 MRR)

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
| v0.0.32 | Day 9 | `--restore` flag — download latest R2 backup + `/download` Worker endpoint |
| v0.0.33 | Day 9 | Sync-state persistence — `--stats` shows last cloud backup time across restarts |
| v0.0.34 | Day 9 | `--check` health validator |
| v0.0.35 | Day 10 | sync.json hot-reload via fsnotify (no daemon restart on Pro onboarding) |
| v0.0.36 | Day 10 | `--backups` history (ring buffer of last 10 cloud uploads) |
| v0.0.37 | Day 10 | version-check (24h GitHub poll → /metrics update_available) |
| v0.0.38 | Day 10 | HTTP `/ask` endpoint (nucleus_ask semantics for non-MCP clients) |
| v0.0.39 | Day 10 | shared-team surface (`X-Team-ID` header, dual-write to team prefix) |
| v0.0.41 | Day 10 | Cursor PathContains filter (excludes workspace.json noise) |
| v0.0.42 | Day 10 | HTTP `/export` (NDJSON streaming, paginated, memory-bounded) |
| v0.0.44 | Day 10 | `--uninstall` flag (symmetric to `--install`) |
| v0.0.45 | Day 10 | `/ask` result cache (LRU + 5min TTL, 64-entry cap) |
| v0.0.46 | Day 10 | `--init` first-run wizard + `udsDialer()` helper |
| v0.0.47 | Day 10 | `/timeline` cross-tool + `/digest` weekly recap endpoints |
| v0.0.48 | Day 10 | bash + zsh shell completions, auto-installed by brew |
| v0.0.49 | Day 10 | `/metrics` exposes `/ask` cache hit/miss + size |
| v0.0.50 | Day 10 | `--digest` CLI (local recap, no daemon needed) |
| v0.0.51 | Day 10 | `--ask` CLI (terminal nucleus_ask, no MCP needed) |
| v0.0.52 | Day 10 | `--capture` stdin → engram (universal pipe target) |
| v0.0.53 | Day 10 | refactor: `internal/textsearch` (single source of truth for question→FTS) |
| v0.0.54 | Day 10 | `--vacuum` SQLite compaction for long-running stores |
| v0.0.55 | Day 10 | outbound webhook hooks (~/.eidetic/hooks.json fires on matching engrams) |
| v0.0.56 | Day 10 | regex hook patterns + `GET /hooks` status endpoint |
| v0.0.58 | Day 10 | `--capture` enriches meta with host + cwd + git_branch + user |
| v0.0.59 | Day 10 | `/hooks` endpoint test coverage + eidetic-mcp 0.0.8 nucleus_link tool |

**Current live numbers:** 300K+ engrams (per Mac menubar test), 803+ sessions, P95 retrieval 0.27ms, DB ~3.5 GB

### MCP package

| Version | What |
|---|---|
| eidetic-mcp 0.0.4 | Earlier shipped to PyPI |
| eidetic-mcp 0.0.5 | `nucleus_ask` tool — AI-powered recall via FTS5 |
| eidetic-mcp 0.0.6 | `nucleus_digest` tool — RAG-shaped weekly recap |
| eidetic-mcp 0.0.7 | `nucleus_timeline` tool — cross-tool chronological view |
| eidetic-mcp 0.0.8 | `nucleus_link` tool — temporally-adjacent engrams across surfaces |

### Integrations shipped (11 surfaces in `integrations/`)

| Surface | Status |
|---|---|
| VS Code extension | ✅ TS+esbuild, 11/11 tests, 17.4kB bundle |
| JetBrains plugin (IntelliJ/PyCharm/GoLand/...) | ✅ Kotlin+Gradle v2 |
| Chrome MV3 extension | ✅ 12 files, manifest validated |
| Raycast extension | ✅ TS, 4 commands, build clean |
| Mac SwiftBar plugin | ✅ Live-tested ("🧠 300K") |
| Mac native AppKit menubar | ✅ Swift scaffold (xcodebuild deferred to Lokesh) |
| Slack /eidetic app | ✅ HMAC verified Worker + manifest |
| Discord /eidetic bot | ✅ Ed25519 Web Crypto Worker |
| Telegram /eidetic bot | ✅ Webhook-secret constant-time Worker |
| docs.eidetic.works | ✅ 10-page Astro static site (pending op-assistant deploy) |
| Web dashboard PWA | ✅ Mobile-installable on iPhone/Android |
| WordPress plugin (eidetic-capture.php) | ✅ save_post hook + admin settings; phply-validated |
| Notion sync (Worker + cron poller) | ✅ Polling primary, webhook secondary; KV checkpoint |

### Cloudflare Workers (6 total)

| Worker | Status |
|---|---|
| eidetic-sync | ✅ Live va4e1c516 — Pro sync + Team dual-write |
| gumroad-kit-sync | ✅ Live ve1287839 — 4-tier routing (Pro/Annual/Founder/Team) |
| eidetic-affiliate | ✅ Scaffold ready — /ref/&lt;code&gt; tracking (op-assistant deploy pending) |
| eidetic-analytics | ✅ Scaffold ready — ADR-020-compliant funnel (op-assistant deploy pending) |
| slack-app | ✅ Scaffold (op-assistant deploy pending) |
| discord-bot | ✅ Scaffold (op-assistant deploy pending) |
| telegram-bot | ✅ Scaffold (op-assistant deploy pending) |

### Distribution

| Item | Status |
|---|---|
| `eidetic.works` landing | Live (Cloudflare Pages, auto-deploy) |
| `install.sh` | Live at eidetic.works/install.sh |
| `install.ps1` | Live at eidetic.works/install.ps1 |
| Homebrew tap | Live — `brew tap eidetic-works/nucleus && brew install eideticd` |
| `eidetic-mcp` PyPI | v0.0.4 — `pip install eidetic-mcp` |
| Gumroad → Kit webhook | ✅ Live (gumroad-kit-sync.morning-lake-f944.workers.dev) |
| **eidetic-sync Worker** | ✅ **LIVE** — eidetic-sync.morning-lake-f944.workers.dev/healthz → ok |
| **Gumroad Pro product** | ✅ **LIVE** — eideticworks.gumroad.com/l/eidetic-pro, $29/mo |
| Landing Pro CTA | ✅ Gumroad href live at eidetic.works |
| `gen_pro_key.sh` | ✅ Worker URL + KV namespace ID pre-filled, zero env vars needed |
| Kit announcement email | **PENDING Lokesh keyboard** — template in docs/PRO_LAUNCH.md § 3 |
| ConvertKit waitlist form | Embedded on landing |
| X replies (5 accounts) | Sent by op-assistant: @shushant_l, @RLanceMartin, @iannuttall, @yigitkonur, @PawelHuryn |
| X thread (own post) | **PENDING Lokesh** — docs/posts/x-thread-day8.md |
| HN Show HN | **PENDING Lokesh** — docs/posts/hn-show-hn-day8.md |
| Reddit r/ClaudeAI | **PENDING Lokesh** — docs/posts/reddit-rclaudeai-day8.md |
| dev.to article | ✅ PUBLISHED 2026-05-19 — dev.to/nucleusos/i-got-tired-of-losing-claude-code-context-between-sessions-so-i-built-a-daemon-4ca5 |

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
