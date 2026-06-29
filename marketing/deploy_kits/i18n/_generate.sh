#!/usr/bin/env bash
# Generates 65 i18n deploy kit files (5 langs x 13 assets)
# Bash 3.2 compatible (no associative arrays)
set -eo pipefail

OUT="/Users/lokeshgarg/gentlequest/marketing/deploy_kits/i18n"

ARTICLES="anxiety-app-no-ads breathing-exercise-app-free cbt-app-free depression-app-no-ads free-mental-health-app-no-ads grounding-exercise-app journal-app-private-no-ai mental-health-app-no-subscription mood-tracker-no-streaks safety-plan-app"

art_title() {
  case "$1" in
    anxiety-app-no-ads) echo "Anxiety App With No Ads: A Calmer, Distraction-Free Option" ;;
    breathing-exercise-app-free) echo "Breathing Exercise App Free: No-Cost Tools to Slow down and Calm" ;;
    cbt-app-free) echo "CBT App Free: No-Cost Tools for Cognitive Behavioral Skills" ;;
    depression-app-no-ads) echo "Depression App With No Ads: Quiet Support Without the Sell" ;;
    free-mental-health-app-no-ads) echo "Free Mental Health App No Ads: Why Ad-Free Should Be the Default" ;;
    grounding-exercise-app) echo "Grounding Exercise App: Tools to Come Back to the Present" ;;
    journal-app-private-no-ai) echo "Journal App That's Private and No AI: Your Words Stay Yours" ;;
    mental-health-app-no-subscription) echo "Mental Health App No Subscription: Tools That Don't Recurringly Charge You" ;;
    mood-tracker-no-streaks) echo "Mood Tracker With No Streaks: Track How You Feel Without the Guilt" ;;
    safety-plan-app) echo "Safety Plan App: A Calm Tool for Your Hardest Moments" ;;
  esac
}

lang_name() {
  case "$1" in
    hi) echo "Hindi" ;;
    es) echo "Spanish" ;;
    pt-BR) echo "Brazilian Portuguese" ;;
    id) echo "Indonesian" ;;
    tl) echo "Tagalog (Filipino)" ;;
  esac
}

lang_url() {
  case "$1" in
    hi) echo "https://gentlequest.app/hi" ;;
    es) echo "https://gentlequest.app/es" ;;
    pt-BR) echo "https://gentlequest.app/pt-BR" ;;
    id) echo "https://gentlequest.app/id" ;;
    tl) echo "https://gentlequest.app/tl" ;;
  esac
}

culture_notes() {
  case "$1" in
    hi) cat <<'EOF'
- Hindi uses circumlocutions for "depression" (उदासी का भाव, मनः मंदता) due to stigma around clinical terms
- Mental health is still taboo in many Hindi-speaking regions; soften clinical language and emphasize "wellbeing" (कल्याण) framing
- Devanagari script; ensure font rendering on all target platforms
- Formal register (आप) is safer than informal (तू) for a wellness app addressing adults
- English loanwords (मूड, स्ट्रीक, जर्नल) are acceptable and common in urban Hindi audiences
- Crisis hotline line must be swapped to an India-specific number (e.g., iCall 9152987821) before publish
EOF
;;
    es) cat <<'EOF'
- "Depresión" and "ansiedad" are clinically accepted and widely understood; no need for circumlocution
- Decide Latin American vs. Peninsular Spanish register — current translation leans neutral/LatAm; keep "tú" informal, avoid "vosotros"
- "Salud mental" is the standard term; avoid colloquialisms that vary by country (e.g., "depresión" is universal but slang for sadness is not)
- Crisis hotline line must be regionalized per target country (e.g., México SAPTEL 55-5259-8121, Argentina 135) before publish
- "18+" and brand name "GentleQuest" stay in English
EOF
;;
    pt-BR) cat <<'EOF'
- "Depressão" and "ansiedade" are clinically accepted in Brazilian Portuguese; no circumlocution needed
- Use Brazilian Portuguese (pt-BR) register exclusively — avoid European Portuguese forms (e.g., "você" not "tu" for informal, "celular" not "telemóvel")
- Informal, warm tone is standard in BR wellness marketing; "você" is the safe second-person
- Mental health awareness is growing in Brazil; destigmatized language is fine but keep supportive framing
- Crisis hotline line must be swapped to CVV 188 (Brazil) before publish
- "18+" and brand name "GentleQuest" stay in English
EOF
;;
    id) cat <<'EOF'
- "Depresi" is used in Indonesian but stigma persists; pair with softer framing like "kesehatan mental" (mental health) and "kesejahteraan" (wellbeing)
- Bahasa Indonesia is the formal standard; avoid regional dialects (Javanese/Sundanese) for a national audience
- Mental health terminology is still evolving in Indonesian — English loanwords (mood, journal, streak) are common and acceptable
- Formal register is appropriate; Indonesian audiences expect polite, professional wellness tone
- Crisis hotline line must be swapped to an Indonesia-specific service (e.g., Into The Light Indonesia / Yayasan Pulih) before publish
- "18+" and brand name "GentleQuest" stay in English
EOF
;;
    tl) cat <<'EOF'
