import streamlit as st
import unicodedata
import re
import html

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="Ghost Buster v2.0 | كاشف الذكاء الاصطناعي",
    page_icon="👻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS مخصص (الألوان: أحمر للمخفي، برتقالي للكلام الآلي) ---
st.markdown("""
<style>
    .stTextArea textarea { font-family: 'Courier New', monospace; line-height: 1.6; }
    
    .result-box {
        padding: 15px; border-radius: 8px; border: 1px solid #444;
        background-color: #1e1e1e; color: #e0e0e0;
        font-family: monospace; white-space: pre-wrap; direction: rtl;
    }
    
    /* ستايل الأحرف المخفية (تقني) */
    .hidden-char {
        background-color: rgba(255, 75, 75, 0.3); color: #ff4b4b;
        padding: 0 4px; border-radius: 4px; border: 1px solid #ff4b4b; font-weight: bold;
    }
    
    /* ستايل جمل الذكاء الاصطناعي (لغوي) */
    .ai-phrase {
        background-color: rgba(255, 165, 0, 0.3); color: #ffa500;
        padding: 0 4px; border-radius: 4px; border: 1px dashed #ffa500; font-weight: bold;
    }
    
    .footer { text-align: center; color: #666; font-size: 12px; margin-top: 50px; }
</style>
""", unsafe_allow_html=True)

# --- 3. قواعد البيانات (Patterns DB) ---

# قائمة الرموز المخفية (التقنية)
BLACKLIST_CHARS = {
    0x200B, 0x200C, 0x200D, 0x200E, 0x200F, 0xFEFF, 
    0x202A, 0x202B, 0x202C, 0x202D, 0x202E,
    0x2060, 0x2061, 0x2062, 0x2063, 0x2064, 0x00A0
}

# قائمة جمل الذكاء الاصطناعي (اللغوية - Regex)
AI_PHRASES = [
    # العربية
    (r"بصفتي (نموذج|ذكاء|لغوي)", "هوية AI"),
    (r"إذا (كنت )?تريد", "عرض خيارات"),
    (r"أقدر (أ)?نشئ لك", "عرض مساعدة"),
    (r"(إليك|ها هو) (النص|الكود|المثال)", "تسليم إجابة"),
    (r"لا تتردد في (سؤالي|طلب)", "خاتمة AI"),
    (r"أنا مجرد برنامج", "تصلب هوية"),
    (r"بناءً على معلوماتي", "تحفظ معرفي"),
    # English
    (r"As an AI language model", "AI Identity"),
    (r"If you (want|need)", "Offering Help"),
    (r"Here is (the|a)", "Delivering Answer"),
    (r"Feel free to ask", "AI Closing"),
    (r"I cannot (fulfill|generate)", "Refusal"),
]

# --- 4. دوال المعالجة ---

def identify_char(char):
    code = ord(char)
    if code == 0x200B: return "ZWSP"
    if code == 0x200E: return "LRM"
    if code == 0x200F: return "RLM"
    if code == 0x00A0: return "NBSP"
    return "HIDDEN"

def scan_ai_speech(text):
    """
    دالة جديدة: تفحص النص بحثاً عن "كليشيهات" الذكاء الاصطناعي
    """
    found_patterns = []
    # ننسخ النص لنضع عليه العلامات لاحقاً
    marked_text = text 
    
    for pattern, label in AI_PHRASES:
        # البحث عن الجملة
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        for match in matches:
            phrase = match.group()
            found_patterns.append(label)
            # استبدال الجملة في النص "المعروض" فقط بوسم HTML ملون
            # نستخدم دالة lambda لتجنب استبدال ما تم استبداله سابقاً بشكل خاطئ
            # (هنا تبسيط للكود، في المشاريع الكبيرة نستخدم Tokenizer)
            replacement = f'<span class="ai-phrase" title="نمط AI: {label}">{phrase}</span>'
            marked_text = marked_text.replace(phrase, replacement)
            
    return marked_text, len(found_patterns)

