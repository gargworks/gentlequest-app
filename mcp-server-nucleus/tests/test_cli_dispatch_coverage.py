"""
Test that every handle_*_command referenced in main() dispatch has a matching definition.

Catches regressions where the sanitizer (scripts/sanitize_cli.py) accidentally
removes handler definitions while leaving their dispatch calls intact.
"""

import ast
import re
from pathlib import Path

CLI_PATH = Path(__file__).parent.parent / "src" / "mcp_server_nucleus" / "cli.py"

# Known exceptions: handlers that are intentionally undefined or use different naming
KNOWN_MISSING = {
    "handle_depot_command",     # dispatch exists but no definition (pre-existing)
    "handle_recipe_command",    # uses _handle_recipe_command (underscore prefix)
    "handle_archive_command",   # sovereign handler, stripped in public build
}


def test_all_dispatched_handlers_are_defined():
    """Every handle_*_command() call in dispatch must have a matching def."""
    content = CLI_PATH.read_text()
    tree = ast.parse(content)

    # Collect all function definitions
    defined = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("handle_"):
            defined.add(node.name)

    # Collect all handle_*_command references (dispatch calls)
    dispatched = set(re.findall(r"(handle_\w+_command)", content))

    missing = dispatched - defined - KNOWN_MISSING
    assert not missing, (
        f"Handler definitions missing for dispatch calls: {sorted(missing)}. "
        f"This usually means scripts/sanitize_cli.py accidentally removed them. "
        f"Check for missing BLOCK_END tags in cli.py."
    )


def test_handler_count_minimum():
    """Ensure we haven't lost a massive number of handlers."""
    content = CLI_PATH.read_text()
    tree = ast.parse(content)
    count = sum(
        1 for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("handle_")
    )
    # We expect ~49 handlers. Alert if we drop below 40.
    assert count >= 40, (
        f"Only {count} handle_*_command definitions found. Expected ~49. "
        f"Massive handler loss likely from sanitizer cascade bug."
    )
