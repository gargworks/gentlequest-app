#!/usr/bin/env python3
"""Generate 50 ASO variant sets for GentleQuest and validate constraints."""
import json
import sys
from collections import Counter

VARIANTS = []

def add(title, subtitle, keywords_ios, short_desc, long_desc, promo, target_set, vnum):
    VARIANTS.append({
        "title": title,
        "subtitle": subtitle,
        "keywords_ios": keywords_ios,
        "short_desc_android": short_desc,
        "long_desc_android": long_desc,
        "promo_text_ios": promo,
        "target_set": target_set,
        "variant_num": vnum,
    })

# ---- Shared long description ----
# Must include EXACT: "Not a diagnosis. See a professional for diagnosis."
# Must include: 18+, Free
# Must mention: mood tracking, journaling, safety plan, breathing exercises, grounding, CBT quests
# Must mention: iOS, Android, Web (gentlequest.app)

LONG_DESC = """{lead}

GentleQuest is a calm, gamified mental wellness companion that turns self-care into gentle, achievable quests. Whether you face everyday stress, low moods, or anxious moments, GentleQuest guides you one small step at a time.

FEATURES
- Mood tracking: Log how you feel each day and spot patterns over time with friendly charts.
- Journaling: Reflect with guided prompts and free-form entries in a private, judgment-free space.
- CBT quests: Bite-sized cognitive behavioral therapy-inspired exercises that reframe negative thoughts and build coping skills.
- Breathing exercises: Guided breathing to calm your nervous system during anxious or stressful moments.
- Grounding: 5-4-3-2-1 and sensory grounding techniques to bring you back to the present.
- Safety plan: Build a personal safety plan with coping strategies, warning signs, and contacts for crisis moments.

AVAILABLE EVERYWHERE
Use GentleQuest on iOS, Android, and the Web at gentlequest.app. Your progress syncs across all devices so you can pick up a quest anywhere.

WHO IT'S FOR
GentleQuest is for adults (18+) seeking supportive, self-guided tools for stress, anxiety, and mood. Not a diagnosis. See a professional for diagnosis. If you are in crisis, contact your local emergency services or a crisis helpline immediately.

PRIVACY FIRST
Your entries stay private. No account required to get started, and you can keep your data anonymous.

PRICE
The core experience is Free to use.

Start your first quest today-small steps, gentle progress."""

def ld(lead):
    return LONG_DESC.format(lead=lead)

# =========================================================================
# SET 1: anxiety
# =========================================================================
SET = "anxiety"

add("GentleQuest: Anxiety Relief", "Calm anxiety with CBT",
    "anxiety,calm,relief,stress,cbt,breathing,grounding,mood,depression,worry,panic,relax,cope,wellness",
    "Calm anxiety with CBT quests, breathing & grounding. Free app.",
    ld("Find calm when anxiety strikes."),
    "Calm anxiety with breathing, grounding & CBT quests. Track mood daily. Free on iOS, Android & Web.",
    SET, 1)

add("Anxiety Help & CBT Quests", "Breathe, ground, track",
    "anxiety,help,cbt,quests,breathe,ground,mood,track,depression,stress,calm,cope,panic,relief",
    "Ease anxiety with breathing, grounding & CBT quests. Free.",
    ld("Ease anxious thoughts with gentle, guided tools."),
    "Ease anxiety with breathing and grounding. Reframe worries with CBT quests. Free on iOS, Android & Web.",
    SET, 2)

add("GentleQuest Anxiety Tracker", "Track anxiety & mood",
    "anxiety,tracker,mood,depression,calm,cbt,breathing,grounding,journal,stress,cope,relief,wellness",
    "Track anxiety, log mood & practice CBT quests. Free app.",
    ld("Track your anxiety and mood, then act with calming tools."),
    "Track anxiety and mood, then calm down with breathing, grounding & CBT quests. Free on iOS & Android.",
    SET, 3)

