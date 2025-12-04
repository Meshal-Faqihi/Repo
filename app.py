import streamlit as st
import unicodedata

# إعداد الصفحة
st.set_page_config(page_title="كاشف النصوص المتقدم", page_icon="🛡️", layout="centered")

# قائمة صريحة بأكواد الرموز المخفية الشائعة لضمان حذفها
INVISIBLE_CHARS = {
    0x200B, # Zero Width Space
    0x200C, # Zero Width Non-Joiner
    0x200D, # Zero Width Joiner
    0x200E, # Left-to-Right Mark
    0x200F, # Right-to-Left Mark
    0xFEFF, # Byte Order Mark
    0x202A, 0x202B, 0x202C, 0x202D, 0x202E, # Directional Formatting
    0x2060, 0x2061, 0x2062, 0x2063, 0x2064, # Invisible Separators
}

def is_hidden(char):
    """
    دالة دقيقة جداً لتحديد هل الحرف مخفي أم لا
    """
    code = ord(char)
    
    # 1. هل هو في قائمتنا المحظورة الصريحة؟
    if code in INVISIBLE_CHARS:
        return True
    
    # 2. هل هو ضمن نطاقات اليونيكود الخاصة بالتنسيق؟
    category = unicodedata.category(char)
    if category == 'Cf': return True
    if category == 'Cc' and char not in ['\n', '\t', '\r']: return True
    
    return False

def get_char_name(char):
    code = ord(char)
    if code == 0x200B: return "ZWSP"
    if code == 0x200E: return "LRM"
    if code == 0x200F: return "RLM"
    return hex(code)

# --- الواجهة ---
st.title("🛡️ منظف النصوص العميق")
st.markdown("هذا الإصدار يستخدم فحصاً دقيقاً (Deep Scan) لكشف ما تخفيه المتصفحات.")

text_input = st.text_area("الصق النص هنا:", height=150)

# ميزة جديدة: إنشاء نص ملغم للتجربة
if st.checkbox("أريد تجربة نص ملغم (للتأكد من عمل الأداة)"):
    # ننشئ نصاً برمجياً يحتوي على رموز حقيقية لا يحذفها المتصفح
    dirty_text = "تجربة" + "\u200b" + " " + "حقيقية" + "\u200f"
    st.info("انسخ هذا النص الموجود في الصندوق بالأسفل (يحتوي على ZWSP و RLM):")
    st.code(dirty_text, language=None)

if st.button("افحص ونظف النص"):
    if text_input:
        cleaned_chars = []
        removed_log = []
        
        for char in text_input:
            if is_hidden(char):
                removed_log.append(get_char_name(char))
            else:
                cleaned_chars.append(char)
                
        cleaned_text = "".join(cleaned_chars)
        removed_count = len(removed_log)
        
        if removed_count > 0:
            st.error(f"⚠️ تم العثور على {removed_count} رمز مخفي وتم حذفهم!", icon="🗑️")
            
            # عرض التفاصيل
            st.write("### 🔍 تقرير الحذف:")
            st.json(removed_log) # يعرض قائمة بما تم حذفه
            
            st.success("✅ النص النظيف:")
            st.text_area("انسخ النص النظيف من هنا:", value=cleaned_text, height=150)
        else:
            st.success("✅ النص نظيف تماماً (أو أن المتصفح قام بتنظيفه تلقائياً عند اللصق).")
            
            # أداة المطورين للتأكد
            with st.expander("🛠️ عرض الكود الخام (للمبرمجين)"):
                hex_view = " ".join([hex(ord(c)) for c in text_input])
                st.text(hex_view)
                st.caption("ابحث عن أكواد مثل 0x200b هنا. إذا لم تجدها، فالنص الذي وصل للموقع كان نظيفاً أصلاً.")
    else:
        st.warning("الرجاء لصق نص أولاً.")
