# Commentary Master Plan: The "Minimalist Assertion" Protocol

**Target Artifact:** `nucleus_demo_master_LOCKED.mp4`
**Design Philosophy:** "Don't describe the action. Describe the power."
**Tone:** Onyx / Deep Neutral. Confident. Zero fluff.

## 1. The Sonic Palette
*   **Voice:** High-fidelity, deep resonance (e.g., ElevenLabs "Brian" or OpenAI "Onyx"). Slow pacing.
*   **SFX Layer:**
    *   **Texture:** *Fast Mechanical Keyboard* (during time-warps).
    *   **Punctuation:** *Subtle Bass Drop / Hum* (on "The Snap" or "Lockout").
    *   **Ambience:** *Server Room Hum* (Very low, -25dB) throughout Demo C.

## 2. The Master Script (Beat Sheet)

| Time Window | Visual Cue | **Spoken Script (The Assertion)** | SFX / Mix Note |
| :--- | :--- | :--- | :--- |
| **00:00 - 00:05** | Terminal Open / "Version 1.0.4" | "System Check." | |
| **00:08 - 00:15** | "NONE are safe" (Freeze) | "The Governance Layer isn't just a setting... It's physics." | **SFX:** Low Thud on "NONE". |
| **00:18 - 00:30** | Demo B Start / Fast Typing | *(Silence)* | **SFX:** High-speed keyboard clacking (-12dB). |
| **00:30 - 00:35** | "Sync Protocol" List | "Total context recall. Instantly." | Fade out keyboard. |
| **00:38 - 00:43** | "Architect Agent" / Date | "Full provenance. It remembers *who* made the decision, and *when*." | |
| **00:45 - 01:00** | Demo C Start / "The Snap" | "The Sovereign Command." | **SFX:** Finger Snap + Reverb on "Snap". |
| **01:10 - 01:20** | Mounting Spinner | "One instruction to mount the entire infrastructure." | **SFX:** Rising synthesized hum. |
| **01:25 - 01:30** | "Demonstration Complete" | "Stripe. Postgres. Search... Aggregated." | |
| **01:35 - 01:40** | Stripe Customer List | "Live production data. Natural language. Zero API keys." | |
| **01:50 - End** | "Clear Gauntlet" / Unmount | "Mission complete. Trace deleted." | **SFX:** Power-down wind-down effect. |

## 3. Production Protocol (The "One Shot" Execution)
To achieve this result without manual editing, we will use a **Programmatic Mix Strategy**:

1.  **Generate Audio segments** as separate files (`vo_01_physics.mp3`, `vo_02_recall.mp3`, etc.).
2.  **Generate/Source SFX** (`sfx_keyboard.mp3`, `sfx_snap.mp3`).
3.  **Complex FFmpeg Filter:**
    *   Place `vo_01` at `delay=5000ms`.
    *   Place `sfx_keyboard` at `delay=20000ms` with `afade`.
    *   *Why:* This decoupled approach allows us to tweak *just the timestamp* in the command if a line is 0.5s off, rather than regenerating the whole track.

## 4. Why This Works
*   **Fixes the "Gap":** By removing the "I am now typing..." narration, we no longer race the 4x video. The SFX fills the gap perfectly.
*   **Elevates the Brand:** It sounds like a movie trailer, not a Udemy tutorial.
*   **Novelty:** It trusts the viewer to read the screen. It respects their intelligence.

**Status:** Plan Converged. Ready for Audio Generation.
