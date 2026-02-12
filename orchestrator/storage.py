from __future__ import annotations

from typing import Optional, Dict

from schemas.output import RunOutput


class StorageError(Exception):
    """
    Raised when storage operations fail.
    """
    pass


class InMemoryStorage:
    """
    Minimal, in-memory storage for runs.

    This is intentionally simple:
    - survives only while the app is running
    - perfect for early Streamlit development
    - easy to replace later with file/db storage
    """

    def __init__(self) -> None:
        self._runs: Dict[str, RunOutput] = {}

    def save_run(self, output: RunOutput) -> None:
        if not output.run_id:
            raise StorageError("Cannot store run without run_id.")
        self._runs[output.run_id] = output

    def get_run(self, run_id: str) -> Optional[RunOutput]:
        return self._runs.get(run_id)

    def list_runs(self) -> Dict[str, RunOutput]:
        """
        Return all stored runs keyed by run_id.
        """
        return dict(self._runs)
