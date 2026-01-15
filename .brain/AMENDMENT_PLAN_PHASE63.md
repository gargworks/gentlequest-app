# Amendment Plan - Phase 63 Phase Shift: The Sovereign Container

## Problem Identification
The "Dual-Engine" strategy (Render + GCP) splits the filesystem.
- **Nucleus Daemon (GCP)** writes to `.brain/pulse.json`.
- **HUD (Render)** tries to read `.brain/pulse.json`.
- **Result:** The HUD will be blind in production because it cannot see the Daemon's files.

## Proposed Solution: The Sovereign Container (Unified Monolith)
We will deploy both the Brain (Python) and the Face (Next.js) in a **single Docker container**.
- **Process Management:** Use `supervisord` to run both processes.
- **Shared Storage:** Both processes share the `/app/.brain` directory within the container's ephemeral storage (or mounted volume).
- **Network:** Next.js serves the frontend on `$PORT`. Nucleus runs in the background.

## Benefits
1.  **Zero Latency:** HUD reads status directly from local RAM disk / FS.
2.  **Simplified Auth:** No need for complex CORS/OIDC between frontend and backend.
3.  **Single Deployment:** One `gcloud run deploy` updates the entire Sovereign Stack.

## Execution Plan (Chat 44)

### 1. `deploy/supervisord.conf`
Create a configuration file to orchestrate the processes:
- `[program:nucleus]`: Runs `python -m mcp_server_nucleus`
- `[program:nextjs]`: Runs `npm start` (Nucleus HUD)

### 2. `deploy/Dockerfile.unified`
A multi-stage build:
- **Stage 1 (Builder):** Build Next.js app.
- **Stage 2 (Final):** Python 3.11 Slim.
    - Install Node.js.
    - Copy Next.js build.
    - Install Python dependencies (`mcp-server-nucleus`).
    - Copy `supervisord.conf`.
    - **Entrypoint:** `supervisord`.

### 3. Update `deploy/cloudbuild.yaml`
- Point to `deploy/Dockerfile.unified`.

## Verification
- Local: Build and run the unified container.
- Remote: Deploy to Cloud Run. Verify HUD loads and shows "ONLINE" (reading local pulse).
