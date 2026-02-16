# 🧪 Atomic Protocol: Forensic Video Analysis
> **Objective**: Deconstruct video files into 3-second semantic frames to enable precise voiceover synchronization.

## 🎯 Target Asset
**File**: `Nucleus 1.0.4 Demo B Part 1.mov`
**Location**: `/Users/lokeshgarg/Documents/`
**Duration**: ~48 seconds
**Expected Frames**: 16 (at 1 frame per 3 seconds)

## 🔬 The Procedure (Step-by-Step)

### Phase 1: Frame Extraction (The Biopsy)
We will use `ffmpeg` to extract a high-quality still image every 3 seconds.
```bash
ffmpeg -i "/Users/lokeshgarg/Documents/Nucleus 1.0.4 Demo B Part 1.mov" \
       -vf "fps=1/3" \
       "/Users/lokeshgarg/.gemini/antigravity/brain/d8b5ff3a-6381-4279-9d7c-d1c1b71eec4e/frames/demo_b_p1_%03d.png"
```

### Phase 2: Visual Forensics (The Analysis)
For *each* extracted frame, we will perform a semantic analysis to determine:
1.  **Timestamp**: Exact time in the video (e.g., 00:03, 00:06).
2.  **Terminal State**: What command is currently executing? (e.g., `nucleus mount list`)
3.  **Visual Output**: What is the specific return value or error message? (e.g., `ToolBlockError: env_lock`)
4.  **User Action**: What did the user just type?
5.  **Narrative Context**: Which part of the "Engram Recall" story does this correspond to?

### Phase 3: The Synthesis (The Output)
We will compile the findings into a structured log: `DEMO_B_PART_1_ANALYSIS.json`.

**Data Structure:**
```json
{
  "frame_id": 2,
  "timestamp": "00:06",
  "visual_summary": "User types 'nucleus memory recall'",
  "terminal_text_detected": "searching engrams...",
  "implied_event": "Memory Retrieval Start",
  "voiceover_cue": "Your agents never forget."
}
```

## 🛡️ Safety Constraints
- **Read-Only**: No files in `Documents` will be modified.
- **Isolated Output**: All frames and logs will be stored in the Agent Brain (`.gemini/...`), keeping the user's Documents folder clean.
- **No Execution**: **This plan is inactive.** I await the signal to begin Phase 1.