add("Calm Anxiety: GentleQuest", "CBT, breathing, ground",
    "anxiety,calm,cbt,breathing,grounding,mood,depression,stress,journal,cope,relax,relief,wellness",
    "Calm anxiety with breathing, grounding & CBT quests. Free.",
    ld("Calm your anxiety with proven, gentle techniques."),
    "Calm anxiety with breathing and grounding. Build coping skills with CBT quests. Free on iOS & Android.",
    SET, 4)

add("Anxiety Relief & Mood Log", "Journal, breathe, reframe",
    "anxiety,relief,mood,log,journal,breathe,reframe,cbt,depression,stress,calm,cope,grounding",
    "Relieve anxiety with mood logging, journaling & CBT. Free.",
    ld("Relieve anxiety by logging, journaling, and reframing."),
    "Relieve anxiety with mood logging, journaling & CBT quests. Free on iOS, Android & gentlequest.app.",
    SET, 5)

add("GentleQuest: Stress & Anxiety", "Cope with calm CBT",
    "anxiety,stress,cope,calm,cbt,quests,breathing,grounding,mood,depression,journal,relief,relax",
    "Cope with stress & anxiety via CBT quests & breathing. Free.",
    ld("Cope with stress and anxiety, one gentle quest at a time."),
    "Cope with stress & anxiety using CBT quests, breathing & grounding. Free on iOS, Android & Web.",
    SET, 6)

add("Anxiety Companion: GentleQuest", "Breathe, ground, journal",
    "anxiety,companion,breathe,ground,journal,mood,cbt,depression,stress,calm,cope,relief,wellness",
    "Your anxiety companion for breathing & CBT quests. Free.",
    ld("A gentle companion for anxious days and nights."),
    "Your anxiety companion: breathe, ground, journal & complete CBT quests. Free on iOS & Android.",
    SET, 7)

add("Ease Anxiety with GentleQuest", "Mood, CBT, breathing",
    "anxiety,ease,mood,cbt,quests,breathing,grounding,depression,stress,calm,cope,journal,relief",
    "Ease anxiety with mood tracking, CBT quests & breathing. Free.",
    ld("Ease anxiety gently, day by day."),
    "Ease anxiety with mood tracking, CBT quests, breathing & grounding. Free on iOS, Android & Web.",
    SET, 8)

add("GentleQuest: Worry & Anxiety", "Reframe worries, mood",
    "anxiety,worry,reframe,mood,cbt,quests,breathing,grounding,depression,stress,calm,cope,journal",
    "Reframe worries with CBT quests, breathing & grounding. Free.",
    ld("Turn worries into gentle, manageable quests."),
    "Reframe worries with CBT quests. Calm down with breathing & grounding. Free on iOS & Android.",
    SET, 9)

add("Anxiety Calm: CBT & Mood", "Ground, breathe, journal",
    "anxiety,calm,cbt,mood,ground,breathe,journal,depression,stress,cope,relief,wellness,track",
    "Stay calm with CBT quests, grounding, breathing & mood. Free.",
    ld("Stay calm and build resilience against anxiety."),
    "Stay calm with CBT quests, grounding, breathing & mood tracking. Free on iOS, Android & Web.",
    SET, 10)

# =========================================================================
# SET 2: mood_journal
# =========================================================================
SET = "mood_journal"

add("GentleQuest: Mood Journal", "Track mood & journal",
    "mood,journal,track,daily,mental,health,anxiety,cbt,breathing,grounding,reflect,wellness,diary",
    "Track mood & journal daily with CBT quests. Free app.",
    ld("Track your mood and journal your day, gently."),
    "Track mood & journal daily with CBT quests, breathing & grounding. Free on iOS, Android & Web.",
    SET, 1)

add("Mood Tracker & Journal App", "Mental health, CBT",
    "mood,tracker,journal,mental,health,cbt,quests,anxiety,breathing,grounding,reflect,wellness,diary",
    "Mood tracker & journal with CBT quests and breathing. Free.",
    ld("A friendly mood tracker and journal in one calm app."),
    "A friendly mood tracker & journal. Complete CBT quests & practice breathing. Free on iOS & Android.",
    SET, 2)

