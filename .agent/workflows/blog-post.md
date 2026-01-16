---
description: Create and publish a blog post for GentleQuest or Nucleus
---

# Blog Post Workflow (Enhanced)

> **Companion Doc**: [BLOG_PIPELINE_STRATEGY.md](../docs/blog-pipeline/BLOG_PIPELINE_STRATEGY.md) — Master list of blog ideas, series, and pipeline status.

This is the **execution protocol** for writing a blog post. The Pipeline Strategy is the **what to write**; this doc is the **how to write it**.

This workflow consolidates all blog publishing operations for **GentleQuest**, **Nucleus**, and **IIP** products.

## Blog Type Taxonomy

| Type | Purpose | Example |
|------|---------|---------|
| **Walkthrough** | Step-by-step technical guide | "Deploying to Cloud Run" |
| **Benchmark** | Comparative analysis with proof | "IIP vs ChatGPT: 3 Stress Tests" |
| **Opinion** | Founder perspective/essay | "Why Local-First AI Matters" |
| **Announcement** | Product launch/feature release | "Introducing Clinical Assessments" |

---

## Step 0: Pipeline Check & Suggestions (Interactive)

**When this workflow is invoked, the agent should:**

1. **Read the Pipeline**: Check `docs/blog-pipeline/BLOG_PIPELINE_STRATEGY.md` for:
   - Ready-to-publish posts (📦)
   - High-priority ideas (📝)

2. **Offer Suggestions**:
   > "Based on your pipeline, here are blog options:
   > 1. **Publish Ready**: `BLOG_IIP_VS_CHATGPT_STRESS_TEST.md` (just needs deploy)
   > 2. **High Priority Idea**: 'How We Cut Render Bill 70%' (from Billing Rescue chat)
   > 3. **Write something new**: Describe your topic
   > 
   > Which would you like to work on?"

3. **Proceed if suitable**: If user picks an option, execute the remaining steps.

> [!NOTE]
> This makes `/blog-post` a proactive assistant, not just a static checklist.

---

## Related Documents

| Document | Path | Purpose |
|----------|------|---------|
| **Blog Export Protocol** | `blog-export-20260114/BLOG_EXPORT_PROTOCOL.md` | Anti-hallucination safeguards, provenance tracking |
| **Nucleus Growth Strategy** | `docs/NUCLEUS_GROWTH_STRATEGY.md` | Channel strategy, posting protocols |
| **GentleQuest Reddit Growth** | `docs/GENTLEQUEST_REDDIT_GROWTH_STRATEGY.md` | Reddit-specific distribution |
| **Growth Automation** | `docs/product/GROWTH_AUTOMATION_STRATEGY.md` | Marketing → Product loop |
| **Oracle Audit** | `.agent/workflows/oracle-audit.md` | Anti-hallucination verification workflow |
| **Archive Protocol** | `.agent/workflows/archive.md` | Post-publish consolidation |
| **Blog Pipeline** | `docs/blog-pipeline/BLOG_PIPELINE_STRATEGY.md` | Master list of blog ideas from all conversations |
| **MASTER_SESSION_REPORT** | `.brain/artifacts/synthesis/` | Exhaustive research (ADHD, B2B, Growth Loops) |

### Tech Stack Quick Reference

| Blog | Framework | Template | Deployment |
|------|-----------|----------|------------|
| GentleQuest | Astro Blog | Default blog theme | Render Static |
| Nucleus | Astro + Starlight | Docs + Blog hybrid | Render Static |

### SGE/GEO Optimization Checklist (from Growth Loop research)

- [ ] TL;DR in first 2 sentences (AI engines cite this)
- [ ] Comparison tables (structured data for citations)
- [ ] Inline code blocks with language tags
- [ ] Provenance footer (builds trust, prevents plagiarism claims)
- [ ] Cross-link to companion blog (builds topic authority)

> [!TIP]
> Run `/oracle-audit` before publishing any Benchmark or Walkthrough post to validate claims.

---

## Target Audience Personas (from cross-chat decisions)

| Product | Primary Persona | Pain Point | Preferred Channels |
|---------|-----------------|------------|-------------------|
| **GentleQuest** | "Alex the Anxious Coder" - Sr. Engineer, 60+ hour weeks, burnout | "I don't have time for mental health but I need it" | Twitter, LinkedIn, r/ExperiencedDevs |
| **Nucleus** | "Context-Fatigued Claude User" - Solo founder, >10 AI chats/day | "My agent forgets everything between sessions" | r/ClaudeAI, r/LocalLLaMA, Hacker News |
| **IIP** | "The Overwhelmed Builder" - Technical PM, idea-to-execution gap | "I have 10 ideas but can't prioritize" | LinkedIn, Twitter, r/startups |

### Channel-Persona Fit

| If targeting... | Focus on... | Avoid... |
|-----------------|-------------|----------|
| Experienced Devs | Technical depth, code samples | Marketing speak, vague benefits |
| Solo Founders | ROI, time savings, "scratch your own itch" | Enterprise jargon |
| PMs / Strategists | Frameworks, decision matrices | Implementation details |

