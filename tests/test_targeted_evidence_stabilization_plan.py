import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.stabilization.targeted_evidence_stabilization_plan import (
    build_blocked_actions_matrix,
    build_evidence_stabilization_priority_matrix,
    build_phase_17_execution_roadmap,
    build_residual_blocker_intake_matrix,
    build_stabilization_plan_summary,
    build_stabilization_plan_validation_checks,
    build_stabilization_success_criteria_matrix,
    build_stabilization_workstream_matrix,
    build_targeted_evidence_stabilization_plan,
    build_task_126_handoff_manifest,
    load_phase_16_closure,
    load_phase_16_closure_manifest,
    write_targeted_evidence_stabilization_plan_report,
)


def _phase_16_closure() -> dict:
    return {
        "phase_16_closure_run_id": "closure_run",
        "gatekeeper_re_evaluation_run_id": "re_gate_run",
        "pre_post_repair_comparison_run_id": "comparison_run",
        "controlled_re_run_trial_run_id": "trial_run",
        "re_run_input_package_run_id": "input_package_run",
        "re_run_re_gate_plan_run_id": "plan_run",
        "research_audit_trail_run_id": "audit_run",
        "final_gatekeeper_outcome": "hold_with_repair_progress",
        "final_progression_allowed": False,
        "final_persona_reviews_allowed": False,
        "remaining_blockers_matrix": [
            {
                "blocker_code": "progression_not_allowed",
                "blocker_label": "Progression not allowed",
                "severity": "critical",
                "blocker_status": "active",
                "proposed_next_phase_workstream": "phase_17_governance_controls",
            },
            {
                "blocker_code": "persona_review_not_allowed",
                "blocker_label": "Persona review not allowed",
                "severity": "critical",
                "blocker_status": "active",
                "proposed_next_phase_workstream": "phase_17_persona_review_block",
            },
            {
                "blocker_code": "evidence_still_unstable_or_not_progression_ready",
                "blocker_label": "Evidence still unstable",
                "severity": "high",
                "blocker_status": "active",
                "proposed_next_phase_workstream": "evidence_stabilization_plan",
            },
            {
                "blocker_code": "residual_benchmark_relative_uncertainty",
                "blocker_label": "Benchmark uncertainty",
                "severity": "high",
                "blocker_status": "active",
                "proposed_next_phase_workstream": "benchmark_relative_stabilization",
            },
            {
                "blocker_code": "residual_walk_forward_or_period_sensitivity",
                "blocker_label": "Walk-forward sensitivity",
                "severity": "high",
                "blocker_status": "active",
                "proposed_next_phase_workstream": "walk_forward_stabilization",
            },
            {
                "blocker_code": "residual_outlier_dependence",
                "blocker_label": "Outlier dependence",
                "severity": "high",
                "blocker_status": "active",
                "proposed_next_phase_workstream": "outlier_stabilization",
            },
            {
                "blocker_code": "residual_metadata_concentration",
                "blocker_label": "Metadata concentration",
                "severity": "moderate",
                "blocker_status": "active",
                "proposed_next_phase_workstream": "metadata_stabilization",
            },
            {
                "blocker_code": "residual_clean_warning_or_anchor_uncertainty",
                "blocker_label": "Clean warning anchor uncertainty",
                "severity": "moderate",
                "blocker_status": "active",
                "proposed_next_phase_workstream": "coverage_anchor_stabilization",
            },
            {
                "blocker_code": "residual_current_core_expanded_cohort_gap",
                "blocker_label": "Core expanded cohort gap",
                "severity": "high",
                "blocker_status": "active",
                "proposed_next_phase_workstream": "cohort_gap_stabilization",
            },
            {
                "blocker_code": "local_artifacts_only_limitation",
                "blocker_label": "Local artifacts limitation",
                "severity": "moderate",
                "blocker_status": "active",
                "proposed_next_phase_workstream": "local_artifact_governance",
            },
        ],
    }


def _write_fixture(outputs_root: Path) -> Path:
    closure = _phase_16_closure()
    root = outputs_root / "phase_16_closures"
    run_dir = root / closure["phase_16_closure_run_id"]
    run_dir.mkdir(parents=True)
    report_path = run_dir / "phase_16_closure.json"
    report_path.write_text(json.dumps(closure), encoding="utf-8")
    (root / "latest_phase_16_closure_manifest.json").write_text(
        json.dumps(
            {
                "phase_16_closure_run_id": closure["phase_16_closure_run_id"],
                "report_json_path": str(report_path),
            }
        ),
        encoding="utf-8",
    )
    return outputs_root


