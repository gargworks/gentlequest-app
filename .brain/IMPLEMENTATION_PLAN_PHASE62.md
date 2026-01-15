# Implementation Plan - Phase 62: The Sovereign Interface (The HUD)

## Goal Description
Build the "Cockpit" for the AI Co-founder.
The HUD (Head-Up Display) visualizes the invisible work of the Nucleus Daemon and the Oracle.
It connects directly to the "Sovereign Files" (`.brain/pulse.json`, `.brain/decisions/*.md`) rather than relying on brittle APIs for local monitoring.

## User Review Required
> [!NOTE]
> **Architecture Decision:** We are using a "Static File Watcher" architecture for the HUD.
> Next.js (Local) -> Reads `.brain/pulse.json` directly -> Renders UI.
> This ensures Zero Latency and 100% Truth (What is on disk is what is real).

## Proposed Changes

### 1. The Signal (Chat 39)
#### [MODIFY] `tools/nucleus-hud/app/api/status/route.ts` (Create if missing)
- Implement a Next.js API Route that reads `.brain/pulse.json` and returns it.
- This bridges the browser (Client) to the File System (Server).

#### [MODIFY] `tools/nucleus-hud/app/components/SystemHealth.tsx`
- Update to poll `/api/status` every 1s (Pulse).
- Visualizes: CPU, Memory, Daemon Status, Active Agents.

### 2. The Oracle Widget (Chat 40)
#### [NEW] `tools/nucleus-hud/app/components/OracleWidget.tsx`
- Reads `.brain/decisions/DECISION_RECORD_PHASE61.md` (via new API route).
- Displays the latest "Titan's Verdict" in a stylish card.
- Shows "Win Probability" and "Strategic Risk".

#### [MODIFY] `tools/nucleus-hud/app/page.tsx`
- Integrate `OracleWidget` into the main grid (Top Right or dedicated Strategy Column).

### 3. The War Room (Chat 41)
#### [NEW] `tools/nucleus-hud/app/components/WarRoom.tsx`
- A dedicated view for "Gladiator Simulations".
- Allows submitting a new proposition (via API -> executes `gladiator_simulator.py`).

## Verification Plan

### Automated Tests
1.  **API Test:** `verify_hud_api.py` (Checks if `/api/status` returns valid JSON from `pulse.json`).
2.  **UI Test:** Manual verification via `npm run dev` (User to look at localhost).
3.  **Integration:** Run `gladiator_simulator.py` manually, refresh HUD, see Oracle Widget update.

### Manual Verification
- Open HUD.
- modify `.brain/pulse.json` manually.
- Watch UI update instantly.
