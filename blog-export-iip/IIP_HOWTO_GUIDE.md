# IIP How-To Guide: From Idea to Engineering Specs

> **Product**: IIP (Innovation Implementation Platform)  
> **URL**: https://iip-frontend-999376128638.us-central1.run.app  
> **Purpose**: Transform vague product ideas into structured engineering work

---

## What is IIP?

IIP is a **Product Discovery Engine** that prevents you from coding in the dark. Instead of jumping straight to implementation, IIP forces structured thinking:

| Stage | What Happens | Output |
|-------|--------------|--------|
| **1. Interview** | AI asks clarifying questions | Validated concept |
| **2. Personas** | AI synthesizes user archetypes | 3-5 User Personas |
| **3. CVP Canvas** | AI identifies value proposition | Core Value + Pain/Gain Matrix |
| **4. Roadmap** | AI breaks down into features | MVP Roadmap with priorities |
| **5. Tasks** | AI converts to engineering tickets | Actionable work items |
| **6. Project Brain** | RAG-powered Q&A about your project | Strategic answers |

---

## Quick Start (5 Minutes)

### Step 1: Create a Team
1. Open https://iip-frontend-999376128638.us-central1.run.app
2. Click the **"+"** button (bottom right)
3. Enter:
   - **Team Name**: Your project name (e.g., "SaaS Dashboard")
   - **Project Focus**: One-sentence description (e.g., "Analytics dashboard for indie hackers")
4. Click **Create**

### Step 2: Conduct the Interview
1. Click the **💬 Chat icon** next to your project
2. Answer the AI Research Assistant's questions honestly
3. Share context about:
   - Who are your users?
   - What problem are you solving?
   - What's your tech stack?
4. Click the **✓ Checkmark** to finalize

### Step 3: Generate Artifacts
After the interview:
1. **Personas**: Click 👤 icon → "Generate Personas"
2. **CVP Canvas**: Click 📊 icon → "Generate with AI"
3. **Roadmap**: Click 🗺️ icon → "Generate with AI"
4. **Tasks**: Click ✅ icon → "Generate Tasks from Roadmap"

### Step 4: Query the Project Brain
1. Click the **🧠 Brain icon**
2. Ask questions like:
   - "What is the core value prop?"
   - "Who is the primary persona?"
   - "What should we build first?"

---

## Diverse Use Case Examples

### Use Case 1: Mental Health App (GentleQuest)

**Input**:  
> "A mobile app that helps overwhelmed developers take tiny mental health breaks through gamified breathing exercises."

**Generated Outputs**:
- **Persona**: "Alex the Anxious Coder" - Sr. Engineer, 60+ hour weeks, uses VSCode
- **CVP**: "Progress without pressure - tiny wins that compound"
- **Roadmap Feature**: "Breathing Exercise Module with Haptic Feedback"
- **Task**: "Implement 4-7-8 breathing animation with Lottie"

---

### Use Case 2: Developer Productivity Tool

**Input**:  
> "I want to build a mobile app where completing coding tasks earns you XP and loot driven by GitHub activity."

**Generated Outputs**:
- **Persona**: "Gina the Gamified Developer" - Mid-level dev, loves RPGs, motivated by streaks
- **CVP**: "Turn mundane commits into epic quests"
- **Roadmap Feature**: "GitHub OAuth Integration + Activity Tracker"
- **Task**: "Design XP calculation algorithm based on commit frequency"

---

### Use Case 3: SaaS Analytics Dashboard

**Input**:  
> "A lightweight analytics dashboard for indie hackers who are overwhelmed by Google Analytics."

**Generated Outputs**:
- **Persona**: "Sam the Solo Founder" - Non-technical, needs simple metrics
- **CVP**: "Analytics that actually fit in your brain"
- **Roadmap Feature**: "One-Page Dashboard with 5 Core Metrics"
- **Task**: "Implement server-side page view tracking without cookies"

---

### Use Case 4: E-commerce Platform

**Input**:  
> "A marketplace for handmade crafts targeting Gen-Z buyers who want sustainable products."

**Generated Outputs**:
- **Persona**: "Zoe the Conscious Shopper" - 24, values transparency, will pay premium for ethics
- **CVP**: "Shop your values, not just prices"
- **Roadmap Feature**: "Sustainability Score per Product"
- **Task**: "Create seller onboarding form with carbon footprint calculator"

---

## Interface Reference

### Dashboard Icons

| Icon | Action | When to Use |
|------|--------|-------------|
| 💬 | Launch Interview | First step after creating a project |
| 👤 | View/Generate Personas | After completing interview |
| 📊 | View/Generate CVP Canvas | After personas exist |
| 🗺️ | View/Generate Roadmap | After CVP is defined |
| ✅ | View/Generate Tasks | After roadmap has features |
| 🧠 | Project Brain (RAG) | Anytime for strategic queries |

---

## Tips for Best Results

1. **Be Specific in Interviews**: "Analytics for indie hackers" is better than "analytics tool"
2. **Answer All Questions**: The AI uses your answers to synthesize insights
3. **Regenerate if Needed**: Each generation can be re-triggered for variety
4. **Use Project Brain**: It has access to ALL your project data (interviews, personas, CVP, roadmap)

---

## Technical Details

- **Backend**: FastAPI (Python) on Cloud Run
- **Frontend**: Flutter Web
- **LLM**: Google Gemini 2.0 Flash
- **Database**: PostgreSQL (Cloud SQL)
- **RAG**: Context Stuffing (all artifacts injected into LLM prompt)

---

## Provenance
- **Session ID**: `6c8d0959-9c69-4eb5-8e9c-303dd8b732ac`
- **Date Generated**: 2026-01-15
- **Tool**: Gemini Code Assist (Antigravity) + IIP Backend
- **Verification**: Live E2E Browser Test Passed (2026-01-15)
