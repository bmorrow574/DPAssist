"""
Gmail integration for creating draft emails with scored feedback.
Tries IMAP first (creates a true draft).  If IMAP is blocked (common on
school Google Workspace accounts), falls back to sending the review email
directly to the teacher via SMTP_SSL so the teacher is never left without
notification of a late submission.
"""
import sys
from pathlib import Path

# Add parent directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

import imaplib
import smtplib
import time
from datetime import datetime
from email.message import EmailMessage
from typing import Dict, List, Optional
from config import config
from schemas.output import RunOutput


class GmailDraftCreator:
    """Create draft emails in Gmail using IMAP"""
    
    def __init__(self):
        pass
    
    def create_feedback_draft(
        self,
        student_email: str,
        student_name: str,
        rubric_title: str,
        output: RunOutput
    ) -> bool:
        """
        Create a draft email with scored feedback
        
        Args:
            student_email: Student's email address
            student_name: Student's name
            rubric_title: Title of the rubric
            output: RunOutput with evaluation results
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build email content
            subject = f"Portfolio Feedback: {rubric_title}"
            body_html = self._build_email_body(student_name, rubric_title, output)
            
            # Create email message
            msg = EmailMessage()
            msg['From'] = config.TEACHER_EMAIL
            msg['To'] = student_email
            msg['Subject'] = subject
            msg.set_content(body_html, subtype='html')
            
            # Connect to Gmail via IMAP
            imap = imaplib.IMAP4_SSL("imap.gmail.com")
            imap.login(config.TEACHER_EMAIL, config.GMAIL_APP_PASSWORD)
            
            # Append to Drafts folder
            drafts_mailbox = '"[Gmail]/Drafts"'
            typ, data = imap.append(
                drafts_mailbox,
                "",  # Flags
                imaplib.Time2Internaldate(time.time()),
                msg.as_bytes(),
            )
            
            imap.logout()
            
            if typ != "OK":
                print(f"IMAP append failed: {typ}, {data}")
                return False
            
            print(f"✓ Draft created for {student_email}")
            return True
            
        except Exception as e:
            print(f"Error creating Gmail draft: {e}")
            import traceback
            traceback.print_exc()
            return False

    def create_teacher_draft(
        self,
        student_email: str,
        student_name: str,
        unit: str,
        rubric_title: str,
        output: RunOutput,
        submission_date: Optional[str] = None,
        due_date: Optional[datetime] = None,
    ) -> bool:
        """
        Create a draft email in the teacher's inbox for a past-due submission.

        The draft is addressed to the teacher (not the student), includes scores
        and full rubric feedback, and is ready for the teacher to review, edit,
        and send.

        Args:
            student_email: Student's email address (shown in the draft body).
            student_name: Student's display name.
            unit: Unit/assignment name (used in subject line).
            rubric_title: Title of the rubric (used in subject line).
            output: RunOutput with full evaluation results including scores.
            submission_date: When the submission was received (optional).
            due_date: Assignment due date, highlighted as PAST DUE (optional).

        Returns:
            True if the draft was created successfully, False otherwise.
        """
        try:
            subject = f"[REVIEW DRAFT] {student_name} - {unit} - {rubric_title}"
            body_html = self._build_teacher_draft_body(
                student_email=student_email,
                student_name=student_name,
                unit=unit,
                rubric_title=rubric_title,
                output=output,
                submission_date=submission_date,
                due_date=due_date,
            )

            msg = EmailMessage()
            msg['From'] = config.TEACHER_EMAIL
            msg['To'] = config.TEACHER_EMAIL
            msg['Subject'] = subject
            msg.set_content(body_html, subtype='html')

            imap = imaplib.IMAP4_SSL("imap.gmail.com")
            imap.login(config.TEACHER_EMAIL, config.GMAIL_APP_PASSWORD)

            drafts_mailbox = '"[Gmail]/Drafts"'
            typ, data = imap.append(
                drafts_mailbox,
                "",
                imaplib.Time2Internaldate(time.time()),
                msg.as_bytes(),
            )

            imap.logout()

            if typ != "OK":
                print(f"IMAP append failed: {typ}, {data}")
                raise RuntimeError(f"IMAP append returned {typ}")

            print(f"✓ Teacher draft created for {student_name} ({student_email})")
            return True

        except Exception as e:
            print(f"IMAP draft creation failed ({e}). Falling back to teacher review email...")
            import traceback
            traceback.print_exc()
            return self._send_teacher_review_email_fallback(
                student_email=student_email,
                student_name=student_name,
                unit=unit,
                rubric_title=rubric_title,
                output=output,
                submission_date=submission_date,
                due_date=due_date,
            )

    def _send_teacher_review_email_fallback(
        self,
        student_email: str,
        student_name: str,
        unit: str,
        rubric_title: str,
        output: RunOutput,
        submission_date: Optional[str] = None,
        due_date: Optional[datetime] = None,
    ) -> bool:
        """
        Send a scored review email directly to the teacher when IMAP draft
        creation is unavailable (e.g. IMAP disabled on school Google Workspace).
        The teacher receives the same content they would see in a draft.
        """
        try:
            subject = f"[REVIEW NEEDED — PAST DUE] {student_name} — {unit} — {rubric_title}"
            body_html = self._build_teacher_draft_body(
                student_email=student_email,
                student_name=student_name,
                unit=unit,
                rubric_title=rubric_title,
                output=output,
                submission_date=submission_date,
                due_date=due_date,
            )

            msg = EmailMessage()
            msg["From"] = config.TEACHER_EMAIL
            msg["To"] = config.TEACHER_EMAIL
            msg["Subject"] = subject
            msg.set_content(body_html, subtype="html")

            with smtplib.SMTP_SSL("smtp.gmail.com", 465, local_hostname="localhost") as smtp:
                smtp.login(config.TEACHER_EMAIL, config.GMAIL_APP_PASSWORD)
                smtp.send_message(msg)

            print(f"✓ Teacher review email (fallback) sent to {config.TEACHER_EMAIL}")
            return True

        except Exception as e2:
            print(f"Teacher review email fallback also failed: {e2}")
            import traceback
            traceback.print_exc()
            return False

    def _build_teacher_draft_body(
        self,
        student_email: str,
        student_name: str,
        unit: str,
        rubric_title: str,
        output: RunOutput,
        submission_date: Optional[str] = None,
        due_date: Optional[datetime] = None,
    ) -> str:
        """Build the HTML body for the teacher review draft."""

        total_score = sum(r.score for r in output.results if r.score is not None)
        total_possible = sum(r.max_points for r in output.results if r.max_points is not None)
        percentage = (total_score / total_possible * 100) if total_possible > 0 else 0

        submission_str = submission_date if submission_date else "Unknown"
        due_str = due_date.strftime("%B %d, %Y") if due_date else "Unknown"

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 700px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #c0392b;
            color: white;
            padding: 20px 24px;
            border-radius: 6px 6px 0 0;
        }}
        .header h1 {{
            margin: 0 0 6px 0;
            font-size: 20px;
        }}
        .header p {{
            margin: 0;
            font-size: 14px;
            opacity: 0.9;
        }}
        .student-info {{
            background-color: #fdf2f2;
            border-left: 4px solid #c0392b;
            padding: 14px 16px;
            margin: 20px 0;
            border-radius: 0 4px 4px 0;
        }}
        .student-info p {{
            margin: 4px 0;
        }}
        .score-summary {{
            background-color: #f5f5f5;
            padding: 15px;
            margin: 20px 0;
            border-left: 4px solid #4A90E2;
            border-radius: 0 4px 4px 0;
        }}
        .criterion {{
            margin: 16px 0;
            padding: 16px;
            border: 1px solid #ddd;
            border-radius: 6px;
        }}
        .criterion-header {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .status {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.4px;
        }}
        .status-meets {{
            background-color: #d4edda;
            color: #155724;
        }}
        .status-partially {{
            background-color: #fff3cd;
            color: #856404;
        }}
        .status-not-yet {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        .evidence {{
            background-color: #f8f9fa;
            padding: 10px 14px;
            margin: 10px 0;
            border-left: 3px solid #6c757d;
            font-style: italic;
            font-size: 14px;
        }}
        .feedback {{
            margin: 10px 0;
        }}
        .what-to-add {{
            margin: 10px 0;
        }}
        .summary {{
            margin: 20px 0;
            padding: 16px;
            background-color: #e7f3ff;
            border-radius: 6px;
        }}
        .footer {{
            margin-top: 32px;
            padding-top: 16px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>[REVIEW DRAFT] Portfolio Evaluation: {rubric_title}</h1>
        <p>This draft is for your review. The student submission is PAST DUE.</p>
    </div>

    <div class="student-info">
        <p><strong>Student:</strong> {student_name} &lt;{student_email}&gt;</p>
        <p><strong>Unit:</strong> {unit}</p>
        <p><strong>Submission Date:</strong> {submission_str}</p>
        <p><strong>Due Date:</strong> {due_str} ⚠️ PAST DUE</p>
    </div>

    <div class="score-summary">
        <h2 style="margin: 0 0 8px 0;">Overall Score: {total_score:.1f} / {total_possible:.1f}</h2>
        <p style="margin: 0;">Percentage: {percentage:.1f}%</p>
    </div>

    <h2>Detailed Feedback by Criterion</h2>
"""

        for result in output.results:
            status_class = {
                'meets': 'status-meets',
                'partially_meets': 'status-partially',
                'not_yet': 'status-not-yet',
            }.get(result.status.value, '')
            status_label = result.status.value.replace('_', ' ').title()

            html += f"""
    <div class="criterion">
        <div class="criterion-header">
            {result.criterion_id}
            <span class="status {status_class}">{status_label}</span>
        </div>
"""

            if result.score is not None and result.max_points is not None:
                html += f"""
        <p><strong>Score:</strong> {result.score} / {result.max_points}</p>
"""

            html += f"""
        <div class="feedback">
            <strong>Feedback:</strong> {result.feedback}
        </div>
"""

            if result.evidence:
                html += """
        <div class="evidence">
            <strong>Evidence from portfolio:</strong>
"""
                for ev in result.evidence:
                    location = ev.ref.location if ev.ref.location else ev.ref.source_name
                    html += f"""
            <p>&ldquo;{ev.text}&rdquo;<br>
            <small>Source: {location}</small></p>
"""
                html += """
        </div>
"""

            if result.what_to_add:
                html += """
        <div class="what-to-add">
            <strong>To improve:</strong>
            <ul>
"""
                for item in result.what_to_add:
                    html += f"                <li>{item}</li>\n"
                html += """            </ul>
        </div>
"""

            html += """    </div>
"""

        html += """
    <div class="summary">
        <h2 style="margin-top: 0;">Summary</h2>
"""

        if output.summary.strengths:
            html += """
        <h3>✅ Strengths</h3>
        <ul>
"""
            for strength in output.summary.strengths:
                html += f"            <li>{strength}</li>\n"
            html += "        </ul>\n"

        if output.summary.biggest_gaps:
            html += """
        <h3>📈 Areas for Growth</h3>
        <ul>
"""
            for gap in output.summary.biggest_gaps:
                html += f"            <li>{gap}</li>\n"
            html += "        </ul>\n"

        if output.summary.missing_artifacts:
            html += """
        <h3>❗ Missing Elements</h3>
        <ul>
"""
            for missing in output.summary.missing_artifacts:
                html += f"            <li>{missing}</li>\n"
            html += "        </ul>\n"

        if output.summary.teacher_comment_draft:
            html += f"""
        <div style="margin-top: 16px; padding: 14px; background-color: white; border: 1px solid #ddd; border-radius: 4px;">
            <strong>Draft Teacher Comment:</strong>
            <p style="margin: 8px 0 0 0;">{output.summary.teacher_comment_draft}</p>
        </div>
"""

        html += """    </div>

    <div class="footer">
        <p>This evaluation was generated automatically by DPAssist and requires teacher review before sending.</p>
    </div>
</body>
</html>
"""
        return html

    def _build_email_body(
        self,
        student_name: str,
        rubric_title: str,
        output: RunOutput
    ) -> str:
        """Build HTML email body with feedback"""
        
        # Calculate total score
        total_score = sum(r.score for r in output.results if r.score is not None)
        total_possible = sum(r.max_points for r in output.results if r.max_points is not None)
        
        # Calculate percentage safely (avoid division by zero)
        if total_possible > 0:
            percentage = (total_score / total_possible) * 100
        else:
            percentage = 0
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .header {{
            background-color: #4A90E2;
            color: white;
            padding: 20px;
            border-radius: 5px;
        }}
        .score-summary {{
            background-color: #f5f5f5;
            padding: 15px;
            margin: 20px 0;
            border-left: 4px solid #4A90E2;
        }}
        .criterion {{
            margin: 20px 0;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }}
        .criterion-header {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .status {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .status-meets {{
            background-color: #d4edda;
            color: #155724;
        }}
        .status-partially {{
            background-color: #fff3cd;
            color: #856404;
        }}
        .status-not-yet {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        .evidence {{
            background-color: #f8f9fa;
            padding: 10px;
            margin: 10px 0;
            border-left: 3px solid #6c757d;
            font-style: italic;
        }}
        .feedback {{
            margin: 10px 0;
        }}
        .what-to-add {{
            margin: 10px 0;
        }}
        .summary {{
            margin: 20px 0;
            padding: 15px;
            background-color: #e7f3ff;
            border-radius: 5px;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Portfolio Evaluation: {rubric_title}</h1>
        <p>Student: {student_name}</p>
    </div>
    
    <div class="score-summary">
        <h2>Overall Score: {total_score:.1f} / {total_possible:.1f}</h2>
        <p>Percentage: {percentage:.1f}%</p>
    </div>
    
    <h2>Detailed Feedback by Criterion</h2>
"""
        
        # Add results for each criterion
        for result in output.results:
            status_class = {
                'meets': 'status-meets',
                'partially_meets': 'status-partially',
                'not_yet': 'status-not-yet'
            }.get(result.status.value, '')
            
            html += f"""
    <div class="criterion">
        <div class="criterion-header">
            {result.criterion_id}
            <span class="status {status_class}">{result.status.value.replace('_', ' ')}</span>
        </div>
"""
            
            if result.score is not None and result.max_points is not None:
                html += f"""
        <p><strong>Score:</strong> {result.score} / {result.max_points}</p>
"""
            
            html += f"""
        <div class="feedback">
            <strong>Feedback:</strong> {result.feedback}
        </div>
"""
            
            # Add evidence
            if result.evidence:
                html += """
        <div class="evidence">
            <strong>Evidence from your portfolio:</strong>
"""
                for ev in result.evidence:
                    html += f"""
            <p>"{ev.text}"<br>
            <small>Location: {ev.ref.location}</small></p>
"""
                html += """
        </div>
"""
            
            # Add what to add
            if result.what_to_add:
                html += """
        <div class="what-to-add">
            <strong>To improve:</strong>
            <ul>
"""
                for item in result.what_to_add:
                    html += f"""
                <li>{item}</li>
"""
                html += """
            </ul>
        </div>
"""
            
            html += """
    </div>
"""
        
        # Add summary
        html += f"""
    <div class="summary">
        <h2>Summary</h2>
        
        <h3>Strengths</h3>
        <ul>
"""
        for strength in output.summary.strengths:
            html += f"""
            <li>{strength}</li>
"""
        
        html += """
        </ul>
        
        <h3>Areas for Growth</h3>
        <ul>
"""
        for gap in output.summary.biggest_gaps:
            html += f"""
            <li>{gap}</li>
"""
        
        html += """
        </ul>
"""
        
        if output.summary.missing_artifacts:
            html += """
        <h3>Missing Elements</h3>
        <ul>
"""
            for missing in output.summary.missing_artifacts:
                html += f"""
            <li>{missing}</li>
"""
            html += """
        </ul>
"""
        
        if output.summary.teacher_comment_draft:
            html += f"""
        <div style="margin-top: 20px; padding: 15px; background-color: white; border: 1px solid #ddd;">
            <strong>Teacher Comments:</strong>
            <p>{output.summary.teacher_comment_draft}</p>
        </div>
"""
        
        html += """
    </div>
    
    <div class="footer">
        <p>This evaluation was generated automatically. If you have questions about your feedback, please reach out to your teacher.</p>
    </div>
</body>
</html>
"""
        
        return html
