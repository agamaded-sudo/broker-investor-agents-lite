import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.gatekeeper_return.gatekeeper_return_package_assembly import (
    build_gatekeeper_return_package,
    build_gatekeeper_return_package_assembly_checks,
    build_return_package_evidence_reference_matrix,
    build_return_package_index_matrix,
    build_return_package_limitation_matrix,
    build_return_package_permission_boundary_section,
    build_return_package_residual_risk_section,
    build_return_package_section_matrix,
    build_return_package_summary,
    build_task_135_handoff_manifest,
    load_gatekeeper_return_input_inventory,
    load_gatekeeper_return_input_inventory_manifest,
    write_gatekeeper_return_package_report,
)


def _components() -> list[dict]:
    codes = [
        "executive_gatekeeper_return_summary",
        "final_gatekeeper_stabilization_decision_record",
        "permission_boundary_summary",
        "blocker_disposition_summary",
        "residual_risk_disclosure",
        "evidence_stabilization_timeline",
        "repaired_evidence_inventory",
        "validation_evidence_inventory",
        "comparison_evidence_inventory",
        "local_artifact_limitation_disclosure",
        "no_persona_review_confirmation",
        "no_investor_agent_execution_confirmation",
        "no_recommendation_output_confirmation",
        "auto_promotion_disabled_confirmation",
        "next_gatekeeper_review_questions",
    ]
    return [
        {
            "component_code": code,
            "component_label": code.replace("_", " "),
            "component_purpose": f"{code} purpose",
            "located_inputs": "local artifact",
            "inventory_status": "available_with_warnings"
            if code == "next_gatekeeper_review_questions"
            else "available",
            "inclusion_status": "ready_with_warnings"
            if code == "next_gatekeeper_review_questions"
            else "ready_for_package_assembly",
            "required_follow_up": "Review warning during assembly."
            if code == "next_gatekeeper_review_questions"
            else "Carry into Task 134 assembly.",
            "safety_boundary": "Component only.",
        }
        for code in codes
    ]


def _evidence() -> list[dict]:
    specs = [
        ("phase_17_closure", 17, 131, "closure_run"),
        ("gatekeeper_stabilization_re_review", 17, 130, "review_run"),
        ("gatekeeper_stabilized_evidence_comparison", 17, 129, "comparison_run"),
        ("stabilization_validation_trial", 17, 128, "validation_run"),
        ("targeted_evidence_repairs", 17, 127, "repair_run"),
        ("residual_blocker_work_orders", 17, 126, "work_order_run"),
        ("targeted_evidence_stabilization_plan", 17, 125, "plan_run"),
        ("phase_16_closure", 16, 124, "phase16_run"),
        ("baseline_gatekeeper_re_evaluation", 16, 123, "baseline_run"),
        ("pre_post_repair_comparison", 16, 122, "pre_post_run"),
        ("controlled_re_run_trial", 16, 121, "trial_run"),
        ("research_audit_trail", 15, 118, "audit_run"),
    ]
    return [
        {
            "evidence_code": code,
            "evidence_label": code.replace("_", " "),
            "source_phase": phase,
            "source_task": task,
            "source_run_id": run_id,
            "located_artifact_path": f"data/outputs/{code}/{run_id}/artifact.json",
            "artifact_exists": True,
            "inventory_status": "available",
            "inclusion_status": "ready_for_package_assembly",
            "role_in_package": "source evidence",
            "limitation_note": "local artifact only",
            "safety_boundary": "Evidence only.",
        }
        for code, phase, task, run_id in specs
    ]


