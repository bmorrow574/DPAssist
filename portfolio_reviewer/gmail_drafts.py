"""
Gmail integration for creating draft emails with scored feedback
Uses IMAP (like agent.py) - works with App Password, no admin needed
"""
import sys
from pathlib import Path

# Add parent directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

import imaplib
import time
from email.message import EmailMessage
from typing import Dict, List
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
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Create draft
            draft = {
                'message': {
                    'raw': raw_message
                }
            }
            
            draft = self.service.users().drafts().create(
                userId='me',
                body=draft
            ).execute()
            
            print(f"Draft created for {student_name} ({student_email})")
            return True
            
        except Exception as e:
            print(f"Error creating draft: {e}")
            return False
    
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
