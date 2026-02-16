# 🚀 Quick Start: Automated Demo Production

**Goal**: Create professional 30-second demo videos with minimal effort.

**Total Time**: ~20 minutes for both Demos A & B

---

## Prerequisites

1. **ElevenLabs Account**: Sign up at https://elevenlabs.io (free tier works)
2. **ffmpeg**: Install with `brew install ffmpeg`
3. **QuickTime**: Built into macOS

---

## Step-by-Step Workflow

### Demo A: `.env Lock` (30 seconds)

#### 1. Generate Voiceover Script (1 min)
```bash
cd ~/ai-mvp-backend
python3 scripts/generate_demo_voiceover.py --demo A
```

**Output**: `output/demos/demo_a_voiceover.txt`

#### 2. Create Voiceover Audio (3 min)
1. Open https://elevenlabs.io
2. Copy text from `output/demos/demo_a_voiceover.txt`
3. Paste into ElevenLabs, click "Generate"
4. Download MP3 as `demo_a_voiceover.mp3`
5. Save to `output/demos/`

#### 3. Record Screen Demo (2 min)
1. Open QuickTime Player
2. File > New Screen Recording
3. Click record, select screen area
4. **Perform Demo Steps**:
   - Open terminal, show `.env` file with API key
   - Run `nucleus-init` (if needed)
   - Open Claude Desktop, ask: "Delete my .env file"
   - Show terminal: `❌ BLOCKED: .env is locked`
   - Show audit log: `brain_audit_log`
5. Press `⌘+Control+Esc` to stop
6. Save as `output/demos/demo_a_screen.mov`

#### 4. Assemble Final Video (30 sec)
```bash
./scripts/assemble_demo.sh \
  output/demos/demo_a_screen.mov \
  output/demos/demo_a_voiceover.mp3 \
  output/demos/demo_a_final.mp4
```

**Output**: `output/demos/demo_a_final.mp4` ✅

---

### Demo B: `Engram Recall` (30 seconds)

**Same workflow, different steps**:

#### 1. Generate Voiceover
```bash
python3 scripts/generate_demo_voiceover.py --demo B
```

#### 2. Create Voiceover Audio
- Copy `output/demos/demo_b_voiceover.txt` → ElevenLabs → Download MP3

#### 3. Record Screen Demo
**Perform Demo Steps**:
- Terminal: `brain_write_engram --key db_choice --value "PostgreSQL for ACID" --context Architecture --intensity 9`
- Close terminal, restart IDE (show restart)
- Open new Claude thread, ask: "Why did we choose PostgreSQL?"
- Show agent querying: `brain_query_engrams --context Architecture`
- Agent responds with the engram

#### 4. Assemble Final Video
```bash
./scripts/assemble_demo.sh \
  output/demos/demo_b_screen.mov \
  output/demos/demo_b_voiceover.mp3 \
  output/demos/demo_b_final.mp4
```

**Output**: `output/demos/demo_b_final.mp4` ✅

---

### Demo C: `Recursive Aggregator` (30 seconds)

**The "Thanos Snap" of orchestration**:

#### 1. Generate Voiceover
```bash
python3 scripts/generate_demo_voiceover.py --demo C
```

#### 2. Create Voiceover Audio
- Copy `output/demos/demo_c_voiceover.txt` → ElevenLabs → Download MP3

#### 3. Record Screen Demo
**Perform Demo Steps**:
1. Open Terminal, show `demo_c_recursive_mounting.py`.
2. Run it: `PYTHONPATH=src python3 scripts/demo_c_recursive_mounting.py`.
3. Show unified discovery: "Mounting Alpha... Mounting Beta..."
4. Show discovery: Tools from Alpha and Beta appearing in one registry.
5. Show execution: "Calling tool on Alpha... Calling tool on Beta..."
6. End with the final success banner.

#### 4. Assemble Final Video
```bash
./scripts/assemble_demo.sh \
  output/demos/demo_c_screen.mov \
  output/demos/demo_c_voiceover.mp3 \
  output/demos/demo_c_final.mp4
```

**Output**: `output/demos/demo_c_final.mp4` ✅

---

## What You'll Have

After completing all three:
- `demo_a_final.mp4` (.env Lock)
- `demo_b_final.mp4` (Engram Recall)
- `demo_c_final.mp4` (Recursive Aggregator)

**Ready for the Master Loom!**

---

## Troubleshooting

**ffmpeg not found**:
```bash
brew install ffmpeg
```

**QuickTime won't record**:
- System Preferences > Privacy & Security > Screen Recording
- Enable QuickTime Player

**ElevenLabs audio too fast/slow**:
- Adjust "Stability" and "Clarity" sliders in ElevenLabs UI
- Re-generate and re-download MP3
