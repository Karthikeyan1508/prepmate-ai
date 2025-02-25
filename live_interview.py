import streamlit as st
import openai
import tempfile
import PyPDF2
import os
import speech_recognition as sr

# Set OpenAI API key
openai.api_key = "YOUR_OPENAI_API_KEY"

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(pdf_file.read())
        temp_pdf_path = temp_pdf.name
    
    text = ""
    with open(temp_pdf_path, "rb") as f:
        pdf_reader = PyPDF2.PdfReader(f)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"

    os.remove(temp_pdf_path)  # Clean up temp file
    return text

# Function to extract skills from text using GPT
def extract_skills(text):
    prompt = f"Extract key skills from the following resume/job description:\n{text}"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"]

# Function to generate interview questions
def generate_questions(resume_skills, jd_skills):
    common_skills = set(resume_skills.split(", ")) & set(jd_skills.split(", "))
    missing_skills = set(jd_skills.split(", ")) - set(resume_skills.split(", "))

    prompt = f"""
    Based on the following skills:
    - Candidate's skills: {resume_skills}
    - Job requirements: {jd_skills}

    Generate 3 technical interview questions based on common skills ({common_skills}) 
    and 2 questions to test missing skills ({missing_skills}).
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response["choices"][0]["message"]["content"].split("\n")

# Function to convert text to speech
def text_to_speech(text):
    response = openai.Audio.create(
        model="tts-1",
        input=text,
        voice="alloy"
    )
    return response["data"]

# Function to transcribe user speech using Whisper API
def speech_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("🎤 Listening...")
        audio = recognizer.listen(source)
    
    try:
        text = recognizer.recognize_whisper(audio)
        return text
    except sr.UnknownValueError:
        return "Sorry, I couldn't understand that."
    except sr.RequestError:
        return "Error connecting to the speech service."

# Streamlit UI
st.title("🎙️ AI-Powered Interview Simulator")
st.write("Upload your Resume and Job Description (PDF) to begin.")

col1, col2 = st.columns(2)
with col1:
    resume_file = st.file_uploader("📄 Upload Resume (PDF)", type=["pdf"])
with col2:
    jd_file = st.file_uploader("📃 Upload Job Description (PDF)", type=["pdf"])

if resume_file and jd_file:
    resume_text = extract_text_from_pdf(resume_file)
    jd_text = extract_text_from_pdf(jd_file)

    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(jd_text)

    st.subheader("🔍 Extracted Skills")
    st.write(f"**Resume Skills:** {resume_skills}")
    st.write(f"**Job Description Skills:** {jd_skills}")

    if st.button("🚀 Start Interview"):
        questions = generate_questions(resume_skills, jd_skills)
        
        for i, question in enumerate(questions):
            st.subheader(f"❓ Question {i+1}: {question}")
            
            # AI speaks the question
            speech_audio = text_to_speech(question)
            st.audio(speech_audio, format="audio/mp3")
            
            st.write("🎙️ Speak your answer...")
            user_answer = speech_to_text()
            st.write(f"🗣️ Your Answer: {user_answer}")

            # AI evaluates the answer
            eval_prompt = f"Evaluate this answer: '{user_answer}' for the question: '{question}'. Provide feedback."
            eval_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": eval_prompt}]
            )
            
            feedback = eval_response["choices"][0]["message"]["content"]
            st.write(f"📢 **AI Feedback:** {feedback}")

        st.success("✅ Interview Completed! Generating Final Report...")

        # Generate final evaluation summary
        final_eval_prompt = f"""
        Based on the candidate's answers, generate a detailed evaluation report including:
        - Strengths
        - Areas to improve
        - Overall score (out of 10)
        """
        
        final_eval = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": final_eval_prompt}]
        )
        
        st.subheader("📊 Final Evaluation Report")
        st.write(final_eval["choices"][0]["message"]["content"])
