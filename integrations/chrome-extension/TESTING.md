# Manual Test Plan — Eidetic Chrome Extension

These steps assume `eideticd` is running locally and you have the bridge
token available. Run each block top-to-bottom; later steps depend on
earlier ones.

## 0. Pre-flight

```bash
# Start the daemon (separate terminal)
eideticd -bridge :8421

# Verify it's listening
curl -s http://127.0.0.1:8421/healthz \
  -H "Authorization: Bearer $(cat ~/.eidetic/bridge-token)"
# expected: {"status":"ok"} or 200 OK
```

## 1. Load the extension

1. Open `chrome://extensions`.
2. Toggle **Developer mode** on (top-right).
3. Click **Load unpacked**, choose `integrations/chrome-extension/`.
4. **Expected:** the options page auto-opens; the Eidetic icon appears in
   the toolbar (likely behind the puzzle-piece icon — pin it).
5. **Expected badge:** `?` (gray) — no token configured yet.

## 2. Configure settings

1. On the options page, leave **Bridge URL** as `http://127.0.0.1:8421`.
2. Paste your token: `cat ~/.eidetic/bridge-token | pbcopy`.
3. Click **Test connection**.
   - **Pass:** "connected ✓" in green.
   - **Fail (no daemon):** "daemon not reachable or token rejected" in red.
   - **Fail (bad token):** same message — verify the daemon log for a 401.
4. Click **Save**.
   - **Expected:** "saved" in green.
   - **Expected badge:** clears (green dot, no text) within a few seconds.

## 3. Save a page

1. Navigate to any public article (e.g. `https://news.ycombinator.com`).
2. Click the Eidetic toolbar icon.
3. **Expected popup state:** status dot green, label "online".
4. Click **Save this page**.
   - **Expected:** "saved (N chars)" in green where N ≤ 5000.
5. Verify on the daemon side:
   ```bash
   curl -s "http://127.0.0.1:8421/search?q=hacker" \
     -H "Authorization: Bearer $(cat ~/.eidetic/bridge-token)" | head -c 500
   ```

## 4. Save a selection

1. On the same page, select a short paragraph of text.
2. Open the popup → **Save this page**.
3. **Expected:** "saved (N chars)" where N matches the selection length,
   not the full page. The popup meta on the daemon side should show
   `"selection": true`.

## 5. Search

1. In the popup, type a word that exists in the saved page.
2. Press Enter or click **Go**.
3. **Expected:** up to 5 result cards appear below the search input,
   each showing surface, score, timestamp, and a payload snippet.
4. **Fail mode:** "no results" if the daemon returns an empty list.

## 6. Ask

1. Type a question into the **Ask** field, e.g. `what was on this page?`.
2. Press Enter or click **Ask**.
3. **Expected:** an answer card appears (teal left-border) followed by
   up to 3 supporting engram cards.

## 7. Offline behaviour

1. Stop the daemon: `pkill -f 'eideticd -bridge'` (or however you launched).
2. Open the popup.
   - **Expected status dot:** red, label "offline".
   - **Expected badge** (within 5 min, or sooner if you re-open popup): `!`
     in red on the toolbar icon.
3. Try **Save** / **Search** / **Ask**.
   - **Expected:** each shows a red error message; no crash.
4. Restart the daemon and click **Test connection** in options to confirm
   recovery. Reopen the popup — status returns to green.

## 8. Restricted pages

1. Navigate to `chrome://settings`.
2. Open popup → **Save this page**.
3. **Expected:** "save failed: cannot capture this page (restricted URL)".
   The extension does not crash; subsequent saves on regular pages still
   work.

## 9. Wrong token

1. Open options, change the token to gibberish, **Save**.
2. **Expected:** status dot turns red on the popup; **Save** / **Search**
   show "HTTP 401" (or whatever the daemon returns).
3. Restore the correct token to recover.

## 10. Wrong bridge URL

1. Set Bridge URL to `http://127.0.0.1:9999`, **Save**.
2. **Expected:** **Test connection** fails fast (<4s); popup status red.
   No host_permissions error — the manifest declares `http://127.0.0.1:8421/*`
   so other ports may fail the same way until you add them.
   - If you need a different port permanently, edit `manifest.json`
     `host_permissions` and reload the extension.

---

## Known limitations / decisions

- **5 KB page cap.** `document.body.innerText.slice(0, 5000)` — keeps
  request bodies small and avoids saving massive SPA dumps. If a selection
  exists, it's used in full (no slice).
- **No retry on POST.** A failed save just surfaces the error; the user
  can retry. Avoids double-inserts.
- **`http://127.0.0.1:8421/*` is the only host permission.** Users with
  a different port must hand-edit `manifest.json`. This was intentional —
  declaring `http://127.0.0.1/*` would trigger a wider permission warning
  at install time.
- **No content script.** Page capture is done via
  `chrome.scripting.executeScript` from the popup; nothing runs on every
  page. Lower attack surface.
- **No icons asset pipeline.** Generated 16/48/128 placeholder PNGs (dark
  square with a teal circle) — swap with the official mark when ready.
