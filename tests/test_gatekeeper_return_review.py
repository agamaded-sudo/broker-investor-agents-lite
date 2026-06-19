import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.gatekeeper_return.gatekeeper_return_package_assembly import (
    build_gatekeeper_return_package,
)
from broker_agents.gatekeeper_return.gatekeeper_return_package_validation import (
    build_gatekeeper_return_package_validation,
)
from broker_agents.gatekeeper_return.gatekeeper_return_review import (
    build_gatekeeper_return_review,
    build_gatekeeper_return_review_checks,
    build_gatekeeper_return_review_summary,
    build_post_review_allowed_scope_matrix,
    build_post_review_permission_boundary_matrix,
    build_post_review_prohibited_scope_matrix,
    build_residual_risk_disposition_matrix,
    build_return_review_decision_record,
    build_return_review_rule_evaluation_matrix,
    build_task_137_handoff_manifest,
    build_warning_disposition_matrix,
    load_gatekeeper_return_package_validation,
    load_gatekeeper_return_package_validation_manifest,
    write_gatekeeper_return_review_report,
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
                "inclusion_status": "ready_with_warnings"
                if code == "next_gatekeeper_review_questions"
                else "ready_for_package_assembly",
                "required_follow_up": "Review warning."
                if code == "next_gatekeeper_review_questions"
                else "Carry forward.",
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


def _validation() -> dict:
    package = build_gatekeeper_return_package(
        gatekeeper_return_package_run_id="package_run",
        generated_at="2026-06-19T00:00:00+00:00",
        inventory=_inventory(),
    ).to_dict()
    return build_gatekeeper_return_package_validation(
        gatekeeper_return_package_validation_run_id="validation_run",
        generated_at="2026-06-19T00:00:00+00:00",
        package=package,
    ).to_dict()


def _write_fixture(outputs_root: Path) -> Path:
    validation = _validation()
    root = outputs_root / "gatekeeper_return_package_validations"
    folder = root / validation["gatekeeper_return_package_validation_run_id"]
    folder.mkdir(parents=True)
    report_path = folder / "gatekeeper_return_package_validation.json"
    report_path.write_text(json.dumps(validation), encoding="utf-8")
    (root / "latest_gatekeeper_return_package_validation_manifest.json").write_text(
        json.dumps(
            {
                "gatekeeper_return_package_validation_run_id": validation[
                    "gatekeeper_return_package_validation_run_id"
                ],
                "report_json_path": str(report_path),
            }
        ),
        encoding="utf-8",
    )
    return outputs_root


def _codes(rows: list[dict], key: str) -> set[str]:
    return {str(row[key]) for row in rows}


def test_loads_latest_package_validation_manifest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_gatekeeper_return_package_validation_manifest(
        outputs_root=outputs_root,
    )

    assert manifest["gatekeeper_return_package_validation_run_id"] == "validation_run"


def test_loads_explicit_package_validation_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_gatekeeper_return_package_validation_manifest(
        outputs_root=outputs_root,
        gatekeeper_return_package_validation_run_id="validation_run",
    )
    report = load_gatekeeper_return_package_validation(
        outputs_root=outputs_root,
        gatekeeper_return_package_validation_run_id="validation_run",
    )

    assert manifest["gatekeeper_return_package_validation_run_id"] == "validation_run"
    assert report["gatekeeper_return_package_validation_run_id"] == "validation_run"


def test_handles_missing_package_validation_manifest(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_gatekeeper_return_package_validation_manifest(outputs_root=tmp_path)


def test_handles_missing_package_validation_report(tmp_path: Path) -> None:
    root = tmp_path / "gatekeeper_return_package_validations"
    root.mkdir()
    (root / "latest_gatekeeper_return_package_validation_manifest.json").write_text(
        json.dumps({"gatekeeper_return_package_validation_run_id": "missing"}),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError):
        load_gatekeeper_return_package_validation(
            outputs_root=tmp_path,
            gatekeeper_return_package_validation_run_id="missing",
        )


def test_gatekeeper_return_review_summary_is_created() -> None:
    summary = build_gatekeeper_return_review_summary(
        gatekeeper_return_review_run_id="review_run",
        validation=_validation(),
    )

    assert summary["phase_id"] == 18
    assert summary["current_task_id"] == 136
    assert summary["source_validation_status"] == "complete_with_warnings"
    assert summary["source_blocking_findings_total"] == 0
    assert summary["source_warning_findings_total"] == 2
    assert summary["final_gatekeeper_stabilization_outcome"] == (
        "hold_with_stabilization_progress"
    )
    assert summary["final_progression_status_before_review"] == (
        "gatekeeper_return_package_only"
    )
    assert summary["final_persona_review_status_before_review"] == "false"
    assert summary["gatekeeper_return_outcome"] in {
        "return_package_accepted_with_warnings",
        "return_package_accepted_for_limited_preparation",
        "return_package_requires_additional_repair",
        "return_package_hold_pending_manual_review",
        "return_package_blocked_by_permission_boundary",
        "return_package_rejected",
    }
    assert summary["post_review_progression_status"] in {
        "false",
        "gatekeeper_return_package_only",
        "limited_preparation_only",
        "persona_review_preparation_only",
    }
    assert summary["post_review_persona_review_status"] in {"false", "preparation_only"}
    assert summary["review_status"] in {"completed", "completed_with_warnings"}
    assert summary["recommended_next_task"].startswith("Task 137")


def test_decision_record_has_required_rows() -> None:
    summary = build_gatekeeper_return_review_summary(
        gatekeeper_return_review_run_id="review_run",
        validation=_validation(),
    )
    rows = build_return_review_decision_record(summary)
    by_code = {row["decision_code"]: row for row in rows}

    assert "gatekeeper_return_outcome" in by_code
    assert "source_validation_status" in by_code
    assert "blocking_findings_total" in by_code
    assert "warning_findings_total" in by_code
    assert "post_review_progression_status" in by_code
    assert "post_review_persona_review_status" in by_code
    assert by_code["investor_agents_allowed"]["decision_value"] is False
    assert by_code["actual_persona_reviews_allowed"]["decision_value"] is False
    assert by_code["recommendations_allowed"]["decision_value"] is False
    assert by_code["rankings_allowed"]["decision_value"] is False
    assert by_code["allocations_allowed"]["decision_value"] is False
    assert by_code["trade_signals_allowed"]["decision_value"] is False
    assert by_code["auto_promotion_status"]["decision_value"] == "disabled"


def test_rule_evaluation_has_required_rules() -> None:
    rows = build_return_review_rule_evaluation_matrix(_validation())
    codes = _codes(rows, "rule_code")

    assert "validation_complete_enough_for_review" in codes
    assert "no_blocking_findings" in codes
    assert "warning_findings_disclosed" in codes
    assert "all_required_sections_satisfied" in codes
    assert "all_evidence_references_validated" in codes
    assert "residual_risks_disclosed" in codes
    assert "permission_boundaries_validated" in codes
    assert "limitations_disclosed" in codes
    assert "safety_boundaries_satisfied" in codes
    assert "persona_review_still_blocked" in codes
    assert "investor_agents_still_blocked" in codes
    assert "recommendations_still_blocked" in codes
    assert "auto_promotion_disabled" in codes


def test_warning_disposition_has_required_warnings() -> None:
    rows = build_warning_disposition_matrix(_validation())
    codes = _codes(rows, "warning_code")

    assert "validation_complete_with_warnings" in codes
    assert "source_assembly_assembled_with_warnings" in codes
    assert "task_133_completed_with_warnings" in codes
    assert "one_component_input_not_ready" in codes
    assert "local_artifact_only_scope" in codes
    assert "no_live_data_refresh" in codes


def test_residual_risk_disposition_has_required_risks() -> None:
    rows = build_residual_risk_disposition_matrix(_validation())
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


def test_post_review_permission_boundary_preserves_blocks() -> None:
    rows = build_post_review_permission_boundary_matrix()
    by_code = {row["permission_code"]: row for row in rows}

    assert "gatekeeper_return_package_preparation" in by_code
    assert "gatekeeper_return_review" in by_code
    assert "persona_review_preparation" in by_code
    assert by_code["actual_persona_review"]["after_review_status"] == "not_allowed"
    assert by_code["investor_agent_execution"]["after_review_status"] == "not_allowed"
    assert by_code["investor_decision_generation"]["after_review_status"] == "not_allowed"
    assert by_code["company_ranking"]["after_review_status"] == "not_allowed"
    assert by_code["investment_recommendation"]["after_review_status"] == "not_allowed"
    assert by_code["allocation_or_rebalancing"]["after_review_status"] == "not_allowed"
    assert by_code["trade_signal_generation"]["after_review_status"] == "not_allowed"
    assert by_code["auto_promotion"]["after_review_status"] == "disabled"


def test_post_review_allowed_scope_is_limited() -> None:
    rows = build_post_review_allowed_scope_matrix()
    codes = _codes(rows, "allowed_code")
    joined = " ".join(row["allowed_actions"] for row in rows)

    assert "phase_18_closure" in codes
    assert "gatekeeper_return_review_documentation" in codes
    assert "limited_preparation_if_allowed" in codes
    assert "persona_review_preparation_if_allowed" in codes
    assert "residual_risk_follow_up" in codes
    assert "permission_boundary_documentation" in codes
    assert "actual persona review" not in joined
    assert "investor agent execution" not in joined
    assert "recommendations" not in joined
    assert "rankings" not in joined
    assert "allocations" not in joined
    assert "trade signals" not in joined


def test_post_review_prohibited_scope_has_required_items() -> None:
    rows = build_post_review_prohibited_scope_matrix()
    codes = _codes(rows, "prohibited_code")

    assert "actual_persona_review" in codes
    assert "investor_agent_execution" in codes
    assert "investor_decision_generation" in codes
    assert "investment_recommendations" in codes
    assert "company_rankings" in codes
    assert "allocations_or_rebalancing" in codes
    assert "trade_signals" in codes
    assert "execution_instructions" in codes
    assert "strategy_validation" in codes
    assert "auto_promotion" in codes


def test_task_137_handoff_manifest_is_created() -> None:
    summary = build_gatekeeper_return_review_summary(
        gatekeeper_return_review_run_id="review_run",
        validation=_validation(),
    )
    handoff = build_task_137_handoff_manifest(summary)

    assert handoff["future_phase_id"] == 18
    assert handoff["future_task_id"] == 137
    assert handoff["readiness_status"] == "ready_for_phase_18_closure"
    assert handoff["execution_allowed_now"] is True
    assert "investor agent execution" in handoff["prohibited_outputs"]
    assert "actual persona reviews" in handoff["prohibited_outputs"]
    assert "recommendations" in handoff["prohibited_outputs"]


def test_review_checks_are_created() -> None:
    rows = build_gatekeeper_return_review_checks()
    codes = _codes(rows, "check_code")

    assert "validation_status_preserved" in codes
    assert "blocking_findings_preserved" in codes
    assert "warning_findings_preserved" in codes
    assert "final_gatekeeper_stabilization_outcome_preserved" in codes
    assert "pre_review_progression_status_preserved" in codes
    assert "pre_review_persona_review_status_preserved" in codes
    assert "actual_persona_review_not_allowed" in codes
    assert "investor_agents_not_allowed" in codes
    assert "no_recommendation_outputs" in codes
    assert "auto_promotion_disabled" in codes
    assert all(row["status"] == "satisfied" for row in rows)


def test_build_review_report_has_sections() -> None:
    report = build_gatekeeper_return_review(
        gatekeeper_return_review_run_id="review_run",
        generated_at="2026-06-19T00:00:00+00:00",
        validation=_validation(),
    )
    data = report.to_dict()

    assert data["gatekeeper_return_review_summary"]
    assert data["return_review_decision_record"]
    assert data["return_review_rule_evaluation_matrix"]
    assert data["warning_disposition_matrix"]
    assert data["residual_risk_disposition_matrix"]
    assert data["post_review_permission_boundary_matrix"]
    assert data["post_review_allowed_scope_matrix"]
    assert data["post_review_prohibited_scope_matrix"]
    assert data["task_137_handoff_manifest"]
    assert data["gatekeeper_return_review_checks"]


def test_write_review_report_writes_files(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    files = write_gatekeeper_return_review_report(
        outputs_root=outputs_root,
        gatekeeper_return_package_validation_run_id="validation_run",
    )

    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.decision_record_path.is_file()
    assert files.rule_csv_path.is_file()
    assert files.warning_csv_path.is_file()
    assert files.residual_risk_csv_path.is_file()
    assert files.permission_csv_path.is_file()
    assert files.allowed_scope_csv_path.is_file()
    assert files.prohibited_scope_csv_path.is_file()
    assert files.task_137_handoff_manifest_path.is_file()
    assert files.checks_csv_path.is_file()
    assert files.latest_manifest_path.is_file()
    markdown = files.markdown_path.read_text(encoding="utf-8")
    assert "## Important Boundary" in markdown
    assert "## Where We Are Now" in markdown
    assert "## Gatekeeper Return Review Summary" in markdown
    assert "## Decision Record" in markdown
    assert "## Rule Evaluation Matrix" in markdown
    assert "## Warning Disposition" in markdown
    assert "## Residual Risk Disposition" in markdown
    assert "## Post-Review Permission Boundary" in markdown
    assert "## Post-Review Allowed Scope" in markdown
    assert "## Post-Review Prohibited Scope" in markdown
    assert "## Task 137 Handoff" in markdown
    assert "## What This Does Not Suggest" in markdown


def test_cli_works_with_explicit_package_validation_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "run-gatekeeper-return-review",
            "--gatekeeper-return-package-validation-run-id",
            "validation_run",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "gatekeeper_return_review_run_id=" in result.output
    assert "gatekeeper_return_package_validation_run_id=validation_run" in result.output
    assert "current_phase=18 - Gatekeeper Return Package Layer" in result.output
    assert "recommended_next_task=Task 137" in result.output


def test_cli_works_with_auto_latest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "run-gatekeeper-return-review",
            "--auto-latest",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "gatekeeper_return_package_validation_run_id=validation_run" in result.output
    assert "status=completed_with_warnings" in result.output
