# Implementation Plan - Phase 8b Verification (Outcome Dashboard)

## Goal
Verify the end-to-end functionality of the Clinical Outcomes Dashboard backend.
Now that the Python 3.14/Protobuf blocker is resolved (Phase 50), we can validte that data flows correctly from submission to retrieval.

## Scope
- Endpoint: **POST** `/api/self_assessment` (Submission)
- Endpoint: **GET** `/api/assessment/history` (Retrieval)
- Verification of:
  - Session ID persistence validation.
  - Required field handling.
  - Data retrieval by session.

## Proposed Changes
No production code changes. Adding a verification tool only.

### [New Script] `scripts/verify_clinical_outcomes.py`
A standalone Python script that:
1.  Generates a random `Test-Session-UUID`.
2.  **POST**s a standard payload (mood, energy, sleep, stress) to `/api/self_assessment`.
3.  Asserts response status is **201 Created**.
4.  **GET**s `/api/assessment/history?session_id=...`.
5.  Asserts response status is **200 OK**.
6.  Asserts the submitted assessment is present in the returned list.
7.  Prints "✅ Verification Passed" or full error details.

## Verification Plan

### Automated
- Run `python3.11 scripts/verify_clinical_outcomes.py` while `app.py` is running.

### Manual Reference (Frontend Simulation)
- This script simulates exactly what the `NucleusWellnessChart` (Frontend) does.
