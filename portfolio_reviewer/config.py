"""
Configuration management for Portfolio Reviewer
Loads settings from .env file
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path so we can import schemas and orchestrator
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Load environment variables from .env file
load_dotenv()

class Config:
    """Central configuration for the application"""
    
    # Google Sheets
    GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', 'service-account-credentials.json')
    GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '')
    
    # Gemini API
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    
    # Gmail
    TEACHER_EMAIL = os.getenv('TEACHER_EMAIL', '')
    
    # Background Service
    CHECK_INTERVAL_SECONDS = int(os.getenv('CHECK_INTERVAL_SECONDS', '60'))
    
    # Paths
    BASE_DIR = Path(__file__).parent  # portfolio_reviewer folder
    RUBRICS_DIR = BASE_DIR / 'rubrics'
    STATE_FILE = BASE_DIR / 'processing_state.json'
    
    @classmethod
    def validate(cls):
        """Check if all required config is present"""
        errors = []
        
        if not cls.GOOGLE_SHEET_ID:
            errors.append("GOOGLE_SHEET_ID not set in .env")
        
        if not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY not set in .env")
        
        if not cls.TEACHER_EMAIL:
            errors.append("TEACHER_EMAIL not set in .env")
        
        creds_path = Path(cls.GOOGLE_CREDENTIALS_PATH)
        if not creds_path.exists():
            errors.append(f"Google credentials file not found: {cls.GOOGLE_CREDENTIALS_PATH}")
        
        return errors
    
    @classmethod
    def setup_directories(cls):
        """Create necessary directories"""
        cls.RUBRICS_DIR.mkdir(exist_ok=True)

# Validate config on import
config = Config()
