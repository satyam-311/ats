import google.generativeai as genai
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
        """Fetches valid models for this specific API Key"""
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
            
        prompt = f"""
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
        """
        try:
            response = self.model.generate_content(prompt)
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except Exception as e:
            return {"error": f"Model Error ({self.model_name}): {str(e)}"}
