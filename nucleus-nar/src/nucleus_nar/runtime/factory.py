"""
Nucleus Agent Runtime - Context Factory
========================================
Maps Intent → Persona → Constrained Toolset

This is the "Kernel" of the Agent OS.
"""

from typing import List, Dict, Any, Optional
from .capabilities import Capability


# ============================================================
# PERSONA DEFINITIONS (Extend or override in your project)
# ============================================================

PERSONA_DEFAULT = {
    "name": "Agent",
    "description": "Generic agent with no specific persona.",
    "capabilities": [],
    "system_prompt_fragment": "You are an AI agent. Execute the user's intent."
}

PERSONAS: Dict[str, Dict] = {
    "default": PERSONA_DEFAULT,
}


def classify_intent(message: str) -> str:
    """
    Basic intent classification.
    Override this in your project for custom classification.
    """
    return "default"


def get_persona_for_intent(intent: str) -> Dict:
    """
    Map intent to persona.
    Override this in your project for custom routing.
    """
    return PERSONAS.get(intent, PERSONA_DEFAULT)


class ContextFactory:
    """
    The Compiler.
    Maps Intent → Persona → Toolset.
    
    Usage:
        factory = ContextFactory()
        factory.register(MyCapability())
        context = factory.create_context("session-1", "Deploy the app")
    """
    
    def __init__(self):
        self._registry: Dict[str, Capability] = {}
        self._personas = PERSONAS.copy()

    def register(self, capability: Capability):
        """Register a capability for use by agents."""
        self._registry[capability.name] = capability

    def register_persona(self, name: str, persona: Dict):
        """Register a custom persona."""
        self._personas[name.lower()] = persona

    def create_context(self, session_id: str, intent: str) -> Dict[str, Any]:
        """
        Create an execution context for an agent.
        
        Returns:
            Context dict with:
            - session_id: Unique session identifier
            - intent: Original intent string
            - persona: Selected persona name
            - tools: List of tool definitions
            - capability_instances: List of Capability objects
            - system_prompt: Generated system prompt
        """
        # Step 1: Classify intent
        intent_category = classify_intent(intent)
        
        # Step 2: Get persona
        persona = get_persona_for_intent(intent_category)
        
        # Step 3: Load capabilities
        tools = []
        active_caps_names = []
        active_caps_instances = []
        
        for cap_name in persona.get("capabilities", []):
            cap = self._registry.get(cap_name)
            if cap:
                tools.extend(cap.get_tools())
                active_caps_names.append(cap.name)
                active_caps_instances.append(cap)
        
        return {
            "session_id": session_id,
            "intent": intent,
            "persona": persona["name"],
            "capabilities": active_caps_names,
            "capability_instances": active_caps_instances,
            "tools": tools,
            "tool_count": len(tools),
            "system_prompt": self._generate_system_prompt(intent, persona, active_caps_names)
        }
    
    def _generate_system_prompt(self, intent: str, persona: Dict, caps: List[str]) -> str:
        """Generate persona-specific system prompt."""
        return f"""
        You are an Ephemeral Agent: {persona['name']}.
        
        {persona.get('system_prompt_fragment', '')}
        
        Intent: {intent}
        Active Capabilities: {', '.join(caps) if caps else 'None'}
        
        Execute the intent using the provided tools.
        """
    
    def list_personas(self) -> List[Dict]:
        """List all registered personas."""
        return [
            {"name": p["name"], "description": p.get("description", "")}
            for p in self._personas.values()
        ]
    
    def list_capabilities(self) -> List[str]:
        """List all registered capability names."""
        return list(self._registry.keys())
