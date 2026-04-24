import os
import json
import cv2
import streamlit as st
import tensorflow as tf
from PIL import Image
import numpy as np
from streamlit_cropper import st_cropper
from groq import Groq
import asyncio
import edge_tts
import gdown
from streamlit_mic_recorder import mic_recorder

# --- AGENTIC LIBRARIES ---
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

# --- 1. CONFIG & API SETUP ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except KeyError:
    st.error("Error: GROQ_API_KEY not found in Secrets. Please add it in Streamlit Cloud Settings.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
st.set_page_config(page_title="Pro Health AI Terminal", page_icon="🏥", layout="wide")

# --- CSS LINKING (OPTION 1) ---
def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"Note: {file_name} file nahi mili. Styling apply nahi hui.")

# Style file ko yahan link kiya gaya hai
style_path = os.path.join(os.path.dirname(__file__), "style.css")
local_css(style_path)

# --- 2. HELPERS ---
def process_audio_data(audio_data):
    if audio_data is None: return None
    filename = "temp_voice.wav"
    with open(filename, "wb") as f:
        f.write(audio_data['bytes'])
    return filename

def get_voice_transcript(audio_path):
    try:
        with open(audio_path, "rb") as file:
            return client.audio.transcriptions.create(
                file=(audio_path, file.read()),
                model="whisper-large-v3",
                response_format="text",
                language="ur"
            )
    except Exception as e: return f"Error: {e}"

async def generate_urdu_voice(text, output_file="ai_advice.mp3"):
    communicate = edge_tts.Communicate(text[:500], "ur-PK-UzmaNeural")
    await communicate.save(output_file)
    return output_file

def text_to_speech_urdu(text):
    output_file = "ai_advice.mp3"
    try:
        asyncio.run(generate_urdu_voice(text, output_file))
        return output_file
    except: return None

def enhance_image(img_pil):
    img_arr = np.array(img_pil)
    lab = cv2.cvtColor(img_arr, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    enhanced_lab = cv2.merge((cl, a, b))
    return Image.fromarray(cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB))

# --- 3. RESOURCE LOADING ---
DRIVE_FILE_ID = '1LJRCdeW9Td2zAqUbT4HaaZAZAqZxZdqT'
url = f'https://drive.google.com/uc?id={DRIVE_FILE_ID}'
model_path = os.path.join(os.path.dirname(__file__), "medical_model.h5")

@st.cache_resource
def load_resources():
    if not os.path.exists(model_path):
        with st.spinner('Downloading AI Model...'):
            try:
                gdown.download(url, model_path, quiet=False)
            except Exception as e:
                st.error(f"Download failed: {e}")

    model = None
    if os.path.exists(model_path):
        try:
            model = tf.keras.models.load_model(model_path, compile=False)
        except Exception:
            from tensorflow.keras.layers import DepthwiseConv2D
            class FixedDepthwiseConv2D(DepthwiseConv2D):
                def __init__(self, *args, **kwargs):
                    if 'groups' in kwargs: kwargs.pop('groups')
                    super().__init__(*args, **kwargs)

            with tf.keras.utils.custom_object_scope({'DepthwiseConv2D': FixedDepthwiseConv2D}):
                try:
                    model = tf.keras.models.load_model(model_path, compile=False)
                except Exception as e:
                    st.error(f"Ultimate loading error: {e}")
    
    labels = ["Healthy", "Jaundice", "Lupus", "Rosacea"]
    return model, labels

model, labels = load_resources()

# --- 4. MAIN UI ---
st.title("🏥 Pro Health AI: Advanced Diagnostic Terminal")
st.markdown("---")

st.markdown('### 📸 Step 1: Upload Scan')
up = st.file_uploader("Upload Skin Image", type=['jpg', 'jpeg', 'png'])
cam = st.camera_input("Or Take Photo")
img_src = up if up else cam

if img_src:
    orig = Image.open(img_src).convert('RGB')
    col1, col2 = st.columns(2)
    with col1:
        st.write("Crop the affected area:")
        cropped = st_cropper(orig, realtime_update=True, box_color='#5bc1ac')
    with col2:
        enhanced = enhance_image(cropped)
        st.image(enhanced, use_column_width=True, caption="✅ Enhanced Scan Ready")
    st.session_state['ready_img'] = enhanced

    with st.sidebar:
        st.header("🎤 Step 2: Voice Symptoms")
        st.write("Record your symptoms in Urdu:")
        audio = mic_recorder(start_prompt="🎤 Start Recording", stop_prompt="🛑 Stop", key='mic')
        
        if audio:
            path = process_audio_data(audio)
            with st.spinner("Transcribing..."):
                st.session_state['transcript'] = get_voice_transcript(path)
        
        if 'transcript' in st.session_state:
            st.success(f"📝 You said: {st.session_state['transcript']}")

    st.markdown('---')
    if st.button("🚀 Run Full AI Analysis"):
        if 'ready_img' in st.session_state and 'transcript' in st.session_state:
            with st.spinner("🔬 AI is analyzing image and voice..."):
                img = st.session_state['ready_img'].resize((224, 224))
                img_arr = np.expand_dims(np.array(img).astype('float32')/255.0, axis=0)
                
                if model:
                    preds = model.predict(img_arr)[0]
                    top_idx = np.argmax(preds)
                    result_str = f"{labels[top_idx]} ({preds[top_idx]*100:.1f}%)"
                else:
                    result_str = "Model processing error."

                llm = ChatGroq(temperature=0.1, groq_api_key=GROQ_API_KEY, model_name="llama-3.3-70b-versatile")
                sys_msg = "You are a Medical Expert. Analyze image results and voice symptoms to provide a brief report and clear advice in Urdu."
                user_msg = f"Detections: {result_str}. Symptoms: {st.session_state['transcript']}."
                
                try:
                    response = llm.invoke([SystemMessage(content=sys_msg), HumanMessage(content=user_msg)])
                    st.markdown(f"<div class='report-box'>### 📋 Diagnostic Report\n{response.content}</div>", unsafe_allow_html=True)
                    
                    voice_path = text_to_speech_urdu(response.content)
                    if voice_path:
                        st.audio(voice_path)
                except Exception as e:
                    st.error(f"AI Analysis failed: {e}")
        else:
            st.warning("Please record your voice symptoms in the sidebar first!")
else:
    st.info("👆 Please upload an image or take a photo to begin.")