def _codes(rows: list[dict], key: str) -> set[str]:
    return {str(row[key]) for row in rows}


def test_loads_latest_phase_16_closure_manifest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_phase_16_closure_manifest(outputs_root=outputs_root)

    assert manifest["phase_16_closure_run_id"] == "closure_run"


def test_loads_explicit_phase_16_closure_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_phase_16_closure_manifest(
        outputs_root=outputs_root,
        phase_16_closure_run_id="closure_run",
    )
    report = load_phase_16_closure(
        outputs_root=outputs_root,
        phase_16_closure_run_id="closure_run",
    )

    assert manifest["final_gatekeeper_outcome"] == "hold_with_repair_progress"
    assert report["final_progression_allowed"] is False


def test_handles_missing_phase_16_closure_manifest(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_phase_16_closure_manifest(outputs_root=tmp_path)


def test_handles_missing_phase_16_closure_report(tmp_path: Path) -> None:
    root = tmp_path / "phase_16_closures"
    root.mkdir()
    (root / "latest_phase_16_closure_manifest.json").write_text(
        json.dumps({"phase_16_closure_run_id": "missing"}),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError):
        load_phase_16_closure(
            outputs_root=tmp_path,
            phase_16_closure_run_id="missing",
        )


def test_stabilization_plan_summary_is_created() -> None:
    summary = build_stabilization_plan_summary(
        stabilization_plan_run_id="plan_run",
        phase_16_closure=_phase_16_closure(),
    )

    assert summary["phase_id"] == 17
    assert summary["current_task_id"] == 125
    assert summary["prior_phase_final_gatekeeper_outcome"] == (
        "hold_with_repair_progress"
    )
    assert summary["prior_phase_final_progression_allowed"] is False
    assert summary["prior_phase_final_persona_reviews_allowed"] is False
    assert summary["plan_status"] == "completed"
    assert summary["recommended_next_task"].startswith("Task 126")


def test_residual_blocker_intake_matrix_has_required_blockers() -> None:
    rows = build_residual_blocker_intake_matrix(_phase_16_closure())

    codes = _codes(rows, "blocker_code")

    assert "progression_not_allowed" in codes
    assert "persona_review_not_allowed" in codes
    assert "evidence_still_unstable_or_not_progression_ready" in codes
    assert "residual_benchmark_relative_uncertainty" in codes
    assert "residual_walk_forward_or_period_sensitivity" in codes
    assert "residual_outlier_dependence" in codes
    assert "residual_metadata_concentration" in codes
    assert "local_artifacts_only_limitation" in codes


def test_stabilization_workstream_matrix_has_required_workstreams() -> None:
    rows = build_stabilization_workstream_matrix()

    codes = _codes(rows, "workstream_code")

    assert "WS1_benchmark_relative_stabilization" in codes
    assert "WS2_walk_forward_period_stability" in codes
    assert "WS3_outlier_dependence_control" in codes
    assert "WS4_clean_warning_anchor_stability" in codes
    assert "WS5_core_vs_expanded_cohort_alignment" in codes
    assert "WS6_metadata_concentration_resolution" in codes
    assert "WS7_local_artifact_limitations_review" in codes
    assert "WS8_gatekeeper_return_package_preparation" in codes


def test_evidence_stabilization_priority_matrix_has_required_areas() -> None:
    rows = build_evidence_stabilization_priority_matrix()

    codes = _codes(rows, "evidence_area")

    assert "benchmark_relative_evidence" in codes
    assert "walk_forward_stability" in codes
    assert "period_sensitivity" in codes
    assert "supportive_period_dependence" in codes
    assert "outlier_dependence" in codes
    assert "metadata_concentration" in codes


def test_phase_17_execution_roadmap_has_tasks_125_to_131() -> None:
    rows = build_phase_17_execution_roadmap()

    task_ids = {row["task_id"] for row in rows}

    assert {125, 126, 127, 128, 129, 130, 131}.issubset(task_ids)


def test_stabilization_success_criteria_matrix_has_required_criteria() -> None:
    rows = build_stabilization_success_criteria_matrix()

    codes = _codes(rows, "criteria_code")

    assert "benchmark_relative_uncertainty_bounded" in codes
    assert "walk_forward_instability_explained_or_reduced" in codes
    assert "outlier_dependence_bounded" in codes
    assert "metadata_concentration_disclosed_or_reduced" in codes
    assert "no_persona_review_until_gatekeeper_allows" in codes


def test_blocked_actions_matrix_has_required_blocks() -> None:
    rows = build_blocked_actions_matrix()

    codes = _codes(rows, "blocked_action_code")

    assert "investor_persona_review" in codes
    assert "buffett_review" in codes
    assert "munger_review" in codes
    assert "investor_decision_generation" in codes
    assert "company_ranking" in codes
    assert "investment_recommendation" in codes
    assert "trade_signal_generation" in codes


def test_task_126_handoff_manifest_is_created() -> None:
    handoff = build_task_126_handoff_manifest(
        stabilization_plan_run_id="plan_run",
        phase_16_closure_run_id="closure_run",
    )

    assert handoff["future_phase_id"] == 17
    assert handoff["future_task_id"] == 126
    assert handoff["readiness_status"] == "ready_to_build_residual_blocker_work_orders"
    assert handoff["execution_allowed_now"] is True


def test_stabilization_plan_validation_checks_are_created() -> None:
    rows = build_stabilization_plan_validation_checks()

    codes = _codes(rows, "check_code")

    assert "prior_gatekeeper_outcome_preserved" in codes
    assert "progression_not_allowed_preserved" in codes
    assert "persona_review_not_allowed_preserved" in codes
    assert "gatekeeper_not_rerun_in_task_125" in codes
    assert "repairs_not_executed_in_task_125" in codes
    assert "no_recommendation_outputs" in codes
    assert "no_network_calls" in codes
    assert all(row["status"] == "satisfied" for row in rows)


def test_build_targeted_evidence_stabilization_plan_report_has_sections() -> None:
    report = build_targeted_evidence_stabilization_plan(
        stabilization_plan_run_id="plan_run",
        generated_at="2026-06-18T12:00:00+00:00",
        phase_16_closure=_phase_16_closure(),
    )
    data = report.to_dict()

    assert data["stabilization_plan_summary"]
    assert data["residual_blocker_intake_matrix"]
    assert data["stabilization_workstream_matrix"]
    assert data["evidence_stabilization_priority_matrix"]
    assert data["phase_17_execution_roadmap"]
    assert data["stabilization_success_criteria_matrix"]
    assert data["blocked_actions_matrix"]
    assert data["task_126_handoff_manifest"]
    assert data["stabilization_plan_validation_checks"]


def test_write_targeted_evidence_stabilization_plan_report_writes_files(
    tmp_path: Path,
) -> None:
    outputs_root = _write_fixture(tmp_path)

    files = write_targeted_evidence_stabilization_plan_report(
        outputs_root=outputs_root,
        phase_16_closure_run_id="closure_run",
    )

    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.residual_blocker_csv_path.is_file()
    assert files.workstream_csv_path.is_file()
    assert files.priority_csv_path.is_file()
    assert files.roadmap_csv_path.is_file()
    assert files.success_criteria_csv_path.is_file()
    assert files.blocked_actions_csv_path.is_file()
    assert files.task_126_handoff_manifest_path.is_file()
    assert files.validation_checks_csv_path.is_file()
    assert files.latest_manifest_path.is_file()
    markdown = files.markdown_path.read_text(encoding="utf-8")
    assert "## Important Boundary" in markdown
    assert "## Where We Are Now" in markdown
    assert "## Residual Blocker Intake Matrix" in markdown
    assert "## Stabilization Workstream Matrix" in markdown
    assert "## Evidence Stabilization Priority Matrix" in markdown
    assert "## Phase 17 Execution Roadmap" in markdown
    assert "## Stabilization Success Criteria" in markdown
    assert "## Blocked Actions" in markdown
    assert "## Task 126 Handoff" in markdown
    assert "## What This Does Not Suggest" in markdown


def test_cli_works_with_explicit_phase_16_closure_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "define-targeted-evidence-stabilization-plan",
            "--phase-16-closure-run-id",
            "closure_run",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "stabilization_plan_run_id=" in result.output
    assert "prior_gatekeeper_outcome=hold_with_repair_progress" in result.output
    assert "persona_reviews_allowed=false" in result.output


def test_cli_works_with_auto_latest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "define-targeted-evidence-stabilization-plan",
            "--auto-latest",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "phase_16_closure_run_id=closure_run" in result.output
    assert "recommended_next_task=Task 126" in result.output
