"""
Caption Analyzer Agent

This agent uses Google's Gemini AI to analyze whether media captions are:
1. Present on all media
2. Descriptive and thorough
3. Relevant to the portfolio content
"""

import logging
import base64
from typing import Dict, Any, List
from PIL import Image
import io

from utils import (
    initialize_gemini,
    get_gemini_model,
    get_column_index,
    update_sheet_cell
)


class CaptionAnalyzerAgent:
    """
    Uses AI to analyze quality and relevance of media captions
    """
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize the Caption Analyzer Agent
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        
        # Initialize Gemini
        initialize_gemini(config)
        self.model = get_gemini_model(config)
        
        # Get agent-specific settings
        agent_config = config['agents']['caption_analyzer']
        self.min_caption_length = agent_config.get('min_caption_length', 20)
        self.strictness_level = agent_config.get('strictness_level', 3)
    
    def _prepare_image(self, screenshot_bytes: bytes) -> Image.Image:
        """
        Prepare screenshot for Gemini API
        
        Args:
            screenshot_bytes: Raw screenshot bytes
            
        Returns:
            PIL Image object
        """
        image = Image.open(io.BytesIO(screenshot_bytes))
        
        # Resize if too large (Gemini has limits)
        max_size = 4096
        if image.width > max_size or image.height > max_size:
            ratio = min(max_size / image.width, max_size / image.height)
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size, Image.LANCZOS)
            self.logger.info(f"Resized screenshot to {new_size}")
        
        return image
    
    def analyze_captions(self, screenshot_bytes: bytes, portfolio_description: str = "") -> Dict[str, Any]:
        """
        Use Gemini to analyze media captions in the screenshot
        
        Args:
            screenshot_bytes: Screenshot of the portfolio page
            portfolio_description: Text description of what the portfolio is about
            
        Returns:
            Analysis results dictionary
        """
        try:
            image = self._prepare_image(screenshot_bytes)
            
            # Build the prompt based on strictness level
            strictness_descriptions = {
                1: "be very lenient - accept minimal captions",
                2: "be somewhat lenient - accept brief captions",
                3: "use moderate standards - expect decent captions",
                4: "be strict - expect detailed captions",
                5: "be very strict - expect comprehensive captions"
            }
            
            strictness_instruction = strictness_descriptions.get(self.strictness_level, strictness_descriptions[3])
            
            prompt = f"""You are evaluating a student's digital portfolio for a teacher. 
Please analyze the media (images, videos, embedded content) visible in this screenshot and evaluate:

1. **Caption Presence**: Are captions or descriptions present for all media elements?
2. **Caption Quality**: Are the captions descriptive and thorough? (Minimum {self.min_caption_length} characters for "good")
3. **Caption Relevance**: Are the media and their captions relevant to the portfolio content?

Context: {portfolio_description if portfolio_description else "General portfolio assignment"}

Please {strictness_instruction}.

Respond in this EXACT format:
MEDIA_COUNT: [number of media elements you can identify]
MISSING_CAPTIONS: [number of media without captions]
POOR_CAPTIONS: [number of media with inadequate captions]
IRRELEVANT_MEDIA: [number of media that seem unrelated to content]
OVERALL_SCORE: [0-100 score for caption quality]
FEEDBACK: [2-3 sentences of constructive feedback for the student]
ISSUES: [specific issues found, one per line, or "None"]
"""
            
            # Send to Gemini
            self.logger.info("Sending screenshot to Gemini for caption analysis...")
            response = self.model.generate_content([prompt, image])
            
            # Parse response
            result = self._parse_gemini_response(response.text)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing captions with Gemini: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Gemini's response into structured data
        
        Args:
            response_text: Raw text response from Gemini
            
        Returns:
            Parsed result dictionary
        """
        result = {
            'success': True,
            'media_count': 0,
            'missing_captions': 0,
            'poor_captions': 0,
            'irrelevant_media': 0,
            'overall_score': 0,
            'feedback': "",
            'issues': []
        }
        
        try:
            lines = response_text.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('MEDIA_COUNT:'):
                    result['media_count'] = int(line.split(':', 1)[1].strip())
                
                elif line.startswith('MISSING_CAPTIONS:'):
                    result['missing_captions'] = int(line.split(':', 1)[1].strip())
                
                elif line.startswith('POOR_CAPTIONS:'):
                    result['poor_captions'] = int(line.split(':', 1)[1].strip())
                
                elif line.startswith('IRRELEVANT_MEDIA:'):
                    result['irrelevant_media'] = int(line.split(':', 1)[1].strip())
                
                elif line.startswith('OVERALL_SCORE:'):
                    score_str = line.split(':', 1)[1].strip()
                    result['overall_score'] = int(score_str)
                
                elif line.startswith('FEEDBACK:'):
                    result['feedback'] = line.split(':', 1)[1].strip()
                
                elif line.startswith('ISSUES:'):
                    issues_text = line.split(':', 1)[1].strip()
                    if issues_text.lower() != 'none':
                        result['issues'].append(issues_text)
                
                elif line and not any(line.startswith(prefix) for prefix in 
                                     ['MEDIA_COUNT:', 'MISSING_CAPTIONS:', 'POOR_CAPTIONS:', 
                                      'IRRELEVANT_MEDIA:', 'OVERALL_SCORE:', 'FEEDBACK:', 'ISSUES:']):
                    # Continuation of issues or feedback
                    if result['issues']:
                        result['issues'].append(line)
            
            # Calculate if there are issues
            result['has_issues'] = (
                result['missing_captions'] > 0 or 
                result['poor_captions'] > 0 or 
                result['irrelevant_media'] > 0
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error parsing Gemini response: {e}")
            result['success'] = False
            result['error'] = str(e)
            return result
    
    def update_sheet_caption_status(self, worksheet, submission: Dict[str, Any], analysis: Dict[str, Any]):
        """
        Update the caption status in the Google Sheet
        
        Args:
            worksheet: Google Sheets worksheet object
            submission: Submission dictionary with _row_index
            analysis: Analysis results dictionary
        """
        row = submission['_row_index']
        caption_status_col = get_column_index(worksheet, 'Caption Status')
        
        if analysis.get('has_issues'):
            status_parts = []
            if analysis['missing_captions'] > 0:
                status_parts.append(f"{analysis['missing_captions']} missing")
            if analysis['poor_captions'] > 0:
                status_parts.append(f"{analysis['poor_captions']} poor")
            if analysis['irrelevant_media'] > 0:
                status_parts.append(f"{analysis['irrelevant_media']} irrelevant")
            
            status_text = f"Issues: {', '.join(status_parts)} (Score: {analysis['overall_score']})"
        else:
            status_text = f"Good (Score: {analysis['overall_score']})"
        
        if caption_status_col:
            update_sheet_cell(worksheet, row, caption_status_col, status_text)
            self.logger.info(f"Updated caption status for row {row}: {status_text}")
    
    def process_submission(self, worksheet, submission: Dict[str, Any], 
                          column_mapping: Dict[str, str], 
                          screenshot_bytes: bytes) -> Dict[str, Any]:
        """
        Process a single submission for caption analysis
        
        Args:
            worksheet: Google Sheets worksheet object
            submission: Submission dictionary
            column_mapping: Column name mapping
            screenshot_bytes: Screenshot of portfolio page
            
        Returns:
            Result dictionary with analysis
        """
        try:
            # Get portfolio description if available
            unit_col = column_mapping.get('unit', 'Unit')
            portfolio_description = submission.get(unit_col, "")
            
            # Analyze captions
            analysis = self.analyze_captions(screenshot_bytes, portfolio_description)
            
            if analysis.get('success'):
                # Update sheet
                self.update_sheet_caption_status(worksheet, submission, analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error processing caption analysis: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }


def main():
    """
    Standalone entry point for testing the Caption Analyzer Agent
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
    agent = CaptionAnalyzerAgent(config, logger)
    
    print("Caption Analyzer Agent initialized successfully")
    print("Note: Full testing requires a screenshot from the Link Validator or Media Checker agents")


if __name__ == '__main__':
    main()
