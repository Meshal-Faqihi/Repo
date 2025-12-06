import streamlit as st
import unicodedata
import re
import html
import google.generativeai as genai

# --- 1. Page Config ---
st.set_page_config(
    page_title="Ghost Buster Forensic",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; }
    
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
    
    .hidden-char { 
        background-color: #ff0000; color: white; 
        padding: 0 5px; border-radius: 3px; 
        font-weight: bold; border: 1px solid white;
        box-shadow: 0 0 5px rgba(255, 0, 0, 0.5);
    }
    
    .suspicious-space {
        background-color: #00ffff; color: black;
        padding: 0 3px; border-radius: 3px;
        font-weight: bold; border: 1px dashed black;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. Forensic Logic ---
BLACKLIST = {
    0x200B: "ZWSP", 0x200C: "ZWNJ", 0x200D: "ZWJ", 0xFEFF: "BOM",
    0x200E: "LRM", 0x200F: "RLM", 0x061C: "ALM",
    0x202A: "LRE", 0x202B: "RLE", 0x202C: "PDF", 0x202D: "LRO", 0x202E: "RLO",
    0x2060: "WJ", 0x2061: "FA", 0x2062: "IT", 0x2063: "IS",
}

SUSPICIOUS_SPACES = {
    0x00A0: "NBSP", # The most common hidden space in resumes/AI text
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
        
        # 1. Check for HIDDEN characters
        if code in BLACKLIST or (unicodedata.category(char) in ['Cf', 'Cc'] and code not in [10, 13, 9]):
            stats["hidden"] += 1
            label = BLACKLIST.get(code, "HIDDEN")
            visual_html += f'<span class="hidden-char" title="Hidden: {label} (U+{code:04X})">[{label}]</span>'
            
        # 2. Check for SUSPICIOUS spaces (like NBSP)
        elif code in SUSPICIOUS_SPACES:
            stats["suspicious_spaces"] += 1
            label = SUSPICIOUS_SPACES.get(code, "SPACE")
            visual_html += f'<span class="suspicious-space" title="Suspicious Space: {label} (U+{code:04X})">[{label}]</span>'
            clean_text.append(" ") # Replace with normal space
            
        # 3. Normal characters
        else:
            safe_char = html.escape(char).replace("\n", "<br>").replace("\t", "&emsp;")
            visual_html += safe_char
            clean_text.append(char)
            
    return "".join(clean_text), visual_html, stats

def generate_hex_dump(text):
    hex_output = []
    for char in text:
        code = ord(char)
        desc = "Char"
        if code in BLACKLIST: desc = "🔴 HIDDEN"
        elif code in SUSPICIOUS_SPACES: desc = "🟡 SUSPICIOUS"
        elif code == 32: desc = "Space" # Normal Space (0x20)
        
        hex_output.append(f"U+{code:04X} : {char!r} ({desc})")
    return "\n".join(hex_output)

# --- 4. UI ---
st.markdown("<h1>🔬 Ghost Buster <span style='color:red'>Forensic</span></h1>", unsafe_allow_html=True)

# File Uploader to bypass browser cleaning
uploaded_file = st.file_uploader("📂 الخيار الأفضل: ارفع ملف نصي (.txt, .md) لتجاوز تنظيف المتصفح", type=["txt", "md"])

if 'input_text' not in st.session_state: st.session_state['input_text'] = ""

if uploaded_file is not None:
    # Read file directly
    string_data = uploaded_file.read().decode("utf-8")
    st.session_state['input_text'] = string_data
    st.success("✅ تم قراءة الملف بنجاح! المتصفح لم يتدخل.")

text_input = st.text_area("أو الصق النص هنا (قد ينظفه المتصفح):", value=st.session_state['input_text'], height=200)

if st.button("🚀 فحص جنائي عميق (Deep Scan)", type="primary", use_container_width=True):
    if text_input:
        clean_text, visual_html, stats = forensic_scan(text_input)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("رموز مخفية (Hidden)", stats['hidden'], delta="خطر" if stats['hidden']>0 else "سليم", delta_color="inverse")
        c2.metric("مسافات مشبوهة", stats['suspicious_spaces'], delta="تنبيه" if stats['suspicious_spaces']>0 else "سليم", delta_color="inverse")
        c3.metric("حجم النص", f"{len(text_input)} chars")
        
        st.markdown("---")
        
        tab1, tab2, tab3 = st.tabs(["👁️ كشف العيوب (Visual)", "🔢 تحليل الأكواد (Hex Dump)", "✅ النص النظيف"])
        
        with tab1:
            st.markdown(f'<div class="forensic-box">{visual_html}</div>', unsafe_allow_html=True)
            
        with tab2:
            st.info("ابحث هنا عن U+00A0 (مسافة مشبوهة) أو U+200B (رمز مخفي). إذا وجدت U+0020 فهذا يعني مسافة سليمة.")
            st.text_area("Hex Dump", value=generate_hex_dump(text_input), height=400)
            
        with tab3:
            st.code(clean_text, language=None)
            
    else:
        st.warning("الرجاء إدخال نص أو رفع ملف.")
