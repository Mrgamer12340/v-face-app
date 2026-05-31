# 🧠 V-Face App — AI Health Prediction System

> An end-to-end AI system that analyzes **facial expressions** and **voice patterns** to predict health conditions including skin diseases, dehydration, and fatigue.

---

## 🚀 Features

- 🎥 **Real-time face analysis** using CNN (TensorFlow/Keras)
- 🎤 **Voice-to-text** transcription via OpenAI Whisper v3 (Urdu & English)
- 🤖 **AI Medical Agent** powered by Groq's Llama 3.3 via LangChain
- 📋 **Dual-language reports** (Urdu + English) with Edge-TTS audio output
- 🌐 **Streamlit web app** with live camera integration

---

## 🛠️ Tech Stack

| Category       | Technologies                                      |
|----------------|---------------------------------------------------|
| AI / ML        | TensorFlow, Keras, CNN, LangChain, Groq (Llama 3.3) |
| Speech         | OpenAI Whisper v3 (STT), Edge-TTS                |
| Image Processing | CLAHE, OpenCV                                  |
| Frontend       | Streamlit, HTML, CSS, JavaScript                 |
| Backend        | Python, PHP                                      |
| Database       | MySQL                                            |

---

## 📁 Project Structure

```
v-face-app/
├── V-FACE-DEPLOY/     # Main application files
├── index.html         # Web interface
├── index.css          # Styling
└── index.js           # Frontend logic
```

---

## ⚙️ Installation & Setup

```bash
# 1. Clone the repository
git clone https://github.com/Mrgamer12340/v-face-app.git
cd v-face-app

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up API keys (.env file)
GROQ_API_KEY=your_groq_api_key_here

# 4. Run the app
streamlit run app.py
```

---

## 🔍 How It Works

1. **Camera captures** user's face in real-time
2. **CNN model** detects skin conditions using CLAHE-enhanced images
3. **Whisper STT** transcribes user's voice symptoms (Urdu/English)
4. **Llama 3.3 AI agent** cross-references visual + voice data
5. **Report generated** in both languages with audio output

---

## 👨‍💻 Developer

**Muhammad Yameen**
- 📧 yaminnaseem843@gmail.com
- 🔗 [GitHub](https://github.com/Mrgamer12340)

---

## 📄 License

This project is for academic purposes.
