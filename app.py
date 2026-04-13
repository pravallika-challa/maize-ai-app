import streamlit as st
import streamlit_authenticator as stauth
import numpy as np
from PIL import Image
from googletrans import Translator
from tensorflow.keras.models import load_model
from tensorflow.keras.layers import Dense
from datetime import datetime

# -------------------------------
# 1. Credentials Setup
# -------------------------------
if 'credentials' not in st.session_state:
    passwords = ["123", "admin123"]

    # ✅ NEW hashing method
    hashed_passwords = [stauth.Hasher().hash(pw) for pw in passwords]

    st.session_state['credentials'] = {
        "usernames": {
            "farmer1": {
                "name": "Farmer1",
                "password": hashed_passwords[0],
                "city": "Hyderabad",
                "phone": "9876543210",
                "roles": ["viewer"]
            },
            "admin1": {
                "name": "Admin1",
                "password": hashed_passwords[1],
                "city": "HQ",
                "phone": "9999999999",
                "roles": ["admin"]
            }
        }
    }

if 'notifications' not in st.session_state:
    st.session_state['notifications'] = []

# -------------------------------
# 2. Load Model
# -------------------------------
@st.cache_resource
def load_model_file():
    class FixedDense(Dense):
        def __init__(self, *args, **kwargs):
            kwargs.pop('quantization_config', None)
            super().__init__(*args, **kwargs)

    try:
        return load_model(
            "plant_disease_prediction_model.h5",
            compile=False,
            custom_objects={"Dense": FixedDense}
        )
    except:
        return None

# -------------------------------
# 3. UI Setup
# -------------------------------
st.set_page_config(page_title="🌽 Maize Care AI", layout="wide")

authenticator = stauth.Authenticate(
    st.session_state['credentials'],
    "maize_cookie",
    "secure_key",
    30
)

# -------------------------------
# 4. Login & Register
# -------------------------------
if not st.session_state.get("authentication_status"):

    st.title("🌽 Smart Maize AI Dashboard")

    tab1, tab2 = st.tabs(["Login", "Register"])

    # -------- LOGIN --------
    with tab1:
        authenticator.login(location="main")

        if st.session_state.get("authentication_status") is False:
            st.error("Invalid username or password")
        elif st.session_state.get("authentication_status") is None:
            st.warning("Enter login details")

    # -------- REGISTER --------
    with tab2:
        st.subheader("Register New Farmer")

        new_user = st.text_input("Username")
        new_name = st.text_input("Full Name")
        new_pw = st.text_input("Password", type="password")
        new_city = st.text_input("City")
        new_phone = st.text_input("Phone")

        if st.button("Register"):
            if new_user and new_pw:
                # ✅ hashing fixed
                hashed_pw = stauth.Hasher().hash(new_pw)

                st.session_state['credentials']['usernames'][new_user] = {
                    "name": new_name,
                    "password": hashed_pw,
                    "city": new_city,
                    "phone": new_phone,
                    "roles": ["viewer"]
                }

                st.success("Registration successful! Please login.")
            else:
                st.error("Username & Password required")

# -------------------------------
# 5. MAIN APP
# -------------------------------
if st.session_state.get("authentication_status"):

    authenticator.logout(location="sidebar")

    username = st.session_state.get("username")
    user_info = st.session_state['credentials']['usernames'].get(username, {})
    roles = user_info.get("roles", [])

    # Sidebar
    st.sidebar.title("👨‍🌾 Profile")
    st.sidebar.write(f"Name: {st.session_state.get('name')}")
    st.sidebar.write(f"City: {user_info.get('city')}")
    st.sidebar.write(f"Phone: {user_info.get('phone')}")

    # Language
    languages = {"English": "en", "Telugu": "te", "Hindi": "hi", "Tamil": "ta"}
    lang = st.sidebar.selectbox("Language", list(languages.keys()))
    lang_code = languages[lang]

    st.title("🌽 Maize Care Dashboard")

    option = st.radio(
        "Choose Service",
        ["Disease Detection", "Notifications"],
        horizontal=True
    )

    model = load_model_file()
    translator = Translator()

    # -------------------------------
    # Disease Detection
    # -------------------------------
    if option == "Disease Detection":
        st.subheader("📸 Upload Leaf Image")

        file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])

        if file:
            img = Image.open(file)
            st.image(img, use_container_width=True)

            if st.button("Predict"):
                if model:
                    img = img.resize((224, 224))
                    arr = np.array(img) / 255.0
                    arr = np.expand_dims(arr, axis=0)

                    pred = model.predict(arr)
                    classes = ["Healthy", "Rust", "Leaf Spot", "Blight"]
                    result = classes[np.argmax(pred)]

                    text = f"Prediction: {result}"
                    translated = translator.translate(text, dest=lang_code).text

                    st.success(translated)

                    # Save notification
                    now = datetime.now().strftime("%I:%M %p")
                    st.session_state['notifications'].append({
                        "time": now,
                        "msg": f"{username} detected {result}"
                    })
                else:
                    st.error("Model file missing")

    # -------------------------------
    # Notifications
    # -------------------------------
    elif option == "Notifications":
        st.subheader("📢 Notifications")

        if "admin" in roles:
            msg = st.text_area("Send notification")

            if st.button("Send"):
                if msg:
                    now = datetime.now().strftime("%I:%M %p")
                    st.session_state['notifications'].append({
                        "time": now,
                        "msg": msg
                    })
                    st.success("Notification sent")

        if st.session_state['notifications']:
            for n in reversed(st.session_state['notifications']):
                st.info(f"[{n['time']}] {n['msg']}")
        else:
            st.write("No notifications yet")
