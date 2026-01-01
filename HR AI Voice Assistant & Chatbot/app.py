import streamlit as st
import json
import os
import time
import requests
from datetime import datetime
from groq import Groq
from pypdf import PdfReader
from streamlit_lottie import st_lottie

# --- CONFIGURATION ---
st.set_page_config(page_title="Infinite AI Interviewer", layout="wide", page_icon="🤖")

API_KEY = "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" # Replace if needed
ADMIN_PASSWORD = "admin" 
RESULTS_FILE = 'interview_results.json'

if not API_KEY:
    st.error("⚠️ API Key is missing.")
    st.stop()

client = Groq(api_key=API_KEY)

# --- CSS STYLING ---
st.markdown("""
<style>
    div.stButton > button {
        background: linear-gradient(to bottom, #4b93ff 5%, #0056b3 100%);
        background-color: #4b93ff;
        border-radius: 10px;
        color: white;
        font-weight: bold;
        padding: 10px 24px;
        box-shadow: 0px 5px 0px 0px #002a55;
        transition: all 0.1s;
    }
    div.stButton > button:active {
        transform: translateY(5px);
        box-shadow: 0px 0px 0px 0px #002a55;
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except: return None

lottie_robot = load_lottieurl("https://lottie.host/5a8b7533-8515-4122-8700-1c3132d73315/o5gXyXy2gP.json")
lottie_processing = load_lottieurl("https://lottie.host/803855eb-3760-466d-92df-8f5379201f37/hYkH99H46F.json")

def generate_questions_from_ai(role, exp):
    """
    This function asks Groq to generate 5 unique questions based on the Role and Experience.
    It returns a list of dictionaries.
    """
    prompt = f"""
    Generate 5 technical interview questions for a {role} with {exp} years of experience.
    Output MUST be a valid JSON array exactly like this:
    [
        {{"question": "Question 1 text", "expected_answer": "Brief expected answer"}},
        {{"question": "Question 2 text", "expected_answer": "Brief expected answer"}}
    ]
    Do not add any extra text, just the JSON.
    """
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": prompt}]
        )
        content = completion.choices[0].message.content
        # Find the start and end of the JSON array to avoid parsing errors
        start = content.find('[')
        end = content.rfind(']') + 1
        json_str = content[start:end]
        return json.loads(json_str)
    except Exception as e:
        # Fallback if AI fails
        return [
            {"question": f"Tell me about your experience as a {role}.", "expected_answer": "Experience summary"},
            {"question": "What is your biggest technical challenge?", "expected_answer": "Problem solving"},
            {"question": "Why do you want to join us?", "expected_answer": "Motivation"}
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
    m, s = divmod(seconds, 60)
    return f"{int(m)}m {int(s)}s" if m > 0 else f"{int(s)}s"

# --- SESSION STATE ---
if "page" not in st.session_state: st.session_state.page = "Login"
if "candidate_data" not in st.session_state: st.session_state.candidate_data = {}

# ==========================================
# 1. LOGIN PAGE
# ==========================================
if st.session_state.page == "Login":
    st.title("🔐 Infinite AI Interviewer")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if lottie_robot: st_lottie(lottie_robot, height=300, key="robot_login")
    
    with col2:
        tab1, tab2 = st.tabs(["👤 Candidate", "🛡️ Admin"])
        
        with tab1:
            st.header("Start Application")
            c_name = st.text_input("Full Name")
            c_email = st.text_input("Email Address")
            if st.button("🚀 Enter Portal"):
                if c_name and c_email:
                    st.session_state.candidate_data = {
                        "name": c_name, "email": c_email,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.page = "Profile_Setup"
                    st.rerun()
                else: st.warning("Enter details.")

        with tab2:
            st.header("Admin Access")
            password = st.text_input("Password", type="password")
            if st.button("Login Admin"):
                if password == ADMIN_PASSWORD:
                    st.session_state.page = "Dashboard"
                    st.rerun()
                else: st.error("Denied.")

# ==========================================
# 2. PROFILE SETUP
# ==========================================
elif st.session_state.page == "Profile_Setup":
    st.title("📄 Professional Profile")
    st.write(f"Welcome, **{st.session_state.candidate_data['name']}**.")
    
    with st.form("hr_form"):
        col1, col2 = st.columns(2)
        with col1:
            role = st.selectbox("Role", ["Python Developer", "AI Engineer", "Data Analyst", "React Developer", "Java Developer"]) # Added more roles
            phone = st.text_input("Phone (Required)")
            exp = st.number_input("Experience (Years)", 0, 20, 0)
        with col2:
            notice = st.selectbox("Notice Period", ["Immediate", "15 Days", "30 Days"])
            ctc = st.text_input("Current CTC")
            resume_file = st.file_uploader("Upload Resume (Optional)", type=["pdf"])
        
        submitted = st.form_submit_button("✅ Generate Interview")
        
        if submitted:
            if phone:
                resume_text = extract_text_from_pdf(resume_file) if resume_file else "No Resume Uploaded"
                st.session_state.candidate_data.update({
                    "role": role, "phone": phone, "experience": exp,
                    "notice_period": notice, "ctc": ctc, "resume_text": resume_text
                })
                
                # --- 🚀 TRIGGER AI GENERATION HERE ---
                with st.spinner(f"🧠 AI is researching {role} questions for you..."):
                    generated_q = generate_questions_from_ai(role, exp)
                    st.session_state.interview_questions = generated_q
                    
                st.session_state.page = "Interview"
                st.rerun()
            else: st.error("Phone Number is required.")

# ==========================================
# 3. INTERVIEW (DYNAMIC QUESTIONS)
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

    # Load the dynamically generated questions
    questions = st.session_state.interview_questions
    
    with st.sidebar:
        if lottie_robot: st_lottie(lottie_robot, height=200, key="robot_sidebar")
        st.divider()
        st.write(f"👤 **{st.session_state.candidate_data['name']}**")
        st.write(f"💼 **{st.session_state.candidate_data['role']}**")
        st.progress(st.session_state.current_q / len(questions)) if len(questions) > 0 else None

    if len(st.session_state.chat_history) == 0 and len(questions) > 0:
        first_q = questions[0]['question']
        st.session_state.chat_history.append({"role": "assistant", "content": f"**Q1:** {first_q}"})
        st.session_state.start_time = time.time()

    st.title("🤖 AI Live Interview")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if not st.session_state.interview_complete:
        if st.session_state.start_time is None: st.session_state.start_time = time.time()
        
        user_ans = st.chat_input("Type your answer...")
        
        if user_ans:
            with st.chat_message("assistant"):
                if lottie_processing: st_lottie(lottie_processing, height=100, key="thinking")
            
            end_time = time.time()
            formatted_time = format_time(end_time - st.session_state.start_time)
            st.session_state.chat_history.append({"role": "user", "content": user_ans})
            
            curr_data = questions[st.session_state.current_q]
            prompt = f"Q: {curr_data['question']} Ans: {user_ans} Task: Rate 1-10. Start with 'Score: X/10'."
            
            try:
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": prompt}]
                )
                feedback = completion.choices[0].message.content
                score = int(''.join(filter(str.isdigit, feedback.split("/10")[0]))) if "Score:" in feedback else 0
                
                st.session_state.scores.append(score)
                st.session_state.admin_log.append(f"**Q:** {curr_data['question']}\n**A:** {user_ans}\n**⏱️ {formatted_time}** | **Rating:** {feedback}\n---")

                st.session_state.current_q += 1
                st.session_state.start_time = time.time()

                if st.session_state.current_q < len(questions):
                    next_q = questions[st.session_state.current_q]['question']
                    st.session_state.chat_history.append({"role": "assistant", "content": f"**Q{st.session_state.current_q+1}:** {next_q}"})
                else:
                    st.session_state.interview_complete = True
                
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    elif st.session_state.interview_complete and not st.session_state.submitted:
        st.divider()
        st.success("✅ Interview Completed!")
        if st.button("🚀 SUBMIT INTERVIEW"):
            final_packet = st.session_state.candidate_data
            final_packet["interview_score"] = sum(st.session_state.scores)
            final_packet["max_score"] = len(questions)*10
            final_packet["interview_details"] = st.session_state.admin_log
            save_result(final_packet)
            st.session_state.submitted = True
            st.balloons()
            st.rerun()

    elif st.session_state.submitted:
        st.title("🎉 Success!")
        if lottie_robot: st_lottie(lottie_robot, height=200, key="success_anim")
        st.info("Results sent to HR.")
        if st.button("⬅️ Back to Login"):
            st.session_state.clear()
            st.session_state.page = "Login"
            st.rerun()

# ==========================================
# 4. ADMIN DASHBOARD
# ==========================================
elif st.session_state.page == "Dashboard":
    st.title("📊 HR Analytics")
    if st.sidebar.button("Log Out"):
        st.session_state.page = "Login"
        st.rerun()
    
    results = load_results()
    if results:
        st.table([{"Name": r['name'], "Role": r['role'], "Score": f"{r['interview_score']}/{r['max_score']}"} for r in results])
        selected = st.selectbox("Select Candidate", [r['name'] for r in results])
        if selected:
            data = next((i for i in results if i["name"] == selected), None)
            if data:
                t1, t2, t3 = st.tabs(["📝 Analysis", "📋 Resume", "👤 Info"])
                with t1:
                    for line in data['interview_details']: st.markdown(line)
                with t2: st.info(data.get('resume_text'))
                with t3: st.write(data.get('email'))
    else:
        st.info("No Data.")