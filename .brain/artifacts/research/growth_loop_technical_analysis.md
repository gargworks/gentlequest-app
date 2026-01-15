# Growth Loop Technical Analysis: "The Social Listener"

**Goal:** Implement a low-cost, high-signal automated system to find "Productivity Pain" in the wild and drive traffic to GentleQuest.

---

## 1. Channel Prioritization

| Channel | Viability | Technical Strategy |
| :--- | :--- | :--- |
| **Reddit** | ⭐⭐⭐⭐⭐ | **PRAW (Python Reddit API Wrapper).** Free tier is generous (100 QPM). |
| **Twitter/X** | ⭐⭐ | **Unofficial Clients (Twikit / ntscraper).** Official API v2 is too expensive ($200/mo). |
| **IndieHackers** | ⭐⭐⭐ | **Web Scraping.** Small community, high density of target audience. |

---

## 2. Technical Implementation: Reddit (Phase 1)
We will monitor subreddits like `r/ADHD`, `r/productivity`, and `r/burnout`.

### The "Golden Hack" (JSON Endpoints)
Instead of a heavy PRAW bot initially, we can use:
`https://www.reddit.com/r/ADHD/new/.json`
*   **Pros:** No API keys, zero rate-limit anxiety for occasional checks, easy to parse.
*   **Mechanism:** Cloud Function runs every 1h -> Scans JSON -> Filters by keywords (`stuck`, `burnout`, `apps don't work`).

### Keyword Map
*   **Primary:** `executive dysfunction`, `task paralysis`, `streak anxiety`.
*   **Secondary:** `ADHD app`, `procrastination`, `exhausted but can't sleep`.

---

## 3. The "Anti-Spam" Response Protocol
To avoid getting banned (as seen in the Jan 10 incident):
1.  **Empathy-First:** 80% of replies must have NO link. Just "I've been there, understimulation burnout is real."
2.  **The "Invitation" (Low Frequency):** Only link GentleQuest if a user *explicitly* asks for "any tool recommendations."
3.  **Wait-Time:** Always wait at least 2h after a post is made before replying (prevents "botting" suspicion).

---

## 4. Architecture (Next Step)
1.  **Trigger:** Cron Job (GitHub Actions or Cloud Scheduler).
2.  **Filter:** Python script using `nltk` or `TextBlob` for sentiment/relevance.
3.  **Action:** Push a notification to the **Marketing Dashboard** for human (founder) approval before posting.
