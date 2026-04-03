"""
Configuration management for Portfolio Reviewer
Loads settings from Streamlit secrets (when running on Streamlit Cloud)
or falls back to environment variables / .env file (when running locally).
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path so we can import schemas and orchestrator
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Load environment variables from .env file (no-op if file doesn't exist)
load_dotenv()

def _get_secret(key: str, default: str = '') -> str:
    """
    Retrieve a secret value.

    Priority order:
    1. Streamlit secrets (st.secrets) — used on Streamlit Cloud
    2. Environment variables / .env file — used locally
    """
    try:
        import streamlit as st
        value = st.secrets.get(key)
        if value is not None:
            return str(value)
    except (ImportError, AttributeError, FileNotFoundError, KeyError):
        pass
    return os.getenv(key, default)


class Config:
    """Central configuration for the application"""

    # Google Sheets
    GOOGLE_CREDENTIALS_PATH = _get_secret('GOOGLE_CREDENTIALS_PATH', 'service-account-credentials.json')
    # JSON string of the entire service-account credentials file (for Streamlit Cloud)
    GOOGLE_CREDENTIALS_JSON = _get_secret('GOOGLE_CREDENTIALS_JSON', '')
    GOOGLE_SHEET_ID = _get_secret('GOOGLE_SHEET_ID', '')

    # Gemini API
    GEMINI_API_KEY = _get_secret('GEMINI_API_KEY', '')

    # Gmail
    TEACHER_EMAIL = _get_secret('TEACHER_EMAIL', '')
    GMAIL_APP_PASSWORD = _get_secret('GMAIL_APP_PASSWORD', '')

    # Background Service
    CHECK_INTERVAL_SECONDS = int(_get_secret('CHECK_INTERVAL_SECONDS', '60'))

    # Paths
    BASE_DIR = Path(__file__).parent  # portfolio_reviewer folder
    RUBRICS_DIR = BASE_DIR / 'rubrics'
    STATE_FILE = BASE_DIR / 'processing_state.json'

    @classmethod
    def validate(cls):
        """Check if all required config is present"""
        errors = []

        if not cls.GOOGLE_SHEET_ID:
            errors.append("GOOGLE_SHEET_ID not set")

        if not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY not set")

        if not cls.TEACHER_EMAIL:
            errors.append("TEACHER_EMAIL not set")

        if not cls.GMAIL_APP_PASSWORD:
            errors.append("GMAIL_APP_PASSWORD not set")

        # Credentials are valid if either the JSON string is provided or the file exists on disk
        has_json_string = bool(cls.GOOGLE_CREDENTIALS_JSON)
        has_creds_file = Path(cls.GOOGLE_CREDENTIALS_PATH).exists()
        if not has_json_string and not has_creds_file:
            errors.append(
                f"Google credentials not found: set GOOGLE_CREDENTIALS_JSON secret "
                f"or place the file at {cls.GOOGLE_CREDENTIALS_PATH}"
            )

        return errors

    @classmethod
    def setup_directories(cls):
        """Create necessary directories"""
        cls.RUBRICS_DIR.mkdir(exist_ok=True)


# Validate config on import
config = Config()
