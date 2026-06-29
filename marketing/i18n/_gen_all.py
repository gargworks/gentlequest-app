#!/usr/bin/env python3
"""Generate all 315 translated i18n files."""
import os, re, json

BASE = "/Users/lokeshgarg/gentlequest/marketing/i18n"
SRC = "/Users/lokeshgarg/gentlequest/marketing/seo/articles"

URLS = "- iOS — https://apps.apple.com/app/gentlequest/id6756537464\n- Android — https://play.google.com/store/apps/details?id=com.gentlequest.app\n- Web — https://gentlequest.app"

# Per-language translations of common sections
LANGS = {}

# ============================================================
# COMMON SECTIONS PER LANGUAGE
# ============================================================

LANGS["hi"] = {
    "gq_title": "## GentleQuest कहाँ फिट बैठता है",
    "gq_body": "GentleQuest एक शांत, निजी ऐप में मूड चेक-इन, ग्राउंडिंग उपकरण, जर्नलिंग और सत्यापित स्क्रीनिंग प्रश्नावली देता है — कोई विज्ञापन नहीं, कोई स्ट्रीक नहीं, कोई सदस्यता नहीं, कोई खाता आवश्यक नहीं। आपका डेटा आपके डिवाइस पर रहता है।",
    "scope_title": "## दायरे के बारे में एक नोट",
    "scope_body": "यह लेख निदान नहीं है; यदि आप संघर्ष कर रहे हैं, तो किसी पेशेवर से मिलें।",
}

LANGS["es"] = {
    "gq_title": "## Dónde encaja GentleQuest",
    "gq_body": "GentleQuest ofrece control de estado de ánimo, herramientas de conexión a tierra, diario y cuestionarios de cribado validados en una aplicación tranquila y privada — sin anuncios, sin rachas, sin suscripción, sin cuenta requerida. Tus datos se quedan en tu dispositivo.",
    "scope_title": "## Una nota sobre el alcance",
    "scope_body": "Este artículo no es un diagnóstico; si estás pasando por un momento difícil, consulta a un profesional.",
}

LANGS["pt-BR"] = {
    "gq_title": "## Onde o GentleQuest se encaixa",
    "gq_body": "O GentleQuest oferece check-ins de humor, ferramentas de ancoragem, diário e questionários de triagem validados em um aplicativo tranquilo e privado — sem anúncios, sem sequências, sem assinatura, sem conta necessária. Seus dados ficam no seu dispositivo.",
    "scope_title": "## Uma nota sobre o escopo",
    "scope_body": "Este artigo não é um diagnóstico; se você está passando por dificuldades, consulte um profissional.",
}

LANGS["id"] = {
    "gq_title": "## Di mana GentleQuest cocok",
    "gq_body": "GentleQuest menawarkan check-in suasana hati, alat penjangkaran, jurnal, dan kuesioner skrining tervalidasi dalam satu aplikasi yang tenang dan privat — tanpa iklan, tanpa rentetan, tanpa langganan, tanpa akun. Data Anda tetap di perangkat Anda.",
    "scope_title": "## Catatan tentang ruang lingkup",
    "scope_body": "Artikel ini bukan diagnosis; jika Anda sedang berjuang, temui profesional.",
}

LANGS["tl"] = {
    "gq_title": "## Saan angkop ang GentleQuest",
    "gq_body": "Nag-aalok ang GentleQuest ng mood check-ins, grounding tools, journaling, at validated screening questionnaires sa isang tahimik at pribadong app — walang ad, walang streak, walang subscription, walang account. Mananatili ang iyong data sa iyong device.",
    "scope_title": "## Isang paalala tungkol sa saklaw",
    "scope_body": "Hindi ito diagnosis; kung nakikipagbaka ka, kumunsulta sa propesyonal.",
}

