
# Implementation Plan - Phase 51: Clinical Integration

> **Goal:** Activate the "Clinical Testing" capabilities in the Nucleus HUD.
> **Target:** `tools/nucleus-hud`

## Proposed Changes

### 1. New Route (`app/clinical/page.tsx`)
- Create a new page accessible at `/clinical`.
- Render `NucleusPHQ9` as the primary widget.
- Include a manual "Trigger Crisis" button to test `NucleusCrisisModal`.

### 2. Navigation
- Add a "CLINICAL" link to the existing Navigation (wherever it is, likely `layout.tsx` or a Sidebar component).
- If no Global Nav exists, add specific link to `app/page.tsx`.

### 3. Component Integration
- Connect `NucleusPHQ9` to trigger `NucleusCrisisModal` if `isCrisis` state is detected (Currently `NucleusPHQ9` validates Q9 but shows an alert div. Upgrade it to use the Modal?).
- *Refinement:* Pass `onCrisis={handleCrisis}` to `NucleusPHQ9`?
- Current `NucleusPHQ9` has internal logic. I might need to Modify `NucleusPHQ9` to accept a callback or use the Modal internally.

## Verification Plan

### Automated Tests
- `npm run build` to ensure no Type Errors.

### Manual Verification
- Navigate to `/clinical`.
- Complete PHQ9.
- Verify Score Calculation.
- Check Crisis Modal appearance.
