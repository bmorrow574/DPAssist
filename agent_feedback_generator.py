"""
Feedback Generator Agent

This agent creates personalized feedback for students based on all the analysis results.
It operates in two modes:
1. BEFORE deadline: Sends feedback directly to students (allows resubmissions)
2. AFTER deadline: Creates draft feedback for teachers to review
"""

import logging
from typing import Dict, Any
from datetime import datetime

from utils import (
    initialize_gemini,
    get_gemini_model,
    parse_deadline,
    get_column_index,
    update_sheet_cell
)


class FeedbackGeneratorAgent:
    """
    Generates personalized portfolio feedback using AI
    """
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize the Feedback Generator Agent
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        
        # Initialize Gemini
        initialize_gemini(config)
        self.model = get_gemini_model(config)
        
        # Get deadline
        self.deadline = parse_deadline(config)
        
        # Get agent-specific settings
        agent_config = config['agents']['feedback_generator']
        self.send_student_feedback = agent_config.get('send_student_feedback', True)
        self.create_teacher_drafts = agent_config.get('create_teacher_drafts', True)
        self.max_feedback_words = agent_config.get('max_feedback_words', 500)
        
        # Load rubric if available
        self.rubric_text = self._load_rubric()
    
    def _load_rubric(self) -> str:
        """
        Load rubric from config
        
        Returns:
            Rubric text or empty string
        """
        rubric_config = self.config.get('rubric', {})
        
        # Check for file path first
        file_path = rubric_config.get('file_path', '')
        if file_path:
            try:
                from pathlib import Path
                rubric_file = Path(file_path)
                
                if rubric_file.exists():
                    if file_path.lower().endswith('.pdf'):
                        from PyPDF2 import PdfReader
                        reader = PdfReader(rubric_file)
                        text = '\n'.join(page.extract_text() for page in reader.pages)
                        return text
                    
                    elif file_path.lower().endswith('.docx'):
                        from docx import Document
                        doc = Document(rubric_file)
                        return '\n'.join(p.text for p in doc.paragraphs)
                    
                    else:
                        with open(rubric_file, 'r') as f:
                            return f.read()
                            
            except Exception as e:
                self.logger.warning(f"Could not load rubric file: {e}")
        
        # Fall back to text in config
        return rubric_config.get('text', '')
    
    def is_past_deadline(self) -> bool:
        """
        Check if current time is past the deadline
        
        Returns:
            True if past deadline, False otherwise
        """
        return datetime.now() > self.deadline
    
    def generate_student_feedback(self, submission: Dict[str, Any], 
                                  all_results: Dict[str, Any]) -> str:
        """
        Generate feedback to send directly to student (before deadline)
        
        Args:
            submission: Submission dictionary
            all_results: Combined results from all agents
            
        Returns:
            Feedback text for student
        """
        prompt = self._build_student_feedback_prompt(submission, all_results)
        
        try:
            self.logger.info("Generating student feedback with Gemini...")
            response = self.model.generate_content(prompt)
            feedback = response.text.strip()
            
            return feedback
            
        except Exception as e:
            self.logger.error(f"Error generating student feedback: {e}", exc_info=True)
            return self._fallback_student_feedback(submission, all_results)
    
    def generate_teacher_feedback(self, submission: Dict[str, Any], 
                                  all_results: Dict[str, Any]) -> str:
        """
        Generate comprehensive feedback for teacher (after deadline)
        
        Args:
            submission: Submission dictionary
            all_results: Combined results from all agents
            
        Returns:
            Feedback text for teacher to review
        """
        prompt = self._build_teacher_feedback_prompt(submission, all_results)
        
        try:
            self.logger.info("Generating teacher feedback with Gemini...")
            response = self.model.generate_content(prompt)
            feedback = response.text.strip()
            
            return feedback
            
        except Exception as e:
            self.logger.error(f"Error generating teacher feedback: {e}", exc_info=True)
            return self._fallback_teacher_feedback(submission, all_results)
    
    def _build_student_feedback_prompt(self, submission: Dict[str, Any], 
                                      all_results: Dict[str, Any]) -> str:
        """
        Build prompt for student feedback generation
        """
        timeliness = all_results.get('timeliness', {})
        link_validation = all_results.get('link_validation', {})
        media_check = all_results.get('media_check', {})
        caption_analysis = all_results.get('caption_analysis', {})
        
        prompt = f"""You are a supportive teacher providing feedback on a student's digital portfolio.

STUDENT INFORMATION:
- Name: {submission.get('First Name', '')} {submission.get('Last Name', '')}
- Submission: {submission.get('Portfolio Link', 'N/A')}

EVALUATION RESULTS:

1. TIMELINESS:
{f"✓ Submitted on time" if not timeliness.get('is_late') else f"✗ Late by {timeliness.get('late_message', 'unknown')}"}

2. LINK ACCESSIBILITY:
{f"✓ Link works correctly" if link_validation.get('success') else f"✗ {link_validation.get('status', 'Error')}: {link_validation.get('error', '')}"}

3. MEDIA ACCESSIBILITY:
{f"✓ All media loads correctly ({media_check.get('accessible_count', 0)} items)" if not media_check.get('has_issues') else f"✗ {media_check.get('broken_count', 0)} media items are broken"}

4. CAPTION QUALITY:
Score: {caption_analysis.get('overall_score', 0)}/100
{f"Issues: {caption_analysis.get('missing_captions', 0)} missing, {caption_analysis.get('poor_captions', 0)} poor quality" if caption_analysis.get('has_issues') else "✓ Good caption quality"}

YOUR TASK:
Write concise, encouraging feedback in BULLET POINT format (maximum {self.max_feedback_words} words):

**What You Did Well:**
- [List 1-2 specific strengths as bullets]

**What Needs Improvement:**
- [List specific issues as bullets]

**Next Steps:**
- [List 1-3 action items as bullets]

Remember: You can resubmit before the deadline!

IMPORTANT: Use bullet points (•) for all feedback items. Keep each bullet to one clear sentence.

Remember: This is formative feedback to help them improve, not a final grade."""

        if self.rubric_text:
            prompt += f"\n\nRUBRIC FOR REFERENCE:\n{self.rubric_text}\n"
        
        return prompt
    
    def _build_teacher_feedback_prompt(self, submission: Dict[str, Any], 
                                      all_results: Dict[str, Any]) -> str:
        """
        Build prompt for teacher feedback generation (final grading)
        """
        timeliness = all_results.get('timeliness', {})
        link_validation = all_results.get('link_validation', {})
        media_check = all_results.get('media_check', {})
        caption_analysis = all_results.get('caption_analysis', {})
        
        prompt = f"""You are assisting a teacher with grading a student's digital portfolio. Generate comprehensive feedback for the teacher to review before sending.

STUDENT INFORMATION:
- Name: {submission.get('First Name', '')} {submission.get('Last Name', '')}
- Email: {submission.get('Email', '')}
- Unit/Project: {submission.get('Unit', 'N/A')}
- Submission: {submission.get('Portfolio Link', 'N/A')}

EVALUATION RESULTS:

1. TIMELINESS:
Status: {timeliness.get('late_message', 'On time') if timeliness.get('is_late') else 'On time'}

2. LINK ACCESSIBILITY:
Status: {link_validation.get('status', 'Unknown')}
{f"Issue: {link_validation.get('error', '')}" if not link_validation.get('success') else ""}

3. MEDIA ACCESSIBILITY:
Total Media: {media_check.get('accessible_count', 0)} accessible, {media_check.get('broken_count', 0)} broken

4. CAPTION QUALITY:
Overall Score: {caption_analysis.get('overall_score', 0)}/100
Media Count: {caption_analysis.get('media_count', 0)}
Missing Captions: {caption_analysis.get('missing_captions', 0)}
Poor Quality Captions: {caption_analysis.get('poor_captions', 0)}
Irrelevant Media: {caption_analysis.get('irrelevant_media', 0)}

AI Assessment: {caption_analysis.get('feedback', 'No feedback available')}

{"RUBRIC:" if self.rubric_text else ""}
{self.rubric_text if self.rubric_text else ""}

YOUR TASK:
Generate professional feedback (maximum {self.max_feedback_words} words) that:
1. Summarizes the portfolio's strengths and weaknesses
2. Evaluates against the rubric (if provided)
3. Notes any technical issues (link, media, captions)
4. Provides a clear assessment of the work quality
5. Suggests areas for growth

Format the feedback as a professional email the teacher can review and send."""
        
        return prompt
    
    def _fallback_student_feedback(self, submission: Dict[str, Any], 
                                   all_results: Dict[str, Any]) -> str:
        """
        Generate basic feedback if AI fails
        """
        feedback_parts = [
            f"Hello {submission.get('First Name', 'Student')},",
            "",
            "Here is automated feedback on your portfolio submission:",
            ""
        ]
        
        timeliness = all_results.get('timeliness', {})
        if timeliness.get('is_late'):
            feedback_parts.append(f"⚠ Your submission was late by {timeliness.get('late_message', 'unknown time')}.")
        
        link_validation = all_results.get('link_validation', {})
        if not link_validation.get('success'):
            feedback_parts.append(f"⚠ Link Issue: {link_validation.get('error', 'Could not access your portfolio')}.")
        
        media_check = all_results.get('media_check', {})
        if media_check.get('has_issues'):
            feedback_parts.append(f"⚠ {media_check.get('broken_count', 0)} media items failed to load properly.")
        
        caption_analysis = all_results.get('caption_analysis', {})
        if caption_analysis.get('has_issues'):
            feedback_parts.append(f"⚠ Caption issues detected: {caption_analysis.get('feedback', 'Check your media captions')}.")
        
        feedback_parts.extend([
            "",
            "Please address these issues and resubmit before the deadline.",
            "",
            "Best regards,",
            "Your Teacher"
        ])
        
        return "\n".join(feedback_parts)
    
    def _fallback_teacher_feedback(self, submission: Dict[str, Any], 
                                   all_results: Dict[str, Any]) -> str:
        """
        Generate basic teacher feedback if AI fails
        """
        feedback_parts = [
            f"Portfolio Evaluation for {submission.get('First Name', '')} {submission.get('Last Name', '')}",
            "",
            "Technical Assessment:"
        ]
        
        timeliness = all_results.get('timeliness', {})
        feedback_parts.append(f"- Timeliness: {timeliness.get('late_message', 'On time')}")
        
        link_validation = all_results.get('link_validation', {})
        feedback_parts.append(f"- Link Status: {link_validation.get('status', 'Unknown')}")
        
        media_check = all_results.get('media_check', {})
        feedback_parts.append(f"- Media: {media_check.get('accessible_count', 0)} accessible, {media_check.get('broken_count', 0)} broken")
        
        caption_analysis = all_results.get('caption_analysis', {})
        feedback_parts.append(f"- Caption Score: {caption_analysis.get('overall_score', 0)}/100")
        
        return "\n".join(feedback_parts)
    
    def process_submission(self, worksheet, submission: Dict[str, Any], 
                          all_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate appropriate feedback based on deadline
        
        Args:
            worksheet: Google Sheets worksheet object
            submission: Submission dictionary
            all_results: Combined results from all agents
            
        Returns:
            Result dictionary with feedback
        """
        try:
            past_deadline = self.is_past_deadline()
            
            if past_deadline:
                # Generate teacher feedback
                self.logger.info("Deadline passed - generating teacher feedback")
                feedback = self.generate_teacher_feedback(submission, all_results)
                feedback_type = 'teacher'
            else:
                # Generate student feedback
                self.logger.info("Before deadline - generating student feedback")
                feedback = self.generate_student_feedback(submission, all_results)
                feedback_type = 'student'
            
            return {
                'success': True,
                'feedback': feedback,
                'feedback_type': feedback_type,
                'past_deadline': past_deadline
            }
            
        except Exception as e:
            self.logger.error(f"Error generating feedback: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }


def main():
    """
    Standalone entry point for testing the Feedback Generator Agent
    """
    from utils import load_config, setup_logging
    
    config = load_config()
    logger = setup_logging(config)
    
    agent = FeedbackGeneratorAgent(config, logger)
    
    print(f"Feedback Generator Agent initialized")
    print(f"Deadline: {agent.deadline}")
    print(f"Past deadline: {agent.is_past_deadline()}")
    print(f"Rubric loaded: {len(agent.rubric_text) > 0}")


if __name__ == '__main__':
    main()