add("GentleQuest Mood & Diary", "Journal feelings, mood",
    "mood,diary,journal,feelings,track,mental,health,cbt,anxiety,breathing,grounding,reflect,calm",
    "Journal feelings & track mood with CBT quests. Free diary.",
    ld("Your mood diary and journal, made gentle."),
    "Journal feelings & track mood daily. Build coping skills with CBT quests. Free on iOS & Android.",
    SET, 3)

add("Mood Journal: GentleQuest", "Daily mental health log",
    "mood,journal,daily,mental,health,companion,cbt,anxiety,breathing,grounding,reflect,diary,calm",
    "Daily mood journal with CBT quests, breathing & grounding. Free.",
    ld("A daily mood journal that feels like a gentle quest."),
    "A daily mood journal with CBT quests, breathing & grounding. Free on iOS, Android & gentlequest.app.",
    SET, 4)

add("Mood Log & Mental Wellness", "Journal, CBT, breathe",
    "mood,log,mental,wellness,journal,cbt,quests,anxiety,breathing,grounding,reflect,diary,calm",
    "Log mood & journal with CBT quests and breathing. Free.",
    ld("Log your mood and nurture your mental wellness."),
    "Log mood, journal thoughts & complete CBT quests. Calm your mind with breathing. Free on iOS & Android.",
    SET, 5)

add("GentleQuest: Feelings Journal", "Track mood, reflect",
    "mood,feelings,journal,track,reflect,breathe,mental,health,cbt,anxiety,grounding,wellness,calm",
    "Track feelings & journal with breathing and CBT. Free.",
    ld("A feelings journal that grows with you."),
    "Track feelings & journal with prompts. Build resilience with CBT quests. Free on iOS, Android & Web.",
    SET, 6)

add("Mood & Journal: Mental Health", "CBT quests, grounding",
    "mood,journal,mental,health,cbt,quests,grounding,calm,anxiety,breathing,reflect,diary,feelings",
    "Mood & journal app with CBT quests and grounding. Free.",
    ld("Mood tracking and journaling for everyday mental health."),
    "Track mood & journal daily. Practice grounding, breathing & CBT quests. Free on iOS & Android.",
    SET, 7)

add("GentleQuest Mood Tracker", "Journal, breathe, ground",
    "mood,tracker,journal,breathe,ground,mental,health,cbt,anxiety,reflect,wellness,diary,calm",
    "Track mood, journal & practice breathing and grounding. Free.",
    ld("Track your mood and find your calm, one entry at a time."),
    "Track mood, journal & practice breathing and grounding. CBT quests included. Free on iOS & Android.",
    SET, 8)

add("Mental Health Mood Journal", "Track, reflect, CBT",
    "mental,health,mood,journal,track,reflect,cbt,quests,anxiety,breathing,grounding,wellness,calm",
    "Mental health mood journal with CBT quests & breathing. Free.",
    ld("A mood journal built for everyday mental health."),
    "A mood journal for mental health: track feelings, reflect & complete CBT quests. Free on iOS & Android.",
    SET, 9)

add("GentleQuest: Mood & Mind", "Journal, CBT, breathing",
    "mood,mind,journal,cbt,breathing,mental,health,anxiety,grounding,reflect,wellness,diary,calm",
    "Track mood & journal with CBT quests and grounding. Free.",
    ld("Track your mood and train your mind, gently."),
    "Track mood & journal. Train your mind with CBT quests, breathing & grounding. Free on iOS & Android.",
    SET, 10)

# =========================================================================
# SET 3: cbt_selfhelp
# =========================================================================
SET = "cbt_selfhelp"

add("GentleQuest: CBT Self-Help", "Reframe thoughts, mood",
    "cbt,self,help,reframe,thoughts,mood,anxiety,depression,journal,breathing,grounding,therapy,cope",
    "CBT self-help quests to reframe thoughts & track mood. Free.",
    ld("CBT-inspired self-help, one quest at a time."),
    "Reframe thoughts with CBT self-help quests. Track mood & journal. Free on iOS, Android & Web.",
    SET, 1)

