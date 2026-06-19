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
)
from broker_agents.gatekeeper_return.phase_18_closure import (
    build_final_allowed_scope_summary,
    build_final_gatekeeper_return_outcome_summary,
    build_final_post_review_permission_boundary_summary,
    build_final_prohibited_scope_summary,
    build_phase_18_closure,
    build_phase_18_closure_checks,
    build_phase_18_closure_summary,
    build_phase_18_task_status_matrix,
    build_phase_19_recommendation_matrix,
    build_remaining_warnings_after_phase_18_matrix,
    build_task_138_handoff_manifest,
    load_gatekeeper_return_review,
    load_gatekeeper_return_review_manifest,
    write_phase_18_closure_report,
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
                "required_follow_up": "Review warning.",
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


def _review() -> dict:
    package = build_gatekeeper_return_package(
        gatekeeper_return_package_run_id="package_run",
        generated_at="2026-06-19T00:00:00+00:00",
        inventory=_inventory(),
    ).to_dict()
    validation = build_gatekeeper_return_package_validation(
        gatekeeper_return_package_validation_run_id="validation_run",
        generated_at="2026-06-19T00:00:00+00:00",
        package=package,
    ).to_dict()
    return build_gatekeeper_return_review(
        gatekeeper_return_review_run_id="review_run",
        generated_at="2026-06-19T00:00:00+00:00",
        validation=validation,
    ).to_dict()


def _write_fixture(outputs_root: Path) -> Path:
    review = _review()
    root = outputs_root / "gatekeeper_return_reviews"
    folder = root / review["gatekeeper_return_review_run_id"]
    folder.mkdir(parents=True)
    report_path = folder / "gatekeeper_return_review.json"
    report_path.write_text(json.dumps(review), encoding="utf-8")
    (root / "latest_gatekeeper_return_review_manifest.json").write_text(
        json.dumps(
            {
                "gatekeeper_return_review_run_id": review[
                    "gatekeeper_return_review_run_id"
                ],
                "report_json_path": str(report_path),
            }
        ),
        encoding="utf-8",
    )
    return outputs_root


def _codes(rows: list[dict], key: str) -> set[str]:
    return {str(row[key]) for row in rows}


def test_loads_latest_gatekeeper_return_review_manifest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_gatekeeper_return_review_manifest(outputs_root=outputs_root)

    assert manifest["gatekeeper_return_review_run_id"] == "review_run"


def test_loads_explicit_gatekeeper_return_review_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_gatekeeper_return_review_manifest(
        outputs_root=outputs_root,
        gatekeeper_return_review_run_id="review_run",
    )
    report = load_gatekeeper_return_review(
        outputs_root=outputs_root,
        gatekeeper_return_review_run_id="review_run",
    )

    assert manifest["gatekeeper_return_review_run_id"] == "review_run"
    assert report["gatekeeper_return_review_run_id"] == "review_run"


def test_handles_missing_gatekeeper_return_review_manifest(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_gatekeeper_return_review_manifest(outputs_root=tmp_path)


def test_handles_missing_gatekeeper_return_review_report(tmp_path: Path) -> None:
    root = tmp_path / "gatekeeper_return_reviews"
    root.mkdir()
    (root / "latest_gatekeeper_return_review_manifest.json").write_text(
        json.dumps({"gatekeeper_return_review_run_id": "missing"}),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError):
        load_gatekeeper_return_review(
            outputs_root=tmp_path,
            gatekeeper_return_review_run_id="missing",
        )


def test_phase_18_closure_summary_is_created() -> None:
    summary = build_phase_18_closure_summary(
        phase_18_closure_run_id="closure_run",
        review=_review(),
    )

    assert summary["phase_id"] == 18
    assert summary["current_task_id"] == 137
    assert summary["phase_completion_status"] == "completed"
    assert summary["final_gatekeeper_return_outcome"] == (
        "return_package_accepted_for_limited_preparation"
    )
    assert summary["final_post_review_progression_status"] == (
        "limited_preparation_only"
    )
    assert summary["final_post_review_persona_review_status"] == "false"
    assert summary["closure_status"] in {
        "closed_for_limited_preparation_only",
        "completed_with_warnings",
    }
    assert summary["recommended_next_phase"] == (
        "Phase 19 - Limited Preparation Governance Layer"
    )
    assert summary["recommended_next_task"].startswith("Task 138")


def test_phase_18_task_status_matrix_has_tasks_132_to_137() -> None:
    rows = build_phase_18_task_status_matrix(
        closure_run_id="closure_run",
        review=_review(),
    )
    codes = _codes(rows, "task_id")

    assert {"132", "133", "134", "135", "136", "137"}.issubset(codes)


def test_final_gatekeeper_return_outcome_summary_is_created() -> None:
    summary = build_final_gatekeeper_return_outcome_summary(_review())

    assert summary["gatekeeper_return_outcome"] == (
        "return_package_accepted_for_limited_preparation"
    )
    assert summary["source_validation_status"] == "complete_with_warnings"
    assert summary["source_blocking_findings_total"] == 0
    assert summary["source_warning_findings_total"] == 2
    assert summary["post_review_progression_status"] == "limited_preparation_only"
    assert summary["post_review_persona_review_status"] == "false"
    blocked = " ".join(summary["blocked_scope"])
    assert "investor agent execution" in blocked
    assert "actual persona review" in blocked
    assert "recommendations" in blocked


def test_final_permission_boundary_summary_preserves_blocks() -> None:
    rows = build_final_post_review_permission_boundary_summary()
    by_code = {row["permission_code"]: row for row in rows}

    assert by_code["limited_preparation"]["final_status"] == "allowed"
    assert by_code["actual_persona_review"]["final_status"] == "not_allowed"
    assert by_code["investor_agent_execution"]["final_status"] == "not_allowed"
    assert by_code["auto_promotion"]["final_status"] == "disabled"
    assert "persona_review_preparation" in by_code
    assert "execution_instruction_generation" in by_code


def test_final_allowed_scope_summary_is_limited() -> None:
    rows = build_final_allowed_scope_summary()
    codes = _codes(rows, "allowed_code")
    joined = " ".join(row["allowed_actions"] for row in rows)

    assert "phase_18_closure" in codes
    assert "limited_preparation_governance_planning" in codes
    assert "limited_preparation_artifact_definition" in codes
    assert "residual_risk_follow_up_planning" in codes
    assert "permission_boundary_documentation" in codes
    assert "next_phase_planning" in codes
    assert "actual persona review" not in joined
    assert "investor agent execution" not in joined
    assert "recommendations" not in joined
    assert "rankings" not in joined
    assert "allocations" not in joined
    assert "trade signals" not in joined


def test_final_prohibited_scope_summary_has_required_items() -> None:
    rows = build_final_prohibited_scope_summary()
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


def test_remaining_warnings_matrix_has_required_warnings() -> None:
    rows = build_remaining_warnings_after_phase_18_matrix()
    codes = _codes(rows, "warning_code")

    assert "complete_with_warnings" in codes
    assert "assembled_with_warnings" in codes
    assert "task_133_completed_with_warnings" in codes
    assert "validation_warning_findings" in codes
    assert "local_artifact_only_scope" in codes
    assert "no_live_data_refresh" in codes
    assert "residual_risk_constraints" in codes
    assert "persona_review_not_allowed" in codes
    assert "investor_agents_not_allowed" in codes
    assert "auto_promotion_disabled" in codes


def test_phase_19_recommendation_matrix_has_required_rows() -> None:
    rows = build_phase_19_recommendation_matrix()
    codes = _codes(rows, "recommendation_code")
    by_code = {row["recommendation_code"]: row for row in rows}

    assert "start_phase_19_limited_preparation_governance_layer" in codes
    assert "define_limited_preparation_governance_plan" in codes
    assert "preserve_actual_persona_review_block" in codes
    assert "preserve_investor_agent_execution_block" in codes
    assert "preserve_no_recommendations" in codes
    assert "preserve_no_rankings" in codes
    assert "preserve_no_trade_signals" in codes
    assert "preserve_auto_promotion_disabled" in codes
    assert "define_preparation_artifacts_only" in codes
    assert "require_future_gatekeeper_approval_before_persona_review" in codes
    assert by_code["start_phase_19_limited_preparation_governance_layer"][
        "recommendation_status"
    ] == "recommended_with_warnings"


def test_task_138_handoff_manifest_is_created() -> None:
    review = _review()
    closure_summary = build_phase_18_closure_summary(
        phase_18_closure_run_id="closure_run",
        review=review,
    )
    handoff = build_task_138_handoff_manifest(
        closure_summary=closure_summary,
        review=review,
    )

    assert handoff["future_phase_id"] == 19
    assert handoff["future_task_id"] == 138
    assert handoff["readiness_status"] == (
        "ready_to_define_limited_preparation_governance_plan"
    )
    assert handoff["execution_allowed_now"] is True
    assert "investor agent execution" in handoff["prohibited_outputs"]
    assert "actual persona reviews" in handoff["prohibited_outputs"]
    assert "recommendations" in handoff["prohibited_outputs"]


def test_phase_18_closure_checks_are_created() -> None:
    rows = build_phase_18_closure_checks()
    codes = _codes(rows, "check_code")

    assert "gatekeeper_return_outcome_preserved" in codes
    assert "post_review_progression_status_preserved" in codes
    assert "post_review_persona_review_status_preserved" in codes
    assert "limited_preparation_only_preserved" in codes
    assert "actual_persona_review_not_allowed" in codes
    assert "investor_agents_not_allowed" in codes
    assert "no_recommendation_outputs" in codes
    assert "auto_promotion_disabled" in codes
    assert all(row["status"] == "satisfied" for row in rows)


def test_build_phase_18_closure_report_has_sections() -> None:
    report = build_phase_18_closure(
        phase_18_closure_run_id="closure_run",
        generated_at="2026-06-19T00:00:00+00:00",
        review=_review(),
    )
    data = report.to_dict()

    assert data["phase_18_closure_summary"]
    assert data["phase_18_task_status_matrix"]
    assert data["final_gatekeeper_return_outcome_summary"]
    assert data["final_post_review_permission_boundary_summary"]
    assert data["final_allowed_scope_summary"]
    assert data["final_prohibited_scope_summary"]
    assert data["remaining_warnings_after_phase_18_matrix"]
    assert data["phase_19_recommendation_matrix"]
    assert data["task_138_handoff_manifest"]
    assert data["phase_18_closure_checks"]


def test_write_phase_18_closure_report_writes_files(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    files = write_phase_18_closure_report(
        outputs_root=outputs_root,
        gatekeeper_return_review_run_id="review_run",
    )

    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.task_status_csv_path.is_file()
    assert files.outcome_csv_path.is_file()
    assert files.permission_csv_path.is_file()
    assert files.allowed_scope_csv_path.is_file()
    assert files.prohibited_scope_csv_path.is_file()
    assert files.warnings_csv_path.is_file()
    assert files.recommendation_csv_path.is_file()
    assert files.task_138_handoff_manifest_path.is_file()
    assert files.checks_csv_path.is_file()
    assert files.latest_manifest_path.is_file()
    markdown = files.markdown_path.read_text(encoding="utf-8")
    assert "## Important Boundary" in markdown
    assert "## Where We Are Now" in markdown
    assert "## Phase 18 Task Status Matrix" in markdown
    assert "## Final Gatekeeper Return Outcome Summary" in markdown
    assert "## Final Permission Boundary Summary" in markdown
    assert "## Final Allowed Scope Summary" in markdown
    assert "## Final Prohibited Scope Summary" in markdown
    assert "## Remaining Warnings After Phase 18" in markdown
    assert "## Phase 19 Recommendation Matrix" in markdown
    assert "## Task 138 Handoff" in markdown
    assert "## What This Does Not Suggest" in markdown


def test_cli_works_with_explicit_gatekeeper_return_review_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "close-phase-18",
            "--gatekeeper-return-review-run-id",
            "review_run",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "phase_18_closure_run_id=" in result.output
    assert "gatekeeper_return_review_run_id=review_run" in result.output
    assert "current_phase=18 - Gatekeeper Return Package Layer" in result.output
    assert "recommended_next_task=Task 138" in result.output


def test_cli_works_with_auto_latest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "close-phase-18",
            "--auto-latest",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "gatekeeper_return_review_run_id=review_run" in result.output
    assert "status=closed_for_limited_preparation_only" in result.output
