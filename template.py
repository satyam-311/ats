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

# UPDATED ENGINE: Fetches Real Models & Filters Experimental ones
gemini_engine_py = """import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

load_dotenv()

class ATSEngine:
    def __init__(self, api_key=None, model_name="models/gemini-1.5-flash"):
        self.api_key = api_key
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model_name = model_name
            self.model = genai.GenerativeModel(self.model_name)

    @staticmethod
    def get_available_models(api_key):
        \"\"\"Fetches only valid, non-experimental models\"\"\"
        if not api_key: return []
        try:
            genai.configure(api_key=api_key)
            # List all generating models
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            # Smart Filter: Remove 'experimental' models to prevent 429 Errors
            stable_models = [m for m in models if "exp" not in m]
            
            # If filtering removed everything, return original list, else return stable
            return sorted(stable_models) if stable_models else sorted(models)
        except Exception as e:
            return []

    def analyze_resume(self, resume_text, jd_text):
        if not self.api_key:
            return {"error": "API Key is missing."}
            
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
            response = self.model.generate_content(prompt)
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except Exception as e:
            return {"error": f"AI Error ({self.model_name}): {str(e)}"}
"""

# UPDATED APP: Explicit .env loading + Secrets Support + Model Selector
app_py = """import streamlit as st
from src.utils import extract_text_from_pdf, create_gauge_chart
from src.gemini_engine import ATSEngine
import os
from pathlib import Path
from dotenv import load_dotenv

# Force load .env from the same directory as app.py (Fixes Local 404)
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

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
                
                report = f"Match: {result.get('match_score')}%\\nVerdict: {result.get('verdict')}\\nMissing: {result.get('missing_keywords')}"
                st.download_button("📥 Download Report", report, "ats_report.txt")

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

print(f"\n🚀 Final Version Ready! Run:\npython generate_ats.py")