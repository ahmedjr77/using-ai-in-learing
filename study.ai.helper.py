# Step 1: Initialize history session state
import streamlit as st
HISTORY_FILE = "history.json"

if "history" not in st.session_state:
    st.session_state.history = []

# Step 2: Importing libraries
import google.generativeai as genai
from PyPDF2 import PdfReader
import os
import json

# Step 3: API Setup
genai.configure(api_key='AIzaSyBFdfJLDdIj2pZcx1z4_VBbfnBupSPawIE')
model = genai.GenerativeModel('gemini-2.0-flash')

USER_FILE = "users.json"

# -----------------------------
# USERS SYSTEM
# -----------------------------

# Load existing users
def load_users():
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w") as f:
            json.dump({}, f)
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

# Register new user with structure
def register_user(username, password):
    users = load_users()
    if username in users:
        return False
    users[username] = {
        "password": password,
        "subjects": []
    }
    save_users(users)
    return True

# Upgrade old users to new structure
def upgrade_old_users():
    users = load_users()
    updated = False
    for uname in users:
        if isinstance(users[uname], str):
            old_password = users[uname]
            users[uname] = {
                "password": old_password,
                "subjects": []
            }
            updated = True
    if updated:
        save_users(users)

# Run upgrade on startup
upgrade_old_users()

# Login check supports old & new structure
def login_user(username, password):
    users = load_users()
    user = users.get(username)
    if not user:
        return False
    if isinstance(user, dict):
        return user["password"] == password
    return user == password

# Get subjects for a user
def get_user_subjects(username):
    users = load_users()
    return users[username].get("subjects", [])

# Add subject to user
def add_user_subject(username, new_subject):
    users = load_users()
    if new_subject not in users[username]["subjects"]:
        users[username]["subjects"].append(new_subject)
        save_users(users)

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

# Add message to history
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

# -----------------------------
# Auth Flow
# -----------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Welcome to study.ai.helper")

    tab1, tab2 = st.tabs(["🔓 Sign In", "📝 Sign Up"])

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
# Sidebar Navigation
# -----------------------------

st.sidebar.title(f"👋 Welcome, {st.session_state.user}")
section = st.sidebar.selectbox("Choose Feature", [
    "🧠 Ask AI",
    "📄 Upload PDF & Summarize",
    "❓ Quiz Generator",
    "📜 History"
])

# -----------------------------
# 🧠 Ask AI
# -----------------------------

if section == "🧠 Ask AI":
    st.title('🤖 Studying AI Assistant 📚')

    default_subjects = ['🧬 Biology', '⚛️ Physics', '➗ Math', '🧪 Chemistry']
    user_subjects = get_user_subjects(st.session_state.user)
    subjects_options = default_subjects + user_subjects

    new_subject = st.text_input("➕ Add a new subject:")
    if st.button("Add Subject"):
        if new_subject.strip() != "":
            add_user_subject(st.session_state.user, new_subject.strip())
            st.success(f"✅ Added '{new_subject}' to your subjects.")
            st.rerun()

    detials_options = ['📝 Brief', '📖 Medium', '📚 Detailed']
    tone_options = ['😊 Friendly', '💼 Professional']
    edu_level_options = ['🏫 Elementary', '👨‍🎓 Junior', '🎓 Senior']

    col1, col2 = st.columns(2)
    subject = col1.selectbox('📘 Choose a subject:', subjects_options)
    detials = col2.selectbox('🔍 Choose details level:', detials_options)

    col3, col4 = st.columns(2)
    tone = col3.selectbox('🎭 Choose a tone:', tone_options)
    edu_level = col4.selectbox('🏷️ Choose educational level:', edu_level_options)

    user_input = st.text_area('🧠 Enter your question:', height=150)

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

        add_to_history(st.session_state.user, "user", user_input)
        add_to_history(st.session_state.user, "ai", answer)

# -----------------------------
# 📄 PDF Summarizer
# -----------------------------

elif section == "📄 Upload PDF & Summarize":
    st.title("🧠 Text & PDF Summarizer")

    summarization_type = st.radio("Choose input method:", ["📜 Enter Text", "📄 Upload PDF"])

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



# -----------------------------
# ❓ Quiz Generator (MCQ + Essay)
# -----------------------------

