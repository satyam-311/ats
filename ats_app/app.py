import streamlit as st
from src.utils import extract_text_from_pdf, create_gauge_chart
from src.gemini_engine import ATSEngine
import os
from dotenv import load_dotenv

load_dotenv()

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
    st.sidebar.title("Configuration")
    env_key = os.getenv("GOOGLE_API_KEY")
    api_key = env_key if env_key else st.sidebar.text_input("Gemini API Key", type="password")
    
    st.title("🚀 Smart ATS Analyzer")
    st.write("Optimize your resume for Applicant Tracking Systems.")
    
    col1, col2 = st.columns(2)
    jd_text = col1.text_area("Job Description", height=250, placeholder="Paste JD here...")
    uploaded_file = col2.file_uploader("Upload Resume (PDF)", type="pdf")

    if st.button("Analyze Resume"):
        if not jd_text or not uploaded_file:
            st.warning("Please provide both Job Description and Resume.")
            return
        
        with st.spinner("Initializing AI & Analyzing..."):
            text = extract_text_from_pdf(uploaded_file)
            
            # Initialize Engine
            engine = ATSEngine(api_key)
            
            # Show which model was selected in sidebar (for debugging)
            st.sidebar.info(f"Using Model: {engine.model_name}")
            
            result = engine.analyze_resume(text, jd_text)
            
            if "error" in result:
                st.error(result["error"])
            else:
                # --- RESULTS SECTION ---
                st.divider()
                
                # 1. Gauge Chart & Verdict
                g_col1, g_col2 = st.columns([1, 2])
                with g_col1:
                    st.plotly_chart(create_gauge_chart(result.get('match_score', 0)), use_container_width=True)
                
                with g_col2:
                    st.subheader("ATS Prediction")
                    
                    # Colored Banner for Verdict
                    verdict = result.get('verdict', 'Unknown')
                    color = "green" if "Excellent" in verdict or "Good" in verdict else "orange" if "Average" in verdict else "red"
                    st.markdown(f"<div style='background-color: {color}; padding: 10px; border-radius: 5px; color: white; text-align: center; font-weight: bold;'>{verdict}</div>", unsafe_allow_html=True)
                    
                    st.write("")
                    # Metrics Row
                    m1, m2 = st.columns(2)
                    m1.metric("Readability", result.get('readability', 'N/A'))
                    m2.metric("Keyword Match", f"{result.get('match_score')}%")

                # 2. Analysis Details
                st.subheader("📝 Profile Analysis")
                st.info(result.get('summary'))
                
                st.write("### 🚨 Missing Keywords")
                st.write(", ".join(result.get('missing_keywords', [])))
                
                # 3. Download Button
                report_text = f"""
ATS ANALYSIS REPORT
-------------------
Job Description: {jd_text[:50]}...
Match Score: {result.get('match_score')}%
Verdict: {result.get('verdict')}
Readability: {result.get('readability')}

Missing Keywords:
{', '.join(result.get('missing_keywords', []))}

Summary:
{result.get('summary')}
                """
                st.download_button(
                    label="📥 Download Full Report",
                    data=report_text,
                    file_name="ats_report.txt",
                    mime="text/plain"
                )

if __name__ == "__main__":
    main()
