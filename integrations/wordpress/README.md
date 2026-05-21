# Eidetic Capture — WordPress Plugin

A single-file WordPress plugin that captures published posts (and optionally
pages + custom post types) as engrams in your locally-running `eideticd`.

```
WP post save  ──save_post hook──▶  eidetic-capture.php
                                            │
                                            ▼
                            POST /engrams   (5s timeout, Bearer auth)
                                            │
                                            ▼
                                eideticd -bridge :8421
                                            │
                                            ▼
                            local engram store (alongside chats + browsing)
```

## How it works

1. WordPress fires `save_post` on every post create/update — including drafts,
   autosaves, revisions, and the auto-draft stubs the editor creates on page-load.
2. `eidetic_capture_on_save_post()` filters aggressively:
   - skips if `EIDETIC_DISABLED` constant is set,
   - skips on `DOING_AUTOSAVE`, `wp_is_post_revision`, `wp_is_post_autosave`,
   - skips `auto-draft`, `inherit`, `trash` statuses,
   - skips non-`publish` statuses when "Capture published only" is on (default).
3. The surviving event builds an engram with `surface: "wordpress"` and
   payload `{post_id, post_type, post_status, title, content, permalink}`,
   plus a `meta` envelope (`site_url`, `plugin_ver`, `author_id`, `update`).
4. `wp_remote_post()` sends it to `<daemon_url>/engrams` with a 5-second
   timeout. Failures are logged to `debug.log` and never block the save.

## Files

| File                 | Lines | Purpose                                          |
|----------------------|-------|--------------------------------------------------|
| `eidetic-capture.php`| 284   | Plugin proper — hook + admin page + AJAX test    |
| `readme.txt`         | ~60   | WordPress.org-style readme (stable tag etc.)     |
| `README.md`          | this  | Developer-facing notes                           |

Single PHP file by design — install is "drop it in, click Activate", no zip,
no Composer, no build step.

## Install (local dev)

```bash
# from a WordPress install root
cp -R /path/to/integrations/wordpress wp-content/plugins/eidetic-capture
# then: WP admin → Plugins → Activate "Eidetic Capture"
# then: Settings → Eidetic → paste bridge token → Test connection
```

Default daemon URL is `http://127.0.0.1:8421` (the local bridge listener).
Paste the contents of `~/.eidetic/bridge-token` as the Bearer token.

## Test locally

Two easy options for a throwaway WP install:

- **Local by Flywheel** — fastest GUI install. Create a site, drop the folder
  into `app/public/wp-content/plugins/eidetic-capture/`, activate.
- **wp-env** (official) — `npx @wordpress/env start` in any directory with a
  `.wp-env.json` mapping this folder to `plugins`.

Smoke test once installed:

```bash
# 1. Start the daemon in another terminal
eideticd -bridge :8421

# 2. In WP admin, hit Settings → Eidetic → Test connection (should be OK)
# 3. Create a draft post and click Publish
# 4. Confirm the engram landed
curl -s http://127.0.0.1:8421/search?q=<some-word-from-your-post> \
  -H "Authorization: Bearer $(cat ~/.eidetic/bridge-token)"
```

If something didn't fire, turn on `WP_DEBUG` + `WP_DEBUG_LOG` in
`wp-config.php` and tail `wp-content/debug.log` — every failure path writes
a `[eidetic-capture]` line.

## Config

| Setting                    | Default                  | Notes                              |
|----------------------------|--------------------------|------------------------------------|
| Daemon URL                 | `http://127.0.0.1:8421`  | Trailing slash stripped on save    |
| Bearer token               | empty                    | Sent as `Authorization: Bearer …`  |
| Capture published only     | on                       | Off = include drafts + pending     |
| `EIDETIC_DISABLED` (const) | unset                    | Define in `wp-config.php` to mute  |

Settings live in the `eidetic_capture_settings` row of `wp_options`.

## Design choices worth flagging

- **Custom post types are captured by default.** `save_post` is global, and we
  forward `post_type` in the payload so downstream filtering happens in the
  engram store, not at the plugin layer. If you want to *exclude* a CPT, the
  cheapest path is a `remove_action('save_post', …)` from your theme's
  `functions.php` keyed on `get_post_type()`.
- **Revisions are never captured.** WordPress writes revisions as their own
  post rows; ingesting them would 10-100x the engram volume per post. We
  explicitly drop them via `wp_is_post_revision`.
- **No retry.** A failed POST logs once and returns. The save still succeeds.
  Replay on next save is good enough for a writing workflow; queue-based
  retry is over-engineering for v0.0.1.
- **`sslverify => true`.** No `sslverify => false` escape hatch. If you're
  fronting the daemon with a self-signed cert, fix the cert, don't disable
  verification.

## Publishing to WordPress.org (deferred)

Path when ready, in order:
1. Run `php -l eidetic-capture.php` (must pass).
2. Run the WordPress plugin checker against the folder
   (`wp plugin verify-checksums` is for installed plugins; for new submissions
   use the official Plugin Check plugin in a fresh WP install).
3. Submit via https://wordpress.org/plugins/developers/add/ — the review team
   eyeballs the source. First-submission review currently takes ~14 days.
4. Once approved, push tags to the assigned SVN repo. Tags `0.0.1`, `0.0.2`,
   etc. map to the `Stable tag:` line in `readme.txt`.

Operator (Lokesh) handles the actual submission — this plugin is shipped from
this repo as a drop-in for now.
