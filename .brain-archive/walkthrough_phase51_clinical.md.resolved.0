
# Walkthrough: Clinical Integrations (Phase 51)

> **Date:** 2026-01-11
> **Status:** ✅ Completed
> **Target:** `tools/nucleus-hud`

## 🎯 Goal
Activate the **Clinical Assessment Testing** capabilities in the Nucleus HUD, enabling operators to validate safety protocols (e.g., PHQ-9 Crisis Flags) directly in the dashboard.

## 🛠 Changes Implemented

### 1. New Route (`/clinical`)
- Created `app/clinical/page.tsx`.
- Implemented a "Clinical Testing Suite" layout.

### 2. Component Activation
- **`NucleusPHQ9`**: 
  - Integrated into the new page.
  - **Upgrade**: Replaced static alert with interactive `NucleusCrisisModal`.
- **`NucleusCrisisModal`**:
  - Activated and linked to PHQ-9 logic.
  - Confirmed accessibility (988/911 hotlinks) and styling (Matrix Red/Black).

### 3. Navigation
- Added `CLINICAL` link to the main HUD header in `app/page.tsx`.

## ✅ Verification
- **Build**: `npm run build` passed.
- **Integration**: Component imports resolved and types aligned.
- **Deployment**: Pushed to `main` (Cloud Build Triggered).

## 🚀 How to use
1. Open Nucleus HUD.
2. Click **CLINICAL** in the header.
3. Take the PHQ-9 Assessment.
4. **Test Crisis Logic**: Answer "More than half the days" (2) or "Nearly every day" (3) on **Question 9**.
5. Verify the **Red Safety Modal** appears.