def _inventory() -> dict:
    return {
        "gatekeeper_return_input_inventory_run_id": "inventory_run",
        "generated_at": "2026-06-19T00:00:00+00:00",
        "gatekeeper_return_plan_run_id": "return_plan_run",
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
        "re_run_re_gate_plan_run_id": "regate_plan_run",
        "research_audit_trail_run_id": "audit_run",
        "input_inventory_summary": {
            "gatekeeper_return_input_inventory_run_id": "inventory_run",
            "gatekeeper_return_plan_run_id": "return_plan_run",
            "phase_17_closure_run_id": "closure_run",
            "phase_id": 18,
            "phase_name": "Gatekeeper Return Package Layer",
            "current_task_id": 133,
            "current_task_name": "Build Gatekeeper Return Package Input Inventory",
            "final_gatekeeper_stabilization_outcome": (
                "hold_with_stabilization_progress"
            ),
            "final_progression_status": "gatekeeper_return_package_only",
            "final_persona_review_status": "false",
            "inventory_status": "completed_with_warnings",
            "component_inputs_total": 15,
            "component_inputs_ready": 14,
            "component_inputs_ready_with_warnings": 1,
            "component_inputs_missing": 0,
            "evidence_artifacts_total": 12,
            "evidence_artifacts_ready": 12,
            "evidence_artifacts_ready_with_warnings": 0,
            "evidence_artifacts_missing": 0,
            "recommended_next_task": "Task 134 - Assemble Gatekeeper Return Package",
        },
        "component_input_inventory_matrix": _components(),
        "evidence_artifact_inventory_matrix": _evidence(),
        "source_run_traceability_matrix": [],
        "missing_or_warning_input_matrix": [
            {
                "issue_code": "local_artifact_limitation",
                "issue_status": "available_with_warnings",
                "severity": "medium",
            },
            {
                "issue_code": "unresolved_material_blocker",
                "issue_status": "available_with_warnings",
                "severity": "high",
            },
            {
                "issue_code": "persona_review_not_allowed",
                "issue_status": "excluded_by_safety_boundary",
                "severity": "critical",
            },
            {
                "issue_code": "investor_agent_execution_not_allowed",
                "issue_status": "excluded_by_safety_boundary",
                "severity": "critical",
            },
            {
                "issue_code": "auto_promotion_disabled",
                "issue_status": "excluded_by_safety_boundary",
                "severity": "critical",
            },
            {
                "issue_code": "gatekeeper_return_package_only_scope",
                "issue_status": "available_with_warnings",
                "severity": "high",
            },
        ],
        "package_assembly_readiness_matrix": [],
        "task_134_handoff_manifest": {"future_task_id": 134},
        "gatekeeper_return_input_inventory_checks": [],
        "inventory_status": "completed_with_warnings",
        "recommended_next_task": "Task 134 - Assemble Gatekeeper Return Package",
        "safety_notice": "Task 133 safety notice.",
    }


def _write_fixture(outputs_root: Path) -> Path:
    inventory = _inventory()
    root = outputs_root / "gatekeeper_return_input_inventories"
    folder = root / inventory["gatekeeper_return_input_inventory_run_id"]
    folder.mkdir(parents=True)
    report_path = folder / "gatekeeper_return_input_inventory.json"
    report_path.write_text(json.dumps(inventory), encoding="utf-8")
    (root / "latest_gatekeeper_return_input_inventory_manifest.json").write_text(
        json.dumps(
            {
                "gatekeeper_return_input_inventory_run_id": (
                    inventory["gatekeeper_return_input_inventory_run_id"]
                ),
                "report_json_path": str(report_path),
            }
        ),
        encoding="utf-8",
    )
    return outputs_root


def _codes(rows: list[dict], key: str) -> set[str]:
    return {str(row[key]) for row in rows}


def test_loads_latest_input_inventory_manifest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_gatekeeper_return_input_inventory_manifest(outputs_root=outputs_root)

    assert manifest["gatekeeper_return_input_inventory_run_id"] == "inventory_run"


def test_loads_explicit_input_inventory_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_gatekeeper_return_input_inventory_manifest(
        outputs_root=outputs_root,
        gatekeeper_return_input_inventory_run_id="inventory_run",
    )
    report = load_gatekeeper_return_input_inventory(
        outputs_root=outputs_root,
        gatekeeper_return_input_inventory_run_id="inventory_run",
    )

    assert manifest["gatekeeper_return_input_inventory_run_id"] == "inventory_run"
    assert report["gatekeeper_return_input_inventory_run_id"] == "inventory_run"


