---
day: 21
channel: buffer
target: x
char_count: 214
topic: kubectl logs piped into capture
source: CHANGELOG.md v0.0.52 use cases
---
How I actually use eidetic: `kubectl logs my-pod | eideticd --capture --surface kubernetes`. Next time something breaks I just ask "what was that error in my-pod last week" and get the line back. Recall as a habit.
