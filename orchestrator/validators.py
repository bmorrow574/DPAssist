from __future__ import annotations

from typing import List

from schemas.output import (
    CriterionResult,
    CriterionStatus,
    ConfidenceLevel,
    RunOutput,
)
from schemas.rubric import RubricVersion


class ValidationError(Exception):
    """
    Raised when a run output violates strictness rules.
    """
    pass


def validate_criterion_result(result: CriterionResult) -> None:
    """
    Enforce strict, PortfoliOS-style rules on a single criterion result.
    """

    # Rule 1: Meets / Partially Meets require evidence
    if result.status in (
        CriterionStatus.MEETS,
        CriterionStatus.PARTIALLY_MEETS,
    ):
        if not result.evidence:
            raise ValidationError(
                f"Criterion '{result.criterion_id}' marked as '{result.status.value}' "
                f"but contains no evidence."
            )

    # Rule 2: NOT_YET should not include evidence
    if result.status == CriterionStatus.NOT_YET and result.evidence:
        raise ValidationError(
            f"Criterion '{result.criterion_id}' marked as NOT_YET "
            f"but includes evidence."
        )

    # Rule 3: Low confidence must not be marked as MEETS
    if (
        result.status == CriterionStatus.MEETS
        and result.confidence == ConfidenceLevel.LOW
    ):
        raise ValidationError(
            f"Criterion '{result.criterion_id}' marked as MEETS "
            f"with LOW confidence."
        )


def validate_run_output(
    output: RunOutput,
    rubric_version: RubricVersion,
) -> None:
    """
    Validate a complete run output against the rubric and strictness rules.
    """

    # Rule 4: Every rubric criterion must appear exactly once
    expected_ids = {c.id for c in rubric_version.all_criteria()}
    actual_ids = {r.criterion_id for r in output.results}

    missing = expected_ids - actual_ids
    extra = actual_ids - expected_ids

    if missing:
        raise ValidationError(
            f"RunOutput missing rubric criteria: {sorted(missing)}"
        )

    if extra:
        raise ValidationError(
            f"RunOutput contains unknown criteria: {sorted(extra)}"
        )

    # Rule 5: Validate each criterion result
    for result in output.results:
        validate_criterion_result(result)
