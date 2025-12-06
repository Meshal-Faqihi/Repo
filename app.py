import streamlit as st
import unicodedata
import re
import html
import google.generativeai as genai

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="Ghost Buster Forensic",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS عالي التباين لكشف العيوب ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; }
    
    /* صندوق النتائج الدقيق */
    .forensic-box {
        font-family: 'Courier New', monospace;
        background-color: #0e1117;
        border: 1px solid #333;
        padding: 15px;
        border-radius: 5px;
        line-height: 2.5;
        direction: rtl;
        font-size: 16px;
    }

    /* تمييز الأخطاء بألوان فاقعة */
    .hidden-char { 
        background-color: #ff0000; color: white; 
        padding: 2px 6px; border-radius: 4px; 
        font-weight: bold; border: 2px solid white;
        box-shadow: 0 0 5px red;
    }
    
    .suspicious-space {
        background-color: #00ffff; color: black;
        padding: 2px 4px; border-radius: 3px;
        font-weight: bold; border: 1px dashed black;
    }
    
    .hex-view {
        font-family: monospace;
        font-size: 14px;
        color: #00ff00;
        background-color: #000;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. محرك الفحص الجنائي (Forensic Engine) ---

# قائمة أوسع تشمل كل أنواع الفراغات وعلامات التنسيق
BLACKLIST = {
    # Zero Width Characters (الأخطر)
    0x200B: "ZWSP", 0x200C: "ZWNJ", 0x200D: "ZWJ", 0xFEFF: "BOM",
    # Direction Marks (علامات التوجيه)
    0x200E: "LRM", 0x200F: "RLM", 0x061C: "ALM",
    # Embeddings
    0x202A: "LRE", 0x202B: "RLE", 0x202C: "PDF", 0x202D: "LRO", 0x202E: "RLO",
    # Separators
    0x2060: "WJ", 0x2061: "FA", 0x2062: "IT", 0x2063: "IS",
    # Tag Characters (Rare)
    0xE0001: "TAG", 
}

# قائمة الفراغات المشبوهة (ليست مسافة عادية 0x20)
SUSPICIOUS_SPACES = {
    0x00A0: "NBSP", # الأشهر في المشاكل
    0x2000: "EnQuad", 0x2001: "EmQuad", 0x2002: "EnSp", 0x2003: "EmSp",
    0x2004: "3/M", 0x2005: "4/M", 0x2006: "6/M", 0x2007: "FigSp",
    0x2008: "PuncSp", 0x2009: "ThinSp", 0x200A: "HairSp", 0x202F: "NNBSP",
    0x205F: "MMSP", 0x3000: "IdSp"
}

def forensic_scan(text):
    visual_html = ""
    stats = {"hidden": 0, "suspicious_spaces": 0}
    clean_text = []
    
    for char in text:
        code = ord(char)
        
        # 1. فحص الرموز المخفية (القائمة السوداء)
        if code in BLACKLIST or (unicodedata.category(char) in ['Cf', 'Cc'] and code not in [10, 13, 9]):
            stats["hidden"] += 1
            label = BLACKLIST.get(code, "HIDDEN")
            visual_html += f'<span class="hidden-char" title="رمز مخفي: {label} (Code: {hex(code)})">[{label}]</span>'
            # لا نضيفه للنص النظيف
            
        # 2. فحص المسافات المشبوهة
        elif code in SUSPICIOUS_SPACES:
            stats["suspicious_spaces"] += 1
            label = SUSPICIOUS_SPACES.get(code, "SPACE")
            visual_html += f'<span class="suspicious-space" title="مسافة غير قياسية: {label} (Code: {hex(code)})">[{label}]</span>'
            clean_text.append(" ") # استبدالها بمسافة عادية آمنة
            
        # 3. حرف سليم
        else:
            safe_char = html.escape(char).replace("\n", "<br>").replace("\t", "&emsp;")
            visual_html += safe_char
            clean_text.append(char)
            
    return "".join(clean_text), visual_html, stats

def generate_hex_dump(text):
    # تحويل النص إلى سلسلة من الأكواد لفحصه يدوياً
    hex_output = []
    for char in text:
        code = ord(char)
        desc = "Char"
        if code in BLACKLIST: desc = "🔴 HIDDEN"
        elif code in SUSPICIOUS_SPACES: desc = "🟡 SUSPICIOUS"
        elif code == 32: desc = "Space"
        
        hex_output.append(f"U+{code:04X} : {char!r} ({desc})")
    return "\n".join(hex_output)

# --- 4. الواجهة ---
st.markdown("<h1>🔬 Ghost Buster <span style='color:red'>Forensic</span></h1>", unsafe_allow_html=True)
st.warning("هذا الوضع يكشف البنية التحتية للنص (الأكواد الرقمية) لتجاوز خداع المتصفحات.")

text_input = st.text_area("ضع النص هنا:", height=200, placeholder="ألصق النص المشبوه...")

if st.button("🚀 فحص جنائي عميق (Deep Scan)", type="primary", use_container_width=True):
    if text_input:
        clean_text, visual_html, stats = forensic_scan(text_input)
        
        # عرض العدادات
        c1, c2, c3 = st.columns(3)
        c1.metric("رموز مخفية (Hidden)", stats['hidden'], delta="خطر" if stats['hidden']>0 else "سليم", delta_color="inverse")
        c2.metric("مسافات مشبوهة", stats['suspicious_spaces'], delta="تنبيه" if stats['suspicious_spaces']>0 else "سليم", delta_color="inverse")
        c3.metric("طول النص", len(text_input))
        
        st.markdown("---")
        
        tab1, tab2, tab3 = st.tabs(["👁️ كشف العيوب (Visual)", "🔢 تحليل الأكواد (Hex Dump)", "✅ النص النظيف"])
        
        with tab1:
            st.markdown("أي شيء ملون هنا هو عنصر غير مرئي تم كشفه:")
            st.markdown(f'<div class="forensic-box">{visual_html}</div>', unsafe_allow_html=True)
            
        with tab2:
            st.info("هذا الجدول يظهر لك حقيقة كل حرف كما يراه الكمبيوتر:")
            st.text_area("Hex Dump", value=generate_hex_dump(text_input), height=300)
            
        with tab3:
            st.success("نسخة آمنة تماماً (تم استبدال المسافات المشبوهة وحذف الرموز المخفية):")
            st.code(clean_text, language=None)
            
    else:
        st.error("الرجاء إدخال نص.")
