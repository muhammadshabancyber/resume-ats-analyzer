# resume-ats-analyzer
AI-powered Resume ATS Analyzer using Streamlit and Gemini Flash
# 📄 ATS Resume Checker

A Streamlit app that scores a resume for ATS (Applicant Tracking System) compatibility using Google Gemini Flash,
and gives concrete improvements.

## Features
- Upload resume as **PDF, DOCX or TXT**
- Optional **job description** for a more accurate keyword match
- Overall **ATS score (0-100)** + breakdown (keywords, formatting, content impact, structure, language)
- Strengths, weaknesses, **missing keywords**
- Prioritised improvements (High / Medium / Low) and **before/after rewrite examples**
- Download the report as JSON

## Run locally
```bash
git clone https://github.com/<your-username>/ats-resume-checker.git
cd ats-resume-checker
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
Get a free API key at https://aistudio.google.com/apikey and either paste it in the sidebar, or create
`.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "your-key-here"
```

## Deploy on Streamlit Community Cloud
1. Push this repo to GitHub (never commit your API key).
2. Go to https://share.streamlit.io, sign in with GitHub, click **Create app**.
3. Select the repo, branch `main`, main file `app.py`.
4. Open **Advanced settings → Secrets** and add: `GEMINI_API_KEY = "your-key-here"`
5. Click **Deploy**.

## Notes
- Model is set by `MODEL_NAME` at the top of `app.py`.
- Scanned/image-only resumes can't be read (a real ATS can't read them either).
- The score is an AI estimate, not the output of any specific commercial ATS.
