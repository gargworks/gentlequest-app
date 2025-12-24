# GentleQuest Admin Operations

Private reference for admin workflows. Not for public docs.

## Community Moderation

### How It Works
- AI blocks crisis/spam/gibberish before publish
- 3+ reports from unique IPs → auto-hide post
- Telegram alert sent to @gentlequest_alerts_bot

### When You Get an Alert

| Alert says | Action |
|------------|--------|
| Legitimately bad | Do nothing |
| False positive | Restore (see below) |

### Quick Commands

**View hidden posts:**
```bash
psql "$DATABASE_URL" -c "SELECT id, topic, body_redacted FROM community_posts WHERE is_hidden = TRUE;"
```

**Restore a post:**
```bash
psql "$DATABASE_URL" -c "UPDATE community_posts SET is_hidden = FALSE WHERE id = POST_ID;"
```

**View reports for a post:**
```bash
psql "$DATABASE_URL" -c "SELECT * FROM community_reports WHERE target_id = POST_ID;"
```

**Delete a post permanently:**
```bash
psql "$DATABASE_URL" -c "DELETE FROM community_posts WHERE id = POST_ID;"
```

---

## Database Connection

```
DATABASE_URL=postgresql://gentlequest_db_4uiy_user:iwQl4oJBr3iCZfhCG6dLgPXtRmXlxunH@dpg-d4d1v2c9c44c7394btkg-a.singapore-postgres.render.com/gentlequest_db_4uiy
```

---

## Env Vars (Render)

| Key | Purpose |
|-----|---------|
| `TELEGRAM_BOT_TOKEN` | Alert bot |
| `TELEGRAM_CHAT_ID` | Your Telegram ID |
| `COMMUNITY_POSTING_ENABLED` | Enable/disable UGC |
| `TEMPLATES_ONLY` | If true, no user posts |

---

## Feature Flags

To enable community posting:
```
COMMUNITY_POSTING_ENABLED=true
TEMPLATES_ONLY=false
```

To disable:
```
COMMUNITY_POSTING_ENABLED=false
TEMPLATES_ONLY=true
```

---

## Useful Queries

**User activity (last 7 days):**
```sql
SELECT DATE(created_at), COUNT(*) FROM conversations 
WHERE created_at > NOW() - INTERVAL '7 days' 
GROUP BY DATE(created_at) ORDER BY 1;
```

**Top community topics:**
```sql
SELECT topic, COUNT(*) FROM community_posts 
GROUP BY topic ORDER BY 2 DESC;
```

**Reports summary:**
```sql
SELECT reason, COUNT(*) FROM community_reports 
GROUP BY reason ORDER BY 2 DESC;
```

---

## Render Dashboard

- **Service:** https://dashboard.render.com/web/srv-d2r3i1fdiees73dqtov0
- **Database:** https://dashboard.render.com/d/dpg-d4d1v2c9c44c7394btkg-a
- **Logs:** Dashboard → Service → Logs tab

---

## Telegram Bot

- Bot: @gentlequest_alerts_bot
- Your Chat ID: 7575125475
- Test alert:
```bash
curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
  -d "chat_id=7575125475&text=Test alert"
```

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| Chat | 30/min |
| Community feed | 60/min |
| Post/react/report | 10/min |

---

## Emergency: Disable Community

If spam attack or issues:
```bash
# In Render dashboard, set:
COMMUNITY_POSTING_ENABLED=false
```
Takes effect immediately after deploy.
