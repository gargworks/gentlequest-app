#!/usr/bin/env python3
"""Generate 315 translated article files for i18n."""
import os, sys

BASE = "/Users/lokeshgarg/gentlequest/marketing/i18n"

URLS = """- iOS — https://apps.apple.com/app/gentlequest/id6756537464
- Android — https://play.google.com/store/apps/details?id=com.gentlequest.app
- Web — https://gentlequest.app"""

GQ = {}
SCOPE = {}

GQ["hi"] = """## GentleQuest कहाँ फिट बैठता है

GentleQuest एक शांत, निजी ऐप में मूड चेक-इन, ग्राउंडिंग उपकरण, जर्नलिंग और सत्यापित स्क्रीनिंग प्रश्नावली देता है — कोई विज्ञापन नहीं, कोई स्ट्रीक नहीं, कोई सदस्यता नहीं, कोई खाता आवश्यक नहीं। आपका डेटा आपके डिवाइस पर रहता है। यह एक छोटा, विश्वसनीय साथी बनने के लिए डिज़ाइन किया गया है।

{urls}"""

GQ["es"] = """## Dónde encaja GentleQuest

GentleQuest ofrece control de estado de ánimo, herramientas de conexión a tierra, diario y cuestionarios de cribado validados en una aplicación tranquila y privada — sin anuncios, sin rachas, sin suscripción, sin cuenta requerida. Tus datos se quedan en tu dispositivo. Está diseñado para ser un compañero pequeño y fiable.

{urls}"""

GQ["pt-BR"] = """## Onde o GentleQuest se encaixa

O GentleQuest oferece check-ins de humor, ferramentas de ancoragem, diário e questionários de triagem validados em um aplicativo tranquilo e privado — sem anúncios, sem sequências, sem assinatura, sem conta necessária. Seus dados ficam no seu dispositivo.

{urls}"""

GQ["id"] = """## Di mana GentleQuest cocok

GentleQuest menawarkan check-in suasana hati, alat penjangkaran, jurnal, dan kuesioner skrining tervalidasi dalam satu aplikasi yang tenang dan privat — tanpa iklan, tanpa rentetan, tanpa langganan, tanpa akun. Data Anda tetap di perangkat Anda.

{urls}"""

GQ["tl"] = """## Saan angkop ang GentleQuest

Nag-aalok ang GentleQuest ng mood check-ins, grounding tools, journaling, at validated screening questionnaires sa isang tahimik at pribadong app — walang ad, walang streak, walang subscription, walang account. Mananatili ang iyong data sa iyong device.

{urls}"""

GQ["ar"] = """## أين يأتي GentleQuest

يقدم GentleQuest تسجيلات المزاج وأدوات التأريض واليوميات واستبيانات الفحص الموثقة في تطبيق هادئ وخاص — بدون إعلانات، بدون سلاسل، بدون اشتراك، بدون حساب. تبقى بياناتك على جهازك.

{urls}"""

GQ["vi"] = """## Nơi GentleQuest phù hợp

GentleQuest cung cấp ghi nhận tâm trạng, công cụ nối đất, nhật ký và bảng câu hỏi sàng lọc đã xác thực trong một ứng dụng yên tĩnh và riêng tư — không quảng cáo, không chuỗi ngày, không đăng ký, không cần tài khoản. Dữ liệu của bạn ở trên thiết bị của bạn.

{urls}"""

GQ["tr"] = """## GentleQuest Nerede İşe Yarar

GentleQuest, sakin ve özel bir uygulamada ruh hali kontrolü, topraklama araçları, günlük ve doğrulanmış tarama anketleri sunar — reklamsız, seri yapısız, aboneliksiz, hesap gerektirmeden. Verileriniz cihazınızda kalır.

{urls}"""

GQ["fr"] = """## Où GentleQuest intervient

GentleQuest propose des suivis de l'humeur, des outils d'ancrage, un journal et des questionnaires de dépistage validés dans une application calme et privée — sans publicités, sans séries, sans abonnement, sans compte requis. Vos données restent sur votre appareil.

{urls}"""

GQ["de"] = """## Wo GentleQuest passt

GentleQuest bietet Stimmungs-Check-ins, Erdungswerkzeuge, Journaling und validierte Screening-Fragebögen in einer ruhigen, privaten App — keine Werbung, keine Serien, kein Abo, kein Konto erforderlich. Ihre Daten bleiben auf Ihrem Gerät.

{urls}"""

