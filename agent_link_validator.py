"""
Link Validator Agent

This agent validates that portfolio links are accessible and don't have permission issues.
It checks for broken links, 404 errors, and Google permission walls.
"""

import logging
import time
from typing import Dict, Any, Tuple
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

from utils import get_column_index, update_sheet_cell


class LinkValidatorAgent:
    """
    Validates portfolio links for accessibility
    """
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize the Link Validator Agent
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        
        # Get agent-specific settings
        agent_config = config['agents']['link_validator']
        self.timeout = agent_config.get('timeout', 30)
        self.max_retries = agent_config.get('max_retries', 3)
    
    def _create_webdriver(self) -> webdriver.Chrome:
        """
        Create a headless Chrome webdriver
        
        Returns:
            Chrome webdriver instance
        """
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Install and use ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(self.timeout)
        
        return driver
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Check if URL has valid format
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid format, False otherwise
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _check_permission_wall(self, driver: webdriver.Chrome) -> Tuple[bool, str]:
        """
        Check if page shows a Google permission wall
        
        Args:
            driver: Chrome webdriver instance
            
        Returns:
            Tuple of (is_restricted: bool, error_message: str)
        """
        try:
            html = driver.page_source.lower()
            title = (driver.title or "").lower()
            url = driver.current_url.lower()
        except Exception as e:
            self.logger.warning(f"Could not check for permission wall: {e}")
            return False, ""
        
        # Check for Google sign-in page
        if "accounts.google.com" in url:
            return True, "Redirected to Google sign-in page"
        
        # Permission phrases
        permission_phrases = [
            "you need permission",
            "request access",
            "you don't have access",
            "sign in to continue",
            "ask the owner for access",
        ]
        
        # Check if on Google Drive with permission issue
        if "drive.google.com" in url or "drive.google.com" in html:
            if any(phrase in html for phrase in permission_phrases):
                return True, "Portfolio requires access permission"
        
        # Check title for permission issues
        if any(phrase in title for phrase in permission_phrases):
            return True, "Portfolio requires access permission"
        
        return False, ""
    
    def validate_link(self, url: str) -> Tuple[str, str, bytes]:
        """
        Validate a portfolio link
        
        Args:
            url: Portfolio URL to validate
            
        Returns:
            Tuple of (status: str, error_message: str, screenshot: bytes or None)
            Status can be: "Valid", "Invalid URL", "Broken Link", "Permission Denied", "Timeout"
        """
        # First check URL format
        if not self._is_valid_url(url):
            self.logger.warning(f"Invalid URL format: {url}")
            return "Invalid URL", "The URL format is not valid", None
        
        driver = None
        screenshot = None
        
        try:
            driver = self._create_webdriver()
            
            # Try to load the page
            self.logger.info(f"Loading URL: {url}")
            driver.get(url)
            
            # Wait a moment for page to load
            time.sleep(3)
            
            # Check for permission wall
            is_restricted, restriction_msg = self._check_permission_wall(driver)
            
            if is_restricted:
                self.logger.warning(f"Permission issue: {restriction_msg}")
                return "Permission Denied", restriction_msg, None
            
            # Check if we got a 404 or error page
            page_title = driver.title.lower()
            if "404" in page_title or "not found" in page_title or "error" in page_title:
                self.logger.warning(f"Page appears broken: {page_title}")
                return "Broken Link", f"Page shows error: {driver.title}", None
            
            # Take a screenshot for later use
            screenshot = driver.get_screenshot_as_png()
            
            self.logger.info(f"Link validation successful: {url}")
            return "Valid", "", screenshot
            
        except TimeoutException:
            self.logger.error(f"Timeout loading URL: {url}")
            return "Timeout", "Page took too long to load", None
            
        except WebDriverException as e:
            self.logger.error(f"WebDriver error: {e}")
            return "Broken Link", str(e), None
            
        except Exception as e:
            self.logger.error(f"Unexpected error validating link: {e}", exc_info=True)
            return "Error", str(e), None
            
        finally:
            if driver:
                driver.quit()
    
    def update_sheet_link_status(self, worksheet, submission: Dict[str, Any], status: str, error_msg: str):
        """
        Update the link status in the Google Sheet
        
        Args:
            worksheet: Google Sheets worksheet object
            submission: Submission dictionary with _row_index
            status: Link validation status
            error_msg: Error message (if any)
        """
        row = submission['_row_index']
        link_status_col = get_column_index(worksheet, 'Link Status')
        
        status_text = status
        if error_msg:
            status_text = f"{status}: {error_msg}"
        
        if link_status_col:
            update_sheet_cell(worksheet, row, link_status_col, status_text)
            self.logger.info(f"Updated link status for row {row}: {status_text}")
    
    def process_submission(self, worksheet, submission: Dict[str, Any], column_mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        Process a single submission for link validation
        
        Args:
            worksheet: Google Sheets worksheet object
            submission: Submission dictionary
            column_mapping: Column name mapping
            
        Returns:
            Result dictionary with validation information
        """
        portfolio_link_col = column_mapping.get('portfolio_link', 'Portfolio Link')
        url = submission.get(portfolio_link_col, '').strip()
        
        if not url:
            self.logger.warning("No portfolio link found in submission")
            self.update_sheet_link_status(worksheet, submission, "Missing", "No URL provided")
            return {
                'success': False,
                'status': 'Missing',
                'error': 'No URL provided'
            }
        
        # Validate the link with retries
        for attempt in range(self.max_retries):
            try:
                status, error_msg, screenshot = self.validate_link(url)
                
                # Update sheet
                self.update_sheet_link_status(worksheet, submission, status, error_msg)
                
                return {
                    'success': status == "Valid",
                    'status': status,
                    'error': error_msg,
                    'screenshot': screenshot,
                    'url': url
                }
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    self.logger.warning(f"Attempt {attempt + 1} failed, retrying...")
                    time.sleep(2)
                else:
                    self.logger.error(f"All validation attempts failed: {e}")
                    self.update_sheet_link_status(worksheet, submission, "Error", str(e))
                    return {
                        'success': False,
                        'status': 'Error',
                        'error': str(e)
                    }


def main():
    """
    Standalone entry point for testing the Link Validator Agent
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
    agent = LinkValidatorAgent(config, logger)
    
    # Process first submission as test
    if submissions:
        test_submission = submissions[0]
        test_submission['_row_index'] = 2
        
        result = agent.process_submission(worksheet, test_submission, column_mapping)
        print(f"Link validation result: {result}")


if __name__ == '__main__':
    main()
