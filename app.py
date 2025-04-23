import streamlit as st
import openai
import speech_recognition as sr
from gtts import gTTS
from tempfile import NamedTemporaryFile
import os
import uuid
from io import BytesIO
from streamlit_mic_recorder import mic_recorder

# Set your OpenAI API key securely
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="Malayalam Voice Chatbot")
st.title("🗣️ Malayalam Voice Chatbot with ChatGPT")
st.markdown("Speak directly using your mic in Malayalam — and get intelligent replies spoken back to you!")

# Record voice directly from browser
wav_audio = mic_recorder(start_prompt="🎙️ Click to Speak in Malayalam", stop_prompt="🛑 Stop Recording", key="recorder")

# Transcribe Malayalam audio
def transcribe_audio_bytes(audio_bytes):
    recognizer = sr.Recognizer()
    with NamedTemporaryFile(delete=False, suffix=".wav") as f:
        f.write(audio_bytes)
        f.flush()
        with sr.AudioFile(f.name) as source:
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

# Speak Malayalam using gTTS
def speak_text(text):
    tts = gTTS(text=text, lang='ml')
    with NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        tts.save(f.name)
        return f.name

# Main logic
if wav_audio is not None:
    st.success("✅ Voice recorded successfully!")
    query_text = transcribe_audio_bytes(wav_audio)
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
