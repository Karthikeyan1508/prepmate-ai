import os
import io
import base64
from dotenv import load_dotenv
import streamlit as st
from PIL import Image
import pdf2image
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Google Gemini AI API
GENAI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GENAI_API_KEY:
    raise ValueError("Google API Key not found. Please set it in your .env file.")

genai.configure(api_key=GENAI_API_KEY)

def get_gemini_response(input_text, pdf_content, prompt):
    """
    Generate AI response using Google's Gemini-Pro-Vision model.
    
    Args:
        input_text (str): The job description provided by the user.
        pdf_content (list): List containing encoded image data of the resume.
        prompt (str): Instruction for AI to evaluate the resume.
    
    Returns:
        str: AI-generated response.
    """
    model = genai.GenerativeModel('gemini-pro-vision')
    response = model.generate_content([input_text, pdf_content[0], prompt])
    return response.text

def input_pdf_setup(uploaded_file):
    """
    Convert the first page of a PDF resume to an image and encode it in base64.
    
    Args:
        uploaded_file (UploadedFile): PDF file uploaded via Streamlit.
    
    Returns:
        list: A list containing a dictionary with encoded image data.
    """
    if uploaded_file is not None:
        images = pdf2image.convert_from_bytes(uploaded_file.read())
        first_page = images[0]
        
        # Convert image to bytes
        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()
        
        # Encode image to base64 format
        pdf_parts = [{
            "mime_type": "image/jpeg",
            "data": base64.b64encode(img_byte_arr).decode()
        }]
        return pdf_parts
    else:
        raise FileNotFoundError("No file uploaded")

# Streamlit App Configuration
st.set_page_config(page_title="ATS Resume Expert")
st.header("ATS Tracking System")

# Input fields
input_text = st.text_area("Job Description:", key="input")
uploaded_file = st.file_uploader("Upload your resume (PDF)...", type=["pdf"])

if uploaded_file:
    st.success("PDF Uploaded Successfully")

# Buttons for user actions
submit1 = st.button("Tell Me About the Resume")
submit3 = st.button("Percentage Match")

# AI Prompts
evaluation_prompt = """
You are an experienced Technical Human Resource Manager. Your task is to review the provided resume against the job description. 
Please share your professional evaluation on whether the candidate's profile aligns with the role. 
Highlight the strengths and weaknesses of the applicant in relation to the specified job requirements.
"""

match_prompt = """
You are a skilled ATS (Applicant Tracking System) scanner with a deep understanding of data science and ATS functionality.
Your task is to evaluate the resume against the provided job description. 
Give me the percentage match if the resume aligns with the job description. 
The output should include:
1. The percentage match.
2. Missing keywords.
3. Final thoughts.
"""

# Processing user actions
if submit1:
    if uploaded_file:
        pdf_content = input_pdf_setup(uploaded_file)
        response = get_gemini_response(input_text, pdf_content, evaluation_prompt)
        st.subheader("Evaluation Report")
        st.write(response)
    else:
        st.warning("Please upload the resume.")

elif submit3:
    if uploaded_file:
        pdf_content = input_pdf_setup(uploaded_file)
        response = get_gemini_response(input_text, pdf_content, match_prompt)
        st.subheader("Percentage Match Analysis")
        st.write(response)
    else:
        st.warning("Please upload the resume.")
