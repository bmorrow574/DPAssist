"""
Email Drafter Agent

This agent handles email operations:
1. Sending feedback directly to students (before deadline)
2. Creating draft emails for teachers to review (after deadline)
3. Supporting multiple email providers (Gmail, Outlook, Generic SMTP)
"""

import logging
import smtplib
import imaplib
import email
from email.message import EmailMessage
from typing import Dict, Any, Optional
from datetime import datetime

from utils import (
    clean_email_address,
    validate_email,
    get_column_index,
    update_sheet_cell
)


class EmailDrafterAgent:
    """
    Handles email composition, sending, and draft creation
    """
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize the Email Drafter Agent
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        
        # Get email configuration
        email_config = config['email']
        self.provider = email_config['provider']
        self.teacher_email = clean_email_address(email_config['teacher_email'])
        
        # Get provider-specific settings
        if self.provider == 'gmail':
            self.password = email_config['gmail']['app_password']
            self.smtp_server = 'smtp.gmail.com'
            self.smtp_port = 587
            self.imap_server = 'imap.gmail.com'
            
        elif self.provider == 'outlook':
            self.password = email_config['outlook']['password']
            self.smtp_server = 'smtp-mail.outlook.com'
            self.smtp_port = 587
            self.imap_server = 'outlook.office365.com'
            
        elif self.provider == 'smtp':
            smtp_config = email_config['smtp']
            self.password = smtp_config['password']
            self.smtp_server = smtp_config['server']
            self.smtp_port = smtp_config['port']
            self.use_tls = smtp_config.get('use_tls', True)
            self.imap_server = None  # Generic SMTP may not have IMAP
            
        else:
            raise ValueError(f"Unknown email provider: {self.provider}")
        
        # Get email templates
        templates = email_config.get('templates', {})
        self.student_subject_template = templates.get('student_subject', 
                                                      'Feedback on Your Portfolio - {student_name}')
        self.teacher_subject_template = templates.get('teacher_subject',
                                                      'Portfolio Grading: {student_name} - {unit}')
    
    def send_student_email(self, student_email: str, student_name: str, 
                          feedback: str, submission: Dict[str, Any]) -> bool:
        """
        Send feedback email directly to student
        
        Args:
            student_email: Student's email address
            student_name: Student's name
            feedback: Feedback text to send
            submission: Submission dictionary
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Validate email
            if not validate_email(student_email):
                self.logger.error(f"Invalid student email: {student_email}")
                return False
            
            # Create email message
            msg = EmailMessage()
            msg['From'] = self.teacher_email
            msg['To'] = student_email
            msg['Subject'] = self.student_subject_template.format(student_name=student_name)
            
            # Build email body
            body = self._build_student_email_body(student_name, feedback, submission)
            msg.set_content(body)
            
            # Send email
            self.logger.info(f"Sending email to {student_email}...")
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if hasattr(self, 'use_tls') and self.use_tls:
                    server.starttls()
                else:
                    server.starttls()  # Default to TLS
                
                server.login(self.teacher_email, self.password)
                server.send_message(msg)
            
            self.logger.info(f"Email sent successfully to {student_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email to {student_email}: {e}", exc_info=True)
            return False
    
    def create_teacher_draft(self, student_email: str, student_name: str, 
                            feedback: str, submission: Dict[str, Any]) -> bool:
        """
        Create a draft email in teacher's account for review
        
        Args:
            student_email: Student's email address
            student_name: Student's name
            feedback: Feedback text
            submission: Submission dictionary
            
        Returns:
            True if draft created successfully, False otherwise
        """
        if self.provider == 'gmail':
            return self._create_gmail_draft(student_email, student_name, feedback, submission)
        
        elif self.provider == 'outlook':
            return self._create_outlook_draft(student_email, student_name, feedback, submission)
        
        else:
            # For generic SMTP, we can't create drafts directly
            # Instead, we'll save to a local file
            self.logger.warning("Draft creation not supported for generic SMTP. Saving to file.")
            return self._save_draft_to_file(student_email, student_name, feedback, submission)
    
    def _create_gmail_draft(self, student_email: str, student_name: str, 
                           feedback: str, submission: Dict[str, Any]) -> bool:
        """
        Create a draft in Gmail using IMAP
        """
        try:
            # Create email message
            msg = EmailMessage()
            msg['From'] = self.teacher_email
            msg['To'] = student_email
            
            unit = submission.get('Unit', 'Portfolio')
            msg['Subject'] = self.teacher_subject_template.format(
                student_name=student_name, 
                unit=unit
            )
            
            # Build email body
            body = self._build_teacher_email_body(student_name, feedback, submission)
            msg.set_content(body)
            
            # Connect to Gmail via IMAP
            self.logger.info("Connecting to Gmail IMAP to create draft...")
            
            with imaplib.IMAP4_SSL(self.imap_server) as imap:
                imap.login(self.teacher_email, self.password)
                
                # Gmail uses [Gmail]/Drafts folder
                imap.select('[Gmail]/Drafts')
                
                # Append message to Drafts folder
                imap.append(
                    '[Gmail]/Drafts',
                    '',
                    imaplib.Time2Internaldate(datetime.now()),
                    msg.as_bytes()
                )
            
            self.logger.info(f"Draft created successfully for {student_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating Gmail draft: {e}", exc_info=True)
            return False
    
    def _create_outlook_draft(self, student_email: str, student_name: str, 
                             feedback: str, submission: Dict[str, Any]) -> bool:
        """
        Create a draft in Outlook using IMAP
        """
        try:
            # Create email message
            msg = EmailMessage()
            msg['From'] = self.teacher_email
            msg['To'] = student_email
            
            unit = submission.get('Unit', 'Portfolio')
            msg['Subject'] = self.teacher_subject_template.format(
                student_name=student_name,
                unit=unit
            )
            
            # Build email body
            body = self._build_teacher_email_body(student_name, feedback, submission)
            msg.set_content(body)
            
            # Connect to Outlook via IMAP
            self.logger.info("Connecting to Outlook IMAP to create draft...")
            
            with imaplib.IMAP4_SSL(self.imap_server) as imap:
                imap.login(self.teacher_email, self.password)
                
                # Outlook uses Drafts folder
                imap.select('Drafts')
                
                # Append message to Drafts folder
                imap.append(
                    'Drafts',
                    '',
                    imaplib.Time2Internaldate(datetime.now()),
                    msg.as_bytes()
                )
            
            self.logger.info(f"Draft created successfully for {student_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating Outlook draft: {e}", exc_info=True)
            return False
    
    def _save_draft_to_file(self, student_email: str, student_name: str, 
                           feedback: str, submission: Dict[str, Any]) -> bool:
        """
        Save draft to a local file (fallback for generic SMTP)
        """
        try:
            from pathlib import Path
            
            drafts_dir = Path('email_drafts')
            drafts_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = drafts_dir / f"draft_{student_name}_{timestamp}.txt"
            
            unit = submission.get('Unit', 'Portfolio')
            subject = self.teacher_subject_template.format(
                student_name=student_name,
                unit=unit
            )
            
            body = self._build_teacher_email_body(student_name, feedback, submission)
            
            draft_content = f"""To: {student_email}
