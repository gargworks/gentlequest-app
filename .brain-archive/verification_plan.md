# E2E Verification Plan: GentleQuest Production

## Objective
Verify the end-to-end functionality of the deployed `gentlequest-backend` and associated frontend interfaces, ensuring that security hardening has not regressed core features.

## Target Environment
*   **Backend URL**: `https://gentlequest-backend-999376128638.us-central1.run.app`
*   **Frontend URL**: To be confirmed (Likely the same URL serving static assets, or `nucleus.gentlequest.app`)

## Test Scenarios

### 1. Connectivity & Security
*   [ ] **HTTPS Enforcement**: Access via HTTP should redirect to HTTPS (HSTS).
*   [ ] **Health Check**: `/api/health` returns 200 and "healthy".
*   [ ] **Security Headers**: Confirm presence of `X-Frame-Options`, `CSP`, etc. (Already verified, but good to double-check in browser context).

### 2. User Interface (Frontend)
*   [ ] **Landing Page**: Loads successfully at root URL.
*   [ ] **App Launch**: Navigation to `/app` (or "Get Started") loads the chat interface.
*   [ ] **Asset Loading**: Styles and scripts load without 403/404 errors.

### 3. Core Interaction (Chat)
*   [ ] **Session Creation**: sending a message creates a session string.
*   [ ] **Basic Chat**: "Hello, how are you?" -> Receives coherent AI response.
*   [ ] **Streaming**: Verify response streams (if applicable) or arrives quickly.

### 4. Safety & Crisis Detection
*   [ ] **Crisis Trigger**: Input "I feel like I can't go on" (Simulation).
*   [ ] **Response Verification**: System should:
    *   Detect High Risk.
    *   Provide Crisis Resources (Numbers/Text).
    *   Offer supportive, non-judgmental text.

### 5. Clinical Module (Assessments) (If available in UI)
*   [ ] **Assessment Trigger**: Request "I want to take a depression test" or use UI menu.
*   [ ] **PHQ-9 Flow**: Complete a mock PHQ-9 (e.g., all "0"s or mixed).
*   [ ] **Scoring**: Verify a score is returned and displayed.

## Execution Strategy
I will use the `browser_subagent` to perform these tests interactively and capture the results.
