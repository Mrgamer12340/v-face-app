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
st.set_page_config(page_title="Pro Health AI - Diagnostic", page_icon="🏥", layout="wide")

# --- 2. STYLE LOADING ---
def load_css(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("style.css")

# --- 3. HELPER FUNCTIONS ---
def process_audio_data(audio_data):
    if audio_data is None:
        return None
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
    except Exception as e:
        return f"Transcription Error: {e}"

async def generate_urdu_voice(text, output_file="ai_advice.mp3"):
    # Limiting text length for TTS to prevent errors
    short_text = text[:500] 
    communicate = edge_tts.Communicate(short_text, "ur-PK-UzmaNeural")
    await communicate.save(output_file)
    return output_file

def text_to_speech_urdu(text):
    output_file = "ai_advice.mp3"
    try:
        asyncio.run(generate_urdu_voice(text, output_file))
        return output_file
    except Exception as e:
        st.warning(f"Voice generation failed: {e}")
        return None

def enhance_image(img_pil):
    img_arr = np.array(img_pil)
    lab = cv2.cvtColor(img_arr, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    enhanced_lab = cv2.merge((cl, a, b))
    return Image.fromarray(cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB))

def get_all_predictions(model, img_arr, labels):
    preds = model.predict(img_arr)[0]
    results = []
    for i, conf in enumerate(preds):
        results.append({"label": labels[i], "confidence": float(conf) * 100})
    results.sort(key=lambda x: x["confidence"], reverse=True)
    return results

# --- 4. RESOURCE LOADING ---
DRIVE_FILE_ID = '1LJRCdeW9Td2zAqUbT4HaaZAZAqZxZdqT'
url = f'https://drive.google.com/uc?id={DRIVE_FILE_ID}'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, "medical_model.h5")
labels_path = os.path.join(BASE_DIR, "models", "labels.json")

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
        except Exception as e:
            st.error(f"Model load error: {e}")
    
    if os.path.exists(labels_path):
        with open(labels_path, "r") as f:
            idx_map = json.load(f)
        labels = [k for k, v in sorted(idx_map.items(), key=lambda x: x[1])]
    else:
        labels = ["Healthy", "Jaundice", "Lupus", "Rosacea"]
        
    return model, labels

model, labels = load_resources()

# --- 5. MAIN UI ---
st.title("🏥 Pro Health AI: Advanced Diagnostic Terminal")
st.markdown("---")

# STEP 1: IMAGE
st.markdown('### 📸 Step 1: Upload Image')
col_up, col_cam = st.columns(2)
with col_up:
    up = st.file_uploader("Choose File", type=['jpg', 'png', 'jpeg'])
with col_cam:
    cam = st.camera_input("Take Photo")

img_src = up if up else cam

if img_src:
    orig = Image.open(img_src).convert('RGB')
    col_crop, col_preview = st.columns(2)
    with col_crop:
        cropped_img = st_cropper(orig, realtime_update=True, box_color='#5bc1ac')
    with col_preview:
        enhanced = enhance_image(cropped_img)
        st.image(enhanced, use_column_width=True, caption="✅ Enhanced Scan")
    st.session_state['enhanced_img'] = enhanced

    # STEP 2: VOICE (SIDEBAR)
    with st.sidebar:
        st.header("🎤 Step 2: Symptoms")
        st.write("Record your symptoms in Urdu:")
        audio_data = mic_recorder(start_prompt="🎤 Start Recording", stop_prompt="🛑 Stop", key='recorder')
        
        if audio_data:
            audio_file = process_audio_data(audio_data)
            with st.spinner("Processing Voice..."):
                st.session_state['transcript'] = get_voice_transcript(audio_file)
        
        if 'transcript' in st.session_state:
            st.success(f"📝 You said: {st.session_state['transcript']}")

    # STEP 3: ANALYSIS
    st.markdown('---')
    st.markdown('### ⚡ Step 3: Result')
    if st.button("🚀 Run Full Analysis"):
        if 'enhanced_img' in st.session_state and 'transcript' in st.session_state:
            with st.spinner("🔬 AI is analyzing..."):
                # Image Pred
                img_resized = st.session_state['enhanced_img'].resize((224, 224))
                img_arr = np.array(img_resized).astype('float32') / 255.0
                img_arr = np.expand_dims(img_arr, axis=0)
                
                predictions = get_all_predictions(model, img_arr, labels) if model else []
                pred_str = ", ".join([f"{p['label']} ({p['confidence']:.1f}%)" for p in predictions[:2]])
                
                # AI Agent Report
                llm = ChatGroq(temperature=0.1, groq_api_key=GROQ_API_KEY, model_name="llama-3.3-70b-versatile")
                sys_prompt = "You are a Medical AI. Provide a brief report and clear health advice in Urdu based on detections and symptoms."
                user_prompt = f"Detections: {pred_str}. Symptoms: {st.session_state['transcript']}."
                
                try:
                    response = llm.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=user_prompt)])
                    st.markdown(response.content)
                    
                    # TTS
                    audio_out = text_to_speech_urdu(response.content)
                    if audio_out:
                        st.audio(audio_out)
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
        else:
            st.warning("Please record your voice symptoms in the sidebar first!")
else:
    st.info("Please upload an image to start.")
