# Governance

## Decision-Making Framework

Nucleus follows the **Hypothesis Loop** for all strategic and technical decisions:

1. **Form Hypothesis** — Tightly scoped, measurable claim
2. **Define Failure Condition** — Exact metric that invalidates it
3. **Execute Minimum Test** — Smallest possible validation
4. **Pivot or Iterate** — If invalidated, pivot immediately; if validated, form Hypothesis N+1

No sunk cost attachment. No "just ship it" without validation.

## Roles

| Role | Responsibility |
|------|---------------|
| **Founder** | Final authority on roadmap, monetization, and strategic pivots |
| **Core Maintainers** | Merge authority, architecture decisions, release management |
| **Contributors** | Feature development, bug fixes, documentation, recipes |
| **Community** | Feedback, issue reporting, pattern contributions, beta testing |

## Contribution Tiers

### Tier 1: Community Contributor
- Submit issues, PRs, documentation fixes
- Contribute recipes and patterns
- Participate in discussions

### Tier 2: Recognized Contributor
- Consistent quality contributions over 3+ months
- Invited to architecture discussions
- Listed in CONTRIBUTORS.md

### Tier 3: Core Maintainer
- Merge authority on non-breaking changes
- Release management participation
- Architecture review responsibility

## Decision Types

### Technical Decisions
- Architecture changes require Core Maintainer review
- Breaking changes require Founder approval
- New dependencies require security review

### Strategic Decisions
- Roadmap changes: Founder + Core Maintainer consensus
- Pricing changes: Founder authority with community input
- Partnership decisions: Founder authority

### Community Decisions
- Code of Conduct enforcement: Core Maintainer consensus
- New Recognized Contributors: Core Maintainer nomination + Founder approval

## Release Process

1. Feature branches merge to `main` via PR
2. All tests must pass (`pytest tests/`)
3. CHANGELOG.md updated with changes
4. Version bump in `pyproject.toml`
5. Tag and release via GitHub Actions

## Transparency

- All non-security decisions are made in public GitHub issues/discussions
- Architecture Decision Records (ADRs) stored in `.brain/artifacts/`
- The 42-Round Audit methodology is applied to major strategic pivots

## Conflict Resolution

1. Technical disagreements → Resolved by benchmarks and data
2. Design disagreements → Resolved by Hypothesis Loop testing
3. Community disputes → Code of Conduct enforcement
4. Escalation → Founder has final authority

## HITL Gates

Certain actions require human-in-the-loop approval:

- **File deletion** — Always requires explicit confirmation
- **External API calls** — Require user consent
- **Code commits** — Require review before push
- **Financial commits** — Require FOUNDER_APPROVED status
- **Roadmap pivots** — Require 42-Round Audit methodology

---

*Governance maintained by the Nucleus team.*
*Last updated: March 2026*
