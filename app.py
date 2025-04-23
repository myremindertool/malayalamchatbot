import streamlit as st
import openai
import speech_recognition as sr
from gtts import gTTS
from tempfile import NamedTemporaryFile
import os
import uuid
from io import BytesIO
import base64

# Set your OpenAI API key (recommended to use st.secrets in deployment)
openai.api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else "YOUR_API_KEY_HERE"

# Title
st.set_page_config(page_title="Malayalam Voice Chatbot")
st.title("🗣️ Malayalam Voice Chatbot with ChatGPT")
st.markdown("Speak in Malayalam and get intelligent replies spoken back to you!")

# Audio Recorder (using browser microphone)
with st.expander("🎤 Record Your Question"):
    audio_file = st.file_uploader("Upload a .wav audio in Malayalam", type=["wav"])

# Transcribe Malayalam audio
def transcribe_audio(file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data, language="ml-IN")
            return text
        except sr.UnknownValueError:
            return "ക്ഷമിക്കണം, ശബ്ദം മനസ്സിലായില്ല."
        except Exception as e:
            return f"തെറ്റായിരിക്കുന്നു: {str(e)}"

# Get response from OpenAI
@st.cache_data(show_spinner=False)
def get_gpt_reply(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": text}]
    )
    return response.choices[0].message.content.strip()

# Convert text to Malayalam audio using gTTS
def speak_text(text):
    tts = gTTS(text=text, lang='ml')
    with NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        tts.save(f.name)
        return f.name

# Process input and respond
if audio_file is not None:
    st.info("🔍 Transcribing your Malayalam audio...")
    with open("temp_audio.wav", "wb") as f:
        f.write(audio_file.read())

    query_text = transcribe_audio("temp_audio.wav")
    st.markdown(f"**🗣️ You said:** {query_text}")

    if query_text and "ക്ഷമിക്കണം" not in query_text:
        with st.spinner("🤖 ChatGPT is thinking..."):
            answer = get_gpt_reply(query_text)
        st.markdown(f"**🤖 Answer:** {answer}")

        mp3_path = speak_text(answer)
        audio_file = open(mp3_path, 'rb')
        audio_bytes = audio_file.read()
        st.audio(audio_bytes, format='audio/mp3')

        audio_file.close()
        os.remove(mp3_path)

    os.remove("temp_audio.wav")
