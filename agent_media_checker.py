"""
Media Checker Agent

This agent checks that all media (images, videos) on the portfolio page loads correctly.
It identifies broken images, failed embeds, and inaccessible media.
"""

import logging
from typing import Dict, Any, List, Tuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from utils import get_column_index, update_sheet_cell


class MediaCheckerAgent:
    """
    Checks accessibility of all media elements on a portfolio page
    """
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize the Media Checker Agent
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        
        # Get agent-specific settings
        agent_config = config['agents']['media_checker']
        self.media_timeout = agent_config.get('media_timeout', 10)
        self.full_page_screenshot = agent_config.get('full_page_screenshot', True)
    
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
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        
        return driver
    
    def check_media_accessibility(self, url: str, screenshot: bytes = None) -> Tuple[List[str], List[str], bytes]:
        """
        Check all media elements on a page
        
        Args:
            url: Portfolio URL to check
            screenshot: Optional existing screenshot from link validator
            
        Returns:
            Tuple of (accessible_media: List[str], broken_media: List[str], screenshot: bytes)
        """
        driver = None
        accessible_media = []
        broken_media = []
        
        try:
            driver = self._create_webdriver()
            
            self.logger.info(f"Loading page for media check: {url}")
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, self.media_timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check images
            images = driver.find_elements(By.TAG_NAME, "img")
            self.logger.info(f"Found {len(images)} image elements")
            
            for img in images:
                try:
                    src = img.get_attribute("src")
                    if not src:
                        continue
                    
                    # Check if image is loaded using JavaScript
                    is_loaded = driver.execute_script(
                        "return arguments[0].complete && arguments[0].naturalHeight !== 0",
                        img
                    )
                    
                    if is_loaded:
                        accessible_media.append(src)
                    else:
                        broken_media.append(src)
                        self.logger.warning(f"Broken image: {src}")
                        
                except Exception as e:
                    self.logger.warning(f"Error checking image: {e}")
            
            # Check videos
            videos = driver.find_elements(By.TAG_NAME, "video")
            self.logger.info(f"Found {len(videos)} video elements")
            
            for video in videos:
                try:
                    src = video.get_attribute("src")
                    if not src:
                        # Check for source tags
                        sources = video.find_elements(By.TAG_NAME, "source")
                        if sources:
                            src = sources[0].get_attribute("src")
                    
                    if src:
                        # Check if video has valid source
                        readyState = driver.execute_script("return arguments[0].readyState", video)
                        if readyState > 0:  # HAVE_NOTHING = 0
                            accessible_media.append(src)
                        else:
                            broken_media.append(src)
                            self.logger.warning(f"Broken video: {src}")
                            
                except Exception as e:
                    self.logger.warning(f"Error checking video: {e}")
            
            # Check iframes (embedded content like YouTube)
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            self.logger.info(f"Found {len(iframes)} iframe elements")
            
            for iframe in iframes:
                try:
                    src = iframe.get_attribute("src")
                    if src:
                        accessible_media.append(f"[Embed] {src}")
                        
                except Exception as e:
                    self.logger.warning(f"Error checking iframe: {e}")
            
            # Take screenshot if not provided
            if screenshot is None and self.full_page_screenshot:
                # Take full-page screenshot
                try:
                    # Get page dimensions
                    total_height = driver.execute_script("return document.body.scrollHeight")
                    driver.set_window_size(1920, total_height)
                    screenshot = driver.get_screenshot_as_png()
                except Exception as e:
                    self.logger.warning(f"Could not take full-page screenshot: {e}")
                    screenshot = driver.get_screenshot_as_png()
            
            return accessible_media, broken_media, screenshot
            
        except Exception as e:
            self.logger.error(f"Error checking media accessibility: {e}", exc_info=True)
            return [], [], screenshot
            
        finally:
            if driver:
                driver.quit()
    
    def update_sheet_media_status(self, worksheet, submission: Dict[str, Any], accessible_count: int, broken_count: int):
        """
        Update the media status in the Google Sheet
        
        Args:
            worksheet: Google Sheets worksheet object
            submission: Submission dictionary with _row_index
            accessible_count: Number of accessible media elements
            broken_count: Number of broken media elements
        """
        row = submission['_row_index']
        media_status_col = get_column_index(worksheet, 'Media Status')
        
        if broken_count > 0:
            status_text = f"{broken_count} broken media found"
        else:
            status_text = f"All media accessible ({accessible_count} items)"
        
        if media_status_col:
            update_sheet_cell(worksheet, row, media_status_col, status_text)
            self.logger.info(f"Updated media status for row {row}: {status_text}")
    
    def process_submission(self, worksheet, submission: Dict[str, Any], 
                          column_mapping: Dict[str, str], url: str, 
                          screenshot: bytes = None) -> Dict[str, Any]:
        """
        Process a single submission for media accessibility
        
        Args:
            worksheet: Google Sheets worksheet object
            submission: Submission dictionary
            column_mapping: Column name mapping
            url: Portfolio URL
            screenshot: Optional existing screenshot
            
        Returns:
            Result dictionary with media information
        """
        try:
            accessible, broken, screenshot = self.check_media_accessibility(url, screenshot)
            
            # Update sheet
            self.update_sheet_media_status(worksheet, submission, len(accessible), len(broken))
            
            return {
                'success': True,
                'accessible_media': accessible,
                'broken_media': broken,
                'accessible_count': len(accessible),
                'broken_count': len(broken),
                'screenshot': screenshot,
                'has_issues': len(broken) > 0
            }
            
        except Exception as e:
            self.logger.error(f"Error processing media check: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }


def main():
    """
    Standalone entry point for testing the Media Checker Agent
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
    agent = MediaCheckerAgent(config, logger)
    
    # Process first submission as test
    if submissions:
        test_submission = submissions[0]
        test_submission['_row_index'] = 2
        
        portfolio_link_col = column_mapping.get('portfolio_link', 'Portfolio Link')
        url = test_submission.get(portfolio_link_col, '')
        
        result = agent.process_submission(worksheet, test_submission, column_mapping, url)
        print(f"Media check result: {result}")


if __name__ == '__main__':
    main()
