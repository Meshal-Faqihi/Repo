import streamlit as st
import unicodedata
import re
import html

# --- 1. إعدادات الصفحة المتقدمة ---
st.set_page_config(
    page_title="Ghost Buster | كاشف النصوص العميق",
    page_icon="👻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS احترافي (Dark Mode Friendly) ---
st.markdown("""
<style>
    /* تحسين الخطوط */
    .stTextArea textarea { font-family: 'Courier New', monospace; line-height: 1.6; }
    
    /* صناديق النتائج */
    .result-box {
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #444;
        background-color: #1e1e1e;
        color: #e0e0e0;
        font-family: monospace;
        white-space: pre-wrap;
        direction: rtl; /* لدعم العربية */
    }
    
    /* تمييز الحذف */
    .removed-tag {
        background-color: rgba(255, 75, 75, 0.3);
        color: #ff4b4b;
        padding: 0 4px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.8em;
        border: 1px solid #ff4b4b;
    }
    
    /* الفوتر */
    .footer { text-align: center; color: #666; font-size: 12px; margin-top: 50px; }
</style>
""", unsafe_allow_html=True)

# --- 3. محرك المعالجة (The Core Engine) ---

# قائمة الرموز المحظورة الصريحة
BLACKLIST_CHARS = {
    0x200B, 0x200C, 0x200D, 0x200E, 0x200F, 0xFEFF, # Zero Width & Marks
    0x202A, 0x202B, 0x202C, 0x202D, 0x202E, # Directional Overrides
    0x2060, 0x2061, 0x2062, 0x2063, 0x2064, # Invisible Separators
    0x00A0, # Non-breaking space (يسبب مشاكل برمجية)
}

def identify_char(char):
    """تحديد نوع الحرف المشبوه بدقة"""
    code = ord(char)
    if code == 0x200B: return "ZWSP"
    if code == 0x200E: return "LRM"
    if code == 0x200F: return "RLM"
    if code == 0x00A0: return "NBSP"
    if code == 0xFEFF: return "BOM"
    return "HIDDEN"

def advanced_cleaning(text, remove_markdown=False, normalize_unicode=True):
    """
    الدالة الشاملة للتنظيف
    """
    clean_chars = []
    visual_report = ""
    stats = {"hidden": 0, "markdown": 0, "normalized": 0}
    
    # 1. مرحلة التطبيع (Normalization)
    # تحويل الأحرف "الشبيهة" إلى أصلها القياسي
    if normalize_unicode:
        # NFKC يوحد الأشكال المختلفة للأحرف
        text = unicodedata.normalize('NFKC', text)

    # 2. معالجة النص حرفاً حرفاً
    for char in text:
        code = ord(char)
        category = unicodedata.category(char)
        
        # شرط الحذف: هل هو في القائمة السوداء أو تنسيق غير مرئي؟
        is_bad = (code in BLACKLIST_CHARS) or (category in ['Cf', 'Cc'] and char not in ['\n', '\t', '\r'])
        
        if is_bad:
            label = identify_char(char)
            stats["hidden"] += 1
            # إضافة وسم أحمر للعرض
            visual_report += f'<span class="removed-tag" title="تم حذف {label}">[{label}]</span>'
        else:
            clean_chars.append(char)
            # تعقيم HTML للعرض
            safe_char = html.escape(char).replace("\n", "<br>")
            visual_report += safe_char

    # تجميع النص الأولي
    cleaned_string = "".join(clean_chars)

    # 3. إزالة آثار الذكاء الاصطناعي (Markdown)
    if remove_markdown:
        # إزالة العريض **text**
        new_text = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned_string)
        if new_text != cleaned_string: stats["markdown"] += 1
        cleaned_string = new_text
        
        # إزالة العناوين ## 
        new_text = re.sub(r'^#{1,6}\s+', '', cleaned_string, flags=re.MULTILINE)
        if new_text != cleaned_string: stats["markdown"] += 1
        cleaned_string = new_text
        
        # إزالة الكود `code`
        cleaned_string = re.sub(r'`(.*?)`', r'\1', cleaned_string)

    return cleaned_string, visual_report, stats