> [!NOTE]
> These personas were synthesized from IIP stress tests and past growth strategy conversations. Update as user research evolves.

---

## Prerequisites
- Identify target blog:
  - **GentleQuest Product Blog:** `gentlequest-blog/src/content/blog/`
  - **Nucleus Technical Blog:** `mcp-server-nucleus/website/src/content/docs/blog/`
  - **IIP Documentation:** Export to `blog-export-{topic}/` bundle

---

## Step 0: Pre-Write Research (NEW)

Before writing, gather evidence:

1. **For Benchmark Posts:**
   - Run stress tests via `browser_subagent` or API scripts
   - Capture recordings (`.webp`) and screenshots (`.png`)
   - Document competitor/baseline outputs for honest comparison

2. **For Walkthrough Posts:**
   - Execute the workflow yourself first
   - Capture terminal output and UI states
   - Note any gotchas or error cases

3. **For Opinion Posts:**
   - Reference prior art (link to sources)
   - Ground claims in observable data

---

## Step 1: Create the Post

1. **Choose a filename:** Use kebab-case (e.g., `streaks-are-broken.md`).
2. **Add frontmatter:**

### GentleQuest Blog Frontmatter
```yaml
---
title: "Your Post Title"
description: "A brief description (2-3 sentences)."
pubDate: "2026-MM-DD"
author: "GentleQuest Team"  # Do NOT use personal names
tags: ["Mental Health", "Product Design", "Topic"]
---
```

### Nucleus Blog Frontmatter
```yaml
---
title: Your Post Title
description: A brief description.
date: 2026-MM-DD
author: "Nucleus Team"  # Do NOT use personal names
tags: ["Local-First", "AI Memory", "Topic"]
---
```

---

## Step 2: Write Content (GEO-First)

Structure for **Generative Engine Optimization**:

1. **TL;DR Hook (First 2 sentences):** Answer the question "Why should I care?" immediately.
2. **Comparison Tables:** Use tables for any A vs B analysis (AI engines love structured data).
3. **Short Paragraphs:** 2-3 sentences max. Scannable > Dense.
4. **Code Blocks with Language Tags:** Always specify language (```python, ```bash).
5. **Embedded Media:**
   - Use `![Caption](/path/to/asset.webp)` for recordings
   - Use `![Caption](/path/to/asset.png)` for screenshots
   - Store in `./assets/` relative to post

---

## Step 3: Embed Media (NEW)

### For Browser Recordings:
```markdown
![Walkthrough Recording](/assets/iip_stresstest_case1_seniorlink.webp)
```
- WebP files from `browser_subagent` are animated (~30MB each)
- Include timestamps in filenames for provenance

### For Screenshots:
```markdown
![Dashboard State](/assets/dashboard_after_deploy.png)
```

### For Terminal Output:
Use fenced code blocks with `text` or `bash` language tag.

---

## Step 4: Anti-Hallucination Validation

**Required for all Nucleus posts. Recommended for others.**

### Source Verification Checklist (from BLOG_EXPORT_PROTOCOL.md)

| Check | Action | Evidence |
|-------|--------|----------|
| **Code snippets** | All code must exist in the repo | Verify file paths with `ls` or `cat` |
| **Terminal output** | Must be from actual command execution | Check command IDs in Antigravity logs |
| **Recordings (.webp)** | Must be from browser_subagent captures | Timestamp in filename proves real capture |
| **Statistics/Metrics** | Must come from actual tool outputs | Cross-reference with Cloud Console/logs |

### Path Validation Script
```bash
#!/bin/bash
set -e  # Kill Switch: Exit immediately on any error

# Validate all file paths in markdown exist
grep -oE '/[^)]+\.(webp|png|jpg)' POST.md | while read path; do
  if [ ! -f "$path" ]; then
    echo "❌ MISSING: $path"
    exit 1
  else
    echo "✅ FOUND: $path"
  fi
done

echo "✅ All paths verified."
```

### Provenance Footer (Required)
```markdown
---
## Provenance
- **Session ID:** `{conversation_id}`
- **Date Generated:** {YYYY-MM-DD}
- **Tool:** Gemini Code Assist (Antigravity) + Nucleus MCP Server
- **Verification:** `/oracle-audit` passed on {AUDIT_DATE}
- **Sources:**
  - Cloud Run Logs: `gcloud run services logs read {SERVICE}`
  - Recordings: {List .webp files with timestamps}
  - Code Files: {List modified files}
```

> [!CAUTION]
> **Kill Switch**: If any media paths are missing or any statistics cannot be verified, do NOT publish. Fix the issue or remove the claim.

---

## Step 5: Cross-Link Products

