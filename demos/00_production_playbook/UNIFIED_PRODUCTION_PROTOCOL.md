# Unified Production Protocol: The "One-Shot" Atomic Plan

**Objective:**
Synthesize 48 hours of design context ("Physics", "Zen", "God Mode") into a definitive, programmatic video production.

**Philosophy:**
The Video is Plastic. The Narrative is King. Focus is Essential.
We force the video to yield to the Story (via Speed/Freeze) and FORCE the eye to the action (via Dynamic Zoom).

## 1. The Narrative Arch (The "Frankie" Synthesis)

We are weaving three distinct threads into one linear story:
1.  **The Moat (Demo A):** "Governance is Physics."
2.  **The Brain (Demo B):** "Recall is Provenance."
3.  **The Power (Demo C):** "Asymmetry (The Snap)."

## 2. The Atomic Manifest (Event-Driven Schema)

This schema defines the input for the `generate_one_shot_trilogy.py` engine.

| Sequence | Event | Script (Voice: Charon, Rate: 1.0) | Source | In | Out | Visual ROI (Zoom) | Transition | SFX Layer |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Hook** | `seq_01` | "People think AI agents are magic. They're not. They're software. And software *breaks*." | Demo A | 00:00 | 00:05 | **Full Screen** | None | *Hum_Low* |
| **2. Brand** | `seq_02` | "That's why I don't run naked LLMs. I run Nucleus." | Demo A | 00:05 | 00:15 | **Zoom: Right (Claude)** | None | *Keyboard_Fast* |
| **3. Physics** | `seq_03` | "Watch. I try to break my own server... 'Governance Lockout'. It's not just a rule. It's **physics**." | Demo A | 00:55 | 01:05 | **Freeze @ 01:00** | None | *Bass_Drop* |
| **Bridge** | `seq_04` | "Most agents have amnesia. You close the tab, they forget..." | **Black** | N/A | N/A | **N/A** | **Text: THE BRAIN** | *Glitch_Light* |
| **4. Gap** | `seq_05` | "...Nucleus doesn't." | Demo B Part 1 | 00:00 | 00:15 | **Speed (2.0x)** | None | None |
| **5. Recall** | `seq_06` | "Total context recall. Instantly." | Demo B Part 2 | 00:00 | 00:10 | **Speed (4.0x)** | None | *Whoosh* |
| **6. Provenance**| `seq_07` | "It remembers *who* made the decision, and *when*. No hallucinations. Just facts." | Demo B Part 2 | 00:35 | 00:45 | **Freeze @ 00:39** | None | *Chime_Success* |
| **Bridge** | `seq_08` | "Now for the superpower." | **Black** | N/A | N/A | **N/A** | **Text: THE POWER** | *Drum_Hit* |
| **7. The Snap** | `seq_09` | "I'm not writing integrations. I'm just **Snap**-ping my fingers." | Demo C | 00:00 | 00:12 | **Zoom: Input Bar** | None | *Finger_Snap* |
| **8. Reveal** | `seq_10` | "Look at that. The Mesh fills up. One instruction to mount the entire infrastructure." | Demo C | 00:40 | 00:50 | **Freeze @ 00:48** | None | *Rising_Hum* |
| **9. God Mode** | `seq_11` | "Now I have God Mode. Live production data... via natural language." | Demo C | 00:60 | 01:10 | **Zoom: Output List** | None | *Data_Noise* |
| **10. Outro** | `seq_12` | "This isn't the future. This is Nucleus. Mission complete." | Blank | N/A | N/A | **Fade to Black** | None | *Power_Down* |

## 3. The Technical Engine (`one_shot_master_engine.py`)

We will write a single Python script that uses `ffmpeg-python` and `google-cloud-texttospeech` to:

1.  **Generate Audio:** Create `vo_seq_XX.mp3`.
2.  **Calculate Timing:** Sync Audio/Video durations.
3.  **Apply Visual Treatments:**
    *   **Zoom/Crop:** Use `crop=W:H:X:Y` filter to isolate the active region (Right Half or Quarter) and `scale=1920:1080` to fill the frame (if quality permits) OR center it on black. **Decision: 50% Right Crop, Scaled to Fit.**
    *   **Transitions:** Insert a 1s Black Frame with White Text (e.g., "THE BRAIN") between Key Sequences using `drawtext` filter.
4.  **Synthesize SFX:** Generate Tones/Noise.
5.  **Assemble:** Concatenate all parts.

## 4. Why This Works
*   **Harvests Context:** Uses "Physics", "Snap", "God Mode", "Recall".
*   **Plasticity:** Bends time to fit the story.
*   **Focus (The Missing Piece):** Removes dead screen space via Dynamic Zoom.
*   **Structure:** Uses Chapter Transition Bridges to fix the "weird" jump cuts.

**Status:** Converged. Ready for "One-Shot" Execution.