LANGS["ar"] = {
    "gq_title": "## أين يأتي GentleQuest",
    "gq_body": "يقدم GentleQuest تسجيلات المزاج وأدوات التأريض واليوميات واستبيانات الفحص الموثقة في تطبيق هادئ وخاص — بدون إعلانات، بدون سلاسل، بدون اشتراك، بدون حساب. تبقى بياناتك على جهازك.",
    "scope_title": "## ملاحظة حول النطاق",
    "scope_body": "هذه المقالة ليست تشخيصًا؛ إذا كنت تعاني، استشر أحد المتخصصين.",
}

LANGS["vi"] = {
    "gq_title": "## Nơi GentleQuest phù hợp",
    "gq_body": "GentleQuest cung cấp ghi nhận tâm trạng, công cụ nối đất, nhật ký và bảng câu hỏi sàng lọc đã xác thực trong một ứng dụng yên tĩnh và riêng tư — không quảng cáo, không chuỗi ngày, không đăng ký, không cần tài khoản. Dữ liệu của bạn ở trên thiết bị của bạn.",
    "scope_title": "## Lưu ý về phạm vi",
    "scope_body": "Bài viết này không phải là chẩn đoán; nếu bạn đang gặp khó khăn, hãy gặp chuyên gia.",
}

LANGS["tr"] = {
    "gq_title": "## GentleQuest Nerede İşe Yarar",
    "gq_body": "GentleQuest, sakin ve özel bir uygulamada ruh hali kontrolü, topraklama araçları, günlük ve doğrulanmış tarama anketleri sunar — reklamsız, seri yapısız, aboneliksiz, hesap gerektirmeden. Verileriniz cihazınızda kalır.",
    "scope_title": "## Kapsam notu",
    "scope_body": "Bu makale bir teşhis değildir; zorlanıyorsanız bir uzmana görünün.",
}

LANGS["fr"] = {
    "gq_title": "## Où GentleQuest intervient",
    "gq_body": "GentleQuest propose des suivis de l'humeur, des outils d'ancrage, un journal et des questionnaires de dépistage validés dans une application calme et privée — sans publicités, sans séries, sans abonnement, sans compte requis. Vos données restent sur votre appareil.",
    "scope_title": "## Une note sur la portée",
    "scope_body": "Cet article n'est pas un diagnostic ; si vous traversez des difficultés, consultez un professionnel.",
}

LANGS["de"] = {
    "gq_title": "## Wo GentleQuest passt",
    "gq_body": "GentleQuest bietet Stimmungs-Check-ins, Erdungswerkzeuge, Journaling und validierte Screening-Fragebögen in einer ruhigen, privaten App — keine Werbung, keine Serien, kein Abo, kein Konto erforderlich. Ihre Daten bleiben auf Ihrem Gerät.",
    "scope_title": "## Ein Hinweis zum Geltungsbereich",
    "scope_body": "Dieser Artikel ist keine Diagnose; wenn Sie zu kämpfen haben, wenden Sie sich an einen Fachmann.",
}

def gq_section(lang):
    d = LANGS[lang]
    return f"{d['gq_title']}\n\n{d['gq_body']}\n\n{URLS}"

def scope_section(lang):
    d = LANGS[lang]
    return f"{d['scope_title']}\n\n{d['scope_body']}"

def wf(lang, subdir, fname, content):
    d = os.path.join(BASE, lang, subdir) if subdir else os.path.join(BASE, lang)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, fname)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content.strip() + "\n")

count = 0
def emit(lang, subdir, fname, title, target_kw, tags, body):
    global count
    tags_str = ", ".join(f'"{t}"' for t in tags)
    fm = f'---\ntitle: "{title}"\ntarget_keyword: "{target_kw}"\ntags: [{tags_str}]\n---\n'
    content = fm + "\n" + body + "\n\n" + gq_section(lang) + "\n\n" + scope_section(lang)
    wf(lang, subdir, fname, content)
    count += 1

print("Script loaded successfully")
print(f"Languages: {list(LANGS.keys())}")
