"""nucleus_wrapped — Phase-2 experimental-lane launcher package.

Spec: .brain/plans/phase2_experiment_design.md (peer-owned).
Scaffold ownership split (per cowork relay_20260421_130731_42e35387):
  - scripts/nucleus_wrapped/launch.py — peer lane (§2.1 8-step implementation)
  - scripts/nucleus_wrapped/__init__.py, tests/experimental_lane/,
    .github/workflows/experimental-lane.yml — main lane (plumbing)

Status: BUILD-AND-HOLD. Do not execute the launcher in CI or production
until §2 is founder-locked.
"""
