import os
from pathlib import Path

# Project Folder Name
project_name = "ats_app"

# ==============================================================================
# 1. FILE CONTENT DEFINITIONS
# ==============================================================================

requirements_txt = """streamlit
google-generativeai
python-dotenv
PyPDF2
plotly
"""

# SECURITY NOTE: Key yahan mat daalna. .env file mein daalna.
env_file = """GOOGLE_API_KEY=""
"""

gitignore_file = """
.env
venv/
__pycache__/
"""

utils_py = """import PyPDF2 as pdf
import plotly.graph_objects as go
import streamlit as st

def extract_text_from_pdf(uploaded_file):
    try:
        reader = pdf.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\\n"
        return text
    except Exception as e:
        return None

def create_gauge_chart(score):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Match Score"},
        number={'font': {'size': 50, 'color': "#00f2ff"}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "#2E86C1"},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "#333",
            'steps': [
                {'range': [0, 50], 'color': 'rgba(255, 0, 0, 0.3)'},
                {'range': [50, 75], 'color': 'rgba(255, 165, 0, 0.3)'},
                {'range': [75, 100], 'color': 'rgba(0, 255, 0, 0.3)'}
            ],
        }
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"}, height=300, margin=dict(l=20, r=20, t=50, b=20))
    return fig
"""

# UPDATED ENGINE: DYNAMICALLY FINDS WORKING MODEL
gemini_engine_py = """import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

load_dotenv()

class ATSEngine:
    def __init__(self, api_key=None):
        self.api_key = api_key if api_key else os.getenv("GOOGLE_API_KEY")
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # Automatically find a working model
            self.model_name = self._find_best_model()
            self.model = genai.GenerativeModel(self.model_name)

    def _find_best_model(self):
        try:
            print("🔍 Checking available models for your API Key...")
            all_models = list(genai.list_models())
            
            # Filter models that support generating text
            supported_models = [m.name for m in all_models if 'generateContent' in m.supported_generation_methods]
            print(f"✅ Available Models found: {supported_models}")
            
            # Priority 1: Gemini 1.5 Flash (Best for ATS)
            for m in supported_models:
                if 'gemini-1.5-flash' in m and 'latest' not in m: return m
            
            # Priority 2: Gemini 1.5 Pro
            for m in supported_models:
                if 'gemini-1.5-pro' in m and 'latest' not in m: return m
            
            # Priority 3: Gemini Pro (Older but reliable)
            for m in supported_models:
                if 'gemini-pro' in m: return m

            # Fallback: Just take the first one available
            if supported_models:
                return supported_models[0]
            
            # Absolute Fallback (If list fails entirely)
            return 'models/gemini-1.5-flash'
            
        except Exception as e:
            print(f"⚠️ Error listing models: {e}")
            return 'models/gemini-1.5-flash'

    def analyze_resume(self, resume_text, jd_text):
        if not self.api_key:
            return {"error": "API Key is missing. Check .env file."}
            
        prompt = f\"\"\"
        Act as an expert ATS (Applicant Tracking System) Scanner.
        
        JOB DESCRIPTION:
        {jd_text}
        
        RESUME:
        {resume_text}
        
        TASK:
        1. Calculate a match percentage (0-100).
        2. Determine Readability level (Options: Simple, Standard, Technical).
        3. Give a Verdict (Options: Excellent Match, Good Match, Average Match, Poor Match).
        4. Identify missing keywords.
        5. Provide a professional summary.
        
        OUTPUT FORMAT (Strict JSON):
        {{
            "match_score": 85,
            "readability": "Standard",
            "verdict": "Good Match",
            "missing_keywords": ["Skill1", "Skill2"],
            "summary": "Candidate summary...",
            "strengths": ["Strength1"],
            "weaknesses": ["Weakness1"]
        }}
        \"\"\"

        try:
            # Generate content
            response = self.model.generate_content(prompt)
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
                
        except Exception as e:
            return {"error": f"AI Error using model '{self.model_name}': {str(e)}"}
"""

# UPDATED APP
app_py = """import streamlit as st
from src.utils import extract_text_from_pdf, create_gauge_chart
from src.gemini_engine import ATSEngine
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="ATS Pro", layout="wide")

st.markdown(\"\"\"
<style>
    .main {background-color: #0e1117;}
    .stButton>button {width: 100%; border-radius: 8px; background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%); color: white;}
    .metric-card {background-color: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #334155; text-align: center;}
    h1, h2, h3, p {color: #e2e8f0;}
</style>
\"\"\", unsafe_allow_html=True)

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
                report_text = f\"\"\"
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
                \"\"\"
                st.download_button(
                    label="📥 Download Full Report",
                    data=report_text,
                    file_name="ats_report.txt",
                    mime="text/plain"
                )

if __name__ == "__main__":
    main()
"""

# ==============================================================================
# 2. GENERATION LOOP
# ==============================================================================

files_to_create = {
    f"{project_name}/requirements.txt": requirements_txt,
    f"{project_name}/.env": env_file,
    f"{project_name}/.gitignore": gitignore_file,
    f"{project_name}/src/__init__.py": "",
    f"{project_name}/src/utils.py": utils_py,
    f"{project_name}/src/gemini_engine.py": gemini_engine_py,
    f"{project_name}/app.py": app_py,
}

for filepath, content in files_to_create.items():
    path = Path(filepath)
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Updated: {filepath}")

print(f"\n🚀 Final Fix Applied! Run:\npython generate_ats.py\nstreamlit run ats_app/app.py")