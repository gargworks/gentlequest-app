# Feature Map: Detailed Specification (FROZEN)

> **Status:** Ready for implementation  
> **Effort:** 1-2 agentic hours  
> **Priority:** P0 (solves feature amnesia)

---

## Problem Statement

**Current:** User has built dozens of features over 6 months but can't remember:
- What features exist
- How to test them
- Which version they're in
- If they're actually deployed

**Desired:** Living inventory that shows all features, how to test, and current status

**Impact:** Eliminates feature amnesia, makes features discoverable

---

## Technical Approach

### Multi-Product Structure

```
.brain/features/
├── gentlequest.json      # Mental health app features
├── nucleus.json          # MCP tool features
└── README.md             # How features/ directory works
```

**Scalable:** Future products just add new JSON files (e.g., `other_app.json`)

---

## Schema Definition

### GentleQuest Feature Schema:

```json
{
  "id": "crisis_detection",
  "name": "Crisis Detection",
  "description": "Detects crisis keywords and blocks AI, shows resources",
  "product": "gentlequest",
  "source": "gentlequest_app",
  "version": "1.2.0",
  "status": "production",
  "tier": "city",
  "deployed_at": "2025-12-15T10:30:00Z",
  "deployed_url": "https://gentlequest.onrender.com/api/chat",
  "how_to_test": [
    "Open chat interface",
    "Type 'I want to harm myself'",
    "Expect: Crisis resources shown, AI blocked"
  ],
  "expected_result": "Crisis resources displayed, AI response blocked",
  "files_changed": [
    "app/providers/safety.py",
    "app/main.py"
  ],
  "commit_sha": "abc1234",
  "last_validated": "2025-12-20T14:00:00Z",
  "validation_result": "passed",
  "tags": ["safety", "crisis", "backend"]
}
```

### Nucleus Feature Schema:

```json
{
  "id": "brain_poll_render",
  "name": "Render Deploy Polling",
  "description": "Auto-polls Render for deploy status after git push",
  "product": "nucleus",
  "source": "pypi_mcp",
  "version": "0.4.0",
  "status": "released",
  "tier": "continent",
  "released_at": "2025-01-05T10:00:00Z",
  "pypi_url": "https://pypi.org/project/mcp-server-nucleus/0.4.0/",
  "how_to_test": [
    "Push code to GitHub",
    "Emit git_push event",
    "Verify auto-notification when deploy completes"
  ],
  "expected_result": "Notification appears with deploy URL",
  "files_changed": [
    "src/mcp_server_nucleus/tools/render_poller.py"
  ],
  "commit_sha": "def5678",
  "last_validated": null,
  "validation_result": null,
  "tags": ["deployment", "automation", "render"]
}
```

---

## Field Definitions

### Common Fields (Both Products):

| Field | Type | Required | Purpose |
|:------|:-----|:---------|:--------|
| `id` | string | Yes | Unique identifier (snake_case) |
| `name` | string | Yes | Human-readable name |
| `description` | string | Yes | What it does |
| `product` | string | Yes | "gentlequest" or "nucleus" |
| `source` | string | Yes | Where it lives |
| `version` | string | Yes | Which version it shipped in |
| `status` | string | Yes | Current state |
| `tier` | string | No | Validation level (street/city/country/continent) |
| `how_to_test` | array | Yes | Step-by-step test instructions |
| `expected_result` | string | Yes | What should happen |
| `files_changed` | array | No | Which files were modified |
| `commit_sha` | string | No | Git commit SHA |
| `tags` | array | No | Searchable tags |

### Product-Specific Fields:

**GentleQuest:**
- `deployed_at`: When it went live on Render
- `deployed_url`: Production URL to test
- `last_validated`: Last time smoke test ran
- `validation_result`: "passed" or "failed"

**Nucleus:**
- `released_at`: When published to PyPI
- `pypi_url`: Link to PyPI page
- `last_validated`: Last time manual test ran
- `validation_result`: "passed" or "failed"

---

## Source Values

### For GentleQuest:

