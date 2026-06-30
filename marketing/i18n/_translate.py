#!/usr/bin/env python3
"""Translation engine for i18n articles. Reads English sources, applies translations."""
import os, re, sys

BASE = "os.path.dirname(os.path.abspath(__file__))"
SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "seo", "articles")

URLS = "- iOS — https://apps.apple.com/app/gentlequest/id6756537464\n- Android — https://play.google.com/store/apps/details?id=com.gentlequest.app\n- Web — https://gentlequest.app"

# Load the base script for common sections
exec(open(os.path.join(BASE, "_gen_all.py")).read())

# Translation dictionaries: {lang: {english_phrase: translation}}
# Applied longest-first to avoid partial matches

# We'll build these from data files
TRANS = {}

# ============================================================
# ARTICLE-SPECIFIC TRANSLATIONS
# Format: (lang, article_slug) -> (title, [tags], body_text)
# body_text excludes the GQ and Scope sections (added automatically)
# ============================================================

ARTICLES = {}

# Load translation data from JSON files
for lang in ["hi","es","pt-BR","id","tl","ar","vi","tr","fr","de"]:
    data_file = os.path.join(BASE, f"_data_{lang.replace('-','_')}.json")
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            ARTICLES[lang] = json.load(f)

import json

P1_ARTICLES = [
    "anxiety-in-students","anxiety-in-new-parents","anxiety-in-caregivers",
    "anxiety-in-healthcare-workers","anxiety-in-founders",
    "depression-in-students","depression-in-new-parents","depression-in-caregivers",
    "depression-in-healthcare-workers","depression-in-shift-workers",
    "box-breathing-step-by-step","5-4-3-2-1-grounding-step-by-step",
    "thought-record-step-by-step","behavioral-activation-step-by-step",
    "progressive-muscle-relaxation-step-by-step",
    "phq-9-explained","gad-7-explained","pcl-5-explained","audit-explained","ace-explained",
    "dass-21-explained","k10-explained","who-5-explained","pss-explained","isi-explained",
    "gentlequest-vs-calm-detailed","gentlequest-vs-headspace-detailed",
    "gentlequest-vs-woebot-detailed","gentlequest-vs-wysa-detailed","gentlequest-vs-finch-detailed",
    "free-anxiety-resources","free-depression-resources","free-panic-attack-resources",
    "free-insomnia-resources","free-ocd-resources","free-burnout-resources",
    "free-resources-for-students","free-resources-for-new-parents",
    "free-resources-for-caregivers","free-resources-for-healthcare-workers",
]

P2_ARTICLES = [
    "anxiety-app-no-ads","depression-app-no-ads","mood-tracker-no-streaks",
    "journal-app-private-no-ai","safety-plan-app","grounding-exercise-app",
    "breathing-exercise-app-free","cbt-app-free","free-mental-health-app-no-ads",
    "mental-health-app-no-subscription","anxiety-in-students","depression-in-new-parents",
    "box-breathing-step-by-step","5-4-3-2-1-grounding-step-by-step",
    "phq-9-explained","gad-7-explained","free-anxiety-resources",
    "free-depression-resources","free-resources-for-students",
    "what-to-do-when-you-cant-afford-therapy",
]

EXISTING_LANGS = ["hi","es","pt-BR","id","tl"]
NEW_LANGS = ["ar","vi","tr","fr","de"]

def process():
    # Part 1: 40 articles x 5 existing languages
    for lang in EXISTING_LANGS:
        if lang not in ARTICLES:
            print(f"WARNING: No data for {lang}")
            continue
        for slug in P1_ARTICLES:
            if slug not in ARTICLES[lang]:
                print(f"WARNING: No {lang} translation for {slug}")
                continue
            art = ARTICLES[lang][slug]
            emit(lang, "articles", slug + ".md", art["title"], art["target_keyword"], art["tags"], art["body"])
    
    # Part 2: 20 articles + 3 base files x 5 new languages
    for lang in NEW_LANGS:
        if lang not in ARTICLES:
            print(f"WARNING: No data for {lang}")
            continue
        for slug in P2_ARTICLES:
            if slug not in ARTICLES[lang]:
                print(f"WARNING: No {lang} translation for {slug}")
                continue
            art = ARTICLES[lang][slug]
            emit(lang, "articles", slug + ".md", art["title"], art["target_keyword"], art["tags"], art["body"])
        # Base files
        for bf in ["landing_hero", "app_store_long_desc", "what_is"]:
            if bf in ARTICLES[lang]:
                content = ARTICLES[lang][bf]["body"]
                wf(lang, None, bf + ".md", content)
                global count
                count += 1
    
    print(f"\nTotal files written: {count}")

if __name__ == "__main__":
    process()
