"""
Background service - runs every 60 seconds to process submissions
"""
import sys
from pathlib import Path

# Add parent directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

import time
import json
from datetime import datetime
from typing import Dict, Set
import traceback

from config import config
from google_sheets import GoogleSheetsClient
from scraper import PortfolioScraper
from evaluator import PortfolioEvaluator
from gmail_drafts import GmailDraftCreator
from rubric_manager import RubricManager
from orchestrator.pipeline import build_and_validate_run
from schemas.run import RunMode


class ProcessingState:
    """Track which submissions have been processed"""
    
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.processed_submissions: Set[str] = set()
        self._load()
    
    def _load(self):
        """Load processing state from file"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                data = json.load(f)
                self.processed_submissions = set(data.get('processed', []))
    
    def _save(self):
        """Save processing state to file"""
        data = {
            'processed': list(self.processed_submissions),
            'last_updated': datetime.now().isoformat()
        }
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def mark_processed(self, submission_key: str):
        """Mark a submission as processed"""
        self.processed_submissions.add(submission_key)
        self._save()
    
    def is_processed(self, submission_key: str) -> bool:
        """Check if submission has been processed"""
        return submission_key in self.processed_submissions


class BackgroundService:
    """Main background service that processes submissions"""
    
    def __init__(self):
        self.sheets_client = GoogleSheetsClient()
        self.scraper = PortfolioScraper()
        self.evaluator = PortfolioEvaluator()
        self.gmail = GmailDraftCreator()
        self.rubric_manager = RubricManager()
        self.state = ProcessingState(config.STATE_FILE)
        
        self.running = False
    
    def start(self):
        """Start the background service loop"""
        print("=" * 60)
        print("PORTFOLIO REVIEWER - Background Service")
        print("=" * 60)
        print(f"Checking every {config.CHECK_INTERVAL_SECONDS} seconds")
        print(f"Google Sheet: {config.GOOGLE_SHEET_ID}")
        print(f"Teacher Email: {config.TEACHER_EMAIL}")
        print("=" * 60)
        
        self.running = True
        
        try:
            while self.running:
                self._process_cycle()
                time.sleep(config.CHECK_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\nShutting down gracefully...")
            self.running = False
    
    def stop(self):
        """Stop the background service"""
        self.running = False
    
    def _process_cycle(self):
        """Process one cycle - check for new submissions and evaluate"""
        try:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking for new submissions...")
            
            # Get all submissions
            submissions = self.sheets_client.get_all_submissions()
            
            if not submissions:
                print("No submissions found.")
                return
            
            new_count = 0
            
            for idx, record in enumerate(submissions, start=2):  # Row 2 is first data row
                # Parse submission
                parsed = GoogleSheetsClient.parse_submission(record)
                
                if not parsed:
                    continue
                
                # Create unique key for this submission
                submission_key = f"{parsed.get('email', 'unknown')}_{parsed.get('unit', 'unknown')}_{parsed.get('timestamp', '')}"
                
                # Skip if already processed
                if self.state.is_processed(submission_key):
                    continue
                
                new_count += 1
                print(f"\nProcessing new submission from {parsed.get('student_name', 'Unknown')}")
                print(f"  Unit: {parsed.get('unit', 'Unknown')}")
                print(f"  URL: {parsed.get('portfolio_url', 'Unknown')}")
                
                # Process this submission
                success = self._process_submission(parsed, idx)
                
                if success:
                    self.state.mark_processed(submission_key)
                    print(f"  ✓ Successfully processed")
                else:
                    print(f"  ✗ Processing failed")
            
            if new_count == 0:
                print("No new submissions to process.")
            else:
                print(f"\nProcessed {new_count} new submission(s)")
            
        except Exception as e:
            print(f"Error in processing cycle: {e}")
            traceback.print_exc()
    
    def _process_submission(self, submission: Dict, row_number: int) -> bool:
        """
        Process a single submission
        
        Args:
            submission: Parsed submission dict
            row_number: Row number in Google Sheet
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get unit and rubric
            unit = submission.get('unit', '')
            rubric = self.rubric_manager.get_rubric_for_unit(unit)
            
            if not rubric:
                print(f"  ! No rubric configured for unit: {unit}")
                self.sheets_client.update_status(row_number, "No rubric configured")
                return False
            
            # Check if past due
            is_past_due = self.rubric_manager.is_past_due(unit)
            
            # Update status to "Processing"
            self.sheets_client.update_status(row_number, "Processing")
            
            # Scrape portfolio
            portfolio_url = submission.get('portfolio_url', '')
            print(f"  Scraping portfolio...")
            portfolio_content = self.scraper.scrape(portfolio_url)
            
            if not portfolio_content:
                print(f"  ! Failed to scrape portfolio")
                self.sheets_client.update_status(row_number, "Scraping failed")
                return False
            
            print(f"  Scraped {len(portfolio_content.get('text', ''))} characters")
            
            # Evaluate with AI
            print(f"  Evaluating with AI (scores: {is_past_due})...")
            evaluation = self.evaluator.evaluate(
                portfolio_content=portfolio_content,
                rubric=rubric,
                include_scores=is_past_due
            )
            
            if not evaluation or not evaluation.get('results'):
                print(f"  ! Evaluation failed")
                self.sheets_client.update_status(row_number, "Evaluation failed")
                return False
            
            # Build and validate run output
            run_id = f"run_{submission.get('email', 'unknown')}_{unit}_{int(time.time())}"
            
            output = build_and_validate_run(
                run_id=run_id,
                rubric_version=rubric,
                artifact_set_id=f"portfolio_{int(time.time())}",
                results=evaluation['results'],
                summary=evaluation['summary'],
                inputs_hash=run_id,
                rubric_fingerprint=rubric.fingerprint(),
                artifact_fingerprint="portfolio_content",
                model_id="gemini-1.5-pro",
                strictness_profile="portfolios_strict_v1"
            )
            
            print(f"  Validation passed")
            
            # Send feedback or create draft
            if is_past_due:
                # Create Gmail draft with scores
                print(f"  Creating scored draft email...")
                success = self.gmail.create_feedback_draft(
                    student_email=submission.get('email', ''),
                    student_name=submission.get('student_name', 'Student'),
                    rubric_title=rubric.title,
                    output=output
                )
                
                if success:
                    self.sheets_client.update_status(row_number, "Draft created")
                    self.sheets_client.update_feedback_sent(row_number, datetime.now().isoformat())
                else:
                    print(f"  ! Failed to create draft")
                    self.sheets_client.update_status(row_number, "Draft failed")
                    return False
            else:
                # Send feedback without scores (TODO: implement email sending)
                print(f"  Would send feedback (no scores) - not yet implemented")
                self.sheets_client.update_status(row_number, "Feedback pending")
            
            # Update last processed timestamp
            self.sheets_client.update_last_processed(row_number, datetime.now().isoformat())
            
            return True
            
        except Exception as e:
            print(f"  ! Error processing submission: {e}")
            traceback.print_exc()
            
            try:
                self.sheets_client.update_status(row_number, f"Error: {str(e)[:50]}")
            except:
                pass
            
            return False


def main():
    """Main entry point for background service"""
    # Validate config
    errors = config.validate()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease check your .env file")
        return
    
    # Setup directories
    config.setup_directories()
    
    # Start service
    service = BackgroundService()
    service.start()


if __name__ == '__main__':
    main()
