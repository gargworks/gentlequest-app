
# ChatOps Strategy & Roadmap

> **Philosophy**: The Nucleus should meet the human where they are. Whether it's a critical production alert on a phone call or a casual "deploy this" text on Telegram, the interface adapts to the context.

## 1. Current Choice: Telegram (Priority) ✈️
**Why**: Lightweight, fast, rich API, supports "Web Apps," and requires zero setup for push notifications.
**Implementation**: `tools/telegram_op.py` (Operator Bot).
**Capabilities**:
- `/deploy <plan>`: Trigger Cloud Run.
- `/status`: Check execution.
- `/logs`: Tail logs (future).

---

## 2. Future Channels (Roadmap)

### A. WhatsApp (The "Life" OS) 💬
**Use Case**: Casual, low-friction interaction. "I'm on the move, just fix it."
**Status**: Planned.
**Technical Strategy**:
- **Sandbox**: Use Twilio Sandbox for immediate dev.
- **Production**: Requires Meta Business Verification (High friction).
- **Fallback**: Use Twilio Programmable SMS if WhatsApp is too complex.

### B. Siri Shortcuts + iOS (The "Magic Button") 🪄
**Use Case**: "Iron Man" style desktop widgets or voice commands.
**Status**: Planned.
**Technical Strategy**:
- **Webhook**: Expose a secure endpoint on Cloud Run (e.g., `/api/ops/webhook?token=xyz`).
- **iOS Shortcut**: Create a "Get URL" shortcut triggered by "Hey Siri, Deploy Nucleus".
- **Widget**: Place the shortcut on Mac/iPhone Home Screen.

### C. Phone Call (The "Red Phone") ☎️
**Use Case**: **CRITICAL** Level 1 Production Outages.
**Status**: Planned.
**Technical Strategy**:
- **Twilio Voice**: Nucleus triggers a call to the Founder's personal number.
- **TTS**: "Alert: Nucleus Brain is unresponsive. Deploy failed. Press 1 to Rollback."

### D. Alexa / Google Home (Ambient Computing) 🏠
**Use Case**: Morning briefing or "hands-full" status checks.
**Status**: Planned (Low Priority).
**Technical Strategy**:
- **Custom Skill**: requires AWS Lambda / Alexa Skills Kit.
- **Voice UI**: "Alexa, ask Nucleus for the sprint status."

### E. Discord (The "War Room") 🎮
**Use Case**: High-bandwidth debugging with team. Streaming logs, sharing graphs.
**Status**: Deprioritized (Code exists in `tools/discord_bot_planned.py`).
**Technical Strategy**:
- Rich Embeds for Git Diffs.
- Threaded discussions for specific error logs.

---

## 3. Integration Architecture
To support all these without 5 different bots, we will move to a **"Unified Sensory Interface"**:
1.  **Event Bus**: `brain_ops` emits "events" (e.g., `DEPLOY_COMPLETE`).
2.  **Router**: A central router decides where to push:
    - `Routine` -> Telegram.
    - `Critical` -> Telegram + Phone Call.
3.  **Command Gateway**: A unified parsing logic (`process_command(text)`) shared by Telegram, WhatsApp, and Discord webhooks.