add("CBT Quests & Self-Help", "Therapy alternative, mood",
    "cbt,quests,self,help,therapy,alternative,mood,anxiety,depression,journal,breathing,grounding,cope",
    "CBT quests as a gentle therapy alternative. Free app.",
    ld("Self-help quests inspired by cognitive behavioral therapy."),
    "Complete CBT quests that reframe thoughts. Log mood & journal. Free on iOS, Android & Web.",
    SET, 2)

add("GentleQuest CBT Companion", "Self-help, journal",
    "cbt,companion,self,help,journal,breathe,mood,anxiety,depression,grounding,therapy,alternative,cope",
    "Your CBT companion for self-help quests & mood. Free.",
    ld("A companion for CBT-style self-help and reflection."),
    "Your CBT companion: reframe thoughts, journal & track mood. Free on iOS, Android & Web.",
    SET, 3)

add("Self-Help CBT: GentleQuest", "Reframe, track, ground",
    "self,help,cbt,reframe,track,ground,mood,anxiety,depression,journal,breathing,therapy,alternative",
    "Self-help CBT quests to reframe thoughts & ground. Free.",
    ld("Self-help that feels like a gentle adventure."),
    "Self-help CBT quests reframe thoughts & build coping skills. Free on iOS, Android & Web.",
    SET, 4)

add("CBT Self-Help & Mood Log", "Therapy alternative, log",
    "cbt,self,help,mood,log,therapy,alternative,journal,anxiety,depression,breathing,grounding,cope",
    "CBT self-help with mood logging & journaling. Free.",
    ld("CBT self-help with mood logging and journaling."),
    "Reframe thoughts with CBT quests, log mood & journal. Free on iOS, Android & Web.",
    SET, 5)

add("GentleQuest: CBT Quests", "Self-help, breathing",
    "cbt,quests,self,help,breathing,mood,anxiety,depression,journal,grounding,therapy,alternative,cope",
    "CBT quests for self-help, breathing & mood. Free app.",
    ld("Bite-sized CBT quests for daily self-help."),
    "Bite-sized CBT quests reframe thoughts & build coping skills. Free on iOS, Android & Web.",
    SET, 6)

add("Therapy Alternative CBT", "Self-help quests, mood",
    "therapy,alternative,cbt,quests,self,help,mood,anxiety,depression,journal,breathing,grounding,cope",
    "A gentle therapy alternative with CBT quests. Free.",
    ld("A gentle, self-guided therapy alternative."),
    "A gentle therapy alternative: CBT quests, mood tracking & journaling. Free on iOS & Android.",
    SET, 7)

add("GentleQuest: Reframe Thoughts", "CBT self-help, journal",
    "cbt,reframe,thoughts,self,help,journal,mood,anxiety,depression,breathing,grounding,therapy,cope",
    "Reframe thoughts with CBT self-help quests. Free app.",
    ld("Reframe unhelpful thoughts, one quest at a time."),
    "Reframe thoughts with CBT self-help quests. Journal & track mood. Free on iOS, Android & Web.",
    SET, 8)

add("CBT Self-Help Mood Tracker", "Quests, breathing, ground",
    "cbt,self,help,mood,tracker,quests,breathing,grounding,anxiety,depression,journal,therapy,cope",
    "CBT self-help mood tracker with quests. Free app.",
    ld("Track your mood while you work through CBT quests."),
    "Track mood while completing CBT self-help quests. Journal & breathe. Free on iOS & Android.",
    SET, 9)

add("GentleQuest: CBT & Calm", "Self-help, mood, journal",
    "cbt,calm,self,help,mood,journal,anxiety,depression,breathing,grounding,therapy,alternative,cope",
    "CBT self-help for calm: quests, mood & journaling. Free.",
    ld("CBT self-help for a calmer, clearer mind."),
    "CBT self-help quests for a calmer mind. Track mood & journal. Free on iOS, Android & Web.",
    SET, 10)

# =========================================================================
# SET 4: safety_crisis
# =========================================================================
SET = "safety_crisis"

