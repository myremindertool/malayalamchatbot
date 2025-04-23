import streamlit as st
import openai
import speech_recognition as sr
from gtts import gTTS
from tempfile import NamedTemporaryFile
import os
import uuid
from io import BytesIO
from pydub import AudioSegment
import base64

# Set your OpenAI API key securely
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="Malayalam Voice Chatbot")
st.title("🗣️ Malayalam Voice Chatbot with ChatGPT")
st.markdown("Malayalam AI voice assistant — starts listening automatically. Speak now!")

# Inject JavaScript to auto-record on load
st.markdown("""
    <script>
    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
        const mediaRecorder = new MediaRecorder(stream);
        let chunks = [];
        mediaRecorder.ondataavailable = e => chunks.push(e.data);
        mediaRecorder.onstop = () => {
            const blob = new Blob(chunks, { 'type': 'audio/webm' });
            const reader = new FileReader();
            reader.readAsDataURL(blob);
            reader.onloadend = function() {
                const base64data = reader.result;
                fetch("/upload_audio", {
                    method: "POST",
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ audio: base64data })
                });
            };
        };
        mediaRecorder.start();
        setTimeout(() => mediaRecorder.stop(), 5000);  // record for 5 seconds
    });
    </script>
""", unsafe_allow_html=True)

# Placeholder to simulate audio received (Streamlit Cloud does not support JS post handlers)
st.info("👂 Listening for Malayalam audio... (simulate in local test only)")

# Transcribe Malayalam audio from raw bytes
def transcribe_audio_bytes(audio_bytes):
    recognizer = sr.Recognizer()
    try:
        audio_segment = AudioSegment.from_file(BytesIO(audio_bytes), format="webm")
        with NamedTemporaryFile(delete=False, suffix=".wav") as f:
            audio_segment.export(f.name, format="wav")
            with sr.AudioFile(f.name) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data, language="ml-IN")
                return text
    except sr.UnknownValueError:
        return "ക്ഷമിക്കണം, ശബ്ദം മനസ്സിലായില്ല."
    except Exception as e:
        return f"❌ പ്രശ്നം: {str(e)}"

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

# Placeholder for uploaded audio simulation
# In real use, integrate server endpoint or simulate with local test audio
if False:  # Replace with True for local simulation
    with open("sample.webm", "rb") as f:
        raw_audio = f.read()
    query_text = transcribe_audio_bytes(raw_audio)
    st.markdown(f"**🗣️ You said:** {query_text}")
    if query_text and "ക്ഷമിക്കണം" not in query_text:
        answer = get_gpt_reply(query_text)
        st.markdown(f"**🤖 Answer:** {answer}")
        mp3_path = speak_text(answer)
        st.audio(open(mp3_path, 'rb').read(), format='audio/mp3')
        os.remove(mp3_path)
