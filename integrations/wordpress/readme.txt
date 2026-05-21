=== Eidetic Capture ===
Contributors: eideticworks
Tags: ai, knowledge-management, search, second-brain, automation
Requires at least: 5.0
Tested up to: 6.7
Requires PHP: 7.4
Stable tag: 0.0.1
License: GPLv2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html

Capture published posts, pages, and custom post types as engrams in your local eideticd, so your AI sessions and your writing live in one searchable store.

== Description ==

Eidetic Capture is a one-file WordPress plugin that hooks `save_post` and POSTs the post's title, body, status, post type, and permalink to your locally-running `eideticd` HTTP bridge (default `http://127.0.0.1:8421`).

If you already use eidetic to capture your AI chats and your browsing, this plugin closes the loop on your **published writing**: every post you publish is searchable alongside the conversations and pages that informed it.

**Features**

* Captures published posts, pages, and any custom post type registered on your site.
* "Capture published only" toggle so drafts and pending posts don't flood the daemon.
* Bearer-token auth (paste the value from `~/.eidetic/bridge-token`).
* "Test connection" button hits `GET /healthz`.
* Honors a `EIDETIC_DISABLED` PHP constant so staging/dev sites can stay quiet.
* Graceful failure: if the daemon is unreachable, the save still succeeds and a single line is written to `debug.log`.

**What it does NOT do**

* Does not capture revisions, autosaves, or WordPress's "auto-draft" stubs.
* Does not capture trashed posts.
* Does not send anything anywhere except the daemon URL you configure.

== Privacy ==

This plugin makes outbound HTTP calls to **one** endpoint: the daemon URL you enter in Settings → Eidetic. By default that's `http://127.0.0.1:8421`, which is a local socket on the same machine WordPress is running on — nothing leaves your machine.

If you point the daemon URL at a remote bridge tunnel (e.g. a Cloudflare Tunnel terminating at your laptop), then post titles, post bodies, post status, post type, permalinks, and a small `meta` envelope (site URL, plugin version, post author ID) are sent over HTTPS to that tunnel. No third-party analytics, no telemetry, no remote calls to eidetic.works infrastructure.

See ADR-020 in the eidetic-works repo for the full data-flow contract.

== Installation ==

1. Download or clone the `eidetic-capture` folder.
2. Drop it into `wp-content/plugins/eidetic-capture/` on your WordPress install.
3. In WP admin, go to **Plugins → Installed Plugins** and click **Activate** on "Eidetic Capture".
4. Go to **Settings → Eidetic**.
5. Set the Daemon URL (default `http://127.0.0.1:8421` is correct if you run WordPress locally with `eideticd -bridge :8421` on the same box).
6. Paste the contents of `~/.eidetic/bridge-token` into the Bearer token field.
7. Click **Test connection** — you should see `OK (HTTP 200)`.
8. Click **Save Changes**.

That's it. From now on, every publish (and every save, if you turn off "published only") sends an engram.

== Frequently Asked Questions ==

= What if my daemon is down? =

The save_post hook calls the daemon with a 5-second timeout and `is_wp_error()` handling. If anything fails, the post still saves; the plugin writes a single line to `wp-content/debug.log` (assuming `WP_DEBUG_LOG` is on).

= Does this capture custom post types? =

Yes. The `save_post` action fires for every registered post type, and the plugin forwards `post_type` in the engram payload so you can filter downstream.

= Can I disable it on staging? =

Yes. Add `define('EIDETIC_DISABLED', true);` to your `wp-config.php`. The hook returns immediately without making any HTTP call.

= Does it send anything when I save a draft? =

Only if you uncheck "Capture published only" in settings. The default is published-only.

== Changelog ==

= 0.0.1 =
* Initial release. `save_post` capture, admin settings page, test-connection button, EIDETIC_DISABLED escape hatch.
