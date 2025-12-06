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
        "homoglyphs": 0,
        "encoded_zero_width": 0,
        "markdown": 0
    }

    # 1. فحص وجود ترميز مخفي (لإحصائيات فقط)
    if detect_zero_width_encoded(text):
        stats["encoded_zero_width"] = 1

    clean_text_builder = []
    visual_html = ""

    # نستخدم النص الأصلي في الحلقة لضمان دقة التقرير البصري
    for char in text:
        # أ. فحص الأحرف المخفية
        issue = detect_hidden_chars(char)
        
        # ب. فحص الهوموجليف (هل هذا الحرف مخادع؟)
        homoglyph_fix = HOMOGLYPHS.get(char) # يرجع الحرف الأصلي أو None

        if issue:
            # حالة: حرف مخفي (يجب حذفه)
            stats["hidden_chars"] += 1
            visual_html += f'<span style="background:#ff4b4b; color:white; padding:1px 4px; border-radius:3px; font-size:0.8em;" title="{issue}">[{issue}]</span>'
            # لا نضيفه لـ clean_text_builder
            
        elif homoglyph_fix:
            # حالة: حرف مخادع (يجب استبداله)
            stats["homoglyphs"] += 1
            # في العرض نلونه بالأصفر
            visual_html += f'<span style="background:#ffd700; color:black; padding:1px 4px; border-radius:3px;" title="تم تحويل {char} إلى {homoglyph_fix}">[{char}→{homoglyph_fix}]</span>'
            # في التنظيف نضع الحرف الصحيح
            clean_text_builder.append(homoglyph_fix)
            
        else:
            # حالة: حرف سليم
            safe_char = char.replace("<", "&lt;").replace(">", "&gt;") # حماية HTML
            if char == "\n":
                visual_html += "<br>"
            else:
                visual_html += safe_char
            
            clean_text_builder.append(char)

    # تجميع النص
    clean_text = "".join(clean_text_builder)

    # 2. التطبيع النهائي (Normalization)
    # نقوم به هنا على النص النظيف لضمان توحيد الأشكال
    if normalize_unicode:
        clean_text = unicodedata.normalize("NFKC", clean_text)

    # 3. إزالة Markdown
    if remove_markdown:
        # إزالة Bold
        cleaned2 = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_text)
        # إزالة Code blocks
        cleaned2 = re.sub(r'`(.*?)`', r'\1', cleaned2)
        # إزالة Links [text](url)
        cleaned2 = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', cleaned2)
        
        if cleaned2 != clean_text:
            stats["markdown"] = 1
        clean_text = cleaned2

    return clean_text, visual_html, stats