add("GentleQuest: Safety Plan", "Crisis support & cope",
    "safety,plan,crisis,support,coping,anxiety,mood,cbt,breathing,grounding,journal,calm,relief,help",
    "Build a safety plan with coping tools & support. Free app.",
    ld("Build a personal safety plan you can reach anytime."),
    "Create a safety plan with coping steps & contacts. Practice breathing & CBT quests. Free on iOS & Android.",
    SET, 1)

add("Safety Plan & Crisis Support", "Cope, breathe, ground",
    "safety,plan,crisis,support,cope,breathe,ground,mood,cbt,journal,anxiety,calm,relief,help",
    "Safety plan & crisis support with breathing. Free app.",
    ld("A safety plan and coping tools, always within reach."),
    "A safety plan & coping tools anytime. Add contacts & practice grounding. Free on iOS & Android.",
    SET, 2)

add("GentleQuest Crisis Companion", "Safety plan, support",
    "crisis,companion,safety,plan,support,cope,mood,cbt,breathing,grounding,journal,anxiety,calm,help",
    "Crisis companion with safety plan & coping tools. Free.",
    ld("A calm companion for crisis moments and recovery."),
    "A calm crisis companion: build a safety plan & practice coping tools. Free on iOS, Android & Web.",
    SET, 3)

add("Safety Plan: GentleQuest", "Crisis coping, support",
    "safety,plan,crisis,coping,support,mood,cbt,breathing,grounding,journal,anxiety,calm,relief,help",
    "Build a safety plan for crisis coping & support. Free.",
    ld("Your safety plan, built gently and kept private."),
    "Build your safety plan with coping steps & contacts. Practice breathing & CBT. Free on iOS & Android.",
    SET, 4)

add("Crisis Support & Safety Plan", "Breathe, ground, journal",
    "crisis,support,safety,plan,breathe,ground,journal,mood,cbt,anxiety,calm,relief,wellness,cope",
    "Crisis support & safety plan with breathing. Free.",
    ld("Crisis support and a safety plan, in one calm app."),
    "Crisis support & a safety plan in one app. Add contacts & practice grounding. Free on iOS & Android.",
    SET, 5)

add("GentleQuest: Coping & Safety", "Plan, breathe, ground",
    "coping,safety,plan,breathe,ground,mood,cbt,crisis,support,journal,anxiety,calm,relief,help",
    "Coping & safety plan with breathing, grounding & CBT. Free.",
    ld("Coping tools and a safety plan, side by side."),
    "Coping tools & a safety plan: add contacts, practice breathing & CBT quests. Free on iOS & Android.",
    SET, 6)

add("Safety Plan & Support Tools", "Crisis help, CBT, mood",
    "safety,plan,support,tools,crisis,help,cbt,mood,breathing,grounding,journal,anxiety,calm,cope",
    "Safety plan & support tools with CBT quests. Free.",
    ld("Support tools and a safety plan for tough moments."),
    "Support tools & a safety plan. Add contacts, track mood & practice grounding. Free on iOS & Android.",
    SET, 7)

add("GentleQuest: Crisis Calm", "Safety plan, breathing",
    "crisis,calm,safety,plan,breathing,mood,cbt,grounding,support,journal,anxiety,relief,cope,help",
    "Find calm in crisis with a safety plan & breathing. Free.",
    ld("Find calm in crisis with a plan you can trust."),
    "Find calm in crisis with a safety plan. Practice breathing, grounding & CBT quests. Free on iOS & Android.",
    SET, 8)

add("Safety Plan & Mood Coping", "Crisis support, ground",
    "safety,plan,mood,coping,crisis,support,grounding,breathing,cbt,journal,anxiety,calm,relief,help",
    "Safety plan & mood coping with grounding. Free app.",
    ld("A safety plan that works with your daily mood coping."),
    "A safety plan that fits your mood coping routine. Track mood & practice grounding. Free on iOS & Android.",
    SET, 9)

