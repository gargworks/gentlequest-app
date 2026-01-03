# Brain Architecture & Installation Guide

> **Purpose:** Comprehensive documentation of how `.brain/` works across projects and all MCP installation approaches.
> **Created:** December 27, 2025

---

## Part 1: Brain Architecture — Single vs Per-Project

### The Core Question

> "Should users have one global brain or a brain per project?"

### Industry Best Practice (from MCP ecosystem research)

| Approach | When to Use | Example |
|----------|-------------|---------|
| **Per-Project Brain** | Team projects, version-controlled | `.brain/` in repo root |
| **Global Brain** | Personal workflows, cross-project | `~/.nucleus-brain/` |

### Our Current Design: Per-Project

```
my-project/
├── .brain/                    ← Brain lives inside project
│   ├── ledger/
│   │   ├── state.json        ← Project-specific state
│   │   ├── triggers.json
│   │   └── events.jsonl
│   ├── artifacts/
│   ├── agents/
│   └── memory/
├── src/
├── package.json
└── README.md
```

**Why Per-Project?**
1. **Version Control:** `.brain/` can be committed to Git
2. **Team Sharing:** Everyone on the project uses same brain
3. **Isolation:** Project A's state doesn't affect Project B
4. **Portability:** Clone repo = get brain included

### Alternative: Global Brain

```
~/.nucleus-brain/             ← Single brain for all projects
├── ledger/
├── artifacts/
└── ...
```

**When Global Makes Sense:**
- Solo founder working on multiple projects
- Personal productivity (not project-specific)
- Cross-project orchestration

### Hybrid Approach (Future)

```
~/.nucleus-brain/              ← Global "master brain"
├── global-state.json         ← Cross-project state
└── projects/
    ├── project-a/            ← Per-project overlay
    └── project-b/
```

---

## Part 2: MCP Server Configuration Models

### Model A: Per-Project Config (Recommended for Teams)

Claude/Cursor can read project-specific configs:

```
my-project/
├── .vscode/mcp.json          ← VSCode/Cursor reads this
├── .cursor/mcp.json          ← Cursor-specific
└── .brain/
```

**Pros:**
- Shareable via version control
- Project-specific tools
- Isolation between projects

**Cons:**
- Need to configure per project
- Can't access cross-project brain

### Model B: Global Config (Current Default)

Single config applies to all projects:

```bash
~/Library/Application Support/Claude/claude_desktop_config.json
~/.cursor/mcp.json
~/.codeium/windsurf/mcp_config.json
```

**Pros:**
- One-time setup
- Works everywhere
- Simpler for solo users

**Cons:**
- Can't share with team
- Same brain across all projects

---

## Part 3: All Installation Approaches Compared

### Full Comparison Matrix

| # | Approach | What It Does | Touch User Files? | Safety | Effort | Best For |
|---|----------|--------------|-------------------|--------|--------|----------|
| 1 | **pip install** | Downloads Python package | No | ✅ Safe | Low | Getting the code |
| 2 | **nucleus init** | Creates `.brain/` folder | Creates new files | ✅ Safe | Low | Bootstrapping brain |
| 3 | **Snippet Generator** | Prints JSON to copy-paste | No | ✅ Safe | Medium | Manual config |
| 4 | **Auto-Installer** | Writes to config files | Yes (DANGER) | ⚠️ Risky | Low | Power users only |
| 5 | **Web Installer** | Website generates config file | Downloads file | ✅ Safe | Medium | Non-technical users |
| 6 | **npx one-liner** | Runs without install | No | ✅ Safe | Very Low | Quick testing |
| 7 | **Docker** | Pre-configured container | No | ✅ Safe | Medium | Consistent environments |
| 8 | **VS Code extension** | Installs via marketplace | Uses extension API | ✅ Safe | Very Low | IDE users |

---

### Detailed Breakdown

#### 1. pip install
```bash
pip install mcp-server-nucleus
```
- **What happens:** Downloads package to `site-packages/`
- **User action:** None
- **Result:** Code is on machine, not yet configured

#### 2. nucleus init
```bash
nucleus init my-project/.brain
```
- **What happens:** Creates folder structure + sample files
- **User action:** Provide path
- **Result:** Ready-to-use brain folder

#### 3. Snippet Generator (Our Current Approach)
```bash
nucleus init
# Outputs:
"nucleus-brain": {
    "command": "python3",
    "args": ["-m", "mcp_server_nucleus"],
    "env": { "NUCLEAR_BRAIN_PATH": "/path/to/brain" }
}
```
- **What happens:** Prints config snippet
- **User action:** Copy-paste into their config file
- **Result:** User in control, educational, safe

#### 4. Auto-Installer (NOT RECOMMENDED YET)
```bash
nucleus-setup
# Automatically edits:
# - claude_desktop_config.json
# - ~/.cursor/mcp.json
# - ~/.codeium/windsurf/mcp_config.json
```
- **What happens:** Directly writes to config files
- **Risk:** JSONC parsing, corruption, permission errors
- **Status:** DEFERRED until safer implementation

#### 5. Web Installer (Future Option)
- User visits: `https://nucleus-mcp.com/install`
- Enters brain path
- Downloads pre-filled config file
- Drags to correct location

#### 6. npx One-Liner (For npm-based MCPs)
```bash
npx mcp-server-nucleus
```
- **What happens:** Downloads and runs without permanent install
- **Limitation:** Doesn't persist brain state well
- **Use case:** Quick demos

#### 7. Docker (For Isolation)
```bash
docker run -v ~/.brain:/brain ghcr.io/nucleus/mcp-server
```
- **What happens:** Runs in container with mounted brain
- **Pros:** Consistent, isolated, portable
- **Use case:** CI/CD, team environments

---

## Part 4: Recommendations

### For Solo Founders (Our Primary ICP)

1. **Use Global Config** — One brain for everything
2. **Store at:** `~/.brain/` or in primary project
3. **Configure once** — Use snippet generator

### For Teams

1. **Use Per-Project Config** — `.brain/` in each repo
2. **Commit to Git** — Share state and patterns
3. **Each dev configures** — Using snippet generator

### For Enterprise (Future)

1. **Central brain server** — Network MCP (not local stdio)
2. **Auth via OAuth** — Secure access
3. **Per-team brains** — Isolated namespaces

---

## Part 5: Roadmap

| Phase | Feature | Priority | Status |
|-------|---------|----------|--------|
| **Now** | Snippet Generator | ✅ High | ✅ Implemented |
| **v0.3** | Per-project `.brain/` support | 🟡 Medium | Planned |
| **v0.4** | Web installer (optional) | 🟢 Low | Backlog |
| **v1.0** | Auto-installer (safe version) | 🟡 Medium | Research |
| **Future** | Docker image | 🟢 Low | Backlog |

---

## Part 6: Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-12-27 | Snippet Generator over Auto-Installer | Risk of corrupting user configs outweighs convenience |
| 2025-12-27 | Per-Project as default | Aligns with VSCode/Cursor best practices |
| 2025-12-27 | Defer Web Installer | Focus on CLI users first (our ICP) |
