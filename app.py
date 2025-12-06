import unicodedata
import re

# --- 1. توسيع قائمة الأحرف المخفية ---
# [استدلال]: قائمة تشمل جميع فئات Unicode تقريباً المرتبطة بالإخفاء
EXTENDED_INVISIBLE_CATEGORIES = {"Cf", "Cc", "Cs"}
BIDI_CONTROL = {
    0x202A, 0x202B, 0x202C, 0x202D, 0x202E,
    0x2066, 0x2067, 0x2068, 0x2069
}
ZERO_WIDTH = {
    0x200B, 0x200C, 0x200D, 0xFEFF, 0x2060, 0x2061, 0x2062, 0x2063, 0x2064
}
NON_BREAKING = {0x00A0, 0x180E}
ALL_HIDDEN = ZERO_WIDTH | BIDI_CONTROL | NON_BREAKING

# كشف الهوموجليف (الأحرف المتشابهة بصرياً)
# [استدلال]: بناء قائمة بناءً على Unicode confusable characters المعروفة
HOMOGLYPHS = {
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H",
    "О": "O", "Р": "P", "С": "C", "Т": "T", "Х": "X",
    "ɑ": "a", "ϲ": "c", "ԁ": "d", "е": "e", "і": "i", "ј": "j"
}

def detect_hidden_chars(char):
    code = ord(char)
    category = unicodedata.category(char)

    if code in ALL_HIDDEN:
        return "HiddenChar"

    if category in EXTENDED_INVISIBLE_CATEGORIES and code not in (10, 13):
        return "UnicodeControl"

    if code in BIDI_CONTROL:
        return "BiDiSpoof"

    return None

def detect_homoglyphs(text):
    found = []
    for index, char in enumerate(text):
        if char in HOMOGLYPHS:
            found.append((index, char, HOMOGLYPHS[char]))
    return found

def detect_zero_width_encoded(text):
    # [استدلال]: بعض أدوات الإخفاء ترمز البيانات بسلسلة من ZWSP / ZWNJ / ZWJ
    pattern = r"[\u200B\u200C\u200D\u2060\u2061\u2062\u2063]{8,}"
    if re.search(pattern, text):
        return True
    return False

# نسخة محسّنة من الدالة الرئيسية
def advanced_cleaning(text, remove_markdown=True, normalize_unicode=True):
    stats = {
        "hidden_chars": 0,
        "bidi": 0,
        "homoglyphs": 0,
        "encoded_zero_width": 0,
        "markdown": 0
    }

    # تطبيع
    if normalize_unicode:
        clean_base = unicodedata.normalize("NFKC", text)
    else:
        clean_base = text

    # فحص الهوموجليف
    homoglyphs = detect_homoglyphs(clean_base)
    stats["homoglyphs"] = len(homoglyphs)

    # فحص ترميز مخفي داخل Zero Width
    if detect_zero_width_encoded(text):
        stats["encoded_zero_width"] = 1

    clean_text = ""
    visual_html = ""

    for char in text:
        issue = detect_hidden_chars(char)
        if issue:
            stats["hidden_chars"] += 1
            color = "#ff4b4b"
            visual_html += f'<span style="background:{color}; padding:2px; border-radius:4px;" title="{issue}">[{issue}]</span>'
        else:
            if char == "\n":
                visual_html += "<br>"
            else:
                visual_html += char

        if not issue:
            clean_text += char

    # إزالة Markdown
    if remove_markdown:
        cleaned2 = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_text)
        cleaned2 = re.sub(r'`(.*?)`', r'\1', cleaned2)
        if cleaned2 != clean_text:
            stats["markdown"] = 1
        clean_text = cleaned2

    return clean_text, visual_html, stats
