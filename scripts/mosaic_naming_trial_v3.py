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
        "BRAND_MANIFESTO": brain_path / "archive" / "rage_session_jan_26" / "BRAND_MANIFESTO.md"
    }
    
    context_str = "# FOUNDATIONAL PRODUCT BRIEF\n\n"
    for name, path in docs.items():
        if path.exists():
            context_str += f"## {name}\n{path.read_text()}\n\n"
            
    return context_str

async def run_agent(persona, intent, mega_context, tools=[]):
    print(f"🚀 Spawning Agent: {persona}...")
    
    context = {
        "persona": persona,
        "intent": intent,
        "tools": tools,
        "system_prompt": f"""You are {persona}. 
Goal: {intent}. 

{mega_context}

CRITICAL INSTRUCTIONS:
1. Provide a TABLE of 5-10 specific name candidates.
2. For each name, provide exactly ONE 'Usage Scenario' (e.g. A user in 2027 asking about their tax records).
3. Do NOT provide abstract philosophy. Show me the NAMES.
4. Categorize names into: 'Soulful', 'Technical', 'Short/Punchy'.
""",
        "session_id": "trial-naming-mosaic-v3"
    }
    
    model = DualEngineLLM(job_type="RESEARCH")
    agent = EphemeralAgent(context, model)
    result = await agent.run()
    
    shard_dir = Path("/Users/lokeshgarg/ai-mvp-backend/.brain/swarms/trial-naming-mosaic-v3")
    shard_dir.mkdir(parents=True, exist_ok=True)
    path = shard_dir / f"shard_{persona.lower().replace(' ', '_')}.md"
    path.write_text(result)
    
    print(f"✅ {persona} finished.")
    return persona, result

async def main():
    problem = "Finalize the tactical list of names and scenarios for the 'Sovereign OS' product. We need 10+ options across different vibes."
    
    print(f"🧵 [MOSAIC V3 START] Problem: {problem}")
    mega_context = load_mega_context()
    
    # Phase 2: Parallel Deliberation (Tactical)
    tasks = [
        run_agent("Piyush Pandey", f"Generate 5-10 names with HIGH CULTURAL RESONANCE. Pair each with a scenario. Problem: {problem}", mega_context),
        run_agent("Steve Jobs", f"Generate 5-10 ESSENTIAL, SIMPLE names. Pair each with a scenario showing impossible simplicity. Problem: {problem}", mega_context),
        run_agent("McKinsey Consultant", f"Generate 5-10 CATEGORY-DEFINING names for the Sovereign OS market. Problem: {problem}", mega_context)
    ]
    
    print("↔️ Running Council in Parallel (Mosaic Tactical)...")
    await asyncio.gather(*tasks)
    
    # Phase 3: Supercharged Synthesis
    print("🧠 Starting Final Naming Ledger Synthesis...")
    
    # Read shards for synthesis
    shard_dir = Path("/Users/lokeshgarg/ai-mvp-backend/.brain/swarms/trial-naming-mosaic-v3")
    shards = ""
    for p in ["Piyush Pandey", "Steve Jobs", "McKinsey Consultant"]:
        p_path = shard_dir / f"shard_{p.lower().replace(' ', '_')}.md"
        if p_path.exists():
            shards += f"### {p} Shard:\n{p_path.read_text()}\n\n"

    synth_intent = "Synthesize all naming candidates into a single MASTER LEDGER. Rank the top 10. Show the scenario for the #1 pick."
    synth_context = {
        "persona": "Synthesizer",
        "intent": synth_intent,
        "tools": [],
        "system_prompt": f"""You are the Master Synthesizer. 
Review these naming candidates. Create a consolidated MASTER LEDGER table.

{mega_context}

SHARDS:
{shards}

GOAL: Output a clean, ranked list of 10 names with their scenarios.
""",
        "session_id": "trial-naming-mosaic-v3"
    }
    
    synth_model = DualEngineLLM(job_type="CRITICAL")
    synth_agent = EphemeralAgent(synth_context, synth_model)
    final_verdict = await synth_agent.run()
    
    final_path = shard_dir / "MASTER_NAMING_LEDGER.md"
    final_path.write_text(final_verdict)
    
    print(f"🏁 [MOSAIC V3 COMPLETE] Master Ledger saved to {final_path}")

if __name__ == "__main__":
    asyncio.run(main())
