import streamlit as st
import openai
import speech_recognition as sr
from gtts import gTTS
from tempfile import NamedTemporaryFile
import os
import uuid
from io import BytesIO
from pydub import AudioSegment
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import av
import numpy as np

# Set your OpenAI API key securely
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="Malayalam Voice Chatbot")
st.title("🗣️ Malayalam Voice Chatbot with ChatGPT")
st.markdown("Speak freely in Malayalam. This assistant listens live and replies back with voice!")

class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.buffer = b""

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        # Convert audio frame to bytes and accumulate
        pcm = frame.to_ndarray().tobytes()
        self.buffer += pcm
        return frame

# Start WebRTC stream for mic input
ctx = webrtc_streamer(
    key="live-audio",
    mode=WebRtcMode.SENDONLY,
    in_audio=True,
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    audio_processor_factory=AudioProcessor,
)

# Helper to transcribe audio using SpeechRecognition
@st.cache_data(show_spinner=False)
def transcribe_audio(buffer):
    recognizer = sr.Recognizer()
    temp_file = NamedTemporaryFile(delete=False, suffix=".wav")
    temp_file.write(buffer)
    temp_file.flush()
    try:
        with sr.AudioFile(temp_file.name) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="ml-IN")
            return text
    except sr.UnknownValueError:
        return "ക്ഷമിക്കണം, ശബ്ദം മനസ്സിലായില്ല."
    except Exception as e:
        return f"❌ പ്രശ്നം: {str(e)}"
    finally:
        temp_file.close()
        os.remove(temp_file.name)

# Get response from ChatGPT
@st.cache_data(show_spinner=False)
def get_gpt_reply(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": text}]
    )
    return response.choices[0].message.content.strip()

# Speak using gTTS
def speak_text(text):
    tts = gTTS(text=text, lang='ml')
    with NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        tts.save(f.name)
        return f.name

# Check if live audio stream is active and has enough data
if ctx and ctx.audio_processor and len(ctx.audio_processor.buffer) > 16000 * 3:  # ~3 seconds
    st.success("✅ Audio captured successfully")
    st.info("🎧 Processing your Malayalam question...")
    query_text = transcribe_audio(ctx.audio_processor.buffer)
    st.markdown(f"**🗣️ You said:** {query_text}")

    if query_text and "ക്ഷമിക്കണം" not in query_text:
        with st.spinner("🤖 ChatGPT is thinking..."):
            answer = get_gpt_reply(query_text)
        st.markdown(f"**🤖 Answer:** {answer}")

        mp3_path = speak_text(answer)
        audio_file = open(mp3_path, 'rb')
        st.audio(audio_file.read(), format='audio/mp3')
        audio_file.close()
        os.remove(mp3_path)
