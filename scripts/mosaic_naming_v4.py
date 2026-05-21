import asyncio
import sys
import os
import json
from pathlib import Path

# Add src to python path (Portability Pass: Slice-1)
_root = Path(__file__).parent.parent
_src_path = os.environ.get("NUCLEUS_SRC_PATH", str(_root / "mcp-server-nucleus" / "src"))
if _src_path not in sys.path:
    sys.path.append(_src_path)

from mcp_server_nucleus.runtime.agent import EphemeralAgent
from mcp_server_nucleus.runtime.llm_client import DualEngineLLM, LLMTier

def load_mega_context():
    """Load foundational documents to eliminate recency bias."""
    from mcp_server_nucleus.runtime.common import get_brain_path
    brain_path = get_brain_path()
    base_path = brain_path.parent
    
    docs = {
        "SOVEREIGN_TESTAMENT": brain_path / "strategy" / "SOVEREIGN_TESTAMENT.md",
        "CLOUD_OPUS_OMNIBUS": base_path / "docs" / "v10_strategy" / "NUCLEUS_CLOUD_OPUS_OMNIBUS.md",
        "BRAND_MANIFESTO": brain_path / "archive" / "rage_session_jan_26" / "BRAND_MANIFESTO.md"
    }
    
    context_str = "# FOUNDATIONAL PRODUCT BRIEF & TITAN CONTEXT\n\n"
    for name, path in docs.items():
        if path.exists():
            context_str += f"## {name}\n{path.read_text()}\n\n"
            
    return context_str

async def run_agent(persona, intent, mega_context, tools=[]):
    print(f"🚀 Spawning Agent: {persona}...")
    
    # Live Feed Hook (Portability Pass: Slice-1)
    from mcp_server_nucleus.runtime.common import get_brain_path
    live_feed_path = get_brain_path() / "swarms" / "trial-naming-mosaic-v4" / "LIVE_FEED.md"
    live_feed_path.parent.mkdir(parents=True, exist_ok=True)
    with open(live_feed_path, "a") as f:
        f.write(f"\n### 🔥 {persona} (The Titan) has entered the Boardroom...\n")
        f.write(f"*Strategic Directive: {intent}*\n")

    context = {
        "persona": persona,
        "intent": intent,
        "tools": tools,
        "system_prompt": f"""You are {persona}. 
Directive: {intent}

{mega_context}

TITAN RULES:
1. Don't be a consultant. Be a Founder. 
2. Steve Jobs: Focus on impossible simplicity. 
3. Bill Gates: Focus on the "Platform" moat (Dominance). 
4. Zuck: Focus on engagement, friction-less sharing, and scale.
5. Every Titan must provide a TABLE of 5-7 names and their corresponding 'Sovereign Scenario'. 
""",
        "session_id": "trial-naming-mosaic-v4"
    }
    
    model = DualEngineLLM(job_type="RESEARCH")
    agent = EphemeralAgent(context, model)
    result = await agent.run()
    
    shard_dir = Path("/Users/lokeshgarg/ai-mvp-backend/.brain/swarms/trial-naming-mosaic-v4")
    shard_dir.mkdir(parents=True, exist_ok=True)
    path = shard_dir / f"shard_{persona.lower().replace(' ', '_')}.md"
    path.write_text(result)
    
    with open(live_feed_path, "a") as f:
        f.write(f"✅ {persona} submitted their Titan Brief.\n")
        
    print(f"✅ {persona} finished.")
    return persona, result

async def main():
    problem = "Finalize the NAMING identity for the Sovereign OS. Resolve the 'Nucleus' vs 'Testament' vs 'Engram' tension from a Founder perspective."
    
    print(f"🧵 [MOSAIC V4 START] The Titan Council: {problem}")
    mega_context = load_mega_context()
    
    # Initialize Live Feed
    live_feed_path = Path("/Users/lokeshgarg/ai-mvp-backend/.brain/swarms/trial-naming-mosaic-v4/LIVE_FEED.md")
    live_feed_path.parent.mkdir(parents=True, exist_ok=True)
    live_feed_path.write_text(f"# 🔥 TITAN BOARDROOM LIVE FEED (V4)\n\n**Problem:** {problem}\n\n----- \n")

    # Phase 2: Parallel Titan Deliberation
    tasks = [
        run_agent("Steve Jobs", f"Distill the Soul. Simplicity over features. Problem: {problem}", mega_context),
        run_agent("Bill Gates", f"Build the Platform. Focus on the 'OS' as the utility moat. Problem: {problem}", mega_context),
        run_agent("Mark Zuckerberg", f"Scale the Network. Focus on engagement and sharing context. Problem: {problem}", mega_context)
    ]
    
    print("↔️ Running Titans in Parallel (Mosaic)...")
    shard_results = await asyncio.gather(*tasks)
    
    # Phase 3: Supercharged Synthesis
    print("🧠 Starting Final Titan Synthesis...")
    
    combined_shards = ""
    for persona, result in shard_results:
        combined_shards += f"### {persona}'s Titan Brief:\n{result}\n\n"

    synth_intent = "Consolidate the Titan briefs into the definitive 'Identity Ledger'. Choose THE name."
    synth_context = {
        "persona": "Synthesizer",
        "intent": synth_intent,
        "tools": [],
        "system_prompt": f"""You are the Master Synthesizer. 
Consolidate the Titan deliberations. Resolve the tension between Simplicity (Jobs), Platform (Gates), and Scale (Zuck).

{mega_context}

TITAN DELIBERATION:
{combined_shards}

GOAL: Output the final MASTER NAMING LEDGER V4. Pick the winner.
""",
        "session_id": "trial-naming-mosaic-v4"
    }
    
    synth_model = DualEngineLLM(job_type="CRITICAL")
    synth_agent = EphemeralAgent(synth_context, synth_model)
    final_verdict = await synth_agent.run()
    
    final_path = Path("/Users/lokeshgarg/ai-mvp-backend/.brain/swarms/trial-naming-mosaic-v4/TITAN_VERDICT.md")
    final_path.write_text(final_verdict)
    
    with open(live_feed_path, "a") as f:
        f.write("\n---\n## 🏆 THE TITAN VERDICT\n\n")
        f.write(final_verdict)
    
    print(f"🏁 [MOSAIC V4 COMPLETE] Final Verdict saved to {final_path}")

if __name__ == "__main__":
    asyncio.run(main())
