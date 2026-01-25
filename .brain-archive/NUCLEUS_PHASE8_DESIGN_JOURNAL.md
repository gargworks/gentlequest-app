# Design Journal: Nucleus Phase 8 - Outcome Dashboard Integration

## Context & Intent
**Date**: Jan 11, 2026
**Objective**: Transition the Nucleus HUD from a "visualization prototype" to a functional "Clinical Dashboard" by connecting it to real GentleQuest assessment data.

## Problem Statement
The Nucleus HUD had "Outcome" components (Charts) that used hardcoded mock data. To be useful for clinical dogfooding, it needs to pull real GAD-7 and PHQ-9 scores from the production/development database.

## Design Decisions

### 1. Unified API Access
- **Decision**: Introduce a second API constant in the HUD.
- **Rationale**: The HUD currently talks to `server.py` (Nucleus Brain) for tasks/events. Clinical data lives in `app.py` (GentleQuest App).
- **Result**: Added `APP_API_URL` to `config.ts`.

### 2. Session-Driven Visualization
- **Decision**: Add a manual `SESSION_ID` input field.
- **Rationale**: Authentic "Auth" isn't implemented in the HUD yet. To allow clinicians to view specific patient progress, we allow them to input the `session_id`.
- **Optimization**: Default to `test-hud-1` for development ease.

### 3. Metric Polymorphism
- **Decision**: Create a single chart component that handles multiple metrics (GAD-7, PHQ-9).
- **Implementation**: Used a dropdown selector that updates the `metric` state, re-triggering the fetch and normalizing the chart Y-axis (21 for GAD-7, 27 for PHQ-9).

## Verification Results
- **API Connectivity**: Verified that `app.py` exposes `/api/assessment/history`.
- **Data Transformation**: Successfully mapped `{type, score, timestamp}` to the SVG chart format.
- **Manual Verification**: Simulated data injection via Curl showed the chart updating dynamically on `SESSION_ID` change.

## Reflections
Moving clinical logic into the HUD makes "Nucleus" feel like a true co-pilot for the mental health platform, not just a debugger for the AI.

## Next Steps
- Real-time "Assessment Alerts": If a score crosses a threshold, trigger a HUD notification.
- Historical Comparison: Side-by-side view of GAD-7 and PHQ-9.
