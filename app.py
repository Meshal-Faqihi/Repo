import streamlit as st
import unicodedata
import re
import html

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="Ghost Buster Pro",
    page_icon="🛡️",
    layout="wide"
)

# --- 2. CSS للتصميم ---
st.markdown("""
<style>
    .stTextArea textarea { font-family: 'Courier New', monospace; }
    .result-box {
        padding: 15px; border-radius: 8px; border: 1px solid #444;
        background-color: #2b2b2b; color: #e0e0e0;
        font-family: monospace; white-space: pre-wrap; direction: rtl; line-height: 1.8;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. قواعد البيانات والتعاريف ---

# قوائم الرموز المخفية
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

# قائمة الهوموجليف (الأحرف الخادعة)
HOMOGLYPHS = {
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H",
    "О": "O", "Р": "P", "С": "C", "Т": "T", "Х": "X",
    "ɑ": "a", "ϲ": "c", "ԁ": "d", "е": "e", "і": "i", "ј": "j"
}

# --- 4. الدوال المساعدة ---

def detect_hidden_chars(char):
    code = ord(char)
    category = unicodedata.category(char)
    
    if code in ALL_HIDDEN: return "HiddenChar"
    if category in EXTENDED_INVISIBLE_CATEGORIES and code not in (10, 13): return "UnicodeControl"
    return None

def detect_zero_width_encoded(text):
    # البحث عن نمط متكرر من الأحرف المخفية (بصمة رقمية)
    pattern = r"[\u200B\u200C\u200D\u2060\u2061\u2062\u2063]{8,}"
    if re.search(pattern, text): return True
    return False

def advanced_cleaning(text, remove_markdown=True, normalize_unicode=True):
    stats = {
        "hidden_chars": 0, "homoglyphs": 0,
        "encoded_zero_width": 0, "markdown": 0
    }

    # فحص بصمة التشفير
    if detect_zero_width_encoded(text):
        stats["encoded_zero_width"] = 1

    clean_text_builder = []
    visual_html = ""

    # المعالجة حرفاً بحرف
    for char in text:
        issue = detect_hidden_chars(char)
        homoglyph_fix = HOMOGLYPHS.get(char)

        if issue:
            stats["hidden_chars"] += 1
            # تمييز الحذف باللون الأحمر
            visual_html += f'<span style="background:rgba(255, 75, 75, 0.4); color:#ff6b6b; padding:0 3px; border-radius:3px; font-size:0.8em;" title="{issue}">[DEL]</span>'
        
        elif homoglyph_fix:
            stats["homoglyphs"] += 1
            # تمييز الاستبدال باللون الأصفر
            visual_html += f'<span style="background:rgba(255, 215, 0, 0.3); color:#ffd700; padding:0 3px; border-radius:3px;" title="تم تحويل {char} إلى {homoglyph_fix}">[{char}→{homoglyph_fix}]</span>'
            clean_text_builder.append(homoglyph_fix)
            
        else:
            # حرف سليم
            safe_char = html.escape(char).replace("\n", "<br>")
            visual_html += safe_char
            clean_text_builder.append(char)

    clean_text = "".join(clean_text_builder)

    # التطبيع النهائي
    if normalize_unicode:
        clean_text = unicodedata.normalize("NFKC", clean_text)

    # تنظيف Markdown
    if remove_markdown
