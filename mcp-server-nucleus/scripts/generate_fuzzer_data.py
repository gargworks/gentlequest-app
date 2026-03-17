import os
import sys
import json
import ast
from collections import defaultdict

# Correctly add the mcp-server-nucleus/src directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
mcp_server_nucleus_base_dir = os.path.abspath(os.path.join(script_dir, '..'))
src_path = os.path.join(mcp_server_nucleus_base_dir, 'src')
sys.path.insert(0, src_path)
print(f"DEBUG: sys.path includes: {sys.path[0]}")

TOOL_MODULE_NAMES = [ # Using just names as file path is built here
    "sync",
    "sessions",
    "tasks",
    "features",
    "engrams",
    "orchestration",
    "federation",
    "governance",
    "observability",
]

OUTPUT_FILE = "mcp-server-nucleus/tests/fuzzer_data.json"

def get_all_actions_by_parsing():
    all_actions = defaultdict(list)
    # The base directory for tools is now correctly derived from src_path
    base_dir_for_tools = os.path.join(src_path, "mcp_server_nucleus", "tools")
    
    for module_name_short in TOOL_MODULE_NAMES:
        file_path = os.path.join(base_dir_for_tools, f"{module_name_short}.py")
        
        if not os.path.exists(file_path):
            print(f"ERROR: File not found: {file_path}", file=sys.stderr)
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=file_path)

            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id.endswith("ROUTER"):
                            if isinstance(node.value, ast.Dict):
                                router_var_name = target.id # e.g., "ROUTER", "ORCH_ROUTER"
                                
                                # Determine the key for all_actions based on module and router name
                                if module_name_short == "orchestration" and router_var_name == "ORCH_ROUTER":
                                    all_actions_key = "orchestration_orch"
                                elif module_name_short == "orchestration" and router_var_name == "TELEM_ROUTER":
                                    all_actions_key = "orchestration_telem"
                                elif module_name_short == "orchestration" and router_var_name == "SLOTS_ROUTER":
                                    all_actions_key = "orchestration_slots"
                                elif module_name_short == "orchestration" and router_var_name == "INFRA_ROUTER":
                                    all_actions_key = "orchestration_infra"
                                elif module_name_short == "orchestration" and router_var_name == "AGENTS_ROUTER":
                                    all_actions_key = "orchestration_agents"
                                else:
                                    # For other modules, like sync.py, the router_var_name is just ROUTER
                                    # and the module_name_short is sufficient for the key.
                                    all_actions_key = module_name_short

                                print(f"DEBUG: Found {router_var_name} in {file_path}. Mapping to key: {all_actions_key}")
                                for key_node in node.value.keys:
                                    # Handle string literals using ast.Constant for Python 3.8+
                                    if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
                                        action_name = key_node.value
                                        all_actions[all_actions_key].append(action_name)
                                    # Keep ast.Str for backward compatibility if needed (Python < 3.8)
                                    elif isinstance(key_node, ast.Str): # Deprecated in 3.8, removed in 3.9
                                        action_name = key_node.s
                                        all_actions[all_actions_key].append(action_name)

        except Exception as e:
            print(f"ERROR: Could not parse module {module_name_short} ({file_path}): {e}", file=sys.stderr)
    return all_actions

def generate_fuzzer_data(actions_by_router):
    fuzzer_data = {}
    print("Generating fuzzer data structure...")
    for router_name, actions in actions_by_router.items():
        for action in actions:
            full_action_name = f"{router_name}.{action}"
            # Placeholder for LLM generation
            fuzzer_data[full_action_name] = {
                "original": action,
                "variants": {
                    "slang": f"LLM_GENERATE_SLANG({action})",
                    "professional": f"LLM_GENERATE_PROFESSIONAL({action})",
                    "concise": f"LLM_GENERATE_CONCISE({action})",
                    "implicit": f"LLM_GENERATE_IMPLICIT({action})",
                    "edge_case": f"LLM_GENERATE_EDGE_CASE({action})"
                }
            }
    return fuzzer_data

if __name__ == "__main__":
    actions = get_all_actions_by_parsing() # Use the new parsing function
    generated_data = generate_fuzzer_data(actions)

    output_path = os.path.abspath(OUTPUT_FILE)
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(generated_data, f, indent=4)

    print(f"Generated fuzzer data to {output_path}")
    print(f"Total actions identified: {sum(len(v) for v in actions.values())}")
