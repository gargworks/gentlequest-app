# Positioning & Messaging Framework: The Agent Control Plane
*Status: CANONICAL SOURCE OF TRUTH*

## 1. The Category Flag
**Primary**: The Agent Control Plane
**Secondary**: Recursive MCP Aggregator

## 2. The Core Value Proposition
Nucleus provides the **Policy, Governance, and Orchestration** that raw tool connections lack. 
*   **Problem**: Tools are powerful but unmanaged.
*   **Solution**: Nucleus is the management layer (The Control Plane).

## 3. Product Claims
*   **"Context is Not Control"**: Replaces the "CLAUDE.md" mental model with an active system.
*   **"Default-Deny Tooling"**: Establishes trust as the primary conversion hook.
*   **"Immutable Decision Ledger"**: Positions the Audit Trail as a mission-critical utility for enterprise/teams.

## 4. Key Terminology for Docs
| Use... | Instead of... | Why? |
| :--- | :--- | :--- |
| **Agent Control Plane** | Agent OS (Legacy) | More infra-correct; less "fluff." |
| **Recursive Aggregator** | Tool Hub | Explains the technical architecture. |
| **Governance** | Security | Broader; includes policy and orchestration. |
| **Mounting** | Adding tools | Standard infra terminology. |
| **Engram** | Memory | Differentiates from commodity RAG. |

## 5. Actionable Examples: Context vs. Control

### Example 1: Secure Code Execution
*   **Context (CLAUDE.md)**: "Please don't execute code without asking."
*   **Control (Nucleus)**: The `Default-Deny` policy technically prevents the Python interpreter from accessing the root directory unless explicitly approved via the `Isolation Boundary`.

### Example 2: Multi-Agent Coordination
*   **Context (CLAUDE.md)**: "You are the Lead Developer. Another agent is the Tester."
*   **Control (Nucleus)**: The `Engram Ledger` records the Developer agent's decision to refactor, and the `Recursive Aggregator` automatically triggers the Tester agent's `brain_claim_task` once the refactor event is emitted.

### Example 3: Long-term Decision Memory
*   **Context (CLAUDE.md)**: "Last week we decided to use Postgres." (Requires manual update by user).
*   **Control (Nucleus)**: `brain_session_start()` automatically surfaces the "Postgres" Engram from the `DecisionMade` trail, ensuring every new agent start with the same architectural constraints.
