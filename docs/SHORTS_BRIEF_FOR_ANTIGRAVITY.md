# Brief: GentleQuest YouTube Shorts Agency

**To:** Antigravity Creator
**From:** Lokesh (GentleQuest)
**Date:** June 27, 2026
**Budget:** $0 (use free tools, open-source assets, AI generation)
**Deadline:** Ongoing — produce 5 shorts per week, indefinitely

---

## The Account

**YouTube channel:** GentleQuest
**Existing content:** 12 shorts (v7-v18) already published
**Current cadence:** 1 short/day through July 2, then nothing
**Your job:** Keep the pipeline full after July 2

## The Product

GentleQuest is a free mood check-in app for ADHD and anxious brains. The core differentiator: **no streaks, no guilt, no productivity pressure.** Every other wellness app punishes you for missing a day. We don't.

- iOS: https://apps.apple.com/app/gentlequest/id6756537464
- Android: https://play.google.com/store/apps/details?id=app.gentlequest.www
- Web: https://gentlequest.app

## The Audience

People with ADHD, anxiety, and chronic overwhelm. They're not looking for productivity hacks. They're looking for:
- Validation that they're not broken
- Gentle, specific techniques that actually work for ADHD brains
- Permission to rest without guilt
- Tools that don't punish them for being inconsistent

## The Tone

Vulnerable. Authentic. First person. Like a friend who gets it, not a brand. No toxic positivity. No "you got this!" energy. More like "this is hard, and here's one small thing that helps."

## The Goal

Drive app installs via YouTube Shorts. Each short should make someone think "this app gets me" and click through to download.

## What You're Producing

5 shorts per week. Each short:
- 15-60 seconds
- Vertical (9:16)
- Captioned (burned-in subtitles — most people watch with sound off)
- Calm, minimal visual style (no flashy edits, no bright colors)
- Ends with: "GentleQuest — free, no streaks, no guilt. Link in description."

## Content Themes (rotate through these)

1. **ADHD paralysis** — why you can't start, and one tiny thing that helps
2. **Streak anxiety** — why streaks make ADHD worse, and what to do instead
3. **Night anxiety** — the 2am brain spiral, and 4-7-8 breathing
4. **Overwhelm** — when everything is too much, start with one breath
5. **Productivity guilt** — you're not lazy, your brain works differently
6. **Grounding** — 5-4-3-2-1 method for anxiety attacks
7. **Task initiation** — the "one spoon" method for starting
8. **Rest as maintenance** — rest is not the opposite of productivity
9. **Rejection sensitive dysphoria** — why criticism hits harder with ADHD
10. **Body doubling** — why having someone nearby helps you start

## Production Notes

- The existing 12 shorts were produced with a render pipeline at `marketing/shorts/` — scripts, audio, and final MP4s are there. Study them to match the style.
- Use the audio agent prompt at `marketing/shorts/AUDIO_AGENT_PROMPT.md` for voice generation.
- Final MP4s go in `marketing/shorts/out/final/` with naming convention `gq_short_v{N}_{topic}_final.mp4`
- After producing each batch, run the upload script: `python3 marketing/shorts/upload_youtube.py v19_topic v20_topic ... --privacy unlisted`
- Then schedule them: `python3 marketing/shorts/schedule_youtube.py --start 2026-07-03 --time 10:00`

## How You're Measured

- Views per short (target: 1000+ in first week)
- Click-through rate to app store (target: 2%+)
- Subscriber growth (target: +50/week)
- Comments that say "this is exactly me" (qualitative signal)

## Constraints

- No copyrighted music. Use royalty-free or AI-generated audio.
- No medical claims. We're peers sharing techniques, not doctors giving advice.
- No crisis content. Don't make shorts about suicide, self-harm, or emergencies.
- No competitor mentions (Calm, Headspace, BetterHelp, Woebot, Wysa).
- No "buy now" energy. The app is free. The pitch is "this exists and it might help."

## You Have Full Creative Control

I'm not going to tell you how to make the shorts. You're the agency. You decide:
- Script or no script
- AI voice or text-only
- Stock footage or simple text cards
- What topics to prioritize
- How to batch production

Just produce 5 per week, upload them, schedule them, and report what you made.

## Reporting

After each batch, update `marketing/shorts/SHORTS_LOG.md` with:
- Short ID and topic
- Upload date
- YouTube URL
- Scheduled publish date

That's it. Go make things that help people feel less alone.
