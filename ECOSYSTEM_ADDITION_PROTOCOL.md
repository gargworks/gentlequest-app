# Nucleus Ecosystem Addition Protocol (LLM-Ready)

This protocol defines the exact sequence for adding a new registry, directory, or ecosystem link to the Nucleus project. Follow these steps to ensure global parity across 100+ endpoints.

---

## 🏗️ The 4-Phase Addition Sequence

### Phase 1: Registry Manifest Creation
Create a new JSON manifest in the `.registry/` directory. This acts as the "Source of Truth" for that specific endpoint.

**Path**: `.registry/[endpoint_name].json`
**Format**:
```json
{
    "name": "nucleus-mcp",
    "version": "1.0.x",
    "description": "Short description of the project.",
    "mirror_to_root": true,
    "templating": [
        {
            "file": "README.md",
            "marker": "ENDPOINT_BADGE",
            "content": "[![Badge](image_url)](link_url)"
        }
    ]
}
```

### Phase 2: Template Marker Insertion (The "Slot")
If the manifold requires markdown injection (e.g., a badge in the README or a link in the Launch Kit), you must first add the "Slot" markers to the target file.

**Format**:
```markdown
<!-- ENDPOINT_BADGE:START -->
<!-- ENDPOINT_BADGE:END -->
```

### Phase 3: Launch Kit Update
Manually add the new link to the **Tiered Link List** in the current active launch document.

**Target**: `nucleus-launch-internal/PRODUCT_HUNT_FINAL_STRIKE.md`

### Phase 4: Sentinel Synchronization
Run the `sync_registry.py` script to force global parity. This script reads the manifest, updates the versions, and injects the templated content into the markers.

**Command**:
```bash
python3 scripts/sync_registry.py
```

---

## 🛡️ Why we do this?
- **Idempotency**: Running the sync script multiple times won't break things.
- **Atomicity**: The `version.json` in `.registry/` is the master version. If you bump it there, the script strikes all 100+ endpoints (NPM, PyPI, Readmes) in one pass.
- **LLM-Safe**: By providing markers, LLMs like Antigravity can safely edit files without destroying surrounding context.

**Protocol Status**: ACTIVE
**Managed by**: Registry Sentinel Engine
