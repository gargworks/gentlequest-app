# Forensic Storyboard: Nucleus 1.0.4 Demo B Part 1

**Video File:** `Nucleus 1.0.4 Demo B Part 1.mov`
**Total Frames:** 16
**Duration:** 47s
**Focus:** Session Initialization & Context Retrieval

## Narrative Arc ("The Hook")
1.  **The Pain:** "Stop pasting context manually."
2.  **The Action:** User starts a fresh session and asks Nucleus to *recall*.
3.  **The Continuity:** Nucleus accesses the "Brain" to retrieve architectural decisions.

## Forensic Storyboard & Production Notes

| Frame | Time | Visual State | User Action | System Response | Production / Audio Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **001** | 00:00 | **Home Screen** <br> "Evening, Hi" | **Idle** | **Ready** | **Audio:** "Stop explaining your project from scratch." <br> **Visual:** Full UI visible. |
| **003** | 00:06 | **Typing Start** <br> "I am star..." | **Typing** <br> (Normal Velocity) | **Input Capture** | **Visual:** Time-warp starts here (4x speed). |
| **008** | 00:21 | **Typing Mid** <br> "...check the Nucleus Brain..." | **Typing** <br> (Smooth Continuation) | **Input Capture** | **Audio:** "Nucleus recalls your entire architecture..." <br> **Note:** *No anomaly. Smooth typing flow.* |
| **012** | 00:33 | **Typing End** <br> "...server preferences..." | **Typing** <br> (Normal Velocity) | **Input Capture** | **Visual:** End Time-warp. Return to real-time. |
| **016** | 00:45 | **Submission** <br> Full query visible. | **Submit** | **Processing** | **Audio:** "...instantly." <br> **Visual:** Hold for 0.5s before cut to Part 2. |

## Production Recommendations (Modular Master Strategy)

### 1. Vertical Strategy (The "Right-Side" Stack)
*   **Focus Zone:** **Right 50% Only** (The Claude UI).
*   **Crop Coordinates:** `x:960, y:0, w:960, h:1080` (Targeting the active chat).
*   **Why:** The left terminal is idle. Cropping to the right maximizes readability of the prompt for mobile viewers.

### 2. Rhythm & Pacing
*   **Time Warp:** The typing sequence (Frames 003-014) is ~30s long. **Speed this up by 4x** to fit a 5-6s "Context Hook".
*   **Breaker:** Insert **1.0s Black/Silence** at the end (after Frame 016) to separate this from Part 2.

### 3. Audio & Script Sync
*   **"Nucleus Brain":** Sync this keyword with the appearance of the text in Frame 008.
*   **Sound Design:** Use a *fast mechanical keyboard* sound effect during the time-warped typing to emphasize speed/efficiency.
