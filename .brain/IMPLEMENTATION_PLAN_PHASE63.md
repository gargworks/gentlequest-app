# Implementation Plan - Phase 63: The Sovereign Cloud (GCP/Render Unification)

## Goal Description
Operationalize the "Sovereign Network" on public cloud infrastructure using a "Dual-Engine" strategy.
- **Render:** Hosting the "Face" (Frontend interfaces: HUD, Landing Page, App).
- **GCP (Cloud Run):** Hosting the "Brain" (Nucleus MCP, Oracle, Gladiator Engine).

This separation ensuring that the "Face" is fast, globally distributed (CDN), and cheap, while the "Brain" has access to high-performance compute and Google's native AI ecosystem (Vertex AI) in a secure, scalable container.

## User Review Required
> [!IMPORTANT]
> **Cost Implications:** Deploying Nucleus to Cloud Run involves potential costs for Compute and Vertex AI usage.
> **Security:** We will need to securely manage the `GEMINI_API_KEY` and other secrets in the Cloud environment.

## Proposed Architecture: The Dual-Engine Topology

### 1. The Face (Render)
- **Service A (GentleQuest):** Existing Flutter Web App.
- **Service B (Nucleus HUD):** New Next.js App (`tools/nucleus-hud`).
- **Service C (Landing Page):** Existing Vite App.
- **Routing:** All routed via `gentlequest.ai` (or similar domain) using Render's path rewriting or subdomains.

### 2. The Brain (Google Cloud Run)
- **Service D (Nucleus Daemon):** The Python MCP Server (`mcp-server-nucleus`).
    - **Role:** Runs the Agent Swarm, persistent memory (Postgres/Redis), and the Oracle.
    - **Exposure:** Protected API (Auth Token required).
    - **Scaling:** Scale-to-zero possible, but "Always On" preferred for Oracle monitoring.

## Integration Plan

### Chat 42: The Cloud Protocol (Strategy)
- Define `Dockerfile.nucleus` for the backend.
- Define `render.yaml` (if not existing) or deployment configuration for the HUD.

### Chat 43: The Dual-Engine Deploy
#### [NEW] `deploy/Dockerfile.nucleus`
- Hardened Dockerfile for running `mcp-server-nucleus` in prod.
- Installs dependencies, sets up non-root user.

#### [NEW] `deploy/cloudbuild.yaml`
- Google Cloud Build config to build and deploy Nucleus to Cloud Run.

#### [NEW] `deploy/render_hud.yaml`
- Blueprint for deploying the Next.js HUD to Render.

### Chat 44: The Sovereign Domain
- Configure DNS records to point `hud.gentlequest.ai` -> Render.
- Configure `api.gentlequest.ai` -> GCP Cloud Run.

## Verification Plan
1.  **Local Build:** Verify `docker build -f deploy/Dockerfile.nucleus .` works locally.
2.  **Staging Deploy:** Deploy to a staging tag on GCP.
3.  **Connectivity:** Verify HUD (Local) can talk to Nucleus (Remote) via config change.
