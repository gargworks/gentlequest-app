---
day: 7
channel: buffer
target: x
char_count: 239
topic: CGO cross-compile silent failure
source: devto-day8.md architecture decisions
---
CGO + cross-compile silently strips SQLite. The binary still builds. It just crashes the first time you query. Burnt half a day learning this. Now everything's pure-Go via modernc.org/sqlite. One source tree, four platforms, no Xcode trap.
