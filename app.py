import streamlit as st
import unicodedata
import re
import html

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="Ghost Buster Ultimate",
    page_icon="👻",
    layout="wide"
)

# --- 2. CSS احترافي (ألوان مميزة لكل نوع تهديد) ---
st.markdown("""
<style>
    .stTextArea textarea { font-family: 'Courier New', monospace; font-size: 16px; }
    
    .result-box {
        padding: 20px; border-radius: 8px; border: 1px solid #444;
        background-color: #2b2b2b; color: #e0e0e0;
        font-family: monospace; white-space: pre-wrap; direction: rtl; line-height: 2;
    }
    
    /* 1. بصمة AI (برتقالي) */
    .ai-phrase {
        background-color: rgba(255, 165, 0, 0.25); 
        border-bottom: 2px dashed #ffa500;
        border-radius: 4px;
        padding: 0 2px;
    }
    
    /* 2. أحرف مخفية (أحمر) */
    .hidden-char {
        background-color: rgba(255, 75, 75, 0.5); 
        color: white;
        padding: 1px 4px; 
        border-radius: 3px; 
        font-size: 0.8em;
        font-weight: bold;
        border: 1px solid #ff4b4b;
        margin: 0 2px;
    }
    
    /* 3. أحرف خادعة Homoglyphs (أصفر) */
    .homoglyph {
        background-color: rgba(255, 215, 0, 0.4); 
        color: #fff;
        padding: 1px 4px; 
        border-radius: 3px;
        border: 1px solid #ffd700;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. قواعد البيانات (Patterns) ---

# أ. قائمة بصمات AI (Real AI Fingerprints)
AI_PHRASES = [
    # العربية
    (r"بصفتي (نموذج|ذكاء|لغوي)", "هوية AI"),
    (r"إذا (كنت )?تريد", "عرض خيارات"),
    (r"أقدر (أ)?نشئ لك", "عرض مساعدة"),
    (r"(إليك|ها هو) (النص|الكود|المثال|الشرح)", "تسليم إجابة"),
    (r"لا تتردد في (سؤالي|طلب)", "خاتمة AI"),
    (r"أنا مجرد برنامج", "تصلب هوية"),
    (r"بناءً على معلوماتي", "تحفظ معرفي"),
    (r"فيما يلي", "تمهيد قائمة"),
    # English
    (r"As an AI language model", "AI Identity"),
    (r"I cannot (fulfill|generate)", "Refusal"),
    (r"Feel free to ask", "AI Closing"),
    (r"Here is (the|a)", "Delivering Answer"),
]

# ب. الرموز المخفية (Technical Hidden Chars)
EXTENDED_INVISIBLE_CATEGORIES = {"Cf", "Cc", "Cs"}
BIDI_CONTROL = {0x202A, 0x202B, 0x202C, 0x202D, 0x202E, 0x2066, 0x2067, 0x2068, 0x2069}
ZERO_WIDTH = {0x200B, 0x200C, 0x200D, 0xFEFF, 0x2060, 0x2061, 0x2062, 0x2063, 0x2064}
NON_BREAKING = {0x00A0, 0x180E}
ALL_HIDDEN = ZERO_WIDTH | BIDI_CONTROL | NON_BREAKING

# ج. الأحرف الخادعة (Homoglyphs)
HOMOGLYPHS = {
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H", "О": "O", "Р": "P", "С": "C", "Т": "T", "Х": "X",
    "ɑ": "a", "ϲ": "c", "ԁ": "d", "е": "e", "і": "i", "ј": "j"
}

# --- 4. منطق المعالجة (The Engine) ---

def get_ai_intervals(text):
    """تحديد أماكن جمل AI للبدء والإغلاق"""
    intervals = []
    for pattern, label in AI_PHRASES:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            intervals.append((match.start(), match.end(), label))
    return intervals

def advanced_cleaning(text, remove_markdown=True, normalize_unicode=True):
    stats = {
        "hidden_chars": 0, "homoglyphs": 0, "markdown": 0, "ai_phrases": 0
    }

    # 1. خريطة جمل AI (Start/End Mapping)
    ai_intervals = get_ai_intervals(text)
    stats["ai_phrases"] = len(ai_intervals)
    
    # تحويل الفترات إلى خريطة سهلة الوصول
    # start_map: index -> label (لبدء الوسم)
    # end_set: index (لإغلاق الوسم)
    start_map = {}
    end_set = set()
    
    for start, end, label in ai_intervals:
        start_map[start] = label
        end_set.add(end)

    clean_text_builder = []
    visual_html = ""
    
    # 2. الحلقة الرئيسية (Character Loop)
    for i, char in enumerate(text):
        # أ. هل يجب إغلاق وسم AI هنا؟
        if i in end_set:
            visual_html += "</span>"
            
        # ب. هل يبدأ وسم AI هنا؟
        if i in start_map:
            label = start_map[i]
            visual_html += f'<span class="ai-phrase" title="بصمة AI: {label}">'

        # ج. فحص الحرف نفسه (تقني)
        code = ord(char)
        category = unicodedata.category(char)
        homoglyph_fix = HOMOGLYPHS.get(char)
        
        # 1. فحص الإخفاء
        is_hidden = False
        issue_label = ""
        if code in ALL_HIDDEN:
            is_hidden = True; issue_label = "Hidden"
        elif category in EXTENDED_INVISIBLE_CATEGORIES and code not in (10, 13):
            is_hidden = True; issue_label = "Control"
            
        if is_hidden:
            stats["hidden_chars"] += 1
            visual_html += f'<span class="hidden-char" title="{issue_label}">[DEL]</span>'
            # لا نضيفه للنص النظيف
            
        # 2. فحص الخداع البصري
        elif homoglyph_fix:
            stats["homoglyphs"] += 1
            visual_html += f'<span class="homoglyph" title="تم تصحيح {char} إلى {homoglyph_fix}">[{char}→{homoglyph_fix}]</span>'
            clean_text_builder.append(homoglyph_fix)
            
        # 3. حرف طبيعي
        else:
            safe_char = html.escape(char).replace("\n", "<br>")
            visual_html += safe_char
            clean_text_builder.append(char)

    # إغلاق أي وسوم AI متبقية في نهاية النص
    if len(text) in end_set:
        visual_html += "</span>"

    clean_text = "".join(clean_text_builder)

    # 3. المعالجة النهائية (Normalization & Markdown)
    if normalize_unicode:
        clean_text = unicodedata.normalize("NFKC", clean_text)

    if remove_markdown:
        cleaned2 = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_text) # Bold
        cleaned2 = re.sub(r'`(.*?)`', r'\1', cleaned2)       # Code
        cleaned2 = re.sub(r'^#+\s+', '', cleaned2, flags=re.MULTILINE) # Headers
        if cleaned2 != clean_text:
            stats["markdown"] = 1
        clean_text = cleaned2

    return clean_text, visual_html, stats

# --- 5. واجهة المستخدم ---

with st.sidebar:
    st.title("⚙️ الإعدادات")
    opt_markdown = st.toggle("إزالة Markdown", value=True)
    opt_normalize = st.toggle("توحيد الأحرف (NFKC)", value=True)
    st.markdown("---")
    
    if st.button("🧪 توليد نص هجين (AI + Hidden)"):
        # نص يحتوي على: جملة AI + حرف مخفي + حرف روسي خادع
        st.session_state['input'] = "**تحليل:** بصفتي نموذج لغوي، أؤكد أن الـ Sysтem" + "\u200b" + " آمن."

st.title("👻 Ghost Buster Ultimate")
st.markdown("##### 🕵️‍♂️ المنصة الشاملة: كشف بصمات AI + الرموز المخفية + الأحرف الخادعة")

if 'input' not in st.session_state: st.session_state['input'] = ""

text_input = st.text_area("النص للفحص:", value=st.session_state['input'], height=150)

if st.button("🚀 فحص جنائي شامل", type="primary", use_container_width=True):
    if text_input:
        final_text, visual_html, stats = advanced_cleaning(text_input, opt_markdown, opt_normalize)
        
        # Dashboard
        st.markdown("---")
        c1, c2, c3, c4 = st.columns(4)
        
        # تلوين العدادات حسب الخطر
        c1.metric("بصمات AI", stats['ai_phrases'], delta="Detected" if stats['ai_phrases']>0 else "Clean", delta_color="inverse")
        c2.metric("أحرف مخفية", stats['hidden_chars'], delta="Found" if stats['hidden_chars']>0 else "Clean", delta_color="inverse")
        c3.metric("أحرف خادعة", stats['homoglyphs'], delta="Fixed" if stats['homoglyphs']>0 else "Clean", delta_color="inverse")
        c4.metric("تنسيقات", "Markdown" if stats['markdown'] else "None")

        # Tabs
        tab1, tab2 = st.tabs(["👁️ كشف المستور (X-Ray)", "✅ النص النظيف"])
        
        with tab1:
            st.markdown("""
            <div style="font-size:0.85em; margin-bottom:10px; color:#aaa;">
            دليل الألوان: 
            <span class="ai-phrase">برتقالي = كلام AI</span> | 
            <span class="hidden-char">أحمر = رمز مخفي</span> | 
            <span class="homoglyph">أصفر = حرف مزيف</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f'<div class="result-box">{visual_html}</div>', unsafe_allow_html=True)
            
        with tab2:
            st.text_area("جاهز للنسخ:", value=final_text, height=200)