elif section == "❓ Quiz Generator":
    st.title("❓ Generate Quiz")

    quiz_topic = st.text_input("Enter a topic for the quiz (e.g. Photosynthesis, Climate Change)")

    num_questions = st.number_input(
        "How many questions?",
        min_value=1,
        max_value=20,
        value=5,
        step=1
    )

    difficulty = st.selectbox(
        "Select difficulty level:",
        ["Easy", "Medium", "Hard"]
    )

    question_type = st.selectbox(
        "Select question type:",
        ["Multiple Choice", "Essay Questions"]
    )

    if "quiz_data" not in st.session_state:
        st.session_state.quiz_data = None
    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}

    if st.button("🎯 Generate Quiz"):
        if question_type == "Multiple Choice":
            quiz_prompt = f"""
            You are an educational quiz generator.
            Create {num_questions} multiple-choice questions about "{quiz_topic}".
            Each question must have 4 answer options (A, B, C, D).
            One correct answer must be clearly marked at the end as: Answer: X (where X is A/B/C/D).
            Format:
            1) Question text
            A) Option A
            B) Option B
            C) Option C
            D) Option D
            Answer: X
            Difficulty: {difficulty} level.
            """
        else:
            quiz_prompt = f"""
            You are an educational quiz generator.
            Create {num_questions} open-ended essay questions about "{quiz_topic}".
            Each question should match a {difficulty} level.
            Format:
            1) Question text
            """

        quiz_response = model.generate_content(quiz_prompt)
        quiz_text = quiz_response.text

        if question_type == "Multiple Choice":
            questions = []
            blocks = quiz_text.strip().split('\n\n')
            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) >= 6:
                    question_text = lines[0][3:].strip()
                    options = {
                        'A': lines[1][3:].strip(),
                        'B': lines[2][3:].strip(),
                        'C': lines[3][3:].strip(),
                        'D': lines[4][3:].strip(),
                    }
                    correct_line = [l for l in lines if l.startswith("Answer:")]
                    correct_answer = correct_line[0].split("Answer:")[1].strip() if correct_line else ""
                    questions.append({
                        'question': question_text,
                        'options': options,
                        'answer': correct_answer
                    })
            st.session_state.quiz_data = questions

        else:
            questions = []
            lines = quiz_text.strip().split('\n')
            for line in lines:
                if line.strip() and line[0].isdigit() and ')' in line:
                    q_text = line.split(')', 1)[1].strip()
                    questions.append({'question': q_text})
            st.session_state.quiz_data = questions

        st.session_state.quiz_answers = {}

    if st.session_state.quiz_data:
        st.subheader("📋 Take the Quiz")

        if question_type == "Multiple Choice":
            for idx, q in enumerate(st.session_state.quiz_data):
                st.markdown(f"**Q{idx+1}: {q['question']}**")
                selected = st.radio(
                    f"Your Answer for Q{idx+1}:",
                    list(q['options'].keys()),
                    format_func=lambda x: f"{x}) {q['options'][x]}",
                    key=f"q_{idx}"
                )
                st.session_state.quiz_answers[idx] = selected

            if st.button("✅ Submit Quiz"):
                score = 0
                total = len(st.session_state.quiz_data)
                results = []
                for idx, q in enumerate(st.session_state.quiz_data):
                    user_ans = st.session_state.quiz_answers.get(idx, None)
                    correct_ans = q['answer']
                    if user_ans == correct_ans:
                        score += 1
                    result_line = f"Q{idx+1}: ✅ Correct!" if user_ans == correct_ans else f"Q{idx+1}: ❌ Incorrect (Your: {user_ans}, Correct: {correct_ans})"
                    results.append(result_line)

                st.success(f"Your score: {score} / {total}")
                st.markdown("### 🗒️ Detailed Results")
                for res in results:
                    st.write(res)

                # SAVE TO HISTORY
                add_to_history(
                    st.session_state.user,
                    "quiz",
                    {
                        "topic": quiz_topic,
                        "type": "MCQ",
                        "score": f"{score}/{total}",
                        "results": results
                    }
                )

                # Reset
                st.session_state.quiz_data = None
                st.session_state.quiz_answers = {}

        else:
            for idx, q in enumerate(st.session_state.quiz_data):
                st.markdown(f"**Q{idx+1}: {q['question']}**")
                essay_ans = st.text_area(f"Your Answer for Q{idx+1}:", key=f"essay_{idx}")
                st.session_state.quiz_answers[idx] = essay_ans

            if st.button("✅ Submit Essay Quiz"):
                results = []
                for idx, q in enumerate(st.session_state.quiz_data):
                    user_ans = st.session_state.quiz_answers.get(idx, "")
                    results.append(f"Q{idx+1}: {q['question']}\nYour Answer: {user_ans}\n")

                st.success("✅ Your essay answers have been saved to your history.")
                st.markdown("### 🗒️ Your Answers")
                for res in results:
                    st.write(res)

                # SAVE TO HISTORY
                add_to_history(
                    st.session_state.user,
                    "quiz",
                    {
                        "topic": quiz_topic,
                        "type": "Essay",
                        "results": results
                    }
                )

                # Reset
                st.session_state.quiz_data = None
                st.session_state.quiz_answers = {}



# -----------------------------
# 📜 History
# -----------------------------

elif section == "📜 History":
    st.title("📜 Your Chat & Quiz History")

    user_history = get_user_history(st.session_state.user)

    if not user_history:
        st.info("No history found yet. Ask AI something or take a quiz first!")
    else:
        for i, item in enumerate(user_history):
            role = item["role"]
            message = item["message"]

            if role == "quiz":
                st.markdown(f"### 📝 Quiz")
                st.markdown(f"**Topic:** {message.get('topic', 'Unknown')}")
                st.markdown(f"**Score:** {message.get('score', 'N/A')}")

                for idx, q in enumerate(message.get("questions", [])):
                    st.markdown(f"**Q{idx+1}: {q['question']}**")
                    if "options" in q:
                        # It's MCQ
                        for option_key, option_value in q["options"].items():
                            st.markdown(f"- {option_key}) {option_value}")
                        st.markdown(f"**✅ Correct Answer:** {q['correct_answer']}")
                        st.markdown(f"**📝 Your Answer:** {q['user_answer']}")
                    else:
                        # It's Essay
                        st.markdown(f"**📝 Your Answer:** {q['user_answer']}")
                        st.markdown(f"**✅ Suggested Answer:** {q['correct_answer']}")

                    st.markdown("---")

            else:
                # Normal AI chat history
                role_icon = "👤" if role == "user" else "🤖"
                st.markdown(f"**{role_icon} {role.capitalize()}**: {message}")
                st.markdown("---")

        if st.button("🗑️ Clear My History"):
            history = load_history()
            history[st.session_state.user] = []
            save_history(history)
            st.success("History cleared!")
            st.rerun()

