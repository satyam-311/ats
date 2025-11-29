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
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#4f46e5"}}
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20))
    return fig
"""

# UPDATED ENGINE: Accepts model_name dynamically
gemini_engine_py = """import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

load_dotenv()

class ATSEngine:
    def __init__(self, api_key=None, model_name="models/gemini-1.5-flash"):
        self.api_key = api_key if api_key else os.getenv("GOOGLE_API_KEY")
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model_name = model_name
            self.model = genai.GenerativeModel(self.model_name)

    @staticmethod
    def get_available_models(api_key):
        \"\"\"Fetches valid models for this specific API Key\"\"\"
        if not api_key: return []
        try:
            genai.configure(api_key=api_key)
            # List only models that support content generation
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            # Filter out experimental/legacy if needed, or keep all
            return sorted(models)
        except Exception as e:
            return []

    def analyze_resume(self, resume_text, jd_text):
        if not self.api_key:
            return {"error": "API Key is missing. Check .env file."}
            
        prompt = f\"\"\"
        Act as an ATS Scanner.
        JD: {jd_text}
        Resume: {resume_text}
        
        Output strict JSON:
        {{
            "match_score": 85,
            "missing_keywords": ["Skill1", "Skill2"],
            "summary": "Short summary...",
            "strengths": ["Strength1"],
            "weaknesses": ["Weakness1"]
        }}
        \"\"\"
        try:
            response = self.model.generate_content(prompt)
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except Exception as e:
            return {"error": f"Model Error ({self.model_name}): {str(e)}"}
"""

# UPDATED APP: Adds Model Selector Dropdown
app_py = """import streamlit as st
from src.utils import extract_text_from_pdf, create_gauge_chart
from src.gemini_engine import ATSEngine
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="ATS Pro", layout="wide")

st.markdown(\"\"\"
<style>
    .stButton>button {width: 100%; border-radius: 5px; background: #4f46e5; color: white;}
</style>
\"\"\", unsafe_allow_html=True)

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
    print(f"✅ Created: {filepath}")

print(f"\n🚀 Fixed! Ab run karo:\ncd {project_name}\nstreamlit run app.py")