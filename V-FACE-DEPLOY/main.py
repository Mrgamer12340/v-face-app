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
import noisereduce as nr
from streamlit_mic_recorder import mic_recorder

# --- AGENTIC LIBRARIES ---
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

# --- 1. CONFIG & API SETUP ---
# Streamlit Secrets se API Key uthayega
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=GROQ_API_KEY)

os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
st.set_page_config(page_title="Pro Health AI - Advanced Diagnostic", page_icon="🏥", layout="wide")

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
    # Browser se aane wale audio bytes ko file mein save karna
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
        return f"Could not transcribe audio: {e}"

async def generate_urdu_voice(text, output_file="ai_advice.mp3"):
    communicate = edge_tts.Communicate(text, "ur-PK-UzmaNeural")
    await communicate.save(output_file)
    return output_file

def text_to_speech_urdu(text):
    output_file = "ai_advice.mp3"
    try:
        asyncio.run(generate_urdu_voice(text, output_file))
        return output_file
    except Exception as e:
        st.warning(f"Could not generate voice: {e}")
        return None

def enhance_image(img_pil):
    img_arr = np.array(img_pil)
    lab = cv2.cvtColor(img_arr, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    enhanced_lab = cv2.merge((cl, a, b))
    return Image.fromarray(cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB))

def get_all_predictions(model, img_arr, labels, threshold=0.75):
    preds = model.predict(img_arr)[0]
    results = []
    for i, conf in enumerate(preds):
        if conf * 100 >= threshold * 100:
            results.append({
                "label": labels[i],
                "confidence": conf * 100,
                "high_confidence": True
            })
    results.sort(key=lambda x: x["confidence"], reverse=True)
    if not results:
        top_idx = np.argmax(preds)
        results.append({
            "label": labels[top_idx],
            "confidence": preds[top_idx] * 100,
            "high_confidence": False
        })
    return results

# --- 4. RESOURCE LOADING (CLOUD SETUP) ---
# Yahan apni sahi wali Google Drive ID likhein
DRIVE_FILE_ID = '1LJRCdeW9Td2zAqUbT4HaaZAZAqZxZdqT' 
url = f'https://drive.google.com/uc?id={DRIVE_FILE_ID}'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, "medical_model.h5")
labels_path = os.path.join(BASE_DIR, "models", "labels.json")

@st.cache_resource
def load_resources():
    if not os.path.exists(model_path):
        with st.spinner('Downloading AI Model from Cloud... Please wait.'):
            try:
                gdown.download(url, model_path, quiet=False)
            except Exception as e:
                st.error(f"Download failed: {e}")

    model = None
    if os.path.exists(model_path):
        model = tf.keras.models.load_model(model_path, compile=False)
    
    if os.path.exists(labels_path):
        with open(labels_path, "r") as f:
            idx_map = json.load(f)
        labels = [k for k, v in sorted(idx_map.items(), key=lambda x: x[1])]
    else:
        labels = ["Healthy", "Jaundice", "Lupus", "Rosacea"]
        
    return model, labels

model, labels = load_resources()

# ─────────────────────────────────────────────
# --- 5. MAIN UI ---
# ─────────────────────────────────────────────
st.title("🏥 Pro Health AI: Advanced Diagnostic Terminal")
st.markdown("---")

# STEP 1 ─ IMAGE UPLOAD
st.markdown('<span class="step-badge">1</span> **Upload Image or Take a Photo**', unsafe_allow_html=True)

col_up, col_cam = st.columns(2)
with col_up:
    up = st.file_uploader("Upload Image", type=['jpg', 'png', 'jpeg'], key="img_upload")
with col_cam:
    cam = st.camera_input("Or Take a Live Photo", key="img_cam")

img_src = up if up else cam

if img_src:
    orig = Image.open(img_src).convert('RGB')
    col_crop, col_preview = st.columns([1, 1])
    with col_crop:
        st.write("Crop the affected area:")
        cropped_img = st_cropper(orig, realtime_update=True, box_color='#5bc1ac', aspect_ratio=None)
    with col_preview:
        enhanced = enhance_image(cropped_img)
        st.image(enhanced, use_column_width=True, caption="✅ Enhanced Scan")

    st.session_state['enhanced_img'] = enhanced
    st.markdown("---")

    # STEP 2 ─ VOICE RECORDING (SIDEBAR)
    with st.sidebar:
        st.header("🎤 Step 2: Describe Symptoms")
        st.write("Record your symptoms in Urdu:")
        
        # Browser-friendly Mic Recorder
        audio_data = mic_recorder(
            start_prompt="🎤 Start Recording",
            stop_prompt="🛑 Stop Recording",
            key='recorder'
        )

        if audio_data:
            audio_file = process_audio_data(audio_data)
            if audio_file:
                st.session_state['audio_path'] = audio_file
                with st.spinner("Transcribing..."):
                    st.session_state['transcript'] = get_voice_transcript(audio_file)
                st.success("✅ Voice captured!")

        if 'transcript' in st.session_state:
            st.info(f"📝 **You said:** {st.session_state['transcript']}")

    # STEP 3 ─ ANALYSIS
    st.markdown('<span class="step-badge">3</span> **Run Analysis**', unsafe_allow_html=True)
    img_ready = 'enhanced_img' in st.session_state
    voice_ready = 'transcript' in st.session_state and st.session_state['transcript']

    analyze_btn = st.button("⚡ Run Full Analysis", disabled=(not img_ready or not voice_ready))

    if analyze_btn:
        with st.spinner("🔬 Analyzing image and voice data..."):
            enhanced_img = st.session_state['enhanced_img']
            img_resized = enhanced_img.resize((224, 224))
            img_arr = np.array(img_resized).astype('float32') / 255.0
            img_arr = np.expand_dims(img_arr, axis=0)

            if model:
                image_diseases = get_all_predictions(model, img_arr, labels, threshold=0.75)
            else:
                image_diseases = [{"label": "Model Not Loaded", "confidence": 0, "high_confidence": False}]

            high_conf_diseases = [d for d in image_diseases if d["high_confidence"]]
            low_conf_top = [d for d in image_diseases if not d["high_confidence"]]

            if high_conf_diseases:
                image_summary = "Detected: " + ", ".join([f"{d['label']} ({d['confidence']:.1f}%)" for d in high_conf_diseases])
            else:
                top = low_conf_top[0] if low_conf_top else {"label": "Unknown", "confidence": 0}
                image_summary = f"Closest match: {top['label']} ({top['confidence']:.1f}%)"

            transcript = st.session_state.get('transcript', '')

            # LLM Analysis
            llm = ChatGroq(temperature=0.1, groq_api_key=GROQ_API_KEY, model_name="llama-3.3-70b-versatile")
            system_msg = "You are a Medical Expert. Analyze image and voice to provide a report and short Urdu advice."
            user_msg = f"Image: {image_summary}. Voice: {transcript}."

            try:
                response = llm.invoke([SystemMessage(content=system_msg), HumanMessage(content=user_msg)])
                st.markdown(f"### 📋 Final Report\n{response.content}")
                
                # Urdu Speech Generation
                urdu_text = response.content.split('Urdu')[-1] if 'Urdu' in response.content else "ڈاکٹر سے مشورہ کریں۔"
                ai_audio_path = text_to_speech_urdu(urdu_text)
                if ai_audio_path:
                    st.audio(ai_audio_path)
            except Exception as e:
                st.error(f"Analysis failed: {e}")
else:
    st.info("👆 Please upload an image first.")
