# Comet Inbox Harvest Protocol

**Role:** The Inbox Listener (Browser Agent)
**Objective:** Navigate to private inboxes, extract "Unread" notifications, and log them for the Brain to process.
**When to Run:** Daily (Morning/Evening) or On-Demand.

---

## 🏁 Step 1: The "Harvest" (Browser Action)

**Agent Instruction:**
> "Go to the following URLs using your active browser session. If you see ANY unread notifications, copy the text and sender."

### Target 1: IndieHackers
*   **URL:** `https://www.indiehackers.com/notifications`
*   **Selector:** Look for "Unread" badges or bold text.
*   **Action:** Copy the *Context* (What post is it?) and the *Comment* (What did they say?).

### Target 2: Reddit
*   **URL:** `https://www.reddit.com/message/inbox`
*   **Action:** Look for "Username mentions" or "Post replies". Copy the text.

### Target 3: Facebook (Page Interaction)
*   **URL:** `https://www.facebook.com`
*   **Identity Check:** Click Profile Icon. If "GentleQuest" is not active, click "See all profiles" -> Select **GentleQuest**.
*   **Target:** `https://www.business.facebook.com/latest/inbox` (Meta Business Suite) OR Page Notifications.
*   **Action:** Look for Comments on Page Posts. Copy the text.

### Target 4: Deep Scan (Replies to Yesterday's Activity)
*   **Why:** Notifications sometimes fail.
*   **Action:** Visit your own Profile -> Comments/Threads tab on Reddit/IndieHackers.
*   **Scan:** Look for any new replies to your comments from the last 24-48 hours.


---

## 🧠 Step 2: Hand-off to Intelligence Portal (Seamless)

**Agent Instruction:**
1.  **Navigate** your browser to `http://localhost:9999/`.
2.  **Locate** the "Agent Drop-Zone" section.
3.  **Paste** the collected inbox notifications into the "Raw Intelligence" box.
4.  **Ensure** "Inbox Listener 📬" is selected in the dropdown.
5.  **Click** the "Save to Brain" button.

---

## 🚀 Step 3: Handoff
1.  **Verify** the status message says "✅ Success: Saved".
2.  **Commit:** `git add docs/marketing/marketing_log.md && git commit -m "marketing: inbox harvest"`
3.  **Notify:** Tell the user "Inbox checked. Dashboard updated."

---

## ⚠️ Safety Rules & Engagement Protocol

### 1. The "Log-First" Rule (CRITICAL)
*   **ABSOLUTELY NO** direct posting, replying, or "staging" of text in the social media browser UI.
*   **WHY?** Social media UIs are brittle and prone to locking/stalling the agent.
*   **PROCEDURE:** If you identify a need to reply:
    1.  **Draft** the response internally.
    2.  **Log** it to the Brain (via Dashboard Ingest or direct log append).
    3.  **Use** the `marketing_log.md` "Draft" format so the *User* can click "Copy & Reply".

### 2. Operational Limits
*   **NO** storing of cookies or passwords in files. Use the live session.
*   **Read Only Mode:** Treat the browser session as a "Read Only" view. Your only "Write" action is to the local Brain/Dashboard.
