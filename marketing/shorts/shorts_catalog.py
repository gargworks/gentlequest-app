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