# --- 4. واجهة الشريط الجانبي (Sidebar) ---
with st.sidebar:
    st.title("⚙️ إعدادات التنظيف")
    
    st.markdown("### مستوى الصرامة")
    opt_markdown = st.toggle("إزالة تنسيقات AI (Markdown)", value=True, help="يزيل النجوم ** والعناوين التي يضعها ChatGPT")
    opt_normalize = st.toggle("تطبيع الأحرف (Normalization)", value=True, help="يحول الأحرف الغريبة والمزخرفة إلى أحرف قياسية")
    
    st.markdown("---")
    st.markdown("### 🧪 منطقة التجارب")
    if st.button("توليد نص خبيث للتجربة"):
        # نص يحتوي: مسافات صفرية + Markdown + مسافة غير منقطعة
        st.session_state['input_text'] = "**تحذير:**" + "\u200b" + " هذا النص " + "\u00A0" + "ملغم" + "\u200f" + "!"

# --- 5. الواجهة الرئيسية (Main UI) ---
st.title("👻 Ghost Buster | قاهر النصوص الخفية")
st.markdown("""
<div style="background-color:#262730; padding:10px; border-radius:5px; border-left: 5px solid #ff4b4b;">
    هذه الأداة تكشف <b>البصمات الرقمية</b> التي تتركها نماذج الذكاء الاصطناعي والمواقع، وتجعلك تنسخ نصاً "نظيفاً برمجياً".
</div>
""", unsafe_allow_html=True)

if 'input_text' not in st.session_state: st.session_state['input_text'] = ""

col_input, col_action = st.columns([4, 1])
with col_input:
    text_input = st.text_area("النص الأصلي:", value=st.session_state['input_text'], height=150, placeholder="الصق النص المشكوك فيه هنا...")

with col_action:
    st.write("##") # Spacer
    process_btn = st.button("🔍 فحص\nشامل", type="primary", use_container_width=True)

# --- 6. عرض النتائج ---
if process_btn and text_input:
    # المعالجة
    final_text, visual_html, stats = advanced_cleaning(text_input, opt_markdown, opt_normalize)
    total_issues = stats["hidden"] + stats["markdown"]

    st.markdown("---")
    
    # لوحة القيادة (Dashboard)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        status_color = "inverse" if total_issues > 0 else "normal"
        status_text = "⚠️ ملوث" if total_issues > 0 else "✅ نظيف"
        st.metric("الحالة الأمنية", status_text, delta_color=status_color)
    with c2: st.metric("أحرف مخفية", stats["hidden"], delta="-removed")
    with c3: st.metric("تنسيقات AI", stats["markdown"], delta="-stripped")
    with c4: st.metric("عدد الأحرف النهائي", len(final_text))

    # منطقة التفاصيل (Tabs)
    tab1, tab2, tab3 = st.tabs(["🔴 كشف المستور (X-Ray)", "✨ النص النظيف (للنسخ)", "💻 الكود الخام (Hex)"])

    with tab1:
        st.markdown("##### ما تراه الأداة ولا تراه عينك:")
        if total_issues == 0:
            st.success("النص سليم 100% ولا يحتوي على أي شوائب.")
        else:
            st.caption("الرموز الحمراء هي بيانات وصفية تم كشفها:")
            st.markdown(f'<div class="result-box">{visual_html}</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown("##### النسخة الآمنة الجاهزة للاستخدام:")
        st.text_area("انسخ من هنا:", value=final_text, height=200, label_visibility="collapsed")
        # زر نسخ مساعد
        st.caption("اضغط Ctrl+A ثم Ctrl+C لنسخ النص.")

    with tab3:
        st.markdown("##### تحليل البيانات الخام (Hex Dump):")
        # عرض الكود الست عشري للمحترفين
        hex_data = " ".join([f"{ord(c):04X}" for c in text_input[:100]]) + "..."
        st.code(hex_data, language="text")
        st.caption("هذا يعرض أول 100 حرف بصيغة Unicode Hex.")

st.markdown("---")
st.markdown('<div class="footer">Developed for Security Research • Runs Locally in Memory</div>', unsafe_allow_html=True)
