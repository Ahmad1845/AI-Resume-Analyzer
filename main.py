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
    