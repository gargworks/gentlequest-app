# Production Strategy & Gap Analysis: Nucleus Demo Trilogy

**Status:** Draft for Review
**Date:** February 14, 2026

## 1. Executive Summary
This document outlines the strategy for producing the Nucleus Demo Trilogy (A, B, C) and identifies specific gaps in the current forensic artifacts for Demo B Part 1.

**Core Recommendation:** Adopt a **"Modular Master"** production workflow. Build one continuous timeline that is designed to be sliced into three standalone vertical shorts without re-editing.

---

## 2. Gap Analysis: Demo B Part 1
*Refining `DEMO_B_PART_1_FORENSICS.json` and `STORYBOARD.md` against Phase C standards.*

### A. Forensics (`DEMO_B_PART_1_FORENSICS.json`)
| Gap Identifier | Description | Severity | Remediation Plan |
| :--- | :--- | :--- | :--- |
| **Typing Velocity** | The current JSON captures `is_typing: true` but lacks the *specific wpm/velocity* data needed to perfectly time the "Time Warp" effect. | Low | Add `typing_velocity` field to `user_input` (e.g., "Normal", "Accelerated 4x"). |
| **Anomaly Complexity** | Frame 008 is flagged, but the *exact* frames before/after for the cut point are not precise enough for an automated editor. | Medium | Add `cut_point: true` metadata to Frame 007 (Out) and Frame 009 (In). |
| **Vertical Framing** | JSON lacks "Region of Interest" (ROI) coordinates for vertical cropping. | High | Add `roi_box` (e.g., `{"x": 0, "y": 0, "w": 1920, "h": 1080}`) to `visual_state` to guide the vertical cop. |

### B. Storyboard (`DEMO_B_PART_1_STORYBOARD.md`)
| Gap Identifier | Description | Severity | Remediation Plan |
| :--- | :--- | :--- | :--- |
| **Vertical Strategy** | Current storyboard assumes 16:9 Landscape. It fails to address how to show the wide "Split Screen" (Terminal + Claude) in 9:16 Vertical. | **Critical** | Add a **"Vertical Layout Strategy"** section: "Split Zone" (Top: Claude, Bottom: Terminal) vs. "Pan and Scan". |
| **Audio Transitions** | The "Typing Crescendo" is mentioned, but the *exact* synchronization with the "Cut" at Frame 008 is vague. | Medium | Specify: "Audio cut *precedes* video cut by 2 frames (J-Cut)." |
| **Hook Theory** | The opening hook (0s-3s) is "Session Limit". It needs to be punchier for a Short. | High | Update Narrative/VO to start *in media res*: "Stop determining context manually." |

---

## 3. Production Strategy: "The Modular Master"

### A. Format Strategy (Clips vs. Full Video)
**Recommendation:** Do **NOT** produce separate disparate clips. Produce one **Master Timeline** (Duration: ~2m 15s) that contains A, B, and C in sequence, with **Clean Breakers**.

*   **The Master Timeline:** 
    *   **0:00 - 0:45:** Demo A (The Hook / Server Start)
    *   **0:45 - 1:30:** Demo B (The Brain / Retrieval) -> *Focus of current work*
    *   **1:30 - 2:15:** Demo C (The Sovereign Command / Recursive Mount)
*   **The "Clean Breaker" Rule:** 
    *   Ensure there is a **1-second silence/black** (or specific transition graphic) between A, B, and C.
    *   **Why?** This allows you to export the full file for YouTube/LinkedIn, *AND* simply slice it at the breaker points for TikTok/Shorts without remixing audio.

### B. Vertical Adaptation Strategy (Shorts)
**Problem:** The Nucleus UI is wide (Terminal Left + Claude Right).
**Solution:** **"The Split Zone Stack"**
*   **Top 50%:** Show the **Active Agent** (Claude UI/Response Area). This is where the eye goes.
*   **Bottom 50%:** Show the **Source of Truth** (Terminal/Logs). This anchors the technical depth.
*   *Avoid:* "Pan and Scan" (moving back and forth), which causes motion sickness in code demos.

---

## 4. Immediate Action Plan
1.  **Refine Demo B Part 1:** Update `FORENSICS.json` and `STORYBOARD.md` to include "Vertical ROI" and "Cut Points".
2.  **Execute Production (Part B):** produce the "Modular Master" segment for Demo B (Part 1 + Part 2 combined).
3.  **Expand to A & C:** Once the "B-Core" is solid, replicate the forensic/storyboard process for A and C.
