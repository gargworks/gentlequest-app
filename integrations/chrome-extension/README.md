# Eidetic Daemon — Chrome Extension

A minimal Manifest V3 Chrome extension that talks to a locally-running
`eideticd` over its HTTP bridge.

## What it does

- **Save this page** — captures `document.title`, the URL, and either the
  current text selection or the first 5,000 chars of `document.body.innerText`,
  then POSTs it to `/engrams` with `surface: "chrome"`.
- **Search** — pipes input to `/search?q=...` and shows the top 5 results.
- **Ask** — pipes input to `/ask?question=...` and shows the answer plus the
  top 3 supporting engrams.
- **Status dot** — green when `/healthz` responds, red when it doesn't.
- **Badge** — the toolbar icon shows an `!` badge when the daemon is
  unreachable, `?` when no token is configured.

## Prerequisites

1. `eideticd` running with the bridge listener:
   ```bash
   eideticd -bridge :8421
   ```
2. The per-session token written to `~/.eidetic/bridge-token`.

## Install (load-unpacked, developer mode)

1. Open `chrome://extensions` in Chrome.
2. Enable **Developer mode** (top-right toggle).
3. Click **Load unpacked**.
4. Select `integrations/chrome-extension/` (this directory).
5. The options page opens automatically on first install. Paste:
   - **Bridge URL**: `http://127.0.0.1:8421` (default)
   - **Bearer token**: contents of `~/.eidetic/bridge-token`
6. Click **Test connection** — should turn green.
7. Click **Save**.

## Files

| File              | Purpose                                              |
|-------------------|------------------------------------------------------|
| `manifest.json`   | MV3 manifest                                         |
| `common.js`       | Shared fetch helpers (auth, timeout, endpoints)      |
| `popup.html/.js`  | Toolbar popup UI                                     |
| `options.html/.js`| Settings page (URL + token + test connection)        |
| `background.js`   | Service worker; 5-min `/healthz` poll + badge update |
| `icons/`          | 16/48/128 PNG icons                                  |

## Configuration storage

Settings live in `chrome.storage.local`:
- `bridgeUrl` — e.g. `http://127.0.0.1:8421` (default applied if unset)
- `token` — Bearer token sent on every request

## Auth

Every request includes `Authorization: Bearer <token>`. CORS is handled by
the daemon (`Access-Control-Allow-Origin: *` on the bridge listener), so
no preflight wrangling needed in the extension.
