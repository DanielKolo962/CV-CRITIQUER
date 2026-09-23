import streamlit as st
import PyPDF2
import io
import os
import json
import re
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AI Resume Optimizer", page_icon="", layout="centered")

st.title("AI Resume Optimizer")
st.markdown("Upload your resume and get AI powered feedback tailored to your needs")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

uploaded_file = st.file_uploader(
    "Upload your resume (PDF) or (TXT)",
    type=["pdf", "txt"]
)

job_role = st.text_input("Enter the type of job you are targetting (optional)")

analyze = st.button("Analyze")


# ---------------------------------------------------------
# FILE HANDLING
# ---------------------------------------------------------

def extract_text_from_pdf(file_bytes):
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))

    text = ""

    for page in pdf_reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n\n"

    return text


def extract_text_from_txt(file_bytes):
    return file_bytes.decode("utf-8")


def detect_file_type(file_bytes):
    """
    Detect the actual file type based on its contents.
    """

    # PDF files normally start with %PDF-
    if file_bytes.startswith(b"%PDF-"):
        return "pdf"

    # If it can be decoded as UTF-8, treat it as plain text.
    try:
        file_bytes.decode("utf-8")
        return "txt"
    except UnicodeDecodeError:
        return "unknown"


def extract_text_from_file(uploaded_file):
    """
    Validate the uploaded file and extract its text.
    """

    file_bytes = uploaded_file.getvalue()

    # Check for an empty file first.
    if not file_bytes:
        raise ValueError(
            "This file is empty. Upload a PDF or TXT file that contains your CV."
        )

    # Determine what the filename says the file is.
    filename = uploaded_file.name.lower()

    if filename.endswith(".pdf"):
        expected_type = "pdf"

    elif filename.endswith(".txt"):
        expected_type = "txt"

    else:
        raise ValueError(
            "Unsupported file type. Upload a PDF or TXT file."
        )

    # Determine what the file actually contains.
    actual_type = detect_file_type(file_bytes)

    if actual_type == "unknown":
        raise ValueError(
            "We couldn't read this file. Please upload a valid PDF or TXT file."
        )

    # Check whether the extension matches the actual content.
    if actual_type != expected_type:
        raise ValueError(
            f"This file is named as a {expected_type.upper()} file, "
            f"but its contents are actually a {actual_type.upper()} file. "
            "Please upload the file with the correct extension."
        )

    # Process PDF.
    if actual_type == "pdf":
        try:
            text = extract_text_from_pdf(file_bytes)

        except Exception:
            raise ValueError(
                "We couldn't read this PDF. Please upload a valid text-based PDF "
                "or a TXT file."
            )

        # PDF exists but no text could be extracted.
        if not text.strip():
            raise ValueError(
                "We couldn't find any text in this PDF. It may be a scanned image — "
                "upload a text-based PDF or a TXT file."
            )

        return text

    # Process TXT.
    if actual_type == "txt":
        try:
            text = extract_text_from_txt(file_bytes)

        except UnicodeDecodeError:
            raise ValueError(
                "This TXT file could not be read as plain text. "
                "Please upload a valid UTF-8 TXT file."
            )

        if not text.strip():
            raise ValueError(
                "This file is empty. Upload a PDF or TXT file that contains your CV."
            )

        return text

    raise ValueError(
        "We couldn't read this file. Please upload a valid PDF or TXT file."
    )


# ---------------------------------------------------------
# AI RESUME ANALYSIS
# ---------------------------------------------------------

