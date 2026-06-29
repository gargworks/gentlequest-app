#!/usr/bin/env python3
"""Catalog of GQ YT Shorts. Each entry = 30s 1080x1920 vertical.

Run:
  python3 shorts_catalog.py            # render all
  python3 shorts_catalog.py v2_safety  # render one

Outputs land in marketing/shorts/out/<name>.mp4.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RENDER = ROOT / "render_short.py"
OUT_DIR = ROOT / "out"
OUT_DIR.mkdir(exist_ok=True)


CATALOG = {
    # v1 already shipped (kept here for reference / re-render)
    "v1_what_it_is": {
        "out": str(OUT_DIR / "gq_short_v1.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "a small mental-health app", "dur": 4, "size": 78},
            {"kind": "phone", "src": "I1_chat_home.png",       "caption": "say what is on your mind",    "dur": 7},
            {"kind": "phone", "src": "M2c_mood_submitted.png", "caption": "check in with your mood",     "dur": 6},
            {"kind": "phone", "src": "P3_safety_plan_card.png","caption": "safety plan, not buried",     "dur": 6},
            {"kind": "phone", "src": "Q2_quest_preview.png",   "caption": "tiny quests, no streaks",     "dur": 5},
            {"kind": "card",  "caption": "iOS + Android · free",                                          "dur": 2, "size": 72},
        ],
    },

    "v2_safety_plan": {
        "out": str(OUT_DIR / "gq_short_v2_safety.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "safety plan,\nnot buried",                                      "dur": 4, "size": 84},
            {"kind": "phone", "src": "P1_profile_top.png",      "caption": "open your profile",            "dur": 6},
            {"kind": "phone", "src": "P1b_about_you.png",       "caption": "tap once. fill once.",         "dur": 6},
            {"kind": "phone", "src": "P3_safety_plan_card.png", "caption": "crisis lines for your country","dur": 7},
            {"kind": "phone", "src": "I7b_safety_legal_sheet.png", "caption": "people you trust · things that help", "dur": 5},
            {"kind": "card",  "caption": "fill it when you are calm.\nfind it when you are not.",          "dur": 2, "size": 60},
        ],
    },

    "v3_mood_no_streaks": {
        "out": str(OUT_DIR / "gq_short_v3_mood.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "mood,\nwithout streaks",                                        "dur": 4, "size": 84},
            {"kind": "phone", "src": "M1_mood_tab.png",        "caption": "open mood",                    "dur": 5},
            {"kind": "phone", "src": "M2_mood_sheet.png",      "caption": "pick how you feel",            "dur": 5},
            {"kind": "phone", "src": "M2b_emoji_selected.png", "caption": "five seconds",                 "dur": 5},
            {"kind": "phone", "src": "M2c_mood_submitted.png", "caption": "logged. that is it.",          "dur": 7},
            {"kind": "card",  "caption": "no streak guilt.\njust notes.",                                 "dur": 4, "size": 72},
        ],
    },

    "v4_tiny_quests": {
        "out": str(OUT_DIR / "gq_short_v4_quests.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "tiny quests.\nno homework feel.",                               "dur": 4, "size": 72},
            {"kind": "phone", "src": "X1c_quest.png",         "caption": "open quests",                   "dur": 5},
            {"kind": "phone", "src": "Q2_quest_preview.png",  "caption": "90-second box breathing",       "dur": 7},
            {"kind": "phone", "src": "RL1_library_all.png",   "caption": "or the library",               "dur": 6},
            {"kind": "phone", "src": "RL2_breathing.png",     "caption": "guided audio. short.",          "dur": 5},
            {"kind": "card",  "caption": "you will outgrow them.\nthat is the point.",                    "dur": 3, "size": 64},
        ],
    },

    "v5_not_an_ai_therapist": {
        "out": str(OUT_DIR / "gq_short_v5_not_ai_therapist.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "not an AI therapist.",                                          "dur": 4, "size": 80},
            {"kind": "phone", "src": "I1_chat_home.png",         "caption": "small chats",                "dur": 6},
            {"kind": "phone", "src": "I7_overflow_open.png",     "caption": "real disclosures",           "dur": 5},
            {"kind": "phone", "src": "I7b_safety_legal_sheet.png", "caption": "not medical care",         "dur": 6},
            {"kind": "phone", "src": "P3_safety_plan_card.png",  "caption": "but a real safety plan",     "dur": 6},
            {"kind": "card",  "caption": "gentler than a podcast.\nserious where it counts.",             "dur": 3, "size": 58},
        ],
    },

    "v6_free_beta": {
        "out": str(OUT_DIR / "gq_short_v6_beta.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "GentleQuest is in beta.",                                       "dur": 4, "size": 78},
            {"kind": "phone", "src": "X1_talk.png",          "caption": "talk",                           "dur": 5},
            {"kind": "phone", "src": "X1c_quest.png",        "caption": "quests",                         "dur": 5},
            {"kind": "phone", "src": "RL1_library_all.png",  "caption": "a small free library",           "dur": 6},
            {"kind": "phone", "src": "P3_safety_plan_card.png", "caption": "and a real safety plan",      "dur": 7},
            {"kind": "card",  "caption": "iOS + Android · 18+ · free",                                    "dur": 3, "size": 64},
        ],
    },

    # ── v7: journaling — private notes, no AI reading ──
    "v7_journal_private": {
        "out": str(OUT_DIR / "gq_short_v7_journal.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "a journal\nthat is just yours",                                 "dur": 4, "size": 80},
            {"kind": "phone", "src": "J1_journal_empty.png",  "caption": "blank page. no prompts.",       "dur": 5},
            {"kind": "phone", "src": "J3_entry_editor.png",   "caption": "write whatever",                "dur": 6},
            {"kind": "phone", "src": "S4_anonymity_toggled.png", "caption": "anonymous mode",             "dur": 5},
            {"kind": "phone", "src": "S2_export_snackbar.png",  "caption": "export anytime. leave anytime.", "dur": 6},
            {"kind": "card",  "caption": "we do not read it.\nno AI summarizes it.",                      "dur": 4, "size": 64},
        ],
    },

    # ── v8: privacy-first — your data, your control ──
    "v8_privacy_first": {
        "out": str(OUT_DIR / "gq_short_v8_privacy.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "your data\nis yours",                                           "dur": 4, "size": 84},
            {"kind": "phone", "src": "S1_settings_top.png",      "caption": "settings",                    "dur": 5},
            {"kind": "phone", "src": "S2_export_snackbar.png",   "caption": "export everything",           "dur": 5},
            {"kind": "phone", "src": "S3_delete_account_sheet.png", "caption": "delete everything",       "dur": 6},
            {"kind": "phone", "src": "S4_anonymity_toggled.png",  "caption": "or go anonymous",            "dur": 5},
            {"kind": "card",  "caption": "no account needed.\nno tracking. no ads.",                      "dur": 5, "size": 62},
        ],
    },

    # ── v9: grounding exercise — 5-4-3-2-1 technique ──
    "v9_grounding_54321": {
        "out": str(OUT_DIR / "gq_short_v9_grounding.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "anxious?\ntry this.",                                           "dur": 4, "size": 80},
            {"kind": "phone", "src": "RL1_library_all.png",     "caption": "open the library",             "dur": 5},
            {"kind": "phone", "src": "RL2b_grounding.png",      "caption": "grounding exercise",           "dur": 6},
            {"kind": "phone", "src": "RL4_exercise_open.png",   "caption": "5 things you see",             "dur": 5},
            {"kind": "phone", "src": "RL4_exercise.png",        "caption": "4 you can touch",              "dur": 5},
            {"kind": "card",  "caption": "60 seconds.\nback to now.",                                     "dur": 5, "size": 70},
        ],
    },

    # ── v10: not social media — curated community, no doomscroll ──
    "v10_not_social_media": {
        "out": str(OUT_DIR / "gq_short_v10_community.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "this is not\nsocial media",                                     "dur": 4, "size": 80},
            {"kind": "phone", "src": "X1d_community.png",      "caption": "a community tab",               "dur": 5},
            {"kind": "phone", "src": "X_community_tab.png",    "caption": "curated. slow.",                "dur": 6},
            {"kind": "phone", "src": "I1_chat_home.png",       "caption": "no likes. no follower count.",  "dur": 5},
            {"kind": "phone", "src": "M2c_mood_submitted.png", "caption": "just you and your mood",        "dur": 6},
            {"kind": "card",  "caption": "no feed to scroll.\nno algorithm to fight.",                    "dur": 4, "size": 58},
        ],
    },

    # ── v11: first 30 seconds — onboarding ──
    "v11_first_30_seconds": {
        "out": str(OUT_DIR / "gq_short_v11_onboarding.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "first 30 seconds\nin the app",                                  "dur": 4, "size": 76},
            {"kind": "phone", "src": "W1_welcome_hero.png",    "caption": "open it",                       "dur": 5},
            {"kind": "phone", "src": "W2_age_modal.png",       "caption": "18+ check",                     "dur": 4},
            {"kind": "phone", "src": "I1_chat_home.png",       "caption": "say hi",                        "dur": 6},
            {"kind": "phone", "src": "M2_mood_sheet.png",      "caption": "log your mood",                 "dur": 6},
            {"kind": "card",  "caption": "that is it.\nyou are in.",                                       "dur": 5, "size": 72},
        ],
    },

    # ── v12: clinical screening — real PHQ-9, not just chat ──
    "v12_clinical_screening": {
        "out": str(OUT_DIR / "gq_short_v12_screening.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "real screening.\nnot just chat.",                               "dur": 4, "size": 76},
            {"kind": "phone", "src": "M4_clinical_assessment_entry.png", "caption": "clinical check-in",   "dur": 5},
            {"kind": "phone", "src": "CA2_phq9_q1.png",       "caption": "PHQ-9. validated.",               "dur": 6},
            {"kind": "phone", "src": "CA4_result_reveal.png",  "caption": "honest results",                 "dur": 6},
            {"kind": "phone", "src": "P3_safety_plan_card.png", "caption": "and a safety plan if needed",   "dur": 5},
            {"kind": "card",  "caption": "not a diagnosis.\na starting point.",                            "dur": 4, "size": 64},
        ],
    },

    # ── v13: weekly mood review — patterns, not streaks ──
    "v13_weekly_review": {
        "out": str(OUT_DIR / "gq_short_v13_weekly.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "a week\nof moods",                                              "dur": 4, "size": 80},
            {"kind": "phone", "src": "M1_mood_tab.png",        "caption": "you logged a few moods",       "dur": 5},
            {"kind": "phone", "src": "M5_weekly_review_row.png", "caption": "at the end of the week",    "dur": 6},
            {"kind": "phone", "src": "M5b_after_scroll.png",   "caption": "patterns, not streaks",       "dur": 6},
            {"kind": "phone", "src": "M3_low_mood_reflection.png", "caption": "trends, not guilt",       "dur": 5},
            {"kind": "card",  "caption": "no streak to break.\njust a picture of your week.",            "dur": 4, "size": 60},
        ],
    },

    # ── v14: journaling with chips — low friction ──
    "v14_journal_chips": {
        "out": str(OUT_DIR / "gq_short_v14_journal_chips.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "journaling\nwithout pressure",                                 "dur": 4, "size": 76},
            {"kind": "phone", "src": "J1_journal_empty.png",  "caption": "blank page",                    "dur": 4},
            {"kind": "phone", "src": "J2_chip_prefill.png",   "caption": "or tap a chip to start",        "dur": 6},
            {"kind": "phone", "src": "J3_entry_editor.png",   "caption": "write a line. or a paragraph.", "dur": 6},
            {"kind": "phone", "src": "S4_anonymity_toggled.png", "caption": "anonymous. private.",        "dur": 5},
            {"kind": "card",  "caption": "no AI reads it.\nno prompts. just yours.",                      "dur": 5, "size": 62},
        ],
    },

    # ── v15: breathing exercise — 90 seconds ──
    "v15_breathing": {
        "out": str(OUT_DIR / "gq_short_v15_breathing.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "90 seconds.\nbreathe.",                                         "dur": 4, "size": 84},
            {"kind": "phone", "src": "RL1_library_all.png",     "caption": "open the library",             "dur": 4},
            {"kind": "phone", "src": "RL2_breathing.png",       "caption": "box breathing",                "dur": 6},
            {"kind": "phone", "src": "RL4_exercise_open.png",   "caption": "in. hold. out. hold.",         "dur": 7},
            {"kind": "phone", "src": "RL4_exercise.png",        "caption": "four counts each",             "dur": 5},
            {"kind": "card",  "caption": "that is it.\nyou are breathing.",                               "dur": 4, "size": 68},
        ],
    },

    # ── v16: compliance guard — 18+ only ──
    "v16_compliance_guard": {
        "out": str(OUT_DIR / "gq_short_v16_compliance.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "this app is\n18+ only",                                        "dur": 4, "size": 80},
            {"kind": "phone", "src": "W1_welcome_hero.png",    "caption": "open it",                       "dur": 4},
            {"kind": "phone", "src": "W2_age_modal.png",       "caption": "age check",                     "dur": 5},
            {"kind": "phone", "src": "W4_under18_screen.png",  "caption": "under 18? here is what helps",   "dur": 7},
            {"kind": "phone", "src": "C1_compliance_guard.png", "caption": "we mean it",                   "dur": 5},
            {"kind": "card",  "caption": "not for kids.\nnot a toy.",                                     "dur": 5, "size": 70},
        ],
    },

    # ── v17: safety contacts — people you trust ──
    "v17_safety_contacts": {
        "out": str(OUT_DIR / "gq_short_v17_contacts.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "who do you\ncall?",                                            "dur": 4, "size": 80},
            {"kind": "phone", "src": "P1_profile_top.png",      "caption": "open your profile",            "dur": 4},
            {"kind": "phone", "src": "P3_safety_plan_card.png", "caption": "safety plan",                  "dur": 5},
            {"kind": "phone", "src": "P4_safety_contacts.png",  "caption": "add people you trust",         "dur": 6},
            {"kind": "phone", "src": "P5_safety_contacts.png",  "caption": "one tap to call",              "dur": 6},
            {"kind": "card",  "caption": "fill it now.\nfind it later.",                                  "dur": 5, "size": 68},
        ],
    },

    # ── v18: not a therapist — honest framing ──
    "v18_honest_framing": {
        "out": str(OUT_DIR / "gq_short_v18_honest.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "we are not\na therapist",                                      "dur": 4, "size": 80},
            {"kind": "phone", "src": "I1_chat_home.png",       "caption": "we are a quiet chat",           "dur": 5},
            {"kind": "phone", "src": "I7_overflow_open.png",   "caption": "real disclosures happen here",  "dur": 5},
            {"kind": "phone", "src": "I7b_safety_legal_sheet.png", "caption": "and we take that seriously", "dur": 6},
            {"kind": "phone", "src": "P3_safety_plan_card.png", "caption": "safety plan. crisis lines.",   "dur": 6},
            {"kind": "card",  "caption": "not a replacement.\na bridge.",                                 "dur": 4, "size": 64},
        ],
    },

    # ════════════════════════════════════════════════════════════════════
    # W1 RESURRECTION — v19 through v60
    # Symptom-led (v19-v38): 10 symptoms × 2 framings
    # Mechanic-led (v39-v58): 10 mechanics × 2 framings
    # Anti-pattern (v59-v60+): 8 shorts
    # ════════════════════════════════════════════════════════════════════

    # ── v19: anxiety — "your chest is tight" (symptom-led, framing 1) ──
    "v19_anxiety_tight": {
        "out": str(OUT_DIR / "gq_short_v19_anxiety_tight.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "your chest\nis tight",                                         "dur": 4, "size": 84},
            {"kind": "card",  "caption": "your thoughts\nwon't slow down",                               "dur": 4, "size": 78},
            {"kind": "phone", "src": "RL2_breathing.png",       "caption": "open breathing",              "dur": 6},
            {"kind": "phone", "src": "RL4_exercise_open.png",   "caption": "in. hold. out. hold.",        "dur": 7},
            {"kind": "phone", "src": "I1_chat_home.png",        "caption": "or just say it",              "dur": 5},
            {"kind": "card",  "caption": "90 seconds.\nback to now.",                                     "dur": 4, "size": 70},
        ],
    },

    # ── v20: anxiety — "you can't stop worrying" (symptom-led, framing 2) ──
    "v20_anxiety_worry": {
        "out": str(OUT_DIR / "gq_short_v20_anxiety_worry.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "can't stop\nworrying?",                                        "dur": 4, "size": 82},
            {"kind": "phone", "src": "J1_journal_empty.png",    "caption": "write it down",               "dur": 6},
            {"kind": "phone", "src": "J3_entry_editor.png",     "caption": "every loop. one page.",       "dur": 6},
            {"kind": "phone", "src": "M2_mood_sheet.png",       "caption": "name the feeling",            "dur": 5},
            {"kind": "phone", "src": "RL2b_grounding.png",      "caption": "then ground yourself",        "dur": 5},
            {"kind": "card",  "caption": "the worry doesn't win.\nyou just see it.",                      "dur": 4, "size": 62},
        ],
    },

    # ── v21: panic — "your heart is racing" (symptom-led, framing 1) ──
    "v21_panic_racing": {
        "out": str(OUT_DIR / "gq_short_v21_panic_racing.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "your heart\nis racing",                                        "dur": 4, "size": 84},
            {"kind": "card",  "caption": "you can't\ncatch your breath",                                 "dur": 4, "size": 76},
            {"kind": "phone", "src": "RL2_breathing.png",       "caption": "box breathing",               "dur": 6},
            {"kind": "phone", "src": "RL4_exercise_open.png",   "caption": "four counts each",            "dur": 7},
            {"kind": "phone", "src": "P3_safety_plan_card.png", "caption": "if it doesn't stop",          "dur": 5},
            {"kind": "card",  "caption": "panic passes.\nyou are safe.",                                 "dur": 4, "size": 70},
        ],
    },

    # ── v22: panic — "it feels like dying" (symptom-led, framing 2) ──
    "v22_panic_dying": {
        "out": str(OUT_DIR / "gq_short_v22_panic_dying.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "panic feels\nlike dying",                                      "dur": 4, "size": 80},
            {"kind": "card",  "caption": "it isn't.\nyou aren't.",                                       "dur": 4, "size": 76},
            {"kind": "phone", "src": "RL4_exercise.png",        "caption": "breathe with this",           "dur": 7},
            {"kind": "phone", "src": "RL2b_grounding.png",      "caption": "5 things you see",            "dur": 6},
            {"kind": "phone", "src": "P3_safety_plan_card.png", "caption": "your safety plan is here",    "dur": 5},
            {"kind": "card",  "caption": "not a diagnosis.\nnot dying. just panic.",                     "dur": 4, "size": 62},
        ],
    },

    # ── v23: depression — "nothing sounds good" (symptom-led, framing 1) ──
    "v23_depression_nothing": {
        "out": str(OUT_DIR / "gq_short_v23_depression_nothing.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "nothing\nsounds good",                                         "dur": 4, "size": 82},
            {"kind": "card",  "caption": "everything\nfeels heavy",                                      "dur": 4, "size": 76},
            {"kind": "phone", "src": "M2_mood_sheet.png",       "caption": "log it anyway",               "dur": 5},
            {"kind": "phone", "src": "Q2_quest_preview.png",    "caption": "one tiny quest",              "dur": 6},
            {"kind": "phone", "src": "I1_chat_home.png",        "caption": "or just talk",                "dur": 5},
            {"kind": "card",  "caption": "small steps count.\neven the tiny ones.",                      "dur": 5, "size": 62},
        ],
    },

    # ── v24: depression — "you can't get out of bed" (symptom-led, framing 2) ──
    "v24_depression_bed": {
        "out": str(OUT_DIR / "gq_short_v24_depression_bed.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "can't get\nout of bed?",                                       "dur": 4, "size": 82},
            {"kind": "phone", "src": "M1_mood_tab.png",        "caption": "log it from here",             "dur": 5},
            {"kind": "phone", "src": "M2c_mood_submitted.png", "caption": "that counts as trying",        "dur": 6},
            {"kind": "phone", "src": "Q1_quest_tab.png",       "caption": "one quest. 90 seconds.",       "dur": 6},
            {"kind": "phone", "src": "RL2_breathing.png",      "caption": "or just breathe",              "dur": 5},
            {"kind": "card",  "caption": "not a streak.\nnot a failure.\njust a day.",                    "dur": 4, "size": 60},
        ],
    },

    # ── v25: insomnia — "3am and you can't sleep" (symptom-led, framing 1) ──
    "v25_insomnia_3am": {
        "out": str(OUT_DIR / "gq_short_v25_insomnia_3am.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "3am.\ncan't sleep.",                                           "dur": 4, "size": 84},
            {"kind": "phone", "src": "RL2_breathing.png",       "caption": "slow breathing",              "dur": 6},
            {"kind": "phone", "src": "RL4_exercise_open.png",   "caption": "in for 4. out for 4.",        "dur": 7},
            {"kind": "phone", "src": "J1_journal_empty.png",    "caption": "or write it out",             "dur": 5},
            {"kind": "phone", "src": "I1_chat_home.png",        "caption": "or just talk",                "dur": 5},
            {"kind": "card",  "caption": "the thought loop\nloses its grip.",                            "dur": 4, "size": 66},
        ],
    },

    # ── v26: insomnia — "your brain won't shut off" (symptom-led, framing 2) ──
    "v26_insomnia_brain": {
        "out": str(OUT_DIR / "gq_short_v26_insomnia_brain.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "your brain\nwon't shut off",                                   "dur": 4, "size": 80},
            {"kind": "phone", "src": "J3_entry_editor.png",     "caption": "dump every thought",          "dur": 6},
            {"kind": "phone", "src": "J1_journal_empty.png",    "caption": "blank page. no prompts.",     "dur": 5},
            {"kind": "phone", "src": "RL2b_grounding.png",      "caption": "then ground",                 "dur": 6},
            {"kind": "phone", "src": "M2_mood_sheet.png",       "caption": "name the feeling",            "dur": 5},
            {"kind": "card",  "caption": "the page holds it.\nyou sleep.",                               "dur": 4, "size": 64},
        ],
    },

    # ── v27: OCD intrusive thoughts — "the thought won't leave" (symptom-led, framing 1) ──
    "v27_ocd_intrusive": {
        "out": str(OUT_DIR / "gq_short_v27_ocd_intrusive.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "the thought\nwon't leave",                                     "dur": 4, "size": 82},
            {"kind": "card",  "caption": "it doesn't\nmean anything",                                    "dur": 4, "size": 74},
            {"kind": "phone", "src": "J3_entry_editor.png",     "caption": "write it down",               "dur": 6},
            {"kind": "phone", "src": "J1_journal_empty.png",    "caption": "see it on paper",             "dur": 5},
            {"kind": "phone", "src": "RL2b_grounding.png",      "caption": "come back to now",            "dur": 6},
            {"kind": "card",  "caption": "a thought is a thought.\nnot a truth.",                        "dur": 4, "size": 60},
        ],
    },

    # ── v28: OCD intrusive thoughts — "you're not your thoughts" (symptom-led, framing 2) ──
    "v28_ocd_not_thoughts": {
        "out": str(OUT_DIR / "gq_short_v28_ocd_not_thoughts.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "you are not\nyour thoughts",                                   "dur": 4, "size": 82},
            {"kind": "phone", "src": "I1_chat_home.png",       "caption": "say it out loud",              "dur": 6},
            {"kind": "phone", "src": "J3_entry_editor.png",    "caption": "or write it",                  "dur": 5},
            {"kind": "phone", "src": "M2_mood_sheet.png",      "caption": "name the anxiety",             "dur": 5},
            {"kind": "phone", "src": "RL4_exercise.png",       "caption": "then breathe",                 "dur": 6},
            {"kind": "card",  "caption": "intrusive ≠ true.\nintrusive ≠ you.",                          "dur": 4, "size": 62},
        ],
    },

    # ── v29: burnout — "everything is too much" (symptom-led, framing 1) ──
    "v29_burnout_too_much": {
        "out": str(OUT_DIR / "gq_short_v29_burnout_too_much.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "everything\nis too much",                                     "dur": 4, "size": 82},
            {"kind": "phone", "src": "M2_mood_sheet.png",       "caption": "log it",                      "dur": 5},
            {"kind": "phone", "src": "Q1_quest_tab.png",       "caption": "one tiny quest",              "dur": 6},
            {"kind": "phone", "src": "RL2_breathing.png",      "caption": "or just breathe",             "dur": 6},
            {"kind": "phone", "src": "J1_journal_empty.png",   "caption": "or write nothing",            "dur": 5},
            {"kind": "card",  "caption": "rest is not lazy.\nrest is the work.",                         "dur": 4, "size": 62},
        ],
    },

    # ── v30: burnout — "you're running on empty" (symptom-led, framing 2) ──
    "v30_burnout_empty": {
        "out": str(OUT_DIR / "gq_short_v30_burnout_empty.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "running\non empty?",                                           "dur": 4, "size": 82},
            {"kind": "phone", "src": "M1_mood_tab.png",        "caption": "check in",                     "dur": 5},
            {"kind": "phone", "src": "M3_low_mood_reflection.png", "caption": "see the pattern",         "dur": 6},
            {"kind": "phone", "src": "RL1_library_all.png",    "caption": "pick one thing",              "dur": 5},
            {"kind": "phone", "src": "P3_safety_plan_card.png", "caption": "and your safety plan",       "dur": 5},
            {"kind": "card",  "caption": "you don't have to\nbe okay right now.",                        "dur": 5, "size": 62},
        ],
    },

    # ── v31: perfectionism — "it has to be perfect" (symptom-led, framing 1) ──
    "v31_perfect_has_to": {
        "out": str(OUT_DIR / "gq_short_v31_perfect_has_to.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "it has to\nbe perfect",                                        "dur": 4, "size": 82},
            {"kind": "card",  "caption": "or what?",                                                     "dur": 4, "size": 78},
            {"kind": "phone", "src": "J3_entry_editor.png",     "caption": "write the fear",              "dur": 6},
            {"kind": "phone", "src": "Q2_quest_preview.png",    "caption": "do it badly. 90 seconds.",    "dur": 6},
            {"kind": "phone", "src": "M2c_mood_submitted.png",  "caption": "log how you feel after",      "dur": 5},
            {"kind": "card",  "caption": "done > perfect.\nalways.",                                     "dur": 4, "size": 68},
        ],
    },

    # ── v32: perfectionism — "you can't start until it's right" (symptom-led, framing 2) ──
    "v32_perfect_cant_start": {
        "out": str(OUT_DIR / "gq_short_v32_perfect_cant_start.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "can't start\nuntil it's right?",                               "dur": 4, "size": 80},
            {"kind": "phone", "src": "Q1_quest_tab.png",       "caption": "start wrong",                  "dur": 6},
            {"kind": "phone", "src": "Q2_quest_preview.png",   "caption": "90 seconds. badly.",           "dur": 6},
            {"kind": "phone", "src": "J1_journal_empty.png",   "caption": "write why it has to be perfect", "dur": 5},
            {"kind": "phone", "src": "I1_chat_home.png",       "caption": "or talk it through",           "dur": 5},
            {"kind": "card",  "caption": "imperfect counts.\nimperfect ships.",                          "dur": 4, "size": 62},
        ],
    },

    # ── v33: rumination — "the same thought on loop" (symptom-led, framing 1) ──
    "v33_rumination_loop": {
        "out": str(OUT_DIR / "gq_short_v33_rumination_loop.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "same thought.\non loop.",                                      "dur": 4, "size": 82},
            {"kind": "phone", "src": "J3_entry_editor.png",     "caption": "write it out",                "dur": 6},
            {"kind": "phone", "src": "J1_journal_empty.png",    "caption": "see it on paper",             "dur": 5},
            {"kind": "phone", "src": "RL2b_grounding.png",      "caption": "come back to now",            "dur": 6},
            {"kind": "phone", "src": "RL4_exercise.png",        "caption": "breathe",                     "dur": 5},
            {"kind": "card",  "caption": "the loop breaks\nwhen you see it.",                            "dur": 4, "size": 62},
        ],
    },

    # ── v34: rumination — "you can't stop replaying it" (symptom-led, framing 2) ──
    "v34_rumination_replay": {
        "out": str(OUT_DIR / "gq_short_v34_rumination_replay.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "can't stop\nreplaying it?",                                    "dur": 4, "size": 80},
            {"kind": "phone", "src": "I1_chat_home.png",       "caption": "say it once",                  "dur": 6},
            {"kind": "phone", "src": "J3_entry_editor.png",    "caption": "write it once",                "dur": 5},
            {"kind": "phone", "src": "M2_mood_sheet.png",      "caption": "name the feeling",             "dur": 5},
            {"kind": "phone", "src": "RL2_breathing.png",      "caption": "then breathe through it",      "dur": 6},
            {"kind": "card",  "caption": "replayed ≠ real.\njust loud.",                                 "dur": 4, "size": 64},
        ],
    },

    # ── v35: social anxiety — "everyone is watching" (symptom-led, framing 1) ──
    "v35_social_anxiety_watching": {
        "out": str(OUT_DIR / "gq_short_v35_social_watching.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "everyone\nis watching",                                        "dur": 4, "size": 82},
            {"kind": "card",  "caption": "they aren't.",                                                 "dur": 4, "size": 78},
            {"kind": "phone", "src": "RL2b_grounding.png",      "caption": "5 things you see",            "dur": 6},
            {"kind": "phone", "src": "RL4_exercise_open.png",   "caption": "breathe slowly",              "dur": 6},
            {"kind": "phone", "src": "J3_entry_editor.png",     "caption": "write the fear out",          "dur": 5},
            {"kind": "card",  "caption": "the room is not watching.\nyou are safe.",                      "dur": 4, "size": 60},
        ],
    },

    # ── v36: social anxiety — "you rehearse every conversation" (symptom-led, framing 2) ──
    "v36_social_anxiety_rehearse": {
        "out": str(OUT_DIR / "gq_short_v36_social_rehearse.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "rehearsing\nevery word?",                                      "dur": 4, "size": 82},
            {"kind": "phone", "src": "J1_journal_empty.png",    "caption": "write it instead",            "dur": 6},
            {"kind": "phone", "src": "M2_mood_sheet.png",       "caption": "name the anxiety",            "dur": 5},
            {"kind": "phone", "src": "RL2_breathing.png",       "caption": "breathe before you go",       "dur": 6},
            {"kind": "phone", "src": "I1_chat_home.png",        "caption": "or talk it through",          "dur": 5},
            {"kind": "card",  "caption": "you don't owe anyone\na perfect version.",                     "dur": 4, "size": 60},
        ],
    },

    # ── v37: health anxiety — "what if it's something serious" (symptom-led, framing 1) ──
    "v37_health_anxiety_serious": {
        "out": str(OUT_DIR / "gq_short_v37_health_serious.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "what if it's\nserious?",                                       "dur": 4, "size": 82},
            {"kind": "card",  "caption": "what if\nit isn't?",                                           "dur": 4, "size": 78},
            {"kind": "phone", "src": "J3_entry_editor.png",     "caption": "write the fear",              "dur": 6},
            {"kind": "phone", "src": "RL2b_grounding.png",      "caption": "come back to your body",      "dur": 6},
            {"kind": "phone", "src": "M2_mood_sheet.png",       "caption": "name the anxiety",            "dur": 5},
            {"kind": "card",  "caption": "not a diagnosis.\nsee a doctor if worried.",                   "dur": 5, "size": 58},
        ],
    },

    # ── v38: health anxiety — "you keep googling symptoms" (symptom-led, framing 2) ──
    "v38_health_anxiety_googling": {
        "out": str(OUT_DIR / "gq_short_v38_health_googling.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "stop\ngoogling.",                                              "dur": 4, "size": 84},
            {"kind": "phone", "src": "J1_journal_empty.png",    "caption": "write the worry instead",     "dur": 6},
            {"kind": "phone", "src": "RL4_exercise.png",        "caption": "breathe",                     "dur": 6},
            {"kind": "phone", "src": "M2c_mood_submitted.png",  "caption": "log the anxiety",             "dur": 5},
            {"kind": "phone", "src": "P3_safety_plan_card.png", "caption": "and your safety plan",        "dur": 5},
            {"kind": "card",  "caption": "Dr. Google is not\na real doctor.",                            "dur": 4, "size": 62},
        ],
    },

    # ── v39: mood log — "five seconds a day" (mechanic-led, framing 1) ──
    "v39_mood_five_seconds": {
        "out": str(OUT_DIR / "gq_short_v39_mood_five_seconds.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "five seconds\na day",                                          "dur": 4, "size": 82},
            {"kind": "phone", "src": "M1_mood_tab.png",        "caption": "open mood",                    "dur": 5},
            {"kind": "phone", "src": "M2_mood_sheet.png",      "caption": "pick a face",                  "dur": 5},
            {"kind": "phone", "src": "M2b_emoji_selected.png", "caption": "tap done",                     "dur": 4},
            {"kind": "phone", "src": "M2c_mood_submitted.png", "caption": "that's it",                    "dur": 6},
            {"kind": "card",  "caption": "no streak. no guilt.\njust a log.",                            "dur": 5, "size": 64},
        ],
    },

    # ── v40: mood log — "see your patterns" (mechanic-led, framing 2) ──
    "v40_mood_patterns": {
        "out": str(OUT_DIR / "gq_short_v40_mood_patterns.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "see your\npatterns",                                           "dur": 4, "size": 82},
            {"kind": "phone", "src": "M5_weekly_review_row.png", "caption": "a week of moods",           "dur": 6},
            {"kind": "phone", "src": "M5b_after_scroll.png",   "caption": "what changed?",               "dur": 6},
            {"kind": "phone", "src": "M3_low_mood_reflection.png", "caption": "what triggered it?",     "dur": 5},
            {"kind": "phone", "src": "M1_mood_tab.png",        "caption": "log again tomorrow",           "dur": 5},
            {"kind": "card",  "caption": "patterns, not streaks.\npictures, not grades.",                "dur": 4, "size": 58},
        ],
    },

    # ── v41: safety plan — "fill it when calm" (mechanic-led, framing 1) ──
    "v41_safety_fill_calm": {
        "out": str(OUT_DIR / "gq_short_v41_safety_fill_calm.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "fill it\nwhen calm",                                           "dur": 4, "size": 82},
            {"kind": "phone", "src": "P1_profile_top.png",      "caption": "open profile",               "dur": 5},
            {"kind": "phone", "src": "P3_safety_plan_card.png", "caption": "safety plan",                 "dur": 5},
            {"kind": "phone", "src": "P4_safety_contacts.png",  "caption": "add contacts",                "dur": 6},
            {"kind": "phone", "src": "P4_safety_plan_filled.png", "caption": "add what helps",           "dur": 6},
            {"kind": "card",  "caption": "find it\nwhen you're not.",                                    "dur": 5, "size": 70},
        ],
    },

    # ── v42: safety plan — "one tap to call" (mechanic-led, framing 2) ──
    "v42_safety_one_tap": {
        "out": str(OUT_DIR / "gq_short_v42_safety_one_tap.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "one tap\nto call",                                             "dur": 4, "size": 84},
            {"kind": "phone", "src": "P5_safety_contacts.png",  "caption": "your people",                 "dur": 6},
            {"kind": "phone", "src": "P4_safety_contacts.png",  "caption": "one tap",                     "dur": 5},
            {"kind": "phone", "src": "I7b_safety_legal_sheet.png", "caption": "crisis lines",            "dur": 6},
            {"kind": "phone", "src": "S8b_crisis_sheet.png",    "caption": "for your country",             "dur": 5},
            {"kind": "card",  "caption": "not buried.\nnot forgotten.\nhere.",                            "dur": 4, "size": 60},
        ],
    },

    # ── v43: quests — "90 seconds to start" (mechanic-led, framing 1) ──
    "v43_quests_90_seconds": {
        "out": str(OUT_DIR / "gq_short_v43_quests_90_seconds.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "90 seconds\nto start",                                         "dur": 4, "size": 82},
            {"kind": "phone", "src": "Q1_quest_tab.png",       "caption": "open quests",                  "dur": 5},
            {"kind": "phone", "src": "Q2_quest_preview.png",   "caption": "pick one",                     "dur": 5},
            {"kind": "phone", "src": "RL4_exercise_open.png",  "caption": "do it now",                    "dur": 7},
            {"kind": "phone", "src": "RL1_library_all.png",    "caption": "or the library",               "dur": 5},
            {"kind": "card",  "caption": "you will outgrow them.\nthat's the point.",                     "dur": 4, "size": 60},
        ],
    },

    # ── v44: quests — "outgrow them and uninstall" (mechanic-led, framing 2) ──
    "v44_quests_outgrow": {
        "out": str(OUT_DIR / "gq_short_v44_quests_outgrow.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "the goal is\nto uninstall",                                    "dur": 4, "size": 80},
            {"kind": "phone", "src": "Q1b_quest_tab_scrolled.png", "caption": "tiny quests",             "dur": 6},
            {"kind": "phone", "src": "Q2_quest_preview.png",   "caption": "CBT-flavored",                 "dur": 5},
            {"kind": "phone", "src": "RL2_breathing.png",      "caption": "breathing",                    "dur": 5},
            {"kind": "phone", "src": "RL2b_grounding.png",     "caption": "grounding",                    "dur": 5},
            {"kind": "card",  "caption": "learn the skill.\nthen delete the app.",                       "dur": 5, "size": 60},
        ],
    },

    # ── v45: journal — "blank page, no prompts" (mechanic-led, framing 1) ──
    "v45_journal_blank": {
        "out": str(OUT_DIR / "gq_short_v45_journal_blank.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "blank page.\nno prompts.",                                     "dur": 4, "size": 80},
            {"kind": "phone", "src": "J1_journal_empty.png",    "caption": "just a page",                 "dur": 5},
            {"kind": "phone", "src": "J3_entry_editor.png",     "caption": "write anything",              "dur": 6},
            {"kind": "phone", "src": "J2_chip_prefill.png",     "caption": "or tap a chip",               "dur": 5},
            {"kind": "phone", "src": "S4_anonymity_toggled.png", "caption": "anonymous. private.",        "dur": 5},
            {"kind": "card",  "caption": "no AI reads it.\nno AI summarizes it.",                        "dur": 5, "size": 60},
        ],
    },

    # ── v46: journal — "write nothing if you want" (mechanic-led, framing 2) ──
    "v46_journal_nothing": {
        "out": str(OUT_DIR / "gq_short_v46_journal_nothing.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "write nothing.\nthat's fine.",                                 "dur": 4, "size": 78},
            {"kind": "phone", "src": "J1_journal_empty.png",    "caption": "open the page",               "dur": 5},
            {"kind": "phone", "src": "M2_mood_sheet.png",       "caption": "log your mood",               "dur": 5},
            {"kind": "phone", "src": "M2c_mood_submitted.png",  "caption": "that's enough",               "dur": 6},
            {"kind": "phone", "src": "S2_export_snackbar.png",  "caption": "export when you want",        "dur": 5},
            {"kind": "card",  "caption": "the page is there.\nyou don't owe it words.",                   "dur": 5, "size": 58},
        ],
    },

    # ── v47: grounding — "5-4-3-2-1 in 60 seconds" (mechanic-led, framing 1) ──
    "v47_grounding_60_seconds": {
        "out": str(OUT_DIR / "gq_short_v47_grounding_60.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "60 seconds.\nback to now.",                                    "dur": 4, "size": 82},
            {"kind": "phone", "src": "RL1_library_all.png",    "caption": "open library",                 "dur": 4},
            {"kind": "phone", "src": "RL2b_grounding.png",     "caption": "grounding",                    "dur": 5},
            {"kind": "phone", "src": "RL4_exercise_open.png",  "caption": "5 you see",                    "dur": 5},
            {"kind": "phone", "src": "RL4_exercise.png",       "caption": "4 you touch",                  "dur": 5},
            {"kind": "card",  "caption": "3 you hear. 2 you smell. 1 you taste.",                        "dur": 7, "size": 64},
        ],
    },

    # ── v48: grounding — "when your mind races" (mechanic-led, framing 2) ──
    "v48_grounding_races": {
        "out": str(OUT_DIR / "gq_short_v48_grounding_races.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "mind racing?\ntry this.",                                      "dur": 4, "size": 80},
            {"kind": "phone", "src": "RL2b_grounding.png",     "caption": "grounding exercise",           "dur": 5},
            {"kind": "phone", "src": "RL4_exercise_open.png",  "caption": "5 things you see",             "dur": 6},
            {"kind": "phone", "src": "RL4_exercise.png",       "caption": "4 you can touch",              "dur": 5},
            {"kind": "phone", "src": "M2_mood_sheet.png",      "caption": "then log your mood",           "dur": 5},
            {"kind": "card",  "caption": "your feet on the floor.\nyou are here.",                        "dur": 5, "size": 62},
        ],
    },

    # ── v49: breathing — "box breathing in 90 seconds" (mechanic-led, framing 1) ──
    "v49_breathing_box_90": {
        "out": str(OUT_DIR / "gq_short_v49_breathing_box_90.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "90 seconds.\nbox breathing.",                                  "dur": 4, "size": 82},
            {"kind": "phone", "src": "RL2_breathing.png",      "caption": "open breathing",               "dur": 5},
            {"kind": "phone", "src": "RL4_exercise_open.png",  "caption": "in for 4",                     "dur": 6},
            {"kind": "phone", "src": "RL4_exercise.png",       "caption": "hold for 4",                   "dur": 5},
            {"kind": "phone", "src": "RL4_exercise_card.png",  "caption": "out for 4. hold for 4.",       "dur": 6},
            {"kind": "card",  "caption": "that's it.\nyou are breathing.",                               "dur": 4, "size": 68},
        ],
    },

    # ── v50: breathing — "when you can't breathe slow" (mechanic-led, framing 2) ──
    "v50_breathing_cant_slow": {
        "out": str(OUT_DIR / "gq_short_v50_breathing_cant_slow.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "can't breathe\nslow?",                                         "dur": 4, "size": 82},
            {"kind": "phone", "src": "RL2_breathing.png",      "caption": "try this",                     "dur": 5},
            {"kind": "phone", "src": "RL4_exercise_open.png",  "caption": "just follow",                  "dur": 7},
            {"kind": "phone", "src": "RL4_exercise.png",       "caption": "in. hold. out. hold.",         "dur": 6},
            {"kind": "phone", "src": "M2c_mood_submitted.png", "caption": "then log it",                  "dur": 4},
            {"kind": "card",  "caption": "your breath is always\nhere. free.",                            "dur": 4, "size": 62},
        ],
    },

    # ── v51: body-scan — "feel your feet" (mechanic-led, framing 1) ──
    "v51_body_scan_feet": {
        "out": str(OUT_DIR / "gq_short_v51_body_scan_feet.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "feel\nyour feet",                                              "dur": 4, "size": 84},
            {"kind": "card",  "caption": "on the floor.",                                                "dur": 4, "size": 78},
            {"kind": "phone", "src": "RL1_library_all.png",    "caption": "open library",                 "dur": 5},
            {"kind": "phone", "src": "RL2_breathing.png",      "caption": "breathing exercise",           "dur": 6},
            {"kind": "phone", "src": "RL4_exercise.png",       "caption": "scan up. slowly.",             "dur": 6},
            {"kind": "card",  "caption": "your body is here.\nyou are here.",                            "dur": 4, "size": 62},
        ],
    },

    # ── v52: body-scan — "where are you tight?" (mechanic-led, framing 2) ──
    "v52_body_scan_tight": {
        "out": str(OUT_DIR / "gq_short_v52_body_scan_tight.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "where are\nyou tight?",                                        "dur": 4, "size": 82},
            {"kind": "card",  "caption": "jaw. shoulders. chest.",                                       "dur": 4, "size": 72},
            {"kind": "phone", "src": "RL4_exercise_open.png",  "caption": "breathe into it",              "dur": 6},
            {"kind": "phone", "src": "RL4_exercise.png",       "caption": "let it go",                    "dur": 6},
            {"kind": "phone", "src": "M2_mood_sheet.png",      "caption": "log the tension",              "dur": 5},
            {"kind": "card",  "caption": "your body holds\nwhat your mind won't say.",                   "dur": 4, "size": 58},
        ],
    },

    # ── v53: thought record — "write the thought down" (mechanic-led, framing 1) ──
    "v53_thought_record_write": {
        "out": str(OUT_DIR / "gq_short_v53_thought_record.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "write the\nthought down",                                      "dur": 4, "size": 80},
            {"kind": "phone", "src": "J1_journal_empty.png",    "caption": "blank page",                  "dur": 5},
            {"kind": "phone", "src": "J3_entry_editor.png",     "caption": "exactly as it is",            "dur": 6},
            {"kind": "phone", "src": "J2_chip_prefill.png",     "caption": "or tap a chip",               "dur": 5},
            {"kind": "phone", "src": "M2_mood_sheet.png",       "caption": "name the feeling",            "dur": 5},
            {"kind": "card",  "caption": "a thought on paper\nis smaller than in your head.",            "dur": 5, "size": 58},
        ],
    },

    # ── v54: thought record — "is it true or just loud?" (mechanic-led, framing 2) ──
    "v54_thought_record_true": {
        "out": str(OUT_DIR / "gq_short_v54_thought_true.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "is it true?\nor just loud?",                                   "dur": 4, "size": 80},
            {"kind": "phone", "src": "J3_entry_editor.png",     "caption": "write it",                    "dur": 5},
            {"kind": "phone", "src": "J1_journal_empty.png",    "caption": "then ask",                    "dur": 5},
            {"kind": "phone", "src": "I1_chat_home.png",        "caption": "or talk it through",          "dur": 6},
            {"kind": "phone", "src": "RL2b_grounding.png",      "caption": "then ground",                 "dur": 5},
            {"kind": "card",  "caption": "loud ≠ true.\nrepeated ≠ real.",                               "dur": 5, "size": 62},
        ],
    },

    # ── v55: behavioral activation — "do one small thing" (mechanic-led, framing 1) ──
    "v55_behavioral_one_thing": {
        "out": str(OUT_DIR / "gq_short_v55_behavioral_one.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "do one\nsmall thing",                                          "dur": 4, "size": 82},
            {"kind": "phone", "src": "Q1_quest_tab.png",       "caption": "open quests",                  "dur": 5},
            {"kind": "phone", "src": "Q2_quest_preview.png",   "caption": "90 seconds",                   "dur": 6},
            {"kind": "phone", "src": "RL4_exercise_open.png",  "caption": "just this one",                "dur": 6},
            {"kind": "phone", "src": "M2c_mood_submitted.png", "caption": "log how you feel after",       "dur": 5},
            {"kind": "card",  "caption": "action before\nmotivation. always.",                           "dur": 4, "size": 62},
        ],
    },

    # ── v56: behavioral activation — "action before motivation" (mechanic-led, framing 2) ──
    "v56_behavioral_action": {
        "out": str(OUT_DIR / "gq_short_v56_behavioral_action.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "you don't wait\nfor motivation",                               "dur": 4, "size": 78},
            {"kind": "card",  "caption": "you act first.",                                               "dur": 4, "size": 78},
            {"kind": "phone", "src": "Q2_quest_preview.png",   "caption": "one quest",                    "dur": 5},
            {"kind": "phone", "src": "RL4_exercise.png",       "caption": "do it badly",                  "dur": 6},
            {"kind": "phone", "src": "M2_mood_sheet.png",      "caption": "then check in",                "dur": 5},
            {"kind": "card",  "caption": "the feeling follows\nthe action. not the reverse.",            "dur": 5, "size": 56},
        ],
    },

    # ── v57: sleep hygiene — "before bed routine" (mechanic-led, framing 1) ──
    "v57_sleep_before_bed": {
        "out": str(OUT_DIR / "gq_short_v57_sleep_before_bed.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "before bed:\ntry this",                                        "dur": 4, "size": 80},
            {"kind": "phone", "src": "J1_journal_empty.png",    "caption": "write the day out",           "dur": 6},
            {"kind": "phone", "src": "RL2_breathing.png",      "caption": "then breathe",                 "dur": 6},
            {"kind": "phone", "src": "RL4_exercise.png",       "caption": "slow. four counts.",           "dur": 5},
            {"kind": "phone", "src": "M2_mood_sheet.png",      "caption": "log your mood",                "dur": 5},
            {"kind": "card",  "caption": "the page holds the day.\nyou sleep.",                          "dur": 4, "size": 60},
        ],
    },

    # ── v58: sleep hygiene — "can't sleep? try this" (mechanic-led, framing 2) ──
    "v58_sleep_cant": {
        "out": str(OUT_DIR / "gq_short_v58_sleep_cant.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "can't sleep?\ntry this.",                                      "dur": 4, "size": 82},
            {"kind": "phone", "src": "J3_entry_editor.png",     "caption": "dump every thought",          "dur": 6},
            {"kind": "phone", "src": "RL2b_grounding.png",      "caption": "then ground",                 "dur": 5},
            {"kind": "phone", "src": "RL4_exercise_open.png",   "caption": "breathe slow",                "dur": 7},
            {"kind": "phone", "src": "M2c_mood_submitted.png",  "caption": "log it",                      "dur": 4},
            {"kind": "card",  "caption": "the loop breaks.\nsleep comes.",                               "dur": 4, "size": 66},
        ],
    },

    # ── v59: anti-pattern — "no ads, no upsell" ──
    "v59_no_ads": {
        "out": str(OUT_DIR / "gq_short_v59_no_ads.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "no ads.",                                                     "dur": 4, "size": 90},
            {"kind": "card",  "caption": "no upsell.",                                                  "dur": 4, "size": 90},
            {"kind": "card",  "caption": "no paywall.",                                                 "dur": 4, "size": 90},
            {"kind": "phone", "src": "S1_settings_top.png",     "caption": "no premium tier",             "dur": 5},
            {"kind": "phone", "src": "S3_delete_account_sheet.png", "caption": "no lock-in",             "dur": 6},
            {"kind": "card",  "caption": "free. 18+. that's it.",                                       "dur": 5, "size": 72},
        ],
    },

    # ── v60: anti-pattern — "no notifications spam" ──
    "v60_no_notifications": {
        "out": str(OUT_DIR / "gq_short_v60_no_notifications.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "we don't\nspam you",                                          "dur": 4, "size": 82},
            {"kind": "phone", "src": "S1b_settings_notifications.png", "caption": "you choose",         "dur": 6},
            {"kind": "phone", "src": "S5_notification_detail.png", "caption": "what. when. off.",       "dur": 6},
            {"kind": "phone", "src": "S1_settings_default.png", "caption": "default: quiet",            "dur": 5},
            {"kind": "phone", "src": "M2c_mood_submitted.png",  "caption": "no streaks to remind you",   "dur": 5},
            {"kind": "card",  "caption": "your phone is loud enough.\nwe aren't adding to it.",         "dur": 4, "size": 56},
        ],
    },

    # ── v61: anti-pattern — "no AI eavesdropping on your journal" ──
    "v61_no_ai_eavesdropping": {
        "out": str(OUT_DIR / "gq_short_v61_no_ai_eavesdrop.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "no AI reads\nyour journal",                                    "dur": 4, "size": 80},
            {"kind": "phone", "src": "J1_journal_empty.png",    "caption": "just a page",                 "dur": 5},
            {"kind": "phone", "src": "J3_entry_editor.png",     "caption": "your words",                  "dur": 6},
            {"kind": "phone", "src": "S4_anonymity_toggled.png", "caption": "anonymous mode",             "dur": 5},
            {"kind": "phone", "src": "S2_export_snackbar.png",  "caption": "export. delete. leave.",      "dur": 5},
            {"kind": "card",  "caption": "no AI summarizes it.\nno AI trains on it.\njust yours.",       "dur": 5, "size": 56},
        ],
    },

    # ── v62: anti-pattern — "no diagnosis" ──
    "v62_no_diagnosis": {
        "out": str(OUT_DIR / "gq_short_v62_no_diagnosis.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "we don't\ndiagnose you",                                      "dur": 4, "size": 80},
            {"kind": "phone", "src": "M4_clinical_assessment_entry.png", "caption": "PHQ-9. GAD-7.",     "dur": 6},
            {"kind": "phone", "src": "CA4_result_reveal.png",  "caption": "a score. not a label.",       "dur": 6},
            {"kind": "phone", "src": "P3_safety_plan_card.png", "caption": "and a safety plan",          "dur": 5},
            {"kind": "phone", "src": "I7b_safety_legal_sheet.png", "caption": "see a professional",      "dur": 5},
            {"kind": "card",  "caption": "a starting point.\nnot a diagnosis.",                          "dur": 4, "size": 62},
        ],
    },

    # ── v63: anti-pattern — "no streaks, no guilt" ──
    "v63_no_streaks": {
        "out": str(OUT_DIR / "gq_short_v63_no_streaks.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "no streaks.",                                                 "dur": 4, "size": 90},
            {"kind": "card",  "caption": "no guilt.",                                                   "dur": 4, "size": 90},
            {"kind": "phone", "src": "M2c_mood_submitted.png", "caption": "log when you want",          "dur": 5},
            {"kind": "phone", "src": "M5_weekly_review_row.png", "caption": "see your week",           "dur": 6},
            {"kind": "phone", "src": "M3_low_mood_reflection.png", "caption": "missed a day? fine.",  "dur": 5},
            {"kind": "card",  "caption": "you don't owe an app\nconsistency.",                          "dur": 5, "size": 58},
        ],
    },

    # ── v64: anti-pattern — "not social media" ──
    "v64_not_social_media": {
        "out": str(OUT_DIR / "gq_short_v64_not_social.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "no feed.",                                                    "dur": 4, "size": 90},
            {"kind": "card",  "caption": "no likes.",                                                   "dur": 4, "size": 90},
            {"kind": "phone", "src": "X1d_community.png",      "caption": "a community. slow.",          "dur": 5},
            {"kind": "phone", "src": "X_community_tab.png",    "caption": "curated. not algorithmic.",   "dur": 6},
            {"kind": "phone", "src": "I1_chat_home.png",       "caption": "just you and your mood",      "dur": 5},
            {"kind": "card",  "caption": "no doomscroll.\nno algorithm to fight.",                       "dur": 5, "size": 58},
        ],
    },

    # ── v65: anti-pattern — "not a therapist" (reprise) ──
    "v65_not_a_therapist": {
        "out": str(OUT_DIR / "gq_short_v65_not_therapist.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "we are not\na therapist",                                     "dur": 4, "size": 80},
            {"kind": "phone", "src": "I1_chat_home.png",       "caption": "we are a quiet chat",         "dur": 5},
            {"kind": "phone", "src": "I7b_safety_legal_sheet.png", "caption": "we take disclosures seriously", "dur": 6},
            {"kind": "phone", "src": "P3_safety_plan_card.png", "caption": "safety plan. crisis lines.", "dur": 5},
            {"kind": "phone", "src": "S8b_crisis_sheet.png",    "caption": "real resources",             "dur": 5},
            {"kind": "card",  "caption": "not a replacement.\na bridge.\nfree.",                         "dur": 5, "size": 58},
        ],
    },

    # ── v66: anti-pattern — "no tracking" ──
    "v66_no_tracking": {
        "out": str(OUT_DIR / "gq_short_v66_no_tracking.mp4"),
        "scenes": [
            {"kind": "card",  "caption": "no tracking.",                                                "dur": 4, "size": 90},
            {"kind": "phone", "src": "S1_settings_top.png",     "caption": "no analytics on you",        "dur": 5},
            {"kind": "phone", "src": "S4_anonymity_toggled.png", "caption": "anonymous mode",            "dur": 5},
            {"kind": "phone", "src": "S2_export_snackbar.png",  "caption": "your data. exportable.",     "dur": 6},
            {"kind": "phone", "src": "S3_delete_account_sheet.png", "caption": "deletable.",            "dur": 5},
            {"kind": "card",  "caption": "your data is yours.\nwe mean it.",                            "dur": 5, "size": 62},
        ],
    },
}


def render_one(name: str) -> dict:
    cfg = CATALOG[name]
    tmpfile = OUT_DIR / f"_{name}_config.json"
    tmpfile.write_text(json.dumps(cfg))
    print(f"\n=== rendering {name} -> {cfg['out']} ===")
    result = subprocess.run(
        ["python3", str(RENDER), "--config", str(tmpfile)],
        capture_output=True, text=True, check=True,
    )
    print(result.stdout, end="")
    tmpfile.unlink()
    return {"name": name, "out": cfg["out"]}


def main() -> None:
    if len(sys.argv) > 1:
        names = sys.argv[1:]
    else:
        names = list(CATALOG.keys())
    # Skip already-shipped/scheduled by default (v1-v6) — pass explicitly to re-render.
    SHIPPED = {"v1_what_it_is", "v2_safety_plan", "v3_mood_no_streaks",
               "v4_tiny_quests", "v5_not_an_ai_therapist", "v6_free_beta"}
    if len(sys.argv) == 1:
        names = [n for n in names if n not in SHIPPED]

    results = []
    for n in names:
        if n not in CATALOG:
            print(f"unknown: {n}", file=sys.stderr); continue
        results.append(render_one(n))

    print("\n=== summary ===")
    for r in results:
        print(f"  {r['name']:30s} -> {r['out']}")


if __name__ == "__main__":
    main()
