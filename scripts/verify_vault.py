#!/usr/bin/env python3
"""
verify_vault.py

Verification script for Phase 57: Chat 18 - The Vault.
Tests BudgetGuard v2 (Zero-Default Spending Limits).
"""

import os
import sys
import logging
from typing import Dict, Any, List

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp-server-nucleus", "src")))

from mcp_server_nucleus.runtime.budget import BudgetGuard, BudgetAuditor
from mcp_server_nucleus.runtime.capabilities.base import Capability

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("VERIFY_VAULT")

# Mock Capability for testing
class ExpensiveTool(Capability):
    def __init__(self):
        self._name = "expensive_tool"
        self._desc = "Costs money"
        
    @property
    def name(self) -> str:
        return self._name
        
    @property
    def description(self) -> str:
        return self._desc
        
    def get_tools(self) -> List[Dict[str, Any]]:
        return []
        
    def execute(self, params: Dict[str, Any]) -> str:
        return "Tool Executed Successfully"

def setup_auditor():
    import tempfile
    from pathlib import Path
    
    tmp_dir = Path(tempfile.mkdtemp())
    (tmp_dir / "ledger").mkdir()
    return BudgetAuditor(tmp_dir), tmp_dir

def verify_zero_budget():
    logger.info("Step 1: Testing Zero Budget (Default Deny)...")
    
    tool = ExpensiveTool()
    auditor, _ = setup_auditor()
    
    # 0.0 Budget
    guard = BudgetGuard(tool, auditor, agent_id="agent.test.zero", max_budget_usd=0.0)
    
    # Try to execute (Cost 0.01)
    result = guard.execute({})
    
    if "SECURITY BLOCK" in result and "Zero Cost Budget Enforced" in result:
        logger.info("✅ Blocked execution with $0.00 budget")
        return True
    else:
        logger.error(f"❌ Failed to block zero budget. Result: {result}")
        return False

def verify_sufficient_budget():
    logger.info("Step 2: Testing Sufficient Budget...")
    
    tool = ExpensiveTool()
    auditor, _ = setup_auditor()
    
    # $1.00 Budget
    guard = BudgetGuard(tool, auditor, agent_id="agent.test.rich", max_budget_usd=1.0)
    
    # Try to execute (Cost 0.01)
    result = guard.execute({})
    
    if result == "Tool Executed Successfully":
        logger.info("✅ Allowed execution with sufficient budget")
        return True
    else:
        logger.error(f"❌ Failed to allow valid execution. Result: {result}")
        return False

def verify_budget_exhaustion():
    logger.info("Step 3: Testing Budget Exhaustion...")
    
    tool = ExpensiveTool()
    auditor, _ = setup_auditor()
    
    # $0.05 Budget
    guard = BudgetGuard(tool, auditor, agent_id="agent.test.poor", max_budget_usd=0.05)
    
    # Execute 5 times (should pass - total cost 0.05)
    for i in range(5):
        res = guard.execute({})
        if "SECURITY BLOCK" in res:
            logger.error(f"❌ Premature block at iteration {i+1}: {res}")
            return False
            
    # Execute 6th time (should fail - total cost 0.06 > 0.05)
    # NOTE: Floating point math means 0.05 might be slightly exceeded or under.
    # Our implementation checks >= max_budget. 
    # If using >=, then iteration 5 *might* block if it hits exactly 0.05 at start or end.
    # Logic in BudgetGuard is:
    # 1. Check spent >= max_budget
    # 2. Execute
    # 3. Add cost
    
    # Iter 1: spent 0.00 -> OK -> spent 0.01
    # Iter 2: spent 0.01 -> OK -> spent 0.02
    # Iter 3: spent 0.02 -> OK -> spent 0.03
    # Iter 4: spent 0.03 -> OK -> spent 0.04
    # Iter 5: spent 0.04 -> OK -> spent 0.05
    # Iter 6: spent 0.05 >= 0.05 -> BLOCK!
    
    result = guard.execute({})
    if "SECURITY BLOCK" in result:
        logger.info("✅ Blocked execution after budget exhaustion")
        return True
    else:
        logger.error(f"❌ Failed to block after exhaustion. Spent: {guard.spent_usd}")
        return False

def main():
    try:
        if not verify_zero_budget():
            sys.exit(1)
            
        if not verify_sufficient_budget():
            sys.exit(1)
            
        if not verify_budget_exhaustion():
            sys.exit(1)
            
        logger.info("✨ ALL VAULT CHECKS PASSED ✨")
        sys.exit(0)
        
    except ImportError as e:
        logger.error(f"❌ Import Error: {e}. Implementation missing?")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
