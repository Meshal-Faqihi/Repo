import streamlit as st
import unicodedata

# إعداد الصفحة
st.set_page_config(page_title="كاشف النصوص المخفية", page_icon="🕵️‍♂️", layout="centered")

def get_char_description(char):
    """
    دالة لترجمة الرموز المخفية إلى أسماء مقروءة
    """
    code = ord(char)
    if code == 0x200B: return "ZWSP" # مسافة صفرية
    if code == 0x200C: return "ZWNJ" # فاصل صفر
    if code == 0x200D: return "ZWDJ" # واصل صفر
    if code == 0x200E: return "LRM"  # علامة يسار-يمين
    if code == 0x200F: return "RLM"  # علامة يمين-يسار
    if code == 0xA0:   return "NBSP" # مسافة غير منقطعة
    return "HIDDEN"

def reveal_text(text):
    """
    دالة تقوم باستبدال الأحرف المخفية بنصوص حمراء واضحة
    """
    revealed_text = ""
    hidden_count = 0
    
    for char in text:
        category = unicodedata.category(char)
        # تحديد الأحرف المخفية وأحرف التحكم (باستثناء الأسطر والمسافات العادية)
        if category == 'Cf' or (category == 'Cc' and char not in ['\n', '\t', '\r']):
            # استبدال الحرف المخفي برمز أحمر
            symbol_name = get_char_description(char)
            revealed_text += f":red[**[{symbol_name}]**]"
            hidden_count += 1
        else:
            revealed_text += char
            
    return revealed_text, hidden_count

def clean_text(text):
    """
    دالة الحذف النهائي
    """
    cleaned_text = []
    for char in text:
        category = unicodedata.category(char)
        if not (category == 'Cf' or (category == 'Cc' and char not in ['\n', '\t', '\r'])):
            cleaned_text.append(char)
    return "".join(cleaned_text)

# --- واجهة المستخدم ---

st.title("🕵️‍♂️ كاشف النصوص والرموز المخفية")
st.markdown("هذه الأداة تكشف لك ما لا تراه عينك في النصوص المنسوخة من الذكاء الاصطناعي أو المواقع.")

# 1. منطقة الإدخال
text_input = st.text_area("1️⃣ الصق النص المشكوك فيه هنا:", height=150, placeholder="الصق النص هنا...")

if text_input:
    # 2. زر الفحص
    st.markdown("---")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        check_btn = st.button("🔍 افحص النص (أين الأحرف المخفية؟)", use_container_width=True)
    
    # مكان عرض النتائج
    if check_btn:
        revealed, count = reveal_text(text_input)
        
        if count > 0:
            st.warning(f"⚠️ تم اكتشاف **{count}** أحرف أو رموز مخفية!", icon="⚠️")
            st.markdown("### 👀 النص كما يراه الحاسوب:")
            st.caption("الرموز الملونة بالأحمر هي بيانات مخفية تم كشفها:")
            
            # عرض النص مع التلوين (نستخدم حاوية لتوضيح النص)
            st.markdown(
                f"""
                <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 1px solid #ff4b4b; line-height: 2;">
                {revealed}
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            st.markdown("---")
            st.markdown("### هل تريد تنظيفه؟")
            
            # زر التنظيف يظهر فقط عند وجود مشكلة
            if st.button("🧹 نعم، نظف النص الآن"):
                final_clean = clean_text(text_input)
                st.success("✅ تم تنظيف النص بنجاح!")
                st.text_area("النص النظيف (جاهز للنسخ):", value=final_clean, height=150)
                
        else:
            st.success("✅ النص سليم! لا توجد أي أحرف مخفية.", icon="🛡️")

# تذييل بسيط
st.markdown("---")
st.caption("يعمل محلياً ولا يحفظ بياناتك.")
