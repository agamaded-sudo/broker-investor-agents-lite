import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.stabilization.gatekeeper_stabilized_evidence_comparison import (
    build_comparison_summary,
    build_evidence_state_delta_matrix,
    build_gatekeeper_blocker_comparison_matrix,
    build_gatekeeper_return_readiness_matrix,
    build_gatekeeper_stabilized_comparison_checks,
    build_gatekeeper_stabilized_evidence_comparison,
    build_residual_risk_comparison_matrix,
    build_task_130_handoff_manifest,
    load_gatekeeper_re_evaluation,
    load_stabilization_validation_trial,
    load_stabilization_validation_trial_manifest,
    write_gatekeeper_stabilized_evidence_comparison_report,
)


def _stabilization_validation() -> dict:
    evidence_areas = [
        ("benchmark_relative_evidence", "WO-126-001"),
        ("walk_forward_stability", "WO-126-002"),
        ("period_sensitivity", "WO-126-002"),
        ("supportive_period_dependence", "WO-126-003"),
        ("outlier_dependence", "WO-126-003"),
        ("clean_warning_split", "WO-126-004"),
        ("anchor_split", "WO-126-004"),
        ("current_core_vs_expanded_cohort", "WO-126-005"),
        ("metadata_concentration", "WO-126-006"),
        ("local_artifact_completeness", "WO-126-007"),
        ("gatekeeper_return_package", "WO-126-008"),
    ]
    uncertainties = [
        ("benchmark_relative_uncertainty", "benchmark_relative_evidence", "high"),
        ("walk_forward_period_sensitivity", "walk_forward_stability", "high"),
        ("supportive_period_dependence", "supportive_period_dependence", "high"),
        ("outlier_dependence", "outlier_dependence", "high"),
        ("clean_warning_anchor_gap", "clean_warning_split", "medium"),
        ("core_vs_expanded_gap", "current_core_vs_expanded_cohort", "high"),
        ("metadata_concentration", "metadata_concentration", "medium"),
        ("local_artifact_only_limitation", "local_artifact_completeness", "medium"),
        ("partial_repair_completion", "all_repaired_evidence", "medium"),
        ("no_gatekeeper_rerun_yet", "governance_state", "critical"),
    ]
    return {
        "stabilization_validation_run_id": "validation_run",
        "targeted_repair_run_id": "repair_run",
        "residual_work_order_package_run_id": "work_order_run",
        "stabilization_plan_run_id": "plan_run",
        "phase_16_closure_run_id": "closure_run",
        "gatekeeper_re_evaluation_run_id": "re_gate_run",
        "pre_post_repair_comparison_run_id": "comparison_run",
        "controlled_re_run_trial_run_id": "trial_run",
        "re_run_input_package_run_id": "input_package_run",
        "re_run_re_gate_plan_run_id": "re_gate_plan_run",
        "research_audit_trail_run_id": "audit_run",
        "validation_trial_summary": {
            "prior_gatekeeper_outcome": "hold_with_repair_progress",
            "progression_allowed": False,
            "persona_reviews_allowed": False,
            "validation_trial_status": "completed",
        },
        "evidence_area_validation_matrix": [
            {
                "evidence_area": area,
                "linked_work_order_id": work_order_id,
                "pre_repair_issue": "Residual blocker from Phase 16 closure.",
                "task_127_repair_finding": "Validation-ready, not cleared.",
                "validation_status": "validated_with_warnings",
                "validation_result": "bounded_uncertainty",
                "stabilization_effect": "validation_ready_not_progression_ready",
                "remaining_blocker": "Task 130 re-review required.",
                "task_129_comparison_input": f"{area}_validated_input",
                "safety_boundary": "Evidence validation only.",
            }
            for area, work_order_id in evidence_areas
        ],
        "residual_uncertainty_matrix": [
            {
                "uncertainty_code": code,
                "linked_evidence_area": area,
                "uncertainty_status": "documented_for_task_129",
                "severity": severity,
                "source": "targeted_evidence_repairs",
                "impact_on_task_129": "Carry into Task 129 comparison.",
                "required_follow_up": "Carry into Task 130.",
                "safety_boundary": "Uncertainty documentation only.",
            }
            for code, area, severity in uncertainties
        ],
    }


