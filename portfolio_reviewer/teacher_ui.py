"""
Teacher UI - Streamlit interface for managing rubrics and monitoring submissions
"""
import re
import sys
from pathlib import Path

# Add parent directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

import streamlit as st
from datetime import datetime, date

from config import config
from rubric_manager import RubricManager
from rubric_parser import RubricParser
from google_sheets import GoogleSheetsClient

# Compiled pattern for minimal email address validation
_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

def setup_page():
    """Configure Streamlit page"""
    st.set_page_config(
        page_title="DPAssist - Teacher Dashboard",
        page_icon="📝",
        layout="wide"
    )
    
    st.title("📝 DPAssist - Teacher Dashboard")

def check_configuration():
    """Check if system is properly configured"""
    errors = config.validate()
    
    if errors:
        st.error("⚠️ Configuration Issues")
        for error in errors:
            st.write(f"- {error}")
        st.info("Please create a .env file with your credentials. See .env.example for reference.")
        st.stop()

def render_rubric_management(rubric_manager: RubricManager, rubric_parser: RubricParser):
    """Render rubric upload and management section"""
    st.header("Rubric Management")
    
    # List existing rubrics
    units = rubric_manager.list_units()
    
    if units:
        st.subheader("Configured Rubrics")
        
        for unit in units:
            with st.expander(f"{unit['unit_name']} - {unit['title']}"):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                col1.write(f"**Due Date:** {unit['due_date']}")
                
                status = "⏰ Active" if not unit['is_past_due'] else "✅ Past Due"
                col2.write(f"**Status:** {status}")
                
                if col3.button("Delete", key=f"delete_{unit['unit_name']}" ):
                    rubric_manager.delete_rubric(unit['unit_name'])
                    st.success(f"Deleted rubric for {unit['unit_name']}")
                    st.rerun()
    
    st.divider()
    
    # Upload new rubric
    st.subheader("Add New Rubric")
    
    uploaded_file = st.file_uploader(
        "Upload Rubric PDF",
        type=['pdf'],
        help="Upload a rubric PDF. The system will attempt to extract criteria automatically."
    )
    
    if uploaded_file:
        col1, col2 = st.columns(2)
        
        with col1:
            unit_name = st.text_input(
                "Unit Name",
                help="This should match the unit name in your Google Form exactly (e.g., 'Plane and Simple')"
            )
        
        with col2:
            due_date = st.date_input(
                "Due Date",
                min_value=date(2020, 1, 1)
            )
        
        if st.button("Parse and Add Rubric"):
            if not unit_name:
                st.error("Please enter a unit name")
            else:
                with st.spinner("Parsing rubric PDF..."):
                    # Save uploaded file temporarily
                    temp_path = config.RUBRICS_DIR / uploaded_file.name
                    with open(temp_path, 'wb') as f:
                        f.write(uploaded_file.getvalue())
                    
                    # Parse PDF
                    rubric = rubric_parser.parse_pdf(temp_path)
                    
                    if rubric:
                        # Add to manager
                        rubric_manager.add_rubric(
                            rubric=rubric,
                            unit_name=unit_name,
                            due_date=due_date.strftime('%Y-%m-%d'),
                            pdf_path=temp_path
                        )
                        
                        st.success(f"✅ Successfully added rubric for {unit_name}")
                        
                        # Show parsed criteria
                        with st.expander("View Parsed Criteria"):
                            for category in rubric.categories:
                                st.write(f"**{category.name}**")
                                for criterion in category.criteria:
                                    st.write(f"- {criterion.title} ({criterion.max_points} points)")
                        
                        st.rerun()
                    else:
                        st.error("Failed to parse rubric. Please check the PDF format.")

def render_submissions_monitor(sheets_client: GoogleSheetsClient, rubric_manager: RubricManager):
    """Render submissions monitoring section"""
    st.header("Recent Submissions")
    
    try:
        submissions = sheets_client.get_all_submissions()
        
        if not submissions:
            st.info("No submissions found in Google Sheet")
            return
        
        # Show summary
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Submissions", len(submissions))
        
        # Count by status
        statuses = {}
        for record in submissions:
            status = record.get('Status', 'Pending')
            statuses[status] = statuses.get(status, 0) + 1
        
        col2.metric("Processed", statuses.get('Draft created', 0))
        col3.metric("Pending", statuses.get('Pending', 0) + statuses.get('Processing', 0))
        
        st.divider()
        
        # Show recent submissions table
        st.subheader("Latest 20 Submissions")
        
        # Parse and display submissions
        display_data = []
        for record in submissions[-20:]:  # Last 20
            parsed = GoogleSheetsClient.parse_submission(record) or {}

            # Fallback email lookup: scan raw record values for something that
            # looks like a real email address — works regardless of header name.
            email = parsed.get('email')
            if not email or not _EMAIL_RE.match(str(email)):
                for value in record.values():
                    if isinstance(value, str) and _EMAIL_RE.match(value):
                        email = value
                        break

            # Discard any value that still doesn't look like an email address
            if email and '@' not in str(email):
                email = None

            # Get rubric info
            unit = parsed.get('unit', 'Unknown')
            due_date = rubric_manager.get_due_date(unit)
            is_past_due = rubric_manager.is_past_due(unit)

            display_data.append({
                'Student': parsed.get('student_name', 'Unknown'),
                'Email': email or 'Unknown',
                'Unit': unit,
                'Status': record.get('Status', 'Pending'),
                'Due': due_date.strftime('%Y-%m-%d') if due_date else 'Not set',
                'Past Due': '✅' if is_past_due else '⏰',
                'Submitted': parsed.get('timestamp', 'Unknown')
            })
        
        if display_data:
            st.dataframe(
                display_data,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No parsed submissions to display")
    
    except Exception as e:
        st.error(f"Error loading submissions: {e}")

def render_system_status():
    """Render system status section"""
    st.header("System Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Configuration")
        
        # Check each component
        checks = {
            "Google Sheets": bool(config.GOOGLE_SHEET_ID),
            "Gemini API": bool(config.GEMINI_API_KEY),
            "Gmail": bool(config.TEACHER_EMAIL),
            "Credentials File": Path(config.GOOGLE_CREDENTIALS_PATH).exists()
        }
        
        for component, status in checks.items():
            if status:
                st.write(f"✅ {component}")
            else:
                st.write(f"❌ {component}")
    
    with col2:
        st.subheader("Settings")
        st.write(f"**Check Interval:** {config.CHECK_INTERVAL_SECONDS}s")
        st.write(f"**Teacher Email:** {config.TEACHER_EMAIL}")
        st.write(f"**Sheet ID:** {config.GOOGLE_SHEET_ID[:20]}...")


def main():
    """Main Streamlit app"""
    setup_page()
    check_configuration()
    
    # Initialize managers
    config.setup_directories()
    rubric_manager = RubricManager()
    rubric_parser = RubricParser()
    
    try:
        sheets_client = GoogleSheetsClient()
    except Exception as e:
        st.error(f"Failed to connect to Google Sheets: {e}")
        st.stop()
    
    # Sidebar navigation
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Select Page",
            ["Rubrics", "Submissions", "System Status"],
            label_visibility="collapsed"
        )
        
        st.divider()
        st.caption("DPAssist v1.0")
        st.caption("Automated portfolio evaluation system")
    
    # Render selected page
    if page == "Rubrics":
        render_rubric_management(rubric_manager, rubric_parser)
    elif page == "Submissions":
        render_submissions_monitor(sheets_client, rubric_manager)
    elif page == "System Status":
        render_system_status()


if __name__ == '__main__':
    main()