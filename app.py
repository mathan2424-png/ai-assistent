import streamlit as st
import json
import os
import time
import requests
import random
from datetime import datetime
from groq import Groq
from pypdf import PdfReader
from streamlit_lottie import st_lottie

# --- CONFIGURATION ---
st.set_page_config(page_title="Flash AI Interviewer", layout="wide", page_icon="⚡")

API_KEY = "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" # Replace if needed
ADMIN_PASSWORD = "admin" 
RESULTS_FILE = 'interview_results.json'

if not API_KEY:
    st.error("⚠️ API Key is missing.")
    st.stop()

# Initialize Groq Client
client = Groq(api_key=API_KEY)

# --- MODERN UI & CSS ---
st.markdown("""
<style>
    /* IMPORT FONT */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');

    /* GLOBAL THEME */
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }
    
    /* BACKGROUND */
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        color: white;
    }

    /* CARDS (Glassmorphism) */
    div.stTabs, div.stForm {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* INPUT FIELDS */
    .stTextInput > div > div > input, .stSelectbox > div > div > div, .stNumberInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.1);
        color: white;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .stTextInput > div > div > input:focus {
        border-color: #00d2ff;
        box-shadow: 0 0 10px rgba(0, 210, 255, 0.5);
    }

    /* BUTTONS */
    div.stButton > button {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
        color: white;
        border: none;
        padding: 12px 28px;
        font-size: 16px;
        font-weight: 600;
        border-radius: 30px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 210, 255, 0.3);
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 210, 255, 0.5);
    }
    div.stButton > button:active {
        transform: translateY(1px);
    }

    /* CHAT BUBBLES */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* HEADERS */
    h1, h2, h3 {
        color: #00d2ff !important;
        text-shadow: 0 0 10px rgba(0, 210, 255, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except: return None

# Load Animations
lottie_robot = load_lottieurl("https://lottie.host/5a8b7533-8515-4122-8700-1c3132d73315/o5gXyXy2gP.json")
lottie_processing = load_lottieurl("https://lottie.host/803855eb-3760-466d-92df-8f5379201f37/hYkH99H46F.json")

def generate_questions_from_ai(role, exp):
    """Generates 5 questions using FAST model."""
    prompt = f"""
    Create 5 short technical interview questions for a {role} ({exp} years exp).
    Output JSON array ONLY:
    [{{"question": "...", "expected_answer": "..."}}]
    """
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant", # UPDATED FAST MODEL
            messages=[{"role": "system", "content": prompt}],
            temperature=0.7
        )
        content = completion.choices[0].message.content
        start, end = content.find('['), content.rfind(']') + 1
        return json.loads(content[start:end])
    except:
        return [
            {"question": f"Explain a core concept in {role}.", "expected_answer": "Core concept"},
            {"question": "How do you handle errors?", "expected_answer": "Error handling"},
            {"question": "Describe a difficult bug you fixed.", "expected_answer": "Problem solving"}
        ]

def extract_text_from_pdf(uploaded_file):
    try:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages: text += page.extract_text()
        return text
    except: return "Error reading PDF"

def save_result(data_packet):
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r') as f:
            try: data = json.load(f)
            except: data = []
    else: data = []
    data.append(data_packet)
    with open(RESULTS_FILE, 'w') as f: json.dump(data, f, indent=4)

def load_results():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r') as f: return json.load(f)
    return []

def format_time(seconds):
    return f"{int(seconds)}s"

# --- SESSION STATE ---
if "page" not in st.session_state: st.session_state.page = "Login"
if "candidate_data" not in st.session_state: st.session_state.candidate_data = {}

# ==========================================
# 1. LOGIN PAGE
# ==========================================
if st.session_state.page == "Login":
    st.title("⚡ Flash AI Interviewer")
    st.markdown("### The fastest way to practice technical interviews.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if lottie_robot: st_lottie(lottie_robot, height=300, key="robot_login")
    
    with col2:
        st.write("") # Spacer
        st.write("") 
        tab1, tab2 = st.tabs(["👤 Candidate", "🛡️ Admin"])
        
        with tab1:
            st.subheader("Candidate Login")
            c_name = st.text_input("Full Name", placeholder="John Doe")
            c_email = st.text_input("Email Address", placeholder="john@example.com")
            st.write("")
            if st.button("Start Interview 🚀"):
                if c_name and c_email:
                    st.session_state.candidate_data = {
                        "name": c_name, "email": c_email,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.page = "Profile_Setup"
                    st.rerun()
                else: st.warning("Please enter your name and email.")

        with tab2:
            st.subheader("Admin Portal")
            password = st.text_input("Admin Password", type="password")
            st.write("")
            if st.button("Access Dashboard 🔓"):
                if password == ADMIN_PASSWORD:
                    st.session_state.page = "Dashboard"
                    st.rerun()
                else:
                    st.error("Incorrect Password")

# ==========================================
# 2. PROFILE SETUP
# ==========================================
elif st.session_state.page == "Profile_Setup":
    st.title("📄 Profile Setup")
    st.markdown("Tell us about your target role.")
    
    with st.form("hr_form"):
        col1, col2 = st.columns(2)
        with col1:
            role = st.selectbox("Target Role", ["Python Developer", "Data Scientist", "Java Developer", "React Dev", "DevOps Engineer"])
            phone = st.text_input("Phone Number")
            exp = st.number_input("Years of Experience", 0, 30, 0)
        with col2:
            notice = st.selectbox("Notice Period", ["Immediate", "15 Days", "30 Days", "60 Days"])
            resume_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
        
        st.write("---")
        submitted = st.form_submit_button("⚡ Generate Interview Questions")
        
        if submitted:
            if phone:
                resume_text = extract_text_from_pdf(resume_file) if resume_file else "No Resume"
                st.session_state.candidate_data.update({
                    "role": role, "phone": phone, "experience": exp, 
                    "notice_period": notice, "resume_text": resume_text
                })
                
                with st.spinner("🤖 AI is reading your profile and generating questions..."):
                    st.session_state.interview_questions = generate_questions_from_ai(role, exp)
                
                st.session_state.page = "Interview"
                st.rerun()
            else: st.error("Phone number is required.")

# ==========================================
# 3. FAST INTERVIEW
# ==========================================
elif st.session_state.page == "Interview":
    
    if "current_q" not in st.session_state:
        st.session_state.current_q = 0
        st.session_state.chat_history = []
        st.session_state.admin_log = []
        st.session_state.scores = []
        st.session_state.interview_complete = False
        st.session_state.submitted = False
        st.session_state.start_time = None

    questions = st.session_state.interview_questions
    
    # Sidebar Info
    with st.sidebar:
        st.title("📋 Status")
        if lottie_robot: st_lottie(lottie_robot, height=120, key="robot_side")
        st.markdown(f"**Candidate:** {st.session_state.candidate_data['name']}")
        st.markdown(f"**Role:** {st.session_state.candidate_data['role']}")
        st.divider()
        if len(questions) > 0:
            progress = st.session_state.current_q / len(questions)
            st.progress(progress)
            st.caption(f"Question {st.session_state.current_q + 1} of {len(questions)}")

    # First Question Init
    if len(st.session_state.chat_history) == 0 and len(questions) > 0:
        first_q = questions[0]['question']
        st.session_state.chat_history.append({"role": "assistant", "content": f"**Question 1:** {first_q}"})
        st.session_state.start_time = time.time()

    st.title("🔥 Live Interview Session")

    # Chat UI
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"], avatar="👤" if msg["role"]=="user" else "🤖"):
                st.markdown(msg["content"])

    if not st.session_state.interview_complete:
        if st.session_state.start_time is None: st.session_state.start_time = time.time()
        
        user_ans = st.chat_input("Type your answer here...")
        
        if user_ans:
            # 1. Show user answer
            st.session_state.chat_history.append({"role": "user", "content": user_ans})
            with st.chat_message("user", avatar="👤"):
                st.markdown(user_ans)
            
            # 2. Show AI Thinking
            with st.chat_message("assistant", avatar="🤖"):
                placeholder = st.empty()
                with placeholder:
                    if lottie_processing:
                        st_lottie(lottie_processing, height=60, key="thinking")
                    else:
                        st.write("🔄 Analyzing answer...")

                # 3. Process Logic
                end_time = time.time()
                time_str = format_time(end_time - st.session_state.start_time)
                
                curr_data = questions[st.session_state.current_q]
                prompt = f"Q: {curr_data['question']} A: {user_ans}. Rate 1-10 (Start with 'Score: X/10')."
                
                try:
                    completion = client.chat.completions.create(
                        model="llama-3.1-8b-instant", 
                        messages=[{"role": "system", "content": prompt}]
                    )
                    feedback = completion.choices[0].message.content
                    score = int(''.join(filter(str.isdigit, feedback.split("/10")[0]))) if "Score:" in feedback else 0
                    
                    st.session_state.scores.append(score)
                    st.session_state.admin_log.append(f"**Q:** {curr_data['question']}\n**A:** {user_ans}\n**⏱️ {time_str}** | **Rating:** {feedback}\n---")

                    st.session_state.current_q += 1
                    st.session_state.start_time = time.time()

                    # 4. Clear loading and Move to next
                    placeholder.empty()

                    if st.session_state.current_q < len(questions):
                        next_q = questions[st.session_state.current_q]['question']
                        st.session_state.chat_history.append({"role": "assistant", "content": f"**Question {st.session_state.current_q+1}:** {next_q}"})
                        st.rerun()
                    else:
                        st.session_state.interview_complete = True
                        st.rerun()
                
                except Exception as e:
                    st.error(f"Error: {e}")

    elif st.session_state.interview_complete and not st.session_state.submitted:
        st.divider()
        st.success("🎉 Interview Completed!")
        col1, col2 = st.columns([2, 1])
        with col2:
            if st.button("💾 Submit Results to HR"):
                final_packet = st.session_state.candidate_data
                final_packet["interview_score"] = sum(st.session_state.scores)
                final_packet["max_score"] = len(questions)*10
                final_packet["interview_details"] = st.session_state.admin_log
                save_result(final_packet)
                st.session_state.submitted = True
                st.balloons()
                st.rerun()

    elif st.session_state.submitted:
        st.balloons()
        st.title("✅ Results Submitted")
        st.markdown("Thank you for your time. The HR team has received your responses.")
        if st.button("⬅️ Return to Home"):
            st.session_state.clear()
            st.session_state.page = "Login"
            st.rerun()

# ==========================================
# 4. ADMIN DASHBOARD
# ==========================================
elif st.session_state.page == "Dashboard":
    st.title("📊 HR Dashboard")
    st.markdown("Review candidate performance and AI insights.")
    
    if st.sidebar.button("🔒 Logout"):
        st.session_state.page = "Login"
        st.rerun()
    
    results = load_results()
    if results:
        # Modern Card for Stats
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Candidates", len(results))
        col2.metric("Avg Score", f"{int(sum([r['interview_score'] for r in results])/len(results)) if results else 0}")
        col3.metric("Pending Reviews", "0") # Placeholder

        st.divider()
        st.markdown("### 🧑‍💻 Candidate List")
        
        # Display as a clean table
        st.table([{"Name": r['name'], "Role": r['role'], "Score": f"{r['interview_score']}/{r['max_score']}"} for r in results])
        
        st.markdown("### 🔎 Deep Dive")
        selected = st.selectbox("Select a Candidate to View Details", [r['name'] for r in results])
        if selected:
            data = next((i for i in results if i["name"] == selected), None)
            if data:
                with st.container():
                    t1, t2 = st.tabs(["📝 Interview Transcript", "📋 Resume Text"])
                    with t1:
                        for line in data['interview_details']: 
                            st.info(line)
                    with t2: 
                        st.text_area("Resume Content", data.get('resume_text'), height=300)
    else:
        st.info("No interviews conducted yet.")
