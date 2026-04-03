"""
Google Sheets integration
Reads student submissions from Google Form responses
"""
import json
import re
import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Optional
from datetime import datetime
from config import config

# Simple pattern that matches the minimal structure of an email address
_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


class GoogleSheetsClient:
    """Read student submissions from Google Sheets"""

    # Class-level cache for AI header mappings (used when st.session_state is unavailable)
    _header_mapping_cache: Dict[str, Dict[str, str]] = {}

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
    def get_header_mapping(headers: List[str]) -> Optional[Dict[str, str]]:
        """
        Map arbitrary Google Sheet column headers to standardized field names using AI.

        Calls the Gemini API once per unique set of headers.  The result is cached
        in ``st.session_state`` (Streamlit context) and in a class-level dict
        (background-service context) so the API is never called more than once.

        Args:
            headers: Column headers from the Google Sheet.

        Returns:
            Dict mapping each header to one of: timestamp, class_section, last_name,
            first_name, unit, portfolio_url, email, other.
            Returns None if the AI call fails and no cached mapping exists.
        """
        cache_key = json.dumps(sorted(headers))

        # --- Try st.session_state cache (Streamlit context) ---
        try:
            import streamlit as st
            cache = st.session_state.setdefault('header_mapping_cache', {})
            if cache_key in cache:
                return cache[cache_key]
        except Exception:
            pass

        # --- Try class-level cache (background-service context) ---
        if cache_key in GoogleSheetsClient._header_mapping_cache:
            return GoogleSheetsClient._header_mapping_cache[cache_key]

        # --- Fetch mapping from AI ---
        mapping = GoogleSheetsClient._fetch_header_mapping_from_ai(headers)
        if mapping is None:
            return None

        # Store in both caches
        try:
            import streamlit as st
            st.session_state.setdefault('header_mapping_cache', {})[cache_key] = mapping
        except Exception:
            pass
        GoogleSheetsClient._header_mapping_cache[cache_key] = mapping

        return mapping

    @staticmethod
    def _fetch_header_mapping_from_ai(headers: List[str]) -> Optional[Dict[str, str]]:
        """
        Call the Gemini API to map column headers to standardized field names.

        Returns a dict like ``{"What is your email address?": "email", ...}``
        or None if the call fails.
        """
        if not config.GEMINI_API_KEY:
            return None

        try:
            import google.generativeai as genai
            genai.configure(api_key=config.GEMINI_API_KEY)

            model = genai.GenerativeModel("gemini-1.5-pro")

            prompt = (
                "You are mapping Google Form column headers to standardized field names.\n\n"
                "Given these column headers from a student portfolio submission Google Sheet:\n"
                f"{json.dumps(headers, indent=2)}\n\n"
                "Map each header to exactly one of these standardized field names:\n"
                "- timestamp: submission timestamp\n"
                "- class_section: class or section identifier\n"
                "- last_name: student's last name\n"
                "- first_name: student's first name\n"
                "- unit: assignment unit name\n"
                "- portfolio_url: URL/link to the student's digital portfolio\n"
                "- email: student's email address\n"
                "- other: any column that does not match the above\n\n"
                "Return ONLY a valid JSON object with no markdown formatting, for example:\n"
                '{"Header text here": "field_name", "Another header": "other"}'
            )

            response = model.generate_content(prompt)
            response_text = response.text.strip()

            # Strip markdown code fences if present
            if "```" in response_text:
                response_text = response_text.replace("```json", "").replace("```", "").strip()

            try:
                mapping = json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"AI header mapping returned invalid JSON: {e}\nResponse was: {response_text[:300]}")
                return None
            return mapping

        except Exception as e:
            print(f"AI header mapping failed: {e}")
            return None

    @staticmethod
    def _parse_submission_fallback(record: Dict[str, str]) -> Optional[Dict[str, str]]:
        """
        Keyword-based fallback parser used when the AI header mapping is unavailable.
        """
        parsed = {}
        first_name = None
        last_name = None

        # Collect all candidate email values so we can pick the best one
        email_candidates: List[str] = []

        for key in record.keys():
            key_lower = key.lower().strip()

            if 'first' in key_lower and 'name' in key_lower:
                first_name = record[key]
            elif 'last' in key_lower and 'name' in key_lower:
                last_name = record[key]
            elif 'email address' in key_lower or key_lower == 'email':
                if record[key] and str(record[key]).strip():
                    email_candidates.append(record[key])
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

        # Pick the best email: prefer a value that looks like a real email address.
        # We check all candidates and take the first with a valid email format.
        # If none pass the check, fall back to the last candidate (Google Forms
        # typically places the dedicated email question near the end of the form).
        if email_candidates:
            real_emails = [v for v in email_candidates if _EMAIL_RE.match(str(v))]
            parsed['email'] = real_emails[0] if real_emails else email_candidates[-1]

        if first_name and last_name:
            parsed['student_name'] = f"{first_name} {last_name}"
        elif first_name:
            parsed['student_name'] = first_name
        elif last_name:
            parsed['student_name'] = last_name

        if not parsed.get('portfolio_url'):
            return None

        return parsed

    @staticmethod
    def parse_submission(record: Dict[str, str]) -> Optional[Dict[str, str]]:
        """
        Parse a submission record into standardized format.

        Tries AI-powered header mapping first (cached after the first call).
        Falls back to keyword matching if the AI call fails.

        Returns:
            Dict with: student_name, email, unit, portfolio_url, timestamp
            or None if portfolio_url is missing.
        """
        headers = list(record.keys())
        mapping = GoogleSheetsClient.get_header_mapping(headers)

        if mapping is None:
            # AI unavailable — use keyword fallback
            return GoogleSheetsClient._parse_submission_fallback(record)

        # Apply the AI-generated mapping
        parsed: Dict[str, str] = {}
        first_name = None
        last_name = None

        for header, value in record.items():
            field = mapping.get(header, 'other')
            if field == 'first_name':
                first_name = value
            elif field == 'last_name':
                last_name = value
            elif field in ('email', 'portfolio_url', 'unit', 'timestamp', 'class_section'):
                if value:
                    parsed[field] = value

        # Combine first and last name
        if first_name and last_name:
            parsed['student_name'] = f"{first_name} {last_name}"
        elif first_name:
            parsed['student_name'] = first_name
        elif last_name:
            parsed['student_name'] = last_name

        # If the AI-mapped email doesn't look like a real email address, scan all
        # record values for one that does (e.g. the header was renamed / mis-mapped).
        if not _EMAIL_RE.match(str(parsed.get('email', ''))):
            for value in record.values():
                if isinstance(value, str) and _EMAIL_RE.match(value):
                    parsed['email'] = value
                    break

        # Validate required fields
        if not parsed.get('portfolio_url'):
            return None

        return parsed
