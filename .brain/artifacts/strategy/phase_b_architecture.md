# Phase B: Pattern Cloud Architecture (v2)

## 🎯 Goal
Enable network effects by allowing users to (optionally) share anonymized patterns to improve recommendations for everyone.

---

## 📊 The Flywheel

```
User joins (free) → Uses patterns → Shares patterns (opt-in)
         ↑                                    ↓
   Better patterns ←←←← Vector Search ←←←← Pattern Cloud
```

---

## 🏗 Architecture Components

### 1. Backend: Supabase
- **Database:** PostgreSQL + `pgvector` extension
- **Auth:** Supabase Auth (Device Flow for CLI)
- **Edge Functions:** Embedding generation, Anonymization checks
- **Storage:** Pattern content (JSONB)

### 2. Client: `nucleus-sync`
- **Daemon:** Background process watching `.brain/`
- **CLI:** `nucleus login`, `nucleus sync`
- **Privacy Filter:** Local REGEX-based PI scrubbing before upload

---

## 📦 Data Schema (Refined)

### `patterns` table
```sql
create extension vector;

create table patterns (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id), -- NULL if totally anon, but better to track reputation
  
  -- Content & Search
  content jsonb not null,
  description text,
  tags text[],
  embedding vector(1536), -- For semantic search
  
  -- Metadata
  pattern_hash text not null, -- SHA256 for deduplication
  pattern_type text not null, -- 'trigger', 'agent_prompt', 'workflow'
  language text default 'english',
  
  -- Metrics
  usage_count int default 0,
  avg_rating float default 0,
  
  -- Safety & Visibility
  is_public boolean default true,
  moderation_status text default 'pending', -- 'approved', 'rejected'
  
  created_at timestamp default now(),
  updated_at timestamp default now()
);

-- Search Index
create index on patterns using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);
```

### `pattern_ratings` table
```sql
create table pattern_ratings (
  id uuid primary key default gen_random_uuid(),
  pattern_id uuid references patterns(id),
  user_id uuid references auth.users(id),
  rating int check (rating >= 1 and rating <= 5),
  comment text,
  created_at timestamp default now()
);
```

---

## 🔐 Privacy & Safety Design

### 1. Local Anonymization (Client-Side)
Before any data leaves the machine:
- **Project Names:** Replaced with `{{PROJECT}}`
- **File Paths:** Stripped or generalized
- **PII:** Named Entity Recognition (NER) or Regex to scrub names/emails
- **User Confirmation:** CLI shows diff of "What will be sent" vs "Original"

### 2. Remote Moderation (Server-Side)
- **Automated:** OpenAI Moderation API check on upload
- **Community:** "Report" button on patterns
- **Status:** Patterns with `moderation_status = 'rejected'` are never synced down

---

## 🔑 Authentication Flow (CLI)

1. User runs `nucleus login`
2. CLI requests code from Supabase Auth
3. CLI opens browser: `https://nucleus.app/activate?code=ABCD-1234`
4. User confirms in browser
5. CLI receives access token + refresh token
6. Token stored securely (system keychain)

---

## 🔎 Discovery & Recommendations

### Vector Search
*   **Query:** "I need a pattern for writing python tests"
*   **Process:** 
    1. Embed query → Vector
    2. Cosine similarity search against `patterns.embedding`
    3. Filter by `moderation_status = 'approved'`
    4. Rank by `avg_rating` boost

### "Similar brain" Recommendations
*   **Implementation:** 
    1. Embed user's current `state.json` (focus area)
    2. Find patterns used by other users with similar state embeddings
    3. Recommend: "Users working on 'React Migration' also found this 'Refactoring Agent' helpful"

---

## 🔄 Sync Flow

```
┌──────────────────────┐        ┌──────────────────────┐
│   User's Machine     │        │    Pattern Cloud     │
│                      │        │                      │
│ nucleus login        │ ────>  │ Supabase Auth        │
│                      │ <────  │ (Access Token)       │
│                      │        │                      │
│ nucleus sync         │        │                      │
│ 1. Read .brain       │        │                      │
│ 2. Anonymize/Scrub   │        │                      │
│ 3. Hash Content      │        │                      │
│ 4. Upload (JSON)     │ ────>  │ Edge Function        │
│                      │        │ 1. Generate Embedding│
│                      │        │ 2. Run Moderation    │
│                      │        │ 3. Store in DB       │
│                      │        │                      │
│ brain_suggest        │ <────  │ API (pgvector)       │
│ "Suggest tools..."   │        │ Returns top k        │
└──────────────────────┘        └──────────────────────┘
```

---

## 📋 Implementation Roadmap (Revised)

### Week 1: Foundation
- [ ] Supabase project setup (Auth + DB + Vector)
- [ ] `nucleus login` command (Device Flow)
- [ ] Basic `patterns` CRUD API

### Week 2: Intelligence
- [ ] Edge Function for OpenRouter/OpenAI embeddings
- [ ] Edge Function for Moderation API
- [ ] `nucleus sync` command with local anonymization regex

### Week 3: Integration
- [ ] `brain_search_patterns` MCP tool
- [ ] `brain_download_pattern` MCP tool
- [ ] Telemetry (PostHog) integration to track usage

---

## 💰 Monetization Strategy

| Feature | Free | Pro ($19/mo) |
|---------|------|--------------|
| **Public Patterns** | ✅ Unlimited | ✅ Unlimited |
| **Search** | ✅ Basic | ✅ Priority/Advanced |
| **Private Sync** | ❌ | ✅ Encrypted Backup |
| **Team Sharing** | ❌ | ❌ (Team Plan $99) |
