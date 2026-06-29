#!/usr/bin/env python3
"""Generate deploy kits for v19-v66 YT shorts."""
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent

LINKS = """iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app"""

FOOTER = "Free. 18+. No ads."

# ── Pinned comment blocks (extracted from pinned_comments.md) ──
PINNED = {
    "v19": """Chest tight? Thoughts won't slow? 90 seconds of breathing, or just say it.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Free. 18+. No ads.""",
    "v20": """Can't stop worrying? Write it down, name the feeling, ground yourself.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Free. 18+. No ads.""",
    "v21": """Heart racing? Can't catch your breath? Box breathing. And your safety plan.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Panic passes. You are safe. Free. 18+.""",
    "v22": """Panic feels like dying. It isn't. You aren't. Breathe with this.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Not a diagnosis. Not dying. Just panic. Free. 18+.""",
    "v23": """Nothing sounds good? Everything feels heavy? Log it. One tiny quest.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Small steps count. Free. 18+.""",
    "v24": """Can't get out of bed? Log it from here. That counts as trying.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Not a streak. Not a failure. Just a day. Free. 18+.""",
    "v25": """3am and can't sleep? Slow breathing, or write it out.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

The thought loop loses its grip. Free. 18+.""",
    "v26": """Brain won't shut off? Dump every thought on a blank page.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

The page holds it. You sleep. Free. 18+.""",
    "v27": """The thought won't leave? It doesn't mean anything. Write it down.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

A thought is a thought. Not a truth. Free. 18+.""",
    "v28": """You are not your thoughts. Say it. Write it. Breathe.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Intrusive ≠ true. Intrusive ≠ you. Free. 18+.""",
    "v29": """Everything is too much? Log it. One tiny quest. Or just breathe.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Rest is not lazy. Rest is the work. Free. 18+.""",
    "v30": """Running on empty? Check in. See the pattern. Your safety plan is here.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

You don't have to be okay right now. Free. 18+.""",
    "v31": """It has to be perfect? Or what? Write the fear. Do it badly. 90 seconds.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Done > perfect. Always. Free. 18+.""",
    "v32": """Can't start until it's right? Start wrong. 90 seconds. Badly.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Imperfect counts. Imperfect ships. Free. 18+.""",
    "v33": """Same thought on loop? Write it out. See it on paper. Come back to now.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

The loop breaks when you see it. Free. 18+.""",
    "v34": """Can't stop replaying it? Say it once. Write it once. Breathe through it.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Replayed ≠ real. Just loud. Free. 18+.""",
    "v35": """Everyone is watching? They aren't. 5 things you see. Breathe.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

The room is not watching. You are safe. Free. 18+.""",
    "v36": """Rehearsing every word? Write it instead. Breathe before you go.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

You don't owe anyone a perfect version. Free. 18+.""",
    "v37": """What if it's serious? What if it isn't? Write the fear. Come back to your body.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Not a diagnosis. See a doctor if worried. Free. 18+.""",
    "v38": """Stop googling. Write the worry instead. Breathe. Log the anxiety.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Dr. Google is not a real doctor. Free. 18+.""",
    "v39": """Five seconds a day. Pick a face. Tap done. No streak. No guilt.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Just a log. Free. 18+.""",
    "v40": """A week of moods. What changed? What triggered it? Log again tomorrow.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Patterns, not streaks. Pictures, not grades. Free. 18+.""",
    "v41": """Fill it when calm. Find it when you're not. Add contacts. Add what helps.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Free. 18+.""",
    "v42": """One tap to call your people. Crisis lines for your country. Not buried.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Free. 18+.""",
    "v43": """90 seconds to start. Pick one quest. Do it now. Or browse the library.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

You will outgrow them. That's the point. Free. 18+.""",
    "v44": """The goal is to uninstall. Learn the skill. Then delete the app.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Free. 18+.""",
    "v45": """Blank page. No prompts. Write anything. Or tap a chip. Anonymous. Private.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

No AI reads it. No AI summarizes it. Free. 18+.""",
    "v46": """Write nothing. That's fine. The page is there. You don't owe it words.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Free. 18+.""",
    "v47": """60 seconds. 5 you see. 4 you touch. 3 you hear. 2 you smell. 1 you taste.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Back to now. Free. 18+.""",
    "v48": """Mind racing? 5 things you see. 4 you can touch. Then log your mood.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Your feet on the floor. You are here. Free. 18+.""",
    "v49": """90 seconds. In for 4. Hold for 4. Out for 4. Hold for 4. That's it.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

You are breathing. Free. 18+.""",
    "v50": """Can't breathe slow? Just follow this. In. Hold. Out. Hold.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Your breath is always here. Free. Free. 18+.""",
    "v51": """Feel your feet on the floor. Scan up slowly. Your body is here. You are here.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Free. 18+.""",
    "v52": """Jaw. Shoulders. Chest. Breathe into it. Let it go. Log the tension.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Your body holds what your mind won't say. Free. 18+.""",
    "v53": """Write the thought down. Exactly as it is. A thought on paper is smaller.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Free. 18+.""",
    "v54": """Is it true? Or just loud? Write it. Ask. Talk it through. Ground.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Loud ≠ true. Repeated ≠ real. Free. 18+.""",
    "v55": """Do one small thing. 90 seconds. Badly. Then log how you feel after.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Action before motivation. Always. Free. 18+.""",
    "v56": """You don't wait for motivation. You act first. One quest. Do it badly.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

The feeling follows the action. Not the reverse. Free. 18+.""",
    "v57": """Before bed: write the day out. Breathe slow. Log your mood.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

The page holds the day. You sleep. Free. 18+.""",
    "v58": """Can't sleep? Dump every thought. Ground. Breathe slow. Log it.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

The loop breaks. Sleep comes. Free. 18+.""",
    "v59": """No ads. No upsell. No paywall. No premium tier. No lock-in.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Free. 18+. That's it.""",
    "v60": """We don't spam you. You choose what, when, or off. Default: quiet.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Your phone is loud enough. Free. 18+.""",
    "v61": """No AI reads your journal. No AI summarizes it. No AI trains on it.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Just yours. Free. 18+.""",
    "v62": """We don't diagnose you. PHQ-9 gives a score, not a label. See a professional.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

A starting point. Not a diagnosis. Free. 18+.""",
    "v63": """No streaks. No guilt. Log when you want. Missed a day? Fine.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

You don't owe an app consistency. Free. 18+.""",
    "v64": """No feed. No likes. No doomscroll. No algorithm to fight.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Just you and your mood. Free. 18+.""",
    "v65": """We are not a therapist. We are a quiet chat with a real safety plan.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Not a replacement. A bridge. Free. 18+.""",
    "v66": """No tracking. No analytics on you. Anonymous mode. Your data, exportable, deletable.

iOS — https://apps.apple.com/app/gentlequest/id6756537464
Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
Web — https://gentlequest.app

Your data is yours. We mean it. Free. 18+.""",
}

