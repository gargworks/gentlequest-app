# 🧠 GentleQuest AI Backend

> AI Mental Health Assistant with Nuclear Brain Architecture

[![Render Deploy](https://img.shields.io/badge/Deploy-Render-46E3B7?style=flat-square&logo=render)](https://render.com)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square&logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-black?style=flat-square&logo=flask)](https://flask.palletsprojects.com/)

---

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/LKGargProjects/ai-mental-health-assistant.git
cd ai-mental-health-assistant
pip install -r requirements.txt

# Run locally
python3 app.py
```

---

## 📱 Telegram Integration

Control your Brain from your phone via **@gentlequest_alerts_bot**.

### Commands

| Command | Description |
|---------|-------------|
| `/status` | Get current Brain status (sprint, tasks, agents) |
| `/sprint <goal>` | Start a new sprint |
| `/tasks` | List current tasks |
| `/event <type> <msg>` | Log a custom event |
| `/help` | Show all commands |

### Setup

1. **Set environment variables:**
   ```bash
   export TELEGRAM_BOT_TOKEN="your-bot-token"
   export TELEGRAM_CHAT_ID="your-chat-id"
   ```

2. **Sync local state to production:**
   ```bash
   python3 brain_sync.py --push-to-prod
   ```

3. **Set webhook (one-time):**
   ```bash
   curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook?url=https://your-domain.com/api/brain/telegram/webhook"
   ```

---

## 🧠 Nuclear Brain Architecture

The `.brain/` directory is the single source of truth for all agentic operations.

```
.brain/
├── ledger/
│   ├── state.json      # Current system state
│   ├── events.jsonl    # Event log
│   └── triggers.json   # Agent triggers
├── agents/             # Agent definitions
├── artifacts/          # Work outputs
├── memory/             # Persistent context
└── workflows/          # Operational procedures
```

### Key Scripts

| Script | Purpose |
|--------|---------|
| `brain_sync.py` | Sync artifacts to event stream |
| `brain_telegram.py` | Telegram bot integration |
| `app.py` | Main Flask application |

---

## 📡 API Endpoints

### Brain API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/brain/status` | GET | Get current Brain state |
| `/api/brain/alert` | POST | Send Telegram alert |
| `/api/brain/sprint` | POST | Start new sprint |
| `/api/brain/sync` | POST | Sync state from local |

### Core API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/chat` | POST | Chat with AI |
| `/api/session` | POST | Create session |

---

## 🔧 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `TELEGRAM_BOT_TOKEN` | No | Telegram bot token |
| `TELEGRAM_CHAT_ID` | No | Your Telegram chat ID |

---

## 📦 Deployment

### Render

The app auto-deploys on push to `main`. Key files:

- `Dockerfile` - Container build
- `.dockerignore` - Build exclusions (whitelist approach)
- `render.yaml` - Render blueprint

### Manual Deploy

```bash
git push origin main
# Render auto-deploys
```

---

## 🧪 Testing

```bash
# Run brain tests
python3 -c "import brain_telegram; print('OK')"
python3 -c "import brain_sync; print('OK')"

# Test Telegram locally
python3 brain_telegram.py status
```

---

## 📚 Documentation

- [NUCLEUS_HUB.md](.brain/NUCLEUS_HUB.md) - Central navigation hub
- [OPERATIONS.md](.brain/workflows/OPERATIONS.md) - Operational protocols
- [AGENTS.md](AGENTS.md) - Agent definitions

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🙏 Credits

Built with ❤️ by [@LokeshGarg](https://github.com/LKGargProjects)

Powered by [Google Gemini](https://ai.google.dev/) and [Flask](https://flask.palletsprojects.com/)
