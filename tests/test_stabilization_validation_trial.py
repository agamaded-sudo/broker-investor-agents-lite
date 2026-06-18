import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.stabilization.stabilization_validation_trial import (
    build_evidence_area_validation_matrix,
    build_residual_uncertainty_matrix,
    build_stabilization_validation_checks,
    build_stabilization_validation_trial,
    build_task_129_handoff_manifest,
    build_validation_artifact_trace_matrix,
    build_validation_readiness_matrix,
    build_validation_trial_summary,
    build_work_order_validation_matrix,
    load_targeted_evidence_repairs,
    load_targeted_evidence_repairs_manifest,
    write_stabilization_validation_trial_report,
)


def _targeted_repairs() -> dict:
    work_orders = [
        ("WO-126-001", "benchmark_relative_stabilization", "benchmark_relative_evidence"),
        ("WO-126-002", "walk_forward_period_stability", "walk_forward_stability"),
        ("WO-126-003", "outlier_dependence_control", "outlier_dependence"),
        ("WO-126-004", "clean_warning_anchor_stability", "clean_warning_split"),
        (
            "WO-126-005",
            "core_vs_expanded_cohort_alignment",
            "current_core_vs_expanded_cohort",
        ),
        ("WO-126-006", "metadata_concentration_resolution", "metadata_concentration"),
        ("WO-126-007", "local_artifact_limitations_review", "local_artifact_completeness"),
        ("WO-126-008", "gatekeeper_return_package_preparation", "gatekeeper_return_package"),
    ]
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
    return {
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
        "repair_execution_summary": {
            "prior_gatekeeper_outcome": "hold_with_repair_progress",
            "progression_allowed": False,
            "persona_reviews_allowed": False,
        },
        "work_order_repair_execution_matrix": [
            {
                "work_order_id": work_order_id,
                "work_order_title": title,
                "evidence_area": area,
                "repair_status": "completed_with_warnings",
                "output_artifact": f"{title}_repair_output",
            }
            for work_order_id, title, area in work_orders
        ],
        "repaired_evidence_matrix": [
            {
                "evidence_area": area,
                "linked_work_order_id": work_order_id,
                "pre_repair_issue": "Residual blocker",
                "stabilized_finding": "Validation-ready, not progression-ready.",
                "remaining_uncertainty": "Task 128 validation required.",
            }
            for area, work_order_id in evidence_areas
        ],
    }


def _write_fixture(outputs_root: Path) -> Path:
    repairs = _targeted_repairs()
    root = outputs_root / "targeted_evidence_repairs"
    run_dir = root / repairs["targeted_repair_run_id"]
    run_dir.mkdir(parents=True)
    report_path = run_dir / "targeted_evidence_repairs.json"
    report_path.write_text(json.dumps(repairs), encoding="utf-8")
    (root / "latest_targeted_evidence_repairs_manifest.json").write_text(
        json.dumps(
            {
                "targeted_repair_run_id": repairs["targeted_repair_run_id"],
                "report_json_path": str(report_path),
            }
        ),
        encoding="utf-8",
    )
    return outputs_root


def _codes(rows: list[dict], key: str) -> set[str]:
    return {str(row[key]) for row in rows}


def test_loads_latest_targeted_repair_manifest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_targeted_evidence_repairs_manifest(outputs_root=outputs_root)

    assert manifest["targeted_repair_run_id"] == "repair_run"


def test_loads_explicit_targeted_repair_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_targeted_evidence_repairs_manifest(
        outputs_root=outputs_root,
        targeted_repair_run_id="repair_run",
    )
    report = load_targeted_evidence_repairs(
        outputs_root=outputs_root,
        targeted_repair_run_id="repair_run",
    )

    assert manifest["residual_work_order_package_run_id"] == "work_order_run"
    assert report["targeted_repair_run_id"] == "repair_run"


