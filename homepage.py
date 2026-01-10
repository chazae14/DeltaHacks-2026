import streamlit as st
import requests
import base64

def get_base64_image(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

bg_image = get_base64_image("background.png")

st.set_page_config(
    page_title="WatchMyStuff",
    layout="centered"
)

BACKEND_URL = "http://localhost:5000/start-monitoring"

if "page" not in st.session_state:
    st.session_state.page = "home"

st.markdown(f"""
<style>
.stApp {{
    background-image: url("data:image/png;base64,{bg_image}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}}

div.stButton > button {{
    background-color: #2ECC71;
    color: white;
    height: 100px;
    font-size: 36px;
    font-weight: bold;
    border-radius: 12px;
    border: none;
}}

div.stButton > button:hover {{
    background-color: #27AE60;
}}

header {{visibility: hidden;}}
footer {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

if st.session_state.page == "home":

    st.write("")
    st.write("")

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.image("logo.png", width=340)

    st.markdown(
        "<p style='text-align: center; font-size:18px; color:#666;'>"
        "Keep your belongings safe while studying."
        "</p>",
        unsafe_allow_html=True
    )

    st.write("")
    st.write("")

    email = st.text_input("Email for noticification", placeholder="user@example.com")

    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:

        if st.button("WatchMyStuff", use_container_width=True):

            if not email:
                st.error("Please enter an email to receive alerts.")
            elif "@" not in email or "." not in email:
                st.error("Please enter a valid email address.")
            else:
                try:
                    response = requests.post(
                        BACKEND_URL,
                        json={"email": email},
                        timeout=3
                    )

                    if response.status_code == 200:
                        st.session_state.user_email = email
                        st.session_state.page = "monitoring"
                        st.rerun()
                    else:
                        st.error("Backend responded but failed.")

                except Exception:
                    st.warning("Backend not connected yet.")

elif st.session_state.page == "monitoring":

    st.markdown(
        "<h1 style='text-align: center;'>🔒 Monitoring Active</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p style='text-align: center; font-size:18px;'>"
        "This laptop is being monitored."
        "</p>",
        unsafe_allow_html=True
    )

    st.markdown(f"<p style='text-align:center;'> Alerts will be sent to <b>{st.session_state.user_email}</b></p>",
        unsafe_allow_html=True
    )
