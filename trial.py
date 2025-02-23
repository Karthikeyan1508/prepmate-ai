import streamlit as st

st.title("I will be back by 12 PM")
st.write("Hello, world!")

prompt = st.chat_input("Say something")
if prompt:
    st.write(f"User has sent the following prompt: {prompt}")