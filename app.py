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

    # تنظيف Markdown (تم إصلاح المسافات هنا)
    if remove_markdown:
        # إزالة Bold/Italic
        cleaned2 = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_text)
        cleaned2 = re.sub(r'\*(.*?)\*', r'\1', cleaned2)
        # إزالة Code blocks
        cleaned2 = re.sub(r'`(.*?)`', r'\1', cleaned2)
        # إزالة العناوين
        cleaned2 = re.sub(r'^#+\s+', '', cleaned2, flags=re.MULTILINE)
        
        if cleaned2 != clean_text:
            stats["markdown"] = 1
        clean_text = cleaned2

    return clean_text, visual_html, stats

# --- 5. واجهة المستخدم ---

# القائمة الجانبية
with st.sidebar:
    st.title("⚙️ الإعدادات")
    opt_markdown = st.toggle("إزالة Markdown (مثل **العريض**)", value=True)
    opt_normalize = st.toggle("توحيد الأحرف (Normalization)", value=True)
    
    st.markdown("---")
    st.info("هذا المشروع مفتوح المصدر للتنظيف الجنائي للنصوص.")
    
    if st.button("تجربة نص مخادع"):
        # نص يحتوي حرف روسي يشبه الإنجليزي + مسافة مخفية
        st.session_state['input'] = "System Hеalth Chеck" + "\u200b" + " OK"

# الواجهة الرئيسية
st.title("🛡️ Ghost Buster | المصحح الجنائي")
st.markdown("أداة متقدمة لكشف النصوص المخفية، الهوموجليف (الأحرف المتشابهة)، وبصمات AI.")

if 'input' not in st.session_state: st.session_state['input'] = ""

text_input = st.text_area("النص:", value=st.session_state['input'], height=150)

if st.button("🚀 ابدأ الفحص", type="primary", use_container_width=True):
    if text_input:
        final_text, visual_html, stats = advanced_cleaning(text_input, opt_markdown, opt_normalize)
        
        # عرض العدادات
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("أحرف مخفية", stats['hidden_chars'], delta_color="inverse")
        col2.metric("أحرف خادعة (Homoglyphs)", stats['homoglyphs'], delta_color="inverse")
        col3.metric("تنسيقات Markdown", stats['markdown'])
        col4.metric("تشفير خفي", "نعم" if stats['encoded_zero_width'] else "لا")

        # التبويبات
        tab1, tab2 = st.tabs(["👁️ تقرير الفحص (X-Ray)", "✅ النص النظيف"])
        
        with tab1:
            if stats['hidden_chars'] == 0 and stats['homoglyphs'] == 0:
                st.success("النص سليم تماماً!")
            else:
                st.markdown("المناطق الملونة هي التهديدات التي تم التعامل معها:")
                st.markdown(f'<div class="result-box">{visual_html}</div>', unsafe_allow_html=True)
        
        with tab2:
            st.text_area("جاهز للنسخ:", value=final_text, height=200)
