"""
Rubric parser - extracts criteria from PDF rubrics using Gemini AI with regex fallback
"""
import sys
from pathlib import Path

# Add parent directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

import json
import re
import PyPDF2
from typing import List, Dict, Optional
from schemas.rubric import RubricCategory, RubricCriterion, RubricVersion


class RubricParser:
    """Parse rubric PDFs and convert to structured format.

    Uses Gemini AI as the primary parser (handles any rubric layout) with a
    regex-based fallback in case the AI is unavailable.
    """

    def __init__(self):
        pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse_pdf(self, pdf_path: Path) -> Optional[RubricVersion]:
        """
        Parse a rubric PDF and extract criteria.

        Tries AI parsing first; falls back to regex if AI is unavailable.
        """
        try:
            text = self._extract_pdf_text(pdf_path)

            # Try AI-powered parsing first
            rubric_data = self._parse_with_ai(text, pdf_path.stem)

            # Fall back to regex if AI failed
            if not rubric_data:
                print("  AI parsing unavailable or failed — using regex fallback")
                rubric_data = self._parse_rubric_text(text, pdf_path.stem)

            if not rubric_data:
                return None

            return self._build_rubric_version(rubric_data, pdf_path.stem)

        except Exception as e:
            print(f"Error parsing rubric PDF {pdf_path}: {e}")
            return None

    # ------------------------------------------------------------------
    # AI-powered parsing (primary path)
    # ------------------------------------------------------------------

    def _parse_with_ai(self, text: str, rubric_name: str) -> Optional[Dict]:
        """
        Send the PDF text to Gemini and ask it to extract rubric criteria.

        Returns a rubric_data dict in the same format as _parse_rubric_text,
        or None if the AI call fails.
        """
        try:
            from config import config
            if not config.GEMINI_API_KEY:
                return None

            import google.generativeai as genai
            genai.configure(api_key=config.GEMINI_API_KEY)

            preferred_models = ["gemini-2.5-pro", "gemini-1.5-pro", "gemini-pro"]
            model = None
            for model_name in preferred_models:
                try:
                    model = genai.GenerativeModel(model_name)
                    break
                except Exception:
                    continue
            if model is None:
                return None

            prompt = f"""You are parsing a teacher's rubric PDF for a digital portfolio assignment.

Extract EVERY graded criterion (section) from the rubric text below.
Each criterion is a skill or deliverable the student must demonstrate.
DO NOT include rubric level descriptions (e.g. "Exceeds", "Meets", "Needs Work") as separate criteria.

Return ONLY a valid JSON object with this exact structure — no markdown, no explanation:
{{
  "title": "{rubric_name}",
  "categories": [
    {{
      "name": "Criterion Title Here",
      "criterion": {{
        "id": "short_snake_case_id",
        "title": "Criterion Title Here",
        "descriptor": "Brief description of what is being assessed",
        "max_points": 10,
        "levels": [
          {{"label": "Exceeds", "descriptor": "What exceeds looks like", "points": 10}},
          {{"label": "Meets", "descriptor": "What meets looks like", "points": 8}},
          {{"label": "Approaches", "descriptor": "What approaches looks like", "points": 6}},
          {{"label": "Needs Work", "descriptor": "What needs work looks like", "points": 2}}
        ]
      }}
    }}
  ]
}}

Rules:
- "id" must be unique, lowercase, underscores only, derived from the criterion title (e.g. "project_overview")
- "max_points" is the highest point value possible for that criterion
- Include all performance levels you can find; if none are listed use the 4-level template above
- If a criterion has no explicit point values, estimate from context or use 10
- The "levels" array goes from best to worst performance

RUBRIC TEXT:
{text[:8000]}
"""

            response = model.generate_content(
                prompt,
                request_options={"timeout": 120},
            )
            response_text = response.text.strip()

            # Strip markdown fences if present
            if "```" in response_text:
                response_text = re.sub(r'```(?:json)?', '', response_text).strip()

            rubric_data = json.loads(response_text)

            # Basic validation
            if not rubric_data.get('categories'):
                return None

            # Ensure every criterion has an id
            for cat in rubric_data['categories']:
                crit = cat.get('criterion', {})
                if not crit.get('id'):
                    crit['id'] = re.sub(r'[^a-z0-9]+', '_', crit.get('title', 'criterion').lower()).strip('_')

            print(f"  AI parsed {len(rubric_data['categories'])} criteria from rubric")
            return rubric_data

        except Exception as e:
            print(f"  AI rubric parsing failed: {e}")
            return None

    # ------------------------------------------------------------------
    # Regex-based parsing (fallback)
    # ------------------------------------------------------------------

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
        Regex-based rubric parser (fallback when AI is unavailable).

        Looks for section headers of the form "Title – N points".
        Requires the title to start with an uppercase letter to avoid
        accidentally matching rubric level descriptions like "2 Needs Work:...".
        """
        rubric_data = {
            'title': rubric_name,
            'total_points': 0,
            'categories': []
        }

        # Find total points
        total_match = re.search(r'(\d+)\s+Points?\s+Total', text, re.IGNORECASE)
        if not total_match:
            total_match = re.search(r'Total\s*[:\-]?\s*(\d+)\s+points?', text, re.IGNORECASE)
        if total_match:
            rubric_data['total_points'] = int(total_match.group(1))

        # Require the title to start with an uppercase letter so we don't match
        # level-description lines that begin with a digit (e.g. "2 Needs Work:...")
        section_pattern = r'([A-Z][^–\n]{3,60}?)\s*[–-]\s*(\d+)\s+points?'
        sections = list(re.finditer(section_pattern, text, re.IGNORECASE))

        if not sections:
            print(f"No sections found in rubric. Text preview: {text[:500]}")
            if rubric_data['total_points'] > 0:
                rubric_data['categories'].append({
                    'name': rubric_name,
                    'criterion': {
                        'id': re.sub(r'[^a-z0-9]+', '_', rubric_name.lower()).strip('_'),
                        'title': rubric_name,
                        'descriptor': '',
                        'max_points': rubric_data['total_points'],
                        'levels': self._default_levels(rubric_data['total_points'])
                    }
                })
            return rubric_data if rubric_data['categories'] else None

        for i, match in enumerate(sections):
            section_title = match.group(1).strip()
            section_points = int(match.group(2))

            start_pos = match.end()
            end_pos = sections[i + 1].start() if i + 1 < len(sections) else len(text)
            section_content = text[start_pos:end_pos]

            levels = self._parse_levels(section_content, section_points)
            if not levels:
                levels = self._default_levels(section_points)

            criterion_id = re.sub(r'[^a-z0-9]+', '_', section_title.lower()).strip('_')[:40]

            rubric_data['categories'].append({
                'name': section_title,
                'criterion': {
                    'id': criterion_id,
                    'title': section_title,
                    'descriptor': '',
                    'max_points': section_points,
                    'levels': levels
                }
            })

        return rubric_data if rubric_data['categories'] else None

    def _default_levels(self, max_points: int) -> List[Dict]:
        return [
            {'label': 'Exceeds',    'descriptor': 'Exceeds expectations',   'points': max_points},
            {'label': 'Meets',      'descriptor': 'Meets expectations',      'points': int(max_points * 0.8)},
            {'label': 'Approaches', 'descriptor': 'Approaches expectations', 'points': int(max_points * 0.6)},
            {'label': 'Needs Work', 'descriptor': 'Needs improvement',       'points': 0},
        ]

    def _parse_levels(self, section_text: str, max_points: int) -> List[Dict]:
        """Parse performance levels from section text."""
        levels = []
        level_pattern = r'[☐□▢]?\s*(\d+)[-–](\d+)\s+(\w+(?:\s+\w+)?)\s*\n([^☐□▢]+?)(?=\n[☐□▢]|\Z)'
        for match in re.finditer(level_pattern, section_text, re.DOTALL | re.MULTILINE):
            label = match.group(3).strip()
            descriptor = re.sub(r'\s+', ' ', match.group(4).strip())
            levels.append({
                'label': label,
                'descriptor': descriptor,
                'points': int(match.group(2))
            })
        return levels

    # ------------------------------------------------------------------
    # Schema construction (shared by both paths)
    # ------------------------------------------------------------------

    def _build_rubric_version(self, rubric_data: Dict, rubric_name: str) -> RubricVersion:
        """Convert parsed data to RubricVersion object"""
        from schemas.rubric import CriterionLevel

        categories = []
        for cat_data in rubric_data['categories']:
            crit_data = cat_data['criterion']
            levels = [
                CriterionLevel(
                    label=lvl['label'],
                    descriptor=lvl['descriptor'],
                    points=lvl.get('points')
                )
                for lvl in crit_data.get('levels', [])
            ]

            criterion = RubricCriterion(
                id=crit_data['id'],
                category=cat_data['name'],
                title=crit_data['title'],
                descriptor=crit_data.get('descriptor', ''),
                max_points=crit_data.get('max_points'),
                levels=levels
            )

            categories.append(RubricCategory(
                name=cat_data['name'],
                criteria=[criterion]
            ))

        rubric_id = rubric_name.lower().replace(' ', '_').replace('-', '_')
        return RubricVersion(
            rubric_id=rubric_id,
            version='v1',
            title=rubric_data['title'],
            categories=categories
        )
