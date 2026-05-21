---
day: 19
channel: buffer
target: x
char_count: 239
topic: FTS5 chosen over vector search
source: SHIPPED.md what's NOT shipped
---
Skipping vector search on purpose. SQLite FTS5 plus a stop-word stripper gives me sub-millisecond recall on 300K engrams. A vector index would add a model dep, a GPU eventually, and zero accuracy win for code-grounded queries. Boring tech.