- Tagalog/Filipino commonly code-switches with English; keeping "depression" and "anxiety" in English is natural and acceptable
- Mental health stigma exists but is decreasing; "kalusugang pangkaisipan" is the formal term, though English "mental health" is more widely used
- Use conversational Filipino register; "ikaw" / "mo" for direct address is appropriate and warm
- English loanwords (mood, journal, streak, app) are standard in Filipino digital contexts — do not force native equivalents
- Crisis hotline line must be swapped to a Philippines-specific service (e.g., NCMH Crisis Hotline 0917-899-8727) before publish
- "18+" and brand name "GentleQuest" stay in English
EOF
;;
  esac
}

asset_source_desc() {
  case "$1" in
    landing_hero)
      echo "marketing/landing_hero.md — the English landing page hero headline and subhead (free, private, no ads, 18+; talk, mood log, safety plan, small quests, no streaks; iOS/Android/Web; your data is yours)"
      ;;
    app_store_long_desc)
      echo "marketing/app_store_long_desc.md — the English App Store / Play Store long-form description (free private companion, chat, mood log, safety plan, quests, journal no-AI, data export, no ads/upsell/paywall/tracking/streaks, 18+, not a diagnosis)"
      ;;
    what_is)
      echo "marketing/what_is.md — the English 'What is GentleQuest?' short definition (free private mental-health app for adults; talk, mood log, safety plan, small quests; no ads, no streaks, no tracking)"
      ;;
  esac
}

asset_label() {
  case "$1" in
    landing_hero) echo "Landing page hero text" ;;
    app_store_long_desc) echo "App Store / Play Store long description" ;;
    what_is) echo "'What is GentleQuest?' definition page" ;;
  esac
}

write_nonarticle() {
  local lang="$1" asset="$2"
  local name; name=$(lang_name "$lang")
  local url; url=$(lang_url "$lang")
  local kitname="${lang}_${asset}"
  local transpath="marketing/i18n/${lang}/${asset}.md"
  local srcdesc; srcdesc=$(asset_source_desc "$asset")
  local assetlabel; assetlabel=$(asset_label "$asset")

  cat > "${OUT}/${kitname}.md" <<EOF
# Deploy Kit: ${lang} — ${asset}

## Source
- **Translated file:** ${transpath}
- **English source:** ${srcdesc}

## Target
- **Language:** ${name} (${lang})
- **Asset type:** ${assetlabel}
- **Target URL:** ${url} (or https://gentlequest.app with hreflang)

## Culture notes (for per-language editor)
$(culture_notes "$lang")

## Publish checklist
- [ ] Translation reviewed by native speaker
- [ ] Culture notes addressed
- [ ] Uploaded to CMS with hreflang tag
- [ ] Links verified (iOS/Android/Web unchanged)
- [ ] "18+" and "GentleQuest" kept as-is
EOF
  echo "wrote ${kitname}.md"
}

write_article() {
  local lang="$1" slug="$2"
  local name; name=$(lang_name "$lang")
  local url; url=$(lang_url "$lang")
  local title; title=$(art_title "$slug")
  local kitname="${lang}_article_${slug}"
  local transpath="marketing/i18n/${lang}/articles/${slug}.md"
  local srcpath="marketing/seo/articles/${slug}.md"

  cat > "${OUT}/${kitname}.md" <<EOF
# Deploy Kit: ${lang} — article: ${slug}

## Source
- **Translated file:** ${transpath}
- **English source:** ${srcpath} — "${title}"
- **Source article:** marketing/seo/articles/${slug}.md

## Target
- **Language:** ${name} (${lang})
- **Asset type:** SEO article (translated)
- **Target URL:** ${url}/blog/${slug} (or https://gentlequest.app/blog/${slug} with hreflang)

## Internal links
- iOS — https://apps.apple.com/app/gentlequest/id6756537464
- Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
- Web — https://gentlequest.app

## Culture notes (for per-language editor)
$(culture_notes "$lang")

## Publish checklist
- [ ] Translation reviewed by native speaker
- [ ] Culture notes addressed
- [ ] Uploaded to CMS with hreflang tag
- [ ] Internal links verified (iOS/Android/Web unchanged)
- [ ] "18+" and "GentleQuest" kept as-is
- [ ] Frontmatter target_keyword kept in English for SEO parity
- [ ] Crisis hotline / professional-care disclaimer localized to target region
EOF
  echo "wrote ${kitname}.md"
}

# ---- Generate all ----
for lang in hi es pt-BR id tl; do
  write_nonarticle "$lang" "landing_hero"
  write_nonarticle "$lang" "app_store_long_desc"
  write_nonarticle "$lang" "what_is"
  for slug in $ARTICLES; do
    write_article "$lang" "$slug"
  done
done

echo "----"
ls -1 "$OUT" | grep -c '\.md$'
