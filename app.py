import streamlit as st
import logging
import time
from typing import List, Dict, Any

# Import your existing backend logic
from main import DPAssistOrchestrator

# --- Page Config ---
st.set_page_config(
    page_title="DPAssist Dashboard",
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

# --- Initialize the System (Cached so it doesn't reload every click) ---
@st.cache_resource
def get_orchestrator():
    """Initializes the backend system once."""
    return DPAssistOrchestrator()

# --- Main App Interface ---
def main():
    st.title("🎓 DPAssist: Feedback Tool")
    st.markdown("Use this dashboard to run checks on student portfolios without opening the terminal.")

    # Initialize the backend
    try:
        with st.spinner("Connecting to Google Cloud & AI Agents..."):
            orchestrator = get_orchestrator()
        st.success("System Online and Connected!")
    except Exception as e:
        st.error(f"Failed to connect: {e}")
        return

    # --- Sidebar for Settings ---
    with st.sidebar:
        st.header("Control Panel")
        check_now = st.button("Check for New Submissions", type="primary")
        
        st.markdown("---")
        st.caption("System Status")
        
        # Display Config Info (Safely)
        st.info(f"📅 Deadline: {orchestrator.timeliness_agent.deadline}")
        st.info(f"📧 Teacher: {orchestrator.email_drafter.teacher_email}")

    # --- Main Action Area ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Live Processing Logs")
        log_container = st.empty()
        
        # If user clicks the button
        if check_now:
            # Setup UI logging
            logger = logging.getLogger()
            # Clear old handlers to prevent duplicates
            for h in logger.handlers:
                logger.removeHandler(h)
            
            # Attach our new Streamlit handler
            handler = StreamlitLogHandler(log_container)
            formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

            st.toast("Checking spreadsheet...")
            
            # RUN THE CHECK (Using your existing logic)
            try:
                # 1. Get Pending
                pending = orchestrator.submission_monitor.get_pending_submissions()
                
                if not pending:
                    logger.info("No new pending submissions found.")
                    st.info("No new submissions found.")
                else:
                    st.toast(f"Found {len(pending)} new submissions!")
                    logger.info(f"Found {len(pending)} pending submission(s)")
                    
                    # 2. Process Each
                    progress_bar = st.progress(0)
                    for i, submission in enumerate(pending):
                        student_name = f"{submission.get('First Name', '')} {submission.get('Last Name', '')}"
                        st.subheader(f"Processing: {student_name}")
                        
                        success = orchestrator.process_submission(submission)
                        
                        if success:
                            st.success(f"Successfully processed {student_name}")
                        else:
                            st.error(f"Failed to process {student_name}")
                        
                        progress_bar.progress((i + 1) / len(pending))
                    
                    st.balloons()
                    
            except Exception as e:
                st.error(f"Critical Error: {e}")
                logger.error(f"Error: {e}")

    with col2:
        st.subheader("Quick Links")
        st.link_button("Open Google Sheet", f"https://docs.google.com/spreadsheets/d/{orchestrator.config['google_sheets']['spreadsheet_name']}")

if __name__ == "__main__":
    main()