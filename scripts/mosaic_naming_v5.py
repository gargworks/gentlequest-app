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
    base_path = Path("/Users/lokeshgarg/ai-mvp-backend")
    brain_path = base_path / ".brain"
    
    docs = {
        "SOVEREIGN_TESTAMENT": brain_path / "strategy" / "SOVEREIGN_TESTAMENT.md",
        "TITAN_VERDICT": brain_path / "swarms" / "trial-naming-mosaic-v4" / "TITAN_VERDICT.md"
    }
    
    context_str = "# FOUNDATIONAL CONTEXT\n\n"
    for name, path in docs.items():
        if path.exists():
            context_str += f"## {name}\n{path.read_text()}\n\n"
            
    return context_str

# GROUND TRUTH AUDIT (V5)
AUDIT_DATA = """
### REAL-WORLD AVAILABILITY AUDIT (JAN 26)
- NucleusSovereign.com: AVAILABLE
- EngramLedger.com: AVAILABLE
- NSOS.io: TAKEN
- @NucleusSovereign (X/YT): AVAILABLE
- @EngramLedger (X/YT): AVAILABLE
- @NSOS (X/YT): TAKEN
"""

async def run_agent(persona, intent, mega_context, tools=[]):
    print(f"🚀 Spawning Agent: {persona}...")
    
    context = {
        "persona": persona,
        "intent": intent,
        "tools": tools,
        "system_prompt": f"""You are {persona}. 
Goal: {intent}

{mega_context}

{AUDIT_DATA}

TACTICAL AUDIT RULES:
1. Don't speculate on availability. Use the AUDIT_DATA provided.
2. GoDaddy Expert: Focus on the "Capture the Flag" (Securing the available names).
3. Product Designer: Focus on the "User UI" (How do these names look in the app?).
4. Growth Hacker: Focus on "Launch Velocity" (Handover parity).
""",
        "session_id": "trial-naming-mosaic-v5"
    }
    
    model = DualEngineLLM(job_type="RESEARCH")
    agent = EphemeralAgent(context, model)
    result = await agent.run()
    
    shard_dir = Path("/Users/lokeshgarg/ai-mvp-backend/.brain/swarms/trial-naming-mosaic-v5")
    shard_dir.mkdir(parents=True, exist_ok=True)
    path = shard_dir / f"shard_{persona.lower().replace(' ', '_')}.md"
    path.write_text(result)
    
    print(f"✅ {persona} finished.")
    return persona, result

async def main():
    problem = "Finalize the TACTICAL LAUNCH MANIFESTO. Given the availability of NucleusSovereign and EngramLedger, how do we deploy the brand across web, social, and app UI?"
    
    print(f"🧵 [MOSAIC V5 START] The Tactical Audit: {problem}")
    mega_context = load_mega_context()
    
    # Phase 2: Parallel Deliberation
    tasks = [
        run_agent("GoDaddy Expert", f"Plan the domain acquisition and redirection strategy. Problem: {problem}", mega_context),
        run_agent("Product Designer", f"Designing the 'User' touchpoints. Where does 'Nucleus Sovereign' live vs 'Engram Ledger'? Problem: {problem}", mega_context),
        run_agent("Growth Hacker", f"Plan the 'Social Blitz'. Handle parity and handle-squatting defense. Problem: {problem}", mega_context)
    ]
    
    print("↔️ Running Tactical Council in Parallel...")
    shard_results = await asyncio.gather(*tasks)
    
    # Phase 3: Supercharged Synthesis
    print("🧠 Starting Final Launch Manifesto Synthesis...")
    
    combined_shards = ""
    for persona, result in shard_results:
        combined_shards += f"### {persona}'s Tactical Note:\n{result}\n\n"

    synth_intent = "Consolidate the Tactical Audit into the LAUNCH MANIFESTO. Resolve all 'User/Domain' tension."
    synth_context = {
        "persona": "Synthesizer",
        "intent": synth_intent,
        "tools": [],
        "system_prompt": f"""You are the Master Synthesizer. 
Consolidate the tactical notes into a single, definitive LAUNCH MANIFESTO.

{mega_context}
{AUDIT_DATA}

TACTICAL NOTES:
{combined_shards}

GOAL: Provide the 0-1 minute launch checklist for Domains, Handles, and App UI.
""",
        "session_id": "trial-naming-mosaic-v5"
    }
    
    synth_model = DualEngineLLM(job_type="CRITICAL")
    synth_agent = EphemeralAgent(synth_context, synth_model)
    final_verdict = await synth_agent.run()
    
    final_path = Path("/Users/lokeshgarg/ai-mvp-backend/.brain/swarms/trial-naming-mosaic-v5/LAUNCH_MANIFESTO.md")
    final_path.write_text(final_verdict)
    
    print(f"🏁 [MOSAIC V5 COMPLETE] Final Launch Manifesto saved to {final_path}")

if __name__ == "__main__":
    asyncio.run(main())
