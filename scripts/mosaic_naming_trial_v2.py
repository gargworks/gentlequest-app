import asyncio
import sys
import os
import json
from pathlib import Path

# Add src to python path
sys.path.append("/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src")

from mcp_server_nucleus.runtime.agent import EphemeralAgent
from mcp_server_nucleus.runtime.llm_client import DualEngineLLM, LLMTier

def load_mega_context():
    """Load foundational documents to eliminate recency bias."""
    base_path = Path("/Users/lokeshgarg/ai-mvp-backend")
    brain_path = base_path / ".brain"
    
    docs = {
        "SOVEREIGN_TESTAMENT": brain_path / "strategy" / "SOVEREIGN_TESTAMENT.md",
        "CLOUD_OPUS_OMNIBUS": base_path / "docs" / "v10_strategy" / "NUCLEUS_CLOUD_OPUS_OMNIBUS.md",
        "BRAND_MANIFESTO": brain_path / "archive" / "rage_session_jan_26" / "BRAND_MANIFESTO.md",
        "GTM_STRATEGY": brain_path / "artifacts" / "strategy" / "NUCLEUS_GTM_OVERHAUL_FINAL_SYNTHESIS_v1.2.md"
    }
    
    context_str = "# FOUNDATIONAL PRODUCT BRIEF & MEGA-SYNTHESIS\n\n"
    for name, path in docs.items():
        if path.exists():
            context_str += f"## {name}\n{path.read_text()}\n\n"
        else:
            print(f"⚠️ Warning: {path} not found.")
            
    return context_str

async def run_agent(persona, intent, mega_context, tools=[]):
    print(f"🚀 Spawning Agent: {persona}...")
    
    # Live Feed Hook
    live_feed_path = Path("/Users/lokeshgarg/ai-mvp-backend/.brain/swarms/trial-naming-mosaic-v2/LIVE_FEED.md")
    live_feed_path.parent.mkdir(parents=True, exist_ok=True)
    with open(live_feed_path, "a") as f:
        f.write(f"\n### 🎙️ {persona} is joining the Boardroom...\n")
        f.write(f"*Goal: {intent}*\n")

    context = {
        "persona": persona,
        "intent": intent,
        "tools": tools,
        "system_prompt": f"""You are {persona}. 
Your goal is: {intent}. 

{mega_context}

CRITICAL RULES:
1. Do NOT hallucinate. Use the foundational context above as your source of truth.
2. Be definitive. We need a name that balances Soul, UX, and Domain Scarcity.
3. If you lack data, state it, but prioritize synthesis from the provided 'Mega-Context'.
""",
        "session_id": "trial-naming-mosaic-v2"
    }
    
    model = DualEngineLLM(job_type="RESEARCH")
    agent = EphemeralAgent(context, model)
    result = await agent.run()
    
    with open(live_feed_path, "a") as f:
        f.write(f"✅ {persona} has submitted their findings.\n")
        
    print(f"✅ {persona} finished.")
    return persona, result

async def main():
    problem = "What name for our product considering brand and domains also as minor factors? We need to finalize the 'Sovereign OS' identity vs just a naming tool."
    
    print(f"🧵 [MOSAIC V2 START] Problem: {problem}")
    
    # Initialize Live Feed
    live_feed_path = Path("/Users/lokeshgarg/ai-mvp-backend/.brain/swarms/trial-naming-mosaic-v2/LIVE_FEED.md")
    live_feed_path.parent.mkdir(parents=True, exist_ok=True)
    live_feed_path.write_text(f"# 🎙️ BOARDROOM LIVE FEED: SUPERCHARGED MOSAIC (V2)\n\n**Problem:** {problem}\n\n---\n")

    # Load Deep Context
    print("🧠 Loading Mega-Context...")
    mega_context = load_mega_context()
    
    # Phase 2: Parallel Deliberation
    tasks = [
        run_agent("Piyush Pandey", f"Analyze cultural resonance and brand 'soul' using the Collective Conscious of the provided docs. Problem: {problem}", mega_context),
        run_agent("Steve Jobs", f"Distill the product down to its essential, impossible simplicity. Apply the 'Sovereign OS' logic. Problem: {problem}", mega_context),
        run_agent("Godaddy Expert", f"Evaluate domain scarcity and handle parity for the 'Sovereign OS' pivot. Problem: {problem}", mega_context)
    ]
    
    print("↔️ Running Council in Parallel (Mosaic)...")
    shard_results = await asyncio.gather(*tasks)
    
    # Save Shards
    shard_dir = Path("/Users/lokeshgarg/ai-mvp-backend/.brain/swarms/trial-naming-mosaic-v2")
    combined_context = ""
    for persona, result in shard_results:
        path = shard_dir / f"shard_{persona.lower().replace(' ', '_')}.md"
        path.write_text(result)
        combined_context += f"### Findings from {persona}:\n{result}\n\n"
    
    # Phase 3: Supercharged Synthesis
    print("🧠 Starting Executive Synthesis with Sequential Thinking...")
    
    with open(live_feed_path, "a") as f:
        f.write("\n---\n## 🏆 FINAL SYNTHESIS: THE VERDICT\n\n")

    synth_intent = f"Synthesize the Council findings into the definitive identity. Resolve the naming paradox. Problem: {problem}"
    synth_context = {
        "persona": "Synthesizer",
        "intent": synth_intent,
        "tools": [],
        "system_prompt": f"""You are the Master Synthesizer. 
Review the parallel findings from the Council. 
Use a high-rigor thinking process to resolve contradictions between Soul, UX, and Scarcity. 

{mega_context}

COUNCIL FINDINGS (MOSAIC):
{combined_context}

GOAL: Provide the ONE definitive name and identity that anchors Nucleus for the next decade.
""",
        "session_id": "trial-naming-mosaic-v2"
    }
    
    synth_model = DualEngineLLM(job_type="CRITICAL")
    synth_agent = EphemeralAgent(synth_context, synth_model)
    final_verdict = await synth_agent.run()
    
    # Final Output
    final_path = shard_dir / "final_verdict.md"
    final_path.write_text(final_verdict)
    
    with open(live_feed_path, "a") as f:
        f.write(final_verdict)
    
    print(f"🏁 [MOSAIC V2 COMPLETE] Final Verdict saved to {final_path}")
    print("\n--- FINAL VERDICT PREVIEW ---")
    print(final_verdict[:500])

if __name__ == "__main__":
    asyncio.run(main())
