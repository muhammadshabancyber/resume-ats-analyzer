import os
import json
import re
import time

import streamlit as st
from pypdf import PdfReader
from docx import Document
from google import genai


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="Resume ATS Analyzer",
    page_icon="📄",
    layout="wide"
)


# ---------------------------------------------------------
# GEMINI CLIENT
# ---------------------------------------------------------

def get_gemini_client():

    api_key = os.getenv("GEMINI_API_KEY")

    # Streamlit Cloud Secrets
    if not api_key:
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            api_key = None

    if not api_key:
        return None

    return genai.Client(api_key=api_key)


# ---------------------------------------------------------
# EXTRACT TEXT FROM PDF
# ---------------------------------------------------------

def extract_pdf_text(uploaded_file):

    reader = PdfReader(uploaded_file)

    text = []

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text.append(page_text)

    return "\n".join(text)


# ---------------------------------------------------------
# EXTRACT TEXT FROM DOCX
# ---------------------------------------------------------

def extract_docx_text(uploaded_file):

    document = Document(uploaded_file)

    paragraphs = []

    for paragraph in document.paragraphs:

        if paragraph.text.strip():
            paragraphs.append(paragraph.text)

    return "\n".join(paragraphs)


# ---------------------------------------------------------
# EXTRACT RESUME TEXT
# ---------------------------------------------------------

def extract_resume_text(uploaded_file):

    file_name = uploaded_file.name.lower()

    if file_name.endswith(".pdf"):

        return extract_pdf_text(uploaded_file)

    elif file_name.endswith(".docx"):

        return extract_docx_text(uploaded_file)

    else:

        raise ValueError(
            "Unsupported file type. Please upload a PDF or DOCX file."
        )


# ---------------------------------------------------------
# CLEAN GEMINI JSON RESPONSE
# ---------------------------------------------------------

def clean_json_response(response_text):

    response_text = response_text.strip()

    # Remove ```json
    response_text = re.sub(
        r"^```json\s*",
        "",
        response_text,
        flags=re.IGNORECASE
    )

    # Remove ```
    response_text = re.sub(
        r"\s*```$",
        "",
        response_text
    )

    return response_text.strip()


# ---------------------------------------------------------
# GEMINI ANALYSIS
# ---------------------------------------------------------

def analyze_resume(resume_text, target_job):

    client = get_gemini_client()

    if client is None:

        raise ValueError(
            "Gemini API key was not found. "
            "Please add GEMINI_API_KEY to Streamlit Secrets."
        )


    # Limit extremely large resumes
    resume_text = resume_text[:50000]


    prompt = f"""
You are an expert ATS resume evaluator and professional career coach.

Analyze the following resume for ATS compatibility and relevance.

TARGET JOB:
{target_job}

RESUME:
-------------------------
{resume_text}
-------------------------

Evaluate the resume using these areas:

1. ATS compatibility
2. Job relevance
3. Keywords
4. Skills
5. Professional summary
6. Work experience
7. Education
8. Formatting/readability
9. Achievements and measurable results
10. Overall resume quality

Return ONLY valid JSON.

Use exactly this structure:

{{
    "ats_score": 0,
    "summary": "",
    "strengths": [],
    "weaknesses": [],
    "missing_keywords": [],
    "formatting_issues": [],
    "content_improvements": [],
    "section_scores": {{
        "ats_compatibility": 0,
        "job_relevance": 0,
        "keywords": 0,
        "skills": 0,
        "experience": 0,
        "education": 0,
        "formatting": 0
    }},
    "recommended_summary": "",
    "priority_actions": []
}}

Rules:

- ats_score must be between 0 and 100.
- All section scores must be between 0 and 100.
- Give practical and specific recommendations.
- Do not invent experience or qualifications.
- Identify missing keywords based on the target job.
- Focus on ATS-friendly improvements.
- Do not judge the candidate's personality.
- Return JSON only.
"""


    # -----------------------------------------------------
    # RETRY SYSTEM FOR TEMPORARY 503 ERRORS
    # -----------------------------------------------------

    max_attempts = 4

    for attempt in range(max_attempts):

        try:

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )

            return json.loads(
                clean_json_response(response.text)
            )


        except Exception as e:

            error_message = str(e)

            # Temporary Gemini server overload
            if "503" in error_message or "UNAVAILABLE" in error_message:

                if attempt < max_attempts - 1:

                    wait_time = 3 * (2 ** attempt)

                    time.sleep(wait_time)

                    continue

                else:

                    raise RuntimeError(
                        "Gemini is currently experiencing high demand. "
                        "Please wait a little and try again."
                    )

            # Other errors
            raise e


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.title("📄 Resume ATS Analyzer")

st.write(
    "Upload your resume and get an AI-powered ATS score, "
    "missing keywords, strengths, weaknesses, and "
    "improvement suggestions."
)

st.divider()


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

with st.sidebar:

    st.header("⚙️ Resume Settings")

    target_job = st.text_input(
        "Target Job",
        placeholder="e.g. Python Developer"
    )

    st.info(
        "Enter the exact job title you are applying for "
        "to get better ATS recommendations."
    )


# ---------------------------------------------------------
# FILE UPLOAD
# ---------------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload your Resume",
    type=["pdf", "docx"],
    help="Supported formats: PDF and DOCX"
)


# ---------------------------------------------------------
# ANALYZE
# ---------------------------------------------------------

