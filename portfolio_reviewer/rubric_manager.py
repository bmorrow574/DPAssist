"""
Rubric manager - handles rubric storage and due-date associations.

Storage modes
─────────────
local  (default): rubric JSON + metadata stored in portfolio_reviewer/rubrics/
                  Used for local installation (Path A / LaunchAgent).
sheets:           rubric data stored in a dedicated Google Sheet tab.
                  Required for cloud deployment (Path B / Railway + Streamlit Cloud).
                  Set env var  RUBRIC_STORAGE=sheets  to activate.
"""
import os
import sys
from pathlib import Path

# Add parent directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

import json
from datetime import datetime
from typing import Dict, List, Optional

from schemas.rubric import RubricVersion, RubricCategory, RubricCriterion, CriterionLevel
from config import config


class RubricManager:
    """Manage rubrics and their associated due dates.

    Instantiate with an optional ``sheets_client`` to enable cloud storage.
    Alternatively, set the ``RUBRIC_STORAGE=sheets`` environment variable and
    pass no argument — the manager will lazily open its own Sheets connection.
    """

    def __init__(self, sheets_client=None):
        self._sheets_client_arg = sheets_client
        self._sheets_client_lazy = None

        # Determine storage mode
        use_sheets_env = os.getenv('RUBRIC_STORAGE', 'local').lower() == 'sheets'
        self._use_sheets = (sheets_client is not None) or use_sheets_env

        if not self._use_sheets:
            # ── Local file storage (original behaviour, fully preserved) ──
            self.rubrics_dir = config.RUBRICS_DIR
            self.rubrics_dir.mkdir(exist_ok=True)
            self.metadata_file = self.rubrics_dir / 'rubrics_metadata.json'
            self.metadata = self._load_metadata()

    # ------------------------------------------------------------------
    # Sheets client (lazy singleton for the "sheets" mode)
    # ------------------------------------------------------------------

    @property
    def _sheets(self):
        if self._sheets_client_arg is not None:
            return self._sheets_client_arg
        if self._sheets_client_lazy is None:
            from google_sheets import GoogleSheetsClient
            self._sheets_client_lazy = GoogleSheetsClient()
        return self._sheets_client_lazy

    # ------------------------------------------------------------------
    # Public API (same interface regardless of storage mode)
    # ------------------------------------------------------------------

    def add_rubric(
        self,
        rubric: RubricVersion,
        unit_name: str,
        due_date: str,
        pdf_path: Optional[Path] = None,
    ):
        """Add or replace a rubric with metadata."""
        if self._use_sheets:
            self._sheets.save_rubric_to_sheet(unit_name, rubric.title, due_date, rubric)
        else:
            self._add_rubric_local(rubric, unit_name, due_date, pdf_path)

    def get_rubric_for_unit(self, unit_name: str) -> Optional[RubricVersion]:
        """Return the RubricVersion for a unit, or None."""
        if self._use_sheets:
            return self._get_rubric_from_sheets(unit_name)
        return self._get_rubric_local(unit_name)

    def get_due_date(self, unit_name: str) -> Optional[datetime]:
        """Return the due date for a unit, or None."""
        if self._use_sheets:
            record = self._get_sheets_record(unit_name)
            if not record:
                return None
            return self._parse_date(record.get('due_date', ''))
        if unit_name not in self.metadata:
            return None
        return self._parse_date(self.metadata[unit_name]['due_date'])

    def is_past_due(self, unit_name: str) -> bool:
        """Return True if the unit's due date has passed."""
        due_date = self.get_due_date(unit_name)
        if not due_date:
            return False
        return datetime.now() > due_date

    def list_units(self) -> List[Dict]:
        """Return all configured units with metadata."""
        if self._use_sheets:
            return self._list_units_sheets()
        return self._list_units_local()

    def delete_rubric(self, unit_name: str):
        """Delete a rubric configuration."""
        if self._use_sheets:
            self._sheets.delete_rubric_from_sheet(unit_name)
        else:
            self._delete_rubric_local(unit_name)

    # ------------------------------------------------------------------
    # Google Sheets backend
    # ------------------------------------------------------------------

    def _get_sheets_record(self, unit_name: str) -> Optional[Dict]:
        records = self._sheets.get_all_rubrics_from_sheet()
        for r in records:
            if r.get('unit_name') == unit_name:
                return r
        return None

    def _get_rubric_from_sheets(self, unit_name: str) -> Optional[RubricVersion]:
        record = self._get_sheets_record(unit_name)
        if not record:
            return None
        rubric_data = record.get('rubric_data', {})
        if not rubric_data:
            return None
        return self._dict_to_rubric_version(rubric_data)

    def _list_units_sheets(self) -> List[Dict]:
        records = self._sheets.get_all_rubrics_from_sheet()
        units = []
        for r in records:
            due_date = self._parse_date(r.get('due_date', ''))
            units.append({
                'unit_name': r['unit_name'],
                'title': r.get('title', ''),
                'due_date': r.get('due_date', ''),
                'is_past_due': datetime.now() > due_date if due_date else False,
                'rubric_id': r.get('rubric_data', {}).get('rubric_id', ''),
            })
        return units

    # ------------------------------------------------------------------
    # Local file backend (original logic, preserved exactly)
    # ------------------------------------------------------------------

    def _load_metadata(self) -> Dict:
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_metadata(self):
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def _add_rubric_local(
        self,
        rubric: RubricVersion,
        unit_name: str,
        due_date: str,
        pdf_path: Optional[Path],
    ):
        rubric_id = rubric.rubric_id
        rubric_file = self.rubrics_dir / f"{rubric_id}.json"

        rubric_data: Dict = {
            'rubric_id': rubric.rubric_id,
            'version': rubric.version,
            'title': rubric.title,
            'categories': [],
        }
        for cat in rubric.categories:
            cat_data: Dict = {'name': cat.name, 'criteria': []}
            for crit in cat.criteria:
                crit_data: Dict = {
                    'id': crit.id,
                    'category': crit.category,
                    'title': crit.title,
                    'descriptor': crit.descriptor,
                    'max_points': crit.max_points,
                    'levels': [
                        {'label': lvl.label, 'descriptor': lvl.descriptor, 'points': lvl.points}
                        for lvl in crit.levels
                    ],
                }
                cat_data['criteria'].append(crit_data)
            rubric_data['categories'].append(cat_data)

        with open(rubric_file, 'w') as f:
            json.dump(rubric_data, f, indent=2)

        self.metadata[unit_name] = {
            'rubric_id': rubric_id,
            'title': rubric.title,
            'due_date': due_date,
            'pdf_path': str(pdf_path) if pdf_path else None,
            'created': datetime.now().isoformat(),
        }
        self._save_metadata()

    def _get_rubric_local(self, unit_name: str) -> Optional[RubricVersion]:
        if unit_name not in self.metadata:
            return None
        rubric_id = self.metadata[unit_name]['rubric_id']
        rubric_file = self.rubrics_dir / f"{rubric_id}.json"
        if not rubric_file.exists():
            return None
        with open(rubric_file, 'r') as f:
            data = json.load(f)
        return self._dict_to_rubric_version(data)

    def _list_units_local(self) -> List[Dict]:
        units = []
        for unit_name, meta in self.metadata.items():
            due_date = self._parse_date(meta['due_date'])
            units.append({
                'unit_name': unit_name,
                'title': meta['title'],
                'due_date': meta['due_date'],
                'is_past_due': datetime.now() > due_date if due_date else False,
                'rubric_id': meta['rubric_id'],
            })
        return units

    def _delete_rubric_local(self, unit_name: str):
        if unit_name not in self.metadata:
            return
        rubric_id = self.metadata[unit_name]['rubric_id']
        rubric_file = self.rubrics_dir / f"{rubric_id}.json"
        if rubric_file.exists():
            rubric_file.unlink()
        del self.metadata[unit_name]
        self._save_metadata()

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_date(date_str: str) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except Exception:
            return None

    @staticmethod
    def _dict_to_rubric_version(data: dict) -> RubricVersion:
        """Reconstruct a RubricVersion from a plain dict (local JSON or Sheets)."""
        categories = []
        for cat_data in data.get('categories', []):
            criteria = []
            for crit_data in cat_data.get('criteria', []):
                levels = [
                    CriterionLevel(
                        label=lvl['label'],
                        descriptor=lvl['descriptor'],
                        points=lvl.get('points'),
                    )
                    for lvl in crit_data.get('levels', [])
                ]
                criteria.append(RubricCriterion(
                    id=crit_data['id'],
                    category=crit_data.get('category', cat_data['name']),
                    title=crit_data['title'],
                    descriptor=crit_data.get('descriptor', ''),
                    max_points=crit_data.get('max_points'),
                    levels=levels,
                ))
            categories.append(RubricCategory(name=cat_data['name'], criteria=criteria))

        return RubricVersion(
            rubric_id=data['rubric_id'],
            version=data.get('version', 'v1'),
            title=data['title'],
            categories=categories,
        )
