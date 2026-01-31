import asyncio
import sys
import os
import json
from pathlib import Path

# Add src to python path
sys.path.append("/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src")

from mcp_server_nucleus.runtime.agent import EphemeralAgent
from mcp_server_nucleus.runtime.llm_client import DualEngineLLM, LLMTier

async def run_agent(persona, intent, tools=[]):
    print(f"🚀 Spawning Agent: {persona}...")
    context = {
        "persona": persona,
        "intent": intent,
        "tools": tools,
        "system_prompt": f"You are {persona}. Your goal is: {intent}. Be sharp, professional, and definitive.",
        "session_id": "trial-naming-mosaic"
    }
    model = DualEngineLLM(job_type="RESEARCH")
    agent = EphemeralAgent(context, model)
    result = await agent.run()
    print(f"✅ {persona} finished.")
    return persona, result

async def main():
    problem = "What name for our product considering brand and domains also as minor factors?"
    
    print(f"🧵 [MOSAIC START] Problem: {problem}")
    
    # Phase 2: Parallel Deliberation
    tasks = [
        run_agent("Piyush Pandey", f"Analyze human/cultural resonance for: {problem}"),
        run_agent("Steve Jobs", f"Analyze product soul and UX simplicity for: {problem}"),
        run_agent("Godaddy Expert", f"Analyze domain availability and keyword brevity for: {problem}")
    ]
    
    print("↔️ Running Council in Parallel...")
    shard_results = await asyncio.gather(*tasks)
    
    # Save Shards
    shard_dir = Path("/Users/lokeshgarg/ai-mvp-backend/.brain/swarms/trial-naming-mosaic")
    shard_dir.mkdir(parents=True, exist_ok=True)
    
    combined_context = ""
    for persona, result in shard_results:
        path = shard_dir / f"shard_{persona.lower().replace(' ', '_')}.md"
        path.write_text(result)
        combined_context += f"### Findings from {persona}:\n{result}\n\n"
    
    # Phase 3: Supercharged Synthesis
    print("🧠 Starting Executive Synthesis...")
    
    synth_intent = f"Synthesize the following Council findings into the definitive product name. Problem: {problem}"
    synth_context = {
        "persona": "Synthesizer",
        "intent": synth_intent,
        "tools": [],
        "system_prompt": f"""You are the Master Synthesizer. 
Review the parallel findings from the Council. 
Use a high-rigor step-by-step thinking process to resolve contradictions. 
Provide a final recommendation that perfectly balances Soul, UX, and Scarcity (Domain).

COUNCIL FINDINGS:
{combined_context}
""",
        "session_id": "trial-naming-mosaic"
    }
    
    synth_model = DualEngineLLM(job_type="CRITICAL")
    synth_agent = EphemeralAgent(synth_context, synth_model)
    final_verdict = await synth_agent.run()
    
    # Final Output
    final_path = shard_dir / "final_verdict.md"
    final_path.write_text(final_verdict)
    
    print(f"🏁 [MOSAIC COMPLETE] Final Verdict saved to {final_path}")
    print("\n--- FINAL VERDICT PREVIEW ---")
    print(final_verdict[:500])

if __name__ == "__main__":
    asyncio.run(main())
