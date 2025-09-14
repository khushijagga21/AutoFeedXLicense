import streamlit as st
import subprocess

# Set your password here
PASSWORD = "123"  # ← Change this to your real password

st.set_page_config(page_title="YouTube Viewer", layout="centered")
st.title("🔐 YouTube Viewer Login")

# Password input field
password_input = st.text_input("Enter password:", type="password")

if st.button("Start Viewer"):
    if password_input == PASSWORD:
        st.success("✅ Password correct! Starting viewer...")
        subprocess.Popen(["python", "main.py"])
    else:
        st.error("❌ Incorrect password. Please try again.")
