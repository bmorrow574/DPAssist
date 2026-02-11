"""
Rubric parser - extracts criteria from PDF rubrics
"""
import sys
from pathlib import Path

# Add parent directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

import PyPDF2
import re
from typing import List, Dict, Optional
from schemas.rubric import RubricCategory, RubricCriterion, RubricVersion, Rubric


class RubricParser:
    """Parse rubric PDFs and convert to structured format"""
    
    def __init__(self):
        pass
    
    def parse_pdf(self, pdf_path: Path) -> Optional[RubricVersion]:
        """
        Parse a rubric PDF and extract criteria
        
        Args:
            pdf_path: Path to rubric PDF file
            
        Returns:
            RubricVersion object or None
        """
        try:
            # Extract text from PDF
            text = self._extract_pdf_text(pdf_path)
            
            # Parse the rubric structure
            rubric_data = self._parse_rubric_text(text, pdf_path.stem)
            
            if not rubric_data:
                return None
            
            # Convert to RubricVersion
            return self._build_rubric_version(rubric_data, pdf_path.stem)
            
        except Exception as e:
            print(f"Error parsing rubric PDF {pdf_path}: {e}")
            return None
    
    def _extract_pdf_text(self, pdf_path: Path) -> str:
        """Extract all text from PDF"""
        text = ""
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        
        return text
    
    def _parse_rubric_text(self, text: str, rubric_name: str) -> Optional[Dict]:
        """
        Parse rubric text and extract criteria
        
        This uses pattern matching to find:
        - Section titles (e.g., "1. Problem Statement & Requirements")
        - Point values
        - Level descriptions (Exceeds, Meets, Approaches, Needs Work)
        """
        rubric_data = {
            'title': rubric_name,
            'total_points': 0,
            'categories': []
        }
        
        # Find total points
        total_match = re.search(r'(\d+)\s+Points?\s+Total', text, re.IGNORECASE)
        if total_match:
            rubric_data['total_points'] = int(total_match.group(1))
        
        # Split into sections
        # Pattern: "1. Title – XX points"
        section_pattern = r'(\d+)\.\s+([^–\n]+)\s*[–-]\s*(\d+)\s+points?'
        sections = list(re.finditer(section_pattern, text, re.IGNORECASE))
        
        for i, match in enumerate(sections):
            section_num = match.group(1)
            section_title = match.group(2).strip()
            section_points = int(match.group(3))
            
            # Extract description (text in parentheses after title)
            desc_match = re.search(r'\(([^)]+)\)', text[match.start():match.start() + 200])
            section_desc = desc_match.group(1) if desc_match else ""
            
            # Get section content (between this section and next)
            start_pos = match.end()
            end_pos = sections[i + 1].start() if i + 1 < len(sections) else len(text)
            section_content = text[start_pos:end_pos]
            
            # Parse levels within this section
            levels = self._parse_levels(section_content, section_points)
            
            # Create criterion
            criterion_id = f"{section_num}_{section_title.lower().replace(' ', '_').replace('&', 'and')[:30]}"
            
            category = {
                'name': section_title,
                'criterion': {
                    'id': criterion_id,
                    'title': section_title,
                    'descriptor': section_desc,
                    'max_points': section_points,
                    'levels': levels
                }
            }
            
            rubric_data['categories'].append(category)
        
        return rubric_data if rubric_data['categories'] else None
    
    def _parse_levels(self, section_text: str, max_points: int) -> List[Dict]:
        """
        Parse performance levels from section text
        
        Looks for patterns like:
        ☐ 9–10 Exceeds
        Description here...
        """
        levels = []
        
        # Pattern for level headers: ☐ 9–10 Exceeds
        level_pattern = r'[☐□▢]?\s*(\d+)[-–](\d+)\s+(\w+(?:\s+\w+)?)\s*\n([^☐□▢]+?)(?=\n[☐□▢]|\Z)'
        
        matches = re.finditer(level_pattern, section_text, re.DOTALL | re.MULTILINE)
        
        for match in matches:
            min_points = int(match.group(1))
            max_points_level = int(match.group(2))
            label = match.group(3).strip()
            descriptor = match.group(4).strip()
            
            # Clean up descriptor
            descriptor = re.sub(r'\s+', ' ', descriptor)
            descriptor = descriptor.replace('\n', ' ')
            
            levels.append({
                'label': label,
                'descriptor': descriptor,
                'points': max_points_level  # Use max of range
            })
        
        return levels
    
    def _build_rubric_version(self, rubric_data: Dict, rubric_name: str) -> RubricVersion:
        """Convert parsed data to RubricVersion object"""
        from schemas.rubric import CriterionLevel
        
        categories = []
        
        for cat_data in rubric_data['categories']:
            # Build levels
            levels = []
            for lvl_data in cat_data['criterion']['levels']:
                level = CriterionLevel(
                    label=lvl_data['label'],
                    descriptor=lvl_data['descriptor'],
                    points=lvl_data.get('points')
                )
                levels.append(level)
            
            # Build criterion
            criterion = RubricCriterion(
                id=cat_data['criterion']['id'],
                category=cat_data['name'],
                title=cat_data['criterion']['title'],
                descriptor=cat_data['criterion']['descriptor'],
                max_points=cat_data['criterion']['max_points'],
                levels=levels
            )
            
            # Build category
            category = RubricCategory(
                name=cat_data['name'],
                criteria=[criterion]
            )
            
            categories.append(category)
        
        # Create rubric
        rubric_id = rubric_name.lower().replace(' ', '_').replace('-', '_')
        
        rubric_version = RubricVersion(
            rubric_id=rubric_id,
            version='v1',
            title=rubric_data['title'],
            categories=categories
        )
        
        return rubric_version
