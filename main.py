import os
import json
import PyPDF2
import docx
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Load your API Key
load_dotenv(os.path.join(BASE_DIR, ".env"))
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# 2. Start the App
app = FastAPI()
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# 3. This tells the app to show your HTML page when you open the browser
@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    with open(os.path.join(BASE_DIR, "index.html"), "r", encoding="utf-8") as f:
        return f.read()

# 4. This is the logic that reads the PDF and asks Gemini for the analysis
@app.post("/api/analyze")
async def analyze_resume(
    jd: str = Form(...), 
    cv: UploadFile = File(None), 
    cv_text: str = Form(None)
):
    try:
        extracted_cv_text = ""
        
        if cv and cv.filename:
            if cv.filename.lower().endswith(".pdf"):
                reader = PyPDF2.PdfReader(cv.file)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        extracted_cv_text += extracted + "\n"
            elif cv.filename.lower().endswith(".docx"):
                doc = docx.Document(cv.file)
                extracted_cv_text = "\n".join([para.text for para in doc.paragraphs])
            elif cv.filename.lower().endswith(".txt"):
                extracted_cv_text = (await cv.read()).decode("utf-8")
            else:
                return {"error": "Unsupported file format. Please upload PDF, DOCX, or TXT."}
        elif cv_text and cv_text.strip():
            extracted_cv_text = cv_text.strip()
        else:
            return {"error": "Please provide either a CV file or paste the CV text."}
        
        user_prompt = f"JOB DESCRIPTION:\n{jd}\n\nCANDIDATE CV:\n{extracted_cv_text}"
        
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        
        response = client.models.generate_content(
            model=model_name,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "job_title": {"type": "STRING"},
                        "match_percentage": {"type": "INTEGER"},
                        "key_strengths": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "skill_gaps": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "red_flags": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "suggestions": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "section_scores": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "section_name": {"type": "STRING"},
                                    "score": {"type": "INTEGER"},
                                    "feedback": {"type": "STRING"}
                                },
                                "required": ["section_name", "score", "feedback"]
                            }
                        }
                    },
                    "required": ["job_title", "match_percentage", "key_strengths", "skill_gaps", "red_flags", "suggestions", "section_scores"]
                },
                system_instruction="""You are a ruthless, expert technical recruiter and ATS parsing engine. Your job is to critically evaluate resumes against a Job Description (JD).
                RULES:
                1. STRICT SCORING: If the CV is missing core/mandatory skills explicitly listed in the JD, the `match_percentage` MUST NOT exceed 75%. Be realistic and highly critical. Do not inflate scores.
                2. CONCISE BULLETS: Every bullet point in strengths, gaps, red flags, and suggestions MUST be extremely concise (1-2 short lines max).
                3. MANDATORY RED FLAGS: You MUST find at least one red flag or ATS warning if the CV is not absolutely perfect (e.g., missing quantifiable metrics, passive voice, missing contact info). Never return an empty red_flags array unless the CV is flawless.
                4. SECTION SCORES: Provide individual ATS scores (0-100) for standard sections: 'Experience', 'Education', 'Skills', and 'Impact & Formatting', along with 1 very short line of feedback for each.
                Extract the most likely Job Title from the JD.""",
                temperature=0.1 
            ),
        )
        
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        elif raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
            
        return json.loads(raw_text.strip())
    
    except Exception as e:
        return {"error": str(e)}
    