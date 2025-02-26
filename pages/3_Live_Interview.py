import asyncio
import base64
import json
import os
import pyaudio
import streamlit as st
from websockets.asyncio.client import connect

# Initialize session state variables
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'interview_started' not in st.session_state:
    st.session_state.interview_started = False
if 'interview_completed' not in st.session_state:
    st.session_state.interview_completed = False
if 'job_description' not in st.session_state:
    st.session_state.job_description = ""
if 'resume_text' not in st.session_state:
    st.session_state.resume_text = ""
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'listening' not in st.session_state:
    st.session_state.listening = False

class AIInterview:
    def __init__(self, jd_text, resume_text):
        self.api_key = os.environ.get("GEMINI_API_KEY") or st.session_state.api_key
        self.model = "gemini-2.0-flash-exp"
        self.uri = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={self.api_key}"
        self.jd_text = jd_text
        self.resume_text = resume_text
        self.conversation = []  # Store conversation history

        # Audio settings
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.CHUNK = 512

    async def start(self):
        """Initialize AI interview session with JD & Resume context."""
        self.ws = await connect(self.uri, additional_headers={"Content-Type": "application/json"})
        await self.ws.send(json.dumps({"setup": {"model": f"models/{self.model}"}}))
        await self.ws.recv(decode=False)

        print("Connected to Gemini AI. Starting the interview...")

        # Generate the first interview question
        first_question = self.generate_first_question()
        self.conversation.append({"role": "AI", "text": first_question})
        await self.speak(first_question)

        # Start audio streaming using asyncio.gather()
        await asyncio.gather(
            self.send_user_audio(),
            self.recv_model_audio(),
        )

    def generate_first_question(self):
        """Generate an opening question using JD & Resume."""
        prompt = f"""
        You are an AI interviewer. You will ask relevant questions based on the given Job Description and Resume.

        JOB DESCRIPTION:
        {self.jd_text}

        CANDIDATE'S RESUME:
        {self.resume_text}

        Ask a professional, relevant, and engaging first question to start the interview.
        """
        return self.query_gemini(prompt)

    def generate_follow_up(self, user_response):
        """Generate a follow-up question based on the JD, Resume, and conversation history."""
        self.conversation.append({"role": "Candidate", "text": user_response})
        conversation_history = "\n".join([f"{entry['role']}: {entry['text']}" for entry in self.conversation])

        prompt = f"""
        You are an AI interviewer. Use the following conversation history and the given Job Description & Resume to generate a logical, relevant follow-up question.

        JOB DESCRIPTION:
        {self.jd_text}

        CANDIDATE'S RESUME:
        {self.resume_text}

        CONVERSATION HISTORY:
        {conversation_history}

        Generate the next question.
        """
        return self.query_gemini(prompt)

    def query_gemini(self, prompt):
        """Query Google Gemini API for a response."""
        # Send the request to the Gemini API (simplified synchronous request)
        response = json.dumps({"text": "Placeholder question based on the prompt"})  # Replace with actual API call
        return json.loads(response)["text"]

    async def speak(self, text):
        """Send AI-generated question as speech to the user."""
        payload = {
            "realtime_input": {
                "text": text  # Correct field name for text input
            }
        }
        await self.ws.send(json.dumps(payload))

    async def send_user_audio(self):
        """Stream user audio response to AI for processing."""
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=16000,
            input=True,
            frames_per_buffer=self.CHUNK,
        )

        while True:
            data = await asyncio.to_thread(stream.read, self.CHUNK)
            await self.ws.send(
                json.dumps(
                    {
                        "realtime_input": {
                            "media_chunks": [
                                {
                                    "data": base64.b64encode(data).decode(),
                                    "mime_type": "audio/pcm",
                                }
                            ]
                        }
                    }
                )
            )

    async def recv_model_audio(self):
        """Receive AI-generated speech response and play it."""
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=self.FORMAT, channels=self.CHANNELS, rate=24000, output=True
        )

        async for msg in self.ws:
            response = json.loads(msg)
            try:
                # If AI generates a question, process it
                if "serverContent" in response:
                    model_text = response["serverContent"]["modelTurn"]["parts"][0]["text"]
                    print("AI:", model_text)
                    await self.speak(model_text)

                    # Store conversation and generate the next follow-up
                    follow_up = self.generate_follow_up(model_text)
                    self.conversation.append({"role": "AI", "text": follow_up})
                    await self.speak(follow_up)

                # If AI responds with audio, play it
                audio_data = response["serverContent"]["modelTurn"]["parts"][0]["inlineData"]["data"]
                await asyncio.to_thread(stream.write, base64.b64decode(audio_data))

            except KeyError:
                pass