From: {self.teacher_email}
Subject: {subject}

{body}
"""
            
            with open(filename, 'w') as f:
                f.write(draft_content)
            
            self.logger.info(f"Draft saved to file: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving draft to file: {e}", exc_info=True)
            return False
    
    def _build_student_email_body(self, student_name: str, feedback: str, 
                                  submission: Dict[str, Any]) -> str:
        """
        Build the email body for student feedback
        """
        body_parts = [
            f"Hello {student_name},",
            "",
            "Thank you for submitting your portfolio. Here is feedback on your current submission:",
            "",
            "=" * 60,
            feedback,
            "=" * 60,
            "",
            "You can resubmit your portfolio before the deadline. Each resubmission will be evaluated automatically.",
            "",
            "If you have questions, please reply to this email.",
            "",
            "Best regards,",
            self.teacher_email
        ]
        
        return "\n".join(body_parts)
    
    def _build_teacher_email_body(self, student_name: str, feedback: str, 
                                  submission: Dict[str, Any]) -> str:
        """
        Build the email body for teacher draft
        """
        body_parts = [
            f"Dear {student_name},",
            "",
            feedback,
            "",
            "Please let me know if you have any questions.",
            "",
            "Best regards"
        ]
        
        return "\n".join(body_parts)
    
    def update_sheet_email_status(self, worksheet, submission: Dict[str, Any], 
                                  sent: bool, is_draft: bool):
        """
        Update the email status in the Google Sheet
        
        Args:
            worksheet: Google Sheets worksheet object
            submission: Submission dictionary with _row_index
            sent: Whether email was sent successfully
            is_draft: Whether this was a draft (vs direct send)
        """
        row = submission['_row_index']
        feedback_sent_col = get_column_index(worksheet, 'Feedback Sent')
        
        if sent:
            if is_draft:
                status_text = f"Draft created {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            else:
                status_text = f"Sent {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        else:
            status_text = "Failed to send"
        
        if feedback_sent_col:
            update_sheet_cell(worksheet, row, feedback_sent_col, status_text)
            self.logger.info(f"Updated email status for row {row}: {status_text}")
    
    def process_submission(self, worksheet, submission: Dict[str, Any], 
                          column_mapping: Dict[str, str], 
                          feedback_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process email sending/drafting for a submission
        
        Args:
            worksheet: Google Sheets worksheet object
            submission: Submission dictionary
            column_mapping: Column name mapping
            feedback_result: Result from FeedbackGeneratorAgent
            
        Returns:
            Result dictionary
        """
        try:
            # Get student info
            email_col = column_mapping.get('email', 'Email')
            first_name_col = column_mapping.get('first_name', 'First Name')
            last_name_col = column_mapping.get('last_name', 'Last Name')
            
            student_email = clean_email_address(submission.get(email_col, ''))
            student_name = f"{submission.get(first_name_col, '')} {submission.get(last_name_col, '')}".strip()
            
            if not student_email:
                self.logger.error("No student email found")
                return {'success': False, 'error': 'No student email'}
            
            feedback = feedback_result.get('feedback', '')
            feedback_type = feedback_result.get('feedback_type', 'student')
            
            # Decide whether to send or create draft
            if feedback_type == 'student':
                # Send directly to student
                success = self.send_student_email(student_email, student_name, feedback, submission)
                is_draft = False
            else:
                # Create draft for teacher
                success = self.create_teacher_draft(student_email, student_name, feedback, submission)
                is_draft = True
            
            # Update sheet
            self.update_sheet_email_status(worksheet, submission, success, is_draft)
            
            return {
                'success': success,
                'is_draft': is_draft,
                'recipient': student_email
            }
            
        except Exception as e:
            self.logger.error(f"Error processing email: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }


def main():
    """
    Standalone entry point for testing the Email Drafter Agent
    """
    from utils import load_config, setup_logging
    
    config = load_config()
    logger = setup_logging(config)
    
    agent = EmailDrafterAgent(config, logger)
    
    print(f"Email Drafter Agent initialized")
    print(f"Provider: {agent.provider}")
    print(f"Teacher email: {agent.teacher_email}")
    print(f"SMTP server: {agent.smtp_server}:{agent.smtp_port}")


if __name__ == '__main__':
    main()
