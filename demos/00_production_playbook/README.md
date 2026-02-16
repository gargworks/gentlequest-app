# Nucleus Demo Production Playbook

**Version:** 1.0 (Indexed Structure)
**Status:** Active Strategy
**Last Updated:** February 14, 2026

## 1. Directory Structure (The Stint Repo)
This `demos/` directory is the canonical playground for Nucleus video production. It is structured as an indexed repository of playbooks and execution artifacts.

```text
demos/
├── 00_production_playbook/         # The Strategy Core
│   ├── README.md                   # This Guide
│   ├── PRODUCTION_STRATEGY.md      # The "Modular Master" Strategy
│   └── VIDEO_ANALYSIS_PROTOCOL.md  # How to extract & analyze frames
│
├── 01_demo_a_startup/              # Demo A: Server Start
│   └── frames/ (gitignored)        # Extracted frames for analysis
│
├── 02_demo_b_context/              # Demo B: The Brain (Context)
│   ├── FORENSICS_PART_1.json       # Confirmed Forensic Data
│   ├── STORYBOARD_PART_1.md        # Narrative & Production Plan
│   ├── FORENSICS_PART_2.json
│   └── STORYBOARD_PART_2.md
│
└── 03_demo_c_sovereign/            # Demo C: Sovereign Command
    └── frames/ (gitignored)        # Extracted frames for analysis
```

## 2. The Forensic Protocol
We do not "edit by feel". We edit by data.
1.  **Extraction:** Extract frames at **0.33 FPS (every 3 seconds)** from the source recording.
2.  **Forensics (`JSON`):** Analyze each frame for:
    *   `visual_state` (UI elements, cursor position).
    *   `user_input` (Typing velocity, text content).
    *   `system_response` (Latency, UI indicators).
3.  **Storyboard (`MD`):** Map the forensic data to a narrative arc.
    *   **The Hook (0-3s):** Define the problem.
    *   **The Action:** The user's input.
    *   **The Payoff:** The system's output.

## 3. Production Strategy: "The Modular Master"
We produce **One Master Timeline** (A -> B -> C) that can be sliced into vertical shorts without re-editing.

*   **Demo A (0:00 - 0:45):** Server Start & Validation.
*   **Breaker:** 1.0s Black/Silence.
*   **Demo B (0:46 - 1:35):** Context Retrieval & Attribution.
*   **Breaker:** 1.0s Black/Silence.
*   **Demo C (1:36 - 2:15):** Recursive Mounting (The Finale).

**Vertical Rule:**
*   **Shorts (9:16):** Focus on the **Right 50%** (Claude UI). The left terminal is structural context but can be cropped if static.
