# Contributing to GentleQuest backend

## Quick setup

```bash
# Runtime + dev deps
pip install -r requirements.txt -r requirements-dev.txt

# Install pre-commit hooks (runs ruff + mypy + fast pytest on changed files)
pre-commit install

# Run the full local gate before pushing
ruff check app.py config/ setup/ helpers/ routes/ tests/test_helpers_*.py tests/test_config_*.py tests/test_setup_*.py
mypy config/ setup/
pytest tests/test_helpers_*.py tests/test_config_*.py tests/test_setup_*.py \
  --cov --cov-config=.coveragerc --cov-fail-under=70
```

## Required CI gates (blocking on PRs to `main`)

| Gate | Scope | Minimum |
|------|-------|---------|
| `ruff check` | `app.py` + `config/` + `setup/` + `helpers/` + `routes/` + scoped tests | 0 errors |
| `mypy` | `config/` + `setup/` | 0 errors |
| `pytest --cov-fail-under=70` | `tests/test_{helpers,config,setup}_*.py` | ≥70% coverage |
| Full test suite | `tests/` | all pass |
| GROUND verification | `nucleus verify --tiers 0,1,2` | exit 0 |

Python matrix: **3.11** and **3.12**.

## Coverage ratchet

The 70% floor is the starting point. It will ratchet up in future phases:

- **Phase D (current):** 70%
- **Phase F (Mood Insights):** 75%
- **Phase I (Crisis v2):** 80%

Never lower the floor. If your PR drops coverage, add tests.

## Code style

- **Line length:** 120 (ruff enforced)
- **Imports:** Sorted (ruff `I` rule)
- **Line-level comments:** only when intent is non-obvious — do **not** narrate the code
- **No `# type: ignore` without a reason:** prefer a real fix; if unavoidable, narrow the scope (`[attr-defined]`, `[assignment]`)

## Test discipline

- Every extracted helper/setup module gets a matching `tests/test_*_{module}.py`
- Test names describe behaviour, not implementation
- Fixtures live at module-top; no shared state across tests
- Never delete a passing test without explicit reviewer approval

## Refactoring philosophy

- **Atomic commits:** one logical change per commit
- **Prefer edits over rewrites:** use `edit` / `multi_edit` tools
- **Re-exports for backward compat:** when moving symbols, re-export from the original module with `# noqa: F401`
- **Smoke test before commit:** `python -m pytest tests/test_helpers_*.py` + a 24-endpoint smoke script

## Branch protection (recommended GitHub settings)

1. Require PR reviews before merge
2. Require status checks to pass:
   - `test (3.11)` and `test (3.12)`
3. Require branches to be up-to-date before merging
4. Squash-merge only (keep history tidy)
