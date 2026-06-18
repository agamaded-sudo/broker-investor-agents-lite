import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.stabilization.targeted_evidence_repairs import (
    build_repair_artifact_trace_matrix,
    build_repair_execution_summary,
    build_repair_limitation_matrix,
    build_repaired_evidence_matrix,
    build_targeted_evidence_repairs,
    build_targeted_repair_validation_checks,
    build_task_128_validation_input_manifest,
    build_work_order_repair_execution_matrix,
    load_residual_blocker_work_orders,
    load_residual_blocker_work_orders_manifest,
    write_targeted_evidence_repairs_report,
)


def _work_order_package() -> dict:
    work_orders = [
        ("WO-126-001", "benchmark_relative_stabilization", "benchmark_relative_evidence"),
        ("WO-126-002", "walk_forward_period_stability", "walk_forward_period_stability"),
        ("WO-126-003", "outlier_dependence_control", "outlier_dependence"),
        ("WO-126-004", "clean_warning_anchor_stability", "clean_warning_anchor_split"),
        (
            "WO-126-005",
            "core_vs_expanded_cohort_alignment",
            "current_core_vs_expanded_cohort",
        ),
        ("WO-126-006", "metadata_concentration_resolution", "metadata_concentration"),
        ("WO-126-007", "local_artifact_limitations_review", "local_artifact_completeness"),
        ("WO-126-008", "gatekeeper_return_package_preparation", "gatekeeper_return_package"),
    ]
    return {
        "residual_work_order_package_run_id": "work_order_run",
        "stabilization_plan_run_id": "plan_run",
        "phase_16_closure_run_id": "closure_run",
        "gatekeeper_re_evaluation_run_id": "re_gate_run",
        "pre_post_repair_comparison_run_id": "comparison_run",
        "controlled_re_run_trial_run_id": "trial_run",
        "re_run_input_package_run_id": "input_package_run",
        "re_run_re_gate_plan_run_id": "re_gate_plan_run",
        "research_audit_trail_run_id": "audit_run",
        "work_order_package_summary": {
            "prior_gatekeeper_outcome": "hold_with_repair_progress",
            "progression_allowed": False,
            "persona_reviews_allowed": False,
        },
        "residual_blocker_work_order_matrix": [
            {
                "work_order_id": work_order_id,
                "work_order_title": title,
                "linked_workstream_code": f"WS{index}_test",
                "evidence_area": evidence_area,
            }
            for index, (work_order_id, title, evidence_area) in enumerate(
                work_orders, start=1
            )
        ],
    }


def _write_fixture(outputs_root: Path) -> Path:
    package = _work_order_package()
    root = outputs_root / "residual_blocker_work_orders"
    run_dir = root / package["residual_work_order_package_run_id"]
    run_dir.mkdir(parents=True)
    report_path = run_dir / "residual_blocker_work_orders.json"
    report_path.write_text(json.dumps(package), encoding="utf-8")
    (root / "latest_residual_blocker_work_orders_manifest.json").write_text(
        json.dumps(
            {
                "residual_work_order_package_run_id": package[
                    "residual_work_order_package_run_id"
                ],
                "report_json_path": str(report_path),
            }
        ),
        encoding="utf-8",
    )
    return outputs_root


def _codes(rows: list[dict], key: str) -> set[str]:
    return {str(row[key]) for row in rows}


def test_loads_latest_residual_work_order_manifest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_residual_blocker_work_orders_manifest(outputs_root=outputs_root)

    assert manifest["residual_work_order_package_run_id"] == "work_order_run"


def test_loads_explicit_residual_work_order_package_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_residual_blocker_work_orders_manifest(
        outputs_root=outputs_root,
        residual_work_order_package_run_id="work_order_run",
    )
    report = load_residual_blocker_work_orders(
        outputs_root=outputs_root,
        residual_work_order_package_run_id="work_order_run",
    )

    assert manifest["stabilization_plan_run_id"] == "plan_run"
    assert report["residual_work_order_package_run_id"] == "work_order_run"