# ── Metadata for each version ──
# (slug, mp4_name, display_name, titles[3], desc_first_100, hashtags[15], fb, x, linkedin)
KITS = [
    # v19
    ("v19_anxiety_tight", "gq_short_v19_anxiety_tight.mp4", "v19 — anxiety: chest tight",
     ['"Chest tight? 90 seconds to breathe"',
      '"When anxiety makes your chest tight"',
      '"Anxiety chest tightness — try this"'],
     "Chest tight and thoughts won't slow? 90 seconds of box breathing, or just say it. GentleQuest is a quiet app for the in-between moments.",
     "#anxiety #anxietyrelief #breathing #boxbreathing #mentalhealth #panicattack #copingskills #grounding #mindfulness #selfcare #selfhelp #anxietysupport #stressrelief #mentalhealthawareness #healing",
     "Chest tight? 90 seconds of breathing can help. Try it free — https://gentlequest.app",
     "Chest tight? Thoughts won't slow? 90 seconds of box breathing. Try it free. #anxiety #breathing #mentalhealth",
     "When anxiety makes your chest tight, 90 seconds of guided breathing can bring you back. A quiet, free tool for the in-between moments."),
    # v20
    ("v20_anxiety_worry", "gq_short_v20_anxiety_worry.mp4", "v20 — anxiety: can't stop worrying",
     ['"Can\'t stop worrying? Write it out"',
      '"When your worry won\'t let go"',
      '"Anxiety loops — break the cycle"'],
     "Can't stop worrying? Write it down, name the feeling, then ground yourself. The worry doesn't win — you just see it.",
     "#anxiety #worry #anxietyrelief #journaling #mentalhealth #copingskills #grounding #mindfulness #selfcare #selfhelp #anxietysupport #stressrelief #mentalhealthawareness #cbt #healing",
     "Can't stop worrying? Write it down, name it, ground yourself. Free tool — https://gentlequest.app",
     "Can't stop worrying? Write it down. Name the feeling. Ground yourself. The worry doesn't win. #anxiety #worry #mentalhealth",
     "When worry loops won't stop, writing it down and naming the feeling can break the cycle. A free, private tool for anxious moments."),
    # v21
    ("v21_panic_racing", "gq_short_v21_panic_racing.mp4", "v21 — panic: heart racing",
     ['"Heart racing? Box breathing"',
      '"When panic makes your heart race"',
      '"Panic attack? Try this 90s"'],
     "Heart racing and can't catch your breath? Box breathing — four counts each. And your safety plan is here if it doesn't stop.",
     "#panic #panicattack #breathing #boxbreathing #mentalhealth #anxiety #copingskills #grounding #mindfulness #selfcare #selfhelp #panicsupport #stressrelief #mentalhealthawareness #safetyplan",
     "Heart racing? Box breathing — 4 counts in, 4 out. Your safety plan is here too. https://gentlequest.app",
     "Heart racing? Can't catch your breath? Box breathing. 4 counts each. Panic passes. #panic #breathing #mentalhealth",
     "When panic sends your heart racing, box breathing can bring you back. A free app with a real safety plan for the moments that matter."),
    # v22
    ("v22_panic_dying", "gq_short_v22_panic_dying.mp4", "v22 — panic: feels like dying",
     ['"Panic feels like dying (it isn\'t)"',
      '"When panic feels like the end"',
      '"Panic attack? You aren\'t dying"'],
     "Panic feels like dying. It isn't. You aren't. Breathe with this, ground yourself, and your safety plan is here.",
     "#panic #panicattack #breathing #grounding #mentalhealth #anxiety #copingskills #mindfulness #selfcare #selfhelp #panicsupport #stressrelief #mentalhealthawareness #safetyplan #healing",
     "Panic feels like dying. It isn't. You aren't. Breathe with this. https://gentlequest.app",
     "Panic feels like dying. It isn't. You aren't. Breathe with this. Ground yourself. #panic #panicattack #mentalhealth",
     "Panic attacks can feel like dying — but they pass. A free app with guided breathing and a real safety plan for those moments."),
    # v23
    ("v23_depression_nothing", "gq_short_v23_depression_nothing.mp4", "v23 — depression: nothing sounds good",
     ['"Nothing sounds good? Log it"',
      '"When everything feels heavy"',
      '"Depression? One tiny quest"'],
     "Nothing sounds good? Everything feels heavy? Log it anyway. One tiny quest. Or just talk. Small steps count.",
     "#depression #mentalhealth #mood #copingskills #behavioralactivation #selfcare #selfhelp #mentalhealthawareness #mindfulness #grounding #depressionsupport #lowmood #tinyquests #cbt #healing",
     "Nothing sounds good? Everything feels heavy? Log it. One tiny quest. https://gentlequest.app",
     "Nothing sounds good? Everything feels heavy? Log it anyway. One tiny quest. Small steps count. #depression #mentalhealth",
     "When depression makes everything feel heavy, logging your mood and doing one tiny quest can help. A free, gentle tool."),
    # v24
    ("v24_depression_bed", "gq_short_v24_depression_bed.mp4", "v24 — depression: can't get out of bed",
     ['"Can\'t get out of bed? Log it"',
      '"When getting up feels impossible"',
      '"Depression? That counts as trying"'],
     "Can't get out of bed? Log it from here. That counts as trying. One quest, 90 seconds. Or just breathe.",
     "#depression #mentalhealth #mood #copingskills #behavioralactivation #selfcare #selfhelp #mentalhealthawareness #mindfulness #grounding #depressionsupport #lowmood #tinyquests #cbt #healing",
     "Can't get out of bed? Log it from here. That counts as trying. https://gentlequest.app",
     "Can't get out of bed? Log it from here. That counts as trying. Not a streak. Not a failure. Just a day. #depression #mentalhealth",
     "When getting out of bed feels impossible, logging your mood from where you are counts as trying. A free, no-pressure app."),
    # v25
    ("v25_insomnia_3am", "gq_short_v25_insomnia_3am.mp4", "v25 — insomnia: 3am",
     ['"3am and can\'t sleep? Try this"',
      '"When insomnia hits at 3am"',
      '"Can\'t sleep? Slow breathing"'],
     "3am and can't sleep? Slow breathing — in for 4, out for 4. Or write it out. Or just talk. The thought loop loses its grip.",
     "#insomnia #sleep #breathing #boxbreathing #mentalhealth #anxiety #copingskills #journaling #mindfulness #selfcare #selfhelp #sleephygiene #stressrelief #mentalhealthawareness #healing",
     "3am and can't sleep? Slow breathing or write it out. The loop loses its grip. https://gentlequest.app",
     "3am and can't sleep? Slow breathing, in for 4, out for 4. Or write it out. The thought loop loses its grip. #insomnia #sleep #mentalhealth",
     "When insomnia hits at 3am, slow breathing or journaling can break the thought loop. A free, quiet tool for sleepless nights."),
    # v26
    ("v26_insomnia_brain", "gq_short_v26_insomnia_brain.mp4", "v26 — insomnia: brain won't shut off",
     ['"Brain won\'t shut off? Dump it"',
      '"When your mind won\'t stop at night"',
      '"Insomnia? Write every thought"'],
     "Brain won't shut off? Dump every thought on a blank page. The page holds it. You sleep.",
     "#insomnia #sleep #journaling #mentalhealth #anxiety #copingskills #mindfulness #selfcare #selfhelp #sleephygiene #stressrelief #mentalhealthawareness #grounding #cbt #healing",
     "Brain won't shut off? Dump every thought on a blank page. You sleep. https://gentlequest.app",
     "Brain won't shut off? Dump every thought on a blank page. The page holds it. You sleep. #insomnia #sleep #mentalhealth",
     "When your brain won't shut off at night, dumping every thought on a blank page can help you sleep. Free and private."),
    # v27
    ("v27_ocd_intrusive", "gq_short_v27_ocd_intrusive.mp4", "v27 — OCD: intrusive thoughts",
     ['"The thought won\'t leave? Write it"',
      '"When intrusive thoughts won\'t stop"',
      '"OCD? A thought is not a truth"'],
     "The thought won't leave? It doesn't mean anything. Write it down, see it on paper, come back to now.",
     "#ocd #intrusivethoughts #mentalhealth #anxiety #copingskills #journaling #mindfulness #selfcare #selfhelp #grounding #ocdsupport #cbt #stressrelief #mentalhealthawareness #healing",
     "The thought won't leave? It doesn't mean anything. Write it down. https://gentlequest.app",
     "The thought won't leave? It doesn't mean anything. Write it down. A thought is a thought. Not a truth. #ocd #mentalhealth",
     "When intrusive thoughts won't leave, writing them down can shrink them. A free, private tool for OCD moments."),
    # v28
    ("v28_ocd_not_thoughts", "gq_short_v28_ocd_not_thoughts.mp4", "v28 — OCD: you're not your thoughts",
     ['"You are not your thoughts"',
      '"Intrusive thoughts ≠ you"',
      '"OCD? Say it, write it, breathe"'],
     "You are not your thoughts. Say it out loud, write it, name the anxiety, then breathe. Intrusive doesn't mean true.",
     "#ocd #intrusivethoughts #mentalhealth #anxiety #copingskills #journaling #mindfulness #selfcare #selfhelp #grounding #ocdsupport #cbt #breathing #mentalhealthawareness #healing",
     "You are not your thoughts. Say it. Write it. Breathe. Intrusive ≠ you. https://gentlequest.app",
     "You are not your thoughts. Say it. Write it. Breathe. Intrusive ≠ true. Intrusive ≠ you. #ocd #mentalhealth",
     "You are not your intrusive thoughts. A free app to say it, write it, and breathe through OCD moments."),
    # v29
    ("v29_burnout_too_much", "gq_short_v29_burnout_too_much.mp4", "v29 — burnout: everything is too much",
     ['"Everything is too much? Log it"',
      '"When burnout hits hard"',
      '"Burnout? One tiny quest"'],
     "Everything is too much? Log it. One tiny quest. Or just breathe. Or write nothing. Rest is not lazy — rest is the work.",
     "#burnout #mentalhealth #mood #copingskills #behavioralactivation #selfcare #selfhelp #mentalhealthawareness #mindfulness #grounding #breathing #stressrelief #burnoutrecovery #cbt #healing",
     "Everything is too much? Log it. One tiny quest. Rest is not lazy. https://gentlequest.app",
     "Everything is too much? Log it. One tiny quest. Or just breathe. Rest is not lazy. Rest is the work. #burnout #mentalhealth",
     "When burnout makes everything feel like too much, logging it and doing one tiny thing can help. Rest is the work."),
    # v30
    ("v30_burnout_empty", "gq_short_v30_burnout_empty.mp4", "v30 — burnout: running on empty",
     ['"Running on empty? Check in"',
      '"When you\'re burned out"',
      '"Burnout? See the pattern"'],
     "Running on empty? Check in, see the pattern, pick one thing. And your safety plan is here. You don't have to be okay right now.",
     "#burnout #mentalhealth #mood #copingskills #selfcare #selfhelp #mentalhealthawareness #mindfulness #grounding #stressrelief #burnoutrecovery #safetyplan #patterns #cbt #healing",
     "Running on empty? Check in. See the pattern. You don't have to be okay right now. https://gentlequest.app",
     "Running on empty? Check in. See the pattern. Your safety plan is here. You don't have to be okay right now. #burnout #mentalhealth",
     "When you're running on empty, checking in and seeing the pattern matters. A free app with a real safety plan."),
    # v31
    ("v31_perfect_has_to", "gq_short_v31_perfect_has_to.mp4", "v31 — perfectionism: has to be perfect",
     ['"It has to be perfect? Or what?"',
      '"Perfectionism? Do it badly"',
      '"Done > perfect. Always."'],
     "It has to be perfect? Or what? Write the fear, do it badly in 90 seconds, then log how you feel after. Done > perfect.",
     "#perfectionism #mentalhealth #anxiety #copingskills #behavioralactivation #selfcare #selfhelp #mentalhealthawareness #mindfulness #journaling #cbt #stressrelief #productivity #selfcompassion #healing",
     "It has to be perfect? Or what? Write the fear. Do it badly. Done > perfect. https://gentlequest.app",
     "It has to be perfect? Or what? Write the fear. Do it badly. 90 seconds. Done > perfect. Always. #perfectionism #mentalhealth",
     "Perfectionism can freeze you. Writing the fear and doing it badly in 90 seconds can break the loop. Done > perfect."),
    # v32
    ("v32_perfect_cant_start", "gq_short_v32_perfect_cant_start.mp4", "v32 — perfectionism: can't start",
     ['"Can\'t start until it\'s right?"',
      '"Perfectionism? Start wrong"',
      '"Imperfect counts. Imperfect ships."'],
     "Can't start until it's right? Start wrong. 90 seconds. Badly. Write why it has to be perfect. Imperfect counts.",
     "#perfectionism #mentalhealth #anxiety #copingskills #behavioralactivation #selfcare #selfhelp #mentalhealthawareness #mindfulness #journaling #cbt #stressrelief #productivity #selfcompassion #healing",
     "Can't start until it's right? Start wrong. 90 seconds. Badly. https://gentlequest.app",
     "Can't start until it's right? Start wrong. 90 seconds. Badly. Imperfect counts. Imperfect ships. #perfectionism #mentalhealth",
     "When perfectionism stops you from starting, starting wrong can break the freeze. A free tool for imperfect action."),
    # v33
    ("v33_rumination_loop", "gq_short_v33_rumination_loop.mp4", "v33 — rumination: same thought on loop",
     ['"Same thought on loop? Write it"',
      '"When rumination won\'t stop"',
      '"Break the thought loop"'],
     "Same thought on loop? Write it out, see it on paper, come back to now. The loop breaks when you see it.",
     "#rumination #mentalhealth #anxiety #copingskills #journaling #mindfulness #selfcare #selfhelp #grounding #breathing #cbt #stressrelief #mentalhealthawareness #overthinking #healing",
     "Same thought on loop? Write it out. See it on paper. The loop breaks when you see it. https://gentlequest.app",
     "Same thought on loop? Write it out. See it on paper. Come back to now. The loop breaks when you see it. #rumination #mentalhealth",
     "When the same thought loops, writing it out can break the cycle. A free, private tool for rumination."),
    # v34
    ("v34_rumination_replay", "gq_short_v34_rumination_replay.mp4", "v34 — rumination: can't stop replaying",
     ['"Can\'t stop replaying it?"',
      '"When your mind replays everything"',
      '"Replayed ≠ real. Just loud."'],
     "Can't stop replaying it? Say it once, write it once, breathe through it. Replayed doesn't mean real — just loud.",
     "#rumination #mentalhealth #anxiety #copingskills #journaling #mindfulness #selfcare #selfhelp #grounding #breathing #cbt #stressrelief #mentalhealthawareness #overthinking #healing",
     "Can't stop replaying it? Say it once. Write it once. Breathe through it. https://gentlequest.app",
     "Can't stop replaying it? Say it once. Write it once. Breathe through it. Replayed ≠ real. Just loud. #rumination #mentalhealth",
     "When you can't stop replaying something, saying it once and writing it once can help. A free tool for overthinking."),
    # v35
    ("v35_social_anxiety_watching", "gq_short_v35_social_watching.mp4", "v35 — social anxiety: everyone is watching",
     ['"Everyone is watching? They aren\'t"',
      '"When social anxiety hits"',
      '"Social anxiety? 5 things you see"'],
     "Everyone is watching? They aren't. 5 things you see, breathe slowly, write the fear out. The room is not watching — you are safe.",
     "#socialanxiety #anxiety #mentalhealth #copingskills #grounding #mindfulness #selfcare #selfhelp #breathing #cbt #stressrelief #mentalhealthawareness #socialanxietysupport #54321 #healing",
     "Everyone is watching? They aren't. 5 things you see. Breathe. You are safe. https://gentlequest.app",
     "Everyone is watching? They aren't. 5 things you see. Breathe slowly. The room is not watching. You are safe. #socialanxiety #mentalhealth",
     "When social anxiety tells you everyone is watching, grounding can bring you back. A free tool for social anxiety moments."),
    # v36
    ("v36_social_anxiety_rehearse", "gq_short_v36_social_rehearse.mp4", "v36 — social anxiety: rehearsing every word",
     ['"Rehearsing every word? Stop"',
      '"When you over-rehearse conversations"',
      '"Social anxiety? Write it instead"'],
     "Rehearsing every word? Write it instead, name the anxiety, breathe before you go. You don't owe anyone a perfect version.",
     "#socialanxiety #anxiety #mentalhealth #copingskills #journaling #mindfulness #selfcare #selfhelp #breathing #cbt #stressrelief #mentalhealthawareness #socialanxietysupport #grounding #healing",
     "Rehearsing every word? Write it instead. Breathe before you go. https://gentlequest.app",
     "Rehearsing every word? Write it instead. Breathe before you go. You don't owe anyone a perfect version. #socialanxiety #mentalhealth",
     "When you rehearse every conversation, writing it out and breathing can help. A free tool for social anxiety."),
    # v37
    ("v37_health_anxiety_serious", "gq_short_v37_health_serious.mp4", "v37 — health anxiety: what if it's serious",
     ['"What if it\'s serious? What if not?"',
      '"When health anxiety spirals"',
      '"Health anxiety? Write the fear"'],
     "What if it's serious? What if it isn't? Write the fear, come back to your body, name the anxiety. Not a diagnosis — see a doctor if worried.",
     "#healthanxiety #anxiety #mentalhealth #copingskills #journaling #mindfulness #selfcare #selfhelp #grounding #cbt #stressrelief #mentalhealthawareness #healthanxietysupport #breathing #healing",
     "What if it's serious? What if it isn't? Write the fear. Come back to your body. https://gentlequest.app",
     "What if it's serious? What if it isn't? Write the fear. Come back to your body. Not a diagnosis. See a doctor if worried. #healthanxiety #mentalhealth",
     "When health anxiety spirals, writing the fear and grounding can help. Not a diagnosis — see a doctor if worried. Free tool."),
    # v38
    ("v38_health_anxiety_googling", "gq_short_v38_health_googling.mp4", "v38 — health anxiety: stop googling",
     ['"Stop googling. Write instead."',
      '"When you can\'t stop symptom-searching"',
      '"Health anxiety? Dr. Google isn\'t real"'],
     "Stop googling. Write the worry instead, breathe, log the anxiety. Dr. Google is not a real doctor. Your safety plan is here.",
     "#healthanxiety #anxiety #mentalhealth #copingskills #journaling #mindfulness #selfcare #selfhelp #grounding #cbt #stressrelief #mentalhealthawareness #healthanxietysupport #breathing #healing",
     "Stop googling. Write the worry instead. Breathe. Dr. Google is not a real doctor. https://gentlequest.app",
     "Stop googling. Write the worry instead. Breathe. Log the anxiety. Dr. Google is not a real doctor. #healthanxiety #mentalhealth",
     "When you can't stop googling symptoms, writing the worry instead can break the cycle. A free tool for health anxiety."),
    # v39
    ("v39_mood_five_seconds", "gq_short_v39_mood_five_seconds.mp4", "v39 — mood log: five seconds a day",
     ['"Five seconds a day. Mood log."',
      '"Mood tracking without streaks"',
      '"Log your mood in 5 seconds"'],
     "Five seconds a day. Pick a face, tap done. No streak. No guilt. Just a log. Free, 18+, no ads.",
     "#mood #moodtracking #mentalhealth #selfcare #selfhelp #mentalhealthawareness #mindfulness #journaling #copingskills #stressrelief #anxiety #depression #wellbeing #cbt #healing",
     "Five seconds a day. Pick a face. Tap done. No streak. No guilt. https://gentlequest.app",
     "Five seconds a day. Pick a face. Tap done. No streak. No guilt. Just a log. Free. 18+. #mood #mentalhealth #selfcare",
     "A mood log that takes five seconds. No streaks, no guilt — just a simple check-in. Free and private."),
    # v40
    ("v40_mood_patterns", "gq_short_v40_mood_patterns.mp4", "v40 — mood log: see your patterns",
     ['"See your mood patterns"',
      '"A week of moods, not streaks"',
      '"What changed? Log it."'],
     "A week of moods. What changed? What triggered it? Log again tomorrow. Patterns, not streaks. Pictures, not grades.",
     "#mood #moodtracking #mentalhealth #selfcare #selfhelp #mentalhealthawareness #mindfulness #patterns #copingskills #stressrelief #anxiety #depression #wellbeing #cbt #healing",
     "A week of moods. What changed? What triggered it? Patterns, not streaks. https://gentlequest.app",
     "A week of moods. What changed? What triggered it? Log again tomorrow. Patterns, not streaks. Pictures, not grades. #mood #mentalhealth",
     "See your mood patterns over a week — not streaks, not grades. A free tool for understanding yourself."),
    # v41
    ("v41_safety_fill_calm", "gq_short_v41_safety_fill_calm.mp4", "v41 — safety plan: fill it when calm",
     ['"Fill it when calm. Find it when not."',
      '"Your safety plan, ready"',
      '"Safety plan? Add contacts now"'],
     "Fill it when calm. Find it when you're not. Add contacts, add what helps. Your safety plan lives at the top of your profile.",
     "#safetyplan #mentalhealth #crisis #copingskills #selfcare #selfhelp #mentalhealthawareness #mindfulness #grounding #stressrelief #anxiety #depression #crisisprevention #wellbeing #healing",
     "Fill it when calm. Find it when you're not. Add contacts. Add what helps. https://gentlequest.app",
     "Fill it when calm. Find it when you're not. Add contacts. Add what helps. Free. 18+. #safetyplan #mentalhealth",
     "A safety plan you fill when calm and find when you're not. Add contacts and what helps. Free and private."),
    # v42
    ("v42_safety_one_tap", "gq_short_v42_safety_one_tap.mp4", "v42 — safety plan: one tap to call",
     ['"One tap to call your people"',
      '"Safety plan? Not buried."',
      '"Crisis lines, one tap away"'],
     "One tap to call your people. Crisis lines for your country. Not buried, not forgotten — here. Free, 18+.",
     "#safetyplan #mentalhealth #crisis #copingskills #selfcare #selfhelp #mentalhealthawareness #grounding #stressrelief #anxiety #depression #crisisprevention #crisislines #wellbeing #healing",
     "One tap to call your people. Crisis lines for your country. Not buried. https://gentlequest.app",
     "One tap to call your people. Crisis lines for your country. Not buried. Not forgotten. Here. #safetyplan #mentalhealth",
     "A safety plan with one-tap calling and crisis lines for your country. Not buried — always accessible. Free."),
    # v43
    ("v43_quests_90_seconds", "gq_short_v43_quests_90_seconds.mp4", "v43 — quests: 90 seconds to start",
     ['"90 seconds to start. One quest."',
      '"Tiny quests, no homework feel"',
      '"Pick one quest. Do it now."'],
     "90 seconds to start. Pick one quest, do it now, or browse the library. You will outgrow them — that's the point.",
     "#quests #cbt #mentalhealth #copingskills #behavioralactivation #selfcare #selfhelp #mentalhealthawareness #mindfulness #grounding #breathing #stressrelief #anxiety #depression #healing",
     "90 seconds to start. Pick one quest. Do it now. You'll outgrow them. https://gentlequest.app",
     "90 seconds to start. Pick one quest. Do it now. Or browse the library. You will outgrow them. That's the point. #cbt #mentalhealth",
     "Tiny quests that take 90 seconds. CBT-flavored, no homework feel. The goal is to outgrow them. Free."),
    # v44
    ("v44_quests_outgrow", "gq_short_v44_quests_outgrow.mp4", "v44 — quests: outgrow and uninstall",
     ['"The goal is to uninstall"',
      '"Learn the skill. Delete the app."',
      '"Quests you\'re meant to outgrow"'],
     "The goal is to uninstall. Learn the skill — breathing, grounding, CBT — then delete the app. That's the point.",
     "#quests #cbt #mentalhealth #copingskills #behavioralactivation #selfcare #selfhelp #mentalhealthawareness #mindfulness #grounding #breathing #stressrelief #anxiety #depression #healing",
     "The goal is to uninstall. Learn the skill. Then delete the app. https://gentlequest.app",
     "The goal is to uninstall. Learn the skill. Then delete the app. That's the point. Free. 18+. #cbt #mentalhealth",
     "A mental health app designed to be outgrown. Learn the skills, then uninstall. That's the point. Free."),
    # v45
    ("v45_journal_blank", "gq_short_v45_journal_blank.mp4", "v45 — journal: blank page, no prompts",
     ['"Blank page. No prompts."',
      '"A journal that\'s just yours"',
      '"Write anything. Or nothing."'],
     "Blank page. No prompts. Write anything, or tap a chip to start. Anonymous, private. No AI reads it. No AI summarizes it.",
     "#journaling #mentalhealth #privacy #selfcare #selfhelp #mentalhealthawareness #mindfulness #journal #copingskills #stressrelief #anxiety #depression #writing #wellbeing #healing",
     "Blank page. No prompts. Write anything. No AI reads it. https://gentlequest.app",
     "Blank page. No prompts. Write anything. Or tap a chip. Anonymous. Private. No AI reads it. No AI summarizes it. #journaling #mentalhealth",
     "A journal with a blank page and no prompts. Anonymous, private — no AI reads it. Free and yours."),
    # v46
    ("v46_journal_nothing", "gq_short_v46_journal_nothing.mp4", "v46 — journal: write nothing",
     ['"Write nothing. That\'s fine."',
      '"A journal with no pressure"',
      '"The page is there. You don\'t owe it."'],
     "Write nothing. That's fine. The page is there. You don't owe it words. Log your mood, export when you want.",
     "#journaling #mentalhealth #privacy #selfcare #selfhelp #mentalhealthawareness #mindfulness #journal #copingskills #stressrelief #anxiety #depression #writing #wellbeing #healing",
     "Write nothing. That's fine. The page is there. You don't owe it words. https://gentlequest.app",
     "Write nothing. That's fine. The page is there. You don't owe it words. Free. 18+. #journaling #mentalhealth",
     "A journal with no pressure. The page is there — you don't owe it words. Free and private."),
    # v47
    ("v47_grounding_60_seconds", "gq_short_v47_grounding_60.mp4", "v47 — grounding: 60 seconds",
     ['"60 seconds. Back to now."',
      '"5-4-3-2-1 grounding exercise"',
      '"Ground yourself in 60 seconds"'],
     "60 seconds. 5 you see, 4 you touch, 3 you hear, 2 you smell, 1 you taste. Back to now. Free, 18+.",
     "#grounding #54321 #mentalhealth #anxiety #copingskills #mindfulness #selfcare #selfhelp #breathing #stressrelief #mentalhealthawareness #groundingexercise #anxietyrelief #panicattack #healing",
     "60 seconds. 5 you see. 4 you touch. 3 you hear. 2 you smell. 1 you taste. Back to now. https://gentlequest.app",
     "60 seconds. 5 you see. 4 you touch. 3 you hear. 2 you smell. 1 you taste. Back to now. Free. 18+. #grounding #mentalhealth",
     "The 5-4-3-2-1 grounding exercise in 60 seconds. Back to now. A free tool for anxious moments."),
    # v48
    ("v48_grounding_races", "gq_short_v48_grounding_races.mp4", "v48 — grounding: mind racing",
     ['"Mind racing? Try this."',
      '"When your mind won\'t stop"',
      '"Ground yourself. You are here."'],
     "Mind racing? 5 things you see, 4 you can touch, then log your mood. Your feet on the floor — you are here.",
     "#grounding #54321 #mentalhealth #anxiety #copingskills #mindfulness #selfcare #selfhelp #breathing #stressrelief #mentalhealthawareness #groundingexercise #anxietyrelief #overthinking #healing",
     "Mind racing? 5 things you see. 4 you can touch. You are here. https://gentlequest.app",
     "Mind racing? 5 things you see. 4 you can touch. Then log your mood. Your feet on the floor. You are here. #grounding #mentalhealth",
     "When your mind races, grounding can bring you back. Your feet on the floor — you are here. Free tool."),
    # v49
    ("v49_breathing_box_90", "gq_short_v49_breathing_box_90.mp4", "v49 — breathing: box breathing 90 seconds",
     ['"90 seconds. Box breathing."',
      '"In 4. Hold 4. Out 4. Hold 4."',
      '"Box breathing in 90 seconds"'],
     "90 seconds. In for 4, hold for 4, out for 4, hold for 4. That's it. You are breathing. Free, 18+.",
     "#breathing #boxbreathing #mentalhealth #anxiety #copingskills #mindfulness #selfcare #selfhelp #stressrelief #mentalhealthawareness #breathingexercise #anxietyrelief #panicattack #grounding #healing",
     "90 seconds. In for 4. Hold for 4. Out for 4. Hold for 4. That's it. https://gentlequest.app",
     "90 seconds. In for 4. Hold for 4. Out for 4. Hold for 4. That's it. You are breathing. Free. 18+. #breathing #mentalhealth",
     "Box breathing in 90 seconds. In for 4, hold for 4, out for 4, hold for 4. A free tool for calm."),
    # v50
    ("v50_breathing_cant_slow", "gq_short_v50_breathing_cant_slow.mp4", "v50 — breathing: can't breathe slow",
     ['"Can\'t breathe slow? Follow this"',
      '"When breathing feels impossible"',
      '"Just follow. In. Hold. Out. Hold."'],
     "Can't breathe slow? Just follow this. In, hold, out, hold. Then log it. Your breath is always here. Free, 18+.",
     "#breathing #boxbreathing #mentalhealth #anxiety #copingskills #mindfulness #selfcare #selfhelp #stressrelief #mentalhealthawareness #breathingexercise #anxietyrelief #panicattack #grounding #healing",
     "Can't breathe slow? Just follow this. In. Hold. Out. Hold. https://gentlequest.app",
     "Can't breathe slow? Just follow this. In. Hold. Out. Hold. Your breath is always here. Free. 18+. #breathing #mentalhealth",
     "When you can't breathe slow, just following along can help. Your breath is always here. Free tool."),
    # v51
    ("v51_body_scan_feet", "gq_short_v51_body_scan_feet.mp4", "v51 — body scan: feel your feet",
     ['"Feel your feet on the floor"',
      '"Body scan in 90 seconds"',
      '"Your body is here. You are here."'],
     "Feel your feet on the floor. Scan up slowly. Your body is here. You are here. Free, 18+.",
     "#bodyscan #mindfulness #mentalhealth #anxiety #copingskills #selfcare #selfhelp #breathing #stressrelief #mentalhealthawareness #grounding #anxietyrelief #meditation #selfawareness #healing",
     "Feel your feet on the floor. Scan up slowly. Your body is here. You are here. https://gentlequest.app",
     "Feel your feet on the floor. Scan up slowly. Your body is here. You are here. Free. 18+. #bodyscan #mindfulness",
     "A body scan that starts with your feet on the floor. Your body is here — you are here. Free tool."),
    # v52
    ("v52_body_scan_tight", "gq_short_v52_body_scan_tight.mp4", "v52 — body scan: where are you tight",
     ['"Where are you tight?"',
      '"Jaw. Shoulders. Chest. Let go."',
      '"Body scan? Find the tension"'],
     "Where are you tight? Jaw, shoulders, chest. Breathe into it, let it go, log the tension. Your body holds what your mind won't say.",
     "#bodyscan #mindfulness #mentalhealth #anxiety #copingskills #selfcare #selfhelp #breathing #stressrelief #mentalhealthawareness #grounding #tension #anxietyrelief #meditation #healing",
     "Where are you tight? Jaw. Shoulders. Chest. Breathe into it. Let it go. https://gentlequest.app",
     "Where are you tight? Jaw. Shoulders. Chest. Breathe into it. Let it go. Your body holds what your mind won't say. #bodyscan #mentalhealth",
     "A body scan for tension — jaw, shoulders, chest. Your body holds what your mind won't say. Free tool."),
    # v53
    ("v53_thought_record_write", "gq_short_v53_thought_record.mp4", "v53 — thought record: write the thought",
     ['"Write the thought down"',
      '"A thought on paper is smaller"',
      '"Thought record? Just write it"'],
     "Write the thought down. Exactly as it is. A thought on paper is smaller than in your head. Name the feeling.",
     "#thoughtrecord #cbt #mentalhealth #anxiety #copingskills #journaling #selfcare #selfhelp #mindfulness #stressrelief #mentalhealthawareness #grounding #anxietyrelief #overthinking #healing",
     "Write the thought down. Exactly as it is. A thought on paper is smaller. https://gentlequest.app",
     "Write the thought down. Exactly as it is. A thought on paper is smaller than in your head. Free. 18+. #cbt #mentalhealth",
     "Writing a thought down exactly as it is can shrink it. A free CBT-flavored tool for overthinking."),
    # v54
    ("v54_thought_record_true", "gq_short_v54_thought_true.mp4", "v54 — thought record: is it true or just loud",
     ['"Is it true? Or just loud?"',
      '"Loud ≠ true. Repeated ≠ real."',
      '"Question your thoughts"'],
     "Is it true? Or just loud? Write it, then ask. Talk it through, then ground. Loud doesn't mean true. Repeated doesn't mean real.",
     "#thoughtrecord #cbt #mentalhealth #anxiety #copingskills #journaling #selfcare #selfhelp #mindfulness #stressrelief #mentalhealthawareness #grounding #anxietyrelief #overthinking #healing",
     "Is it true? Or just loud? Write it. Then ask. Loud ≠ true. https://gentlequest.app",
     "Is it true? Or just loud? Write it. Ask. Talk it through. Ground. Loud ≠ true. Repeated ≠ real. Free. 18+. #cbt #mentalhealth",
     "Is it true, or just loud? A CBT-flavored tool to question your thoughts. Loud doesn't mean true. Free."),
    # v55
    ("v55_behavioral_one_thing", "gq_short_v55_behavioral_one.mp4", "v55 — behavioral activation: do one small thing",
     ['"Do one small thing. 90 seconds."',
      '"Action before motivation"',
      '"Behavioral activation? Start small"'],
     "Do one small thing. 90 seconds. Badly. Then log how you feel after. Action before motivation — always.",
     "#behavioralactivation #cbt #mentalhealth #depression #copingskills #selfcare #selfhelp #mindfulness #stressrelief #mentalhealthawareness #motivation #anxiety #tinyquests #productivity #healing",
     "Do one small thing. 90 seconds. Badly. Then log how you feel after. https://gentlequest.app",
     "Do one small thing. 90 seconds. Badly. Then log how you feel after. Action before motivation. Always. #mentalhealth #cbt",
     "Behavioral activation: do one small thing badly in 90 seconds. Action before motivation — always. Free."),
    # v56
    ("v56_behavioral_action", "gq_short_v56_behavioral_action.mp4", "v56 — behavioral activation: action before motivation",
     ['"You don\'t wait for motivation"',
      '"Act first. Feel later."',
      '"The feeling follows the action"'],
     "You don't wait for motivation. You act first. One quest, do it badly, then check in. The feeling follows the action — not the reverse.",
     "#behavioralactivation #cbt #mentalhealth #depression #copingskills #selfcare #selfhelp #mindfulness #stressrelief #mentalhealthawareness #motivation #anxiety #tinyquests #productivity #healing",
     "You don't wait for motivation. You act first. One quest. Do it badly. https://gentlequest.app",
     "You don't wait for motivation. You act first. One quest. Do it badly. The feeling follows the action. Not the reverse. #mentalhealth #cbt",
     "Action before motivation. The feeling follows the action, not the reverse. A free CBT-flavored tool."),
    # v57
    ("v57_sleep_before_bed", "gq_short_v57_sleep_before_bed.mp4", "v57 — sleep hygiene: before bed",
     ['"Before bed: try this"',
      '"A wind-down routine that works"',
      '"Sleep hygiene? Write, breathe, log"'],
     "Before bed: write the day out, breathe slow, log your mood. The page holds the day. You sleep. Free, 18+.",
     "#sleep #sleephygiene #mentalhealth #insomnia #copingskills #journaling #selfcare #selfhelp #mindfulness #breathing #stressrelief #mentalhealthawareness #bedtime #anxiety #healing",
     "Before bed: write the day out. Breathe slow. Log your mood. You sleep. https://gentlequest.app",
     "Before bed: write the day out. Breathe slow. Log your mood. The page holds the day. You sleep. Free. 18+. #sleep #mentalhealth",
     "A before-bed wind-down routine: write the day out, breathe slow, log your mood. The page holds the day. Free."),
    # v58
    ("v58_sleep_cant", "gq_short_v58_sleep_cant.mp4", "v58 — sleep hygiene: can't sleep",
     ['"Can\'t sleep? Try this."',
      '"When sleep won\'t come"',
      '"Dump every thought. Then sleep."'],
     "Can't sleep? Dump every thought, ground, breathe slow, log it. The loop breaks. Sleep comes. Free, 18+.",
     "#sleep #sleephygiene #mentalhealth #insomnia #copingskills #journaling #selfcare #selfhelp #mindfulness #breathing #stressrelief #mentalhealthawareness #grounding #anxiety #healing",
     "Can't sleep? Dump every thought. Ground. Breathe slow. Log it. https://gentlequest.app",
     "Can't sleep? Dump every thought. Ground. Breathe slow. Log it. The loop breaks. Sleep comes. Free. 18+. #sleep #mentalhealth",
     "When sleep won't come, dumping every thought and grounding can break the loop. A free tool for insomnia."),
    # v59
    ("v59_no_ads", "gq_short_v59_no_ads.mp4", "v59 — anti-pattern: no ads",
     ['"No ads. No upsell. No paywall."',
      '"A mental health app with no ads"',
      '"Free. 18+. That\'s it."'],
     "No ads. No upsell. No paywall. No premium tier. No lock-in. Free, 18+, that's it. Your data is exportable and deletable.",
     "#noads #free #mentalhealth #privacy #selfcare #selfhelp #mentalhealthawareness #mindfulness #nopaywall #transparency #copingskills #stressrelief #anxiety #depression #healing",
     "No ads. No upsell. No paywall. No premium tier. No lock-in. Free. 18+. https://gentlequest.app",
     "No ads. No upsell. No paywall. No premium tier. No lock-in. Free. 18+. That's it. #mentalhealth #noads #free",
     "A mental health app with no ads, no upsell, no paywall, no lock-in. Free and 18+. That's it."),
    # v60
    ("v60_no_notifications", "gq_short_v60_no_notifications.mp4", "v60 — anti-pattern: no notifications spam",
     ['"We don\'t spam you"',
      '"Notifications? You choose."',
      '"Your phone is loud enough"'],
     "We don't spam you. You choose what, when, or off. Default: quiet. No streaks to remind you. Your phone is loud enough.",
     "#notifications #mentalhealth #privacy #selfcare #selfhelp #mentalhealthawareness #mindfulness #nospam #copingskills #stressrelief #anxiety #depression #wellbeing #boundaries #healing",
     "We don't spam you. You choose what, when, or off. Default: quiet. https://gentlequest.app",
     "We don't spam you. You choose what, when, or off. Default: quiet. Your phone is loud enough. Free. 18+. #mentalhealth #nospam",
     "A mental health app that doesn't spam you. You choose what, when, or off. Default: quiet. Free."),
    # v61
    ("v61_no_ai_eavesdropping", "gq_short_v61_no_ai_eavesdrop.mp4", "v61 — anti-pattern: no AI eavesdropping",
     ['"No AI reads your journal"',
      '"Your journal is just yours"',
      '"No AI. No summaries. No training."'],
     "No AI reads your journal. No AI summarizes it. No AI trains on it. Anonymous mode, export anytime, delete anytime. Just yours.",
     "#privacy #ai #mentalhealth #journaling #selfcare #selfhelp #mentalhealthawareness #mindfulness #nopersonaldata #copingskills #stressrelief #anxiety #depression #dataprotection #healing",
     "No AI reads your journal. No AI summarizes it. No AI trains on it. Just yours. https://gentlequest.app",
     "No AI reads your journal. No AI summarizes it. No AI trains on it. Just yours. Free. 18+. #privacy #mentalhealth",
     "A journal no AI reads, summarizes, or trains on. Anonymous mode, exportable, deletable. Just yours. Free."),
    # v62
    ("v62_no_diagnosis", "gq_short_v62_no_diagnosis.mp4", "v62 — anti-pattern: no diagnosis",
     ['"We don\'t diagnose you"',
      '"PHQ-9 gives a score, not a label"',
      '"A starting point. Not a diagnosis."'],
     "We don't diagnose you. PHQ-9 and GAD-7 give a score, not a label. See a professional. A starting point, not a diagnosis.",
     "#phq9 #mentalhealth #screening #selfcare #selfhelp #mentalhealthawareness #mindfulness #copingskills #stressrelief #anxiety #depression #cbt #clinical #wellbeing #healing",
     "We don't diagnose you. PHQ-9 gives a score, not a label. See a professional. https://gentlequest.app",
     "We don't diagnose you. PHQ-9 gives a score, not a label. See a professional. A starting point. Not a diagnosis. #mentalhealth #phq9",
     "We don't diagnose you. PHQ-9 and GAD-7 give a score, not a label. A starting point — see a professional. Free."),
    # v63
    ("v63_no_streaks", "gq_short_v63_no_streaks.mp4", "v63 — anti-pattern: no streaks",
     ['"No streaks. No guilt."',
      '"Log when you want. Miss a day? Fine."',
      '"You don\'t owe an app consistency"'],
     "No streaks. No guilt. Log when you want. Missed a day? Fine. See your week without the pressure. You don't owe an app consistency.",
     "#nostreaks #mentalhealth #mood #selfcare #selfhelp #mentalhealthawareness #mindfulness #copingskills #stressrelief #anxiety #depression #noguilt #wellbeing #cbt #healing",
     "No streaks. No guilt. Log when you want. Missed a day? Fine. https://gentlequest.app",
     "No streaks. No guilt. Log when you want. Missed a day? Fine. You don't owe an app consistency. Free. 18+. #mentalhealth #nostreaks",
     "A mood log with no streaks and no guilt. Log when you want — missed a day is fine. Free."),
    # v64
    ("v64_not_social_media", "gq_short_v64_not_social.mp4", "v64 — anti-pattern: not social media",
     ['"No feed. No likes. No doomscroll."',
      '"This is not social media"',
      '"Just you and your mood"'],
     "No feed. No likes. No doomscroll. No algorithm to fight. A curated, slow community. Just you and your mood. Free, 18+.",
     "#notsocialmedia #mentalhealth #privacy #selfcare #selfhelp #mentalhealthawareness #mindfulness #nodoomscroll #copingskills #stressrelief #anxiety #depression #wellbeing #nocomparison #healing",
     "No feed. No likes. No doomscroll. No algorithm to fight. Just you and your mood. https://gentlequest.app",
     "No feed. No likes. No doomscroll. No algorithm to fight. Just you and your mood. Free. 18+. #mentalhealth #notsocialmedia",
     "A mental health app that's not social media. No feed, no likes, no doomscroll. Just you and your mood. Free."),
    # v65
    ("v65_not_a_therapist", "gq_short_v65_not_therapist.mp4", "v65 — anti-pattern: not a therapist",
     ['"We are not a therapist"',
      '"A quiet chat, not a clinician"',
      '"Not a replacement. A bridge."'],
     "We are not a therapist. We are a quiet chat with a real safety plan. We take disclosures seriously. Not a replacement — a bridge.",
     "#notatherapist #mentalhealth #safetyplan #selfcare #selfhelp #mentalhealthawareness #mindfulness #copingskills #stressrelief #anxiety #depression #crisis #wellbeing #cbt #healing",
     "We are not a therapist. We are a quiet chat with a real safety plan. https://gentlequest.app",
     "We are not a therapist. We are a quiet chat with a real safety plan. Not a replacement. A bridge. Free. 18+. #mentalhealth",
     "We're not a therapist — we're a quiet chat with a real safety plan. Not a replacement, a bridge. Free."),
    # v66
    ("v66_no_tracking", "gq_short_v66_no_tracking.mp4", "v66 — anti-pattern: no tracking",
     ['"No tracking. No analytics on you."',
      '"Your data is yours. We mean it."',
      '"Anonymous mode. Exportable. Deletable."'],
     "No tracking. No analytics on you. Anonymous mode. Your data is exportable and deletable. We mean it. Free, 18+.",
     "#privacy #notracking #mentalhealth #selfcare #selfhelp #mentalhealthawareness #mindfulness #anonymous #copingskills #stressrelief #anxiety #depression #dataprotection #wellbeing #healing",
     "No tracking. No analytics on you. Anonymous mode. Your data is yours. https://gentlequest.app",
     "No tracking. No analytics on you. Anonymous mode. Your data, exportable, deletable. We mean it. Free. 18+. #privacy #mentalhealth",
     "A mental health app with no tracking and no analytics on you. Anonymous mode, exportable, deletable. Free."),
]


