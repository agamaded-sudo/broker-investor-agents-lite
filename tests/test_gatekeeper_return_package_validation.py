import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.gatekeeper_return.gatekeeper_return_package_assembly import (
    build_gatekeeper_return_package,
)
from broker_agents.gatekeeper_return.gatekeeper_return_package_validation import (
    build_evidence_reference_validation_matrix,
    build_gatekeeper_return_package_validation,
    build_gatekeeper_return_package_validation_checks,
    build_limitation_validation_matrix,
    build_package_validation_summary,
    build_permission_boundary_validation_matrix,
    build_residual_risk_validation_matrix,
    build_safety_boundary_validation_matrix,
    build_section_completeness_matrix,
    build_task_136_handoff_manifest,
    load_gatekeeper_return_package,
    load_gatekeeper_return_package_manifest,
    write_gatekeeper_return_package_validation_report,
)


def _inventory() -> dict:
    components = [
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
    evidence = [
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
    return {
        "gatekeeper_return_input_inventory_run_id": "inventory_run",
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
            "final_gatekeeper_stabilization_outcome": (
                "hold_with_stabilization_progress"
            ),
            "final_progression_status": "gatekeeper_return_package_only",
            "final_persona_review_status": "false",
        },
        "component_input_inventory_matrix": [
            {
                "component_code": code,
                "component_label": code.replace("_", " "),
                "inventory_status": "available_with_warnings"
                if code == "next_gatekeeper_review_questions"
                else "available",
                "inclusion_status": "ready_with_warnings"
                if code == "next_gatekeeper_review_questions"
                else "ready_for_package_assembly",
                "required_follow_up": "Review warning during validation."
                if code == "next_gatekeeper_review_questions"
                else "Carry into Task 134 assembly.",
                "safety_boundary": "Component only.",
            }
            for code in components
        ],
        "evidence_artifact_inventory_matrix": [
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
            for code, phase, task, run_id in evidence
        ],
        "missing_or_warning_input_matrix": [],
        "inventory_status": "completed_with_warnings",
    }


def _package() -> dict:
    return build_gatekeeper_return_package(
        gatekeeper_return_package_run_id="package_run",
        generated_at="2026-06-19T00:00:00+00:00",
        inventory=_inventory(),
    ).to_dict()


def _write_fixture(outputs_root: Path) -> Path:
    package = _package()
    root = outputs_root / "gatekeeper_return_packages"
    folder = root / package["gatekeeper_return_package_run_id"]
    folder.mkdir(parents=True)
    report_path = folder / "gatekeeper_return_package.json"
    report_path.write_text(json.dumps(package), encoding="utf-8")
    (root / "latest_gatekeeper_return_package_manifest.json").write_text(
        json.dumps(
            {
                "gatekeeper_return_package_run_id": package[
                    "gatekeeper_return_package_run_id"
                ],
                "report_json_path": str(report_path),
            }
        ),
        encoding="utf-8",
    )
    return outputs_root


def _codes(rows: list[dict], key: str) -> set[str]:
    return {str(row[key]) for row in rows}


def test_loads_latest_package_manifest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_gatekeeper_return_package_manifest(outputs_root=outputs_root)

    assert manifest["gatekeeper_return_package_run_id"] == "package_run"


def test_loads_explicit_package_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_gatekeeper_return_package_manifest(
        outputs_root=outputs_root,
        gatekeeper_return_package_run_id="package_run",
    )
    report = load_gatekeeper_return_package(
        outputs_root=outputs_root,
        gatekeeper_return_package_run_id="package_run",
    )

    assert manifest["gatekeeper_return_package_run_id"] == "package_run"
    assert report["gatekeeper_return_package_run_id"] == "package_run"


def test_handles_missing_package_manifest(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_gatekeeper_return_package_manifest(outputs_root=tmp_path)


def test_handles_missing_package_report(tmp_path: Path) -> None:
    root = tmp_path / "gatekeeper_return_packages"
    root.mkdir()
    (root / "latest_gatekeeper_return_package_manifest.json").write_text(
        json.dumps({"gatekeeper_return_package_run_id": "missing"}),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError):
        load_gatekeeper_return_package(
            outputs_root=tmp_path,
            gatekeeper_return_package_run_id="missing",
        )


def test_package_validation_summary_is_created() -> None:
    package = _package()
    sections = build_section_completeness_matrix(package)
    evidence = build_evidence_reference_validation_matrix(package)
    residual = build_residual_risk_validation_matrix(package)
    permissions = build_permission_boundary_validation_matrix(package)
    limitations = build_limitation_validation_matrix(package)
    safety = build_safety_boundary_validation_matrix()

    summary = build_package_validation_summary(
        gatekeeper_return_package_validation_run_id="validation_run",
        package=package,
        sections=sections,
        evidence=evidence,
        residual_risks=residual,
        permissions=permissions,
        limitations=limitations,
        safety=safety,
    )

    assert summary["phase_id"] == 18
    assert summary["current_task_id"] == 135
    assert summary["final_gatekeeper_stabilization_outcome"] == (
        "hold_with_stabilization_progress"
    )
    assert summary["final_progression_status"] == "gatekeeper_return_package_only"
    assert summary["final_persona_review_status"] == "false"
    assert summary["source_assembly_status"] == "assembled_with_warnings"
    assert summary["validation_status"] == "complete_with_warnings"
    assert summary["recommended_next_task"].startswith("Task 136")


def test_section_completeness_matrix_has_all_required_sections() -> None:
    rows = build_section_completeness_matrix(_package())
    codes = _codes(rows, "section_code")

    assert "executive_gatekeeper_return_summary" in codes
    assert "phase_17_final_outcome_summary" in codes
    assert "gatekeeper_stabilization_decision_record" in codes
    assert "permission_boundary_summary" in codes
    assert "blocker_disposition_summary" in codes
    assert "residual_risk_disclosure" in codes
    assert "evidence_stabilization_timeline" in codes
    assert "repaired_evidence_inventory" in codes
    assert "validation_evidence_inventory" in codes
    assert "comparison_evidence_inventory" in codes
    assert "source_run_traceability" in codes
    assert "local_artifact_limitation_disclosure" in codes
    assert "no_persona_review_confirmation" in codes
    assert "no_investor_agent_execution_confirmation" in codes
    assert "no_recommendation_output_confirmation" in codes
    assert "auto_promotion_disabled_confirmation" in codes
    assert "next_gatekeeper_review_questions" in codes
    assert all(row["found_in_package"] for row in rows)


def test_evidence_reference_validation_has_all_required_refs() -> None:
    rows = build_evidence_reference_validation_matrix(_package())
    codes = _codes(rows, "evidence_ref_code")

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
    assert all(row["reference_found"] for row in rows)


def test_residual_risk_validation_has_all_required_risks() -> None:
    rows = build_residual_risk_validation_matrix(_package())
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
    assert all(row["found_in_package"] for row in rows)


def test_permission_boundary_validation_preserves_blocks() -> None:
    rows = build_permission_boundary_validation_matrix(_package())
    codes = _codes(rows, "permission_code")
    by_code = {row["permission_code"]: row for row in rows}

    assert "gatekeeper_return_package_preparation" in codes
    assert "actual_gatekeeper_re_review" in codes
    assert "persona_review_preparation" in codes
    assert "actual_persona_review" in codes
    assert "investor_agent_execution" in codes
    assert "investor_decision_generation" in codes
    assert "company_ranking" in codes
    assert "investment_recommendation" in codes
    assert "allocation_or_rebalancing" in codes
    assert "trade_signal_generation" in codes
    assert "auto_promotion" in codes
    assert by_code["actual_persona_review"]["package_status"] == "not_allowed"
    assert by_code["investor_agent_execution"]["package_status"] == "not_allowed"
    assert by_code["auto_promotion"]["package_status"] == "disabled"


def test_limitation_validation_has_all_required_limitations() -> None:
    rows = build_limitation_validation_matrix(_package())
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


def test_safety_boundary_validation_has_all_required_checks() -> None:
    rows = build_safety_boundary_validation_matrix()
    codes = _codes(rows, "safety_code")

    assert "no_investor_agents_run" in codes
    assert "no_actual_persona_review_run" in codes
    assert "no_investor_decisions_created" in codes
    assert "no_recommendations_created" in codes
    assert "no_rankings_created" in codes
    assert "no_allocations_created" in codes
    assert "no_rebalancing_created" in codes
    assert "no_trade_signals_created" in codes
    assert "no_execution_instructions_created" in codes
    assert "no_strategy_validation_created" in codes
    assert "auto_promotion_disabled" in codes
    assert "no_network_calls" in codes
    assert all(row["validation_status"] == "satisfied" for row in rows)


def test_task_136_handoff_manifest_is_created() -> None:
    package = _package()
    report = build_gatekeeper_return_package_validation(
        gatekeeper_return_package_validation_run_id="validation_run",
        generated_at="2026-06-19T00:00:00+00:00",
        package=package,
    )
    handoff = build_task_136_handoff_manifest(
        summary=report.package_validation_summary,
        package_outputs_validated=["gatekeeper_return_package"],
    )

    assert handoff["future_phase_id"] == 18
    assert handoff["future_task_id"] == 136
    assert handoff["readiness_status"] in {
        "ready_for_gatekeeper_return_review",
        "ready_with_warnings",
    }
    assert handoff["execution_allowed_now"] is True
    assert "investor agent execution" in handoff["prohibited_outputs"]
    assert "actual persona reviews" in handoff["prohibited_outputs"]
    assert "recommendations" in handoff["prohibited_outputs"]


def test_validation_checks_are_created() -> None:
    rows = build_gatekeeper_return_package_validation_checks(
        validation_status="complete_with_warnings",
        blocking_findings_total=0,
    )
    codes = _codes(rows, "check_code")

    assert "required_sections_validated" in codes
    assert "evidence_references_validated" in codes
    assert "residual_risks_validated" in codes
    assert "permission_boundaries_validated" in codes
    assert "limitations_validated" in codes
    assert "final_gatekeeper_stabilization_outcome_preserved" in codes
    assert "final_progression_status_preserved" in codes
    assert "final_persona_review_status_preserved" in codes
    assert "gatekeeper_return_package_only_preserved" in codes
    assert "actual_persona_review_not_allowed" in codes
    assert "investor_agents_not_allowed" in codes
    assert "no_recommendation_outputs" in codes
    assert "auto_promotion_disabled" in codes
    assert all(row["status"] == "satisfied" for row in rows)


def test_build_validation_report_has_sections() -> None:
    report = build_gatekeeper_return_package_validation(
        gatekeeper_return_package_validation_run_id="validation_run",
        generated_at="2026-06-19T00:00:00+00:00",
        package=_package(),
    )
    data = report.to_dict()

    assert data["package_validation_summary"]
    assert data["section_completeness_matrix"]
    assert data["evidence_reference_validation_matrix"]
    assert data["residual_risk_validation_matrix"]
    assert data["permission_boundary_validation_matrix"]
    assert data["limitation_validation_matrix"]
    assert data["safety_boundary_validation_matrix"]
    assert data["task_136_handoff_manifest"]
    assert data["gatekeeper_return_package_validation_checks"]


def test_write_validation_report_writes_files(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    files = write_gatekeeper_return_package_validation_report(
        outputs_root=outputs_root,
        gatekeeper_return_package_run_id="package_run",
    )

    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.section_csv_path.is_file()
    assert files.evidence_csv_path.is_file()
    assert files.residual_risk_csv_path.is_file()
    assert files.permission_csv_path.is_file()
    assert files.limitation_csv_path.is_file()
    assert files.safety_csv_path.is_file()
    assert files.task_136_handoff_manifest_path.is_file()
    assert files.checks_csv_path.is_file()
    assert files.latest_manifest_path.is_file()
    markdown = files.markdown_path.read_text(encoding="utf-8")
    assert "## Important Boundary" in markdown
    assert "## Where We Are Now" in markdown
    assert "## Package Validation Summary" in markdown
    assert "## Section Completeness Matrix" in markdown
    assert "## Evidence Reference Validation Matrix" in markdown
    assert "## Residual Risk Validation Matrix" in markdown
    assert "## Permission Boundary Validation Matrix" in markdown
    assert "## Limitation Validation Matrix" in markdown
    assert "## Safety Boundary Validation Matrix" in markdown
    assert "## Task 136 Handoff" in markdown
    assert "## What This Does Not Suggest" in markdown


def test_cli_works_with_explicit_package_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "validate-gatekeeper-return-package",
            "--gatekeeper-return-package-run-id",
            "package_run",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "gatekeeper_return_package_validation_run_id=" in result.output
    assert "gatekeeper_return_package_run_id=package_run" in result.output
    assert "current_phase=18 - Gatekeeper Return Package Layer" in result.output
    assert "recommended_next_task=Task 136" in result.output


def test_cli_works_with_auto_latest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "validate-gatekeeper-return-package",
            "--auto-latest",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "gatekeeper_return_package_run_id=package_run" in result.output
    assert "status=complete_with_warnings" in result.output
