import streamlit as st
import unicodedata
import re
import html
import time
import google.generativeai as genai

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="Ghost Buster Public",
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
    .ai-phrase { background-color: rgba(255, 165, 0, 0.2); border-bottom: 2px dashed #ffa500; border-radius: 4px; padding: 2px 4px; }
    .hidden-char { background-color: rgba(255, 75, 75, 0.6); color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 0.8em; margin: 0 2px; }
    .homoglyph { background-color: rgba(255, 215, 0, 0.3); color: #fff; padding: 1px 4px; border: 1px solid #ffd700; border-radius: 4px; }
    h1 { color: #4285F4; text-align: center; margin-bottom: 30px; }
</style>
""", unsafe_allow_html=True)

# --- 3. المنطق وقواعد البيانات ---
AI_PHRASES = [
    (r"بصفتي (نموذج|ذكاء|لغوي)", "هوية AI"), (r"إذا (كنت )?تريد", "عرض خيارات"),
    (r"أقدر (أ)?نشئ لك", "عرض مساعدة"), (r"(إليك|ها هو) (النص|الكود|المثال)", "تسليم إجابة"),
    (r"لا تتردد في (سؤالي|طلب)", "خاتمة AI"), (r"أنا مجرد برنامج", "تصلب هوية"),
    (r"As an AI language model", "AI Identity"), (r"I cannot (fulfill|generate)", "Refusal")
]
EXTENDED_INVISIBLE_CATEGORIES = {"Cf", "Cc", "Cs"}
BIDI_CONTROL = {0x202A, 0x202B, 0x202C, 0x202D, 0x202E, 0x2066, 0x2067, 0x2068, 0x2069}
ZERO_WIDTH = {0x200B, 0x200C, 0x200D, 0xFEFF, 0x2060, 0x2061, 0x2062, 0x2063, 0x2064}
ALL_HIDDEN = ZERO_WIDTH | BIDI_CONTROL | {0x00A0, 0x180E}
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
    stats = {"hidden": 0, "homoglyphs": 0, "ai_phrases": len(ai_intervals)}
    
    for i, char in enumerate(text):
        if i in end_set: visual_html += "</span>"
        if i in start_map: visual_html += f'<span class="ai-phrase" title="{start_map[i]}">'
            
        code = ord(char)
        if code in ALL_HIDDEN or (unicodedata.category(char) in EXTENDED_INVISIBLE_CATEGORIES and code not in (10, 13)):
            stats["hidden"] += 1
            visual_html += '<span class="hidden-char">✖</span>'
        elif char in HOMOGLYPHS:
            stats["homoglyphs"] += 1
            visual_html += f'<span class="homoglyph">[{char}→{HOMOGLYPHS[char]}]</span>'
            clean_text_builder.append(HOMOGLYPHS[char])
        else:
            visual_html += html.escape(char).replace("\n", "<br>")
            clean_text_builder.append(char)
            
    if len(text) in end_set: visual_html += "</span>"
    clean_text = "".join(clean_text_builder)
    
    if normalize_unicode: clean_text = unicodedata.normalize("NFKC", clean_text)
    
    if remove_markdown:
        clean_text = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_text)
    
    return clean_text, visual_html, stats

# --- الدالة الذكية (تم تحديث القائمة بناءً على صورتك) ---
def humanize_with_gemini(text):
    try:
        api_key = st.secrets["GEMINI_KEY"]
    except:
        return "خطأ: لم يتم العثور على المفتاح في Secrets."

    genai.configure(api_key=api_key)
    
    # هذه القائمة مأخوذة حرفياً من صورة الفحص التي أرسلتها (image_2611fd.png)
    models_to_try = [
        'gemini-2.0-flash',        # الأولوية الأولى
        'gemini-2.0-flash-exp',    # نسخة تجريبية سريعة
        'gemini-2.5-flash',        # النسخة الأحدث التي ظهرت عندك
        'models/gemini-2.0-flash', # في حال طلب المسار الكامل
        'models/gemini-2.5-flash'
    ]
    
    prompt = f"أعد صياغة النص التالي ليكون بأسلوب بشري طبيعي جداً وبسيط وتخلص من نبرة الذكاء الاصطناعي:\n{text}"
    
    last_error = ""
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            last_error = str(e)
            continue
            
    return f"فشل الاتصال بجميع النماذج. الخطأ الأخير: {last_error}"

# --- 4. واجهة المستخدم ---
st.markdown("<h1>👻 Ghost Buster <span style='font-size:0.5em; color:#4285F4'>Public</span></h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>أداة مجانية للجميع لتنظيف النصوص وإعادة صياغتها</p>", unsafe_allow_html=True)
st.markdown("---")

if 'input' not in st.session_state: st.session_state['input'] = ""

with st.sidebar:
    st.header("⚙️ خيارات")
    opt_markdown = st.toggle("إزالة Markdown", value=True)
    opt_normalize = st.toggle("توحيد الأحرف", value=True)
    st.info("الخدمة تعمل تلقائياً.")

text_input = st.text_area("ضع النص هنا:", value=st.session_state['input'], height=150, placeholder="ألصق النص وسنقوم نحن بالباقي...")

c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    col_a, col_b = st.columns(2)
    with col_a:
        clean_btn = st.button("🧹 تنظيف فقط", type="secondary", use_container_width=True)
    with col_b:
        humanize_btn = st.button("✨ تنظيف + صياغة", type="primary", use_container_width=True)

if text_input and (clean_btn or humanize_btn):
    progress_text = "جاري المعالجة..."
    my_bar = st.progress(0, text=progress_text)
    for percent_complete in range(100):
        time.sleep(0.005)
        my_bar.progress(percent_complete + 1, text=progress_text)
    my_bar.empty()
    
    clean_text, visual_html, stats = advanced_cleaning(text_input, opt_markdown, opt_normalize)
    final_output = clean_text

    if humanize_btn:
        with st.spinner("🤖 جاري إعادة الصياغة (AI)..."):
            final_output = humanize_with_gemini(clean_text)
            if "خطأ" in final_output or "فشل" in final_output:
                st.toast("حدث خطأ في الخدمة", icon="⚠️")
                st.error(final_output)
            else:
                st.toast("تمت الصياغة!", icon="🎉")
    else:
        st.toast("تم التنظيف!", icon="✅")

    st.markdown("### 📊 النتائج")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("الحالة", "تمت", "100%")
    m2.metric("رموز مخفية", stats['hidden'], delta="-removed", delta_color="inverse")
    m3.metric("مزيفة", stats['homoglyphs'], delta="-fixed", delta_color="inverse")
    m4.metric("AI", stats['ai_phrases'], delta="detected", delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True)
    tab_clean, tab_xray = st.tabs(["✨ النص الجاهز", "👁️ التفاصيل"])
    
    with tab_clean:
        st.code(final_output, language=None)
    with tab_xray:
        st.markdown(f'<div class="result-box">{visual_html}</div>', unsafe_allow_html=True)

elif not text_input and (clean_btn or humanize_btn):
    st.warning("الرجاء إدخال نص أولاً!")