# Main app UI
st.title("AI Voice Interview Assistant")
st.caption("Powered by Google Gemini")

# Sidebar for configuration
with st.sidebar:
    st.header("Setup Interview")
    
    # API Key input
    api_key = st.text_input("Enter Google Gemini API Key", type="password")
    if api_key:
        st.session_state.api_key = api_key
    
    # Upload JD
    jd_file = st.file_uploader("Upload Job Description (TXT)", type=["txt"])
    if jd_file is not None:
        job_description = jd_file.getvalue().decode("utf-8")
        st.session_state.job_description = job_description
        st.success("Job description uploaded successfully!")
    
    # Or input JD as text
    jd_text = st.text_area("Or paste Job Description here")
    if jd_text:
        st.session_state.job_description = jd_text
        st.success("Job description provided successfully!")
    
    def extract_text_from_resume(uploaded_file):
        """
        Extracts text from an uploaded resume file (PDF, DOCX, or TXT).
        Returns the extracted text or an empty string if extraction fails.
        """
        try:
            if uploaded_file.type == "application/pdf":
                # Extract text from PDF
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                text = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
                return text if text else ""  # Return empty string if no text is extracted

            elif uploaded_file.type == "text/plain":
                # Extract text from TXT
                return uploaded_file.getvalue().decode("utf-8")

            elif "word" in uploaded_file.type:
                # Extract text from DOCX
                import docx
                doc = docx.Document(uploaded_file)
                return " ".join([para.text for para in doc.paragraphs])

            else:
                st.error(f"Unsupported file format: {uploaded_file.type}")
                return ""  # Return empty string for unsupported formats

        except Exception as e:
            st.error(f"Error extracting text from {uploaded_file.name}: {e}")
            return ""  # Return empty string if extraction fails

   # Upload resume
resume_file = st.file_uploader("Upload Resume", type=["pdf", "docx", "txt"])
if resume_file is not None:
    # Validate file size and type
    if resume_file.size == 0:
        st.error("The uploaded file is empty. Please upload a valid file.")
    else:
        resume_text = extract_text_from_resume(resume_file)
        if resume_text.strip():  # Check if text extraction was successful
            st.session_state.resume_text = resume_text
            st.success("Resume processed successfully!")
        else:
            st.error("Failed to extract text from the resume. Please upload a valid file.")
    


    # Debugging: Display session state values
    st.write("Debugging Info:")
    st.write(f"Job Description: {st.session_state.job_description[:100]}...")  # Show first 100 chars
    st.write(f"Resume Text: {st.session_state.resume_text[:100]}...")  # Show first 100 chars
    
    # Start interview button
    if st.button("Start Interview") and not st.session_state.interview_started:
        if not st.session_state.api_key:
            st.error("Please provide a Google Gemini API key.")
        elif not st.session_state.job_description:
            st.error("Please provide a job description.")
        elif not st.session_state.resume_text:
            st.error("Please provide a resume.")
        else:
            st.session_state.interview_started = True
            st.session_state.conversation = []
            st.rerun()

# Main interview area
if st.session_state.interview_started and not st.session_state.interview_completed:
    st.header("Interview in Progress")
    
    # Display conversation history
    for entry in st.session_state.conversation:
        role = "AI" if entry["role"] == "AI" else "You"
        st.write(f"**{role}:** {entry['text']}")
    
    # If no conversation has started, begin with an opening question
    if not st.session_state.conversation:
        client = AIInterview(st.session_state.job_description, st.session_state.resume_text)
        asyncio.run(client.start())
        st.session_state.conversation = client.conversation
        st.rerun()

# Interview results
if st.session_state.interview_completed:
    st.header("Interview Results")
    
    # Display feedback
    st.subheader("Feedback")
    st.write(st.session_state.feedback)
    
    # Export results
    if st.button("Export Results"):
        results = {
            "job_description": st.session_state.job_description,
            "resume": st.session_state.resume_text,
            "conversation": st.session_state.conversation,
            "feedback": st.session_state.feedback
        }
        
        # Convert to JSON
        results_json = json.dumps(results, indent=4)
        
        # Create download button
        st.download_button(
            label="Download JSON",
            data=results_json,
            file_name="interview_results.json",
            mime="application/json"
        )
    
    # Reset interview
    if st.button("Start New Interview"):
        st.session_state.interview_started = False
        st.session_state.interview_completed = False
        st.session_state.conversation = []
        st.session_state.feedback = ""
        st.rerun()