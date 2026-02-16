# Automated Nucleus Demo Video Production Plan

## Executive Summary

**Goal**: Produce professional demo videos (30s clips + 5min master) with **maximum automation** and **zero iMovie editing**.

**User Constraint**: "I'm really not in the mood of doing all this. Max I can do is some kind of editing in iMovie. I will also kind of avoid that though."

**Solution**: Leverage existing infrastructure (ElevenLabs voice, macOS screen recording, ffmpeg) to create a semi-automated pipeline.

---

## Infrastructure Assessment

### What We Have
1. **ElevenLabs Voice Access**: Past work shows ElevenLabs integration for custom voice (see `ANTIGRAVITY_MEGA_CONTEXT_2026-02-02.md`)
2. **macOS Screen Recording**: Native `screencapture` or QuickTime for terminal/IDE capture
3. **ffmpeg**: Available for video assembly (no evidence of existing scripts, but can create)
4. **believe_it_bot**: Minimal (just a VEO stub, not useful for this)

### What We Need to Build
1. **Voiceover Script Generator**: Convert demo scripts → ElevenLabs-ready text
2. **Screen Recording Automation**: Capture terminal output + IDE interactions
3. **Video Assembly Pipeline**: Merge screen recordings + voiceover with ffmpeg

---

## Production Pipeline (3 Phases)

### Phase 1: Immediate (Demos A & B - No Opus Required)

**Demos to Produce**:
- Demo A: `.env Lock` (30s)
- Demo B: `Engram Recall` (30s)

**Workflow**:

#### Step 1: Generate Voiceover Audio
```bash
# Create voiceover script for Demo A
python3 scripts/generate_demo_voiceover.py --demo A --output demo_a_voiceover.txt

# Send to ElevenLabs API (or use web UI if no API key)
# Output: demo_a_voiceover.mp3
```

**Script Content (Demo A)**:
> "This is what happens when an agent tries to delete your API keys. Nucleus blocks it, logs it, and you get a cryptographic receipt. Zero-trust by default."

#### Step 2: Record Screen Actions
**Manual (but scripted)**:
1. Open terminal, run `nucleus-init`
2. Start QuickTime screen recording (or use `screencapture` if we can automate)
3. Execute the demo steps (ask Claude to delete `.env`, show block, show audit log)
4. Stop recording → `demo_a_screen.mov`

**Semi-Automated Option**:
```bash
# Use AppleScript to automate QuickTime recording
osascript scripts/record_demo_a.scpt
```

#### Step 3: Merge Video + Audio
```bash
# Use ffmpeg to overlay voiceover on screen recording
ffmpeg -i demo_a_screen.mov -i demo_a_voiceover.mp3 \
  -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 \
  -shortest demo_a_final.mp4
```

**Output**: `demo_a_final.mp4` (30s, ready to upload)

---

### Phase 2: Post-Opus (Demo C - Recursive Aggregator)

**Blocker**: Requires `brain_mount_server` implementation (Opus dev work)

**Same Workflow**: Once Demo C is functional, repeat Phase 1 steps.

---

### Phase 3: Master 5-Minute Loom [COMPLETED]
- [x] **Sovereign Trilogy Rendered (V19)**
- [x] Eliminates overlaps, sanitized roadmap, natural cadence.
- [x] Definitive asset: `SOVEREIGN_MASTER_V19.mp4`

**After All 3 Demos Are Ready**:

#### Step 1: Generate Master Voiceover
```bash
python3 scripts/generate_demo_voiceover.py --demo master --output master_voiceover.txt
```

**Script Content** (from LOOM_RECORDING_GUIDE_v2.md):
- [0:00-0:30] Hook
- [0:30-1:30] Demo B
- [1:30-2:30] Demo A
- [2:30-3:30] Demo C
- [3:30-4:15] Price contextualization
- [4:15-4:45] CTA
- [4:45-5:00] Objections

#### Step 2: Assemble Master Video
```bash
# Concatenate all demos + intro/outro
ffmpeg -f concat -i master_concat_list.txt -c copy master_raw.mp4

# Overlay master voiceover
ffmpeg -i master_raw.mp4 -i master_voiceover.mp3 \
  -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 \
  -shortest master_final.mp4
```

**Output**: `master_final.mp4` (5min, ready for Loom/YouTube)

---

## Automation Scripts to Build

### 1. `scripts/generate_demo_voiceover.py`
**Purpose**: Convert demo scripts → ElevenLabs-ready text files

**Usage**:
```bash
python3 scripts/generate_demo_voiceover.py --demo A
python3 scripts/generate_demo_voiceover.py --demo B
python3 scripts/generate_demo_voiceover.py --demo master
```

**Output**: `.txt` files ready for ElevenLabs web UI or API

### 2. `scripts/record_demo_a.scpt` (AppleScript)
**Purpose**: Automate QuickTime screen recording for Demo A

**Workflow**:
1. Open QuickTime
2. Start screen recording
3. Wait 30 seconds (user performs demo steps)
4. Stop recording, save to `output/demo_a_screen.mov`

### 3. `scripts/assemble_demo.sh`
**Purpose**: Merge screen recording + voiceover with ffmpeg

**Usage**:
```bash
./scripts/assemble_demo.sh demo_a_screen.mov demo_a_voiceover.mp3 demo_a_final.mp4
```

---

## Decision: Now or Post-Opus?

### Recommendation: **Hybrid Approach**

**Do NOW (Phase 1)**:
- Build the 3 automation scripts above
- Record Demos A & B (`.env Lock`, `Engram Recall`)
- Generate 2x 30-second clips
- Post Template A to r/ClaudeAI with Demo B embedded

**Why NOW**:
- Demos A & B require zero Opus dev work
- Validates the automation pipeline before scaling
- Gets immediate traction on Reddit while Opus builds Demo C

**Do POST-OPUS (Phase 2 & 3)**:
- Implement Demo C (Recursive Aggregator)
- Record Demo C using the same pipeline
- Assemble the 5-minute master Loom
- Launch on HN with full video

---

## Effort Estimate

### User Effort (Minimal)
1. **Voiceover**: Copy/paste scripts into ElevenLabs web UI (5 min per demo)
2. **Screen Recording**: Perform demo steps while QuickTime records (30s per demo)
3. **Review**: Watch final output, approve or request re-record (2 min per demo)

**Total User Time**: ~20 minutes for Demos A & B

### Agent Effort (Automated)
1. Build 3 automation scripts (1 hour)
2. Generate voiceover scripts (5 min)
3. Run ffmpeg assembly (1 min per demo)

**Total Agent Time**: ~1 hour setup, then 5 min per future demo

---

## Next Steps

1. **Immediate**: Build `generate_demo_voiceover.py`, `record_demo_a.scpt`, `assemble_demo.sh`
2. **User Action**: Record Demos A & B using the scripts
3. **Post to Reddit**: Embed Demo B in Template A hand-raiser post
4. **Post-Opus**: Repeat for Demo C, then assemble master Loom

---

## Appendix: ElevenLabs Integration

**If API Key Available**:
```python
import requests

def generate_elevenlabs_audio(text, output_path):
    url = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": os.getenv("ELEVENLABS_API_KEY")}
    data = {"text": text, "model_id": "eleven_monolingual_v1"}
    
    response = requests.post(url, json=data, headers=headers)
    with open(output_path, "wb") as f:
        f.write(response.content)
```

**If No API Key**:
- Use ElevenLabs web UI: https://elevenlabs.io
- Upload voiceover script, download MP3
- Save to `output/demo_a_voiceover.mp3`
