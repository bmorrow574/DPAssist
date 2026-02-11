"""
Rubric manager - handles rubric storage and due date associations
"""
import sys
from pathlib import Path

# Add parent directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

import json
from datetime import datetime
from typing import Dict, List, Optional
from schemas.rubric import RubricVersion
from config import config


class RubricManager:
    """Manage rubrics and their associated due dates"""
    
    def __init__(self):
        self.rubrics_dir = config.RUBRICS_DIR
        self.rubrics_dir.mkdir(exist_ok=True)
        
        self.metadata_file = self.rubrics_dir / 'rubrics_metadata.json'
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Load rubrics metadata from JSON file"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self):
        """Save rubrics metadata to JSON file"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def add_rubric(
        self,
        rubric: RubricVersion,
        unit_name: str,
        due_date: str,
        pdf_path: Optional[Path] = None
    ):
        """
        Add a rubric with metadata
        
        Args:
            rubric: RubricVersion object
            unit_name: Name of the unit (for matching form submissions)
            due_date: Due date string (YYYY-MM-DD)
            pdf_path: Optional path to original PDF
        """
        rubric_id = rubric.rubric_id
        
        # Save rubric data as JSON
        rubric_file = self.rubrics_dir / f"{rubric_id}.json"
        rubric_data = {
            'rubric_id': rubric.rubric_id,
            'version': rubric.version,
            'title': rubric.title,
            'categories': []
        }
        
        for cat in rubric.categories:
            cat_data = {
                'name': cat.name,
                'criteria': []
            }
            
            for crit in cat.criteria:
                crit_data = {
                    'id': crit.id,
                    'category': crit.category,
                    'title': crit.title,
                    'descriptor': crit.descriptor,
                    'max_points': crit.max_points,
                    'levels': []
                }
                
                for level in crit.levels:
                    crit_data['levels'].append({
                        'label': level.label,
                        'descriptor': level.descriptor,
                        'points': level.points
                    })
                
                cat_data['criteria'].append(crit_data)
            
            rubric_data['categories'].append(cat_data)
        
        with open(rubric_file, 'w') as f:
            json.dump(rubric_data, f, indent=2)
        
        # Save metadata
        self.metadata[unit_name] = {
            'rubric_id': rubric_id,
            'title': rubric.title,
            'due_date': due_date,
            'pdf_path': str(pdf_path) if pdf_path else None,
            'created': datetime.now().isoformat()
        }
        
        self._save_metadata()
    
    def get_rubric_for_unit(self, unit_name: str) -> Optional[RubricVersion]:
        """
        Get rubric for a specific unit
        
        Args:
            unit_name: Unit name from form submission
            
        Returns:
            RubricVersion or None
        """
        if unit_name not in self.metadata:
            return None
        
        rubric_id = self.metadata[unit_name]['rubric_id']
        rubric_file = self.rubrics_dir / f"{rubric_id}.json"
        
        if not rubric_file.exists():
            return None
        
        with open(rubric_file, 'r') as f:
            data = json.load(f)
        
        # Reconstruct RubricVersion
        from schemas.rubric import RubricCategory, RubricCriterion, CriterionLevel
        
        categories = []
        for cat_data in data['categories']:
            criteria = []
            
            for crit_data in cat_data['criteria']:
                levels = []
                for lvl_data in crit_data.get('levels', []):
                    level = CriterionLevel(
                        label=lvl_data['label'],
                        descriptor=lvl_data['descriptor'],
                        points=lvl_data.get('points')
                    )
                    levels.append(level)
                
                criterion = RubricCriterion(
                    id=crit_data['id'],
                    category=crit_data['category'],
                    title=crit_data['title'],
                    descriptor=crit_data['descriptor'],
                    max_points=crit_data.get('max_points'),
                    levels=levels
                )
                criteria.append(criterion)
            
            category = RubricCategory(
                name=cat_data['name'],
                criteria=criteria
            )
            categories.append(category)
        
        rubric = RubricVersion(
            rubric_id=data['rubric_id'],
            version=data['version'],
            title=data['title'],
            categories=categories
        )
        
        return rubric
    
    def get_due_date(self, unit_name: str) -> Optional[datetime]:
        """Get due date for a unit"""
        if unit_name not in self.metadata:
            return None
        
        due_date_str = self.metadata[unit_name]['due_date']
        try:
            return datetime.strptime(due_date_str, '%Y-%m-%d')
        except:
            return None
    
    def is_past_due(self, unit_name: str) -> bool:
        """Check if unit is past due date"""
        due_date = self.get_due_date(unit_name)
        if not due_date:
            return False
        
        return datetime.now() > due_date
    
    def list_units(self) -> List[Dict]:
        """List all configured units with their rubrics"""
        units = []
        
        for unit_name, meta in self.metadata.items():
            due_date = self.get_due_date(unit_name)
            
            units.append({
                'unit_name': unit_name,
                'title': meta['title'],
                'due_date': meta['due_date'],
                'is_past_due': datetime.now() > due_date if due_date else False,
                'rubric_id': meta['rubric_id']
            })
        
        return units
    
    def delete_rubric(self, unit_name: str):
        """Delete a rubric configuration"""
        if unit_name in self.metadata:
            rubric_id = self.metadata[unit_name]['rubric_id']
            
            # Delete rubric file
            rubric_file = self.rubrics_dir / f"{rubric_id}.json"
            if rubric_file.exists():
                rubric_file.unlink()
            
            # Remove from metadata
            del self.metadata[unit_name]
            self._save_metadata()
