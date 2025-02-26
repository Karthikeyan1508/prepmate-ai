import os
import io
import base64
import fitz  # PyMuPDF for text extraction
import streamlit as st
import google.generativeai as genai
import re
import nltk
from nltk.corpus import stopwords
from collections import Counter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Google Gemini AI API
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GENAI_API_KEY:
    raise ValueError("Google API Key not found. Please set it in your .env file.")

genai.configure(api_key=GENAI_API_KEY, transport="rest")

# Download stopwords for keyword extraction
nltk.download("stopwords")
stop_words = set(stopwords.words("english"))

# Function to extract text from PDF
def extract_text_from_pdf(uploaded_file):
    """Extracts text from an uploaded PDF file."""
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    return text

# Function to extract keywords from text
def extract_keywords(text):
    """Extracts keywords from the given text (resume or job description)."""
    words = re.findall(r"\b\w+\b", text.lower())  # Tokenize words
    keywords = [word for word in words if word not in stop_words]  # Remove stopwords
    return Counter(keywords)  # Count keyword frequency

# Function to calculate ATS match percentage
def calculate_match_percentage(resume_text, jd_text):
    """Calculates the ATS match percentage based on keyword overlap."""
    resume_keywords = extract_keywords(resume_text)
    jd_keywords = extract_keywords(jd_text)

    common_keywords = set(resume_keywords.keys()) & set(jd_keywords.keys())
    total_jd_keywords = len(set(jd_keywords.keys()))

    match_percentage = (len(common_keywords) / total_jd_keywords) * 100 if total_jd_keywords > 0 else 0
    missing_keywords = set(jd_keywords.keys()) - set(resume_keywords.keys())

    return round(match_percentage, 2), missing_keywords

# Function to get AI-generated resume feedback
def get_gemini_feedback(resume_text, jd_text, prompt):
    """Generate AI feedback using Google's Gemini-Pro model."""
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content([resume_text, jd_text, prompt])
    return response.text

# Streamlit UI
def run_ats_analyzer():
    st.set_page_config(page_title="ATS Analyzer")
    st.title("📄 ATS Analyzer")
    st.write("Analyze your resume for ATS compatibility and get AI-powered feedback.")

    

    # User inputs
    input_text = st.text_area("📌 Paste Job Description Here:", key="input")
    uploaded_file = st.file_uploader("📤 Upload your resume (PDF)...", type=["pdf"])

    if uploaded_file:
        st.success("✅ PDF Uploaded Successfully")

    # Buttons for analysis
    analyze_ats = st.button("📊 Get ATS Match Score")
    get_feedback = st.button("🤖 Get AI Feedback")

    if analyze_ats:
        if uploaded_file and input_text:
            resume_text = extract_text_from_pdf(uploaded_file)
            match_percentage, missing_keywords = calculate_match_percentage(resume_text, input_text)

            st.subheader("📊 ATS Match Score")
            st.write(f"✅ Your resume matches **{match_percentage}%** of the job description.")

            if missing_keywords:
                st.subheader("⚠️ Missing Keywords")
                st.write(", ".join(missing_keywords))
            else:
                st.write("🎉 No missing keywords! Your resume is well-optimized.")

        else:
            st.warning("⚠️ Please upload a resume and provide a job description.")

    if get_feedback:
        if uploaded_file and input_text:
            resume_text = extract_text_from_pdf(uploaded_file)

            ai_prompt = """
            You are a professional HR recruiter. Analyze the given resume based on the provided job description.
            Provide feedback on:
            1. Strengths of the candidate.
            2. Weaknesses and missing skills.
            3. Suggestions for improvement.
            """

            response = get_gemini_feedback(resume_text, input_text, ai_prompt)
            st.subheader("🤖 AI-Powered Resume Feedback")
            st.write(response)

        else:
            st.warning("⚠️ Please upload a resume and provide a job description.")

if __name__ == "__main__":
    run_ats_analyzer()