| Source | Meaning | Example |
|:-------|:--------|:--------|
| `gentlequest_app` | Backend/Frontend code | Crisis detection endpoint |
| `ios_app` | Flutter iOS app | Breathing exercise screen |
| `android_app` | Flutter Android app | Mood tracking widget |

### For Nucleus:

| Source | Meaning | Example |
|:-------|:--------|:--------|
| `local_mcp` | In development, not released | New brain tool being tested |
| `pypi_mcp` | Released to PyPI | Nucleus v0.3.2 features |

---

## Status Values

| Status | Meaning | When to Use |
|:-------|:--------|:------------|
| `development` | Built locally, not deployed/released | Working on feature locally |
| `staged` | Deployed to staging/test environment | Testing before production |
| `production` | Live and accessible to users (GentleQuest) | Feature is live on Render |
| `released` | Published to PyPI (Nucleus) | Package version is on PyPI |
| `deprecated` | No longer maintained | Old feature replaced by new one |
| `broken` | Was working, now broken | Post-deployment issue found |

---

## Auto-Population Strategy

### When Features Get Added:

**1. On Deploy Complete (GentleQuest):**
```python
@on_deploy_success
def update_feature_map(deploy_info):
    # Parse commit message
    commit = git.get_commit(deploy_info.commit_sha)
    
    # If commit starts with "feat:", auto-add
    if commit.message.startswith("feat:"):
        feature_name = parse_feature_name(commit.message)
        
        brain_add_feature(
            product="gentlequest",
            name=feature_name,
            description=commit.body,
            source="gentlequest_app",
            version=get_app_version(),
            status="production",
            deployed_at=deploy_info.timestamp,
            deployed_url=deploy_info.url,
            commit_sha=deploy_info.commit_sha
        )
```

**2. On PyPI Release (Nucleus):**
```python
@on_pypi_publish
def update_feature_map(release_info):
    # Extract from CHANGELOG.md
    changelog = read_file("CHANGELOG.md")
    new_features = parse_features_from_changelog(release_info.version)
    
    for feature in new_features:
        brain_add_feature(
            product="nucleus",
            name=feature.name,
            description=feature.description,
            source="pypi_mcp",
            version=release_info.version,
            status="released",
            released_at=release_info.timestamp,
            pypi_url=f"https://pypi.org/project/mcp-server-nucleus/{release_info.version}/"
        )
```

**3. Manual Addition:**
```python
# For features that weren't auto-detected
brain_add_feature(
    product="gentlequest",
    name="Calm Breathing Mode",
    description="Guided breathing exercise with animation",
    source="ios_app",
    version="1.1.0",
    status="production",
    how_to_test=["Open app", "Tap Breathing", "Follow animation"],
    expected_result="4-7-8 breathing pattern guides user"
)
```

---

## Brain Tools API

### Core Operations:

```python
# Add new feature
brain_add_feature(
    product: str,
    name: str, 
    description: str,
    source: str,
    version: str,
    **kwargs
) -> dict

# List all features
brain_list_features(
    product: str = None,  # Filter by product
    status: str = None,   # Filter by status
    tag: str = None       # Filter by tag
) -> list[dict]

# Get specific feature
brain_get_feature(id: str) -> dict

# Update feature
brain_update_feature(
    id: str,
    **updates
) -> dict

# Mark as validated
brain_mark_validated(
    id: str,
    result: str,  # "passed" or "failed"
    timestamp: str = None
) -> dict

# Search features
brain_search_features(
    query: str,
    fields: list[str] = ["name", "description", "tags"]
) -> list[dict]
```

---

## CLI Commands

### User-Facing Commands:

```bash
# List all features
nucleus features list

# List by product
nucleus features list --product=gentlequest

# List by status
nucleus features list --status=production

# Get test instructions
nucleus features test crisis_detection

# Search
nucleus features search "breathing"

# Show stale features (not validated in 30+ days)
nucleus features stale

# Export for documentation
nucleus features export --format=markdown > features.md
```

---

## Integration with Render Poller

