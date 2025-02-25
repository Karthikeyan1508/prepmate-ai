import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_interview_questions(job_description, domain):
    """Generate domain-specific interview questions using Gemini API."""
    
    # Select Gemini model
    model = genai.GenerativeModel("gemini-pro")

    prompt = f"""
    You are an AI interviewer preparing an interview for a {domain} candidate.
    Based on the following Job Description, generate 5 domain-specific questions 
    (coding for IT, theoretical for others). Format the output as a Python list.

    Job Description:
    {job_description}

    Return output as:
    ["Question 1", "Question 2", "Question 3", "Question 4", "Question 5"]
    """

    # Generate response
    response = model.generate_content(prompt)
    print("Generated Questions:", questions)


    # Extract and return list of questions
    return response.text.strip("[]").replace('"', '').split(", ")
