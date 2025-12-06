import streamlit as st
import unicodedata
import re
import html
import time # للإيحاء بالمعالجة
from openai import OpenAI

# --- 1. إعدادات الصفحة والتصميم العام ---
st.set_page_config(
    page_title="Ghost Buster AI",
    page_icon="👻",
    layout="wide",
    initial_sidebar_state="collapsed" # القائمة مغلقة لتركيز أكبر
)

# --- 2. CSS احترافي جداً (Dark Mode Friendly) ---
st.markdown("""
<style>
    /* تحسين الخطوط */
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; }
    
    /* جعل الأزرار تأخذ عرض العمود بالكامل */
    .stButton button { width: 100%; border-radius: 8px; font-weight: bold; transition: all 0.3s; }
    
    /* صندوق النتائج (Scrollable) */
    .result-box {
        padding: 20px; border-radius: 10px; border: 1px solid #444;
        background-color: #1e1e1e; color: #e0e0e0;
        font-family: 'Courier New', monospace; white-space: pre-wrap; direction: rtl; line-height: 2;
        max-height: 400px; overflow-y: auto; /* شريط تمرير إذا النص طويل */
        box-shadow: inset 0 0 10px #00000050;
    }
    
    /* الألوان الخاصة بالتهديدات */
    .ai-phrase { background-color: rgba(255, 165, 0, 0.2); border-bottom: 2px dashed #ffa500; border-radius: 4px; padding: 2px 4px; }
    .hidden-char { background-color: rgba(255, 75, 75, 0.6); color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 0.8em; margin: 0 2px; box-shadow: 0 0 5px rgba(255, 75, 75, 0.4); }
    .homoglyph { background-color: rgba(255, 215, 0, 0.3); color: #fff; padding: 1px 4px; border: 1px solid #ffd700; border-radius: 4px; }
    
    /* تحسين العناوين */
    h1 { color: #ff4b4b; text-align: center; margin-bottom: 30px; }
</style>
""", unsafe_allow_html=True)

# --- 3. المنطق البرمجي (نفس المحرك القوي) ---
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
            visual_html += '<span class="hidden-char">✖</span>' # رمز X بدلاً من DEL لجمالية أكثر
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
    if remove_markdown: clean_text = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_text)
    
    return clean_text, visual_html, stats

def humanize_with_ai(text, api_key):
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "أنت محرر نصوص محترف. أعد صياغة النص ليبدو طبيعياً جداً وتخلص من رسمية الذكاء الاصطناعي."},
                {"role": "user", "content": f"أعد صياغة هذا النص: {text}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# --- 4. واجهة المستخدم (UX Design) ---

# Header Section
st.markdown("<h1>👻 Ghost Buster <span style='font-size:0.5em; color:gray'>Ultimate Edition</span></h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>المنصة الأقوى لتنظيف النصوص من البصمات الرقمية الخفية</p>", unsafe_allow_html=True)
st.markdown("---")

# Session State
if 'input' not in st.session_state: st.session_state['input'] = ""
if 'processed' not in st.session_state: st.session_state['processed'] = False

# Sidebar
with st.sidebar:
    st.header("⚙️ لوحة التحكم")
    st.info("قم بإعداد خيارات التنظيف هنا")
    opt_markdown = st.toggle("إزالة Markdown", value=True)
    opt_normalize = st.toggle("توحيد الأحرف (NFKC)", value=True)
    
    st.divider()
    
    st.subheader("🧠 الوضع البشري (Pro)")
    user_api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...", help="مطلوب فقط لميزة إعادة الصياغة")
    
    st.divider()
    if st.button("🧪 نص للتجربة"):
        st.session_state['input'] = "**تحذير:** بصفتي نموذج لغوي، أؤكد أن الـ Sysтem" + "\u200b" + " آمن."

# Main Input Area
text_input = st.text_area("الصق النص هنا:", value=st.session_state['input'], height=150, placeholder="النص المشكوك فيه...")

# Action Buttons (Centered & Large)
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    col_a, col_b = st.columns(2)
    with col_a:
        clean_btn = st.button("🧹 تنظيف تقني", type="secondary", use_container_width=True)
    with col_b:
        humanize_btn = st.button("✨ تنظيف + صياغة", type="primary", use_container_width=True, disabled=not user_api_key, help="يتطلب مفتاح API")

# Processing Logic
if text_input and (clean_btn or humanize_btn):
    st.session_state['processed'] = True
    
    # Progress Bar (Visual Feedback)
    progress_text = "جاري مسح البصمات الرقمية..."
    my_bar = st.progress(0, text=progress_text)
    
    for percent_complete in range(100):
        time.sleep(0.005) # محاكاة سريعة
        my_bar.progress(percent_complete + 1, text=progress_text)
    my_bar.empty()
    
    # Core Processing
    clean_text, visual_html, stats = advanced_cleaning(text_input, opt_markdown, opt_normalize)
    final_output = clean_text

    # AI Processing if requested
    if humanize_btn:
        with st.spinner("🤖 جاري إعادة الكتابة بأسلوب بشري..."):
            final_output = humanize_with_ai(clean_text, user_api_key)
            if "Error" in final_output:
                st.toast(final_output, icon="❌")
            else:
                st.toast("تمت إعادة الصياغة بنجاح!", icon="🎉")
    else:
        st.toast("تم التنظيف التقني بنجاح!", icon="✅")

    # --- Results Dashboard ---
    st.markdown("### 📊 تقرير الفحص")
    
    # Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("الحالة", "تم التنظيف", "100%", delta_color="normal")
    m2.metric("رموز مخفية", stats['hidden'], delta="-removed", delta_color="inverse")
    m3.metric("أحرف مزيفة", stats['homoglyphs'], delta="-fixed", delta_color="inverse")
    m4.metric("بصمات AI", stats['ai_phrases'], delta="detected", delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs for clearer view
    tab_clean, tab_xray = st.tabs(["✨ النص النهائي (جاهز للنسخ)", "👁️ الأشعة السينية (X-Ray)"])
    
    with tab_clean:
        st.success("يمكنك نسخ النص الآمن من الأسفل:")
        st.code(final_output, language=None) # استخدام st.code يسهل النسخ بزر واحد
    
    with tab_xray:
        st.info("هنا ترى ما تم حذفه أو تعديله:")
        st.markdown(f'<div class="result-box">{visual_html}</div>', unsafe_allow_html=True)
        st.caption("الرموز الحمراء: مخفية | الصفراء: مزيفة | البرتقالية: كلمات AI")

elif not text_input and (clean_btn or humanize_btn):
    st.warning("الرجاء إدخال نص أولاً!")
