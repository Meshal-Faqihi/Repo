import streamlit as st
import google.generativeai as genai
import importlib.metadata

st.set_page_config(page_title="Debug Mode", layout="wide")

st.title("🛠️ فحص حالة الاتصال (Debug)")

# 1. طباعة إصدار المكتبة (مهم جداً لمعرفة هل التحديث تم أم لا)
try:
    version = importlib.metadata.version("google-generativeai")
    st.info(f"📦 إصدار مكتبة جوجل الحالي: {version}")
    
    # تحذير إذا كانت المكتبة قديمة
    if version < "0.7.0":
        st.error("⚠️ المكتبة قديمة جداً! المشكلة في ملف requirements.txt لم يتم تطبيقه.")
    else:
        st.success("✅ إصدار المكتبة حديث وممتاز.")
except:
    st.warning("تعذر قراءة الإصدار.")

# 2. فحص المفتاح والنماذج
user_key = st.text_input("ضع مفتاح API هنا للفحص:", type="password")

if st.button("🚀 افحص المفتاح والنماذج"):
    if not user_key:
        st.error("الرجاء وضع المفتاح.")
    else:
        try:
            genai.configure(api_key=user_key)
            
            st.write("جاري الاتصال بسيرفرات جوجل...")
            
            # محاولة جلب النماذج المتاحة لهذا المفتاح
            models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    models.append(m.name)
            
            if models:
                st.success(f"🎉 نجح الاتصال! المفتاح سليم.")
                st.write("### النماذج التي يدعمها مفتاحك حالياً:")
                st.code("\n".join(models))
                st.balloons()
            else:
                st.warning("المفتاح يعمل لكن لم نجد نماذج تدعم النصوص! (غريب)")
                
        except Exception as e:
            st.error("❌ فشل الاتصال. تفاصيل الخطأ:")
            st.code(str(e))
            
            if "400" in str(e) or "INVALID_ARGUMENT" in str(e):
                st.warning("💡 هذا يعني غالباً أن المفتاح منسوخ بشكل خاطئ أو يحتوي مسافات.")
