import os
import google.generativeai as genai
import structlog
from typing import List, Dict, Any
import json

logger = structlog.get_logger()

# Configure Gemini
GENAI_KEY = os.getenv("GEMINI_API_KEY")
if GENAI_KEY:
    genai.configure(api_key=GENAI_KEY)

class AIInsightsService:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    async def extract_anrum(self, interview_text: str) -> List[Dict[str, Any]]:
        """
        Extracts ANRUM insights from interview notes.
        Returns a list of dicts: [{attitude, need, response, use_case, mental_model, quote}]
        """
        prompt = f"""
        You are an expert Design Research Analyst.
        Analyze the following interview notes and extract structured ANRUM insights.
        
        CRITERIA:
        - Attitude: How they feel/think.
        - Need: Underlying unmet goal.
        - Response: Immediate reaction/behavior.
        - Use Case: Specific context of use.
        - Mental Model: Their belief system about the problem.
        
        OUTPUT FORMAT:
        Strict JSON Array of objects. No markdown formatting.
        Keys: "category" (one of A,N,R,U,M), "insight", "quote".
        
        INPUT TEXT:
        {interview_text}
        """
        
        try:
            response = await self.model.generate_content_async(prompt)
            text = response.text.replace("```json", "").replace("```", "").strip()
            insights = json.loads(text)
            return insights
        except Exception as e:
            logger.error("llm_extraction_failed", error=str(e))
            # Fallback/Empty for resilience
            return []

    async def generate_personas(
        self, 
        interviews_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Synthesizes personas from multiple interviews.
        Input: List of dicts with 'id', 'notes', 'insights'.
        """
        if not interviews_data:
            return []

        # Prepare context for LLM
        context_str = json.dumps(interviews_data, indent=2)

        prompt = f"""
        You are a Lead Design Strategist. 
        Synthesize the following research interview data into 3-5 distinct User Personas.
        Cluster users based on shared behaviors, motivations, and frustrations (not just demographics).

        INPUT DATA (JSON):
        {context_str}

        OUTPUT FORMAT:
        Strict JSON Array of Persona objects. No markdown.
        Schema:
        - name (Creative string)
        - age (Appropriate integer)
        - context (Brief bio/role)
        - goals (Array of strings)
        - frustrations (Array of strings)
        - behaviors (Array of strings)
        - motivations (Array of strings)
        - barriers (Array of strings)
        - environment (Physical/Digital context)
        - supportingquotes (Array of strings - direct quotes from input)
        - supportinginterviewids (Array of integers - IDs of interviews that informed this persona)
        """

        try:
            response = await self.model.generate_content_async(prompt)
            text = response.text.replace("```json", "").replace("```", "").strip()
            personas = json.loads(text)
            return personas
        except Exception as e:
            logger.error("llm_persona_generation_failed", error=str(e))
            return []

    async def generate_cvp(
        self, 
        personas: List[Any]
    ) -> Dict[str, Any]:
        """
        Synthesizes a CVP Canvas from Persona data.
        Input: List of Persona objects or dicts.
        """
        if not personas:
            return {}

        # Convert objects to dicts for JSON serialization
        # Handling both SQLModel objects and raw dicts
        personas_list = []
        for p in personas:
            if hasattr(p, "model_dump"):
                personas_list.append(p.model_dump())
            else:
                personas_list.append(p)
                
        context_str = json.dumps(personas_list, indent=2, default=str)

        prompt = f"""
        You are a Value Proposition Design Expert.
        Synthesize a Customer Value Proposition (CVP) Canvas based on the following synthesized Personas.
        Focus on finding the "Fit" between the pains/gains of these personas and a potential solution.

        INPUT PERSONAS (JSON):
        {context_str}

        OUTPUT FORMAT:
        Strict JSON Object for a single CVPCanvas. No markdown.
        Schema (lowercase concatenated keys):
        - customersegment (High-level summary of the target segment)
        - jobstobedone (Array of main functional/emotional/social jobs)
        - valueproposition (One-sentence clear value statement)
        - pains (Array of negative emotions, undesired costs/situations)
        - gains (Array of benefits, positive outcomes, requirements)
        - painrelievers (Array of how the solution alleviates pains)
        - gaincreators (Array of how the solution produces gains)
        - competitivepositioning (How this differs from status quo or competitors)
        """

        try:
            response = await self.model.generate_content_async(prompt)
            text = response.text.replace("```json", "").replace("```", "").strip()
            cvp_json = json.loads(text)
            return cvp_json
        except Exception as e:
            logger.error("llm_cvp_generation_failed", error=str(e))
            raise e

    async def generate_mvp_roadmap(
        self, 
        cvp_data: Any
    ) -> Dict[str, Any]:
        """
        Synthesizes an MVP Roadmap from CVP data.
        Input: CVPCanvas object or dict.
        Returns: Dict matching MVPRoadmapCreate schema.
        """
        if not cvp_data:
            return {}
            
        # Serialize CVP data
        if hasattr(cvp_data, "model_dump"):
            cvp_dict = cvp_data.model_dump()
        else:
            cvp_dict = cvp_data
            
        context_str = json.dumps(cvp_dict, indent=2, default=str)
        
        prompt = f"""
        You are an elite CTO and Product Manager.
        Your goal is to define a strict MVP (Minimum Viable Product) Roadmap based on the provided CVP Canvas.
        
        CRITERIA:
        1. Ruthless Prioritization: Use MoSCoW method. "MUST_HAVE" means the product fails without it.
        2. Traceability: Every feature must explicitly link back to a specific Pain or Gain in the CVP.
        3. Parsimony: Do not build "nice to haves". Focus on the core value proposition.
        
        INPUT CVP DATA (JSON):
        {context_str}
        
        OUTPUT FORMAT:
        Strict JSON Object. No markdown.
        Schema:
        {{
            "vision_statement": "A bold, one-sentence product vision.",
            "features": [
                {{
                    "title": "Feature Name",
                    "description": "Brief technical description",
                    "priority": "MUST_HAVE" | "SHOULD_HAVE" | "COULD_HAVE" | "WONT_HAVE",
                    "complexity": "LOW" | "MEDIUM" | "HIGH",
                    "rationale": "Why this is critical for MVP.",
                    "related_cvp_element": "Pain: [Specific Pain] or Gain: [Specific Gain]"
                }}
            ]
        }}
        """
        
        try:
            response = await self.model.generate_content_async(prompt)
            text = response.text.replace("```json", "").replace("```", "").strip()
            roadmap_json = json.loads(text)
            return roadmap_json
        except Exception as e:
            logger.error("llm_roadmap_generation_failed", error=str(e))
            # Fallback to Mock Data for Dev/Preview without valid Key
            return {
                "vision_statement": "A Unified Schema Validation Platform for High-Integrity Teams.",
                "features": [
                    {
                        "title": "Strict Schema Enforcer",
                        "description": "Middleware to block any request with non-concatenated keys.",
                        "priority": "MUST_HAVE", # Corrected to match Enum
                        "complexity": "MEDIUM",
                        "rationale": "Directly addresses the pain of 'Mismatched JSON keys'.",
                        "related_cvp_element": "Pain: Mismatched JSON keys"
                    },
                    {
                        "title": "Auto-Concatenator",
                        "description": "Utility to automatically strip underscores from legacy payloads.",
                        "priority": "SHOULD_HAVE",
                        "complexity": "LOW",
                        "rationale": "Increases adoption by reducing friction for legacy teams.",
                        "related_cvp_element": "Gain: Pure concatenated data"
                    },
                     {
                        "title": "Validation Dashboard",
                        "description": "Visual report of schema compliance scores.",
                        "priority": "COULD_HAVE",
                        "complexity": "HIGH",
                        "rationale": "Provides visibility but not critical for day 1 function.",
                        "related_cvp_element": "Gain: Strict typing"
                    }
                ]
            }


    async def generate_project_tasks(
        self, 
        roadmap_data: Any
    ) -> List[Dict[str, Any]]:
        """
        Breaks down an MVP Roadmap into specific engineering tasks.
        Input: MVPRoadmap object or dict.
        Returns: List of Dicts matching ProjectTaskCreate schema.
        """
        if not roadmap_data:
            return []
            
        # Serialize Roadmap data
        if hasattr(roadmap_data, "model_dump"):
            roadmap_dict = roadmap_data.model_dump()
        else:
            roadmap_dict = roadmap_data
            
        context_str = json.dumps(roadmap_dict, indent=2, default=str)
        
        prompt = f"""
        You are an experienced Engineering Manager and Technical Architect.
        Your goal is to take the provided MVP Product Roadmap and break it down into a granular, actionable backlog of engineering tasks.
        
        INPUT ROADMAP (JSON):
        {context_str}
        
        INSTRUCTIONS:
        1. Analyze each 'MUST_HAVE' and 'SHOULD_HAVE' feature in the roadmap.
        2. decomposed into technical components:
           - Backend/API tasks (Schema, Endpoints, Logic)
           - Frontend/UI tasks (Components, Screens, State)
           - Infrastructure/DevOps (DB setup, CI/CD, deployment)
        3. Estimate hours (integer) for each task.
        4. Assign a role (Frontend, Backend, DevOps, Design).
        
        OUTPUT FORMAT:
        Strict JSON Array of Task objects. No markdown.
        Schema:
        - title (Actionable title, e.g. "Implement POST /login endpoint")
        - description (Technical details)
        - priority (HIGH, MEDIUM, LOW - infer from feature priority)
        - status (Always "TODO")
        - estimated_hours (1-8 hours, break down large tasks)
        - assignee_role (e.g. "Backend Developer", "Frontend Developer")
        - feature_link_title (The title of the roadmap feature this belongs to, for reference)
        """
        
        try:
            response = await self.model.generate_content_async(prompt)
            text = response.text.replace("```json", "").replace("```", "").strip()
            tasks_json = json.loads(text)
            return tasks_json
        except Exception as e:
            logger.error("llm_task_generation_failed", error=str(e))
            return []

    async def conduct_interview(
        self, 
        history: List[Dict[str, str]], 
        user_message: str
    ) -> str:
        """
        Conducts an interactive interview as a Design Researcher.
        Input: History of messages [{"role": "user/assistant", "content": "..."}]
        Output: The AI's response text.
        """
        # Format history for context
        conversation_text = ""
        for msg in history:
            role = "Interviewer" if msg["role"] == "assistant" else "Participant"
            conversation_text += f"{role}: {msg['content']}\n"
        
        conversation_text += f"Participant: {user_message}\n"
        
        prompt = f"""
        You are an expert Design Researcher conducting an empathy interview.
        Your goal is to uncover the user's deep motivations, unmet needs, and mental models regarding their workflow/problem.
        
        GUIDELINES:
        - Be empathetic and curious.
        - Ask one question at a time.
        - Use "The Five Whys" technique naturally (gently probe deeper).
        - Keep responses concise (1-2 sentences).
        - Building rapport is key.
        - If the user says "Goodbye" or indicates they are done, wrap up politely.
        
        CURRENT CONVERSATION:
        {conversation_text}
        
        Interviewer Response:
        """
        
        try:
            response = await self.model.generate_content_async(prompt)
            # Cleanup response
            text = response.text.replace("Interviewer:", "").strip()
            return text
        except Exception as e:
            logger.error("llm_chat_failed", error=str(e))
            return "I'm listening. Please tell me more."

    async def chat_with_project(
        self,
        project_context: str,
        user_message: str
    ) -> str:
        """
        Conducts a chat session rooted in the Project's aggregated context (RAG).
        """
        prompt = f"""
        You are the AI Innovation Lead for this project.
        You have full access to all research, strategy, and planning documents.

        YOUR GOAL:
        Help the user execute this project by answering questions, suggesting next steps, or clarifying the strategy.
        Always base your answers on the provided CONTEXT.

        CONTEXT (Interviews, Personas, CVP, Roadmap, Tasks):
        ===
        {project_context}
        ===

        USER QUESTION:
        {user_message}

        YOUR RESPONSE:
        (Be helpful, strategic, and concise. Use markdown if needed.)
        """

        try:
            response = await self.model.generate_content_async(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error("llm_project_chat_failed", error=str(e))
            return "I'm having trouble accessing the project files right now. Please try again."