add("GentleQuest: Support & Plan", "Crisis, cope, breathe",
    "support,plan,crisis,cope,breathe,mood,cbt,grounding,safety,journal,anxiety,calm,relief,help",
    "Support & safety plan with coping & breathing. Free.",
    ld("Support and a safety plan, whenever you need them."),
    "Support & a safety plan anytime. Add contacts & practice breathing & CBT quests. Free on iOS & Android.",
    SET, 10)

# =========================================================================
# SET 5: private_noads
# =========================================================================
SET = "private_noads"

add("GentleQuest: Private Journal", "Anonymous, no ads",
    "private,anonymous,no,ads,secure,journal,mood,cbt,breathing,grounding,safety,anxiety,calm,diary",
    "Private & anonymous mood journal. No ads. Free app.",
    ld("A private, anonymous space for your mental wellness."),
    "A private, anonymous space for wellness. Journal, track mood & do CBT quests. Free on iOS & Android.",
    SET, 1)

add("Anonymous Mood Tracker", "Private, no ads, journal",
    "anonymous,mood,tracker,private,no,ads,journal,cbt,breathing,grounding,safety,anxiety,calm,diary",
    "Anonymous mood tracker & journal. No ads. Free.",
    ld("Track your mood anonymously, with zero ads."),
    "Track mood anonymously with zero ads. Journal & complete CBT quests. Free on iOS, Android & Web.",
    SET, 2)

add("GentleQuest: No Ads, Private", "Anonymous journal, mood",
    "no,ads,private,anonymous,journal,mood,cbt,breathing,grounding,safety,anxiety,calm,wellness,diary",
    "No-ads private journal & mood tracker. Anonymous. Free.",
    ld("No ads. No tracking. Just gentle wellness quests."),
    "No ads & no tracking. Journal privately, track mood & do CBT quests. Free on iOS, Android & Web.",
    SET, 3)

add("Private Mental Health Journal", "Anonymous, no ads, CBT",
    "private,mental,health,journal,anonymous,no,ads,cbt,mood,breathing,grounding,safety,anxiety,calm",
    "Private mental health journal. Anonymous & no ads. Free.",
    ld("A private journal for your mental health, ad-free."),
    "A private, ad-free journal for mental health. Track mood & do CBT quests. Free on iOS & Android.",
    SET, 4)

add("GentleQuest: Anonymous Diary", "No ads, private, secure",
    "anonymous,diary,no,ads,private,secure,mood,cbt,breathing,grounding,safety,anxiety,calm,journal",
    "Anonymous diary & mood tracker. No ads. Free app.",
    ld("An anonymous diary that respects your privacy."),
    "An anonymous diary that respects your privacy. No ads. Track mood & do CBT quests. Free on iOS & Android.",
    SET, 5)

add("No-Ads Mood & Journal App", "Private, anonymous, CBT",
    "no,ads,mood,journal,private,anonymous,cbt,breathing,grounding,safety,anxiety,calm,wellness,diary",
    "No-ads mood & journal app. Private & anonymous. Free.",
    ld("Your mood and journal, ad-free and private."),
    "Your mood tracker & journal, ad-free & private. Complete CBT quests. Free on iOS, Android & Web.",
    SET, 6)

add("GentleQuest: Private & Calm", "Anonymous, no ads, mood",
    "private,calm,anonymous,no,ads,mood,cbt,breathing,grounding,safety,anxiety,journal,wellness,diary",
    "Private & calm mood tracker. Anonymous, no ads. Free.",
    ld("Private, calm, and completely ad-free."),
    "Private, calm & ad-free. Track mood, journal & do CBT quests. Free on iOS, Android & Web.",
    SET, 7)

add("Anonymous Wellness Journal", "No ads, private, CBT",
    "anonymous,wellness,journal,no,ads,private,cbt,quests,mood,breathing,grounding,safety,anxiety,calm",
    "Anonymous wellness journal with CBT quests. No ads. Free.",
    ld("An anonymous wellness journal with no ads."),
    "An anonymous wellness journal with no ads. Track mood & do CBT quests. Free on iOS & Android.",
    SET, 8)