def _gatekeeper_re_evaluation() -> dict:
    return {
        "gatekeeper_re_evaluation_run_id": "re_gate_run",
        "re_evaluation_summary": {
            "new_gatekeeper_outcome": "hold_with_repair_progress",
            "progression_allowed_after_re_evaluation": False,
            "persona_reviews_allowed_after_re_evaluation": False,
        },
        "re_gate_decision_record": {
            "new_gatekeeper_outcome": "hold_with_repair_progress",
            "progression_allowed_after_re_evaluation": False,
            "persona_reviews_allowed_after_re_evaluation": False,
        },
    }


def _write_fixture(outputs_root: Path) -> Path:
    validation = _stabilization_validation()
    gatekeeper = _gatekeeper_re_evaluation()
    validation_root = outputs_root / "stabilization_validation_trials"
    validation_dir = validation_root / validation["stabilization_validation_run_id"]
    validation_dir.mkdir(parents=True)
    validation_path = validation_dir / "stabilization_validation_trial.json"
    validation_path.write_text(json.dumps(validation), encoding="utf-8")
    (validation_root / "latest_stabilization_validation_trial_manifest.json").write_text(
        json.dumps(
            {
                "stabilization_validation_run_id": validation[
                    "stabilization_validation_run_id"
                ],
                "report_json_path": str(validation_path),
            }
        ),
        encoding="utf-8",
    )
    gatekeeper_dir = (
        outputs_root
        / "gatekeeper_re_evaluations"
        / gatekeeper["gatekeeper_re_evaluation_run_id"]
    )
    gatekeeper_dir.mkdir(parents=True)
    (gatekeeper_dir / "gatekeeper_re_evaluation.json").write_text(
        json.dumps(gatekeeper),
        encoding="utf-8",
    )
    return outputs_root


def _codes(rows: list[dict], key: str) -> set[str]:
    return {str(row[key]) for row in rows}


def test_loads_latest_stabilization_validation_manifest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_stabilization_validation_trial_manifest(outputs_root=outputs_root)

    assert manifest["stabilization_validation_run_id"] == "validation_run"


def test_loads_explicit_stabilization_validation_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_stabilization_validation_trial_manifest(
        outputs_root=outputs_root,
        stabilization_validation_run_id="validation_run",
    )
    report = load_stabilization_validation_trial(
        outputs_root=outputs_root,
        stabilization_validation_run_id="validation_run",
    )

    assert manifest["gatekeeper_re_evaluation_run_id"] == "re_gate_run"
    assert report["stabilization_validation_run_id"] == "validation_run"


def test_supports_explicit_gatekeeper_re_evaluation_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    report = load_gatekeeper_re_evaluation(
        outputs_root=outputs_root,
        gatekeeper_re_evaluation_run_id="re_gate_run",
    )

    assert report["gatekeeper_re_evaluation_run_id"] == "re_gate_run"


