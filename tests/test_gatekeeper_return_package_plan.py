import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.gatekeeper_return.gatekeeper_return_package_plan import (
    build_gatekeeper_return_package_plan,
    build_gatekeeper_return_plan_summary,
    build_gatekeeper_return_plan_validation_checks,
    build_phase_18_execution_roadmap,
    build_return_package_component_matrix,
    build_return_package_evidence_inventory_matrix,
    build_return_package_permission_boundary_matrix,
    build_return_package_residual_risk_disclosure_matrix,
    build_task_133_handoff_manifest,
    load_phase_17_closure,
    load_phase_17_closure_manifest,
    write_gatekeeper_return_package_plan_report,
)


def _closure() -> dict:
    permission_rows = [
        ("gatekeeper_return_package_preparation", "allowed"),
        ("actual_persona_review", "not_allowed"),
        ("investor_agent_execution", "not_allowed"),
        ("investor_decision_generation", "not_allowed"),
        ("company_ranking", "not_allowed"),
        ("investment_recommendation", "not_allowed"),
        ("allocation_or_rebalancing", "not_allowed"),
        ("trade_signal_generation", "not_allowed"),
        ("auto_promotion", "disabled"),
    ]
    blocker_codes = [
        "unresolved_material_blockers",
        "partially_improved_evidence_blockers",
        "local_artifact_limitations",
        "residual_metadata_concentration",
        "residual_period_sensitivity",
        "residual_outlier_dependence",
        "investor_agent_execution_not_allowed",
        "auto_promotion_disabled",
    ]
    return {
        "phase_17_closure_run_id": "closure_run",
        "gatekeeper_stabilization_re_review_run_id": "review_run",
        "gatekeeper_stabilized_comparison_run_id": "comparison_run",
        "stabilization_validation_run_id": "validation_run",
        "targeted_repair_run_id": "repair_run",
        "residual_work_order_package_run_id": "work_order_run",
        "stabilization_plan_run_id": "plan_run",
        "phase_16_closure_run_id": "phase16_run",
        "baseline_gatekeeper_re_evaluation_run_id": "baseline_run",
        "pre_post_repair_comparison_run_id": "pre_post_run",
        "controlled_re_run_trial_run_id": "trial_run",
        "re_run_input_package_run_id": "input_run",
        "re_run_re_gate_plan_run_id": "plan119_run",
        "research_audit_trail_run_id": "audit_run",
        "phase_17_closure_summary": {
            "final_gatekeeper_stabilization_outcome": "hold_with_stabilization_progress",
            "final_progression_status": "gatekeeper_return_package_only",
            "final_persona_review_status": "false",
        },
        "final_permission_boundary_summary": [
            {
                "permission_code": code,
                "permission_label": code.replace("_", " "),
                "final_status": status,
                "allowed_scope": "Gatekeeper return package only",
                "blocked_scope": "Investor-facing action",
                "condition_to_expand_scope": "Future Gatekeeper authorization",
            }
            for code, status in permission_rows
        ],
        "remaining_blockers_after_phase_17_matrix": [
            {
                "blocker_code": code,
                "status_after_phase_17": "remaining_or_preserved",
                "severity": "high",
            }
            for code in blocker_codes
        ],
    }


def _write_fixture(outputs_root: Path) -> Path:
    closure = _closure()
    root = outputs_root / "phase_17_closures"
    run_dir = root / closure["phase_17_closure_run_id"]
    run_dir.mkdir(parents=True)
    report_path = run_dir / "phase_17_closure.json"
    report_path.write_text(json.dumps(closure), encoding="utf-8")
    (root / "latest_phase_17_closure_manifest.json").write_text(
        json.dumps(
            {
                "phase_17_closure_run_id": closure["phase_17_closure_run_id"],
                "report_json_path": str(report_path),
            }
        ),
        encoding="utf-8",
    )
    return outputs_root


def _codes(rows: list[dict], key: str) -> set[str]:
    return {str(row[key]) for row in rows}


def test_loads_latest_phase_17_closure_manifest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_phase_17_closure_manifest(outputs_root=outputs_root)

    assert manifest["phase_17_closure_run_id"] == "closure_run"


def test_loads_explicit_phase_17_closure_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_phase_17_closure_manifest(
        outputs_root=outputs_root,
        phase_17_closure_run_id="closure_run",
    )
    report = load_phase_17_closure(
        outputs_root=outputs_root,
        phase_17_closure_run_id="closure_run",
    )

    assert manifest["phase_17_closure_run_id"] == "closure_run"
    assert report["phase_17_closure_run_id"] == "closure_run"


