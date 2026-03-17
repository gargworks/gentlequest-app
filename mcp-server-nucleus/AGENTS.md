# Nucleus Agent Guidelines

This file defines guidelines for AI agents working on the Nucleus codebase.

---

## Principles

1. **Read before write** — understand existing code before modifying it
2. **Branch, don't mutate** — work on branches, test, merge only after tests pass
3. **Append-only brain** — never overwrite engrams, ledger entries, or event logs
4. **Test coverage** — new features require tests. Bug fixes require regression tests.
5. **Security first** — no secrets in committed files. Run pre-commit hooks.

## Guardrails

| Area | Do | Don't |
|------|-----|-------|
| Code | Generate modules, functions, refactors, tests | Rewrite release scripts or CI gates |
| Docs | Draft comments, docstrings, README sections | Edit governance docs without review |
| Brain | Read engrams, query state, write new engrams | Overwrite or delete existing brain data |
| Releases | Propose version bumps with changelog | Push releases without test validation |

## Safety

- Pre-launch validation must show ≥18/20 tests passing before any release tag
- Any destructive operation (delete, overwrite, force-push) requires confirmation
- Circuit breaker: if 3 consecutive operations fail, stop and report

---

*For contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).*