def test_handles_missing_stabilization_validation_manifest(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_stabilization_validation_trial_manifest(outputs_root=tmp_path)


def test_handles_missing_stabilization_validation_report(tmp_path: Path) -> None:
    root = tmp_path / "stabilization_validation_trials"
    root.mkdir()
    (root / "latest_stabilization_validation_trial_manifest.json").write_text(
        json.dumps({"stabilization_validation_run_id": "missing"}),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError):
        load_stabilization_validation_trial(
            outputs_root=tmp_path,
            stabilization_validation_run_id="missing",
        )


def test_handles_missing_gatekeeper_re_evaluation_report(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_gatekeeper_re_evaluation(
            outputs_root=tmp_path,
            gatekeeper_re_evaluation_run_id="missing",
        )


def test_comparison_summary_is_created() -> None:
    blocker_rows = build_gatekeeper_blocker_comparison_matrix(
        _stabilization_validation(),
        _gatekeeper_re_evaluation(),
    )

    summary = build_comparison_summary(
        gatekeeper_stabilized_comparison_run_id="comparison_run",
        stabilization_validation=_stabilization_validation(),
        gatekeeper_re_evaluation=_gatekeeper_re_evaluation(),
        blocker_rows=blocker_rows,
    )

    assert summary["phase_id"] == 17
    assert summary["current_task_id"] == 129
    assert summary["task_123_gatekeeper_outcome"] == "hold_with_repair_progress"
    assert summary["progression_allowed"] is False
    assert summary["persona_reviews_allowed"] is False
    assert summary["comparison_status"] == "completed"
    assert summary["recommended_next_task"].startswith("Task 130")


def test_gatekeeper_blocker_comparison_matrix_has_required_blockers() -> None:
    rows = build_gatekeeper_blocker_comparison_matrix(
        _stabilization_validation(),
        _gatekeeper_re_evaluation(),
    )

    codes = _codes(rows, "blocker_code")

    assert "progression_not_allowed" in codes
    assert "persona_review_not_allowed" in codes
    assert "evidence_still_unstable_or_not_progression_ready" in codes
    assert "residual_benchmark_relative_uncertainty" in codes
    assert "residual_walk_forward_or_period_sensitivity" in codes
    assert "residual_outlier_dependence" in codes
    assert "residual_metadata_concentration" in codes
    assert "residual_clean_warning_or_anchor_uncertainty" in codes
    assert "residual_current_core_expanded_cohort_gap" in codes
    assert "local_artifacts_only_limitation" in codes


def test_evidence_state_delta_matrix_has_required_areas() -> None:
    rows = build_evidence_state_delta_matrix(_stabilization_validation())

    areas = _codes(rows, "evidence_area")

    assert "benchmark_relative_evidence" in areas
    assert "walk_forward_stability" in areas
    assert "period_sensitivity" in areas
    assert "supportive_period_dependence" in areas
    assert "outlier_dependence" in areas
    assert "clean_warning_split" in areas
    assert "anchor_split" in areas
    assert "current_core_vs_expanded_cohort" in areas
    assert "metadata_concentration" in areas
    assert "local_artifact_completeness" in areas
    assert "gatekeeper_return_package" in areas


def test_residual_risk_comparison_matrix_has_required_risks() -> None:
    rows = build_residual_risk_comparison_matrix(_stabilization_validation())

    codes = _codes(rows, "risk_code")

    assert "benchmark_relative_uncertainty" in codes
    assert "walk_forward_period_sensitivity" in codes
    assert "supportive_period_dependence" in codes
    assert "outlier_dependence" in codes
    assert "metadata_concentration" in codes
    assert "no_gatekeeper_rerun_yet" in codes


def test_gatekeeper_return_readiness_matrix_has_required_items() -> None:
    rows = build_gatekeeper_return_readiness_matrix()

    codes = _codes(rows, "readiness_code")

    assert "task_123_baseline_loaded" in codes
    assert "stabilization_validation_loaded" in codes
    assert "evidence_area_deltas_available" in codes
    assert "residual_risks_disclosed" in codes
    assert "task_130_input_package_ready" in codes
    assert "progression_still_not_allowed_until_task_130" in codes
    assert "persona_review_still_not_allowed_until_task_130" in codes
    assert "no_gatekeeper_rerun_in_task_129" in codes


def test_task_130_handoff_manifest_is_created() -> None:
    validation = _stabilization_validation()
    gatekeeper = _gatekeeper_re_evaluation()
    evidence_rows = build_evidence_state_delta_matrix(validation)
    blocker_rows = build_gatekeeper_blocker_comparison_matrix(validation, gatekeeper)

    handoff = build_task_130_handoff_manifest(
        gatekeeper_stabilized_comparison_run_id="comparison_run",
        stabilization_validation=validation,
        gatekeeper_re_evaluation=gatekeeper,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
    )

    assert handoff["future_phase_id"] == 17
    assert handoff["future_task_id"] == 130
    assert handoff["readiness_status"]
    assert handoff["execution_allowed_now"] is True
    assert "investor agent execution" in handoff["prohibited_outputs"]
    assert "persona reviews" in handoff["prohibited_outputs"]
    assert "recommendations" in handoff["prohibited_outputs"]


def test_validation_checks_are_created() -> None:
    rows = build_gatekeeper_stabilized_comparison_checks()

    codes = _codes(rows, "check_code")

    assert "task_123_gatekeeper_outcome_preserved" in codes
    assert "progression_not_allowed_preserved" in codes
    assert "persona_review_not_allowed_preserved" in codes
    assert "gatekeeper_not_rerun_in_task_129" in codes
    assert "no_recommendation_outputs" in codes
    assert "no_network_calls" in codes
    assert all(row["status"] == "satisfied" for row in rows)


def test_build_comparison_report_has_sections() -> None:
    report = build_gatekeeper_stabilized_evidence_comparison(
        gatekeeper_stabilized_comparison_run_id="comparison_run",
        generated_at="2026-06-18T12:00:00+00:00",
        stabilization_validation=_stabilization_validation(),
        gatekeeper_re_evaluation=_gatekeeper_re_evaluation(),
    )
    data = report.to_dict()

    assert data["comparison_summary"]
    assert data["gatekeeper_blocker_comparison_matrix"]
    assert data["evidence_state_delta_matrix"]
    assert data["residual_risk_comparison_matrix"]
    assert data["gatekeeper_return_readiness_matrix"]
    assert data["task_130_handoff_manifest"]
    assert data["gatekeeper_stabilized_comparison_checks"]
    assert data["comparison_status"] == "completed"


def test_write_comparison_report_writes_files(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    files = write_gatekeeper_stabilized_evidence_comparison_report(
        outputs_root=outputs_root,
        stabilization_validation_run_id="validation_run",
    )

    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.blocker_csv_path.is_file()
    assert files.evidence_delta_csv_path.is_file()
    assert files.residual_risk_csv_path.is_file()
    assert files.readiness_csv_path.is_file()
    assert files.task_130_handoff_manifest_path.is_file()
    assert files.checks_csv_path.is_file()
    assert files.latest_manifest_path.is_file()
    markdown = files.markdown_path.read_text(encoding="utf-8")
    assert "## Important Boundary" in markdown
    assert "## Where We Are Now" in markdown
    assert "## Gatekeeper Blocker Comparison Matrix" in markdown
    assert "## Evidence State Delta Matrix" in markdown
    assert "## Residual Risk Comparison Matrix" in markdown
    assert "## Gatekeeper Return Readiness Matrix" in markdown
    assert "## Task 130 Handoff" in markdown
    assert "## What This Does Not Suggest" in markdown


def test_cli_works_with_explicit_stabilization_validation_run_id(
    tmp_path: Path,
) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "compare-gatekeeper-stabilized-evidence",
            "--stabilization-validation-run-id",
            "validation_run",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "gatekeeper_stabilized_comparison_run_id=" in result.output
    assert "task_123_gatekeeper_outcome=hold_with_repair_progress" in result.output
    assert "persona_reviews_allowed=false" in result.output


def test_cli_works_with_explicit_stabilization_and_gatekeeper_ids(
    tmp_path: Path,
) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "compare-gatekeeper-stabilized-evidence",
            "--stabilization-validation-run-id",
            "validation_run",
            "--gatekeeper-re-evaluation-run-id",
            "re_gate_run",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "gatekeeper_re_evaluation_run_id=re_gate_run" in result.output
    assert "recommended_next_task=Task 130" in result.output


def test_cli_works_with_auto_latest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "compare-gatekeeper-stabilized-evidence",
            "--auto-latest",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "stabilization_validation_run_id=validation_run" in result.output
    assert "status=completed" in result.output
