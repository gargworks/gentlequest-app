# Tech Debt Fix: Increase Smoke Test Timeout

## Goal
Increase the `brain_smoke_test` timeout from **30s** to **60s** to accommodate Render "Free Tier" cold starts, which periodically cause false positive health check failures.

## Proposed Changes

### Nucleus Server
#### [MODIFY] [mcp-server-nucleus/src/mcp_server_nucleus/runtime/capabilities/render_poller_cap.py](mcp-server-nucleus/src/mcp_server_nucleus/runtime/capabilities/render_poller_cap.py)
- Change default timeout logic to 60 seconds.

## Verification
1. **Automated**: The `nucleus-builder` job itself will run unit tests.
2. **Manual**: After deployment, the user can verify via `/deploy` status or by running `nucleus smoke` (if CLI available).
