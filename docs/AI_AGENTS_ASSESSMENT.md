# AI Agents Assessment for GentleQuest

> **Date:** December 25, 2025  
> **Status:** Exploration / Future Reference  
> **Based on:** "How to Build AI Agents from Scratch" framework

---

## Current Architecture Summary

| Component | Current Implementation |
|-----------|------------------------|
| **AI Provider** | Direct API calls to Gemini/OpenAI/Perplexity with multi-key rotation |
| **Conversation** | In-memory dict + DB logging (no long-term context) |
| **Crisis Detection** | Rule-based keyword matching |
| **Tools** | None - pure Q&A chatbot |
| **Memory** | Session-based only (1-hour timeout) |
| **Orchestration** | Single Flask monolith |

---

## Agent Approach Analysis

### ✅ Would Benefit Your Project

| Step | Benefit | How It Applies | Implementation Path |
|------|---------|----------------|---------------------|
| **Step 4: Reasoning + Tools** | ⭐⭐⭐⭐ | Allow Luna to access wellness tools (mood tracker, journal prompts, breathing exercises) | LangChain or direct function calling |
| **Step 6: Memory/RAG** | ⭐⭐⭐⭐⭐ | Remember user's emotional patterns across sessions | ChromaDB/Pinecone + LangChain Memory |
| **Step 3: Prompt Tuning** | ⭐⭐⭐⭐ | Already doing this, but could systematize with personas | Current prompts are good, could enhance |
| **Step 8: Structured Output** | ⭐⭐⭐ | Return structured wellness recommendations | Pydantic + function calling |

### ⚠️ Possible But Not Critical

| Step | Assessment | Why |
|------|------------|-----|
| **Step 5: Multi-Agent** | Overkill for now | You don't need Planner/Researcher/Reporter agents yet |
| **Step 7: Voice/Vision** | Optional enhancement | Could add emotion detection from text analysis |
| **Step 10: Eval/Monitor** | Good idea | Already have Sentry; add AI-specific metrics later |

### ❌ Not Recommended Yet

| Step | Why Not |
|------|---------|
| **CrewAI/LangGraph** | Adds complexity without proportional benefit for a mental health chatbot |
| **OpenAI Swarm** | Over-engineered for your use case |

---

## Practical Recommendations

### High-Value, Low-Risk Additions

#### 1. Memory Layer (RAG) - Most Impactful
- Store conversation summaries in vector DB (ChromaDB is free, local)
- Retrieve relevant past context before generating responses
- **Cost:** ~$0.001/query for embeddings
- **Tools:** `chromadb`, `sentence-transformers`

#### 2. Function Calling/Tools - Already Supported by Gemini
```python
# Your Gemini provider already uses google-generativeai
# Add tool declarations for:
# - log_mood(level, note)
# - get_breathing_exercise()
# - schedule_checkin(time)
# - get_journal_prompt()
```

#### 3. Structured Crisis Response
- Replace string-based crisis detection with JSON schema output
- Better parsing, more reliable actions

---

## Cost & Compatibility Analysis

| Tool | Cost | Compatible? | Scalable? |
|------|------|-------------|-----------|
| **LangChain** | Free | ✅ Python | ✅ Yes |
| **ChromaDB** | Free (self-host) | ✅ Python | ⚠️ Limited |
| **Pinecone** | ~$70/mo starter | ✅ API | ✅ Yes |
| **CrewAI** | Free | ⚠️ Heavy deps | ⚠️ Overhead |
| **LangGraph** | Free | ⚠️ Complex | ✅ Yes |
| **Gemini Function Calling** | Included in API | ✅ Already using | ✅ Yes |

---

## Recommendation Summary

> **Start with Gemini's native function calling** (no new dependencies!) to add tools like mood logging and breathing exercises. Then add **ChromaDB for memory** when you want Luna to remember users across sessions.
>
> **Don't adopt** full agent frameworks (CrewAI, LangGraph) until you have clear multi-step reasoning needs. Your current architecture is clean and efficient for a supportive chatbot.

---

## Next Steps (When Ready)

1. **Phase 1:** Add Gemini function calling for wellness tools
2. **Phase 2:** Implement ChromaDB for conversation memory
3. **Phase 3:** Evaluate multi-agent needs based on product evolution

---

## Reference Materials

- Original infographic: "How to Build AI Agents from Scratch" by Dr. Maryam Miradi
- Tools mentioned: LangChain, ChromaDB, Pinecone, CrewAI, LangGraph, OpenAI Swarm
