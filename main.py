"""
PortfoliOS Main Orchestrator

This is the main program that coordinates all the specialized agents.
It runs continuously in the background, processing portfolio submissions.
"""

import os
import time
import logging
import signal
import sys
from typing import Dict, Any

from utils import (
    load_config,
    setup_logging,
    connect_to_google_sheets,
    autodetect_columns
)

from agent_submission_monitor import SubmissionMonitorAgent
from agent_timeliness import TimelinessAgent
from agent_link_validator import LinkValidatorAgent
from agent_media_checker import MediaCheckerAgent
from agent_caption_analyzer import CaptionAnalyzerAgent
from agent_feedback_generator import FeedbackGeneratorAgent
from agent_email_drafter import EmailDrafterAgent


class DPAssistOrchestrator:
    """
    Main orchestrator that coordinates all agents
    """
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        Initialize the orchestrator and all agents
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config_path = config_path
        self.config = load_config(self.config_path)

        
        # Setup logging
        self.logger = setup_logging(self.config)
        self.logger.info("=" * 70)
        self.logger.info("DPAssist Multi-Agent System Starting")
        self.logger.info("=" * 70)
        
        # Connect to Google Sheets
        self.client, self.worksheet = connect_to_google_sheets(self.config)
        
        # Auto-detect columns
        headers = self.worksheet.row_values(1)
        self.column_mapping = autodetect_columns(headers)
        self.logger.info(f"Column mapping: {self.column_mapping}")
        
        # Initialize all agents
        self.logger.info("Initializing agents...")
        
        self.submission_monitor = SubmissionMonitorAgent(self.config, self.logger)
        self.timeliness_agent = TimelinessAgent(self.config, self.logger)
        self.link_validator = LinkValidatorAgent(self.config, self.logger)
        self.media_checker = MediaCheckerAgent(self.config, self.logger)
        self.caption_analyzer = CaptionAnalyzerAgent(self.config, self.logger)
        self.feedback_generator = FeedbackGeneratorAgent(self.config, self.logger)
        self.email_drafter = EmailDrafterAgent(self.config, self.logger)
        
        self.logger.info("All agents initialized successfully")
        
        # Flag for graceful shutdown
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        import threading

        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

    
    def _signal_handler(self, signum, frame):
        """
        Handle shutdown signals gracefully
        """
        self.logger.info("Shutdown signal received. Finishing current task...")
        self.running = False
    def reload_config(self):
        try:
            self.config = load_config(self.config_path)

            # Debug: prove which config file and what deadline the worker loaded
            abs_path = os.path.abspath(self.config_path)
            deadline = self.config.get("project", {}).get("deadline") or self.config.get("deadline")
            self.logger.info(f"[CONFIG] loaded from {abs_path} | deadline={deadline}")

        except Exception as e:
            self.logger.error(f"Failed to reload config: {e}")


    
    def process_submission(self, submission: Dict[str, Any]) -> bool:
        """
        Process a single submission through all agents
        
        Args:
            submission: Submission dictionary
            
        Returns:
            True if processed successfully, False otherwise
        """
        student_name = f"{submission.get('First Name', '')} {submission.get('Last Name', '')}".strip()
        self.logger.info("=" * 70)
        self.logger.info(f"Processing submission for: {student_name}")
        self.logger.info("=" * 70)
        
        # Mark as processing
        self.submission_monitor.mark_submission_processing(submission)
        
        # Store results from each agent
        all_results = {}
        
        try:
            # STEP 1: Check timeliness
            self.logger.info("[1/6] Checking timeliness...")
            timeliness_result = self.timeliness_agent.process_submission(
                self.worksheet, submission, self.column_mapping
            )
            all_results['timeliness'] = timeliness_result
            
            # STEP 2: Validate link
            self.logger.info("[2/6] Validating portfolio link...")
            link_result = self.link_validator.process_submission(
                self.worksheet, submission, self.column_mapping
            )
            all_results['link_validation'] = link_result
            
            # If link is invalid, stop here and notify student
            if not link_result.get('success'):
                self.logger.warning("Link validation failed. Stopping processing.")
                
                # Send immediate notification to student about link issue
                error_feedback = {
                    'feedback': self._generate_link_error_feedback(link_result),
                    'feedback_type': 'student'
                }
                
                self.email_drafter.process_submission(
                    self.worksheet, submission, self.column_mapping, error_feedback
                )
                
                self.submission_monitor.mark_submission_error(
                    submission, 
                    f"Link Error: {link_result.get('status')}"
                )
                return False
            
            # STEP 3: Check media accessibility
            self.logger.info("[3/6] Checking media accessibility...")
            media_result = self.media_checker.process_submission(
                self.worksheet, submission, self.column_mapping,
                link_result.get('url', ''),
                link_result.get('screenshot')
            )
            all_results['media_check'] = media_result
            
            # If media check fails completely, warn but continue
            if not media_result.get('success'):
                self.logger.warning("Media check encountered errors, but continuing...")
            
            # STEP 4: Analyze captions with AI
            self.logger.info("[4/6] Analyzing captions with AI...")
            
            screenshot = media_result.get('screenshot') or link_result.get('screenshot')
            
            if screenshot:
                # Get rubric text if available
                rubric_text = self.feedback_generator.rubric_text or ""
                
                caption_result = self.caption_analyzer.process_submission(
                    self.worksheet, submission, self.column_mapping, screenshot, rubric_text
                )
                all_results['caption_analysis'] = caption_result
            else:
                self.logger.warning("No screenshot available for caption analysis")
                all_results['caption_analysis'] = {
                    'success': False,
                    'error': 'No screenshot available'
                }
            
            # STEP 5: Generate feedback
            self.logger.info("[5/6] Generating feedback with AI...")
            feedback_result = self.feedback_generator.process_submission(
                self.worksheet, submission, all_results
            )
            
            if not feedback_result.get('success'):
                self.logger.error("Feedback generation failed")
                self.submission_monitor.mark_submission_error(
                    submission,
                    "Feedback generation failed"
                )
                return False
            
            # STEP 6: Send email or create draft
            self.logger.info("[6/6] Processing email...")
            email_result = self.email_drafter.process_submission(
                self.worksheet, submission, self.column_mapping, feedback_result
            )
            
            if not email_result.get('success'):
                self.logger.error("Email processing failed")
                self.submission_monitor.mark_submission_error(
                    submission,
                    "Email failed to send"
                )
                return False
            
            # Mark as complete
            self.submission_monitor.mark_submission_complete(submission)
            
            self.logger.info(f"✓ Successfully processed submission for {student_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing submission: {e}", exc_info=True)
            self.submission_monitor.mark_submission_error(submission, str(e))
            return False
    
    def _generate_link_error_feedback(self, link_result: Dict[str, Any]) -> str:
        """
        Generate feedback message for link errors
        """
        status = link_result.get('status', 'Error')
        error = link_result.get('error', '')
        
        feedback_parts = [
            "Hello,",
            "",
            "I tried to access your portfolio submission but encountered an issue:",
            "",
            f"❌ {status}: {error}",
            "",
            "Please check the following:",
            "1. Make sure the URL is correct and complete",
            "2. If it's a Google Site, ensure sharing is set to 'Anyone with the link can view'",
            "3. Test the link yourself in an incognito/private browser window",
            "",
            "Once you've fixed the issue, please resubmit using the same form.",
            "",
            "Best regards"
        ]
        
        return "\n".join(feedback_parts)
    
    def run(self):
        """
        Main run loop - continuously monitors and processes submissions
        """
        self.logger.info("Starting main processing loop...")
        self.logger.info(f"Checking for submissions every {self.config['google_sheets'].get('check_interval', 300)} seconds")
        
        check_interval = self.config['google_sheets'].get('check_interval', 300)
        
        while self.running:
            # Reload config each cycle (allows Streamlit edits to apply)
            self.reload_config()

            # Refresh agents that depend on config (deadline, rubric)
            self.timeliness_agent = TimelinessAgent(self.config, self.logger)
            self.feedback_generator = FeedbackGeneratorAgent(self.config, self.logger)


            try:
                # Check for pending submissions
                pending = self.submission_monitor.get_pending_submissions()
                
                if pending:
                    self.logger.info(f"Found {len(pending)} pending submission(s)")
                    
                    # Process each submission
                    for submission in pending:
                        if not self.running:
                            break
                        
                        self.process_submission(submission)
                        
                        # Small delay between submissions
                        time.sleep(2)
                else:
                    self.logger.debug("No pending submissions")
                
                # Wait before next check
                if self.running:
                    time.sleep(check_interval)
                
            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt received")
                break
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}", exc_info=True)
                # Wait a bit before retrying
                time.sleep(60)
        
        self.logger.info("PortfoliOS shutting down gracefully")


def main():
    """
    Entry point for the application
    """
    try:
        print("=" * 70)
        print("PortfoliOS - Multi-Agent Portfolio Feedback System")
        print("=" * 70)
        print()
        print("Initializing...")
        
        orchestrator = DPAssistOrchestrator()

        
        print("✓ System initialized successfully")
        print()
        print("The system is now running continuously.")
        print("It will automatically process new submissions as they arrive.")
        print()
        print("Press Ctrl+C to stop.")
        print("=" * 70)
        print()
        
        orchestrator.run()
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print()
        print("Please create a config.yaml file using config.example.yaml as a template.")
        sys.exit(1)
        
    except ValueError as e:
        print(f"ERROR: {e}")
        print()
        print("Please check your config.yaml file and fill in all required fields.")
        sys.exit(1)
        
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
