"""
Shared utilities for PortfoliOS agents
Functions used by multiple agents live here
"""

import re
import yaml
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials
import google.generativeai as genai


# =============================================================================
# Configuration Loading
# =============================================================================

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file
    
    Args:
        config_path: Path to config.yaml file
        
    Returns:
        Dictionary containing all configuration settings
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is malformed
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            f"Please copy config.example.yaml to config.yaml and fill in your details."
        )
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Validate required fields
    required_fields = [
        ('google_sheets', 'spreadsheet_name'),
        ('google_sheets', 'service_account_file'),
        ('deadline', 'datetime'),
        ('gemini', 'api_key'),
        ('email', 'provider'),
        ('email', 'teacher_email'),
    ]
    
    for section, field in required_fields:
        if section not in config or field not in config[section]:
            raise ValueError(f"Missing required config field: {section}.{field}")
        
        value = config[section][field]
        if not value or (isinstance(value, str) and value.startswith("YOUR_")):
            raise ValueError(
                f"Please fill in {section}.{field} in config.yaml\n"
                f"Currently set to: {value}"
            )
    
    return config


# =============================================================================
# Google Sheets Connection
# =============================================================================

def connect_to_google_sheets(config: Dict[str, Any]) -> tuple:
    """
    Connect to Google Sheets using service account credentials
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Tuple of (gspread.Client, gspread.Worksheet)
    """
    service_account_file = config['google_sheets']['service_account_file']
    spreadsheet_name = config['google_sheets']['spreadsheet_name']
    
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    creds = Credentials.from_service_account_file(service_account_file, scopes=scopes)
    client = gspread.authorize(creds)
    
    # Open the spreadsheet
    sheet = client.open(spreadsheet_name)
    worksheet = sheet.sheet1  # Use first worksheet by default
    
    return client, worksheet


def get_all_submissions(worksheet: gspread.Worksheet) -> list:
    """
    Get all submission records from the worksheet
    
    Args:
        worksheet: Google Sheets worksheet object
        
    Returns:
        List of dictionaries, one per submission row
    """
    return worksheet.get_all_records()


def update_sheet_cell(worksheet: gspread.Worksheet, row: int, col: int, value: Any):
    """
    Update a single cell in the worksheet
    
    Args:
        worksheet: Google Sheets worksheet object
        row: Row number (1-indexed, where 1 is the header)
        col: Column number (1-indexed)
        value: Value to write to the cell
    """
    worksheet.update_cell(row, col, value)


def get_column_index(worksheet: gspread.Worksheet, column_name: str) -> int:
    """
    Get the 1-based column index for a given column name
    
    Args:
        worksheet: Google Sheets worksheet object
        column_name: Name of the column to find
        
    Returns:
        1-based column index, or None if not found
    """
    header_row = worksheet.row_values(1)
    try:
        return header_row.index(column_name) + 1
    except ValueError:
        return None


# =============================================================================
# Email Utilities
# =============================================================================

def clean_email_address(email: str) -> str:
    """
    Clean and validate email address
    
    Args:
        email: Raw email address string
        
    Returns:
        Cleaned email address
    """
    email = email.strip().lower()
    # Remove any whitespace
    email = re.sub(r'\s+', '', email)
    return email


