# Nucleus Coordinator Autopilot

**Full multi-turn autopilot coordinator for persistent Gemini CLI sessions**

## Overview

The Nucleus Coordinator Autopilot enables long-running, multi-turn conversations with Gemini CLI while maintaining full integration with Nucleus's self-healing, error routing, and state persistence systems.

## Features

### Core Capabilities

- **Multi-turn sessions**: Keep Gemini CLI alive across multiple prompts
- **Turn persistence**: All turns logged to `.brain/coordinator/turns.jsonl`
- **Interactive mode**: REPL-style prompt loop with special commands
- **Batch mode**: Execute prompts from a file sequentially
- **State recovery**: Resume sessions with full context restoration
- **Self-healing**: Automatic error detection and routing to selfhealer
- **Graceful shutdown**: Ctrl+C saves state and prints statistics

### Integration Points

1. **Wire 1**: Gemini CLI output capture
2. **Wire 2**: Intent parsing (errors, reviews, file changes)
3. **Wire 3**: Routing to selfhealer or Cascade
4. **Wire 4**: Turn completion detection and loop continuation

## Usage

### One-Shot Mode (Backwards Compatible)

```bash
# Execute a single task and exit
nucleus run coordinator --task "nucleus status --format json"

# With specific session
nucleus run coordinator --task "help me debug this" --resume-id my-session
```

### Interactive Autopilot Mode

```bash
# Start interactive multi-turn session
nucleus run coordinator --autopilot

# With initial task
nucleus run coordinator --autopilot --task "Let's build a feature"
```

**Interactive Commands**:
- `/help` — Show available commands
- `/auth` — Show authentication status (API key, session ID, proxy URL)
- `/stats` — Print session statistics
- `/heal` — Force self-heal check on last output
- `/turns` — Show turn history
- `/exit` or `/quit` — Graceful shutdown

### Batch Autopilot Mode

```bash
# Execute prompts from file
nucleus run coordinator --prompt-file prompts.txt
```

**Prompt file format**:
```
# Lines starting with # are comments
nucleus --version
nucleus status --minimal
nucleus engram search selfheal
```

### Advanced Options

```bash
# Custom idle timeout (default: 15 seconds)
nucleus run coordinator --autopilot --idle-timeout 30

# Auto-wait on rate limits
nucleus run coordinator --autopilot --gemini-auto-wait

# YOLO mode (auto-approve Gemini tools)
nucleus run coordinator --autopilot --gemini-yolo

# Quiet mode (minimal output for scripting)
nucleus run coordinator --autopilot --quiet
```

## Architecture

### Turn Flow

```
┌─────────────────────────────────────────┐
│  1. User Input / Prompt Queue          │
│     ↓                                   │
│  2. Send to Gemini CLI (-p mode)       │
│     ↓                                   │
│  3. Stream stdout → handle_line()      │
│     ↓                                   │
│  4. Parse intent (error/review/file)   │
│     ↓                                   │
│  5. Route to selfhealer/summon/log     │
│     ↓                                   │
│  6. Persist turn to turns.jsonl        │
│     ↓                                   │
│  7. Next prompt or exit                │
└─────────────────────────────────────────┘
```

### State Persistence

**Turn Records** (`.brain/coordinator/turns.jsonl`):
```json
{
  "turn_id": 1,
  "prompt": "nucleus status --format json",
  "response_line_count": 42,
  "response_preview": "...",
  "stats_snapshot": {"lines": 42, "errors": 0, "heals": 0},
  "ts": "2026-03-11T16:45:00Z"
}
```

**Session State** (`.brain/session/current_id`):
```
my-session-slug
```

### Chained One-Shot Implementation

Due to Gemini CLI's TTY requirement for interactive mode, autopilot currently uses **chained one-shot calls** with `--resume`:

```
Turn 1: gemini -p "prompt 1" --resume
  ↓
Turn 2: gemini -p "prompt 2" --resume
  ↓
Turn 3: gemini -p "prompt 3" --resume
```

This maintains session continuity while working within Gemini CLI's constraints.

## Testing

### Run Test Suite

```bash
# Full test suite (all 10 tests)
./scripts/test-coordinator-autopilot.sh
```

### Test Cases

1. **Perplexity Case 1**: Direct nucleus CLI (satellite view)
2. **Perplexity Case 2**: Coordinator one-shot (nucleus --help)
3. **Perplexity Case 3**: MCP surface (engram search)
4. **Perplexity Case 4**: Self-heal trigger
5. **Autopilot Test 5**: Batch mode with --prompt-file
6. **Autopilot Test 6**: Turn persistence
7. **Autopilot Test 7**: Interactive mode commands
8. **Backwards Compat 8**: Existing one-shot mode
9. **Backwards Compat 9**: CLI wrapper
10. **Autopilot Test 10**: Idle timeout configuration

### Manual Testing

