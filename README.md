# AI Resume Analyzer

A modern, highly professional AI-powered tool that analyzes a candidate's CV against a target Job Description. It leverages Google's **Gemini 2.5 Flash** model to provide instant match scoring, strength identification, skill gaps, and actionable recommendations.

## Features

- **Premium UI**: A sleek, "SaaS-grade" dark mode dashboard with subtle glassmorphism, floating micro-animations, and a responsive split-pane layout.
- **Dynamic Scoring**: Features an animated, circular SVG gauge chart to represent the match percentage visually.
- **AI-Powered Insights**: Extracts text from PDFs and prompts the Gemini AI to provide structured feedback (Strengths, Gaps, Tips).
- **FastAPI Backend**: A lightning-fast asynchronous Python backend.

## Tech Stack

- **Backend**: FastAPI, Python, PyPDF2, Google GenAI SDK (`google-genai`).
- **Frontend**: Vanilla HTML5, JavaScript, TailwindCSS (via CDN).
- **AI Engine**: Google Gemini 2.5 Flash.

## Project Structure

```text
resume-analyzer/
│
├── static/
│   ├── css/
│   │   └── style.css       # Custom styling, animations, and Tailwind overrides
│   └── js/
│       └── script.js       # Frontend logic, API calls, file handling, DOM manipulation
│
├── index.html              # Main UI structure (Split-pane dashboard)
├── main.py                 # FastAPI server and AI integration
├── .env                    # Environment variables (API Keys)
└── README.md               # Project documentation
```

## Setup & Installation

1. **Clone or download** the repository.
2. **Install the dependencies**:
   Make sure you have Python installed, then run:
   ```bash
   pip install fastapi uvicorn python-dotenv pypdf2 google-genai python-multipart
   ```
3. **Set up Environment Variables**:
   Create a `.env` file in the root directory (if it doesn't exist) and add your Gemini API key:
   ```env
   GEMINI_API_KEY=your_google_gemini_api_key_here
   ```

## How to Run

Start the FastAPI development server using Uvicorn:

```bash
python -m uvicorn main:app --reload
```

Then, open your web browser and navigate to:
**[http://127.0.0.1:8000](http://127.0.0.1:8000)**

## Usage

1. Drag and drop your CV (PDF format) into the upload zone on the left pane.
2. Paste the target Job Description into the text area.
3. Click **Analyze Resume** and wait a few seconds.
4. Review your Match Score, Key Strengths, Skill Gaps, and AI Recommendations on the right pane!
