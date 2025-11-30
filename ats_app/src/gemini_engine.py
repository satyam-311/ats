import google.generativeai as genai
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
            # Generate content
            response = self.model.generate_content(prompt)
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
                
        except Exception as e:
            return {"error": f"AI Error using model '{self.model_name}': {str(e)}"}
