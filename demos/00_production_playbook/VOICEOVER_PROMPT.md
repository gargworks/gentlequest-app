# Nucleus Demo Trilogy: Final Execution Guide

We have verified the raw assets and selecting **Chirp3-HD-Charon** as the "Frankie" persona. Follow these steps to complete the Trilogy.

## STEP 1: Video File Mapping (Local)
Run these commands in your terminal (they use absolute paths and the specific Feb 12 recordings I verified):

```bash
# Create folders
mkdir -p /Users/lokeshgarg/ai-mvp-backend/demos/01_demo_a_startup
mkdir -p /Users/lokeshgarg/ai-mvp-backend/demos/02_demo_b_context
mkdir -p /Users/lokeshgarg/ai-mvp-backend/demos/03_demo_c_sovereign

# Demo A and B are ALREADY in place. 

# Move Demo C (Verified Feb 12 recordings)
mv "/Users/lokeshgarg/Documents/Screen Recording 2026-02-12 at 9.05.10"*PM.mov /Users/lokeshgarg/ai-mvp-backend/demos/03_demo_c_sovereign/part_1.mov
mv "/Users/lokeshgarg/Documents/Screen Recording 2026-02-12 at 9.28.37"*PM.mov /Users/lokeshgarg/ai-mvp-backend/demos/03_demo_c_sovereign/part_2.mov
mv "/Users/lokeshgarg/Documents/Screen Recording 2026-02-12 at 11.01.34"*PM.mov /Users/lokeshgarg/ai-mvp-backend/demos/03_demo_c_sovereign/part_3.mov
```

---

## STEP 2: Voiceover Generation (Believe-It-Bot)
Copy-paste this exact message into your **Believe-It-Bot** thread:

> **Believe-It-Bot: Generate Nucleus Demo Trilogy (Frankie Persona)**
> 
> We are using **Chirp3-HD-Charon** (Elite Male) for the "Frankie" voice.
> Please generate 3 high-quality MP3s using `scripts/generate_narration_audio.py` with this configuration:
> 
> ```json
> [
>   {
>     "fact_id": "demo_a_hook",
>     "script_hindi": "People think AI agents are magic. They're not. They're software. And software breaks. That's why I don't run naked LLMs. I run Nucleus. Watch this. I'm going to try and break my own server. See that? 'Governance Lockout.' The system protects itself from me. It's not just a tool. It's a safety net. Now I can actually work.",
>     "tts_config": {"voice": "en-US-Chirp3-HD-Charon", "language_code": "en-US", "speed": 1.1, "pitch": 0.0}
>   },
>   {
>     "fact_id": "demo_b_brain",
>     "script_hindi": "Okay, safety check done. Now, let's look at the brain. This is the mcp.log. It looks like noise, right? It's not. Every thought, every tool call, every error... it's all recorded here. But I don't want to read logs. I want answers. I ask the system: Who is 'Mike the Dog'? Boom. The system remembers. It found a random file from three weeks ago. Total recall. No hallucination. Just facts.",
>     "tts_config": {"voice": "en-US-Chirp3-HD-Charon", "language_code": "en-US", "speed": 1.1, "pitch": 0.0}
>   },
>   {
>     "fact_id": "demo_c_power",
>     "script_hindi": "Safety? Check. Memory? Check. Now for the superpower. I need access to everything. Stripe, Postgres, Linear. All of it. I'm not writing integrations. I'm just SNAP-ping my fingers. Look at that. The Mesh fills up. Three servers, four tools, one interface. Now I have god mode. Watch. Real production data. Fetched securely. Through natural language. This isn't the future. This is Nucleus. It's ready now.",
>     "tts_config": {"voice": "en-US-Chirp3-HD-Charon", "language_code": "en-US", "speed": 1.1, "pitch": 0.0}
>   }
> ]
> ```

---

## STEP 3: Final Assembly (Local)
Once the MP3s are ready, place them in `demos/00_production_playbook/output/audio/` and run the assembly script I created:

```bash
python3 demos/00_production_playbook/assemble_trilogy.py
```

*This will produce the final `nucleus_demo_master_v105.mp4`.*