| If writing for... | Link to... |
|-------------------|-----------|
| GentleQuest | Nucleus technical deep-dive |
| Nucleus | GentleQuest product impact story |
| IIP | Both (it's the bridge) |

Example:
```markdown
*Read how we apply these principles to mental health in our companion post on the [GentleQuest Blog: Streaks are Broken](...).*
```

---

## Step 6: Create Export Bundle (NEW)

For portable distribution:
```bash
mkdir -p blog-export-{topic}/assets
cp POST.md blog-export-{topic}/
cp *.webp *.png blog-export-{topic}/assets/
# Update paths to relative
sed -i '' 's|/absolute/path/to/brain/[^/]*/|./assets/|g' blog-export-{topic}/*.md
```

---

## Step 7: Build & Verify (with Lint Checks)

**Common Blog Build Issues (from past sessions):**

| Issue | Cause | Fix |
|-------|-------|-----|
| `frontmatter error` | Missing required field | Add `pubDate` or `date` field |
| `image not found` | Absolute path in markdown | Use relative `./assets/` paths |
| `MDX compile error` | Unescaped `<` or `{` in text | Wrap in backticks or escape |
| `astro:content` type error | Schema mismatch | Check `src/content/config.ts` |

// turbo
1. Navigate to the blog directory:
   - `cd gentlequest-blog` OR `cd mcp-server-nucleus/website`
// turbo
2. Install dependencies (if needed):
   - `npm install`
// turbo
3. **Run lint check first:**
   - `npm run lint` (if available) or `npx astro check`
4. Fix any lint errors before building.
// turbo
5. Build the site:
   - `npm run build`
6. Verify the post appears in the build output (e.g., `/dist/blog/your-post-slug/index.html`).

> [!WARNING]
> If build fails, check the terminal output for line numbers. Common culprits:
> - Unclosed markdown links: `[text](url` → `[text](url)`
> - Invalid YAML in frontmatter (wrong indentation)
> - WebP files larger than 50MB may timeout on some hosts

---

## Step 8: Commit & Push

// turbo
1. Stage changes:
   - `git add .`
2. Commit with a descriptive message:
   - `git commit -m "content(blog): Add 'Your Post Title' post"`
// turbo
3. Push to main:
   - `git push origin main`

---

## Step 9: Distribution Strategy (2026 GEO)

**Generative Engine Optimization (GEO)** means structuring content so AI search engines (Perplexity, ChatGPT Browse, Google SGE) can cite you.

### Channel Matrix (from NUCLEUS_GROWTH_STRATEGY.md)

| Channel | Format | Goal | Best For |
|---------|--------|------|----------|
| **Twitter/X** | "Build in Public" threads | 100 followers / 10 beta users | Announcements, Walkthroughs |
| **r/ClaudeAI** | Workflow optimization | 20 quality comments | Benchmarks, Technical posts |
| **r/LocalLLaMA** | "Memory for local models" | Tech validation | Nucleus-specific posts |
| **LinkedIn** | Professional insight | B2B credibility | Opinion pieces, Founder essays |
| **Hacker News** | Technical depth | Top 10 rank | Benchmarks, Open Source launches |
| **GitHub** | README + Releases | Stars & Issues | Any post with code |

### Platform-Specific Framing Rules

**r/ClaudeAI / r/LocalLLaMA:**
- ❌ Do NOT pitch: "Use our product."
- ✅ DO share: "I built a script to solve X because I was frustrated. Here's the repo."
- Frame as "scratch your own itch" → Developers love authenticity.

**Twitter/X:**
- Always include a visual (screenshot, GIF, or recording)
- Tags: `#buildinpublic #AI #Claude #Cursor #DevTools`
- Thread format: Hook → 3-5 insights → CTA with link

**LinkedIn:**
- Professional framing, no hashtag spam
- "What we learned" > "What we built"
- Encourage comments with a question at the end

**Hacker News:**
- Title must be factual, no hype ("Show HN: Local-first AI memory" not "Revolutionary AI Memory System")
- First comment should be from you explaining context
- Only post Benchmarks or Open Source launches

### Post Templates

**For Walkthrough Posts:**
> "How we deployed [X] to [Platform]: A step-by-step guide with code."

**For Benchmark Posts:**
> "We tested [Our Tool] vs [Competitor] on [N] real-world scenarios. Here's the data."

**For Opinion Posts:**
> "Why [Counterintuitive Take]: Lessons from building [Product]."

> [!TIP]
> Cross-post to multiple channels but adapt framing. Reddit hates self-promotion; Twitter loves visuals; HN demands substance.

---

## Author Guidelines

| Blog | Default Author | When to Use Personal Name |
|------|----------------|---------------------------|
| GentleQuest | `GentleQuest Team` | Never (brand consistency) |
| Nucleus | `Nucleus Team` | Only for founder essays/opinion pieces explicitly labeled |
| IIP | `IIP Team` | Only for technical deep-dives |

---

## Quick Checklist

- [ ] Pre-write research complete (stress tests, screenshots)
- [ ] TL;DR hook in first 2 sentences
- [ ] Tables for comparisons
- [ ] Media embedded with captions
- [ ] Provenance footer added
- [ ] Cross-links included
- [ ] Export bundle created
- [ ] Build verified locally
- [ ] Distribution channels identified