def test_handles_missing_targeted_repair_manifest(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_targeted_evidence_repairs_manifest(outputs_root=tmp_path)


def test_handles_missing_targeted_repair_report(tmp_path: Path) -> None:
    root = tmp_path / "targeted_evidence_repairs"
    root.mkdir()
    (root / "latest_targeted_evidence_repairs_manifest.json").write_text(
        json.dumps({"targeted_repair_run_id": "missing"}),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError):
        load_targeted_evidence_repairs(
            outputs_root=tmp_path,
            targeted_repair_run_id="missing",
        )


def test_validation_trial_summary_is_created() -> None:
    repairs = _targeted_repairs()
    rows = build_work_order_validation_matrix(repairs)

    summary = build_validation_trial_summary(
        stabilization_validation_run_id="validation_run",
        targeted_repairs=repairs,
        validation_rows=rows,
    )

    assert summary["phase_id"] == 17
    assert summary["current_task_id"] == 128
    assert summary["prior_gatekeeper_outcome"] == "hold_with_repair_progress"
    assert summary["progression_allowed"] is False
    assert summary["persona_reviews_allowed"] is False
    assert summary["validation_trial_status"] == "completed"
    assert summary["recommended_next_task"].startswith("Task 129")


def test_work_order_validation_matrix_has_required_work_orders() -> None:
    rows = build_work_order_validation_matrix(_targeted_repairs())

    ids = _codes(rows, "work_order_id")

    assert "WO-126-001" in ids
    assert "WO-126-002" in ids
    assert "WO-126-003" in ids
    assert "WO-126-004" in ids
    assert "WO-126-005" in ids
    assert "WO-126-006" in ids
    assert "WO-126-007" in ids
    assert "WO-126-008" in ids
    assert all(row["validation_status"] for row in rows)
    assert all(row["validation_result"] for row in rows)
    assert all(row["ready_for_task_129"] is True for row in rows)


def test_evidence_area_validation_matrix_has_required_areas() -> None:
    rows = build_evidence_area_validation_matrix(_targeted_repairs())

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


def test_validation_readiness_matrix_has_required_items() -> None:
    rows = build_validation_readiness_matrix()

    codes = _codes(rows, "readiness_code")

    assert "repaired_evidence_available" in codes
    assert "benchmark_relative_validation_ready" in codes
    assert "walk_forward_validation_ready" in codes
    assert "outlier_validation_ready" in codes
    assert "no_gatekeeper_rerun" in codes
    assert "no_persona_review" in codes


def test_residual_uncertainty_matrix_has_required_uncertainties() -> None:
    rows = build_residual_uncertainty_matrix()

    codes = _codes(rows, "uncertainty_code")

    assert "benchmark_relative_uncertainty" in codes
    assert "walk_forward_period_sensitivity" in codes
    assert "supportive_period_dependence" in codes
    assert "outlier_dependence" in codes
    assert "metadata_concentration" in codes


def test_validation_artifact_trace_matrix_has_required_sources() -> None:
    rows = build_validation_artifact_trace_matrix(_targeted_repairs())

    sources = _codes(rows, "source_artifact")

    assert "targeted_evidence_repairs" in sources
    assert "residual_work_order_package" in sources
    assert "stabilization_plan" in sources
    assert "phase_16_closure" in sources
    assert all(row["trace_status"] == "traced" for row in rows)


def test_task_129_handoff_manifest_is_created() -> None:
    repairs = _targeted_repairs()
    evidence_rows = build_evidence_area_validation_matrix(repairs)
    validation_rows = build_work_order_validation_matrix(repairs)

    handoff = build_task_129_handoff_manifest(
        stabilization_validation_run_id="validation_run",
        targeted_repairs=repairs,
        evidence_rows=evidence_rows,
        validation_rows=validation_rows,
    )

    assert handoff["future_phase_id"] == 17
    assert handoff["future_task_id"] == 129
    assert handoff["readiness_status"]
    assert handoff["execution_allowed_now"] is True
    assert "Gatekeeper rerun" in handoff["prohibited_outputs"]
    assert "persona reviews" in handoff["prohibited_outputs"]
    assert "recommendations" in handoff["prohibited_outputs"]


def test_stabilization_validation_checks_are_created() -> None:
    rows = build_stabilization_validation_checks()

    codes = _codes(rows, "check_code")

    assert "prior_gatekeeper_outcome_preserved" in codes
    assert "progression_not_allowed_preserved" in codes
    assert "persona_review_not_allowed_preserved" in codes
    assert "gatekeeper_not_rerun_in_task_128" in codes
    assert "no_recommendation_outputs" in codes
    assert "no_network_calls" in codes
    assert all(row["status"] == "satisfied" for row in rows)


def test_build_stabilization_validation_trial_report_has_sections() -> None:
    report = build_stabilization_validation_trial(
        stabilization_validation_run_id="validation_run",
        generated_at="2026-06-18T12:00:00+00:00",
        targeted_repairs=_targeted_repairs(),
    )
    data = report.to_dict()

    assert data["validation_trial_summary"]
    assert data["work_order_validation_matrix"]
    assert data["evidence_area_validation_matrix"]
    assert data["validation_readiness_matrix"]
    assert data["residual_uncertainty_matrix"]
    assert data["validation_artifact_trace_matrix"]
    assert data["task_129_handoff_manifest"]
    assert data["stabilization_validation_checks"]


def test_write_stabilization_validation_trial_report_writes_files(
    tmp_path: Path,
) -> None:
    outputs_root = _write_fixture(tmp_path)

    files = write_stabilization_validation_trial_report(
        outputs_root=outputs_root,
        targeted_repair_run_id="repair_run",
    )

    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.work_order_validation_csv_path.is_file()
    assert files.evidence_area_validation_csv_path.is_file()
    assert files.validation_readiness_csv_path.is_file()
    assert files.residual_uncertainty_csv_path.is_file()
    assert files.validation_artifact_trace_csv_path.is_file()
    assert files.task_129_handoff_manifest_path.is_file()
    assert files.validation_checks_csv_path.is_file()
    assert files.latest_manifest_path.is_file()
    markdown = files.markdown_path.read_text(encoding="utf-8")
    assert "## Important Boundary" in markdown
    assert "## Where We Are Now" in markdown
    assert "## Work Order Validation Matrix" in markdown
    assert "## Evidence Area Validation Matrix" in markdown
    assert "## Validation Readiness Matrix" in markdown
    assert "## Residual Uncertainty Matrix" in markdown
    assert "## Validation Artifact Trace" in markdown
    assert "## Task 129 Handoff" in markdown
    assert "## What This Does Not Suggest" in markdown


def test_cli_works_with_explicit_targeted_repair_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "run-stabilization-validation-trial",
            "--targeted-repair-run-id",
            "repair_run",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "stabilization_validation_run_id=" in result.output
    assert "prior_gatekeeper_outcome=hold_with_repair_progress" in result.output
    assert "persona_reviews_allowed=false" in result.output


def test_cli_works_with_auto_latest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "run-stabilization-validation-trial",
            "--auto-latest",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "targeted_repair_run_id=repair_run" in result.output
    assert "recommended_next_task=Task 129" in result.output
