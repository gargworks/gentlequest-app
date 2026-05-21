---
day: 12
channel: buffer
target: x
char_count: 230
topic: Slack /eidetic slash command
source: SHIPPED.md eidetic-slack worker
---
/eidetic <question> now works in Slack. Slash command hits a Cloudflare Worker, the Worker forwards to your local daemon over a tunnel. HMAC-verified. Answers in the thread. Your engrams, queryable from any channel.

eidetic.works
