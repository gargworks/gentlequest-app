# Terminal Sync Quick Start

**Purpose**: Mirror Gemini CLI terminal output into Windsurf for real-time coordination.

## 30-Second Setup

```bash
cd /Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus

# Run any command with sync
./scripts/terminal_sync.sh nucleus status

# View the log
python3 scripts/monitor_terminal_sync.py tail 50
```

## Usage Patterns

### Pattern 1: Error-Only Relay (Recommended)

Run commands normally. When an error occurs:

```bash
# Wrap the failing command
./scripts/terminal_sync.sh nucleus task update

# Then tell Windsurf to read the log
# Windsurf will read: /tmp/nucleus-terminal-sync.log
```

### Pattern 2: Continuous Monitoring

Terminal 1 (Gemini CLI):
```bash
./scripts/terminal_sync.sh nucleus status
./scripts/terminal_sync.sh nucleus task list
```

Terminal 2 (Monitor):
```bash
python3 scripts/monitor_terminal_sync.py
# Press Ctrl+C to stop
```

## Self-Healing Validation

Run the automated test suite:

```bash
./scripts/self_heal_test_suite.sh
python3 scripts/monitor_terminal_sync.py tail 100
```

This triggers 6 error scenarios to validate self-healing behavior.

## Commands Reference

| Command | What It Does |
|---------|-------------|
| `./scripts/terminal_sync.sh <cmd>` | Run command with output capture |
| `python3 scripts/monitor_terminal_sync.py` | Monitor log in real-time |
| `python3 scripts/monitor_terminal_sync.py tail N` | Show last N lines |
| `python3 scripts/monitor_terminal_sync.py clear` | Clear the log file |
| `./scripts/self_heal_test_suite.sh` | Run error scenario tests |

## How Windsurf Reads the Log

In this chat, I can directly read the sync log:

```python
read_file("/tmp/nucleus-terminal-sync.log")
```

This enables:
- Real-time error detection
- Self-healing diagnosis
- Cross-terminal coordination
- Pattern collection from CLI usage

## Log File Location

`/tmp/nucleus-terminal-sync.log` (cleared on reboot)

## Integration with Self-Healing

The sync log provides the **error output** dimension for 4-dimension self-healing:

1. **Error output** ← From sync log
2. **Code file** ← From file system  
3. **Intent** ← From engrams + active task
4. **Recent history** ← From git diff

---

**Full documentation**: `.brain/artifacts/terminal_sync_workflow.md`