if analyze and uploaded_file:
    try:
        file_content = extract_text_from_file(uploaded_file)

        prompt = f"""
        You are an expert Resume Reviewer, ATS Specialist, and Technical Recruiter.

        Analyze the following resume specifically for this target job:

        TARGET JOB:
        {job_role if job_role else "General Software Engineering / Technology Role"}

        RESUME:
        {file_content}

        Return your analysis as VALID JSON ONLY.

        Do not include Markdown fences such as ```json.
        Do not include explanations before or after the JSON.

        Use exactly this structure:

        {{
            "resume_score": {{
                "overall": 0,
                "ats_compatibility": 0,
                "content_quality": 0,
                "skills": 0,
                "experience": 0
            }},

            "critical_issues": [
                {{
                    "issue": "Short description of the problem",
                    "why_it_matters": "Explain why this matters",
                    "recommendation": "Specific action the candidate should take"
                }}
            ],

            "strengths": [
                "Specific strength supported by the resume"
            ],

            "recommended_changes": [
                {{
                    "section": "Summary",
                    "current_problem": "What needs improvement",
                    "recommendation": "What the candidate should change"
                }}
            ],

            "missing_keywords": [
                "keyword 1",
                "keyword 2"
            ],

            "skills_analysis": {{
                "existing_skills": [
                    "Skill actually found in the resume"
                ],
                "skills_to_consider": [
                    "Potential relevant skill to consider if the candidate has experience with it"
                ]
            }},

            "summary_feedback": "A concise overall assessment of the resume.",

            "suggested_summary": "An improved professional summary based ONLY on information actually present in the resume."
        }}

        SCORING RULES:

        Score each category from 0 to 100.

        "overall":
        Overall quality of the resume.

        "ats_compatibility":
        How well the resume's structure, terminology, keywords, and content align
        with Applicant Tracking Systems for the target role.

        "content_quality":
        Clarity, professionalism, relevance, grammar, and effectiveness of the
        resume content.

        "skills":
        Relevance, organization, clarity, and presentation of technical skills.

        "experience":
        Quality, relevance, specificity, and impact of the work experience.

        IMPORTANT:

        - Scores must be integers between 0 and 100.
        - Do not invent information.
        - Do not invent employment history.
        - Do not invent skills.
        - Do not invent education.
        - Do not invent certifications.
        - Do not invent achievements.
        - Do not invent metrics or percentages.
        - If a measurable achievement is missing, recommend that the candidate
          add a metric if they have one.
        - Only list existing skills under "existing_skills" if they actually appear
          in the resume.
        - "skills_to_consider" should contain suggestions, not claims that the
          candidate already possesses those skills.
        - Missing keywords should be relevant to the target job and should be
          clearly treated as keywords the candidate may want to consider if they
          genuinely have the corresponding experience.
        - Keep feedback specific to this resume.
        - Do not give generic resume advice when the resume provides enough
          information for a specific recommendation.
        """

        client = ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model="openai/gpt-oss-120b",
            temperature=0.3,
            max_tokens=2500
        )

        response = client.invoke([
            {
                "role": "system",
                "content": "You are an expert resume reviewer and ATS Specialist Always follow the requested JSON structure exactly."
            },
            {
                "role": "user",
                "content": prompt
            }
        ])

        raw_response = response.content.strip()

        # Remove Markdown code fences if the model added them
        raw_response = re.sub(r"^```json\s*", "", raw_response)
        raw_response = re.sub(r"^```\s*", "", raw_response)
        raw_response = re.sub(r"\s*```$", "", raw_response)

        analysis = json.loads(raw_response)

        st.markdown("### Analysis Results")
        st.markdown("## Resume Score")

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric(
            "Overall",
            f"{analysis['resume_score']['overall']}/100"
        )

        col2.metric(
            "ATS",
            f"{analysis['resume_score']['ats_compatibility']}/100"
        )

        col3.metric(
            "Content",
            f"{analysis['resume_score']['content_quality']}/100"
        )

        col4.metric(
            "Skills",
            f"{analysis['resume_score']['skills']}/100"
        )

        col5.metric(
            "Experience",
            f"{analysis['resume_score']['experience']}/100"
        )

        st.markdown("## 🚨 Critical Issues")

        for issue in analysis["critical_issues"]:
            with st.expander(issue["issue"]):
                st.markdown("**Why it matters:**")
                st.write(issue["why_it_matters"])

                st.markdown("**Recommendation:**")
                st.write(issue["recommendation"])

        st.markdown("## ✅ Strengths")

        for strength in analysis["strengths"]:
            st.success(strength)

        st.markdown("## ✍️ Recommended Changes")

        for change in analysis["recommended_changes"]:
            with st.expander(change["section"]):
                st.markdown("**Current Problem**")
                st.write(change["current_problem"])

                st.markdown("**Recommendation**")
                st.write(change["recommendation"])

        st.markdown("## 🔑 Missing Keywords")

        keywords = analysis["missing_keywords"]

        if keywords:
            st.write(", ".join(keywords))
        else:
            st.success("No major missing keywords identified.")

        st.markdown("## 📝 Suggested Professional Summary")

        st.info(analysis["suggested_summary"])



    except ValueError as e:

        st.error(str(e))


    except json.JSONDecodeError:

        st.error("The AI returned an invalid response format. Please try again.")


    except Exception as e:

        st.error(f"An unexpected error occurred: {e}")
