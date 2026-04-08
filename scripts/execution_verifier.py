"""
Execution Verifier — Thin shim re-exporting from MCP package.

The canonical engine lives in:
  mcp-server-nucleus/src/mcp_server_nucleus/runtime/execution_verifier.py

This shim exists so existing imports (driver, tests, CI) keep working
without any path changes.
"""

import sys
from pathlib import Path

# Try importing from the installed package first
try:
    from mcp_server_nucleus.runtime.execution_verifier import *  # noqa: F401,F403
    from mcp_server_nucleus.runtime.execution_verifier import (
        verify_execution,
        build_calibration_dpo,
        detect_runtime_checks,
        _tier0_diff_nonempty,
        _tier1_syntax_check,
        _tier2_import_check,
        _tier3_test_execution,
        _tier4_runtime_check,
        _tier5_outcome_check,
        extract_plan_claims,
        capture_outcome_baseline,
        _get_changed_files,
        _check_json,
        _check_yaml,
    )
except ImportError:
    # Fallback: add the source tree to path (for dev without pip install)
    _src = Path(__file__).resolve().parent.parent / "mcp-server-nucleus" / "src"
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))
    from mcp_server_nucleus.runtime.execution_verifier import *  # noqa: F401,F403
    from mcp_server_nucleus.runtime.execution_verifier import (
        verify_execution,
        build_calibration_dpo,
        detect_runtime_checks,
        _tier0_diff_nonempty,
        _tier1_syntax_check,
        _tier2_import_check,
        _tier3_test_execution,
        _tier4_runtime_check,
        _tier5_outcome_check,
        extract_plan_claims,
        capture_outcome_baseline,
        _get_changed_files,
        _check_json,
        _check_yaml,
    )
