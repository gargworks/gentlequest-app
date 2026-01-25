# Dual-Engine LLM Client: Migration Strategy

## The Pattern: "Safe Transition"
We will implement a wrapper class that unifies the interface for both the new `google.genai` Client and the legacy `google.generativeai` module.

```python
class DualEngineLLM:
    def __init__(self, model_name="gemini-2.0-flash-exp", system_instruction=None):
        self.model_name = model_name
        self.system_instruction = system_instruction
        self.client = None
        self.legacy_model = None
        
        # Try initializing New Engine
        try:
            from google import genai
            self.client = genai.Client(http_options={'api_version': 'v1alpha'})
            self.engine = "NEW"
        except Exception as e:
            print(f"⚠️ New GenAI Client failed: {e}. Falling back to legacy.")
            self.engine = "LEGACY"

    def generate_content(self, prompt):
        if self.engine == "NEW":
            try:
                # New API Call
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config={'system_instruction': self.system_instruction}
                )
                return response
            except Exception as e:
                print(f"⚠️ New Engine runtime error: {e}. Switching to legacy.")
                self.engine = "LEGACY"
                # Fallthrough to legacy
        
        # Legacy API Call
        import google.generativeai as old_genai
        if not self.legacy_model:
            old_genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            self.legacy_model = old_genai.GenerativeModel(
                self.model_name, 
                system_instruction=self.system_instruction
            )
        
        return self.legacy_model.generate_content(prompt)
```

## Implementation Steps

1.  **Create `runtime/llm_client.py`**:
    *   Define `DualEngineLLM` class.
    *   Standardize the `response.text` access (wrapper might be needed if objects differ significantly).

2.  **Refactor `agent.py`**:
    *   Remove direct `import google.generativeai`.
    *   Import `DualEngineLLM`.
    *   Replace `self.model.generate_content()` with `self.llm.generate_content()`.

3.  **Verification**:
    *   Run `brain_spawn_agent` with a simple task.
    *   Check logs to see "Using NEW Engine" or "Switching to legacy".

## Benefit
This allows us to deploy the new code immediately. If the new API behaves unexpectedly in production (e.g., auth issues on Render), the system **automatically heals** itself by reverting to the old, working method.
