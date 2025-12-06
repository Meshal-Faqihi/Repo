import streamlit as st
import google.generativeai as genai
import re
import unicodedata

# 1. إعداد الصفحة
st.set_page_config(page_title="Ghost Buster AI", layout="wide")

# 2. التنسيق
st.markdown("""
<style>
    .stTextArea textarea { direction: rtl; }
    div[data-testid="stMetricValue"] { font-size: 20px; }
</style>
""", unsafe_allow_html=True)

# 3. دوال التنظيف الأساسية
def clean_text_logic(text):
    # إزالة الرموز المخفية
    invisible_chars = [
        0x200B, 0x200C, 0x200D, 0xFEFF, 0x2060, 
        0x2061, 0x2062, 0x2063, 0x2064, 0x202A, 
        0x202B, 0x202C, 0x202D, 0x202E
    ]
    cleaned = ""
    hidden_count = 0
    
    for char in text:
        if ord(char) in invisible_chars or (unicodedata.category(char) in ['Cf'] and ord(char) not in [10, 13]):
            hidden_count += 1
        else:
            cleaned += char
            
    # إزالة المارك داون
    cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned)
    
    return cleaned, hidden_count

# 4. دالة الذكاء الاصطناعي (التي كانت تسبب المشاكل)
def ai_rewrite(text, api_key):
    if not api_key:
        return "⚠️ الرجاء وضع مفتاح API أولاً."
        
    try:
        genai.configure(api_key=api_key)
        
        # قائمة الموديلات التي سنجربها بالترتيب
        models = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
        
        # محاولة الاتصال بأول موديل متاح
        active_model = None
        for m in models:
            try:
                test_model = genai.GenerativeModel(m)
                # تجربة وهمية للتأكد من الموديل
                test_model.generate_content("test")
                active_model = m
                break
            except:
                continue
        
        if not active_model:
            return "❌ فشل العثور على موديل يعمل. تأكد من المفتاح."

        # التنفيذ الفعلي
        model = genai.GenerativeModel(active_model)
        response = model.generate_content(f"أعد صياغة هذا النص بأسلوب بشري طبيعي جداً:\n{text}")
        return response.text
        
    except Exception as e:
        return f"خطأ غير متوقع: {str(e)}"

# --- الواجهة ---
st.title("👻 Ghost Buster (النسخة المستقرة)")

# القائمة الجانبية للمفتاح
with st.sidebar:
    st.header("الإعدادات")
    # محاولة قراءة المفتاح من الأسرار، وإذا لم يوجد نطلب إدخاله يدوياً
    try:
        default_key = st.secrets["GEMINI_KEY"]
        key_status = "✅ المفتاح مربوط من السيرفر"
    except:
        default_key = ""
        key_status = "⚠️ المفتاح غير مربوط"
        
    st.info(key_status)
    
    # مربع إدخال احتياطي (في حال فشل الأسرار)
    user_key = st.text_input("مفتاح API (احتياطي):", value=default_key, type="password")

text_input = st.text_area("ضع النص هنا:", height=150)

col1, col2 = st.columns(2)

with col1:
    if st.button("🧹 تنظيف فقط", use_container_width=True):
        if text_input:
            final, count = clean_text_logic(text_input)
            st.success("تم التنظيف")
            st.metric("رموز محذوفة", count)
            st.code(final, language=None)
        else:
            st.warning("ادخل نصاً أولاً")

with col2:
    if st.button("✨ تنظيف + صياغة AI", type="primary", use_container_width=True):
        if text_input and user_key:
            # أولاً ننظف
            cleaned_draft, _ = clean_text_logic(text_input)
            
            with st.spinner("جاري الاتصال بـ Google AI..."):
                result = ai_rewrite(cleaned_draft, user_key)
                
            if "خطأ" in result or "فشل" in result:
                st.error(result)
            else:
                st.success("النتيجة النهائية:")
                st.write(result)
                st.code(result, language=None)
        elif not user_key:
            st.error("يجب توفر مفتاح API للعمل.")
        else:
            st.warning("ادخل نصاً أولاً")