SCOPE["hi"] = "## दायरे के बारे में एक नोट\n\nयह लेख निदान नहीं है; यदि आप संघर्ष कर रहे हैं, तो किसी पेशेवर से मिलें।"
SCOPE["es"] = "## Una nota sobre el alcance\n\nEste artículo no es un diagnóstico; si estás pasando por un momento difícil, consulta a un profesional."
SCOPE["pt-BR"] = "## Uma nota sobre o escopo\n\nEste artigo não é um diagnóstico; se você está passando por dificuldades, consulte um profissional."
SCOPE["id"] = "## Catatan tentang ruang lingkup\n\nArtikel ini bukan diagnosis; jika Anda sedang berjuang, temui profesional."
SCOPE["tl"] = "## Isang paalala tungkol sa saklaw\n\nHindi ito diagnosis; kung nakikipagbaka ka, kumunsulta sa propesyonal."
SCOPE["ar"] = "## ملاحظة حول النطاق\n\nهذه المقالة ليست تشخيصًا؛ إذا كنت تعاني، استشر أحد المتخصصين."
SCOPE["vi"] = "## Lưu ý về phạm vi\n\nBài viết này không phải là chẩn đoán; nếu bạn đang gặp khó khăn, hãy gặp chuyên gia."
SCOPE["tr"] = "## Kapsam notu\n\nBu makale bir teşhis değildir; zorlanıyorsanız bir uzmana görünün."
SCOPE["fr"] = "## Une note sur la portée\n\nCet article n'est pas un diagnostic ; si vous traversez des difficultés, consultez un professionnel."
SCOPE["de"] = "## Ein Hinweis zum Geltungsbereich\n\nDieser Artikel ist keine Diagnose; wenn Sie zu kämpfen haben, wenden Sie sich an einen Fachmann."

def gq(lang):
    return GQ[lang].format(urls=URLS)

def wf(lang, subdir, fname, content):
    d = os.path.join(BASE, lang, subdir) if subdir else os.path.join(BASE, lang)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, fname)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content.strip() + "\n")
    return p

count = 0
def emit(lang, subdir, fname, body, frontmatter):
    global count
    content = frontmatter + "\n\n" + body
    wf(lang, subdir, fname, content)
    count += 1

# Articles list for Part 1 (40 per existing lang, items 11-50)
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

# Articles list for Part 2 (20 per new lang)
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

import json

# ── Load translation data files ──────────────────────────────────────
TRANSLATIONS = {}
for lang in EXISTING_LANGS + NEW_LANGS:
    path = os.path.join(BASE, f"_data_{lang}.json")
    with open(path, encoding="utf-8") as f:
        TRANSLATIONS[lang] = json.load(f)

# ── Helpers ──────────────────────────────────────────────────────────
def make_frontmatter(entry):
    """Build YAML frontmatter from a data entry."""
    title = entry.get("title", "")
    kw = entry.get("target_keyword", "")
    tags = entry.get("tags", [])
    tag_str = ", ".join(f'"{t}"' for t in tags)
    fm = f'---\ntitle: "{title}"\ntarget_keyword: "{kw}"\ntags: [{tag_str}]\n---'
    return fm

def generate_article(lang, slug):
    """Generate one article .md file from data."""
    data = TRANSLATIONS[lang]
    if slug not in data:
        print(f"  WARNING: '{slug}' not found in _data_{lang}.json — skipping")
        return False
    entry = data[slug]
    fm = make_frontmatter(entry)
    body = entry["body"].strip()
    # Append GQ section and scope note
    body += "\n\n" + gq(lang) + "\n\n" + SCOPE[lang]
    emit(lang, "articles", slug + ".md", body, fm)
    return True

def generate_base_file(lang, key):
    """Generate a base file (landing_hero, app_store_long_desc, what_is)."""
    data = TRANSLATIONS[lang]
    if key not in data:
        print(f"  WARNING: '{key}' not found in _data_{lang}.json — skipping")
        return False
    entry = data[key]
    body = entry["body"].strip()
    # Base files already have frontmatter in the body
    wf(lang, "", key + ".md", body)
    global count
    count += 1
    return True

# ── Generate existing-language articles (P1: 40 per lang = 200) ─────
print("=== Generating existing-language P1 articles ===")
for lang in EXISTING_LANGS:
    print(f"\n[{lang}] Generating {len(P1_ARTICLES)} articles...")
    for slug in P1_ARTICLES:
        generate_article(lang, slug)
print(f"\nExisting-language articles written: {count}")

# ── Generate new-language articles + base files (P2: 20+3 per lang = 115) ─
p2_count_start = count
print("\n=== Generating new-language P2 articles + base files ===")
BASE_FILES = ["landing_hero", "app_store_long_desc", "what_is"]
for lang in NEW_LANGS:
    print(f"\n[{lang}] Generating {len(P2_ARTICLES)} articles + {len(BASE_FILES)} base files...")
    for slug in P2_ARTICLES:
        generate_article(lang, slug)
    for key in BASE_FILES:
        generate_base_file(lang, key)

p2_total = count - p2_count_start
print(f"\nNew-language files written: {p2_total}")

# ── Summary ──────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"TOTAL FILES GENERATED: {count}")
print(f"  Existing-language P1 articles: {p2_count_start}")
print(f"  New-language P2 articles + base: {p2_total}")
print(f"{'='*60}")