def test_handles_missing_phase_17_closure_manifest(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_phase_17_closure_manifest(outputs_root=tmp_path)


def test_handles_missing_phase_17_closure_report(tmp_path: Path) -> None:
    root = tmp_path / "phase_17_closures"
    root.mkdir()
    (root / "latest_phase_17_closure_manifest.json").write_text(
        json.dumps({"phase_17_closure_run_id": "missing"}),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError):
        load_phase_17_closure(
            outputs_root=tmp_path,
            phase_17_closure_run_id="missing",
        )


def test_gatekeeper_return_plan_summary_is_created() -> None:
    summary = build_gatekeeper_return_plan_summary(
        gatekeeper_return_plan_run_id="plan_run",
        closure=_closure(),
    )

    assert summary["phase_id"] == 18
    assert summary["current_task_id"] == 132
    assert summary["final_gatekeeper_stabilization_outcome"] == (
        "hold_with_stabilization_progress"
    )
    assert summary["final_progression_status"] == "gatekeeper_return_package_only"
    assert summary["final_persona_review_status"] == "false"
    assert summary["plan_status"] == "completed"
    assert summary["planning_role"] == "gatekeeper_return_package_planning"
    assert summary["recommended_next_task"].startswith("Task 133")


def test_return_package_component_matrix_has_required_components() -> None:
    rows = build_return_package_component_matrix()
    codes = _codes(rows, "component_code")

    assert "executive_gatekeeper_return_summary" in codes
    assert "final_gatekeeper_stabilization_decision_record" in codes
    assert "permission_boundary_summary" in codes
    assert "blocker_disposition_summary" in codes
    assert "residual_risk_disclosure" in codes
    assert "evidence_stabilization_timeline" in codes
    assert "repaired_evidence_inventory" in codes
    assert "validation_evidence_inventory" in codes
    assert "comparison_evidence_inventory" in codes
    assert "local_artifact_limitation_disclosure" in codes
    assert "no_persona_review_confirmation" in codes
    assert "no_investor_agent_execution_confirmation" in codes
    assert "no_recommendation_output_confirmation" in codes
    assert "auto_promotion_disabled_confirmation" in codes


def test_return_package_evidence_inventory_matrix_has_required_sources() -> None:
    rows = build_return_package_evidence_inventory_matrix(_closure())
    codes = _codes(rows, "evidence_code")

    assert "phase_17_closure" in codes
    assert "gatekeeper_stabilization_re_review" in codes
    assert "gatekeeper_stabilized_evidence_comparison" in codes
    assert "stabilization_validation_trial" in codes
    assert "targeted_evidence_repairs" in codes
    assert "residual_blocker_work_orders" in codes
    assert "targeted_evidence_stabilization_plan" in codes
    assert "phase_16_closure" in codes
    assert "baseline_gatekeeper_re_evaluation" in codes
    assert "pre_post_repair_comparison" in codes
    assert "controlled_re_run_trial" in codes
    assert "research_audit_trail" in codes


def test_residual_risk_disclosure_matrix_has_required_risks() -> None:
    rows = build_return_package_residual_risk_disclosure_matrix(_closure())
    codes = _codes(rows, "risk_code")

    assert "unresolved_material_blockers" in codes
    assert "partially_improved_evidence_blockers" in codes
    assert "local_artifact_limitations" in codes
    assert "residual_metadata_concentration" in codes
    assert "residual_period_sensitivity" in codes
    assert "residual_outlier_dependence" in codes
    assert "no_actual_persona_review_allowed" in codes
    assert "investor_agent_execution_not_allowed" in codes
    assert "auto_promotion_disabled" in codes
    assert "gatekeeper_return_package_scope_only" in codes


def test_permission_boundary_matrix_preserves_blocks() -> None:
    rows = build_return_package_permission_boundary_matrix(_closure())
    by_code = {row["permission_code"]: row for row in rows}

    assert by_code["gatekeeper_return_package_preparation"][
        "phase_18_planned_status"
    ] == "allowed"
    assert by_code["actual_gatekeeper_re_review"]["phase_18_planned_status"] == (
        "not_in_task_132"
    )
    assert by_code["persona_review_preparation"]["phase_18_planned_status"] == (
        "not_allowed"
    )
    assert by_code["actual_persona_review"]["phase_18_planned_status"] == "not_allowed"
    assert by_code["investor_agent_execution"]["phase_18_planned_status"] == (
        "not_allowed"
    )
    assert by_code["investor_decision_generation"]["phase_18_planned_status"] == (
        "not_allowed"
    )
    assert by_code["company_ranking"]["phase_18_planned_status"] == "not_allowed"
    assert by_code["investment_recommendation"]["phase_18_planned_status"] == (
        "not_allowed"
    )
    assert by_code["allocation_or_rebalancing"]["phase_18_planned_status"] == (
        "not_allowed"
    )
    assert by_code["trade_signal_generation"]["phase_18_planned_status"] == (
        "not_allowed"
    )
    assert by_code["auto_promotion"]["phase_18_planned_status"] == "disabled"


def test_phase_18_execution_roadmap_has_tasks_132_to_137() -> None:
    rows = build_phase_18_execution_roadmap()

    assert {row["task_id"] for row in rows} == {132, 133, 134, 135, 136, 137}


def test_task_133_handoff_manifest_is_created() -> None:
    components = build_return_package_component_matrix()
    evidence = build_return_package_evidence_inventory_matrix(_closure())
    handoff = build_task_133_handoff_manifest(
        gatekeeper_return_plan_run_id="plan_run",
        closure=_closure(),
        components=components,
        evidence=evidence,
    )

    assert handoff["future_phase_id"] == 18
    assert handoff["future_task_id"] == 133
    assert handoff["readiness_status"] == (
        "ready_to_build_gatekeeper_return_package_input_inventory"
    )
    assert handoff["execution_allowed_now"] is True
    assert "investor agent execution" in handoff["prohibited_outputs"]
    assert "actual persona reviews" in handoff["prohibited_outputs"]
    assert "recommendations" in handoff["prohibited_outputs"]


def test_validation_checks_are_created() -> None:
    rows = build_gatekeeper_return_plan_validation_checks()
    codes = _codes(rows, "check_code")

    assert "final_gatekeeper_stabilization_outcome_preserved" in codes
    assert "final_progression_status_preserved" in codes
    assert "final_persona_review_status_preserved" in codes
    assert "gatekeeper_return_package_only_preserved" in codes
    assert "actual_persona_review_not_allowed" in codes
    assert "investor_agents_not_allowed" in codes
    assert "no_recommendation_outputs" in codes
    assert "no_ranking_outputs" in codes
    assert "no_trade_signal_outputs" in codes
    assert "auto_promotion_disabled" in codes
    assert all(row["status"] == "satisfied" for row in rows)


def test_build_plan_report_has_sections() -> None:
    report = build_gatekeeper_return_package_plan(
        gatekeeper_return_plan_run_id="plan_run",
        generated_at="2026-06-19T00:00:00+00:00",
        closure=_closure(),
    )
    data = report.to_dict()

    assert data["gatekeeper_return_plan_summary"]
    assert data["return_package_component_matrix"]
    assert data["return_package_evidence_inventory_matrix"]
    assert data["return_package_residual_risk_disclosure_matrix"]
    assert data["return_package_permission_boundary_matrix"]
    assert data["phase_18_execution_roadmap"]
    assert data["task_133_handoff_manifest"]
    assert data["gatekeeper_return_plan_validation_checks"]


def test_write_plan_report_writes_files(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    files = write_gatekeeper_return_package_plan_report(
        outputs_root=outputs_root,
        phase_17_closure_run_id="closure_run",
    )

    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.component_csv_path.is_file()
    assert files.evidence_csv_path.is_file()
    assert files.residual_risk_csv_path.is_file()
    assert files.permission_csv_path.is_file()
    assert files.roadmap_csv_path.is_file()
    assert files.task_133_handoff_manifest_path.is_file()
    assert files.checks_csv_path.is_file()
    assert files.latest_manifest_path.is_file()
    markdown = files.markdown_path.read_text(encoding="utf-8")
    assert "## Important Boundary" in markdown
    assert "## Where We Are Now" in markdown
    assert "## Return Package Component Matrix" in markdown
    assert "## Return Package Evidence Inventory Matrix" in markdown
    assert "## Residual Risk Disclosure Matrix" in markdown
    assert "## Permission Boundary Matrix" in markdown
    assert "## Phase 18 Execution Roadmap" in markdown
    assert "## Task 133 Handoff" in markdown
    assert "## What This Does Not Suggest" in markdown


def test_cli_works_with_explicit_phase_17_closure_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "define-gatekeeper-return-package-plan",
            "--phase-17-closure-run-id",
            "closure_run",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "gatekeeper_return_plan_run_id=" in result.output
    assert "phase_17_closure_run_id=closure_run" in result.output
    assert "current_phase=18 - Gatekeeper Return Package Layer" in result.output
    assert "recommended_next_task=Task 133" in result.output


def test_cli_works_with_auto_latest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "define-gatekeeper-return-package-plan",
            "--auto-latest",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "phase_17_closure_run_id=closure_run" in result.output
    assert "status=completed" in result.output
