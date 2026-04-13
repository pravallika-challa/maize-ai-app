import streamlit as st
import numpy as np
from PIL import Image
from googletrans import Translator
from tensorflow.keras.models import load_model
from tensorflow.keras.layers import Dense
from datetime import datetime
import gdown, os, json, tempfile
from gtts import gTTS

# -------------------------------
# CONFIG
# -------------------------------
DB_FILE = "users.json"
MODEL_PATH = "plant_disease_prediction_model.h5"

# -------------------------------
# DATABASE
# -------------------------------
def load_users():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

users = load_users()

# Default users
if not users:
    users = {
        "farmer1": {"name": "Farmer1", "password": "123", "city": "Hyderabad", "phone": "9876543210"},
        "admin1": {"name": "Admin1", "password": "admin123", "city": "HQ", "phone": "9999999999"}
    }
    save_users(users)

# -------------------------------
# MODEL
# -------------------------------
@st.cache_resource
def load_model_file():
    class FixedDense(Dense):
        def __init__(self, *args, **kwargs):
            kwargs.pop('quantization_config', None)
            super().__init__(*args, **kwargs)

    if not os.path.exists(MODEL_PATH):
        file_id = "YOUR_FILE_ID_HERE"
        url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(url, MODEL_PATH, quiet=False)

    return load_model(MODEL_PATH, compile=False, custom_objects={"Dense": FixedDense})

# -------------------------------
# VOICE (WORKS IN CLOUD)
# -------------------------------
def speak(text, lang="en"):
    try:
        tts = gTTS(text=text, lang=lang)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            st.audio(fp.name)
    except:
        st.warning("Voice not supported for this language")

# -------------------------------
# UI
# -------------------------------
st.set_page_config(page_title="🌽 Maize Care AI", layout="wide")

st.markdown("""
<style>
.stButton>button {
    background-color:#4CAF50;
    color:white;
    border-radius:10px;
}
</style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# -------------------------------
# LOGIN / REGISTER
# -------------------------------
if not st.session_state.logged_in:

    st.title("🌽 Smart Maize AI System")
    st.caption("AI-powered crop disease detection for farmers")

    tab1, tab2 = st.tabs(["Login", "Register"])

    # LOGIN
    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if username in users and users[username]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid credentials")

    # REGISTER
    with tab2:
        new_user = st.text_input("New Username")
        new_name = st.text_input("Full Name")
        new_pw = st.text_input("New Password", type="password")
        new_city = st.text_input("City")
        new_phone = st.text_input("Phone")

        if st.button("Register"):
            if new_user and new_pw:
                users[new_user] = {
                    "name": new_name,
                    "password": new_pw,
                    "city": new_city,
                    "phone": new_phone
                }
                save_users(users)
                st.success("Registered successfully!")
            else:
                st.error("Fill all fields")

# -------------------------------
# MAIN APP
# -------------------------------
else:
    username = st.session_state.username
    user = users[username]

    # Sidebar
    st.sidebar.title("👨‍🌾 Profile")
    st.sidebar.write(f"Name: {user['name']}")
    st.sidebar.write(f"City: {user['city']}")
    st.sidebar.write(f"Phone: {user['phone']}")

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # Language
    languages = {
        "English": "en",
        "Telugu": "te",
        "Hindi": "hi",
        "Tamil": "ta"
    }
    lang_name = st.sidebar.selectbox("🌐 Language", list(languages.keys()))
    lang_code = languages[lang_name]

    st.title("🌽 Maize Disease Detection")

    option = st.radio("Choose", ["Detection", "Notifications"], horizontal=True)

    model = load_model_file()
    translator = Translator()

    if "notifications" not in st.session_state:
        st.session_state.notifications = []

    # -------------------------------
    # DETECTION
    # -------------------------------
    if option == "Detection":

        col1, col2 = st.columns(2)

        with col1:
            file = st.file_uploader("Upload Leaf Image")

        with col2:
            if file:
                img = Image.open(file)
                st.image(img)

        if st.button("Predict"):
            if file:
                img = img.resize((224,224))
                arr = np.array(img)/255.0
                arr = np.expand_dims(arr,0)

                pred = model.predict(arr)
                classes = ["Healthy","Rust","Leaf Spot","Blight"]
                result = classes[np.argmax(pred)]

                text = f"Prediction: {result}"

                # 🌐 Translate
                translated = translator.translate(text, dest=lang_code).text

                st.success(translated)

                # 🔊 Voice output
                speak(translated, lang_code)

                # Save notification
                st.session_state.notifications.append(
                    f"{datetime.now().strftime('%H:%M')} - {username}: {result}"
                )

    # -------------------------------
    # NOTIFICATIONS
    # -------------------------------
    else:
        if username == "admin1":
            msg = st.text_input("Send notification")
            if st.button("Send"):
                st.session_state.notifications.append(msg)

        for n in reversed(st.session_state.notifications):
            st.info(n)
