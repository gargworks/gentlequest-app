
import os
import sys
import json
from pathlib import Path

# Tool Scaffolder
# Usage: python3 tools/omega/scaffold_tool.py <tool_name> <description>

def scaffold_tool(tool_name: str, description: str):
    root_tools = Path("/Users/lokeshgarg/ai-mvp-backend/tools")
    tool_dir = root_tools / tool_name
    
    if tool_dir.exists():
        print(f"❌ Tool {tool_name} already exists.")
        return

    print(f"🔨 Scaffolding {tool_name}...")
    
    # 1. Create Directories
    (tool_dir / "src").mkdir(parents=True)
    (tool_dir / "tests").mkdir(parents=True)
    
    # 2. Create manifest.json
    manifest = {
        "name": tool_name,
        "version": "0.1.0",
        "description": description,
        "author": "Nucleus User",
        "capabilities": ["llm_generate"],
        "entry_point": "src.main"
    }
    (tool_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    
    # 3. Create __init__.py
    (tool_dir / "__init__.py").touch()
    (tool_dir / "src" / "__init__.py").touch()
    
    # 4. Create src/main.py (Boilerplate)
    main_py = f"""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("{tool_name}")

@mcp.tool()
def {tool_name}_run(input_data: str) -> str:
    \"\"\"
    {description}
    \"\"\"
    return f"Processed {{input_data}} via {tool_name}"
    """
    (tool_dir / "src" / "main.py").write_text(main_py.strip())
    
    # 5. Create README.md
    readme = f"""
# {tool_name}
{description}

## Usage
Installed via Nucleus Tool Marketplace.
    """
    (tool_dir / "README.md").write_text(readme.strip())
    
    print(f"✅ Created {tool_dir}")
    print(f"👉 Next: Register in tools/registry.json")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 scaffold_tool.py <tool_name> <description>")
        sys.exit(1)
        
    scaffold_tool(sys.argv[1], sys.argv[2])
