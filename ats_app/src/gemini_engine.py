import google.generativeai as genai
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
        """Fetches only valid, non-experimental models"""
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
            
        prompt = f"""
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
        """
        try:
            response = self.model.generate_content(prompt)
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except Exception as e:
            return {"error": f"AI Error ({self.model_name}): {str(e)}"}
