"""
Email service for sending feedback emails to students via Gmail SMTP.
Uses App Password authentication — no admin/OAuth required.
"""
import sys
from pathlib import Path

# Add parent directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

import smtplib
import traceback
from datetime import datetime
from email.message import EmailMessage
from typing import Optional

from config import config
from schemas.output import RunOutput


class EmailService:
    """Send feedback emails to students via Gmail SMTP."""

    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 465

    def send_feedback_email(
        self,
        student_email: str,
        student_name: str,
        rubric_title: str,
        output: RunOutput,
        due_date: Optional[datetime] = None,
        portfolio_url: str = "",
    ) -> bool:
        """
        Send a feedback email (without scores) to a student.

        Args:
            student_email: Student's email address.
            student_name: Student's display name.
            rubric_title: Title of the rubric / assignment.
            output: RunOutput containing criterion results and summary.
            due_date: Resubmission deadline (optional).
            portfolio_url: URL the student can update for resubmission (optional).

        Returns:
            True if the email was sent successfully, False otherwise.
        """
        try:
            subject = f"Portfolio Feedback: {rubric_title}"
            body_html = self._build_email_body(
                student_name=student_name,
                rubric_title=rubric_title,
                output=output,
                due_date=due_date,
                portfolio_url=portfolio_url,
            )

            msg = EmailMessage()
            msg["From"] = config.TEACHER_EMAIL
            msg["To"] = student_email
            msg["Subject"] = subject
            msg.set_content(body_html, subtype="html")

            with smtplib.SMTP_SSL(self.SMTP_HOST, self.SMTP_PORT) as smtp:
                smtp.login(config.TEACHER_EMAIL, config.GMAIL_APP_PASSWORD)
                smtp.send_message(msg)

            print(f"✓ Feedback email sent to {student_email}")
            return True

        except Exception as e:
            print(f"Error sending feedback email to {student_email}: {e}")
            traceback.print_exc()
            return False

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_email_body(
        self,
        student_name: str,
        rubric_title: str,
        output: RunOutput,
        due_date: Optional[datetime] = None,
        portfolio_url: str = "",
    ) -> str:
        """Build the HTML body for the feedback email."""

        deadline_str = (
            due_date.strftime("%B %d, %Y") if due_date else "your teacher's specified date"
        )
        resubmit_section = ""
        if portfolio_url:
            resubmit_section = f"""
    <div class="callout">
        <p><strong>🔗 Resubmission link:</strong>
        <a href="{portfolio_url}">{portfolio_url}</a></p>
    </div>
"""

        teacher_contact = config.TEACHER_EMAIL if config.TEACHER_EMAIL else "your teacher"

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
            background-color: #4A90E2;
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
        .body-content {{
            padding: 20px 0;
        }}
        .deadline-box {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 12px 16px;
            margin: 20px 0;
            border-radius: 0 4px 4px 0;
        }}
        .criterion {{
            margin: 16px 0;
            padding: 16px;
            border: 1px solid #ddd;
            border-radius: 6px;
        }}
        .criterion-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
        }}
        .criterion-title {{
            font-weight: bold;
            color: #2c3e50;
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
        .improve-list {{
            margin: 10px 0;
            padding-left: 20px;
        }}
        .summary-box {{
            margin: 24px 0;
            padding: 16px;
            background-color: #e7f3ff;
            border-radius: 6px;
        }}
        .callout {{
            margin: 20px 0;
            padding: 14px 16px;
            background-color: #f0fff4;
            border-left: 4px solid #28a745;
            border-radius: 0 4px 4px 0;
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
        <h1>Portfolio Feedback: {rubric_title}</h1>
        <p>Hi {student_name} — here is your personalised feedback.</p>
    </div>

    <div class="body-content">
        <p>Dear {student_name},</p>

        <p>Your portfolio for <strong>{rubric_title}</strong> has been reviewed.
        Below you will find detailed feedback for each criterion.  Please read
        through each section carefully — there are specific, actionable steps
        you can take to strengthen your work before the deadline.</p>

        <div class="deadline-box">
            <strong>⏰ Resubmission deadline: {deadline_str}</strong><br>
            Please update your portfolio and notify your teacher before this date.
        </div>

        <h2 style="color:#2c3e50;">Criterion-by-Criterion Feedback</h2>
"""

        for result in output.results:
            status_value = result.status.value
            status_class = {
                "meets": "status-meets",
                "partially_meets": "status-partially",
                "not_yet": "status-not-yet",
            }.get(status_value, "")
            status_label = status_value.replace("_", " ").title()

            html += f"""
        <div class="criterion">
            <div class="criterion-header">
                <span class="criterion-title">{result.criterion_id}</span>
                <span class="status {status_class}">{status_label}</span>
            </div>
"""

            html += f"""
            <div class="feedback">
                <strong>Feedback:</strong> {result.feedback}
            </div>
"""

            if result.evidence:
                html += """
            <div class="evidence">
                <strong>Evidence from your portfolio:</strong>
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
            <div>
                <strong>To improve this criterion:</strong>
                <ul class="improve-list">
"""
                for item in result.what_to_add:
                    html += f"                    <li>{item}</li>\n"
                html += """                </ul>
            </div>
"""

            html += "        </div>\n"

        # Summary section
        html += """
        <div class="summary-box">
            <h2 style="margin-top:0;">Overall Summary</h2>
"""
        if output.summary.strengths:
            html += """
            <h3>✅ Strengths</h3>
            <ul>
"""
            for strength in output.summary.strengths:
                html += f"                <li>{strength}</li>\n"
            html += "            </ul>\n"

        if output.summary.biggest_gaps:
            html += """
            <h3>📈 Areas to Improve</h3>
            <ul>
"""
            for gap in output.summary.biggest_gaps:
                html += f"                <li>{gap}</li>\n"
            html += "            </ul>\n"

        if output.summary.missing_artifacts:
            html += """
            <h3>❗ Missing Elements</h3>
            <ul>
"""
            for missing in output.summary.missing_artifacts:
                html += f"                <li>{missing}</li>\n"
            html += "            </ul>\n"

        if output.summary.teacher_comment_draft:
            html += f"""
            <p><strong>Teacher's note:</strong> {output.summary.teacher_comment_draft}</p>
"""

        html += "        </div>\n"

        # Call to action
        html += f"""
        <p>You still have time to improve your work before the deadline of
        <strong>{deadline_str}</strong>.  Make the changes listed above,
        update your portfolio, and reach out if you have any questions.</p>
"""
        html += resubmit_section

        html += f"""
        <div class="footer">
            <p>This feedback was generated automatically by DPAssist.<br>
            If you have questions, please contact your teacher at
            <a href="mailto:{config.TEACHER_EMAIL}">{teacher_contact}</a>.</p>
        </div>
    </div>
</body>
</html>
"""
        return html
