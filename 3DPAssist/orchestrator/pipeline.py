from __future__ import annotations

from typing import List

from schemas.rubric import RubricVersion
from schemas.output import (
    RunOutput,
    RunSummary,
    CriterionResult,
)
from orchestrator.validators import validate_run_output


class PipelineError(Exception):
    """
    Raised when the pipeline cannot complete a run.
    """
    pass


def build_and_validate_run(
    *,
    run_id: str,
    rubric_version: RubricVersion,
    artifact_set_id: str,
    results: List[CriterionResult],
    summary: RunSummary,
    inputs_hash: str,
    rubric_fingerprint: str,
    artifact_fingerprint: str,
    model_id: str,
    strictness_profile: str,
) -> RunOutput:
    """
    Assemble a RunOutput and enforce strict validation.

    At this stage:
    - results are assumed to already exist (no AI yet)
    - this function guarantees the output is rubric-complete and valid
    """

    output = RunOutput(
        run_id=run_id,
        rubric_id=rubric_version.rubric_id,
        rubric_version=rubric_version.version,
        artifact_set_id=artifact_set_id,
        results=results,
        summary=summary,
        inputs_hash=inputs_hash,
        rubric_fingerprint=rubric_fingerprint,
        artifact_fingerprint=artifact_fingerprint,
        model_id=model_id,
        strictness_profile=strictness_profile,
    )

    # Hard gate: nothing passes without validation
    validate_run_output(output, rubric_version)

    return output
