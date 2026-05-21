---
day: 4
channel: buffer
target: x
char_count: 168
topic: P95 latency vs SLO
source: devto-day8.md
---
SLO was 100ms P95. Actual on 278K real engrams: 0.27ms. That's 370x inside the target. The trick is SQLite WAL plus an FTS5 index, not a vector store. Boring tech wins.
