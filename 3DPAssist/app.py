import streamlit as st

from schemas.rubric import RubricCategory, RubricCriterion, RubricVersion, Rubric
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


def build_demo_rubric() -> RubricVersion:
    criterion = RubricCriterion(
        id="process.clarity",
        category="Process",
        title="Clear Process Description",
        descriptor="The student clearly explains their process.",
        max_points=5,
    )

    category = RubricCategory(name="Process", criteria=[criterion])

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
    return rubric_version


def build_demo_output(rubric_version: RubricVersion):
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

    output = build_and_validate_run(
        run_id="run_demo_001",
        rubric_version=rubric_version,
        artifact_set_id="artifact_set_demo_001",
        results=[result],
        summary=summary,
        inputs_hash="demo_inputs",
        rubric_fingerprint=rubric_version.fingerprint(),
        artifact_fingerprint="demo_artifacts",
        model_id="no-model",
        strictness_profile="portfolios_strict_v1",
    )
    return output


def get_service() -> RunService:
    if "run_service" not in st.session_state:
        st.session_state.run_service = RunService()
    return st.session_state.run_service


st.set_page_config(page_title="3DPAssist (Demo)", layout="wide")
st.title("3DPAssist — Minimal Demo (No AI)")

service = get_service()

# Build rubric for preview (same demo rubric)
rubric_version_for_preview = build_demo_rubric()

with st.sidebar:
    st.header("Demo Controls")

    strictness_demo = st.checkbox(
        "Strictness demo (intentionally invalid run)",
        value=False,
    )

    if st.button("Run Demo Evaluation", type="primary"):
        rubric_version = build_demo_rubric()

        service.start_run(
            RunRequest(
                run_id="run_demo_001" if not strictness_demo else "run_demo_BAD_001",
                rubric_id=rubric_version.rubric_id,
                rubric_version=rubric_version.version,
                artifact_set_id="artifact_set_demo_001",
            )
        )

        try:
            if strictness_demo:
                # Intentionally INVALID: MEETS with no evidence -> should fail validation
                bad_result = CriterionResult(
                    criterion_id="process.clarity",
                    status=CriterionStatus.MEETS,
                    score=5,
                    max_points=5,
                    confidence=ConfidenceLevel.HIGH,
                    evidence=[],  # invalid on purpose
                    feedback="This should be blocked by validators.",
                    what_to_add=[],
                )

                bad_summary = RunSummary(
                    strengths=[],
                    biggest_gaps=["This run is intentionally invalid"],
                    missing_artifacts=[],
                    teacher_comment_draft="(invalid)",
                )

                output = build_and_validate_run(
                    run_id="run_demo_BAD_001",
                    rubric_version=rubric_version,
                    artifact_set_id="artifact_set_demo_001",
                    results=[bad_result],
                    summary=bad_summary,
                    inputs_hash="demo_inputs_bad",
                    rubric_fingerprint=rubric_version.fingerprint(),
                    artifact_fingerprint="demo_artifacts",
                    model_id="no-model",
                    strictness_profile="portfolios_strict_v1",
                )
            else:
                output = build_demo_output(rubric_version)

            service.complete_run(output)
            st.success("Demo evaluation completed and stored.")

        except Exception as e:
            service.fail_run(str(e))
            st.error(f"Run blocked (as intended): {e}")

    if st.button("Clear Stored Output"):
        st.session_state.pop("run_service", None)
        st.success("Cleared. Reloaded service on next interaction.")


# --- Rubric preview (teacher-facing) ---
st.subheader("Rubric Preview (Demo)")

with st.expander(
    f"{rubric_version_for_preview.title} — "
    f"{rubric_version_for_preview.rubric_id}:{rubric_version_for_preview.version}",
    expanded=False,
):
    for cat in rubric_version_for_preview.categories:
        st.write(f"### {cat.name}")
        for c in cat.criteria:
            pts = f" (Max {c.max_points})" if c.max_points is not None else ""
            st.write(f"- **{c.id}**: {c.title}{pts}")
            st.caption(c.descriptor)

st.divider()

# --- Output display ---
st.subheader("Latest Stored Output")

last = service.get_last_output()
if last is None:
    st.info("No output stored yet. Click **Run Demo Evaluation** in the sidebar.")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Run ID", last.run_id)
col2.metric("Rubric Version", f"{last.rubric_id}:{last.rubric_version}")
col3.metric("Artifact Set", last.artifact_set_id)

st.divider()

st.subheader("Criterion Results")

for r in last.results:
    with st.expander(
        f"{r.criterion_id} — {r.status.value} ({r.confidence.value})",
        expanded=True,
    ):
        if r.score is not None and r.max_points is not None:
            st.write(f"**Score:** {r.score} / {r.max_points}")

        st.write("**Feedback**")
        st.write(r.feedback or "(none)")

        st.write("**Evidence**")
        if not r.evidence:
            st.write("(none)")
        else:
            for ev in r.evidence:
                st.code(ev.text)
                st.caption(
                    f"{ev.ref.source_name} • {ev.ref.artifact_id} • {ev.ref.location}"
                )

        st.write("**What to add**")
        if not r.what_to_add:
            st.write("(none)")
        else:
            for item in r.what_to_add:
                st.write(f"- {item}")

st.divider()
st.subheader("Summary")
st.write("**Strengths**")
st.write("\n".join([f"- {s}" for s in last.summary.strengths]) or "(none)")

st.write("**Biggest gaps**")
st.write("\n".join([f"- {g}" for g in last.summary.biggest_gaps]) or "(none)")

st.write("**Missing artifacts**")
st.write("\n".join([f"- {m}" for m in last.summary.missing_artifacts]) or "(none)")

st.write("**Teacher comment draft**")
st.write(last.summary.teacher_comment_draft or "(none)")