def test_handles_missing_input_inventory_manifest(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_gatekeeper_return_input_inventory_manifest(outputs_root=tmp_path)


def test_handles_missing_input_inventory_report(tmp_path: Path) -> None:
    root = tmp_path / "gatekeeper_return_input_inventories"
    root.mkdir()
    (root / "latest_gatekeeper_return_input_inventory_manifest.json").write_text(
        json.dumps({"gatekeeper_return_input_inventory_run_id": "missing"}),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError):
        load_gatekeeper_return_input_inventory(
            outputs_root=tmp_path,
            gatekeeper_return_input_inventory_run_id="missing",
        )


def test_return_package_summary_is_created() -> None:
    inventory = _inventory()
    index = build_return_package_index_matrix(inventory)
    evidence = build_return_package_evidence_reference_matrix(inventory)
    limitations = build_return_package_limitation_matrix()

    summary = build_return_package_summary(
        gatekeeper_return_package_run_id="package_run",
        inventory=inventory,
        index_rows=index,
        evidence_rows=evidence,
        limitation_rows=limitations,
    )

    assert summary["current_task_id"] == 134
    assert summary["recommended_next_task"].startswith("Task 135")
    assert summary["package_status"] == "assembled_with_warnings"


def test_return_package_index_matrix_has_required_sections() -> None:
    rows = build_return_package_index_matrix(_inventory())
    codes = _codes(rows, "section_code")

    assert "executive_gatekeeper_return_summary" in codes
    assert "phase_17_final_outcome_summary" in codes
    assert "gatekeeper_stabilization_decision_record" in codes
    assert "permission_boundary_summary" in codes
    assert "residual_risk_disclosure" in codes
    assert "source_run_traceability" in codes
    assert "no_persona_review_confirmation" in codes
    assert "no_investor_agent_execution_confirmation" in codes
    assert "no_recommendation_output_confirmation" in codes
    assert "auto_promotion_disabled_confirmation" in codes
    assert "next_gatekeeper_review_questions" in codes


def test_return_package_section_matrix_is_created() -> None:
    inventory = _inventory()
    index = build_return_package_index_matrix(inventory)
    rows = build_return_package_section_matrix(inventory=inventory, index_rows=index)

    assert len(rows) == len(index)
    assert any(row["section_code"] == "permission_boundary_summary" for row in rows)


def test_evidence_reference_matrix_has_required_sources() -> None:
    rows = build_return_package_evidence_reference_matrix(_inventory())
    codes = _codes(rows, "evidence_ref_code")

    assert "phase_17_closure" in codes
    assert "gatekeeper_stabilization_re_review" in codes
    assert "gatekeeper_stabilized_evidence_comparison" in codes
    assert "stabilization_validation_trial" in codes
    assert "targeted_evidence_repairs" in codes
    assert "residual_blocker_work_orders" in codes
    assert "phase_16_closure" in codes
    assert "baseline_gatekeeper_re_evaluation" in codes
    assert "pre_post_repair_comparison" in codes
    assert "controlled_re_run_trial" in codes
    assert "research_audit_trail" in codes


def test_residual_risk_section_has_required_risks() -> None:
    rows = build_return_package_residual_risk_section(_inventory())
    codes = _codes(rows, "risk_code")

    assert "unresolved_material_blocker" in codes
    assert "local_artifact_limitation" in codes
    assert "persona_review_not_allowed" in codes
    assert "investor_agent_execution_not_allowed" in codes
    assert "auto_promotion_disabled" in codes


def test_permission_boundary_section_has_required_boundaries() -> None:
    rows = build_return_package_permission_boundary_section()
    codes = _codes(rows, "permission_code")

    assert "gatekeeper_return_package_preparation" in codes
    assert "actual_gatekeeper_re_review" in codes
    assert "persona_review_preparation" in codes
    assert "actual_persona_review" in codes
    assert "investor_agent_execution" in codes
    assert "investment_recommendation" in codes
    assert "company_ranking" in codes
    assert "trade_signal_generation" in codes
    assert "auto_promotion" in codes


def test_limitation_matrix_has_required_limitations() -> None:
    rows = build_return_package_limitation_matrix()
    codes = _codes(rows, "limitation_code")

    assert "task_133_completed_with_warnings" in codes
    assert "one_component_input_not_ready" in codes
    assert "local_artifact_only_scope" in codes
    assert "no_live_data_refresh" in codes
    assert "no_actual_persona_review" in codes
    assert "no_investor_agent_execution" in codes
    assert "no_recommendations" in codes
    assert "no_rankings" in codes
    assert "no_trade_signals" in codes
    assert "auto_promotion_disabled" in codes


def test_task_135_handoff_manifest_is_created() -> None:
    inventory = _inventory()
    index = build_return_package_index_matrix(inventory)
    evidence = build_return_package_evidence_reference_matrix(inventory)
    limitations = build_return_package_limitation_matrix()
    summary = build_return_package_summary(
        gatekeeper_return_package_run_id="package_run",
        inventory=inventory,
        index_rows=index,
        evidence_rows=evidence,
        limitation_rows=limitations,
    )

    handoff = build_task_135_handoff_manifest(
        report_summary=summary,
        index_rows=index,
        evidence_rows=evidence,
        limitation_rows=limitations,
    )

    assert handoff["future_task_id"] == 135
    assert handoff["future_task_name"] == "Validate Gatekeeper Return Package Completeness"
    assert handoff["execution_allowed_now"] is True
    assert "investor decisions" in handoff["prohibited_outputs"]


def test_assembly_checks_are_satisfied() -> None:
    rows = build_gatekeeper_return_package_assembly_checks()
    codes = _codes(rows, "check_code")

    assert "input_inventory_loaded" in codes
    assert "return_package_index_matrix_created" in codes
    assert "return_package_section_matrix_created" in codes
    assert "task_135_handoff_manifest_created" in codes
    assert "actual_persona_review_not_allowed" in codes
    assert "investor_agents_not_allowed" in codes
    assert "no_recommendation_outputs" in codes
    assert "no_trade_signal_outputs" in codes
    assert "auto_promotion_disabled" in codes
    assert all(row["status"] == "satisfied" for row in rows)


def test_build_return_package_report_has_sections() -> None:
    report = build_gatekeeper_return_package(
        gatekeeper_return_package_run_id="package_run",
        generated_at="2026-06-19T00:00:00+00:00",
        inventory=_inventory(),
    )
    data = report.to_dict()

    assert data["return_package_summary"]
    assert data["return_package_index_matrix"]
    assert data["return_package_section_matrix"]
    assert data["return_package_evidence_reference_matrix"]
    assert data["return_package_residual_risk_section"]
    assert data["return_package_permission_boundary_section"]
    assert data["return_package_limitation_matrix"]
    assert data["task_135_handoff_manifest"]
    assert data["gatekeeper_return_package_assembly_checks"]


def test_write_return_package_report_writes_files(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    files = write_gatekeeper_return_package_report(
        outputs_root=outputs_root,
        gatekeeper_return_input_inventory_run_id="inventory_run",
    )

    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.index_csv_path.is_file()
    assert files.section_csv_path.is_file()
    assert files.evidence_reference_csv_path.is_file()
    assert files.residual_risk_csv_path.is_file()
    assert files.permission_boundary_csv_path.is_file()
    assert files.limitation_csv_path.is_file()
    assert files.task_135_handoff_manifest_path.is_file()
    assert files.checks_csv_path.is_file()
    assert files.latest_manifest_path.is_file()
    markdown = files.markdown_path.read_text(encoding="utf-8")
    assert "## Important Boundary" in markdown
    assert "## Where We Are Now" in markdown
    assert "## Return Package Index Matrix" in markdown
    assert "## Return Package Section Matrix" in markdown
    assert "## Evidence Reference Matrix" in markdown
    assert "## Residual Risk Section" in markdown
    assert "## Permission Boundary Section" in markdown
    assert "## Limitation Matrix" in markdown
    assert "## Task 135 Handoff" in markdown
    assert "## What This Does Not Suggest" in markdown


def test_cli_works_with_explicit_input_inventory_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "assemble-gatekeeper-return-package",
            "--gatekeeper-return-input-inventory-run-id",
            "inventory_run",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "gatekeeper_return_package_run_id=" in result.output
    assert "gatekeeper_return_input_inventory_run_id=inventory_run" in result.output
    assert "current_phase=18 - Gatekeeper Return Package Layer" in result.output
    assert "recommended_next_task=Task 135" in result.output


def test_cli_works_with_auto_latest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "assemble-gatekeeper-return-package",
            "--auto-latest",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "gatekeeper_return_input_inventory_run_id=inventory_run" in result.output
    assert "status=assembled_with_warnings" in result.output
