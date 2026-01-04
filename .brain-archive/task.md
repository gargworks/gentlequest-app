# Nucleus Onboarding Sprint

## Objective
Enhance `nucleus-init` to provide a guided onboarding experience for new users.

---

## Tasks

### Phase 1: Implementation
- [x] Add `DEFAULT_TASKS` to `cli.py` (instructional seed tasks)
- [x] Add `.brain/README.md` creation to both templates
- [x] Improve CLI output with bolder "next steps" prompts

### Phase 2: Verification
- [x] Test `nucleus-init` locally (default template)
- [x] Test `nucleus-init --template=solo` locally
- [x] Verify tasks appear in Claude Desktop (Fixed in v0.3.2)
- [x] **Regression Test:** Create unit tests for V2 task logic (`tests/test_brain_v2_logic.py`)

### Phase 3: Ship
- [x] Bump version to 0.3.1 (Broken) -> 0.3.2 (Fixed)
- [x] Update CHANGELOG.md
- [x] Commit and push
- [x] Upload to PyPI (v0.3.2 live)
