
# PARALLEL DOCS UPDATE STRATEGY: The "Frankie" Experiment
**Status:** EXPERIMENTAL (Test Branch)
**Reference:** `LOOM_RECORDING_GUIDE_v2.md` + `ag1202 Context`
**Objective:** Align explicitly with the "Demonstrate, Don't Explain" framework.

## 1. The Frankie Framework Analysis
The `LOOM_RECORDING_GUIDE_v2.md` defines a strict narrative arc:
1.  **The Hook (0:00):** State the problem instantly. No sales calls (or in our case, no config edits).
2.  **The Hand-Raiser (0:20):** Address the "pain point" that makes them self-qualify.
3.  **Offer Summary (1:00):** "Promise, not Service." (e.g., "Prevent leaks," not "File locking").
4.  **Contextualize Price/Value (2:30):** "Right now, it's free/open source."
5.  **CTA (Ending):** Clear instructions.

## 2. The Timeline Mapping
We must map this 5-minute framework onto our **3-minute Locked Video**.

| Time | Visual Action | Frankie Framework Beat | Script (Experimental) |
| :--- | :--- | :--- | :--- |
| **00:00** | Terminal Init | **The Hook** | "I stopped trying to manage AI permissions manually. It's a losing game." |
| **00:08** | "NONE are safe" | **The Hand-Raiser** | "If you've ever had an agent hallucinate an API key into a log file, this is for you." |
| **00:30** | `ls -R` (Gap) | **Demonstrate Outcome** | "See this? My `.env` file. The agent *can* read it. But watch what happens when it tries to burn it." |
| **00:55** | Blocked Error | **Promise, Not Service** | "Blocked. I didn't write a regex. I didn't prompt it. The *OS* stopped it." |
| **01:15** | Demo B Start | **Value Context** | "Most tools charge you for 'enterprise security'. This is just... local physics." |
| **01:22** | Typing | **Demonstrate Outcome 2** | "And memory? You stop repeating yourself." |
| **01:45** | Agent Response | **The "Who" (Provenance)** | "It remembers the context. It remembers *me*. No amnesia." |
| **02:10** | Manual Snap | **The "Snap" (Ease)** | "I don't spend hours on integration. I just... Snap." |
| **02:40** | Mesh Fill | **Outcome 3 (Scale)** | "One instruction. The whole infrastructure is mounted." |
| **02:50** | Output List | **Contextualize Price** | "This is typically what you build a whole platform for. Nucleus does it locally. Free." |
| **03:00** | Fade Out | **Clear CTA** | "Check the GitHub. `pip install mcp-server-nucleus`. Do it now." |

## 3. The Experimental Engine Config
To execute this "Frankie Experiment," we will use this specific JSON configuration for `simple_overlay_engine.py`:

```json
{
    "video_source": "nucleus_demo_master_LOCKED.mp4",
    "cues": [
        {
            "id": "exp_01_hook",
            "time": 0.5,
            "text": "I stopped trying to manage AI permissions manually. It's a losing game.",
            "sfx_under": "hum_low"
        },
        {
            "id": "exp_02_pain",
            "time": 8.0,
            "text": "If you've ever had an agent hallucinate a delete command on a production database, you know the fear.",
            "sfx_under": null
        },
        {
            "id": "exp_03_demo",
            "time": 30.0,
            "text": "See this? My .env file. The agent thinks it has access. But watch what happens when it tries to break rule number one.",
            "sfx_under": null
        },
        {
            "id": "exp_04_outcome",
            "time": 56.0,
            "text": "Blocked. I didn't write a regex. I didn't prompt engineering this. The Operating System stopped it.",
            "sfx_under": "bass_drop"
        },
        {
            "id": "exp_05_value",
            "time": 76.0,
            "text": "Most tools make you pay 'enterprise' seats for this. Nucleus just makes it physics.",
            "sfx_under": "glitch_light"
        },
        {
             "id": "exp_06_memory",
             "time": 82.0,
             "text": "And the amnesia? Gone.",
             "sfx_under": "whoosh"
        },
        {
            "id": "exp_07_provenance",
            "time": 105.0,
            "text": "It remembers the context. It remembers *me*. No hallucinations. Just audit logs.",
            "sfx_under": "chime_success"
        },
        {
            "id": "exp_08_snap",
            "time": 145.0,
            "text": "I'm not spending my weekend writing integrations. I just... Snap.",
            "sfx_under": "finger_snap"
        },
        {
            "id": "exp_09_scale",
            "time": 160.0,
            "text": "One instruction. Stripe, Postgres, Vectors... Mounted.",
            "sfx_under": "rising_hum"
        },
        {
            "id": "exp_10_godmode",
            "time": 170.0,
            "text": "It's God Mode for your local stack. Live data. Natural language. Zero setup.",
            "sfx_under": "data_noise"
        },
        {
            "id": "exp_11_cta",
            "time": 180.0,
            "text": "This is open source. Check the GitHub. `pip install mcp-server-nucleus`. Do it now.",
            "sfx_under": "power_down"
        }
    ],
    "global_sfx": {
        "hum_low": { "vol": "0.4" },
        "bass_drop": { "vol": "0.8" },
        "glitch_light": { "vol": "0.1" },
        "whoosh": { "vol": "0.3" },
        "chime_success": { "vol": "0.6" },
        "finger_snap": { "vol": "0.8" },
        "rising_hum": { "vol": "0.3" },
        "data_noise": { "vol": "0.2" },
        "power_down": { "vol": "0.5" }
    },
    "voice_params": {
        "name": "en-US-Chirp3-HD-Charon",
        "rate": 1.05
    }
}
```

## 4. Why This is "Next Level"
1.  **Psychological Alignment:** It speaks to the *fear* (hallucinated delete) and the *pain* (integrations on weekends).
2.  **Rate Adjustment:** Speed is slightly up (1.05) to sound more "YouTuber/Frankie" and less "Corporate".
3.  **CTA:** It ends with a specific instruction (`pip install`), not a vague "Mission complete".

## 5. Execution
If approved, I will:
1.  Save the JSON above to `EXPERIMENTAL_SCRIPT_CONFIG.json`.
2.  Run `simple_overlay_engine.py` pointing to this config.
3.  Output as `nucleus_demo_trilogy_experimental.mp4`.
