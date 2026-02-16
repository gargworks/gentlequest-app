# v0.5 Alpha: "The Poison Pill" Implementation Plan

# Goal Description
Execute the "Poison Pill" strategy by releasing Nucleus v0.5 Alpha with "Recursive Mounting" as the standard-setting feature. This establishes Nucleus as the "Browser for the Internet of Agents" and leverages the "Thanos Snap" effect (exponential ecosystem growth).

## User Review Required
> [!IMPORTANT]
> **CLI Bug Fix**: Identified and fixing a conflict in `nucleus mount` command parsing before release.

> [!WARNING]
> **Alpha Release**: This is an Alpha release. It works, but we expect edge cases. The goal is to define the standard, not perfection.

## Proposed Changes

### Nucleus Core Package (`nucleus-mcp`)
#### [MODIFY] [pyproject.toml](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/pyproject.toml)
- Bump version to `0.5.0`
- Ensure dependencies are correct

#### [MODIFY] [cli.py](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/cli.py)
- **Fix**: Rename top-level argparse destination to `cli_command` to avoid conflict with `--command` argument.
- **Cleanup**: Remove dead/duplicate `main()` function.
- **Feature**: Ensure `nucleus mount` command is robust.

#### [MODIFY] [mounter_ops.py](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/runtime/mounter_ops.py)
- **Persistence**: Add `restore_mounts()` to reload connections on startup.

#### [MODIFY] [stdio_server.py](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/runtime/stdio_server.py)
- **Startup**: Call `restore_mounts()` during initialization.

### Documentation
#### [NEW] [RELEASE_NOTES_v0.5.md](file:///Users/lokeshgarg/.gemini/antigravity/brain/d8b5ff3a-6381-4279-9d7c-d1c1b71eec4e/RELEASE_NOTES_v0.5.md)
- Document "Recursive Brain" features.
- Define "Poison Pill" strategy.
- Add CLI documentation.

#### [NEW] [docs/PROTOCOL_SPEC.md](file:///Users/lokeshgarg/.gemini/antigravity/brain/d8b5ff3a-6381-4279-9d7c-d1c1b71eec4e/docs/PROTOCOL_SPEC.md)
- Formal RFC for mounting protocol.

#### [MODIFY] [docs/ECOSYSTEM.md](file:///Users/lokeshgarg/.gemini/antigravity/brain/d8b5ff3a-6381-4279-9d7c-d1c1b71eec4e/docs/ECOSYSTEM.md)
- Add "Thanos Snap" thesis.

## Verification Plan

### Automated Tests
- `scripts/verify_mounting.py`: Verify recursive mounting and persistence (Completed).
- `scripts/test_mount_cli.py`: Verify CLI mount addition (Completed).

### Manual Verification
- Local install (`pip install -e .`)
- run `nucleus mount list`
- run `nucleus mount add ...` (Verify bug fix)
