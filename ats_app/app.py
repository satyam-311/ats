import streamlit as st
from src.utils import extract_text_from_pdf, create_gauge_chart
from src.gemini_engine import ATSEngine
import os
from pathlib import Path
from dotenv import load_dotenv

# Force load .env from the same directory as app.py (Fixes Local 404)
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

st.set_page_config(page_title="ATS Pro", layout="wide")

st.markdown("""
<style>
    .main {background-color: #0e1117;}
    .stButton>button {width: 100%; border-radius: 8px; background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%); color: white;}
    .metric-card {background-color: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #334155; text-align: center;}
    h1, h2, h3, p {color: #e2e8f0;}
</style>
""", unsafe_allow_html=True)

def main():
    # --- API KEY LOGIC ---
    api_key = None
    
    # 1. Cloud Secrets (Try-Except block prevents local crash)
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            api_key = st.secrets["GOOGLE_API_KEY"]
    except:
        pass
    
    # 2. Local .env
    if not api_key:
        api_key = os.getenv("GOOGLE_API_KEY")

    st.sidebar.title("Configuration")
    
    # 3. Sidebar Input
    if not api_key:
        api_key = st.sidebar.text_input("Gemini API Key", type="password")
        if not api_key:
            st.sidebar.warning("⚠️ Enter API Key")
    else:
        st.sidebar.success("✅ API Key Loaded")

    # --- MODEL SELECTOR (The Fix for 404) ---
    selected_model = "models/gemini-1.5-flash"
    if api_key:
        with st.spinner("Checking models..."):
            available_models = ATSEngine.get_available_models(api_key)
        
        if available_models:
            # Auto-select 1.5 Flash if available
            default_ix = 0
            for i, m in enumerate(available_models):
                if 'gemini-1.5-flash' in m:
                    default_ix = i
                    break
            selected_model = st.sidebar.selectbox("AI Model", available_models, index=default_ix)
        else:
            st.sidebar.error("Invalid API Key or No Models Found")

    st.title("🚀 Smart ATS Analyzer")
    col1, col2 = st.columns(2)
    jd_text = col1.text_area("Job Description", height=250)
    uploaded_file = col2.file_uploader("Upload Resume (PDF)", type="pdf")

    if st.button("Analyze Resume"):
        if not api_key or not uploaded_file or not jd_text:
            st.warning("Missing Inputs!")
            return
        
        with st.spinner(f"Analyzing with {selected_model}..."):
            text = extract_text_from_pdf(uploaded_file)
            engine = ATSEngine(api_key, selected_model)
            result = engine.analyze_resume(text, jd_text)
            
            if "error" in result:
                st.error(result["error"])
            else:
                st.divider()
                g1, g2 = st.columns([1, 2])
                with g1: st.plotly_chart(create_gauge_chart(result.get('match_score', 0)), use_container_width=True)
                with g2:
                    st.subheader("Verdict")
                    verdict = result.get('verdict', 'Unknown')
                    color = "green" if "Excellent" in verdict or "Good" in verdict else "orange" if "Average" in verdict else "red"
                    st.markdown(f"<div style='background-color: {color}; padding: 10px; border-radius: 5px; color: white; text-align: center; font-weight: bold;'>{verdict}</div>", unsafe_allow_html=True)
                    st.write(f"**Readability:** {result.get('readability')}")
                    st.write(f"**Missing:** {', '.join(result.get('missing_keywords', []))}")
                
                st.subheader("Summary")
                st.write(result.get('summary'))
                
                report = f"Match: {result.get('match_score')}%\nVerdict: {result.get('verdict')}\nMissing: {result.get('missing_keywords')}"
                st.download_button("📥 Download Report", report, "ats_report.txt")

if __name__ == "__main__":
    main()
