import streamlit as st
import json
import os
import time
import requests
import random
from datetime import datetime
from groq import Groq
from pypdf import PdfReader
# We keep streamlit_lottie because it makes the UI look "Modern"
from streamlit_lottie import st_lottie

# --- CONFIGURATION ---
st.set_page_config(page_title="Flash AI", layout="wide", page_icon="⚡")

API_KEY = "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" 
ADMIN_PASSWORD = "admin" 
RESULTS_FILE = 'interview_results.json'

if not API_KEY:
    st.error("⚠️ API Key is missing.")
    st.stop()

client = Groq(api_key=API_KEY)

# --- MODERN CSS (GLASSMORPHISM) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }
    
    /* BACKGROUND */
    .stApp {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
    }

    /* CARDS */
    div.stTabs, div.stForm, div.stContainer {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }

    /* INPUTS */
    .stTextInput > div > div > input, .stSelectbox > div > div > div {
        background-color: rgba(255, 255, 255, 0.15);
        color: white;
        border-radius: 10px;
        border: none;
    }

    /* BUTTONS */
    div.stButton > button {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
        color: white;
        border: none;
        padding: 10px 25px;
        border-radius: 25px;
        font-weight: bold;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 0 15px rgba(0, 210, 255, 0.5);
    }
    
    /* CHAT BUBBLES */
    .stChatMessage {
        background-color: rgba(0, 0, 0, 0.2);
        border-radius: 15px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except: return None

# Load Animations (Modern Look)
lottie_robot = load_lottieurl("https://lottie.host/5a8b7533-8515-4122-8700-1c3132d73315/o5gXyXy2gP.json")
lottie_loading = load_lottieurl("https://lottie.host/803855eb-3760-466d-92df-8f5379201f37/hYkH99H46F.json")

def generate_questions(role, exp):
    prompt = f"""Create 5 technical interview questions for a {role} ({exp} years). JSON array: [{{"question": "...", "expected_answer": "..."}}]"""
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant", # FAST MODEL
            messages=[{"role": "system", "content": prompt}],
            temperature=0.7
        )
        content = completion.choices[0].message.content
        start, end = content.find('['), content.rfind(']') + 1
        return json.loads(content[start:end])
    except:
        return [{"question": f"Explain {role} core concepts.", "expected_answer": "..."}] * 5

def extract_pdf(file):
    try:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages: text += page.extract_text()
        return text
    except: return ""

def save_result(data):
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r') as f:
            try: d = json.load(f)
            except: d = []
    else: d = []
    d.append(data)
    with open(RESULTS_FILE, 'w') as f: json.dump(d, f, indent=4)

def load_results():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r') as f: return json.load(f)
    return []

# --- STATE ---
if "page" not in st.session_state: st.session_state.page = "Login"
if "candidate_data" not in st.session_state: st.session_state.candidate_data = {}

# ==========================================
# 1. LOGIN PAGE (MODERN)
# ==========================================
if st.session_state.page == "Login":
    st.title("⚡ Flash AI")
    st.markdown("### Next-Gen Interview Practice")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if lottie_robot: st_lottie(lottie_robot, height=280)
    with col2:
        tab1, tab2 = st.tabs(["👤 Candidate", "🛡️ Admin"])
        with tab1:
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            if st.button("Start 🚀"):
                if name:
                    st.session_state.candidate_data = {"name": name, "email": email}
                    st.session_state.page = "Profile"
                    st.rerun()
        with tab2:
            pwd = st.text_input("Password", type="password")
            if st.button("Login"):
                if pwd == ADMIN_PASSWORD:
                    st.session_state.page = "Dashboard"
                    st.rerun()

