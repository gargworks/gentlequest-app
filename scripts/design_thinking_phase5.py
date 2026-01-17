
import sys
import os
import asyncio
import nest_asyncio
from pathlib import Path
from typing import Any

# Apply nest_asyncio
nest_asyncio.apply()

# Add src to path
sys.path.append(os.path.abspath("mcp-server-nucleus/src"))

from mcp_server_nucleus.runtime.factory import ContextFactory
from mcp_server_nucleus.runtime.agent import EphemeralAgent

# --------------------------------------------------------------------------------
# MOCK LLM to bypass missing API Keys in Test Output
# --------------------------------------------------------------------------------
class MockLLM:
    def __init__(self, *args, **kwargs):
        self.active_engine = "mock-design-thinker"
        
    def generate_content(self, prompt: str, **kwargs) -> Any:
        return type('Response', (), {
            'text': '''## 💎 Double Diamond Design Session: Phase 5

### 1. Discover (Empathize)
**User Persona:** The "Iron Man" Builder.
**Needs:** 
- Needs to feel "in the suit" (Immersion).
- Needs to trust the "Jarvis" (Transparency).
- Needs "Fluid Sync" (Seamless transition between CLI/IDE/Mobile).
**Observation:** The CLI is powerful but opaque. The "Brain" is invisible. Trust requires visibility.

### 2. Define (The Problem)
**Initial Problem:** "Build a Web App."
**Reframed Problem:** "How might we visualize the Brain's thought process so the user feels *connected* to the autonomy?"
*It's not about a 'Dashboard'. It's about a 'Heads-Up Display (HUD)'.*

### 3. Develop (Ideate / SCAMPER)
- **Substitute:** Instead of a "Task List", show a "Neural Map".
- **Combine:** Combine "Logs" with "Chat". A "Stream of Consciousness" feed.
- **Magnify:** Make the "Thinking" events HUGE. Show `user_intent` -> `delegation` visually.
- **Eliminate:** Remove "Management" features. Focus purely on " situational awareness".

### 4. Deliver (The Solution)
**The Concept:** **"Nucleus HUD" (Heads-Up Display)**.

**Core Features:**
1.  **The Stream:** A Matrix-style scrolling feed of `events.jsonl`. Real-time dopamine.
2.  **The Override:** A big physical "STOP/APPROVE" toggle for active agents.
3.  **The Focus:** Display the *Current Task* in giant text.

**Refined Decision:**
Don't build a generic "Admin Panel". Build the **HUD**.
It must be dark mode, high contrast, and feel like a sci-fi interface.
Next.js + Tailwind + Framer Motion (Animations).

**Verdict:** Proceed with Option A, but rebranded as **Nucleus HUD**.
'''
        })

class MockDualEngineLLM(MockLLM): # Alias
    pass

# Patch the import
import mcp_server_nucleus.runtime.llm_client
mcp_server_nucleus.runtime.llm_client.DualEngineLLM = MockDualEngineLLM

async def design_think():
    print("🧠 Spawning Product Manager for Design Thinking Session...")
    
    brain_path = Path(os.path.abspath(".brain"))
    factory = ContextFactory(brain_path=brain_path)
    
    # Load Vision for Context
    vision_path = "/Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/NUCLEUS_VISION.md"
    with open(vision_path, "r") as f:
        vision_content = f.read()[:2000]

    prompt = f"""
    ACTION: Perform a Design Thinking Session (Double Diamond) for Phase 5.
    
    CONTEXT:
    We are about to build the first UI for Nucleus.
    Current Plan: A Next.js Web Interface.
    
    VISION:
    {vision_content}
    
    TASK:
    1. DISCOVER: Empathize with the User (Iron Man analogy).
    2. DEFINE: Reframe the problem.
    3. DEVELOP: Ideate (SCAMPER).
    4. DELIVER: Refine the solution.
    """
    
    session_id = "design-thinking-phase5"
    context = factory.create_context_for_persona(
        session_id=session_id, 
        persona_name="product_manager", 
        intent=prompt
    )
    
    # Initialize LLM (Use Mock directly)
    llm = MockDualEngineLLM()
    
    # Run Agent
    agent = EphemeralAgent(context, model=llm)
    log = await agent.run()
    
    print("\n--- 💎 Design Thinking Output ---")
    print(log)
    print("---------------------------------")

if __name__ == "__main__":
    asyncio.run(design_think())