def char_count(s: str) -> int:
    """Count chars excluding surrounding quotes."""
    return len(s.strip().strip('"'))


def generate_kit(slug, mp4, display_name, titles, desc, hashtags, fb, x, linkedin, pinned):
    vnum = slug.split("_")[0]
    t1, t2, t3 = titles
    c1, c2, c3 = char_count(t1), char_count(t2), char_count(t3)
    return f"""# Deploy Kit: {display_name}

## File
- **MP4:** `marketing/shorts/out/final/{mp4}`
- **Duration:** 30s
- **Dimensions:** 1080×1920 (vertical)

## Title (pick one — A/B test)
1. {t1} ({c1} chars)
2. {t2} ({c2} chars)
3. {t3} ({c3} chars)

## Description
{desc}

{LINKS}

{FOOTER}

## Hashtags (15)
{hashtags}

## Pinned comment
```
{pinned}
```

## Upload checklist
- [ ] File selected: {mp4}
- [ ] Category: People & Blogs
- [ ] Audience: No, it's not made for kids
- [ ] Title pasted (pick variant 1, 2, or 3)
- [ ] Description pasted
- [ ] Tags pasted
- [ ] Captions: ON (auto-generate, then fix)
- [ ] Pinned comment: paste after publish, then pin

## Buffer crosspost
- **FB:** {fb}
- **X:** {x}
- **LinkedIn:** {linkedin}
"""


def main():
    count = 0
    for slug, mp4, display_name, titles, desc, hashtags, fb, x, linkedin in KITS:
        vnum = slug.split("_")[0]
        pinned = PINNED[vnum]
        content = generate_kit(slug, mp4, display_name, titles, desc, hashtags, fb, x, linkedin, pinned)
        outpath = OUT_DIR / f"{slug}.md"
        outpath.write_text(content)
        count += 1
    print(f"Generated {count} deploy kits in {OUT_DIR}")


if __name__ == "__main__":
    main()
