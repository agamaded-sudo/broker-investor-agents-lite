import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.stabilization.residual_blocker_work_orders import (
    build_residual_blocker_work_order_matrix,
    build_residual_blocker_work_orders,
    build_residual_work_order_validation_checks,
    build_task_127_execution_manifest,
    build_work_order_dependency_matrix,
    build_work_order_execution_sequence,
    build_work_order_input_requirements_matrix,
    build_work_order_package_summary,
    build_work_order_success_criteria_matrix,
    load_targeted_evidence_stabilization_plan,
    load_targeted_evidence_stabilization_plan_manifest,
    write_residual_blocker_work_order_report,
)


def _plan() -> dict:
    return {
        "stabilization_plan_run_id": "plan_run",
        "phase_16_closure_run_id": "closure_run",
        "gatekeeper_re_evaluation_run_id": "re_gate_run",
        "pre_post_repair_comparison_run_id": "comparison_run",
        "controlled_re_run_trial_run_id": "trial_run",
        "re_run_input_package_run_id": "input_package_run",
        "re_run_re_gate_plan_run_id": "re_gate_plan_run",
        "research_audit_trail_run_id": "audit_run",
        "stabilization_plan_summary": {
            "prior_phase_final_gatekeeper_outcome": "hold_with_repair_progress",
            "prior_phase_final_progression_allowed": False,
            "prior_phase_final_persona_reviews_allowed": False,
        },
        "stabilization_workstream_matrix": [
            {"workstream_code": "WS1_benchmark_relative_stabilization"},
            {"workstream_code": "WS2_walk_forward_period_stability"},
            {"workstream_code": "WS3_outlier_dependence_control"},
            {"workstream_code": "WS4_clean_warning_anchor_stability"},
            {"workstream_code": "WS5_core_vs_expanded_cohort_alignment"},
            {"workstream_code": "WS6_metadata_concentration_resolution"},
            {"workstream_code": "WS7_local_artifact_limitations_review"},
            {"workstream_code": "WS8_gatekeeper_return_package_preparation"},
        ],
    }


def _write_fixture(outputs_root: Path) -> Path:
    plan = _plan()
    root = outputs_root / "targeted_evidence_stabilization_plans"
    run_dir = root / plan["stabilization_plan_run_id"]
    run_dir.mkdir(parents=True)
    report_path = run_dir / "targeted_evidence_stabilization_plan.json"
    report_path.write_text(json.dumps(plan), encoding="utf-8")
    (root / "latest_targeted_evidence_stabilization_plan_manifest.json").write_text(
        json.dumps(
            {
                "stabilization_plan_run_id": plan["stabilization_plan_run_id"],
                "report_json_path": str(report_path),
            }
        ),
        encoding="utf-8",
    )
    return outputs_root


def _codes(rows: list[dict], key: str) -> set[str]:
    return {str(row[key]) for row in rows}


def test_loads_latest_stabilization_plan_manifest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_targeted_evidence_stabilization_plan_manifest(
        outputs_root=outputs_root
    )

    assert manifest["stabilization_plan_run_id"] == "plan_run"


def test_loads_explicit_stabilization_plan_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_targeted_evidence_stabilization_plan_manifest(
        outputs_root=outputs_root,
        stabilization_plan_run_id="plan_run",
    )
    report = load_targeted_evidence_stabilization_plan(
        outputs_root=outputs_root,
        stabilization_plan_run_id="plan_run",
    )

    assert manifest["gatekeeper_re_evaluation_run_id"] == "re_gate_run"
    assert report["stabilization_plan_run_id"] == "plan_run"


