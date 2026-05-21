---
day: 20
channel: buffer
target: x
char_count: 216
topic: /export NDJSON streaming (v0.0.42)
source: CHANGELOG.md v0.0.42
---
v0.0.42: GET /export streams every engram as NDJSON. Server-side paginated, memory-bounded against 10M-row stores. `curl -O` saves it, jq consumes it line by line. Right-to-export, proven not promised.

eidetic.works
