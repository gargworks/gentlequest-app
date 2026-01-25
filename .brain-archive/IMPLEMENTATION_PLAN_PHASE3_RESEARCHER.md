
# Implementation Plan: Deep Research Agent (Phase 3)

## Goal
Activate a **Deep Research Agent** capable of performing real web searches and synthesizing information.
This replaces the "Simulation" placeholder in `WebOps` with real capabilities.

## User Review Required
> [!IMPORTANT]
> This requires installing new python packages: `duckduckgo-search` and `beautifulsoup4`.
> I have added them to `pyproject.toml`. You may need to run `pip install -e .` or `pip install duckduckgo-search beautifulsoup4` to activate them in your environment.

## Proposed Changes

### `mcp-server-nucleus`

#### [MODIFY] `src/mcp_server_nucleus/runtime/capabilities/web_ops.py`
- Import `duckduckgo_search`.
- Replace `[WebOps] Simulation...` with real `DDGS().text(query)` calls.
- Improve `web_read_page` with `BeautifulSoup` for better text extraction.

#### [NEW] `.brain/agents/researcher.md`
- **Identity**: Deep Research Specialist.
- **Protocol**:
  1. **Plan**: Break down the question.
  2. **Search**: Use `web_search` to find sources.
  3. **Read**: Use `web_read_page` to extract details.
  4. **Synthesize**: Combine findings into a coherent answer.
  5. **Cite**: Always provide URLs.

## Verification Plan

### Automated Verification
- **Test Script**: `tests/test_researcher.py`.
- **Logic**:
  1. Instantiate `WebOps`.
  2. Call `web_search(query="latest python version")`.
  3. Assert results contain "Python".

### Manual Verification
- **Spawn Agent**: `nucleus spawn "Research the latest features of Next.js 15"`
- **Expectation**: Agent searches, reads 2-3 pages, and produces a summary with citations.
