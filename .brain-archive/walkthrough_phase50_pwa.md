
# Walkthrough: Nucleus HUD PWA Architecture (Phase 50)

> **Date:** 2026-01-11
> **Status:** ✅ Completed
> **Target:** `tools/nucleus-hud`

## 🎯 Goal
Transform the **Nucleus HUD** (Admin Dashboard) into a **Progressive Web App (PWA)** to enable:
1.  **Offline Capability**: Access the dashboard even without an internet connection.
2.  **Installability**: Install as a standalone app on Desktop/Mobile.
3.  **Stability**: Removed unused code causing build failures.

## 🛠 Changes Implemented

### 1. Dependencies
- Installed `@ducanh2912/next-pwa` (Next.js 16+ compatible).
- Uninstalled `recharts` (Unused).

### 2. Configuration (`next.config.ts`)
- Wrapped configuration with `withPWAInit`.
- Configured to output Service Worker to `public/`.
- **Optimization**: Forced `--webpack` build to resolve Next.js 16 Turbopack compatibility issues.

### 3. Assets
- **Manifest**: Created `public/manifest.json`.
- **Icon**: Generated and deployed `public/icon.png`.

### 4. Cleanup (Tech Debt)
- **Deleted Unused Components**:
  - `GenericMetaTags.tsx` (Removed broken `react-helmet` dependency).
  - `GenericWellnessChart.tsx` (Removed unused `recharts` dependency).
  - `GenericPHQ9.tsx` (Unused).
  - `GenericCrisisModal.tsx` (Unused).

## ✅ Verification
- **Build Success**: `npm run build` passes with generated Service Worker.
- **Assets Present**: `sw.js`, `workbox-*.js`, `manifest.json`, `icon.png` verified in `public/`.

## 🚀 How to use
The HUD is now installable. When deployed or run locally (`npm run start`), your browser will offer an "Install" option. Offline access works automatically via the Service Worker.
