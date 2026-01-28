"""
Timeliness Agent

This agent checks whether a portfolio submission was submitted on time or late.
It compares the submission timestamp against the configured deadline.
"""

import logging
from typing import Dict, Any, Tuple
from datetime import datetime

from utils import (
    parse_deadline,
    is_submission_late,
    get_column_index,
    update_sheet_cell
)


class TimelinessAgent:
    """
    Checks submission timeliness against deadline
    """
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize the Timeliness Agent
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        
        # Parse the deadline from config
        self.deadline = parse_deadline(config)
        self.logger.info(f"Deadline set to: {self.deadline}")
    
    def check_timeliness(self, submission: Dict[str, Any], column_mapping: Dict[str, str]) -> Tuple[bool, str]:
        """
        Check if a submission is late
        
        Args:
            submission: Submission dictionary
            column_mapping: Mapping of standard names to actual column names
            
        Returns:
            Tuple of (is_late: bool, status_message: str)
        """
        timestamp_col = column_mapping.get('timestamp', 'Timestamp')
        submission_time = submission.get(timestamp_col, '')
        
        if not submission_time:
            self.logger.warning("No timestamp found for submission")
            return False, "No timestamp"
        
        is_late, late_by = is_submission_late(submission_time, self.deadline)
        
        if is_late:
            status_msg = f"Late by {late_by}"
            self.logger.info(f"Submission is late: {status_msg}")
        else:
            status_msg = "On time"
            self.logger.info("Submission is on time")
        
        return is_late, status_msg
    
    def update_sheet_timeliness(self, worksheet, submission: Dict[str, Any], is_late: bool, status_msg: str):
        """
        Update the timeliness status in the Google Sheet
        
        Args:
            worksheet: Google Sheets worksheet object
            submission: Submission dictionary with _row_index
            is_late: Whether submission is late
            status_msg: Status message to write
        """
        row = submission['_row_index']
        timeliness_col = get_column_index(worksheet, 'Timeliness')
        
        if timeliness_col:
            update_sheet_cell(worksheet, row, timeliness_col, status_msg)
            self.logger.info(f"Updated timeliness status for row {row}: {status_msg}")
    
    def process_submission(self, worksheet, submission: Dict[str, Any], column_mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        Process a single submission for timeliness
        
        Args:
            worksheet: Google Sheets worksheet object
            submission: Submission dictionary
            column_mapping: Column name mapping
            
        Returns:
            Result dictionary with timeliness information
        """
        try:
            is_late, status_msg = self.check_timeliness(submission, column_mapping)
            
            # Update the sheet
            self.update_sheet_timeliness(worksheet, submission, is_late, status_msg)
            
            return {
                'success': True,
                'is_late': is_late,
                'late_message': status_msg if is_late else None
            }
            
        except Exception as e:
            self.logger.error(f"Error checking timeliness: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }


def main():
    """
    Standalone entry point for testing the Timeliness Agent
    """
    from utils import load_config, setup_logging, connect_to_google_sheets, get_all_submissions, autodetect_columns
    
    config = load_config()
    logger = setup_logging(config)
    
    # Connect to sheet
    client, worksheet = connect_to_google_sheets(config)
    
    # Get submissions
    submissions = get_all_submissions(worksheet)
    headers = worksheet.row_values(1)
    column_mapping = autodetect_columns(headers)
    
    # Create agent
    agent = TimelinessAgent(config, logger)
    
    # Process first submission as test
    if submissions:
        test_submission = submissions[0]
        test_submission['_row_index'] = 2
        
        result = agent.process_submission(worksheet, test_submission, column_mapping)
        print(f"Timeliness check result: {result}")


if __name__ == '__main__':
    main()
