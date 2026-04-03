"""
Google Sheets integration
Reads student submissions from Google Form responses
"""
import json
import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Optional
from datetime import datetime
from config import config


class GoogleSheetsClient:
    """Read student submissions from Google Sheets"""
    
    def __init__(self):
        self.client = None
        self.sheet = None
        self._connect()
    
    def _connect(self):
        """Connect to Google Sheets using service account"""
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        if config.GOOGLE_CREDENTIALS_JSON:
            # Credentials provided as a JSON string (e.g. from Streamlit Cloud secrets)
            try:
                creds_info = json.loads(config.GOOGLE_CREDENTIALS_JSON)
            except json.JSONDecodeError as e:
                raise ValueError(
                    "GOOGLE_CREDENTIALS_JSON is not valid JSON. "
                    "Ensure the secret contains the full contents of your service account JSON file."
                ) from e
            creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        else:
            # Credentials provided as a file on disk (local development)
            creds = Credentials.from_service_account_file(
                config.GOOGLE_CREDENTIALS_PATH,
                scopes=scopes
            )
        
        self.client = gspread.authorize(creds)
        self.sheet = self.client.open_by_key(config.GOOGLE_SHEET_ID).sheet1
    
    def get_headers(self) -> List[str]:
        """Get column headers from the sheet"""
        return self.sheet.row_values(1)
    
    def get_all_submissions(self) -> List[Dict[str, str]]:
        """Get all form submissions as list of dictionaries"""
        records = self.sheet.get_all_records()
        return records
    
    def get_new_submissions(self, last_processed_row: int = 1) -> List[Dict[str, str]]:
        """
        Get only new submissions since last check
        
        Args:
            last_processed_row: Last row number that was processed
            
        Returns:
            List of new submission dictionaries
        """
        all_records = self.sheet.get_all_records()
        
        # Return only records after the last processed row
        # Row 1 is headers, so row 2 is first data row
        new_records = all_records[last_processed_row - 1:] if last_processed_row > 1 else all_records
        
        return new_records
    
    def get_row_count(self) -> int:
        """Get total number of rows (including header)"""
        return len(self.sheet.get_all_values())
    
    def update_status(self, row_number: int, status: str):
        """
        Update the Status column for a specific row
        
        Args:
            row_number: Row number in sheet (1-indexed, including header)
            status: Status text to write
        """
        headers = self.get_headers()
        
        # Find Status column
        if 'Status' in headers:
            status_col = headers.index('Status') + 1
            self.sheet.update_cell(row_number, status_col, status)
    
    def update_feedback_sent(self, row_number: int, timestamp: str):
        """
        Update the Feedback Sent column
        
        Args:
            row_number: Row number in sheet
            timestamp: Timestamp string
        """
        headers = self.get_headers()
        
        if 'Feedback Sent' in headers:
            feedback_col = headers.index('Feedback Sent') + 1
            self.sheet.update_cell(row_number, feedback_col, timestamp)
    
    def update_last_processed(self, row_number: int, timestamp: str):
        """
        Update the Last Processed column
        
        Args:
            row_number: Row number in sheet
            timestamp: Timestamp string
        """
        headers = self.get_headers()
        
        if 'Last Processed' in headers:
            processed_col = headers.index('Last Processed') + 1
            self.sheet.update_cell(row_number, processed_col, timestamp)
    
    @staticmethod
    def parse_submission(record: Dict[str, str]) -> Optional[Dict[str, str]]:
        """
        Parse a submission record into standardized format
        
        Handles various possible header names from Google Forms
        
        Returns:
            Dict with: student_name, email, unit, portfolio_url, timestamp
        """
        # Try to find the right columns (Google Forms can have varying header names)
        parsed = {}
        
        # Student name (first + last)
        first_name = None
        last_name = None
        
        for key in record.keys():
            key_lower = key.lower()
            
            if 'first' in key_lower and 'name' in key_lower:
                first_name = record[key]
            elif 'last' in key_lower and 'name' in key_lower:
                last_name = record[key]
            elif 'email address' in key_lower or key_lower == 'email':
                # Match "What is your email address?" but NOT
                # "When is a good time to meet..." or other questions
                parsed['email'] = record[key]
            elif (
                ('copy' in key_lower and 'paste' in key_lower)
                or ('publish' in key_lower and 'portf' in key_lower)
                or ('portf' in key_lower and ('url' in key_lower or 'link' in key_lower))
            ):
                parsed['portfolio_url'] = record[key]
            elif 'select' in key_lower and 'unit' in key_lower:
                parsed['unit'] = record[key]
            elif 'timestamp' in key_lower:
                parsed['timestamp'] = record[key]
            elif 'class' in key_lower and 'section' in key_lower:
                parsed['class_section'] = record[key]
        
        # Combine first and last name
        if first_name and last_name:
            parsed['student_name'] = f"{first_name} {last_name}"
        elif first_name:
            parsed['student_name'] = first_name
        elif last_name:
            parsed['student_name'] = last_name
        
        # Validate required fields
        if not parsed.get('portfolio_url'):
            return None
        
        return parsed
