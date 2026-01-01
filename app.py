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

# --- CSS STYLING ---
st.markdown("""
<style>
    div.stButton > button {
        background: linear-gradient(to bottom, #FF4B4B 5%, #cc0000 100%);
        background-color: #FF4B4B;
        border-radius: 8px;
        color: white;
        font-weight: bold;
        padding: 10px 24px;
        box-shadow: 0px 4px 0px 0px #8b0000;
        transition: all 0.1s;
    }
    div.stButton > button:active {
        transform: translateY(4px);
        box-shadow: 0px 0px 0px 0px #8b0000;
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
            model="llama3-8b-8192", # SPEED MODEL
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
    st.title("⚡ Speed AI Interviewer")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if lottie_robot: st_lottie(lottie_robot, height=250, key="robot_login")
    
    with col2:
        tab1, tab2 = st.tabs(["👤 Candidate", "🛡️ Admin"])
        
        with tab1:
            st.subheader("Candidate Login")
            c_name = st.text_input("Name")
            c_email = st.text_input("Email")
            if st.button("Start Now"):
                if c_name and c_email:
                    st.session_state.candidate_data = {
                        "name": c_name, "email": c_email,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.page = "Profile_Setup"
                    st.rerun()
                else: st.warning("Enter details.")

        with tab2:
            st.subheader("Admin Login")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                if password == ADMIN_PASSWORD:
                    st.session_state.page = "Dashboard"
                    st.rerun()

# ==========================================
# 2. PROFILE SETUP
# ==========================================
elif st.session_state.page == "Profile_Setup":
    st.title("📄 Setup Profile")
    with st.form("hr_form"):
        col1, col2 = st.columns(2)
        with col1:
            role = st.selectbox("Role", ["Python Developer", "Data Scientist", "Java Developer", "React Dev"])
            phone = st.text_input("Phone (Required)")
            exp = st.number_input("Experience (Years)", 0, 30, 0)
        with col2:
            notice = st.selectbox("Notice Period", ["Immediate", "15 Days", "30 Days"])
            resume_file = st.file_uploader("Resume (Optional)", type=["pdf"])
        
        if st.form_submit_button("🚀 Generate Interview"):
            if phone:
                resume_text = extract_text_from_pdf(resume_file) if resume_file else "No Resume"
                st.session_state.candidate_data.update({
                    "role": role, "phone": phone, "experience": exp, 
                    "notice_period": notice, "resume_text": resume_text
                })
                
                # Show loading spinner instead of code
                with st.spinner("⚡ AI is generating your interview..."):
                    st.session_state.interview_questions = generate_questions_from_ai(role, exp)
                
                st.session_state.page = "Interview"
                st.rerun()
            else: st.error("Phone required.")

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
    
    # --- SIDEBAR FIX: No unwanted codes showing ---
    with st.sidebar:
        if lottie_robot: st_lottie(lottie_robot, height=150, key="robot_side")
        st.divider()
        st.write(f"Candidate: **{st.session_state.candidate_data['name']}**")
        
        # FIX: Proper If-statement to prevent printing "None" or code objects
        if len(questions) > 0:
            st.progress(st.session_state.current_q / len(questions))

    # First Question Init
    if len(st.session_state.chat_history) == 0 and len(questions) > 0:
        first_q = questions[0]['question']
        st.session_state.chat_history.append({"role": "assistant", "content": f"**Q1:** {first_q}"})
        st.session_state.start_time = time.time()

    st.title("⚡ Quick-Fire Interview")

    # Display Chat History
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if not st.session_state.interview_complete:
        if st.session_state.start_time is None: st.session_state.start_time = time.time()
        
        user_ans = st.chat_input("Type answer here...")
        
        if user_ans:
            # 1. Show user answer instantly
            st.session_state.chat_history.append({"role": "user", "content": user_ans})
            with st.chat_message("user"):
                st.markdown(user_ans)
            
            # 2. Show LOADING only (No text, no codes)
            with st.chat_message("assistant"):
                placeholder = st.empty()
                with placeholder:
                    if lottie_processing:
                        st_lottie(lottie_processing, height=60, key="thinking")
                    else:
                        st.write("🔄 Analyzing...")

                # 3. Process Logic (Hidden)
                end_time = time.time()
                time_str = format_time(end_time - st.session_state.start_time)
                
                curr_data = questions[st.session_state.current_q]
                prompt = f"Q: {curr_data['question']} A: {user_ans}. Rate 1-10 (Start with 'Score: X/10')."
                
                try:
                    completion = client.chat.completions.create(
                        model="llama3-8b-8192", 
                        messages=[{"role": "system", "content": prompt}]
                    )
                    feedback = completion.choices[0].message.content
                    score = int(''.join(filter(str.isdigit, feedback.split("/10")[0]))) if "Score:" in feedback else 0
                    
                    st.session_state.scores.append(score)
                    st.session_state.admin_log.append(f"**Q:** {curr_data['question']}\n**A:** {user_ans}\n**⏱️ {time_str}** | **Rating:** {feedback}\n---")

                    st.session_state.current_q += 1
                    st.session_state.start_time = time.time()

                    # 4. Clear Loading & Show Next Question
                    placeholder.empty() # Removes the loading animation

                    if st.session_state.current_q < len(questions):
                        next_q = questions[st.session_state.current_q]['question']
                        st.session_state.chat_history.append({"role": "assistant", "content": f"**Q{st.session_state.current_q+1}:** {next_q}"})
                        st.rerun()
                    else:
                        st.session_state.interview_complete = True
                        st.rerun()
                
                except Exception as e:
                    st.error(f"Error: {e}")

    elif st.session_state.interview_complete and not st.session_state.submitted:
        st.divider()
        st.success("✅ Done!")
        if st.button("🚀 SUBMIT RESULTS"):
            final_packet = st.session_state.candidate_data
            final_packet["interview_score"] = sum(st.session_state.scores)
            final_packet["max_score"] = len(questions)*10
            final_packet["interview_details"] = st.session_state.admin_log
            save_result(final_packet)
            st.session_state.submitted = True
            st.balloons()
            st.rerun()

    elif st.session_state.submitted:
        st.title("🎉 Submitted")
        if st.button("Back to Home"):
            st.session_state.clear()
            st.session_state.page = "Login"
            st.rerun()

# ==========================================
# 4. ADMIN DASHBOARD
# ==========================================
elif st.session_state.page == "Dashboard":
    st.title("📊 HR Dashboard")
    if st.sidebar.button("Logout"):
        st.session_state.page = "Login"
        st.rerun()
    
    results = load_results()
    if results:
        st.table([{"Name": r['name'], "Role": r['role'], "Score": f"{r['interview_score']}/{r['max_score']}"} for r in results])
        selected = st.selectbox("View Candidate", [r['name'] for r in results])
        if selected:
            data = next((i for i in results if i["name"] == selected), None)
            if data:
                t1, t2 = st.tabs(["📝 Analysis", "📋 Resume"])
                with t1:
                    for line in data['interview_details']: st.markdown(line)
                with t2: st.info(data.get('resume_text'))
    else: st.info("No Data.")
