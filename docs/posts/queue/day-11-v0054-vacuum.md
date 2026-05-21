---
day: 11
channel: buffer
target: x
char_count: 212
topic: --vacuum SQLite compaction (v0.0.54)
source: CHANGELOG.md v0.0.54
---
v0.0.54: eideticd --vacuum. After heavy purges your SQLite store holds free pages. VACUUM rewrites the file with none. Typical reduction in heavy-purge stores: 20-40%. Hygiene flag for power users.

eidetic.works
