import streamlit as st
from src.utils import extract_text_from_pdf, create_gauge_chart
from src.gemini_engine import ATSEngine
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="ATS Pro", layout="wide")

st.markdown("""
<style>
    .stButton>button {width: 100%; border-radius: 5px; background: #4f46e5; color: white;}
</style>
""", unsafe_allow_html=True)

def main():
    st.sidebar.title("Configuration")
    
    # 1. API Key Setup
    env_key = os.getenv("GOOGLE_API_KEY")
    api_key = env_key if env_key else st.sidebar.text_input("Gemini API Key", type="password")
    
    if api_key:
        st.sidebar.success(f"Key Loaded (...{api_key[-4:]})")
        
        # 2. Model Selector (The Fix!)
        # Automatically fetch models that WORK with your key
        with st.spinner("Fetching available models..."):
            available_models = ATSEngine.get_available_models(api_key)
            
        if available_models:
            # Default to 1.5-flash if available, else first one
            default_ix = 0
            for i, m in enumerate(available_models):
                if 'gemini-1.5-flash' in m and 'exp' not in m:
                    default_ix = i
                    break
            
            selected_model = st.sidebar.selectbox("Select Model", available_models, index=default_ix)
        else:
            st.sidebar.error("Could not fetch models. Check Key.")
            selected_model = "models/gemini-1.5-flash"
    else:
        st.sidebar.warning("Please enter API Key to see models.")
        selected_model = "models/gemini-1.5-flash"

    st.title("🚀 Smart ATS Analyzer")
    col1, col2 = st.columns(2)
    jd_text = col1.text_area("Job Description", height=300)
    uploaded_file = col2.file_uploader("Upload Resume", type="pdf")

    if st.button("Analyze Resume"):
        if not jd_text or not uploaded_file:
            st.warning("Please provide both JD and Resume!")
            return
        
        with st.spinner(f"Analyzing with {selected_model}..."):
            text = extract_text_from_pdf(uploaded_file)
            
            # Pass selected model to engine
            engine = ATSEngine(api_key, model_name=selected_model)
            
            result = engine.analyze_resume(text, jd_text)
            
            if "error" in result:
                st.error(result["error"])
            else:
                st.divider()
                c1, c2 = st.columns([1, 2])
                c1.plotly_chart(create_gauge_chart(result.get('match_score', 0)), use_container_width=True)
                c2.success("Analysis Complete")
                c2.write(f"**Summary:** {result.get('summary')}")
                st.write(f"**Missing Keywords:** {', '.join(result.get('missing_keywords', []))}")

if __name__ == "__main__":
    main()
