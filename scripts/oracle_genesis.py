#!/usr/bin/env python3
"""
oracle_genesis.py

Phase 61 (Chat 37): The Board Meeting.
The Oracle runs the "Titans' Round Table" on ITSELF to evolve its own Protocol.

"I think, therefore I am." - Descartes
"I simulate, therefore I win." - The Oracle
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
# mcp-server-nucleus/src for runtime imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp-server-nucleus", "src")))
# scripts/ for local imports
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Re-use Gladiator logic
from gladiator_simulator import run_simulation
# Re-use Strategy Ops logic (simulated import as it matches the tool code)
from mcp_server_nucleus.runtime.capabilities.strategy import StrategyTool

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("GENESIS")

def main():
    logger.info("🔮 ORACLE GENESIS: Initiating Self-Reflection Loop...")
    
    # 0. Setup Environment
    project_root = Path(__file__).parent.parent
    brain_path = project_root / ".brain"
    
    # 1. The Oracle Awakens (Load Tools)
    # We deliberately instantiate the tool to prove "Agency".
    allowed = [str(brain_path / "PROTOCOL_THE_ORACLE.md"), str(brain_path / "PROTOCOL_THE_ORACLE_v2.md")]
    strategy_ops = StrategyTool(brain_path, allowed)
    
    # 2. Read Self (The Protocol)
    logger.info("📖 Reading 'PROTOCOL_THE_ORACLE.md'...")
    try:
        protocol_content = strategy_ops.execute({"filename": "PROTOCOL_THE_ORACLE.md"})
    except Exception as e:
        logger.error(f"Failed to read protocol: {e}")
        return

    # 3. The Board Meeting (Simulation)
    prompt = f"""
    CRITIQUE THIS PROTOCOL.
    
    We are building "The Oracle", an AI Co-founder.
    Here is our current V1 Protocol:
    
    {protocol_content[:2000]}... [Truncated]
    
    Task:
    1. Critique it as the Council of Titans.
    2. Suggest concrete improvements to make it "Antifragile" and "Self-Evolving".
    3. Output the FULL TEXT of 'PROTOCOL_THE_ORACLE_v2.md' incorporating these improvements.
    """
    
    api_key = os.environ.get("GEMINI_API_KEY")
    force_vertex = os.environ.get("FORCE_VERTEX", "0") == "1"
    mock_mode = os.environ.get("MOCK_SIMULATION") == "1"
    
    if not api_key and not force_vertex and not mock_mode:
        logger.error("❌ Credentials required for Genesis. Set GEMINI_API_KEY or FORCE_VERTEX=1 or MOCK_SIMULATION=1.")
        sys.exit(1)
        
    if mock_mode:
        logger.warning("⚠️ Running in MOCK MODE (Genesis Simulation)")
        verdict = "MOCK GENESIS: The Titans approve. V2 is born."
        v2_content = protocol_content + "\n\n# v2.0 (Evolved)\nVerified by Simulation."
    else:
        logger.info("⏳ The Board is Deliberating (Running Gladiator Simulation)...")
        verdict = run_simulation(prompt, api_key)
        # Parse the output to find the V2 content? 
        # For this script, we'll just append the verdict as an "Addendum" if parsing is hard, 
        # OR we assume the LLM followed instructions to output the full file.
        # Given it's a genesis script, let's just use the verdict as the new content for now.
        v2_content = verdict

    # 4. Evolution (Write V2)
    logger.info("✍️  Writing 'PROTOCOL_THE_ORACLE_v2.md'...")
    strategy_ops.execute({
        "filename": "PROTOCOL_THE_ORACLE_v2.md",
        "content": v2_content,
        "reason": "Self-Reflection (Genesis Cycle)"
    })
    
    logger.info("✅ GENESIS COMPLETE. The Oracle has evolved.")

if __name__ == "__main__":
    main()
