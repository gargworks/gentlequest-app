#!/usr/bin/env python3
"""
Nucleus Demo Voiceover Script Generator

Converts demo scripts from LOOM_RECORDING_GUIDE_v2.md into ElevenLabs-ready text files.

Usage:
    python3 scripts/generate_demo_voiceover.py --demo A
    python3 scripts/generate_demo_voiceover.py --demo B
    python3 scripts/generate_demo_voiceover.py --demo master
"""

import argparse
import os
from pathlib import Path

import requests
import json
from dotenv import load_dotenv
from google.cloud import texttospeech

# Load environment variables
load_dotenv()

# Demo voiceover scripts (from LOOM_RECORDING_GUIDE_v2.md)
DEMO_SCRIPTS = {
    "A": {
        "name": "Phase A: Sovereign Context (.env Lock)",
        "duration": "30 seconds",
        "elevenlabs_voice_id": "pNInz6obpgDQGcFmaJgB", # Antoni (Warm, engaging)
        "google_voice_id": "en-US-Neural2-J", 
        "script": """This is what happens when an agent tries to delete your API keys. Nucleus blocks it, logs it, and you get a cryptographic receipt. Zero-trust by default."""
    },
    "B": {
        "name": "Phase B: Engram Recall (Memory Persistence)",
        "duration": "30 seconds",
        "elevenlabs_voice_id": "pNInz6obpgDQGcFmaJgB",
        "google_voice_id": "en-US-Neural2-J",
        "script": """Your agents never forget. This decision was written 3 months ago. New thread, new session—doesn't matter. The memory persists."""
    },
    "C": {
        "name": "Phase C: Recursive Aggregator (The Thanos Snap)",
        "duration": "45 seconds",
        "elevenlabs_voice_id": "pNInz6obpgDQGcFmaJgB",
        "google_voice_id": "en-US-Neural2-J",
        "script": """This is Phase C: The Recursive Aggregator. The problem with the agentic web right now is fragmentation. Linear growth is a trap. With Nucleus v0.5, we've achieved the 'Thanos Snap' of connectivity. Mount one parent server, and you instantly inherit the tools of every child below it. Recursive discovery, unified namespacing, and total control. One connection to Nucleus. A thousand tools at your agent's command. Nucleus v0.5—The Netscape Moment for Agents."""
    },
    "A_LONG": {
        "name": "Phase A: Sovereign Context (Long-Form)",
        "duration": "2 minutes",
        "elevenlabs_voice_id": "pNInz6obpgDQGcFmaJgB",
        "google_voice_id": "en-US-Neural2-J",
        "script": """The Agentic Web is built on trust, but today, that trust is fragile. This is Phase A: Sovereign Context. You're watching an agent attempt to access or modify sensitive environment credentials. In any other system, this is a security failure. But with Nucleus v0.5, the control plane intercepts the system call at the transport layer. It doesn't just block the action; it generates a cryptographic audit receipt—a permanent Verisign Pillar in your ledger. Governance isn't a post-hoc check; it's the very infrastructure of the agentic economy. This is zero-trust, verified by code, and enforced by the Sovereign Control Plane."""
    },
    "B_LONG": {
        "name": "Phase B: Engram Recall (Long-Form)",
        "duration": "2 minutes",
        "elevenlabs_voice_id": "pNInz6obpgDQGcFmaJgB",
        "google_voice_id": "en-US-Neural2-J",
        "script": """Context rot is the hidden tax of modern AI. Every new thread is a blank slate—a regression to amnesia. Phase B of Nucleus v0.5 introduces Engram Recall. Every decision your agent makes, every preference it learns, is etched into the Engram Ledger. You're seeing a fresh conversation retrieving a decision made months ago. New thread, new model, different IDE—it doesn't matter. The context persists because it lives in the infrastructure, not the prompt. Ground your agents in the truth of their own history. Build memory that scales."""
    },
    "C_LONG": {
        "name": "Phase C: The Netscape Event (Long-Form)",
        "duration": "2 minutes",
        "elevenlabs_voice_id": "pNInz6obpgDQGcFmaJgB",
        "google_voice_id": "en-US-Neural2-J",
        "script": """Welcome to the Netscape moment for the Internet of Agents. Our ecosystem is fragmented into thousands of silos. Linear integration is a trap. We're launching the Thanos Snap for orchestration. Observe the recursive mounting sequence. Instead of connecting fifty tools to your agent, you mount one parent Nucleus. Instantly, you inherit the unified namespace of every child server below it—Stripe for transactions, Postgres for data, Brave for discovery. It's fractal connectivity. Federated discovery with absolute governance. Stop building silos. Start building the mesh."""
    },
    "master": {
        "name": "5-Minute Master Loom (The Netscape Event)",
        "duration": "5 minutes",
        "elevenlabs_voice_id": "pNInz6obpgDQGcFmaJgB",
        "google_voice_id": "en-US-Neural2-J",
        "script": """Welcome to the Netscape moment for the Agentic Web. 

The problem with today’s AI ecosystem is fragmentation. Every new tool is a new silo. Linear growth is a trap.

Nucleus changes the math. We're launching the 'Thanos Snap' for agents—a recursive control plane that turns chaos into a unified network. 

First, the connectivity. With Nucleus v0.5, we've solved the aggregation problem. You mount one server, and you instantly inherit the tools of every child below it. This is recursive discovery. One connection to Nucleus provides a unified interface to your entire distributed agent network. This is our 'Thanos Snap'—exponential reach with zero overhead.

Next, the governance. This isn't just a router; it's a ledger. If an agent tries to leak a secret or delete a database, Nucleus intercepts, blocks, and logs it. We provide a 'Why-Trace'—cryptographic proof of every decision. This is the 'Verisign Pillar'—the trust layer for the agentic economy.

Finally, the memory. Those decisions aren't transient. They are etched into the Engram Ledger. New thread, new IDE—doesn't matter. The context persists because the governance is baked into the infrastructure, not the prompt.

Nucleus is free, open source, and local-first. We are building the browser for agents. 

To get started, pip install nucleus-mcp. 

Stop building silos. Start building the Internet of Agents."""
    }
}

