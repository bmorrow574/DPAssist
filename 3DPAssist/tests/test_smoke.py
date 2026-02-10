"""
Smoke test for 3DPAssist core.

Run with:
    python tests/test_smoke.py
"""

from schemas.rubric import (
    RubricCategory,
    RubricCriterion,
    RubricVersion,
    Rubric,
)
from schemas.output import (
    CriterionResult,
    CriterionStatus,
    ConfidenceLevel,
    EvidenceRef,
    EvidenceQuote,
    RunSummary,
)
from schemas.run import RunRequest
from orchestrator.pipeline import build_and_validate_run
from orchestrator.service import RunService


def main() -> None:
    # ---- Create a minimal rubric ----
    criterion = RubricCriterion(
        id="process.clarity",
        category="Process",
        title="Clear Process Description",
        descriptor="The student clearly explains their process.",
        max_points=5,
    )

    category = RubricCategory(
        name="Process",
        criteria=[criterion],
    )

    rubric_version = RubricVersion(
        rubric_id="demo_rubric",
        version="v1",
        title="Demo Rubric",
        categories=[category],
    )

    rubric = Rubric(
        rubric_id="demo_rubric",
        versions=[rubric_version],
        current_version="v1",
    )

    rubric.validate()

    # ---- Create valid evidence ----
    evidence = EvidenceQuote(
        text="I first sketched the idea, then iterated based on feedback.",
        ref=EvidenceRef(
            artifact_id="reflection.txt",
            source_name="reflection.txt",
            location="Paragraph 1",
        ),
    )

    result = CriterionResult(
        criterion_id="process.clarity",
        status=CriterionStatus.MEETS,
        score=5,
        max_points=5,
        confidence=ConfidenceLevel.HIGH,
        evidence=[evidence],
        feedback="Process is clearly explained.",
        what_to_add=[],
    )

    summary = RunSummary(
        strengths=["Clear explanation of process"],
        biggest_gaps=[],
        missing_artifacts=[],
        teacher_comment_draft="Strong work overall.",
    )

    # ---- Build run output through pipeline ----
    output = build_and_validate_run(
        run_id="run_001",
        rubric_version=rubric_version,
        artifact_set_id="artifact_set_001",
        results=[result],
        summary=summary,
        inputs_hash="demo_inputs",
        rubric_fingerprint=rubric_version.fingerprint(),
        artifact_fingerprint="demo_artifacts",
        model_id="no-model",
        strictness_profile="portfolios_strict_v1",
    )

    # ---- Store via service ----
    service = RunService()
    service.start_run(
        RunRequest(
            run_id="run_001",
            rubric_id="demo_rubric",
            rubric_version="v1",
            artifact_set_id="artifact_set_001",
        )
    )
    service.complete_run(output)

    stored = service.get_last_output()
    assert stored is not None, "Run was not stored"

    print("SUCCESS: Smoke test passed.")


if __name__ == "__main__":
    main()
