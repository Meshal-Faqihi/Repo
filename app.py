import streamlit as st
import unicodedata

def clean_text(text):
    
    cleaned_text = []
    removed_count = 0
    removed_details = []

    for char in text:
    
        category = unicodedata.category(char)
        
        if category == 'Cf' or (category == 'Cc' and char not in ['\n', '\t', '\r']):
            removed_count += 1
            removed_details.append(f"{hex(ord(char))}")
        else:
            cleaned_text.append(char)
            
    return "".join(cleaned_text), removed_count, removed_details

st.set_page_config(page_title="Text Sanitizer", page_icon="🧹")

st.title("🧹 Text Sanitizer & Metadata Remover")
st.markdown("أداة بسيطة لتنظيف النصوص من الأحرف غير المرئية (Invisible Characters) وبقايا التنسيق.")

user_input = st.text_area("الصق النص هنا:", height=200)

if st.button("نظّف النص (Clean Text)"):
    if user_input:
        cleaned, count, details = clean_text(user_input)
        
        st.success("تم تنظيف النص بنجاح!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("عدد الأحرف الأصلية", len(user_input))
        with col2:
            st.metric("أحرف مخفية تم حذفها", count)
            
        st.code(cleaned, language=None)
        
        if count > 0:
            with st.expander("عرض تفاصيل الأحرف المحذوفة"):
                st.write(f"رموز الأحرف التي تم حذفها: {', '.join(set(details))}")
    else:
        st.warning("الرجاء لصق نص أولاً.")

st.markdown("---")
st.caption("تم التطوير بواسطة [Mesh] باستخدام Python و Streamlit")