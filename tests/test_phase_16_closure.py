import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.regate.phase_16_closure import (
    build_gatekeeper_outcome_summary,
    build_next_phase_recommendation_matrix,
    build_phase_16_closure,
    build_phase_16_closure_validation_checks,
    build_phase_closure_summary,
    build_phase_task_status_matrix,
    build_remaining_blockers_matrix,
    build_residual_risk_matrix,
    build_task_125_handoff_manifest,
    load_gatekeeper_re_evaluation,
    load_gatekeeper_re_evaluation_manifest,
    write_phase_16_closure_report,
)


def _gatekeeper_re_evaluation() -> dict:
    return {
        "gatekeeper_re_evaluation_run_id": "re_gate_run",
        "pre_post_repair_comparison_run_id": "comparison_run",
        "controlled_re_run_trial_run_id": "trial_run",
        "re_run_input_package_run_id": "input_package_run",
        "re_run_re_gate_plan_run_id": "plan_run",
        "research_audit_trail_run_id": "audit_run",
        "re_gate_decision_record": {
            "previous_gatekeeper_decision": "hold",
            "new_gatekeeper_outcome": "hold_with_repair_progress",
            "progression_allowed_after_re_evaluation": False,
            "persona_reviews_allowed_after_re_evaluation": False,
        },
    }


def _write_fixture(outputs_root: Path) -> Path:
    re_evaluation = _gatekeeper_re_evaluation()
    root = outputs_root / "gatekeeper_re_evaluations"
    run_dir = root / re_evaluation["gatekeeper_re_evaluation_run_id"]
    run_dir.mkdir(parents=True)
    report_path = run_dir / "gatekeeper_re_evaluation.json"
    report_path.write_text(json.dumps(re_evaluation), encoding="utf-8")
    (root / "latest_gatekeeper_re_evaluation_manifest.json").write_text(
        json.dumps(
            {
                "gatekeeper_re_evaluation_run_id": re_evaluation[
                    "gatekeeper_re_evaluation_run_id"
                ],
                "report_json_path": str(report_path),
            }
        ),
        encoding="utf-8",
    )
    return outputs_root


def _codes(rows: list[dict], key: str) -> set[str]:
    return {str(row[key]) for row in rows}


def test_loads_latest_gatekeeper_re_evaluation_manifest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_gatekeeper_re_evaluation_manifest(outputs_root=outputs_root)

    assert manifest["gatekeeper_re_evaluation_run_id"] == "re_gate_run"


def test_loads_explicit_gatekeeper_re_evaluation_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_gatekeeper_re_evaluation_manifest(
        outputs_root=outputs_root,
        gatekeeper_re_evaluation_run_id="re_gate_run",
    )
    report = load_gatekeeper_re_evaluation(
        outputs_root=outputs_root,
        gatekeeper_re_evaluation_run_id="re_gate_run",
    )

    assert manifest["controlled_re_run_trial_run_id"] == "trial_run"
    assert report["re_gate_decision_record"]["new_gatekeeper_outcome"] == (
        "hold_with_repair_progress"
    )


