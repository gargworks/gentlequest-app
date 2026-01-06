"""
Nucleus Agent Runtime - Ephemeral Agent
========================================
The disposable execution context that runs until completion.
"""

from typing import Dict, Any, List, Optional
import json
import re


class EphemeralAgent:
    """
    The Runtime.
    A disposable agent that executes a single intent and terminates.
    
    Supports two modes:
    - LLM Mode (Smart): Uses an LLM model for reasoning and tool selection
    - Heuristic Mode (Fast): Uses keyword matching for quick execution
    """
    
    def __init__(self, context: Dict[str, Any], model: Any = None):
        """
        Initialize an ephemeral agent.
        
        Args:
            context: Context from ContextFactory.create_context()
            model: Optional LLM model (e.g., Gemini, OpenAI). If None, uses heuristic mode.
        """
        self.context = context
        self.model = model
        self.history: List[str] = []

    async def run(self) -> str:
        """
        Execute the agent loop.
        
        Returns:
            Execution log as string
        """
        log = []
        log.append(f"--- Spawning Ephemeral Agent ({self.context.get('persona', 'Unknown')}) ---")
        log.append(f"Intent: {self.context['intent']}")
        
        if self.model:
            return await self._run_llm(log)
        else:
            return self._run_heuristic(log)

    async def _run_llm(self, log: List[str]) -> str:
        """
        LLM-driven execution with tool calling.
        """
        log.append(">> Mode: LLM (Smart)")
        
        # Build prompt
        system_prompt = self.context.get('system_prompt', "You are an agent.")
        tools_desc = "\n".join([f"- {t['name']}: {t['description']}" for t in self.context.get('tools', [])])
        
        full_prompt = f"""{system_prompt}

AVAILABLE TOOLS:
{tools_desc}

RULES:
1. You MUST call a tool to perform actions.
2. Output a JSON block with "tool" and "args" to call a tool.
   Format: 
   ```json
   {{
     "tool": "tool_name",
     "args": {{ ... }}
   }}
   ```
"""
        
        try:
            response = self.model.generate_content(full_prompt)
            text = response.text
            log.append(f"[LLM Output]: {text[:200]}...")
            
            # Parse tool call
            match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
            
            if match:
                tool_call = json.loads(match.group(1))
                tool_name = tool_call.get("tool")
                args = tool_call.get("args", {})
                
                log.append(f">> Tool detected: {tool_name}")
                result = self._execute_tool(tool_name, args)
                log.append(f"[Tool Result]: {result}")
            else:
                log.append("No tool call detected in LLM output.")

        except Exception as e:
            log.append(f"LLM Error: {e}")
            
        log.append("--- Agent Terminated ---")
        return "\n".join(log)

    def _run_heuristic(self, log: List[str]) -> str:
        """
        Fast heuristic-based execution without LLM.
        Override this in subclasses for custom behavior.
        """
        log.append(">> Mode: Heuristic (Fast)")
        log.append("No heuristic rules defined for this intent.")
        log.append("--- Agent Terminated ---")
        return "\n".join(log)

    def _execute_tool(self, tool_name: str, args: Dict) -> str:
        """Execute a tool using the registered capabilities."""
        caps = self.context.get('capability_instances', [])
        for cap in caps:
            tool_names = [t['name'] for t in cap.get_tools()]
            if tool_name in tool_names:
                return cap.execute_tool(tool_name, args)
        
        return f"Error: Tool '{tool_name}' not found in active capabilities."
