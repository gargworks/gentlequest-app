# Voice API Keys & Terminal Privacy Setup

## API Keys Located ✅

From your `believe-it-bot` project documentation, I found the following API keys:

### ElevenLabs API Key
```bash
ELEVENLABS_API_KEY=sk_xxx
```

### Google Cloud TTS
```bash
GOOGLE_APPLICATION_CREDENTIALS=~/believe-it-bot-key.json
```

---

## Integration Plan

### Option 1: Use Existing `.env` File (Recommended)

If you already have a `.env` file in your `ai-mvp-backend` project:

```bash
# Add to your existing .env file
ELEVENLABS_API_KEY=sk_xxx  # Replace with actual key from believe-it-bot
GOOGLE_APPLICATION_CREDENTIALS=/Users/lokeshgarg/believe-it-bot-key.json
```

### Option 2: Copy from believe-it-bot

```bash
# Copy the credentials file
cp ~/believe-it-bot-key.json ~/ai-mvp-backend/

# Update .env
echo "GOOGLE_APPLICATION_CREDENTIALS=./believe-it-bot-key.json" >> .env
```

---

## Terminal Hostname Privacy Solution

### Problem
Your terminal shows `lokeshs-macbook-air` in recordings, which reveals personal information.

### Solution 1: Custom PS1 Prompt (Temporary, Per-Session)

**For Demo Recording Only:**

```bash
# Before recording, run this in your terminal:
export PS1="nucleus-demo $ "
```

This changes your prompt from:
```
lokeshs-macbook-air:~ lokesh$
```

To:
```
nucleus-demo $
```

**Pros**: Clean, professional, no personal info
**Cons**: Resets when you close the terminal

---

### Solution 2: Permanent Prompt Change

**Add to `~/.zshrc` (or `~/.bash_profile` if using bash):**

```bash
# Add this line at the end of the file
export PS1="%1~ $ "  # Shows only current directory
```

**Or for a branded prompt:**

```bash
export PS1="nucleus $ "  # Always shows "nucleus $"
```

**Apply changes:**

```bash
source ~/.zshrc  # Reload config
```

---

### Solution 3: Hide Hostname in Terminal Preferences

**macOS Terminal App:**

1. Terminal → Preferences → Profiles
2. Select your profile (e.g., "Basic")
3. Go to "Window" tab
4. Uncheck "Set window title to: Active process name"
5. Set custom title: "Nucleus Demo"

**This only changes the window title, not the prompt itself.**

---

### Solution 4: Use iTerm2 with Custom Profiles (Advanced)

**If you use iTerm2:**

1. Create a new profile: Preferences → Profiles → + (New Profile)
2. Name it "Demo Recording"
3. Under "General" → "Command" → set:
   ```bash
   /bin/zsh -c "export PS1='nucleus $ '; exec /bin/zsh"
   ```
4. Use this profile when recording demos

---

## Recommended Workflow for Demo Recording

### Before Recording:

```bash
# 1. Set clean prompt
export PS1="nucleus $ "

# 2. Clear screen
clear

# 3. Start recording (QuickTime or your preferred tool)
```

### During Recording:

- Your prompt will show: `nucleus $`
- No personal hostname visible
- Professional, branded appearance

### After Recording:

- Close terminal or run `source ~/.zshrc` to restore normal prompt

---

## Quick Test

**Test the prompt change:**

```bash
# Save current prompt
OLD_PS1=$PS1

# Set demo prompt
export PS1="nucleus-demo $ "

# Test it (you should see the new prompt)
echo "Testing new prompt"

# Restore original
export PS1=$OLD_PS1
```

---

## Recommendation for Your Use Case

**For Nucleus demos, I recommend Solution 1 (Temporary PS1):**

1. **Simple**: One command before recording
2. **Safe**: Doesn't permanently change your terminal
3. **Clean**: Professional appearance
4. **Flexible**: Easy to customize per demo

**Command to run before each demo recording:**

```bash
export PS1="nucleus $ " && clear
```

This sets the prompt and clears the screen in one command.

---

## Next Steps

1. **Locate the actual ElevenLabs API key** from your `believe-it-bot` project
2. **Add it to your `.env` file** in `ai-mvp-backend`
3. **Test the voiceover generator** with the real API key
4. **Practice the terminal prompt change** before recording demos

Would you like me to:
- Update the `generate_demo_voiceover.py` script to use ElevenLabs API directly?
- Create a pre-recording checklist script that sets up the terminal automatically?
