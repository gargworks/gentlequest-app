---
day: 29
channel: buffer
target: x
char_count: 206
topic: Cursor auto-capture
source: CHANGELOG.md v0.0.41 Cursor PathContains
---
Cursor users: the daemon's fsnotify watcher captures chatSessions/*.json automatically. v0.0.41 added a PathContains filter so the workspace.json noise stays out. Plug in the MCP and Cursor gets recall too.
