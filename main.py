import streamlit as st
from extract_pdf import extract_text_pdf
from generate_questions import generate_interview_questions
import tempfile

st.title("Prepmate AI - Interview Preparation")

# User selects domain
domain = st.selectbox("Select Your Domain", ["IT", "ECE", "EEE", "Mechanical"])

# File Upload
uploaded_file = st.file_uploader("Upload your Job Description (PDF)", type="pdf")

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(uploaded_file.read())
        temp_path = temp_file.name

    # Extract Text
    extracted_text = extract_text_pdf(temp_path)

    # Display Extracted JD
    st.subheader("Extracted Job Description Text:")
    st.write(extracted_text)

    # Generate Questions
    if st.button("Generate Interview Questions"):
        with st.spinner("Generating Questions..."):
            questions = generate_interview_questions(extracted_text, domain)

        # Debugging: Print questions
        print("Generated Questions:", questions)

        if questions:
            st.subheader("Answer the Interview Questions:")
            for i, question in enumerate(questions):
                st.write(f"**Q{i+1}: {question}**")
                st.text_area(f"Your Answer (Q{i+1})", key=f"answer_{i+1}")
        else:
            st.error("No questions generated. Please try again.")
