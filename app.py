import streamlit as st
import logging
import pandas as pd
from datetime import datetime
import io

# Import your existing backend logic
from main import DPAssistOrchestrator

# --- Page Config ---
st.set_page_config(
    page_title="DPAssist Teacher Dashboard",
    page_icon="🎓",
    layout="wide"
)

# --- Custom Logging Handler to show logs in the UI ---
class StreamlitLogHandler(logging.Handler):
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.text = ""

    def emit(self, record):
        msg = self.format(record)
        self.text += msg + "\n"
        self.container.code(self.text, language="text")

# --- Initialize the System ---
@st.cache_resource
def get_orchestrator():
    """Initializes the backend system once."""
    return DPAssistOrchestrator()

# --- Main App Interface ---
def main():
    st.title("🎓 DPAssist: Teacher Dashboard")
    st.markdown("Automated grading and feedback for student portfolios.")

    # Initialize Backend
    try:
        with st.spinner("Connecting to agents..."):
            orchestrator = get_orchestrator()
        st.success("✅ System Online")
    except Exception as e:
        st.error(f"Failed to connect: {e}")
        return

    # ==========================================
    # SIDEBAR: Teacher Controls
    # ==========================================
    with st.sidebar:
        st.header("📋 Grading Settings")
        
        # 1. Due Date Setting
        st.subheader("1. Set Due Date")
        current_deadline = orchestrator.timeliness_agent.deadline
        new_date = st.date_input("Deadline Date", value=current_deadline.date())
        new_time = st.time_input("Deadline Time", value=current_deadline.time())
        
        # Combine into a datetime object
        selected_deadline = datetime.combine(new_date, new_time)
        
        # 2. Rubric Upload
        st.subheader("2. Upload Rubric")
        uploaded_rubric = st.file_uploader("Upload Rubric (PDF, Docx, or Txt)", type=['pdf', 'docx', 'txt'])
        
        # 3. Student Exceptions (Extensions)
        st.subheader("3. Manage Exceptions")
        st.caption("Enter emails of students allowed to be late (one per line).")
        exempt_emails_input = st.text_area("Extended/Exempt Students")
        exempt_emails = [e.strip() for e in exempt_emails_input.split('\n') if e.strip()]

        st.markdown("---")
        check_now = st.button("🚀 Run Grading Now", type="primary")

    # ==========================================
    # MAIN AREA
    # ==========================================
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Live Processing Logs")
        log_container = st.empty()
        
        if check_now:
            # --- APPLY TEACHER SETTINGS BEFORE RUNNING ---
            
            # 1. Update Deadline in Agent
            orchestrator.timeliness_agent.deadline = selected_deadline
            st.toast(f"Deadline set to: {selected_deadline}")
            
            # 2. Update Rubric in Agent (if uploaded)
            if uploaded_rubric:
                # Read file content based on type
                try:
                    import PyPDF2
                    import docx
                    
                    file_text = ""
                    if uploaded_rubric.name.endswith('.pdf'):
                        reader = PyPDF2.PdfReader(uploaded_rubric)
                        file_text = '\n'.join(page.extract_text() for page in reader.pages)
                    elif uploaded_rubric.name.endswith('.docx'):
                        doc = docx.Document(uploaded_rubric)
                        file_text = '\n'.join(p.text for p in doc.paragraphs)
                    else: # txt
                        stringio = io.StringIO(uploaded_rubric.getvalue().decode("utf-8"))
                        file_text = stringio.read()
                    
                    # Inject into Feedback Generator
                    orchestrator.feedback_generator.rubric_text = file_text
                    st.toast("✅ Custom Rubric Loaded")
                except Exception as e:
                    st.error(f"Error reading rubric: {e}")

            # 3. Setup Logging
            logger = logging.getLogger()
            for h in logger.handlers: logger.removeHandler(h) # Clear old
            
            handler = StreamlitLogHandler(log_container)
            formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

            # --- RUN THE LOGIC ---
            try:
                pending = orchestrator.submission_monitor.get_pending_submissions()
                
                if not pending:
                    logger.info("No new pending submissions found.")
                    st.info("No new submissions found to grade.")
                else:
                    st.toast(f"Grading {len(pending)} portfolios...")
                    progress_bar = st.progress(0)
                    
                    for i, submission in enumerate(pending):
                        # Get Student Info
                        student_name = f"{submission.get('First Name', '')} {submission.get('Last Name', '')}"
                        student_email = submission.get('Email', '')
                        
                        st.write(f"**Analyzing:** {student_name}")
                        
                        # CHECK FOR EXCEPTIONS (EXTENSIONS)
                        # If student is in the 'Exempt' list, we temporarily trick the agent 
                        # by moving the deadline into the future just for this student.
                        original_deadline = orchestrator.timeliness_agent.deadline
                        if student_email in exempt_emails:
                            logger.info(f"⚠️ Student {student_name} has an extension. Bypassing late check.")
                            # Set deadline to next year so they are always "on time"
                            orchestrator.timeliness_agent.deadline = datetime(2030, 1, 1)
                        
                        # Process
                        success = orchestrator.process_submission(submission)
                        
                        # Restore original deadline for next student
                        orchestrator.timeliness_agent.deadline = original_deadline
                        
                        status = "✅ Done" if success else "❌ Failed"
                        st.caption(f"{status} - {student_name}")
                        progress_bar.progress((i + 1) / len(pending))
                    
                    st.balloons()
                    st.success("Grading Run Complete!")
                    
            except Exception as e:
                st.error(f"Critical Error: {e}")
                logger.error(f"Error: {e}")

    with col2:
        st.subheader("Quick Links")
        try:
            sheet_name = orchestrator.config['google_sheets']['spreadsheet_name']
            st.link_button("📂 Open Google Sheet", f"https://docs.google.com/spreadsheets/d/{sheet_name}")
        except:
            st.info("Spreadsheet link unavailable")
            
        st.info(f"**Current Deadline Config:**\n\n{selected_deadline.strftime('%B %d, %Y at %I:%M %p')}")

if __name__ == "__main__":
    main()