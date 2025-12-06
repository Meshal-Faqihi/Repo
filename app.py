import streamlit as st
import unicodedata
import re
import html
import time
import google.generativeai as genai
import binascii

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="Ghost Buster Pro",
    page_icon="👻",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; }
    .stButton button { width: 100%; border-radius: 8px; font-weight: bold; transition: all 0.3s; }
    .result-box {
        padding: 20px; border-radius: 10px; border: 1px solid #444;
        background-color: #1e1e1e; color: #e0e0e0;
        font-family: 'Courier New', monospace; white-space: pre-wrap; direction: rtl; line-height: 2;
        max-height: 400px; overflow-y: auto;
    }
    /* ألوان التهديدات */
    .ai-phrase { background-color: rgba(255, 165, 0, 0.2); border-bottom: 2px dashed #ffa500; border-radius: 4px; padding: 2px 4px; }
    .hidden-char { background-color: rgba(255, 75, 75, 0.6); color: white; padding: 0 4px; border-radius: 3px; font-weight: bold; font-size: 0.8em; border: 1px solid #ff4b4b; }
    .homoglyph { background-color: rgba(255, 215, 0, 0.3); color: #fff; padding: 0 4px; border: 1px solid #ffd700; border-radius: 4px; }
    /* لون جديد للمسافات الغريبة (NBSP) */
    .weird-space { background-color: rgba(0, 191, 255, 0.3); color: cyan; padding: 0 2px; border: 1px solid cyan; border-radius: 3px; font-size: 0.8em;}
    
    h1 { color: #4285F4; text-align: center; margin-bottom: 30px; }
</style>
""", unsafe_allow_html=True)

# --- 3. قواعد البيانات الموسعة ---
AI_PHRASES = [
    (r"بصفتي (نموذج|ذكاء|لغوي)", "هوية AI"), (r"إذا (كنت )?تريد", "عرض خيارات"),
    (r"أقدر (أ)?نشئ لك", "عرض مساعدة"), (r"(إليك|ها هو) (النص|الكود|المثال)", "تسليم إجابة"),
    (r"لا تتردد في (سؤالي|طلب)", "خاتمة AI"), (r"أنا مجرد برنامج", "تصلب هوية"),
    (r"As an AI language model", "AI Identity"), (r"I cannot (fulfill|generate)", "Refusal")
]

# قائمة الأحرف المخفية والخطيرة
# 0xA0 = Non-Breaking Space (المتهم الأول في السير الذاتية)
DANGEROUS_CHARS = {
    0x200B, 0x200C, 0x200D, 0xFEFF, # Zero Width
    0x2060, 0x2061, 0x2062, 0x2063, 0x2064, # Invisible Separators
    0x202A, 0x202B, 0x202C, 0x202D, 0x202E, # Bidi Control
    0x00AD, # Soft Hyphen
    0x2009, 0x200A, # Thin Spaces
}

HOMOGLYPHS = {"А":"A", "В":"B", "Е":"E", "К":"K", "М":"M", "Н":"H", "О":"O", "Р":"P", "С":"C", "Т":"T", "Х":"X", "е":"e", "і":"i"}

def get_ai_intervals(text):
    intervals = []
    for pattern, label in AI_PHRASES:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            intervals.append((match.start(), match.end(), label))
    return intervals

def advanced_cleaning(text, remove_markdown=True, normalize_unicode=True):
    ai_intervals = get_ai_intervals(text)
    start_map = {start: label for start, end, label in ai_intervals}
    end_set = {end for start, end, label in ai_intervals}
    
    clean_text_builder = []
    visual_html = ""
    stats = {"hidden": 0, "homoglyphs": 0, "weird_spaces": 0, "ai_phrases": len(ai_intervals)}
    
    for i, char in enumerate(text):
        if i in end_set: visual_html += "</span>"
        if i in start_map: visual_html += f'<span class="ai-phrase" title="{start_map[i]}">'
            
        code = ord(char)
        
        # 1. فحص المسافات الغريبة (NBSP) - المشكلة الشائعة في الـ CV
        if code == 0x00A0: 
            stats["weird_spaces"] += 1
            visual_html += '<span class="weird-space" title="Non-Breaking Space (0xA0)">[NBSP]</span>'
            clean_text_builder.append(" ") # استبدالها بمسافة عادية
            
        # 2. فحص الأحرف المخفية الخطيرة
        elif code in DANGEROUS_CHARS or (unicodedata.category(char) in ['Cf', 'Cc'] and code not in (9, 10, 13)):
            stats["hidden"] += 1
            hex_val = f"{code:04X}"
            visual_html += f'<span class="hidden-char" title="Hidden Char ({hex_val})">[DEL]</span>'
            # لا نضيفها للنص النظيف
            
        # 3. فحص الأحرف المزيفة
        elif char in HOMOGLYPHS:
            stats["homoglyphs"] += 1
            visual_html += f'<span class="homoglyph">[{char}→{HOMOGLYPHS[char]}]</span>'
            clean_text_builder.append(HOMOGLYPHS[char])
            
        # 4. حرف طبيعي
        else:
            safe_char = html.escape(char).replace("\n", "<br>").replace("\t", "&emsp;")
            visual_html += safe_char
            clean_text_builder.append(char)
            
    if len(text) in end_set: visual_html += "</span>"
    clean_text = "".join(clean_text_builder)
    
    if normalize_unicode: clean_text = unicodedata.normalize("NFKC", clean_text)
    if remove_markdown: clean_text = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_text)
    
    return clean_text, visual_html, stats

def humanize_with_gemini(text):
    try:
        api_key = st.secrets["GEMINI_KEY"]
    except:
        return "خطأ: لم يتم العثور على المفتاح في Secrets."

    genai.configure(api_key=api_key)
    models_to_try = ['gemini-2.0-flash', 'gemini-2.0-flash-exp', 'gemini-1.5-flash']
    
    prompt = f"أعد صياغة النص التالي ليكون بأسلوب بشري طبيعي وبسيط جداً:\n{text}"
    
    last_err = ""
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            last_err = str(e)
            continue
    return f"فشل الاتصال: {last_err}"

# --- 4. واجهة المستخدم ---
st.markdown("<h1>👻 Ghost Buster <span style='font-size:0.5em; color:#4285F4'>Paranoid Mode</span></h1>", unsafe_allow_html=True)
st.markdown("---")

if 'input' not in st.session_state: st.session_state['input'] = ""

with st.sidebar:
    st.header("⚙️ خيارات")
    opt_markdown = st.toggle("إزالة Markdown", value=True)
    opt_normalize = st.toggle("توحيد الأحرف", value=True)
    st.info("الوضع البارانويا: يكشف حتى المسافات البيضاء غير القياسية.")

text_input = st.text_area("ضع النص هنا:", value=st.session_state['input'], height=200, placeholder="ألصق النص وسنقوم بمسحه...")

c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    col_a, col_b = st.columns(2)
    with col_a:
        clean_btn = st.button("🧹 تنظيف دقيق", type="secondary", use_container_width=True)
    with col_b:
        humanize_btn = st.button("✨ تنظيف + صياغة", type="primary", use_container_width=True)

if text_input and (clean_btn or humanize_btn):
    progress_text = "جاري الفحص الدقيق..."
    my_bar = st.progress(0, text=progress_text)
    for percent_complete in range(100):
        time.sleep(0.005)
        my_bar.progress(percent_complete + 1, text=progress_text)
    my_bar.empty()
    
    clean_text, visual_html, stats = advanced_cleaning(text_input, opt_markdown, opt_normalize)
    final_output = clean_text

    if humanize_btn:
        with st.spinner("🤖 جاري الصياغة..."):
            final_output = humanize_with_gemini(clean_text)
            if "خطأ" in final_output:
                st.toast("خطأ في الاتصال", icon="⚠️")
                st.error(final_output)
            else:
                st.toast("تم!", icon="🎉")
    else:
        st.toast("تم التنظيف!", icon="✅")

    # النتائج
    st.markdown("### 📊 تقرير التهديدات")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("مسافات وهمية (NBSP)", stats['weird_spaces'], delta="Cyan", delta_color="off")
    c2.metric("رموز مخفية (Hidden)", stats['hidden'], delta="Red", delta_color="inverse")
    c3.metric("أحرف مزيفة (Fake)", stats['homoglyphs'], delta="Gold", delta_color="inverse")
    c4.metric("بصمات AI", stats['ai_phrases'], delta="Orange", delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True)
    tab_clean, tab_xray, tab_hex = st.tabs(["✨ النص الجاهز", "👁️ الأشعة السينية", "🔢 فحص الكود (Hex)"])
    
    with tab_clean:
        st.code(final_output, language=None)
    with tab_xray:
        st.markdown(f'<div class="result-box">{visual_html}</div>', unsafe_allow_html=True)
        st.caption("اللون السماوي [NBSP] هو مسافات غير قياسية تسبب مشاكل، تم استبدالها بمسافات عادية.")
    
    with tab_hex:
        st.info("هنا الحقيقة المطلقة: هذا التبويب يعرض الكود الرقمي لكل حرف.")
        # عرض الـ Hex Dump لأول 500 حرف
        hex_data = ' '.join(f"{ord(c):04X}" for c in text_input[:1000])
        st.code(hex_data, language="text")
        st.markdown("**دليل سريع:** `0020`=مسافة عادية (سليم) | `00A0`=مسافة وهمية (مشكلة) | `200B`=مسافة صفرية (خطر)")

elif not text_input and (clean_btn or humanize_btn):
    st.warning("الرجاء إدخال نص أولاً!")
