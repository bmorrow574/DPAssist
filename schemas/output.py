from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
import time


class CriterionStatus(str, Enum):
    """
    Evaluation status for a single rubric criterion.
    """
    MEETS = "meets"
    PARTIALLY_MEETS = "partially_meets"
    NOT_YET = "not_yet"


class ConfidenceLevel(str, Enum):
    """
    How confident the system is in its judgment, based on evidence coverage.
    """
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class EvidenceRef:
    """
    Strict reference to where evidence was found.
    This prevents hallucinated evidence.
    """
    artifact_id: str
    source_name: str
    location: str = ""  # e.g., paragraph, page, section


@dataclass(frozen=True)
class EvidenceQuote:
    """
    Short, direct quote or excerpt from an artifact.
    """
    text: str
    ref: EvidenceRef


@dataclass(frozen=True)
class CriterionResult:
    """
    Result of evaluating one rubric criterion.
    """
    criterion_id: str
    status: CriterionStatus

    score: Optional[float] = None
    max_points: Optional[float] = None

    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

    evidence: List[EvidenceQuote] = field(default_factory=list)
    feedback: str = ""
    what_to_add: List[str] = field(default_factory=list)

    flags: List[str] = field(default_factory=list)

    def validate(self) -> None:
        if not self.criterion_id.strip():
            raise ValueError("CriterionResult missing criterion_id.")

        if self.status in (CriterionStatus.MEETS, CriterionStatus.PARTIALLY_MEETS):
            if not self.evidence:
                raise ValueError(
                    f"CriterionResult '{self.criterion_id}' requires evidence for status '{self.status.value}'."
                )

        if self.score is not None and self.max_points is not None:
            if self.score < 0 or self.score > self.max_points:
                raise ValueError(
                    f"CriterionResult '{self.criterion_id}' score out of range."
                )


@dataclass(frozen=True)
class RunSummary:
    """
    Teacher-facing synthesis of the run.
    """
    strengths: List[str] = field(default_factory=list)
    biggest_gaps: List[str] = field(default_factory=list)
    missing_artifacts: List[str] = field(default_factory=list)

    teacher_comment_draft: str = ""


@dataclass(frozen=True)
class RunOutput:
    """
    Complete output of a single evaluation run.
    """
    run_id: str
    rubric_id: str
    rubric_version: str
    artifact_set_id: str

    results: List[CriterionResult]
    summary: RunSummary

    created_ts: float = field(default_factory=lambda: time.time())

    inputs_hash: str = ""
    rubric_fingerprint: str = ""
    artifact_fingerprint: str = ""
    model_id: str = ""
    strictness_profile: str = ""

    meta: Dict[str, Any] = field(default_factory=dict)

    def validate(self, expected_criterion_ids: Optional[List[str]] = None) -> None:
        if not self.run_id.strip():
            raise ValueError("RunOutput missing run_id.")
        if not self.results:
            raise ValueError("RunOutput must contain results.")

        seen = set()
        for r in self.results:
            r.validate()
            if r.criterion_id in seen:
                raise ValueError(f"Duplicate result for criterion '{r.criterion_id}'.")
            seen.add(r.criterion_id)

        if expected_criterion_ids is not None:
            missing = [cid for cid in expected_criterion_ids if cid not in seen]
            extra = [cid for cid in seen if cid not in expected_criterion_ids]
            if missing:
                raise ValueError(f"RunOutput missing criteria: {missing}")
            if extra:
                raise ValueError(f"RunOutput contains unknown criteria: {extra}")
