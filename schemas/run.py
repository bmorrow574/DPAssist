from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any
import time
import hashlib


class RunMode(str, Enum):
    """
    Controls whether scoring is produced or feedback only.
    """
    FEEDBACK_ONLY = "feedback_only"
    SCORE_AND_FEEDBACK = "score_and_feedback"


class StrictnessProfile(str, Enum):
    """
    Defines how conservative the evaluator must be.
    """
    PORTFOLIOS_STRICT_V1 = "portfolios_strict_v1"


class RunStatus(str, Enum):
    """
    Lifecycle state of a run.
    """
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass(frozen=True)
class RunRequest:
    """
    Immutable description of what the UI is asking the orchestrator to run.
    """
    run_id: str
    rubric_id: str
    rubric_version: str
    artifact_set_id: str

    mode: RunMode = RunMode.FEEDBACK_ONLY
    strictness: StrictnessProfile = StrictnessProfile.PORTFOLIOS_STRICT_V1

    student_id: Optional[str] = None
    class_id: Optional[str] = None

    options: Dict[str, Any] = field(default_factory=dict)
    created_ts: float = field(default_factory=lambda: time.time())

    def validate(self) -> None:
        if not self.run_id.strip():
            raise ValueError("RunRequest missing run_id.")
        if not self.rubric_id.strip():
            raise ValueError("RunRequest missing rubric_id.")
        if not self.rubric_version.strip():
            raise ValueError("RunRequest missing rubric_version.")
        if not self.artifact_set_id.strip():
            raise ValueError("RunRequest missing artifact_set_id.")

    def inputs_hash(self) -> str:
        """
        Stable hash of run inputs for audit and caching.
        """
        parts = [
            self.run_id,
            self.rubric_id,
            self.rubric_version,
            self.artifact_set_id,
            self.mode.value,
            self.strictness.value,
            self.student_id or "",
            self.class_id or "",
            str(sorted(self.options.items(), key=lambda x: x[0])),
        ]
        return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


@dataclass
class RunRecord:
    """
    Mutable record owned by the orchestrator to track run progress.
    """
    request: RunRequest
    status: RunStatus = RunStatus.QUEUED
    started_ts: Optional[float] = None
    finished_ts: Optional[float] = None
    error: Optional[str] = None

    model_id: Optional[str] = None

    def mark_running(self) -> None:
        self.status = RunStatus.RUNNING
        self.started_ts = time.time()

    def mark_complete(self) -> None:
        self.status = RunStatus.COMPLETE
        self.finished_ts = time.time()

    def mark_failed(self, error: str) -> None:
        self.status = RunStatus.FAILED
        self.error = error
        self.finished_ts = time.time()