# ==========================================
# 2. PROFILE (MODERN)
# ==========================================
elif st.session_state.page == "Profile":
    st.title("📄 Setup Profile")
    
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            role = st.selectbox("Target Role", ["Python Developer", "Data Scientist", "React Dev", "Manager"])
            phone = st.text_input("Phone")
            exp = st.slider("Years Experience", 0, 20, 1)
        with col2:
            notice = st.selectbox("Notice Period", ["Immediate", "30 Days"])
            resume = st.file_uploader("Resume (PDF)", type=["pdf"])

        st.divider()
        if st.button("⚡ Generate Questions"):
            if phone:
                text = extract_pdf(resume) if resume else ""
                st.session_state.candidate_data.update({"role": role, "phone": phone, "resume": text})
                
                with st.spinner("🤖 AI is crafting your interview..."):
                    st.session_state.questions = generate_questions(role, exp)
                
                st.session_state.current_q = 0
                st.session_state.chat = []
                st.session_state.scores = []
                st.session_state.page = "Interview"
                st.rerun()
            else:
                st.warning("Phone number is required.")

# ==========================================
# 3. INTERVIEW (MODERN CHAT)
# ==========================================
elif st.session_state.page == "Interview":
    
    q_idx = st.session_state.current_q
    questions = st.session_state.questions

    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.candidate_data['name']}")
        st.caption(st.session_state.candidate_data['role'])
        st.progress((q_idx) / len(questions))
        if lottie_robot: st_lottie(lottie_robot, height=100)

    st.subheader("🔥 Live Interview")

    # Initialize Chat
    if not st.session_state.chat:
        st.session_state.chat.append({"role": "assistant", "content": questions[0]['question']})

    # Render Chat
    for msg in st.session_state.chat:
        with st.chat_message(msg["role"], avatar="👤" if msg['role']=='user' else "🤖"):
            st.write(msg["content"])

    # Input Area
    if q_idx < len(questions):
        if user_ans := st.chat_input("Type your answer here..."):
            st.session_state.chat.append({"role": "user", "content": user_ans})
            with st.chat_message("user", avatar="👤"):
                st.write(user_ans)

            # AI Thinking Animation
            with st.chat_message("assistant", avatar="🤖"):
                placeholder = st.empty()
                with placeholder:
                    if lottie_loading: st_lottie(lottie_loading, height=60)
                    else: st.write("Analyzing...")
                
                # Scoring
                curr_q = questions[q_idx]
                try:
                    prompt = f"Rate 1-10 for Q: {curr_q['question']} A: {user_ans}. Output number only."
                    feedback = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": prompt}]
                    ).choices[0].message.content
                    score = int(''.join(filter(str.isdigit, feedback)))
                except: score = 5
                st.session_state.scores.append(score)

                # Next Question
                st.session_state.current_q += 1
                placeholder.empty() # Remove animation

                if st.session_state.current_q < len(questions):
                    next_q = questions[st.session_state.current_q]['question']
                    st.session_state.chat.append({"role": "assistant", "content": next_q})
                    st.rerun()
                else:
                    st.session_state.page = "Result"
                    st.rerun()

# ==========================================
# 4. RESULTS
# ==========================================
elif st.session_state.page == "Result":
    st.balloons()
    st.title("🎉 Interview Complete")
    
    score = sum(st.session_state.scores)
    total = len(st.session_state.questions) * 10
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Final Score", f"{score}/{total}")
    with col2:
        st.info("Your results have been sent to HR.")

    if st.button("Submit & Logout"):
        save_result({
            "name": st.session_state.candidate_data['name'],
            "role": st.session_state.candidate_data['role'],
            "score": score,
            "max_score": total,
            "resume_text": st.session_state.candidate_data.get('resume', '')
        })
        st.session_state.clear()
        st.session_state.page = "Login"
        st.rerun()

# ==========================================
# 5. DASHBOARD
# ==========================================
elif st.session_state.page == "Dashboard":
    st.title("📊 HR Dashboard")
    if st.sidebar.button("Logout"):
        st.session_state.page = "Login"
        st.rerun()

    results = load_results()
    if results:
        st.dataframe(results)
        
        selected = st.selectbox("Select Candidate", [r['name'] for r in results])
        if selected:
            data = next(r for r in results if r['name'] == selected)
            st.text_area("Resume", data.get('resume_text', 'No resume'), height=200)
    else:
        st.info("No data found.")