# --- ALTERNATIVE NARRATIVES (LEGACY / "THANOS SNAP" VERSION) ---
# Use these for more aggressive "Product vs Product" launches.
# 
# LEGACY_DEMO_C_THANOS = """
# This is the Thanos Snap for the Internet of Agents. One connection to Nucleus, 
# and you instantly inherit the tools of every mounted server. 
# Recursive discovery, unified governance, total control.
# """
# 
# LEGACY_MASTER_ORIGINAL = """
# This is the problem. Your agents forget. Every. Single. Time.
# 
# With Nucleus, you write it once. They remember forever. Across threads, across sessions, across IDEs.
# 
# And they can't accidentally leak your secrets. Even if they try.
# 
# Every tool they use—GitHub, Slack, whatever—goes through Nucleus. You control it. You audit it.
# 
# Right now, Nucleus is free and open source. When we launch the Enterprise tier, it'll be $X per month for unlimited agents, unlimited engrams, and compliance-ready audit logs. But for now, it's free.
# 
# To get started, click the link below. Run pip install mcp-server-nucleus, then nucleus-init. That's it. If you get stuck, join the Discord. Link is in the README.
# 
# I know what you're thinking: Does this work with Cursor? Yes. Does it work on Windows? Yes. Do I need to change my MCP config? No, Nucleus wraps your existing setup. Any other questions, drop them in the Discord.
# """

def call_google_tts(text, voice_id, output_path):
    """Call Google Cloud TTS API to generate audio."""
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials_path:
        print("⚠️  Skipping Google TTS: GOOGLE_APPLICATION_CREDENTIALS not set")
        return False
    
    # Expand ~ if present
    credentials_path = os.path.expanduser(credentials_path)
    if not os.path.exists(credentials_path):
        print(f"⚠️  Skipping Google TTS: Credentials file not found at {credentials_path}")
        return False

    try:
        from google.oauth2 import service_account
        print(f"🎙️  Calling Google TTS API for {output_path.name} (Voice: {voice_id})...")
        
        client = texttospeech.TextToSpeechClient()
        
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name=voice_id
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0
        )
        
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        with open(output_path, "wb") as f:
            f.write(response.audio_content)
            
        print(f"✅ Audio generated successfully (Google): {output_path}")
        return True
    except Exception as e:
        print(f"❌ Google TTS API error: {e}")
        return False

def call_elevenlabs(text, voice_id, output_path):
    """Call ElevenLabs API to generate audio."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key or api_key.startswith("<"):
        print("⚠️  Skipping API call: ElevenLabs API key not set in .env")
        return False
    
    print(f"🎙️  Calling ElevenLabs API for {output_path.name}...")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    data = {
        "text": text,
        "model_id": "eleven_turbo_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"✅ Audio generated successfully: {output_path}")
        return True
    else:
        print(f"❌ ElevenLabs API error: {response.status_code} - {response.text}")
        return False

def generate_voiceover(demo_id, output_dir):
    """Generate voiceover script and audio for a specific demo."""
    if demo_id not in DEMO_SCRIPTS:
        print(f"❌ Error: Unknown demo ID '{demo_id}'")
        print(f"Available demos: {', '.join(DEMO_SCRIPTS.keys())}")
        return False
    
    demo = DEMO_SCRIPTS[demo_id]
    txt_output_path = Path(output_dir) / f"demo_{demo_id.lower()}_voiceover.txt"
    mp3_output_path = Path(output_dir) / f"demo_{demo_id.lower()}_voiceover.mp3"
    
    # Create output directory if it doesn't exist
    txt_output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write script to file
    with open(txt_output_path, "w") as f:
        f.write(f"# {demo['name']}\n")
        f.write(f"# Duration: {demo['duration']}\n\n")
        f.write(demo['script'])
    
    print(f"✅ Generated voiceover script: {txt_output_path}")
    
    # Try ElevenLabs first
    audio_success = call_elevenlabs(demo['script'], demo['elevenlabs_voice_id'], mp3_output_path)
    
    # Try Google TTS as fallback
    if not audio_success:
        audio_success = call_google_tts(demo['script'], demo['google_voice_id'], mp3_output_path)
    
    if not audio_success:
        print(f"\n📝 Manual Steps Required:")
        print(f"1. Copy the text from {txt_output_path}")
        print(f"2. Paste into ElevenLabs: https://elevenlabs.io")
        print(f"3. Download the MP3 as: demo_{demo_id.lower()}_voiceover.mp3")
        print(f"4. Save to: {output_dir}/")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Generate Nucleus demo voiceover scripts")
    parser.add_argument("--demo", required=True, choices=list(DEMO_SCRIPTS.keys()),
                       help="Demo ID (A, B, C, or master)")
    parser.add_argument("--output-dir", default="output/demos",
                       help="Output directory for voiceover scripts")
    
    args = parser.parse_args()
    
    print(f"🎙️ Nucleus Demo Voiceover Generator")
    print(f"Demo: {DEMO_SCRIPTS[args.demo]['name']}\n")
    
    success = generate_voiceover(args.demo, args.output_dir)
    
    if success:
        print(f"\n🎬 Ready for ElevenLabs!")
    else:
        exit(1)

if __name__ == "__main__":
    main()
