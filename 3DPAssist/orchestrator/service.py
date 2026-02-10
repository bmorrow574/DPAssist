from __future__ import annotations

from typing import Optional

from schemas.run import (
    RunRequest,
    RunRecord,
    RunStatus,
)
from schemas.output import RunOutput
from orchestrator.storage import InMemoryStorage



class ServiceError(Exception):
    """
    Raised when a run cannot be managed correctly.
    """
    pass


class RunService:
    """
    Minimal run lifecycle manager.

    This class does NOT:
    - call an LLM
    - inspect artifacts
    - modify outputs

    It only tracks state and ownership of a run.
    """

    def __init__(self) -> None:
        self._current_run: Optional[RunRecord] = None
        self._last_output: Optional[RunOutput] = None
        self._storage = InMemoryStorage()


    def start_run(self, request: RunRequest) -> None:
        if self._current_run is not None:
            raise ServiceError("A run is already in progress.")

        record = RunRecord(request=request)
        record.mark_running()
        self._current_run = record

    def complete_run(self, output: RunOutput) -> None:
        if self._current_run is None:
            raise ServiceError("No active run to complete.")

        self._current_run.mark_complete()
        self._storage.save_run(output)
        self._last_output = output
        self._current_run = None


    def fail_run(self, error: str) -> None:
        if self._current_run is None:
            raise ServiceError("No active run to fail.")

        self._current_run.mark_failed(error)
        self._current_run = None

    def get_status(self) -> Optional[RunStatus]:
        if self._current_run is None:
            return None
        return self._current_run.status

    def get_last_output(self) -> Optional[RunOutput]:
        return self._last_output
