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

# --- 1. CONFIG & CSS SETUP ---
st.set_page_config(page_title="Pro Health AI Terminal", page_icon="🏥", layout="wide")

def load_css(file_name):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        css_path = os.path.join(current_dir, file_name)
        if os.path.exists(css_path):
            with open(css_path) as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except Exception:
        pass

load_css("style.css")

# --- 2. API SETUP ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except KeyError:
    st.error("Error: GROQ_API_KEY not found in Secrets.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

# --- 3. HELPERS ---
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

# --- 4. RESOURCE LOADING ---
# Note: Aapne kaha ke dataset bada hai, isliye labels ki list ko apne model ke mutabiq update karein
@st.cache_resource
def load_resources():
    DRIVE_FILE_ID = '1LJRCdeW9Td2zAqUbT4HaaZAZAqZxZdqT'
    model_path = os.path.join(os.path.dirname(__file__), "medical_model.h5")
    
    if not os.path.exists(model_path):
        url = f'https://drive.google.com/uc?id={DRIVE_FILE_ID}'
        gdown.download(url, model_path, quiet=False)

    # APNE SAARE LABELS YAHAN LIKHEIN (Order wahi ho jo training mein tha)
    labels = ["Healthy", "Jaundice", "Lupus", "Rosacea", "Acne", "Eczema", "Melanoma", "Psoriasis"] 
    
    model = None
    try:
        model = tf.keras.models.load_model(model_path, compile=False)
    except Exception:
        from tensorflow.keras.layers import DepthwiseConv2D
        class FixedDepthwiseConv2D(DepthwiseConv2D):
            def __init__(self, *args, **kwargs):
                if 'groups' in kwargs: kwargs.pop('groups')
                super().__init__(*args, **kwargs)
        with tf.keras.utils.custom_object_scope({'DepthwiseConv2D': FixedDepthwiseConv2D}):
            model = tf.keras.models.load_model(model_path, compile=False)
    
    return model, labels

model, labels = load_resources()

# --- 5. MAIN UI ---
st.title("🏥 Pro Health AI: Advanced Diagnostic Terminal")

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
        st.image(enhanced, use_column_width=True, caption="✅ Scan Ready")
    st.session_state['ready_img'] = enhanced

    with st.sidebar:
        st.header("🎤 Voice Symptoms")
        audio = mic_recorder(start_prompt="🎤 Start Recording", stop_prompt="🛑 Stop", key='mic')
        if audio:
            path = process_audio_data(audio)
            st.session_state['transcript'] = get_voice_transcript(path)
        if 'transcript' in st.session_state:
            st.success(f"📝 Transcribed: {st.session_state['transcript']}")

    if st.button("🚀 Run Full AI Analysis"):
        if 'ready_img' in st.session_state and 'transcript' in st.session_state:
            with st.spinner("🔬 Picture aur Voice ka muqabla kiya ja raha hai..."):
                # 1. Image Prediction
                img = st.session_state['ready_img'].resize((224, 224))
                img_arr = np.expand_dims(np.array(img).astype('float32')/255.0, axis=0)
                
                preds = model.predict(img_arr)[0]
                top_idx = np.argmax(preds)
                detected_name = labels[top_idx]
                confidence = preds[top_idx]*100

                # 2. AI Agent Reasoning (Match Picture with Voice)
                llm = ChatGroq(temperature=0, groq_api_key=GROQ_API_KEY, model_name="llama-3.3-70b-versatile")
                
                sys_msg = f"""You are a Senior Medical Consultant.
                STRICT PROTOCOL:
                - Image Model ne '{detected_name}' detect kiya hai (Confidence: {confidence:.1f}%).
                - User ne ye symptoms bataye hain: '{st.session_state['transcript']}'.
                - Aapne image detection ko primary rakhna hai lekin voice symptoms se confirm karna hai.
                - Agar dono match karte hain, toh detail mein Urdu mein samjhayein.
                - Agar image aur voice bilkul alag hain, toh politely batayein ke mazeed checkup ki zaroorat hai.
                - Report hamesha Urdu mein honi chahiye."""

                user_msg = f"Visual Detection: {detected_name}. Audio Symptoms: {st.session_state['transcript']}."
                
                try:
                    response = llm.invoke([SystemMessage(content=sys_msg), HumanMessage(content=user_msg)])
                    st.markdown(f"### 📋 Final Diagnostic Report\n{response.content}")
                    
                    voice_path = text_to_speech_urdu(response.content)
                    if voice_path: st.audio(voice_path)
                except Exception as e:
                    st.error(f"Analysis Error: {e}")
        else:
            st.warning("Pehle image upload karein aur voice record karein!")
