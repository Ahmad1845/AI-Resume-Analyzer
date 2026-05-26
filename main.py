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

from fastapi.responses import HTMLResponse, StreamingResponse
import asyncio
import io

# 4. This is the logic that reads the PDF and asks Gemini for the analysis
@app.post("/api/analyze")
async def analyze_resume(
    jd: str = Form(...), 
    cv: UploadFile = File(None), 
    cv_text: str = Form(None)
):
    # Read the file fully into memory immediately
    cv_content = None
    cv_filename = None
    if cv and cv.filename:
        cv_filename = cv.filename
        cv_content = await cv.read()
        
    async def analyze_generator():
        try:
            # Step 1: Document Parsing
            yield f"data: {json.dumps({'status': 'Parsing document structure...'})}\n\n"
            await asyncio.sleep(0.5) # Give UI time to animate
            
            extracted_cv_text = ""
            
            if cv_filename:
                if cv_filename.lower().endswith(".pdf"):
                    reader = PyPDF2.PdfReader(io.BytesIO(cv_content))
                    for page in reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            extracted_cv_text += extracted + "\n"
                elif cv_filename.lower().endswith(".docx"):
                    doc = docx.Document(io.BytesIO(cv_content))
                    extracted_cv_text = "\n".join([para.text for para in doc.paragraphs])
                elif cv_filename.lower().endswith(".txt"):
                    extracted_cv_text = cv_content.decode("utf-8")
                else:
                    yield f"data: {json.dumps({'error': 'Unsupported file format. Please upload PDF, DOCX, or TXT.'})}\n\n"
                    return
            elif cv_text and cv_text.strip():
                extracted_cv_text = cv_text.strip()
            else:
                yield f"data: {json.dumps({'error': 'Please provide either a CV file or paste the CV text.'})}\n\n"
                return
                
            # Step 2: Extracting Skills & Cross-referencing
            yield f"data: {json.dumps({'status': 'Extracting candidate skills...'})}\n\n"
            await asyncio.sleep(0.5)
            
            yield f"data: {json.dumps({'status': 'Cross-referencing Job Description with Gemini AI...'})}\n\n"
            
            user_prompt = f"JOB DESCRIPTION:\n{jd}\n\nCANDIDATE CV:\n{extracted_cv_text}"
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            
            def call_gemini():
                return client.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        system_instruction="""You are a ruthless, expert technical recruiter and ATS parsing engine. Your job is to critically evaluate resumes against a Job Description (JD).
                RULES:
                1. STRICT SCORING: If the CV is missing core/mandatory skills explicitly listed in the JD, the `match_percentage` MUST NOT exceed 75%. Be realistic and highly critical. Do not inflate scores.
                2. CONCISE BULLETS: Every bullet point in strengths, gaps, red flags, and suggestions MUST be extremely concise (1-2 short lines max).
                3. MANDATORY RED FLAGS: You MUST find at least one red flag or ATS warning if the CV is not absolutely perfect (e.g., missing quantifiable metrics, passive voice, missing contact info). Never return an empty red_flags array unless the CV is flawless.
                4. SECTION SCORES: Provide individual ATS scores (0-100) for standard sections: 'Experience', 'Education', 'Skills', and 'Impact & Formatting', along with 1 very short line of feedback for each.
                Extract the most likely Job Title from the JD.
                Return ONLY valid JSON matching this schema: 
                {"job_title": str, "match_percentage": int, "key_strengths": [str], "skill_gaps": [str], "red_flags": [str], "suggestions": [str], "section_scores": [{"section_name": str, "score": int, "feedback": str}]}""",
                        temperature=0.2 
                    ),
                )
            
            response = await asyncio.to_thread(call_gemini)
            
            # Step 3: Final Report
            yield f"data: {json.dumps({'status': 'Generating final report...'})}\n\n"
            await asyncio.sleep(0.5)
            
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            elif raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
                
            yield f"data: {json.dumps({'result': json.loads(raw_text.strip())})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(analyze_generator(), media_type="text/event-stream")

    