add("GentleQuest: Secure & Private", "No ads, anonymous, mood",
    "secure,private,no,ads,anonymous,mood,cbt,breathing,grounding,safety,anxiety,journal,calm,diary",
    "Secure & private mood tracker. No ads, anonymous. Free.",
    ld("Secure, private, and ad-free wellness quests."),
    "Secure, private & ad-free. Track mood, journal & do CBT quests. Free on iOS, Android & Web.",
    SET, 9)

add("Private CBT & Mood Tracker", "Anonymous, no ads, log",
    "private,cbt,mood,tracker,anonymous,no,ads,journal,breathing,grounding,safety,anxiety,calm,diary",
    "Private CBT & mood tracker. Anonymous, no ads. Free.",
    ld("A private CBT and mood tracker with no ads."),
    "A private CBT & mood tracker with no ads. Stay anonymous & journal. Free on iOS, Android & Web.",
    SET, 10)

# =========================================================================
# VALIDATION
# =========================================================================
errors = []

forbidden = ["Garg", "Lokesh", "Axis Bank"]
required_long = ["18+", "Free", "Not a diagnosis. See a professional for diagnosis."]
required_mentions = ["mood tracking", "journaling", "safety plan", "breathing exercises", "grounding", "CBT quests"]
required_platforms = ["iOS", "Android", "gentlequest.app"]
valid_sets = {"anxiety", "mood_journal", "cbt_selfhelp", "safety_crisis", "private_noads"}

set_counts = Counter()

for i, v in enumerate(VARIANTS):
    tag = f"[{v['target_set']}#{v['variant_num']}]"
    for w in forbidden:
        for field in ["title", "subtitle", "keywords_ios", "short_desc_android", "long_desc_android", "promo_text_ios"]:
            if w.lower() in v[field].lower():
                errors.append(f"{tag} forbidden word '{w}' in {field}")
    if len(v["title"]) > 30:
        errors.append(f"{tag} title {len(v['title'])}>30: {v['title']!r}")
    if len(v["subtitle"]) > 30:
        errors.append(f"{tag} subtitle {len(v['subtitle'])}>30: {v['subtitle']!r}")
    if len(v["keywords_ios"]) > 100:
        errors.append(f"{tag} keywords_ios {len(v['keywords_ios'])}>100")
    if len(v["short_desc_android"]) > 80:
        errors.append(f"{tag} short_desc {len(v['short_desc_android'])}>80: {v['short_desc_android']!r}")
    if len(v["long_desc_android"]) > 4000:
        errors.append(f"{tag} long_desc {len(v['long_desc_android'])}>4000")
    if len(v["promo_text_ios"]) > 170:
        errors.append(f"{tag} promo_text {len(v['promo_text_ios'])}>170")
    ld_text = v["long_desc_android"]
    for r in required_long:
        if r not in ld_text:
            errors.append(f"{tag} long_desc missing '{r}'")
    for m in required_mentions:
        if m.lower() not in ld_text.lower():
            errors.append(f"{tag} long_desc missing mention '{m}'")
    for p in required_platforms:
        if p.lower() not in ld_text.lower():
            errors.append(f"{tag} long_desc missing platform '{p}'")
    if v["target_set"] not in valid_sets:
        errors.append(f"{tag} invalid target_set")
    if not (1 <= v["variant_num"] <= 10):
        errors.append(f"{tag} variant_num out of range")
    set_counts[v["target_set"]] += 1

for s in valid_sets:
    if set_counts[s] != 10:
        errors.append(f"set '{s}' has {set_counts[s]} variants (expected 10)")

if len(VARIANTS) != 50:
    errors.append(f"total variants {len(VARIANTS)} != 50")

if errors:
    print("VALIDATION FAILED:")
    for e in errors:
        print(" -", e)
    sys.exit(1)
else:
    print(f"VALIDATION PASSED: {len(VARIANTS)} variants, all constraints satisfied.")

out_path = "/Users/lokeshgarg/gentlequest/marketing/aso/variants.json"
with open(out_path, "w") as f:
    json.dump(VARIANTS, f, indent=2, ensure_ascii=False)
print(f"Wrote {out_path}")