def advanced_cleaning(text, remove_markdown=True, normalize_unicode=True):
    # 1. تحليل لغوي (AI Speech)
    text_with_ai_marks, ai_count = scan_ai_speech(text)
    
    # 2. تحليل تقني (Hidden Chars)
    clean_chars = []
    visual_report_parts = [] # سنعيد بناء النص للعرض
    
    stats = {"hidden": 0, "markdown": 0, "ai_speech": ai_count}
    
    # تطبيع النص (Normalize)
    if normalize_unicode:
        # ملاحظة: التطبيع يتم على النص الخام للتنظيف، لكننا نحتفظ بالنص الملون للعرض
        text_for_cleaning = unicodedata.normalize('NFKC', text)
    else:
        text_for_cleaning = text

    # معالجة الأحرف المخفية
    # (هنا حيلة برمجية: نستخدم النص الأصلي للعرض مع علامات AI، وننظف النص الخام)
    
    # بناء التقرير البصري (دمج علامات AI مع علامات الحذف)
    # هذه الخطوة تتطلب دقة، لذا سنقوم بمسح بسيط للعرض:
    final_visual_html = ""
    
    # لتجنب تعقيد الكود في دمج HTML مع الرموز، سنقوم بالمسح على النص الذي يحتوي علامات AI مسبقاً
    # ونضيف عليه علامات الحذف للأحرف المخفية
    for char in text_with_ai_marks:
        # إذا كان الحرف جزءاً من تاغ HTML أضفناه سابقاً، نتجاوزه (تبسيط)
        # لكن بما أننا نعالج حرفاً حرفاً، الأحرف المخفية لن تكون داخل تاغ HTML للكلام
        
        code = ord(char)
        if code in BLACKLIST_CHARS or (unicodedata.category(char) in ['Cf'] and code not in [10, 13]): # 10=New line
            label = identify_char(char)
            stats["hidden"] += 1
            final_visual_html += f'<span class="hidden-char" title="تم حذف {label}">[{label}]</span>'
        else:
            # الحرف سليم (أو هو جزء من تاغ HTML الخاص بـ AI Phrases)
            if char == "\n":
                final_visual_html += "<br>"
            else:
                final_visual_html += char

    # بناء النص النظيف النهائي (بدون أي HTML أو رموز)
    final_clean_text = ""
    for char in text_for_cleaning:
        if not (ord(char) in BLACKLIST_CHARS or unicodedata.category(char) == 'Cf'):
            final_clean_text += char
            
    # إزالة المارك داون من النص النظيف
    if remove_markdown:
        final_clean_text = re.sub(r'\*\*(.*?)\*\*', r'\1', final_clean_text) # Bold
        final_clean_text = re.sub(r'`(.*?)`', r'\1', final_clean_text)       # Code
        if final_clean_text != text_for_cleaning: stats["markdown"] = 1

    return final_clean_text, final_visual_html, stats

# --- 5. الواجهة (Sidebar & Main) ---
with st.sidebar:
    st.title("🛡️ المحرك")
    st.write("إعدادات الفحص:")
    st.toggle("كشف عبارات AI (لغوي)", value=True, disabled=True)
    st.toggle("كشف الرموز المخفية (تقني)", value=True, disabled=True)
    
    st.markdown("---")
    if st.button("توليد رد AI نمطي للتجربة"):
        st.session_state['input_text'] = "بصفتي نموذج لغوي، يسعدني مساعدتك.\nإذا تريد، أقدر أنشئ لك الكود." + "\u200b"

st.title("👻 Ghost Buster v2.0")
st.caption("يكشف الرموز المخفية + عبارات الذكاء الاصطناعي النمطية")

if 'input_text' not in st.session_state: st.session_state['input_text'] = ""

text_input = st.text_area("النص:", value=st.session_state['input_text'], height=150)

if st.button("🚀 تحليل جنائي شامل", type="primary", use_container_width=True):
    if text_input:
        clean_text, visual_html, stats = advanced_cleaning(text_input)
        
        # النتائج
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1: 
            if stats['ai_speech'] > 0:
                st.metric("بصمة AI اللغوية", f"{stats['ai_speech']} عبارات", delta="Detected", delta_color="inverse")
            else:
                st.metric("بصمة AI اللغوية", "0", delta="Clean")
                
        with c2: st.metric("رموز مخفية", stats['hidden'], delta="Dangerous" if stats['hidden']>0 else "Safe")
        with c3: st.metric("تنسيقات Markdown", stats['markdown'])
        
        if stats['ai_speech'] > 0:
            st.warning("⚠️ **تحذير:** النص يحتوي على عبارات نمطية تشير إلى أنه منسوخ من محادثة مع AI (انظر اللون البرتقالي).")

        tab1, tab2 = st.tabs(["🔍 كشف المستور (X-Ray)", "✅ النص النظيف"])
        
        with tab1:
            st.markdown("""
            <div style="font-size:0.9em; margin-bottom:10px;">
            دليل الألوان: <span class="hidden-char">أحمر = رمز مخفي</span> | <span class="ai-phrase">برتقالي = كلام AI نمطي</span>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f'<div class="result-box">{visual_html}</div>', unsafe_allow_html=True)
            
        with tab2:
            st.text_area("النص:", value=clean_text, height=200)
