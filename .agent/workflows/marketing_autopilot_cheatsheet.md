# Marketing Autopilot Cheatsheet ✈️

> **How to use:**
> Open your Browser Agent (Perplexity, ChatGPT, Claude) and paste the relevant **Prompt** below.
> Ensure you are logged into the destination platforms (Twitter, Reddit, IndieHackers) in that browser.

---

## 👂 The Listener (Start Here)
*Check for replies to your previous posts.*

**Prompt:**
```text
Act as my "Inbox Listener".
Your Goal: Find unread notifications or replies to my recent posts.
Scope: Twitter Notifications, Reddit Inbox, IndieHackers Notifications.

1. Navigate to these inboxes.
2. If you find a reply/comment, copy the context and the message.
3. CRITICAL: Also check my Profile -> "Comments/Threads" to see if anyone replied to my yesterday's activity.

IF YOU ARE A CLOUD BOT (Perplexity/ChatGPT):
- You cannot access my localhost.
- FORMAT your findings as a code block I can copy-paste.
- Title: "Inbox Update"

IF YOU ARE A BROWSER AGENT (MultiOn/Operator):
4. Go to http://localhost:9999 (My Dashboard).
5. Paste the findings into the "Raw Intelligence" box.
6. Select "Inbox Listener 📬" and click "Save".

META-FEEDBACK (Optional):
- If this prompt missed something or was hard to follow, suggest a better version of this prompt at the end of your report.
```


---

## 🧠 The Brain (Automatic)
* *The Dashboard/Brain automatically detects the log update and drafts responses.*
* *You check `http://localhost:9999` to see the new Drafts under "New Opportunities".*

---

## ✍️ The Publisher (Finish Here)
*Publish the drafts pending in the dashboard.*

**Prompt:**
```text
Act as my "Publisher".
Your Goal: Publish pending drafts.

IF YOU ARE A CLOUD BOT (Perplexity):
- Ask me: "Please paste the draft content from your Dashboard here."
- Once I provide it, go to the platform and help me polish/publish it.
- Remind me to click "Mark Posted" on my dashboard.
- META-FEEDBACK: If the draft format was annoying to copy, tell me how to change the Brain's output template.

IF YOU ARE A BROWSER AGENT (MultiOn):
1. Go to http://localhost:9999.
2. Look for any cards marked "DRAFT READY".
3. For each draft:
   a. Extract content -> Navigate to Platform -> Paste -> Post.
   b. RETURN to Dashboard -> Click "✅ Mark Posted".
   c. META-FEEDBACK: If any button selector failed, report it so I can update the code.
```

---

## 📡 The Scout (Optional - Daily Trend Check)
*Find new topics to post about.*

**Prompt:**
```text
Act as my "Trend Scout".
Your Goal: Find high-signal discussions from the last 24h.
Scope: r/SaaS, r/ADHD, Twitter Dev Community.

1. Search for: "Developer burnout", "AI fatigue", "SaaS marketing trends".
2. Summarize top 3 complaints or emotional vibes.

IF YOU ARE A CLOUD BOT:
- Output the summary as a text block I can copy.
- META-FEEDBACK: Suggest 1 new Search Term I should add to this prompt for next time.

IF YOU ARE A BROWSER AGENT:
3. Go to http://localhost:9999.
4. Paste summary into "Raw Intelligence".
5. Select "Trend Scout 📡" and click "Save".
```