def test_handles_missing_stabilization_plan_manifest(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_targeted_evidence_stabilization_plan_manifest(outputs_root=tmp_path)


def test_handles_missing_stabilization_plan_report(tmp_path: Path) -> None:
    root = tmp_path / "targeted_evidence_stabilization_plans"
    root.mkdir()
    (root / "latest_targeted_evidence_stabilization_plan_manifest.json").write_text(
        json.dumps({"stabilization_plan_run_id": "missing"}),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError):
        load_targeted_evidence_stabilization_plan(
            outputs_root=tmp_path,
            stabilization_plan_run_id="missing",
        )


def test_work_order_package_summary_is_created() -> None:
    work_orders = build_residual_blocker_work_order_matrix(_plan())
    summary = build_work_order_package_summary(
        residual_work_order_package_run_id="package_run",
        stabilization_plan=_plan(),
        work_orders=work_orders,
    )

    assert summary["phase_id"] == 17
    assert summary["current_task_id"] == 126
    assert summary["prior_gatekeeper_outcome"] == "hold_with_repair_progress"
    assert summary["progression_allowed"] is False
    assert summary["persona_reviews_allowed"] is False
    assert summary["package_status"] == "completed"
    assert summary["recommended_next_task"].startswith("Task 127")


def test_residual_blocker_work_order_matrix_has_required_work_orders() -> None:
    rows = build_residual_blocker_work_order_matrix(_plan())

    ids = _codes(rows, "work_order_id")
    titles = _codes(rows, "work_order_title")

    assert "WO-126-001" in ids
    assert "WO-126-002" in ids
    assert "WO-126-003" in ids
    assert "WO-126-004" in ids
    assert "WO-126-005" in ids
    assert "WO-126-006" in ids
    assert "WO-126-007" in ids
    assert "WO-126-008" in ids
    assert "benchmark_relative_stabilization" in titles
    assert "walk_forward_period_stability" in titles
    assert "outlier_dependence_control" in titles
    assert "metadata_concentration_resolution" in titles
    assert all(row["linked_workstream_code"].startswith("WS") for row in rows)
    assert all(row["objective"] for row in rows)
    assert all(row["required_inputs"] for row in rows)
    assert all(row["planned_repair_action"] for row in rows)
    assert all(row["expected_output"] for row in rows)
    assert all(row["success_criteria"] for row in rows)
    assert all(row["validation_method"] for row in rows)


def test_work_order_dependency_matrix_has_parallel_and_gatekeeper_dependencies() -> None:
    rows = build_work_order_dependency_matrix()

    by_id = {row["work_order_id"]: row for row in rows}

    assert by_id["WO-126-008"]["can_execute_in_parallel"] is False
    assert "WO-126-001" in by_id["WO-126-008"]["depends_on"]
    assert any(row["can_execute_in_parallel"] is True for row in rows)


def test_work_order_input_requirements_matrix_has_required_inputs() -> None:
    rows = build_work_order_input_requirements_matrix(_plan())

    codes = _codes(rows, "required_input_code")

    assert "phase_16_closure" in codes
    assert "gatekeeper_re_evaluation" in codes
    assert "pre_post_repair_comparison" in codes
    assert "controlled_re_run_trial" in codes
    assert "metadata_diversity_recheck" in codes
    assert "delayed_anchor_repair" in codes
    assert "walk_forward_repair" in codes
    assert "outlier_repair" in codes


def test_work_order_success_criteria_matrix_has_required_criteria() -> None:
    rows = build_work_order_success_criteria_matrix()

    codes = _codes(rows, "success_criteria_code")

    assert "benchmark_relative_uncertainty_bounded" in codes
    assert "walk_forward_instability_explained_or_reduced" in codes
    assert "outlier_dependence_bounded" in codes
    assert "metadata_concentration_disclosed_or_reduced" in codes
    assert "gatekeeper_return_package_ready" in codes


def test_work_order_execution_sequence_is_created() -> None:
    rows = build_work_order_execution_sequence()

    assert len(rows) == 4
    assert rows[0]["execution_group"] == "readiness_review"
    assert any("no repairs executed in Task 126" in row["safety_boundary"] for row in rows)


def test_task_127_execution_manifest_is_created() -> None:
    work_orders = build_residual_blocker_work_order_matrix(_plan())
    manifest = build_task_127_execution_manifest(
        residual_work_order_package_run_id="package_run",
        stabilization_plan_run_id="plan_run",
        work_orders=work_orders,
    )

    assert manifest["future_phase_id"] == 17
    assert manifest["future_task_id"] == 127
    assert manifest["readiness_status"] == "ready_for_targeted_evidence_repair_execution"
    assert manifest["execution_allowed_now"] is True
    assert "Gatekeeper rerun" in manifest["prohibited_outputs"]
    assert "persona reviews" in manifest["prohibited_outputs"]
    assert "recommendations" in manifest["prohibited_outputs"]


def test_residual_work_order_validation_checks_are_created() -> None:
    rows = build_residual_work_order_validation_checks()

    codes = _codes(rows, "check_code")

    assert "prior_gatekeeper_outcome_preserved" in codes
    assert "progression_not_allowed_preserved" in codes
    assert "persona_review_not_allowed_preserved" in codes
    assert "gatekeeper_not_rerun_in_task_126" in codes
    assert "repairs_not_executed_in_task_126" in codes
    assert "no_recommendation_outputs" in codes
    assert "no_network_calls" in codes
    assert all(row["status"] == "satisfied" for row in rows)


def test_build_residual_blocker_work_orders_report_has_sections() -> None:
    report = build_residual_blocker_work_orders(
        residual_work_order_package_run_id="package_run",
        generated_at="2026-06-18T12:00:00+00:00",
        stabilization_plan=_plan(),
    )
    data = report.to_dict()

    assert data["work_order_package_summary"]
    assert data["residual_blocker_work_order_matrix"]
    assert data["work_order_dependency_matrix"]
    assert data["work_order_input_requirements_matrix"]
    assert data["work_order_success_criteria_matrix"]
    assert data["work_order_execution_sequence"]
    assert data["task_127_execution_manifest"]
    assert data["residual_work_order_validation_checks"]


def test_write_residual_blocker_work_order_report_writes_files(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    files = write_residual_blocker_work_order_report(
        outputs_root=outputs_root,
        stabilization_plan_run_id="plan_run",
    )

    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.work_order_csv_path.is_file()
    assert files.dependency_csv_path.is_file()
    assert files.input_requirements_csv_path.is_file()
    assert files.success_criteria_csv_path.is_file()
    assert files.execution_sequence_csv_path.is_file()
    assert files.task_127_execution_manifest_path.is_file()
    assert files.validation_checks_csv_path.is_file()
    assert files.latest_manifest_path.is_file()
    markdown = files.markdown_path.read_text(encoding="utf-8")
    assert "## Important Boundary" in markdown
    assert "## Where We Are Now" in markdown
    assert "## Residual Blocker Work Order Matrix" in markdown
    assert "## Work Order Dependency Matrix" in markdown
    assert "## Work Order Input Requirements" in markdown
    assert "## Work Order Success Criteria" in markdown
    assert "## Work Order Execution Sequence" in markdown
    assert "## Task 127 Execution Manifest" in markdown
    assert "## What This Does Not Suggest" in markdown


def test_cli_works_with_explicit_stabilization_plan_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "build-residual-blocker-work-orders",
            "--stabilization-plan-run-id",
            "plan_run",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "residual_work_order_package_run_id=" in result.output
    assert "prior_gatekeeper_outcome=hold_with_repair_progress" in result.output
    assert "persona_reviews_allowed=false" in result.output


def test_cli_works_with_auto_latest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "build-residual-blocker-work-orders",
            "--auto-latest",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "stabilization_plan_run_id=plan_run" in result.output
    assert "recommended_next_task=Task 127" in result.output