if uploaded_file:

    st.success(
        f"Uploaded: {uploaded_file.name}"
    )


    if st.button(
        "🚀 Analyze Resume",
        type="primary",
        use_container_width=True
    ):

        # ---------------------------------------------
        # CHECK TARGET JOB
        # ---------------------------------------------

        if not target_job.strip():

            st.warning(
                "Please enter the target job title first."
            )

            st.stop()


        try:

            # -----------------------------------------
            # EXTRACT + ANALYZE
            # -----------------------------------------

            with st.spinner(
                "Reading your resume and analyzing it with Gemini..."
            ):

                resume_text = extract_resume_text(
                    uploaded_file
                )


                if not resume_text.strip():

                    st.error(
                        "Could not extract readable text "
                        "from this resume."
                    )

                    st.stop()


                result = analyze_resume(
                    resume_text,
                    target_job
                )


            st.success(
                "Resume analysis completed!"
            )

            st.divider()


            # -----------------------------------------
            # ATS SCORE
            # -----------------------------------------

            score = int(
                result.get("ats_score", 0)
            )

            score = max(
                0,
                min(score, 100)
            )


            st.subheader(
                "🎯 ATS Score"
            )


            col1, col2, col3 = st.columns(3)


            with col1:

                st.metric(
                    "ATS Score",
                    f"{score}/100"
                )


            with col2:

                if score >= 80:

                    status = "Excellent"

                elif score >= 60:

                    status = "Good"

                elif score >= 40:

                    status = "Needs Improvement"

                else:

                    status = "Poor"


                st.metric(
                    "Status",
                    status
                )


            with col3:

                st.metric(
                    "Target Job",
                    target_job
                )


            st.progress(
                score / 100
            )


            # -----------------------------------------
            # SUMMARY
            # -----------------------------------------

            st.subheader(
                "📝 Overall Analysis"
            )

            st.write(
                result.get(
                    "summary",
                    "No summary available."
                )
            )


            # -----------------------------------------
            # SECTION SCORES
            # -----------------------------------------

            st.subheader(
                "📊 Section Scores"
            )


            section_scores = result.get(
                "section_scores",
                {}
            )


            score_columns = st.columns(4)


            items = list(
                section_scores.items()
            )


            for index, (section, section_score) in enumerate(items):

                with score_columns[index % 4]:

                    readable_name = section.replace(
                        "_",
                        " "
                    ).title()


                    st.metric(
                        readable_name,
                        f"{section_score}/100"
                    )


            # -----------------------------------------
            # STRENGTHS
            # -----------------------------------------

            st.subheader(
                "✅ Strengths"
            )


            strengths = result.get(
                "strengths",
                []
            )


            for item in strengths:

                st.write(
                    f"• {item}"
                )


            # -----------------------------------------
            # WEAKNESSES
            # -----------------------------------------

            st.subheader(
                "⚠️ Weaknesses"
            )


            weaknesses = result.get(
                "weaknesses",
                []
            )


            for item in weaknesses:

                st.write(
                    f"• {item}"
                )


            # -----------------------------------------
            # MISSING KEYWORDS
            # -----------------------------------------

            st.subheader(
                "🔑 Missing Keywords"
            )


            missing_keywords = result.get(
                "missing_keywords",
                []
            )


            if missing_keywords:

                keyword_text = " • ".join(
                    missing_keywords
                )

                st.info(
                    keyword_text
                )

            else:

                st.success(
                    "No major missing keywords identified."
                )


            # -----------------------------------------
            # FORMATTING ISSUES
            # -----------------------------------------

            st.subheader(
                "📐 Formatting Issues"
            )


            formatting_issues = result.get(
                "formatting_issues",
                []
            )


            for item in formatting_issues:

                st.write(
                    f"• {item}"
                )


            # -----------------------------------------
            # CONTENT IMPROVEMENTS
            # -----------------------------------------

            st.subheader(
                "✍️ Content Improvements"
            )


            content_improvements = result.get(
                "content_improvements",
                []
            )


            for item in content_improvements:

                st.write(
                    f"• {item}"
                )


            # -----------------------------------------
            # RECOMMENDED SUMMARY
            # -----------------------------------------

            st.subheader(
                "✨ Recommended Professional Summary"
            )


            st.write(
                result.get(
                    "recommended_summary",
                    "No recommended summary available."
                )
            )


            # -----------------------------------------
            # PRIORITY ACTIONS
            # -----------------------------------------

            st.subheader(
                "🚀 Priority Actions"
            )


            priority_actions = result.get(
                "priority_actions",
                []
            )


            for index, action in enumerate(
                priority_actions,
                start=1
            ):

                st.write(
                    f"**{index}.** {action}"
                )


            # -----------------------------------------
            # DOWNLOAD REPORT
            # -----------------------------------------

            st.divider()


            report = json.dumps(
                result,
                indent=4,
                ensure_ascii=False
            )


            st.download_button(
                label="⬇️ Download Analysis",
                data=report,
                file_name="resume_ats_analysis.json",
                mime="application/json"
            )


        except RuntimeError as e:

            st.error(
                str(e)
            )

            st.info(
                "Please wait 1–2 minutes and click "
                "'Analyze Resume' again."
            )


        except json.JSONDecodeError:

            st.error(
                "Gemini returned an unexpected response format. "
                "Please try again."
            )


        except Exception as e:

            st.error(
                f"Something went wrong: {str(e)}"
            )


else:

    st.info(
        "👆 Upload a PDF or DOCX resume to begin."
    )


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.divider()

st.caption(
    "Resume ATS Analyzer • Powered by Streamlit and Gemini"
)
