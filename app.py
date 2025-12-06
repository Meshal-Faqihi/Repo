import streamlit as st
import unicodedata
import re
import html
# استدعاء مكتبة الربط (قد تحتاج لتثبيتها أولاً: pip install openai)
from openai import OpenAI 

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Ghost Buster Ultimate", page_icon="👻", layout="wide")

# --- 2. CSS ---
st.markdown("""
<style>
    .stTextArea textarea { font-family: 'Courier New', monospace; }
    .result-box { padding: 20px; border-radius: 8px; background-color: #2b2b2b; color: #e0e0e0; direction: rtl; line-height: 2; }
    .ai-phrase { background-color: rgba(255, 165, 0, 0.25); border-bottom: 2px dashed #ffa500; border-radius: 4px; }
    .hidden-char { background-color: rgba(255, 75, 75, 0.5); color: white; padding: 1px 4px; border-radius: 3px; border: 1px solid #ff4b4b; }
    .homoglyph { background-color: rgba(255, 215, 0, 0.4); color: #fff; padding: 1px 4px; border-radius: 3px; border: 1px solid #ffd700; }
</style>
""", unsafe_allow_html=True)

# --- 3. بيانات الفحص (Patterns) ---
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

# --- 4. دوال المعالجة والربط ---

def get_ai_intervals(text):
    intervals = []
    for pattern, label in AI_PHRASES:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            intervals.append((match.start(), match.end(), label))
    return intervals

def advanced_cleaning(text, remove_markdown=True, normalize_unicode=True):
    # ... (نفس منطق التنظيف السابق تماماً) ...
    # اختصاراً للمساحة، سأضع المنطق الأساسي هنا
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
            visual_html += '<span class="hidden-char">[DEL]</span>'
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

# --- دالة الربط بـ OpenAI (الجديدة) ---
def humanize_with_ai(text, api_key):
    try:
        client = OpenAI(api_key=api_key)
        
        prompt = """
        أعد صياغة النص التالي ليكون طبيعياً جداً، وكأنه مكتوب بواسطة إنسان عادي.
        - استخدم تنوعاً في طول الجمل.
        - تجنب كلمات الذكاء الاصطناعي الرسمية والمكررة.
        - حافظ على المعنى الأصلي تماماً.
        النص:
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini", # نموذج سريع ورخيص وقوي
            messages=[
                {"role": "system", "content": "أنت خبير في التحرير اللغوي الطبيعي."},
                {"role": "user", "content": prompt + text}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"خطأ في الاتصال: {str(e)}"

# --- 5. واجهة المستخدم ---

with st.sidebar:
    st.title("⚙️ الإعدادات")
    opt_markdown = st.toggle("إزالة Markdown", value=True)
    
    st.markdown("---")
    st.markdown("### 🧠 ربط الذكاء الاصطناعي")
    st.caption("لتفعيل ميزة إعادة الصياغة البشرية، أدخل مفتاح OpenAI:")
    # حقل آمن لإدخال المفتاح (يظهر كنقاط)
    user_api_key = st.text_input("OpenAI API Key", type="password", help="يبدأ عادة بـ sk-...")
    
    st.markdown("---")
    if st.button("🧪 نص للتجربة"):
        st.session_state['input'] = "**تنبيه:** بصفتي نموذج لغوي، لا يمكنني تأكيد الـ Daтa" + "\u200b" + "."

st.title("👻 Ghost Buster Ultimate + AI Link")

if 'input' not in st.session_state: st.session_state['input'] = ""
text_input = st.text_area("النص:", value=st.session_state['input'], height=150)

col1, col2 = st.columns([1, 1])

with col1:
    clean_btn = st.button("🔍 تنظيف تقني فقط", use_container_width=True)
with col2:
    # هذا الزر يعمل فقط إذا أدخل المستخدم المفتاح
    humanize_btn = st.button("✨ تنظيف + صياغة بشرية", type="primary", use_container_width=True, disabled=not user_api_key)

# --- التنفيذ ---

if text_input and (clean_btn or humanize_btn):
    # أولاً: التنظيف التقني (يحدث في الحالتين)
    clean_text, visual_html, stats = advanced_cleaning(text_input, opt_markdown)
    
    st.markdown("---")
    
    # عرض النتائج التقنية
    with st.expander("👁️ تقرير الفحص التقني (الأحرف المخفية)", expanded=clean_btn):
        st.markdown(f'<div class="result-box">{visual_html}</div>', unsafe_allow_html=True)
        st.caption(f"تمت إزالة {stats['hidden']} رمز مخفي، و {stats['homoglyphs']} حرف مزيف.")

    # ثانياً: إذا طلب المستخدم "صياغة بشرية"
    if humanize_btn:
        with st.spinner("جاري الاتصال بالعقل الإلكتروني لإعادة الصياغة..."):
            # نرسل النص "النظيف تقنياً" ليتم إعادة صياغته
            final_output = humanize_with_ai(clean_text, user_api_key)
            
        st.success("✅ النص جاهز! (نظيف تقنياً + أسلوب بشري)")
        st.text_area("النتيجة النهائية:", value=final_output, height=200)
    
    elif clean_btn:
        st.success("✅ تم التنظيف التقني فقط")
        st.text_area("النص النظيف:", value=clean_text, height=200)