def test_handles_missing_gatekeeper_re_evaluation_manifest(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_gatekeeper_re_evaluation_manifest(outputs_root=tmp_path)


def test_handles_missing_gatekeeper_re_evaluation_report(tmp_path: Path) -> None:
    root = tmp_path / "gatekeeper_re_evaluations"
    root.mkdir()
    (root / "latest_gatekeeper_re_evaluation_manifest.json").write_text(
        json.dumps({"gatekeeper_re_evaluation_run_id": "missing"}),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError):
        load_gatekeeper_re_evaluation(
            outputs_root=tmp_path,
            gatekeeper_re_evaluation_run_id="missing",
        )


def test_phase_closure_summary_is_created() -> None:
    summary = build_phase_closure_summary(
        phase_16_closure_run_id="closure_run",
        gatekeeper_re_evaluation=_gatekeeper_re_evaluation(),
    )

    assert summary["current_task_id"] == 124
    assert summary["phase_completion_status"] == "completed"
    assert summary["final_gatekeeper_outcome"] == "hold_with_repair_progress"
    assert summary["final_progression_allowed"] is False
    assert summary["final_persona_reviews_allowed"] is False
    assert summary["recommended_next_phase_id"] == 17
    assert summary["recommended_next_phase_name"] == (
        "Targeted Evidence Stabilization Layer"
    )
    assert summary["recommended_next_task_id"] == 125
    assert summary["recommended_next_task_name"] == (
        "Define Targeted Evidence Stabilization Plan"
    )


def test_phase_task_status_matrix_includes_tasks_119_to_124() -> None:
    rows = build_phase_task_status_matrix(_gatekeeper_re_evaluation())

    task_ids = {row["task_id"] for row in rows}

    assert {119, 120, 121, 122, 123, 124}.issubset(task_ids)
    assert all(row["status"] == "completed" for row in rows)
    assert all(row["safety_boundary_preserved"] is True for row in rows)


def test_gatekeeper_outcome_summary_preserves_hold_with_repair_progress() -> None:
    summary = build_gatekeeper_outcome_summary(_gatekeeper_re_evaluation())

    assert summary["new_gatekeeper_outcome"] == "hold_with_repair_progress"
    assert summary["outcome_classification"] == "repair_progress_without_progression"
    assert summary["progression_allowed_after_re_evaluation"] is False
    assert summary["persona_reviews_allowed_after_re_evaluation"] is False


def test_remaining_blockers_matrix_has_required_blockers() -> None:
    rows = build_remaining_blockers_matrix(_gatekeeper_re_evaluation())

    codes = _codes(rows, "blocker_code")

    assert "progression_not_allowed" in codes
    assert "persona_review_not_allowed" in codes
    assert "evidence_still_unstable_or_not_progression_ready" in codes
    assert "residual_benchmark_relative_uncertainty" in codes
    assert "residual_walk_forward_or_period_sensitivity" in codes
    assert "residual_outlier_dependence" in codes
    assert "local_artifacts_only_limitation" in codes


def test_residual_risk_matrix_has_required_risks() -> None:
    rows = build_residual_risk_matrix()

    codes = _codes(rows, "risk_code")

    assert "false_progression_risk" in codes
    assert "premature_persona_review_risk" in codes
    assert "overreading_repair_progress_risk" in codes
    assert "governance_drift_risk" in codes


def test_next_phase_recommendation_matrix_has_required_recommendations() -> None:
    rows = build_next_phase_recommendation_matrix()

    codes = _codes(rows, "recommendation_code")

    assert "recommended_next_phase" in codes
    assert "first_task" in codes
    assert "why_not_persona_review" in codes
    assert "why_not_investor_agents" in codes
    assert "success_criteria_for_returning_to_gatekeeper" in codes


def test_task_125_handoff_manifest_is_created() -> None:
    handoff = build_task_125_handoff_manifest(
        phase_16_closure_run_id="closure_run",
        gatekeeper_re_evaluation_run_id="re_gate_run",
    )

    assert handoff["future_phase_id"] == 17
    assert handoff["future_task_id"] == 125
    assert handoff["readiness_status"] == (
        "ready_for_targeted_evidence_stabilization_planning"
    )
    assert handoff["execution_allowed_now"] is True


def test_phase_16_closure_validation_checks_are_created() -> None:
    rows = build_phase_16_closure_validation_checks()

    codes = _codes(rows, "check_code")

    assert "phase_16_marked_completed" in codes
    assert "final_gatekeeper_outcome_preserved" in codes
    assert "progression_not_allowed_preserved" in codes
    assert "persona_review_not_allowed_preserved" in codes
    assert "investor_agents_not_run" in codes
    assert "gatekeeper_not_rerun_in_task_124" in codes
    assert "no_recommendation_outputs" in codes
    assert "no_network_calls" in codes
    assert all(row["status"] == "satisfied" for row in rows)


def test_build_phase_16_closure_report_contains_required_sections() -> None:
    report = build_phase_16_closure(
        phase_16_closure_run_id="closure_run",
        generated_at="2026-06-18T12:00:00+00:00",
        gatekeeper_re_evaluation=_gatekeeper_re_evaluation(),
    )
    data = report.to_dict()

    assert data["phase_closure_summary"]
    assert data["phase_task_status_matrix"]
    assert data["gatekeeper_outcome_summary"]
    assert data["remaining_blockers_matrix"]
    assert data["residual_risk_matrix"]
    assert data["next_phase_recommendation_matrix"]
    assert data["task_125_handoff_manifest"]
    assert data["phase_16_closure_validation_checks"]
    assert data["final_persona_reviews_allowed"] is False


def test_write_phase_16_closure_report_writes_files(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    files = write_phase_16_closure_report(
        outputs_root=outputs_root,
        gatekeeper_re_evaluation_run_id="re_gate_run",
    )

    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.phase_task_status_csv_path.is_file()
    assert files.gatekeeper_outcome_summary_csv_path.is_file()
    assert files.remaining_blockers_csv_path.is_file()
    assert files.residual_risk_csv_path.is_file()
    assert files.next_phase_recommendation_csv_path.is_file()
    assert files.task_125_handoff_manifest_path.is_file()
    assert files.validation_checks_csv_path.is_file()
    assert files.latest_manifest_path.is_file()
    markdown = files.markdown_path.read_text(encoding="utf-8")
    assert "## Important Boundary" in markdown
    assert "## Where We Are Now" in markdown
    assert "## Phase Task Status Matrix" in markdown
    assert "## Gatekeeper Outcome Summary" in markdown
    assert "## Remaining Blockers" in markdown
    assert "## Residual Risks" in markdown
    assert "## Next Phase Recommendation" in markdown
    assert "## Task 125 Handoff" in markdown
    assert "## What This Does Not Suggest" in markdown


def test_cli_works_with_explicit_gatekeeper_re_evaluation_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "close-phase-16",
            "--gatekeeper-re-evaluation-run-id",
            "re_gate_run",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "phase_16_closure_run_id=" in result.output
    assert "final_gatekeeper_outcome=hold_with_repair_progress" in result.output
    assert "final_persona_reviews_allowed=false" in result.output


def test_cli_works_with_auto_latest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "close-phase-16",
            "--auto-latest",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "gatekeeper_re_evaluation_run_id=re_gate_run" in result.output
    assert "recommended_next_task=Task 125" in result.output