def test_handles_missing_residual_work_order_manifest(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_residual_blocker_work_orders_manifest(outputs_root=tmp_path)


def test_handles_missing_residual_work_order_report(tmp_path: Path) -> None:
    root = tmp_path / "residual_blocker_work_orders"
    root.mkdir()
    (root / "latest_residual_blocker_work_orders_manifest.json").write_text(
        json.dumps({"residual_work_order_package_run_id": "missing"}),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError):
        load_residual_blocker_work_orders(
            outputs_root=tmp_path,
            residual_work_order_package_run_id="missing",
        )


def test_repair_execution_summary_is_created() -> None:
    package = _work_order_package()
    repairs = build_work_order_repair_execution_matrix(package)

    summary = build_repair_execution_summary(
        targeted_repair_run_id="repair_run",
        work_order_package=package,
        repair_rows=repairs,
    )

    assert summary["phase_id"] == 17
    assert summary["current_task_id"] == 127
    assert summary["prior_gatekeeper_outcome"] == "hold_with_repair_progress"
    assert summary["progression_allowed"] is False
    assert summary["persona_reviews_allowed"] is False
    assert summary["repair_execution_status"] == "completed"
    assert summary["recommended_next_task"].startswith("Task 128")


def test_work_order_repair_execution_matrix_has_required_work_orders() -> None:
    rows = build_work_order_repair_execution_matrix(_work_order_package())

    ids = _codes(rows, "work_order_id")

    assert "WO-126-001" in ids
    assert "WO-126-002" in ids
    assert "WO-126-003" in ids
    assert "WO-126-004" in ids
    assert "WO-126-005" in ids
    assert "WO-126-006" in ids
    assert "WO-126-007" in ids
    assert "WO-126-008" in ids
    assert all(row["repair_status"] for row in rows)
    assert all(row["repair_result"] for row in rows)
    assert all(row["executed_action"] for row in rows)
    assert all(row["validation_needed"] is True for row in rows)


def test_repaired_evidence_matrix_has_required_areas() -> None:
    rows = build_repaired_evidence_matrix()

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


def test_repair_limitation_matrix_has_required_limitations() -> None:
    rows = build_repair_limitation_matrix()

    codes = _codes(rows, "limitation_code")

    assert "local_artifacts_only" in codes
    assert "no_new_market_data" in codes
    assert "no_new_financials" in codes
    assert "gatekeeper_not_rerun_in_task_127" in codes
    assert "persona_review_not_allowed" in codes


def test_repair_artifact_trace_matrix_has_required_sources() -> None:
    rows = build_repair_artifact_trace_matrix(_work_order_package())

    sources = _codes(rows, "source_artifact")

    assert "residual_work_order_package" in sources
    assert "stabilization_plan" in sources
    assert "phase_16_closure" in sources
    assert "gatekeeper_re_evaluation" in sources
    assert "pre_post_comparison" in sources
    assert all(row["trace_status"] == "traced" for row in rows)


def test_task_128_validation_input_manifest_is_created() -> None:
    package = _work_order_package()
    repairs = build_work_order_repair_execution_matrix(package)
    evidence = build_repaired_evidence_matrix()

    manifest = build_task_128_validation_input_manifest(
        targeted_repair_run_id="repair_run",
        work_order_package=package,
        repaired_evidence=evidence,
        repair_rows=repairs,
    )

    assert manifest["future_phase_id"] == 17
    assert manifest["future_task_id"] == 128
    assert manifest["readiness_status"] == "ready_for_stabilization_validation_trial"
    assert "Gatekeeper rerun" in manifest["prohibited_outputs"]
    assert "persona reviews" in manifest["prohibited_outputs"]
    assert "recommendations" in manifest["prohibited_outputs"]


def test_targeted_repair_validation_checks_are_created() -> None:
    rows = build_targeted_repair_validation_checks()

    codes = _codes(rows, "check_code")

    assert "prior_gatekeeper_outcome_preserved" in codes
    assert "progression_not_allowed_preserved" in codes
    assert "persona_review_not_allowed_preserved" in codes
    assert "gatekeeper_not_rerun_in_task_127" in codes
    assert "no_recommendation_outputs" in codes
    assert "no_network_calls" in codes
    assert all(row["status"] == "satisfied" for row in rows)


def test_build_targeted_evidence_repairs_report_has_sections() -> None:
    report = build_targeted_evidence_repairs(
        targeted_repair_run_id="repair_run",
        generated_at="2026-06-18T12:00:00+00:00",
        work_order_package=_work_order_package(),
    )
    data = report.to_dict()

    assert data["repair_execution_summary"]
    assert data["work_order_repair_execution_matrix"]
    assert data["repaired_evidence_matrix"]
    assert data["repair_limitation_matrix"]
    assert data["repair_artifact_trace_matrix"]
    assert data["task_128_validation_input_manifest"]
    assert data["targeted_repair_validation_checks"]


def test_write_targeted_evidence_repairs_report_writes_files(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    files = write_targeted_evidence_repairs_report(
        outputs_root=outputs_root,
        residual_work_order_package_run_id="work_order_run",
    )

    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.work_order_repair_csv_path.is_file()
    assert files.repaired_evidence_csv_path.is_file()
    assert files.limitation_csv_path.is_file()
    assert files.artifact_trace_csv_path.is_file()
    assert files.task_128_validation_input_manifest_path.is_file()
    assert files.validation_checks_csv_path.is_file()
    assert files.latest_manifest_path.is_file()
    markdown = files.markdown_path.read_text(encoding="utf-8")
    assert "## Important Boundary" in markdown
    assert "## Where We Are Now" in markdown
    assert "## Work Order Repair Execution Matrix" in markdown
    assert "## Repaired Evidence Matrix" in markdown
    assert "## Repair Limitations" in markdown
    assert "## Repair Artifact Trace" in markdown
    assert "## Task 128 Validation Input Manifest" in markdown
    assert "## What This Does Not Suggest" in markdown


def test_cli_works_with_explicit_residual_work_order_package_run_id(
    tmp_path: Path,
) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "execute-targeted-evidence-repairs",
            "--residual-work-order-package-run-id",
            "work_order_run",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "targeted_repair_run_id=" in result.output
    assert "prior_gatekeeper_outcome=hold_with_repair_progress" in result.output
    assert "persona_reviews_allowed=false" in result.output


def test_cli_works_with_auto_latest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "execute-targeted-evidence-repairs",
            "--auto-latest",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "residual_work_order_package_run_id=work_order_run" in result.output
    assert "recommended_next_task=Task 128" in result.output
