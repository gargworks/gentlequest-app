# Nucleus Mounting Protocol (NMP) v1.0 — The "Netscape" for Agents

## Abstract
NMP defines a standard for **Recursive Client-Side Aggregation** of Model Context Protocol (MCP) servers. It establishes the "Netscape Event" for the Agentic Web—enabling an MCP client (the "Parent") to mount other MCP servers (the "Children") and expose their tools via a unified, navigable, and namespaced interface.

## 1. Namespacing
### 1.1. The `mount_id`
Every mounted server MUST be assigned a unique `mount_id` within the parent's scope.
- **Format**: `[a-z0-9_]+` (Snake case recommended).
- **Scope**: Local to the parent. Grandchildren are namespaced relative to their direct parent.

### 1.2. Tool Exposure
Tools from the child server are exposed by the parent with the prefix:
`{mount_id}:{original_tool_name}`

**Example**:
- Parent mounts Child A (`mount_id="fs"`)
- Child A has tool `read_file`
- Parent exposes tool `fs:read_file`

## 2. Recursive Traversal
### 2.1. Discovery
A parent server MUST expose a `list_tools` capability that includes:
1.  **Local Tools**: Native tools of the parent.
2.  **Mounted Tools**: Tools from all active children, properly namespaced.

### 2.2. Execution
When a client calls a namespaced tool (`fs:read_file`):
1.  **Routing**: The parent parses the `mount_id` (`fs`).
2.  **Lookup**: The parent retrieves the active connection for that ID.
3.  **Forwarding**: The parent forwards the request (stripped of the prefix) to the child.
    - `call_tool("fs:read_file", args)` -> `child.call_tool("read_file", args)`
4.  **Response**: The child's response (result or error) is returned to the client as-is.

## 3. Error Handling
### 3.1. Circular Dependencies (Future Scope)
Implementations should detect cycles if a Nucleus mounts itself (e.g., A -> B -> A). The current v0.5 implementation relies on manual configuration discipline.

### 3.2. Connection Failures
If a child server crashes or disconnects:
- The parent MUST return a specific error code (e.g., `-32000 Server Not Available`) to the client.
- The parent SHOULD attempt auto-reconnection or expose a `remount` tool.

## 4. Security
### 4.1. "Sandboxed Mounting"
A parent server MUST NOT expose "Admin" tools (like `brain_mount_server`) from a child unless explicitly configured. This prevents "Jailbreak Mounting".

## 5. Attestation & Trust (The "Verisign" Pillar)
### 5.1. Cryptographic Receipts
A parent server SHOULD provide an optional `attestation` mode. When enabled:
1.  **Receipt Generation**: Every child tool invocation generates a signed JSON-LD receipt.
2.  **Verification**: These receipts can be verified by external auditors to prove the agent's chain of custody.

### 5.2. Governance Dashboard (Future)
The protocol reserves the namespace `_nucleus:*` for administrative and governance tools (e.g., `_nucleus:audit_stats`, `_nucleus:list_mounts`).