def validate_email(email: str) -> bool:
    """
    Validate email address format
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid format, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


# =============================================================================
# Gemini AI Utilities
# =============================================================================

def initialize_gemini(config: Dict[str, Any]):
    """
    Initialize the Gemini AI API
    
    Args:
        config: Configuration dictionary
    """
    api_key = config['gemini']['api_key']
    genai.configure(api_key=api_key)


def get_gemini_model(config: Dict[str, Any]):
    """
    Get configured Gemini model instance
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Gemini GenerativeModel instance
    """
    model_name = config['gemini'].get('model', 'gemini-2.0-flash-exp')
    temperature = config['gemini'].get('temperature', 0.7)
    
    generation_config = {
        'temperature': temperature,
        'top_p': 0.95,
        'top_k': 40,
        'max_output_tokens': 8192,
    }
    
    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config=generation_config
    )
    
    return model


# =============================================================================
# Date/Time Utilities
# =============================================================================

def parse_deadline(config: Dict[str, Any]) -> datetime:
    """
    Parse deadline from config
    
    Args:
        config: Configuration dictionary
        
    Returns:
        datetime object representing the deadline
    """
    deadline_str = config['deadline']['datetime']
    
    # Parse the datetime string
    try:
        deadline = datetime.strptime(deadline_str, '%Y-%m-%d %H:%M')
    except ValueError:
        raise ValueError(
            f"Invalid deadline format: {deadline_str}\n"
            f"Expected format: YYYY-MM-DD HH:MM (e.g., '2026-02-15 23:59')"
        )
    
    return deadline


def is_submission_late(submission_time: str, deadline: datetime) -> tuple:
    """
    Check if a submission is late
    
    Args:
        submission_time: Timestamp string from Google Form
        deadline: Deadline datetime object
        
    Returns:
        Tuple of (is_late: bool, late_by: str or None)
    """
    try:
        # Try multiple date formats
        formats = [
            '%m/%d/%Y %H:%M:%S',  # Google Forms format
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%m/%d/%Y %I:%M:%S %p',
        ]
        
        submission_dt = None
        for fmt in formats:
            try:
                submission_dt = datetime.strptime(submission_time, fmt)
                break
            except ValueError:
                continue
        
        if submission_dt is None:
            return False, None
        
        if submission_dt > deadline:
            # Calculate how late
            delta = submission_dt - deadline
            
            days = delta.days
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            
            late_str_parts = []
            if days > 0:
                late_str_parts.append(f"{days} day{'s' if days > 1 else ''}")
            if hours > 0:
                late_str_parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
            if minutes > 0:
                late_str_parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
            
            late_str = ", ".join(late_str_parts) if late_str_parts else "less than a minute"
            
            return True, late_str
        else:
            return False, None
            
    except Exception as e:
        logging.error(f"Error parsing submission time: {e}")
        return False, None


# =============================================================================
# Logging Setup
# =============================================================================

def setup_logging(config: Dict[str, Any]) -> logging.Logger:
    """
    Set up logging for the application
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured logger instance
    """
    log_dir = Path(config['logging'].get('log_directory', 'logs'))
    log_dir.mkdir(exist_ok=True)
    
    log_level = config['logging'].get('level', 'INFO')
    
    # Create logger
    logger = logging.getLogger('portfolios')
    logger.setLevel(getattr(logging, log_level))
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    log_file = log_dir / f"portfolios_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


# =============================================================================
# Auto-detect Column Names
# =============================================================================

def autodetect_columns(headers: list) -> Dict[str, str]:
    """
    Auto-detect column names from sheet headers using fuzzy matching
    
    Args:
        headers: List of header strings from worksheet
        
    Returns:
        Dictionary mapping standard names to actual column names
    """
    headers_lower = [h.lower() if h else "" for h in headers]
    
    mapping = {}
    
    # Define patterns for each required column
    patterns = {
        'timestamp': ['timestamp', 'date', 'time', 'submitted'],
        'email': ['email', 'e-mail', 'mail'],
        'first_name': ['first', 'firstname', 'fname', 'given name'],
        'last_name': ['last', 'lastname', 'lname', 'surname', 'family name'],
        'portfolio_link': ['portfolio', 'link', 'url', 'site', 'website'],
        'unit': ['unit', 'project', 'assignment', 'module'],
    }
    
    for standard_name, keywords in patterns.items():
        for i, header in enumerate(headers_lower):
            if any(keyword in header for keyword in keywords):
                mapping[standard_name] = headers[i]
                break
    
    # Validate required columns
    required = ['timestamp', 'email', 'portfolio_link']
    missing = [k for k in required if k not in mapping]
    
    if missing:
        raise ValueError(
            f"Could not auto-detect required columns: {', '.join(missing)}\n"
            f"Please ensure your sheet has columns with these names."
        )
    
    return mapping
