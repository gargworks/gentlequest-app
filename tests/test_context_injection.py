
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path("/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src")))

from mcp_server_nucleus.runtime.factory import ContextFactory

def test_injection():
    # Mock _register_defaults to avoid loading actual tools (which might fail validation)
    original_register = ContextFactory._register_defaults
    ContextFactory._register_defaults = lambda self: None
    
    try:
        factory = ContextFactory()
    finally:
        # Restore just in case
        ContextFactory._register_defaults = original_register
    
    # Test Case 1: "deploy" intent
    print("--- Testing 'deploy' intent ---")
    ctx = factory.create_context("test_session", "How do I deploy to Cloud Run?")
    prompt = ctx["system_prompt"]
    
    if "DYNAMIC CONTEXT INJECTION" in prompt and "cloudbuild.yaml" in prompt:
        print("✅ SUCCESS: Found injected cloudbuild.yaml context")
    else:
        print("❌ FAILED: Missing injected context")
        print("Prompt snippet:", prompt[-500:])

    # Test Case 2: "database" intent
    print("\n--- Testing 'database' intent ---")
    ctx = factory.create_context("test_session", "What is the database schema?")
    prompt = ctx["system_prompt"]
    
    if "DATABASE_SCHEMA.md" in prompt:
        print("✅ SUCCESS: Found injected DATABASE_SCHEMA.md context")
    else:
        print("❌ FAILED: Missing database context")
        
    # Test Case 3: "irrelevant" intent
    print("\n--- Testing 'hello' intent ---")
    ctx = factory.create_context("test_session", "Hello world")
    prompt = ctx["system_prompt"]
    
    if "DYNAMIC CONTEXT INJECTION" not in prompt:
        print("✅ SUCCESS: No context injected for irrelevant intent")
    else:
        print("❌ FAILED: Injected context where none was expected")

if __name__ == "__main__":
    test_injection()
