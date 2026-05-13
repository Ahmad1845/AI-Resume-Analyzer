import os
import json
import PyPDF2
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
async def analyze_resume(cv: UploadFile = File(...), jd: str = Form(...)):
    try:
        cv_text = ""
        reader = PyPDF2.PdfReader(cv.file)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                cv_text += extracted + "\n"
        
        user_prompt = f"JOB DESCRIPTION:\n{jd}\n\nCANDIDATE CV:\n{cv_text}"
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                system_instruction="""You are an expert technical recruiter. Analyze the CV against the Job Description. 
                Return ONLY valid JSON matching this schema: 
                {"match_percentage": int, "key_strengths": [str], "skill_gaps": [str], "suggestions": [str]}""",
                temperature=0.2 
            ),
        )
        return json.loads(response.text)
    
    except Exception as e:
        return {"error": str(e)}
    