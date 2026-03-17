#!/usr/bin/env python3
"""
Nucleus Incident Controller — Phase F/G (Autonomous Policy Engine + Policy Surface)
"Nucleus auto-heals itself so Lokesh can sleep."

A playbook-driven, outcome-aware incident controller that adapts its
behavior based on historical incident resolution success rates, and
exposes a reliability policy surface with autonomy bounds.

Architecture:
  1. PLAYBOOKS define detection conditions, ordered actions, and success criteria
  2. The ENGINE iterates playbooks, detects incidents, executes actions
  3. OUTCOME EVALUATION re-queries metrics after a delay to grade resolution
  4. POLICY STATE tracks per-type success rates and adapts cooldowns/flags
  5. POLICY SURFACE exposes stats, intent summaries, and autonomy bounds

Usage:
    python3 scripts/incident-controller.py                # Single check
    python3 scripts/incident-controller.py --daemon        # Continuous
    python3 scripts/incident-controller.py --dry-run       # Preview
    python3 scripts/incident-controller.py --evaluate      # Evaluate pending
    python3 scripts/incident-controller.py --policy-report # Show policy state

    npm run incident:check
    npm run incident:daemon
    npm run incident:dry-run

NOTE FOR FUTURE-SELF (AND AI TOOLS):
    This file is part of the "danger set" (autonomy + incident brain).
    - Do not auto-apply large refactors from code assistants without reading the diff.
    - Always run `pytest tests/test_pre_launch_validation.py` after modifying this file.
    - Treat changes here as proposals that must keep the safety envelope intact.
"""

import argparse
import copy
import datetime
import json
import logging
import os
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.parse