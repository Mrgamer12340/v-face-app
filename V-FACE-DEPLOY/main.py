import os
import json
import cv2
import streamlit as st
import tensorflow as tf
from PIL import Image
import numpy as np
from streamlit_cropper import st_cropper
from groq import Groq
import sounddevice as sd
from scipy.io.wavfile import write
import noisereduce as nr
import asyncio
import edge_tts

# --- AGENTIC LIBRARIES ---
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

# --- 1. CONFIG & API SETUP -
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=GROQ_API_KEY)

os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
st.set_page_config(page_title="Pro Health AI - Advanced Diagnostic", page_icon="🏥", layout="wide")
# for style
st.set_page_config(page_title="Pro Health AI", page_icon="🏥", layout="wide")
def load_css(file_path):
    with open(file_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("style.css")

# --- 3. HELPER FUNCTIONS ---

def record_audio_auto_stop(fs=44100, silence_threshold=0.015, silence_duration=5.0):
    filename = "temp_voice.wav"
    chunk_size = 1024
    recording = []
    try:
        sd._terminate()
        sd._initialize()
        with sd.InputStream(samplerate=fs, channels=1, dtype='float32') as stream:
            st.info("🎤 Listening... Speak now (stops after 5 seconds of silence)")
            silent_chunks = 0
            max_silent_chunks = int(fs / chunk_size * silence_duration)
            while True:
                data, _ = stream.read(chunk_size)
                recording.append(data.copy())
                rms = np.sqrt(np.mean(data ** 2))
                if rms < silence_threshold:
                    silent_chunks += 1
                else:
                    silent_chunks = 0
                if silent_chunks > max_silent_chunks:
                    break

        full_audio = np.concatenate(recording, axis=0).flatten()
        reduced_noise_audio = nr.reduce_noise(y=full_audio, sr=fs, prop_decrease=0.85)
        audio_int16 = (reduced_noise_audio * 32767).astype(np.int16)
        write(filename, fs, audio_int16)
        return filename
    except Exception as e:
        st.error(f"Microphone Error: {e}")
        return None


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
    """
    Returns all diseases that have confidence >= threshold (75%).
    If none pass the threshold, returns the top prediction anyway
    with a low-confidence warning.
    """
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


# --- 4. RESOURCE LOADING ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, "models", "medical_model.h5")
labels_path = os.path.join(BASE_DIR, "models", "labels.json")


@st.cache_resource
def load_resources():
    model = tf.keras.models.load_model(model_path, compile=False) if os.path.exists(model_path) else None
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

# ══════════════════════════════════════════════
# STEP 1 ─ IMAGE UPLOAD
# ══════════════════════════════════════════════
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
        cropped_img = st_cropper(
            orig,
            realtime_update=True,
            box_color='#5bc1ac',
            aspect_ratio=None
        )
    with col_preview:
        enhanced = enhance_image(cropped_img)
        st.image(enhanced, use_column_width=True, caption="✅ Enhanced Scan")

    st.session_state['enhanced_img'] = enhanced
    st.success("✅ Image ready! Now record your symptoms using the sidebar.")
    st.markdown("---")

    # ══════════════════════════════════════════════
    # STEP 2 ─ VOICE RECORDING (sidebar)
    # ══════════════════════════════════════════════
    with st.sidebar:
        st.header("🎤 Step 2: Describe Symptoms")
        st.markdown(
            "After uploading your image, press the button below "
            "and describe your symptoms in Urdu."
        )

        if st.button("🎤 Record Symptoms"):
            if 'enhanced_img' not in st.session_state:
                st.warning("Please upload an image first!")
            else:
                audio_file = record_audio_auto_stop()
                if audio_file:
                    st.session_state['audio_path'] = audio_file
                    with st.spinner("Transcribing your voice..."):
                        st.session_state['transcript'] = get_voice_transcript(audio_file)
                    st.success("✅ Voice captured!")

        if 'audio_path' in st.session_state:
            st.audio(st.session_state['audio_path'])
            st.markdown("**📝 You said:**")
            st.info(st.session_state.get('transcript', '...'))

    # ══════════════════════════════════════════════
    # STEP 3 ─ ANALYSIS BUTTON
    # ══════════════════════════════════════════════
    st.markdown('<span class="step-badge">3</span> **Run Analysis**', unsafe_allow_html=True)

    img_ready = 'enhanced_img' in st.session_state
    voice_ready = 'transcript' in st.session_state and st.session_state['transcript']

    if img_ready and voice_ready:
        st.success("✅ Image and voice are both ready — run the analysis!")
    elif img_ready and not voice_ready:
        st.warning("⚠️ Please record your symptoms (sidebar button) before running analysis.")

    analyze_btn = st.button(
        "⚡ Run Full Analysis",
        disabled=(not img_ready or not voice_ready)
    )

    if analyze_btn:
        with st.spinner("🔬 Analyzing image and voice data..."):

            enhanced_img = st.session_state['enhanced_img']
            img_resized = enhanced_img.resize((224, 224))
            img_arr = np.array(img_resized).astype('float32') / 255.0
            img_arr = np.expand_dims(img_arr, axis=0)

            image_diseases = []
            CONFIDENCE_THRESHOLD = 75.0

            if model:
                image_diseases = get_all_predictions(model, img_arr, labels, threshold=CONFIDENCE_THRESHOLD)
            else:
                image_diseases = [{"label": "Model Not Loaded", "confidence": 0, "high_confidence": False}]

            high_conf_diseases = [d for d in image_diseases if d["high_confidence"]]
            low_conf_top = [d for d in image_diseases if not d["high_confidence"]]

            if high_conf_diseases:
                image_summary = "Image shows these diseases with 75%+ confidence: " + \
                    ", ".join([f"{d['label']} ({d['confidence']:.1f}%)" for d in high_conf_diseases])
            else:
                top = low_conf_top[0] if low_conf_top else {"label": "Unknown", "confidence": 0}
                image_summary = (
                    f"No disease detected above 75% confidence. "
                    f"Closest match: {top['label']} ({top['confidence']:.1f}%) — uncertain result."
                )

            transcript = st.session_state.get('transcript', '')

            # ── LLM Combined Analysis ──────────────────────
            llm = ChatGroq(
                temperature=0.1,
                groq_api_key=GROQ_API_KEY,
                model_name="llama-3.3-70b-versatile"
            )

            system_msg = """You are an Expert Medical AI Diagnostic Agent.

You receive TWO inputs:
1. Image Analysis Result - what the vision model detected in the patient's photo
2. Voice Transcript - what the patient said about their symptoms in Urdu

Your job:
- Analyze BOTH inputs together to give the best possible diagnosis
- Provide a professional English clinical report covering:
  * Visual Findings (from image)
  * Symptom Analysis (from voice)
  * Combined Assessment
  * Recommended Next Steps
- Then generate a SHORT Urdu voice summary (2-3 sentences ONLY) suitable for text-to-speech.
  The Urdu part should mention what disease is likely based on image and symptoms, and advise the patient to see a doctor.

Output format (strictly follow this — no extra text outside these tags):
ENGLISH_REPORT_START
[Professional English clinical report here]
ENGLISH_REPORT_END
###
URDU_ADVICE_START
[صرف 2 سے 3 جملے اردو میں — بیماری کا نام، مختصر وجہ، اور ڈاکٹر سے ملنے کی ہدایت۔ یہ آواز میں سنایا جائے گا۔]
URDU_ADVICE_END"""

            user_msg = f"""
Image Analysis: {image_summary}

Patient Voice Transcript (Urdu): {transcript}

Please analyze both together and provide the combined diagnostic report.
"""

            try:
                response = llm.invoke([
                    SystemMessage(content=system_msg),
                    HumanMessage(content=user_msg)
                ])
                full_content = response.content

                # Parse response
                if "###" in full_content:
                    parts = full_content.split("###")
                    eng_part = parts[0]
                    urdu_part = parts[1] if len(parts) > 1 else "ڈاکٹر سے رابطہ کریں۔"
                else:
                    eng_part = full_content
                    urdu_part = "براہ کرم ڈاکٹر سے رابطہ کریں۔"

                # Clean tags
                for tag in ["ENGLISH_REPORT_START", "ENGLISH_REPORT_END",
                            "URDU_ADVICE_START", "URDU_ADVICE_END"]:
                    eng_part = eng_part.replace(tag, "")
                    urdu_part = urdu_part.replace(tag, "")

                eng_report = eng_part.strip()
                urdu_mashwara = urdu_part.strip()

                # ── DISPLAY RESULTS ──────────────────────────
                st.markdown("---")
                st.subheader("📊 Analysis Results")

                # Image Disease Cards
                st.markdown("#### 🔬 Visual Analysis (Model Predictions)")
                if high_conf_diseases:
                    for d in high_conf_diseases:
                        st.markdown(
                            f'<div class="disease-card">'
                            f'<span class="confidence-high">🔴 {d["label"]}</span> — '
                            f'<b>{d["confidence"]:.1f}%</b> confidence (above 75%)'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                else:
                    top_d = low_conf_top[0] if low_conf_top else {"label": "N/A", "confidence": 0}
                    st.markdown(
                        f'<div class="warning-box">'
                        f'⚠️ No disease detected above 75% threshold. '
                        f'Closest match: <b>{top_d["label"]}</b> '
                        f'({top_d["confidence"]:.1f}%) — further testing recommended.'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                # English Clinical Report
                st.markdown(
                    f"""
                    <div class="report-box">
                        <h3 style="color:#2d7a6a; margin-top:0;">
                            📋 English Clinical Report
                        </h3>
                        <div style="font-size:15px; color:#333; line-height:1.8;">
                            {eng_report.replace(chr(10), '<br>')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Urdu Voice Report (audio only — no text displayed)
                st.markdown(
                    """
                    <div class="voice-report-box">
                        <h3 style="color:#2d7a6a; margin-top:0;">
                            🔊 AI Voice Report (Urdu)
                        </h3>
                        <p style="color:#555; font-size:14px;">
                            Press play to hear the AI medical advice in Urdu
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                ai_audio_path = text_to_speech_urdu(urdu_mashwara)
                if ai_audio_path:
                    st.audio(ai_audio_path)
                else:
                    st.warning("Voice generation failed. Please try again.")

                # Disclaimer
                st.markdown(
                    '<div class="warning-box">'
                    '⚠️ <b>Disclaimer:</b> This is an AI-generated analysis only. '
                    'Please consult a qualified medical doctor for final diagnosis and treatment.'
                    '</div>',
                    unsafe_allow_html=True
                )

            except Exception as e:
                st.error(f"Analysis failed: {e}")

else:
    st.info(
        "👆 Please upload an image or take a photo first, "
        "then record your symptoms in the Sidebar, "
        "then click Run Full Analysis."
    )