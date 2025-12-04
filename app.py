import streamlit as st
import unicodedata

# إعدادات الصفحة العامة
st.set_page_config(
    page_title="Deep Clean | منظف النصوص",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS  ---
st.markdown("""
<style>
    .big-font { font-size:20px !important; font-weight: bold; }
    .stTextArea textarea { font-family: 'Courier New', monospace; }
    .highlight { background-color: #ff4b4b40; border-radius: 4px; padding: 0 4px; font-weight: bold; color: #ff4b4b; }
</style>
""", unsafe_allow_html=True)

# --- (Logic) ---
INVISIBLE_CHARS = {
    0x200B, 0x200C, 0x200D, 0x200E, 0x200F, 0xFEFF,
    0x202A, 0x202B, 0x202C, 0x202D, 0x202E,
    0x2060, 0x2061, 0x2062, 0x2063, 0x2064
}

def is_hidden(char):
    code = ord(char)
    if code in INVISIBLE_CHARS: return True
    category = unicodedata.category(char)
    if category == 'Cf': return True
    if category == 'Cc' and char not in ['\n', '\t', '\r']: return True
    return False

def get_char_label(char):
    code = ord(char)
    labels = {
        0x200B: "ZWSP", 0x200E: "LRM", 0x200F: "RLM",
        0x200C: "ZWNJ", 0x200D: "ZWJ"
    }
    return labels.get(code, "HIDDEN")

def process_text(text):
    clean_chars = []
    visual_html = ""
    removed_stats = {}
    total_removed = 0

    for char in text:
        if is_hidden(char):
            # للإحصائيات
            label = get_char_label(char)
            removed_stats[label] = removed_stats.get(label, 0) + 1
            total_removed += 1
            # للعرض البصري (تمييز الحذف)
            visual_html += f'<span class="highlight" title="تم حذف {label}">[{label}]</span>'
        else:
            clean_chars.append(char)
            # تعقيم النص للعرض في HTML لتجنب مشاكل XSS
            safe_char = char.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
            visual_html += safe_char

    return "".join(clean_chars), visual_html, total_removed, removed_stats

# --- (Sidebar) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2092/2092663.png", width=80)
    st.title("Deep Clean Tool")
    st.markdown("---")
    st.markdown("""
    **عن الأداة:**
    هذه الأداة تقوم بتحليل النصوص بعمق لإزالة:
    - 🕵️‍♂️ الأحرف غير المرئية (Zero-width spaces).
    - 🔄 علامات توجيه النص (LRM/RLM).
    - 🧹 بقايا التنسيق المنسوخة.
    """)
    st.markdown("---")
    st.info("💡 **نصيحة:** استخدم هذه الأداة قبل نشر المنشورات في وسائل التواصل أو إرسال الأكواد البرمجية.")
    
    # خيار توليد نص للتجربة 
    if st.button("توليد نص ملغّم للتجربة"):
        st.session_state['input_text'] = "هذا النص​ يبدو طبيعياً جداً،‏ لكنه في الحقيقة​ يحتوي على‎ رموز مخفية لا تراها عينك!"

# --- (Main UI) ---
st.title("🛡️ كاشف ومنظف النصوص الاحترافي")
st.caption("احمِ خصوصيتك وتخلص من العلامات المائية المخفية في النصوص.")

# منطقة الإدخال
if 'input_text' not in st.session_state:
    st.session_state['input_text'] = ""

text_input = st.text_area(
    "1️⃣ الصق النص المراد فحصه هنا:",
    value=st.session_state['input_text'],
    height=150,
    placeholder="الصق النص هنا..."
)

# زر التنفيذ 
if st.button("🚀 فحص وتنظيف النص", type="primary", use_container_width=True):
    if text_input:
        clean_text, visual_html, count, stats = process_text(text_input)
        
        st.markdown("---")
        
        if count > 0:
            # عرض الإحصائيات
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("حالة النص", "ملوث ⚠️", delta_color="inverse")
            with c2: st.metric("عدد الأحرف المخفية", f"{count}", delta="-"+str(count))
            with c3: st.metric("الطول الجديد", len(clean_text))
            
            st.markdown("### 📊 النتائج التفصيلية")
            
            # استخدام التبويبات لعرض النتائج
            tab1, tab2, tab3 = st.tabs(["👁️ المعاينة البصرية", "✅ النص النظيف", "📈 التقرير التقني"])
            
            with tab1:
                st.markdown("المناطق الملونة بالأحمر هي ما تم حذفه:")
                st.markdown(f'<div style="background:white; color:black; padding:15px; border-radius:10px; border:1px solid #ddd; direction:rtl;">{visual_html}</div>', unsafe_allow_html=True)
                
            with tab2:
                st.success("تم التنظيف بنجاح! يمكنك النسخ الآن:")
                st.text_area("النص النهائي:", value=clean_text, height=150, label_visibility="collapsed")
            
            with tab3:
                st.write("أنواع الرموز التي تم كشفها:")
                st.json(stats)
                
        else:
            st.success("✅ النص سليم ونظيف تماماً! لا توجد أي بيانات مخفية.", icon="🎉")
            st.balloons()
            
    else:
        st.warning("الرجاء إدخال نص أولاً للبدء.")

