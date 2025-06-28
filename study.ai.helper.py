# Step 1: Initialize history session state
import streamlit as st
HISTORY_FILE = "history.json"

if "history" not in st.session_state:
    st.session_state.history = []

# Step 2: Importing libraries
import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import os

# Step 3: API Setup
genai.configure(api_key='AIzaSyBFdfJLDdIj2pZcx1z4_VBbfnBupSPawIE')
model = genai.GenerativeModel('gemini-2.0-flash')

# -----------------------------
# Sign In / Sign Up System (with file storage)
# -----------------------------
import json

USER_FILE = "users.json"

# Load existing users
def load_users():
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w") as f:
            json.dump({}, f)  # empty dict for users
        return {}

    with open(USER_FILE, "r") as f:
        try:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
        except json.JSONDecodeError:
            print("⚠️ users.json is corrupted or invalid. Resetting it.")
            with open(USER_FILE, "w") as f:
                json.dump({}, f)
            return {}

# Save users
def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

# Register a new user
def register_user(username, password):
    users = load_users()
    if username in users:
        return False
    users[username] = password
    save_users(users)
    return True

# Login check
def login_user(username, password):
    users = load_users()
    return users.get(username) == password

# Session state init
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Login or Register
if not st.session_state.logged_in:
    st.title("🔐 Welcome to study.ai.helper")

    tab1, tab2 = st.tabs(["🔓 Sign In", "📝 Sign Up"])

    # --- Sign In Tab ---
    with tab1:
        uname = st.text_input("Username", key="login_user")
        pwd = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if login_user(uname, pwd):
                st.session_state.logged_in = True
                st.session_state.user = uname
                st.success("✅ Login successful!")
                st.rerun()

            else:
                st.error("❌ Incorrect username or password.")

    # --- Sign Up Tab ---
    with tab2:
        new_uname = st.text_input("Choose a Username", key="signup_user")
        new_pwd = st.text_input("Choose a Password", type="password", key="signup_pass")
        if st.button("Register"):
            if register_user(new_uname, new_pwd):
                st.success("✅ Registered successfully! Please sign in.")
            else:
                st.error("⚠️ Username already exists.")

    st.stop()

# -----------------------------
# History System
# -----------------------------

# Load all history
def load_history():
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w") as f:
            json.dump({}, f)
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)

# Save all history
def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

# Add message to user's history
def add_to_history(user, role, message):
    history = load_history()
    if user not in history:
        history[user] = []
    history[user].append({"role": role, "message": message})
    save_history(history)

# Get user's history
def get_user_history(user):
    history = load_history()
    return history.get(user, [])


# -----------------------------------
# Sidebar Navigation After Login
# -----------------------------------
st.sidebar.title(f"👋 Welcome, {st.session_state.user}")
section = st.sidebar.selectbox("Choose Feature", [
    "🧠 Ask AI", 
    "📄 Upload PDF & Summarize", 
    "❓ Quiz Generator",
    "📜 History"
])

# -------------------------------
# 🧠 Ask AI Section
# -------------------------------
if section == "🧠 Ask AI":
    st.title('🤖 Studying AI Assistant 📚')
    subjects_options = ['🧬 Biology', '⚛️ Physics', '➗ Math', '🧪 Chemistry']
    detials_options = ['📝 Brief', '📖 Medium', '📚 Detailed']
    tone_options = ['😊 Friendly', '💼 Professional']
    edu_level_options = ['🏫 Elementary', '👨‍🎓 Junior', '🎓 Senior']

    # First row
    col1, col2 = st.columns(2)
    subject = col1.selectbox('📘 Choose a subject:', subjects_options)
    detials = col2.selectbox('🔍 Choose details level:', detials_options)

    # Second row
    col3, col4 = st.columns(2)
    tone = col3.selectbox('🎭 Choose a tone:', tone_options)
    edu_level = col4.selectbox('🏷️ Choose educational level:', edu_level_options)

    # Taking user question
    user_input = st.text_area('🧠 Enter your question:', height=150)

    # Get AI response on button click
    if st.button('💡 Get Answer'):
        prompt = f"""
        You are an AI studying assistant helping a {edu_level} level student with {subject}.
        Answer in a {tone} tone and provide a {detials} explanation.
        The question is:
        {user_input}
        """
        response = model.generate_content(prompt)
        answer = response.text

        st.markdown("### ✅ Answer:")
        st.write(answer)

        # Save to chat history
        add_to_history(st.session_state.user, "user", user_input)
        add_to_history(st.session_state.user, "ai", answer)



elif section == "📄 Upload PDF & Summarize":
    st.title("🧠 Text & PDF Summarizer")

    summarization_type = st.radio("Choose input method:", ["📜 Enter Text", "📄 Upload PDF"])

    # -------------------------------
    # 📜 Manual Text Input Summarizer
    # -------------------------------
    if summarization_type == "📜 Enter Text":
        input_text = st.text_area("✍️ Paste or type your text here:", height=300)

        if st.button("🧠 Summarize Text"):
            if input_text.strip() == "":
                st.warning("⚠️ Please enter some text to summarize.")
            else:
                with st.spinner("Summarizing your text..."):
                    prompt = f"Summarize this clearly for a student:\n\n{input_text}"
                    response = model.generate_content(prompt)
                    st.markdown("### 📝 Text Summary:")
                    st.write(response.text)

    # -------------------------------
    # 📄 PDF Upload Summarizer
    # -------------------------------
    elif summarization_type == "📄 Upload PDF":
        pdf_file = st.file_uploader("📄 Upload a PDF file", type=["pdf"])

        if pdf_file:
            reader = PdfReader(pdf_file)
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() or ""

            if not full_text.strip():
                st.error("❌ Could not extract any readable text from the PDF.")
            else:
                if st.button("📚 Summarize PDF"):
                    with st.spinner("Summarizing your PDF..."):
                        summary_prompt = f"Summarize this clearly for a student:\n\n{full_text}"
                        summary_response = model.generate_content(summary_prompt)
                        st.markdown("### 📑 PDF Summary:")
                        st.write(summary_response.text)


# -------------------------------
# ❓ Quiz Generator Section
# -------------------------------
elif section == "❓ Quiz Generator":
    st.title("❓ Generate Multiple-Choice Questions")
    quiz_topic = st.text_input("Enter a topic for quiz (e.g. Photosynthesis, Newton's Laws, etc.)")

    if st.button("🎯 Generate Quiz"):
        quiz_prompt = f"""
        Generate 5 multiple-choice questions (each with 4 choices, and one correct answer marked) about: {quiz_topic}.
        Format them clearly for students.
        """
        quiz_response = model.generate_content(quiz_prompt)
        st.markdown("### 🧪 Quiz:")
        st.write(quiz_response.text)


# -------------------------------
#  📜 History chat Section
# -------------------------------
elif section == "📜 History":
    st.title("📜 Your Chat History")

    user_history = get_user_history(st.session_state.user)

    if not user_history:
        st.info("No history found yet. Ask AI something first!")
    else:
        for i, item in enumerate(user_history):
            role_icon = "👤" if item["role"] == "user" else "🤖"
            st.markdown(f"**{role_icon} {item['role'].capitalize()}**: {item['message']}")
            st.markdown("---")

        if st.button("🗑️ Clear My History"):
            history = load_history()
            history[st.session_state.user] = []
            save_history(history)
            st.success("History cleared!")
            st.rerun()

