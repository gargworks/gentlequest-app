---
description: The Sovereign Outreach Protocol (Team Communication via Resend)
---

# /outreach: The Sovereign Outreach Protocol 🛡️

Use this workflow to send official project communications from **The Nucleus Team** identity using our Resend infrastructure.

## 🛠️ The Command Line Tool
The core logic resides in `scripts/outreach_cli.py`. You can use it to send pre-defined templates or custom "manual" emails.

### ⚠️ Mandatory Confirmation
**Before executing any send**, Antigravity MUST:
1.  Explicitly state which email is being used (`admin@nucleusos.dev` vs `hello@nucleusos.dev`).
2.  Wait for the user to confirm the choice.
3.  Cross-check the recipient and subject for any PII leaks.

### Generic Outreach (Manual Mode)
```bash
python3 scripts/outreach_cli.py --to [RECIPIENT] --subject "[SUBJECT]" --body "[HTML_BODY]" --sender [admin|hello]
```

### Template: Stargazer (Feedback Request)
```bash
python3 scripts/outreach_cli.py --to [RECIPIENT] --type stargazer --name "[NAME]"
```

## 🛡️ Narrative Guardrails
- **Identity**: Always use the `--sender` flag to align with your current persona.
    - `hello`: Casual, general support, community building.
    - `admin`: Authoritative, project governance, official takedowns.
- **Tone**: Keep it "Sovereign" - technical, direct, and non-marketing.
- **Anonymity**: The script uses your domain-authenticated email, keeping your personal Gmail hidden.

## 📋 Common Templates Catalog

### 1. The "Takedown" (Governance)
**Sender**: `admin`
**Subject**: `Duplicate/Legacy Listing Removal Request: Nucleus Brain`
**Body**:
```html
<p>Hello,</p>
<p>I am writing from the <strong>Nucleus Team</strong>. We have identified a legacy/duplicate listing of our server on your registry: [URL]</p>
<p>Please <strong>remove</strong> this entry to protect project identity during our launch.</p>
<p>Thank you,<br><strong>The Nucleus Team</strong></p>
```

### 2. The "Handshake" (Community)
**Sender**: `hello`
**Subject**: `thanks for using nucleus mcp`
**Body**:
```html
<p>Hi {name},</p>
<p>Saw you using Nucleus. If you have any feedback or something broke, I'd love to hear it.</p>
<p>Discord: <a href="https://discord.gg/RJuBNNJ5MT">https://discord.gg/RJuBNNJ5MT</a></p>
<p>Best,<br>The Nucleus Team</p>
```
