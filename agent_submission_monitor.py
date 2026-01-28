"""
Submission Monitor Agent

This agent continuously watches the Google Sheet for new or updated portfolio submissions.
It runs in the background and triggers the other agents when work is needed.
"""

import time
import logging
from typing import Set, Dict, Any
from datetime import datetime

from utils import (
    load_config,
    connect_to_google_sheets,
    get_all_submissions,
    get_column_index,
    update_sheet_cell,
    autodetect_columns,
    setup_logging
)


class SubmissionMonitorAgent:
    """
    Monitors Google Sheet for new portfolio submissions and tracks processing status
    """
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize the Submission Monitor Agent
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.processed_submissions: Set[str] = set()
        
        # Connect to Google Sheets
        self.client, self.worksheet = connect_to_google_sheets(config)
        self.logger.info("Connected to Google Sheets")
        
        # Auto-detect columns
        headers = self.worksheet.row_values(1)
        self.column_mapping = autodetect_columns(headers)
        self.logger.info(f"Auto-detected columns: {self.column_mapping}")
        
        # Add status columns if they don't exist
        self._ensure_status_columns()
    
    def _ensure_status_columns(self):
        """
        Ensure all required status columns exist in the sheet
        """
        required_columns = [
            'Status',
            'Timeliness',
            'Link Status',
            'Media Status',
            'Caption Status',
            'Feedback Sent',
            'Last Processed',
        ]
        
        headers = self.worksheet.row_values(1)
        
        for col_name in required_columns:
            if col_name not in headers:
                # Add column to the end
                next_col = len(headers) + 1
                self.worksheet.update_cell(1, next_col, col_name)
                headers.append(col_name)
                self.logger.info(f"Added missing column: {col_name}")
    
    def get_pending_submissions(self) -> list:
        """
        Get list of submissions that need processing
        
        Returns:
            List of submission dictionaries that need processing
        """
        all_submissions = get_all_submissions(self.worksheet)
        
        pending = []
        
        for i, submission in enumerate(all_submissions):
            # Skip if already processed recently
            submission_id = self._generate_submission_id(submission)
            
            if submission_id in self.processed_submissions:
                continue
            
            # Check if submission needs processing
            status = submission.get('Status', '')
            
            # Process if:
            # 1. No status set yet (new submission)
            # 2. Status is "Error" (retry)
            # 3. Status is "Pending" (in queue)
            # 4. Submission was updated (timestamp changed)
            
            if not status or status in ['', 'Pending', 'Error', 'Resubmitted']:
                submission['_row_index'] = i + 2  # +2 because sheet is 1-indexed and has header
                pending.append(submission)
        
        return pending
    
    def _generate_submission_id(self, submission: Dict[str, Any]) -> str:
        """
        Generate a unique ID for a submission
        
        Args:
            submission: Submission dictionary
            
        Returns:
            Unique identifier string
        """
        email = submission.get(self.column_mapping.get('email', 'Email'), '')
        timestamp = submission.get(self.column_mapping.get('timestamp', 'Timestamp'), '')
        portfolio_link = submission.get(self.column_mapping.get('portfolio_link', 'Portfolio Link'), '')
        
        return f"{email}|{timestamp}|{portfolio_link}"
    
    def mark_submission_pending(self, submission: Dict[str, Any]):
        """
        Mark a submission as pending in the sheet
        
        Args:
            submission: Submission dictionary with _row_index
        """
        row = submission['_row_index']
        status_col = get_column_index(self.worksheet, 'Status')
        
        if status_col:
            update_sheet_cell(self.worksheet, row, status_col, 'Pending')
    
    def mark_submission_processing(self, submission: Dict[str, Any]):
        """
        Mark a submission as currently being processed
        
        Args:
            submission: Submission dictionary with _row_index
        """
        row = submission['_row_index']
        status_col = get_column_index(self.worksheet, 'Status')
        
        if status_col:
            update_sheet_cell(self.worksheet, row, status_col, 'Processing')
        
        # Update last processed time
        last_processed_col = get_column_index(self.worksheet, 'Last Processed')
        if last_processed_col:
            update_sheet_cell(
                self.worksheet, 
                row, 
                last_processed_col, 
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
    
    def mark_submission_complete(self, submission: Dict[str, Any]):
        """
        Mark a submission as completed
        
        Args:
            submission: Submission dictionary with _row_index
        """
        row = submission['_row_index']
        status_col = get_column_index(self.worksheet, 'Status')
        
        if status_col:
            update_sheet_cell(self.worksheet, row, status_col, 'Complete')
        
        # Add to processed set
        submission_id = self._generate_submission_id(submission)
        self.processed_submissions.add(submission_id)
    
    def mark_submission_error(self, submission: Dict[str, Any], error_msg: str):
        """
        Mark a submission as having an error
        
        Args:
            submission: Submission dictionary with _row_index
            error_msg: Error message to log
        """
        row = submission['_row_index']
        status_col = get_column_index(self.worksheet, 'Status')
        
        if status_col:
            update_sheet_cell(self.worksheet, row, status_col, f'Error: {error_msg}')
        
        self.logger.error(f"Submission error for row {row}: {error_msg}")
    
    def run_monitoring_loop(self, check_interval: int = None):
        """
        Main monitoring loop that runs continuously
        
        Args:
            check_interval: How many seconds between checks (default from config)
        """
        if check_interval is None:
            check_interval = self.config['google_sheets'].get('check_interval', 300)
        
        self.logger.info(f"Starting monitoring loop (checking every {check_interval} seconds)")
        
        while True:
            try:
                # Get pending submissions
                pending = self.get_pending_submissions()
                
                if pending:
                    self.logger.info(f"Found {len(pending)} pending submissions")
                    
                    # Return the pending submissions for processing
                    # The main orchestrator will handle them
                    return pending
                else:
                    self.logger.debug("No pending submissions found")
                
                # Wait before next check
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                self.logger.info("Monitoring stopped by user")
                break
            
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                # Wait a bit before retrying to avoid rapid error loops
                time.sleep(60)


def main():
    """
    Standalone entry point for testing the Submission Monitor Agent
    """
    config = load_config()
    logger = setup_logging(config)
    
    agent = SubmissionMonitorAgent(config, logger)
    
    # Run monitoring loop
    agent.run_monitoring_loop()


if __name__ == '__main__':
    main()
