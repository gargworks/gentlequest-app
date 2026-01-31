from typing import Dict, Any, List
from .. import commitment_ledger
from pathlib import Path
import os
import json

# Gemini types imported dynamically or duck-typed via DualEngineLLM

def get_brain_path_internal() -> Path:
    """Helper to get brain path inside runtime"""
    return Path(os.getenv("NUCLEAR_BRAIN_PATH", "/Users/lokeshgarg/ai-mvp-backend/.brain"))

class DecisionMade:
    """
    NOP v3.0: The "Why" Link.
    Represents a sovereign decision with cryptographic anchoring.
    """
    def __init__(self, decision_id: str, reasoning: str, context_hash: str, confidence: float = 1.0):
        self.decision_id = decision_id
        self.reasoning = reasoning
        self.context_hash = context_hash
        self.confidence = confidence
        self.timestamp = None # Set by emitter

class ActionRequested:
    """
    NOP v3.0: The "What" Linked to "Why".
    """
    def __init__(self, action_id: str, decision_id: str, tool_name: str, args: Dict):
        self.action_id = action_id
        self.decision_id = decision_id
        self.tool_name = tool_name
        self.args = args

class EphemeralAgent:
    """
    The Runtime.
    A disposable agent that runs until completion.
    MDR_005: Supports both LLM-driven (Smart) and Heuristic (Fast) modes.
    MDR_002: Implements Active Correction (Critic) in LLM mode.
    """
    def __init__(self, context: Dict[str, Any], model: Any = None):
        self.context = context
        self.model = model
        self.history: List[str] = []
        self.active = True

    async def run(self) -> str:
        """
        Execute the agent loop.
        Returns execution log.
        """
        # MDR_010: Auto-record telemetry
        try:
             brain_path = get_brain_path_internal()
             commitment_ledger.record_interaction(brain_path)
        except Exception:
             pass 

        log = []
        log.append(f"--- Spawning Ephemeral Agent ({self.context['persona']}) ---")
        log.append(f"Intent: {self.context['intent']}")
        
        if self.model:
            return await self._run_llm(log)
        else:
            return self._run_heuristic(log)

    async def _run_llm(self, log: List[str]) -> str:
        """
        MDR_005 / MDR_002: Real LLM Execution Loop with Critic & Multi-Turn Support
        """
        log.append(">> Mode: LLM (Smart)")
        
        # 1. Build Base Prompt
        system_prompt = self.context.get('system_prompt', "You are an agent.")
        
        tools_desc = []
        for t in self.context['tools']:
             tools_desc.append(f"### {t['name']}")
             tools_desc.append(f"Description: {t['description']}")
             tools_desc.append(f"Parameters: {json.dumps(t.get('parameters', {}), indent=2)}")
             tools_desc.append("")
        
        tools_block = "\n".join(tools_desc)
        
        base_prompt = f"""{system_prompt}
        
AVAILABLE TOOLS:
{tools_block}

CRITICAL RULES (MDR_002):
1. You MUST call a tool to perform actions.
2. Do not just say you did it.
3. Output a JSON block with "tool" and "args" to call a tool.
   Format: 
   ```json
   {{
     "tool": "tool_name",
     "args": {{ ... }}
   }}
   ```
"""
        # 2. Multi-Turn Loop
        max_turns = 5
        turn = 0
        current_history = []
        
        while turn < max_turns:
            turn += 1
            log.append(f"\n--- Turn {turn}/{max_turns} ---")
            
            # Construct full prompt with history
            history_str = "\n\n".join(current_history)
            if history_str:
                turn_prompt = f"{base_prompt}\n\n# EXECUTION HISTORY\n{history_str}\n\nNEXT STEP:"
            else:
                turn_prompt = base_prompt

            try:
                response = self.model.generate_content(turn_prompt)
                
                # Defensive: Handle None or malformed response
                if response is None:
                    log.append("[LLM Error]: Response is None (quota/network issue)")
                    current_history.append("SYSTEM: LLM returned no response. Retrying...")
                    continue
                
                text = getattr(response, 'text', None)
                if text is None:
                    # Try to extract from candidates
                    if hasattr(response, 'candidates') and response.candidates:
                        text = response.candidates[0].content.parts[0].text if response.candidates[0].content.parts else ""
                    else:
                        log.append("[LLM Error]: Response has no text content")
                        current_history.append("SYSTEM: LLM response malformed. Retrying...")
                        continue
                
                log.append(f"[LLM Output]: {text[:500]}...")
                current_history.append(f"AI: {text}")

                
                # 3. Parse and Execute
                import re
                match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
                
                if match:
                    tool_call = json.loads(match.group(1))
                    tool_name = tool_call.get("tool")
                    args = tool_call.get("args", {})
                    
                    log.append(f">> Tool detected: {tool_name}")
                    result = self._execute_tool(tool_name, args)
                    log.append(f"[Tool Result]: {str(result)[:1000]}...")
                    current_history.append(f"TOOL_RESULT ({tool_name}): {result}")
                else:
                    # No tool call - check if it's the final answer
                    if self.context['persona'] == 'Synthesizer' or "MISSION_COMPLETE" in text or "FINAL_ANSWER" in text:
                         log.append("✅ Mission complete signal detected.")
                         
                         # GHOST COMPLETION FIX: Persist mission summary BEFORE returning
                         try:
                             brain_path = get_brain_path_internal()
                             import time as _time
                             timestamp = int(_time.time())
                             session_id = self.context.get('session_id', f'unknown_{timestamp}')
                             
                             mission_dir = brain_path / "swarms" / session_id
                             mission_dir.mkdir(parents=True, exist_ok=True)
                             
                             # Write summary.md
                             summary_path = mission_dir / "summary.md"
                             summary_content = f"""# Mission Summary

**Persona:** {self.context['persona']}
**Intent:** {self.context['intent']}
**Completed At:** {_time.strftime('%Y-%m-%dT%H:%M:%S')}
**Turns Used:** {turn}/{max_turns}

## Final Output

{text}

## Execution Log

```
{chr(10).join(log[-10:])}
```
"""
                             summary_path.write_text(summary_content)
                             
                             # Write mission_log.json
                             log_path = mission_dir / "mission_log.json"
                             mission_data = {
                                 "session_id": session_id,
                                 "persona": self.context['persona'],
                                 "intent": self.context['intent'],
                                 "completed_at": _time.strftime('%Y-%m-%dT%H:%M:%S'),
                                 "turns_used": turn,
                                 "max_turns": max_turns,
                                 "history": current_history[-10:],
                                 "status": "COMPLETE"
                             }
                             log_path.write_text(json.dumps(mission_data, indent=2))
                             
                             log.append(f"💾 Mission persisted to {mission_dir}")
                         except Exception as persist_error:
                             log.append(f"⚠️ Persistence warning: {persist_error}")
                         
                         break
                         
                    # MDR_002: THE ACTIVE CRITIC Intervention
                    log.append("⚠️ [CRITIC INTERVENTION] No tool call detected.")
                    
                    critique_prompt = f"{turn_prompt}\n\nSYSTEM CRITIC: You did not call a tool! You MUST output a JSON tool call block or mark MISSION_COMPLETE if finished."
                    response_retry = self.model.generate_content(critique_prompt)
                    text_retry = response_retry.text
                    log.append(f"[LLM Retry Output]: {text_retry[:500]}...")
                    current_history.append(f"AI (Retry): {text_retry}")
                    
                    match_retry = re.search(r'```json\s*(\{.*?\})\s*```', text_retry, re.DOTALL)
                    if match_retry:
                        tool_call = json.loads(match_retry.group(1))
                        tool_name = tool_call.get("tool")
                        args = tool_call.get("args", {})
                        
                        log.append(f">> Tool detected (after critique): {tool_name}")
                        result = self._execute_tool(tool_name, args)
                        log.append(f"[Tool Result]: {str(result)[:1000]}...")
                        current_history.append(f"TOOL_RESULT ({tool_name}): {result}")
                    else:
                         # Bug 5 Fix: Persist findings even on tool-call failure
                         log.append("❌ Agent failed to call tool after critique.")
                         
                         # Save orphan output before terminating
                         try:
                             brain_path = get_brain_path_internal()
                             orphan_dir = brain_path / "swarms" / "orphan_outputs"
                             orphan_dir.mkdir(parents=True, exist_ok=True)
                             
                             import time as _time
                             timestamp = int(_time.time())
                             output_file = orphan_dir / f"critic_failure_{self.context['persona']}_{timestamp}.md"
                             
                             findings = f"""# Orphan Agent Output

**Persona:** {self.context['persona']}
**Intent:** {self.context['intent']}
**Timestamp:** {timestamp}

## Agent Analysis (Not Persisted via Tool)

{text_retry}

## Execution History

```
{chr(10).join(current_history[-5:])}
```
"""
                             output_file.write_text(findings)
                             log.append(f"💾 Orphan output saved to {output_file}")
                         except Exception as persist_error:
                             log.append(f"⚠️ Failed to save orphan output: {persist_error}")
                         
                         break

            except Exception as e:
                log.append(f"LLM Error: {e}")
                break
                
        return "\n".join(log)

    def _run_heuristic(self, log: List[str]) -> str:
        """Legacy Heuristic Mode"""
        log.append(">> Mode: Heuristic (Fast)")
        
        full_intent = self.context['intent'].lower()
        executed = False
        
        # 1. BRAIN OPS
        if "brain" in full_intent or "task" in full_intent or "scan" in full_intent:
             # Heuristic mapping for heuristic mode
             pass 

        # 2. RENDER OPS
        if "deploy" in full_intent or "check" in full_intent or "list" in full_intent:
             if "render_list_services" in [t['name'] for t in self.context['tools']] and ("list" in full_intent or "check" in full_intent):
                 result = self._execute_tool("render_list_services", {})
                 log.append(">> [Heuristic] Calling render_list_services...")
                 log.append(result)
                 executed = True
             elif "render_deploy_service" in [t['name'] for t in self.context['tools']] and "deploy" in full_intent:
                 # Extract Service ID (Mock logic for now, or assume args provided in context?)
                 # For now, just list to be safe if no ID found
                 result = self._execute_tool("render_list_services", {}) 
                 log.append(">> [Heuristic] Intent detected deploy, listing services first...")
                 log.append(result)
                 executed = True

        if not executed:
             log.append("No heuristic action map found.")
             
        log.append("--- Agent Terminated ---")
        return "\n".join(log)

    def _execute_tool(self, tool_name: str, args: Dict) -> str:
        # Find the capability that owns this tool
        caps = self.context.get('capability_instances', [])
        for cap in caps:
            tools = [t['name'] for t in cap.get_tools()]
            if tool_name in tools:
                return cap.execute_tool(tool_name, args)
        
        return f"Error: Tool {tool_name} implementation not found."