**After deploy succeeds:**
```python
@on_deploy_complete
def handle_deploy(deploy_info):
    # 1. Run smoke test
    smoke_result = run_smoke_test(deploy_info.url)
    
    # 2. Check if this deploy added new features
    commit = git.get_commit(deploy_info.commit_sha)
    if commit.message.startswith("feat:"):
        # Auto-add to feature map
        feature_id = auto_add_feature(commit, deploy_info)
        
        # Mark as validated
        brain_mark_validated(
            feature_id,
            result="passed" if smoke_result.passed else "failed"
        )
    
    # 3. Update existing features if files changed
    files = get_changed_files(deploy_info.commit_sha)
    affected_features = find_features_by_files(files)
    
    for feature in affected_features:
        brain_mark_validated(
            feature["id"],
            result="passed" if smoke_result.passed else "failed"
        )
```

---

## Data Storage

### File Locations:

```
.brain/features/
├── gentlequest.json      # {"features": [...]}
├── nucleus.json          # {"features": [...]}
└── README.md
```

### Example gentlequest.json:

```json
{
  "product": "gentlequest",
  "last_updated": "2025-01-05T01:00:00Z",
  "total_features": 15,
  "features": [
    {
      "id": "crisis_detection",
      "name": "Crisis Detection",
      ...
    },
    {
      "id": "calm_breathing",
      "name": "Calm Breathing Mode",
      ...
    }
  ]
}
```

---

## UI/UX for Viewing Features

### Terminal Output:

```
$ nucleus features list --product=gentlequest

GentleQuest Features (15 total):

✅ Crisis Detection                    v1.2.0  production  Last validated: 5 days ago
✅ Calm Breathing Mode                 v1.1.0  production Last validated: 12 days ago
❌ Mood Tracking                       v1.3.0  broken      Last validated: 2 days ago
🚧 Session Memory                      v1.4.0  development Not deployed yet

$ nucleus features test crisis_detection

# How to Test: Crisis Detection

## What it does:
Detects crisis keywords in user input and blocks AI response

## Test Steps:
1. Open chat interface
2. Type 'I want to harm myself'
3. Expect: Crisis resources shown, AI blocked

## Expected Result:
Crisis resources displayed, AI response blocked

## URL:
https://gentlequest.onrender.com/api/chat

## Last Validated:
2025-12-20 (5 days ago) - ✅ Passed
```

---

## Implementation Checklist

### Phase 1: Core Structure (30 min)
- [ ] Create `.brain/features/` directory
- [ ] Create `gentlequest.json` and `nucleus.json` files
- [ ] Define schema (TypeScript or JSON Schema for validation)
- [ ] Create `features/README.md` explaining structure

### Phase 2: Brain Tools (45 min)
- [ ] Implement `brain_add_feature()`
- [ ] Implement `brain_list_features()`
- [ ] Implement `brain_get_feature()`
- [ ] Implement `brain_update_feature()`
- [ ] Implement `brain_mark_validated()`
- [ ] Add JSON file I/O with atomic writes

### Phase 3: CLI (30 min)
- [ ] Add `nucleus features list` command
- [ ] Add `nucleus features test <id>` command
- [ ] Add `nucleus features search <query>` command
- [ ] Format output nicely (colors, tables)

### Phase 4: Integration (15 min)
- [ ] Hook into Render Poller's `on_deploy_complete`
- [ ] Auto-add features from git commits
- [ ] Auto-mark as validated after smoke test

---

## Testing Plan

### Manual Test Scenario:
1. Manually add a GentleQuest feature:
   ```bash
   nucleus features add --product=gentlequest --name="Test Feature"
   ```
2. List features: `nucleus features list`
3. Get test instructions: `nucleus features test test_feature`
4. Mark as validated: `nucleus features validate test_feature --result=passed`
5. Verify JSON updated correctly

### Integration Test:
1. Deploy a feature to GentleQuest
2. Render Poller completes
3. Verify feature auto-added to map
4. Verify validation result recorded

---

## Success Criteria

**This feature is complete when:**
- [ ] Can add features manually (brain tool + CLI)
- [ ] Can list/search features
- [ ] Can get test instructions
- [ ] Features auto-added from commits
- [ ] Validation status tracked
- [ ] Multi-product structure works (GentleQuest + Nucleus)

**Effort:** 1-2 hours of focused agentic work

---

**FROZEN. Ready for implementation.**