```bash
# Test interactive mode
nucleus run coordinator --autopilot

# Test batch mode
echo -e "nucleus --version\nnucleus status" > /tmp/test.txt
nucleus run coordinator --prompt-file /tmp/test.txt

# Test self-heal
NUCLEAR_BRAIN_PATH=/tmp/bad nucleus run coordinator \
  --task "nucleus status" --no-resume
```

## Configuration

### Environment Variables

- `NUCLEUS_SESSION_ID` — Current session identifier
- `NUCLEAR_BRAIN_PATH` — Brain directory path (default: `.brain`)
- `GEMINI_API_KEY` — Gemini API key (or use `.env.gemini`)
- `NUCLEUS_PROXY_DEFAULT_URL` — Gemini proxy base URL

### Session Discovery

Priority order for session ID resolution:
1. `NUCLEUS_SESSION_ID` env var (if CLI slug, not UUID)
2. `.brain/session/current_id` (centralized discovery)
3. `GEMINI_MAIN_SESSION_ID` env var
4. `.gemini-sessions.json` config file

## Troubleshooting

### Gemini CLI Not Found

```bash
npm i -g @google/gemini-cli
```

### API Key Not Set

Create `.env.gemini` in project root:
```
your-api-key-here
```

### Turn Persistence Not Working

Check brain path:
```bash
echo $NUCLEAR_BRAIN_PATH
ls -la .brain/coordinator/
```

### Self-Heal Not Triggering

Verify selfhealer is importable:
```bash
python3 -c "from mcp_server_nucleus.selfhealer import diagnose_and_fix; print('OK')"
```

## Implementation Details

### Key Functions

**`watch_gemini_autopilot()`** (coordinator.py:883-1090)
- Main autopilot loop
- Handles prompt queue and interactive input
- Manages turn persistence
- Supports batch and interactive modes

**`_persist_turn()`** (coordinator.py:808-823)
- Appends turn record to JSONL
- Includes prompt, response preview, stats snapshot

**`handle_line()`** (coordinator.py:471-541)
- Processes each line from Gemini output
- Routes to selfhealer, summon, or validator
- Detects task completion signals

### CLI Integration

**Flags** (cli.py:1634-1636):
- `--autopilot` — Enable multi-turn mode
- `--prompt-file <path>` — Batch mode
- `--idle-timeout <seconds>` — Tune turn detection

**Routing** (cli.py:4199-4207):
```python
if getattr(args, 'autopilot', False) or getattr(args, 'prompt_file', None):
    return mod.watch_gemini_autopilot(...)
```

## Future Enhancements

### Planned Features

1. **True PTY Interactive Mode** — Use Python's `pty` module for real stdin/stdout interaction
2. **Streaming Turn Display** — Real-time output during turn execution
3. **Turn Replay** — Replay previous turns from history
4. **Multi-Agent Coordination** — Coordinate multiple Gemini sessions
5. **Turn Branching** — Fork conversation at specific turns

### Known Limitations

- **TTY Requirement**: Gemini CLI interactive mode needs TTY (workaround: chained one-shot)
- **Idle Detection**: Fixed timeout, not adaptive to response length
- **No Streaming**: Full turn buffered before display
- **Single Session**: One autopilot instance per brain

## Related Documentation

- [Coordinator Architecture](./COORDINATOR.md)
- [Self-Healing System](./SELFHEALER.md)
- [Session Management](./SESSIONS.md)
- [Perplexity Spec](../PERPLEXITY_SPEC.md)

## Examples

### Example 1: Debug Session

```bash
nucleus run coordinator --autopilot --task "Help me debug the routing fuzzer"
```

**Session**:
```
🧠 [nucleus] > Show me the test failures
[Turn 1 executes...]

🧠 [nucleus] > Fix the keyword collision in test_routing_fuzzer.py
[Turn 2 executes...]

🧠 [nucleus] > Run the tests again
[Turn 3 executes...]

🧠 [nucleus] > /stats
📊 [Coordinator] Session Stats:
   Lines processed: 342
   Errors caught:   2
   Self-heals:      2
   Reviews sent:    1
   Files validated: 3

🧠 [nucleus] > /exit
```

### Example 2: Batch Deployment

**prompts.txt**:
```
# Deployment checklist
nucleus status --format json
nucleus doctor --fix
nucleus recipe list --tag production
nucleus engram search deployment
```

**Execute**:
```bash
nucleus run coordinator --prompt-file prompts.txt --quiet
```

### Example 3: Self-Healing Demo

```bash
# Trigger error for self-heal demo
NUCLEAR_BRAIN_PATH=/tmp/nonexistent nucleus run coordinator \
  --task "nucleus status" --no-resume --gemini-auto-wait
```

**Output**:
```
[coordinator] error: No such file or directory: '/tmp/nonexistent'
  [self_heal] error caught
  ✅ [self-heal] AUTO-FIXED: create_brain_directory
```

---

**Version**: 1.0.0  
**Last Updated**: 2026-03-11  
**Status**: Production Ready
