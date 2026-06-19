import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.stabilization.phase_17_closure import (
    build_final_gatekeeper_stabilization_summary,
    build_final_permission_boundary_summary,
    build_phase_17_closure,
    build_phase_17_closure_checks,
    build_phase_17_closure_summary,
    build_phase_17_task_status_matrix,
    build_phase_18_recommendation_matrix,
    build_remaining_blockers_after_phase_17_matrix,
    build_task_132_handoff_manifest,
    load_gatekeeper_stabilization_re_review,
    load_gatekeeper_stabilization_re_review_manifest,
    write_phase_17_closure_report,
)


def _re_review() -> dict:
    return {
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
        "re_review_summary": {
            "baseline_gatekeeper_outcome": "hold_with_repair_progress",
            "new_gatekeeper_stabilization_outcome": "hold_with_stabilization_progress",
            "progression_status_after_re_review": "gatekeeper_return_package_only",
            "persona_review_status_after_re_review": "false",
            "outcome_confidence": "conservative_moderate",
            "re_review_status": "completed_with_warnings",
            "recommended_next_task": "Task 131 - Phase 17 Closure & Next-Step Decision",
        },
        "stabilization_gatekeeper_decision_record": {
            "auto_promotion_status": "disabled",
            "investor_agent_execution_status": "not_allowed",
            "review_scope_allowed": [
                "phase_17_closure",
                "gatekeeper_return_package_preparation",
            ],
            "review_scope_blocked": [
                "investor decisions",
                "recommendations",
                "rankings",
                "allocations",
                "rebalancing",
                "trade signals",
                "actual persona reviews",
                "auto-promotion",
            ],
        },
        "permission_boundary_matrix": [
            {
                "permission_code": code,
                "permission_label": code.replace("_", " "),
                "status_after_re_review": status,
                "allowed_scope": allowed,
                "blocked_scope": blocked,
                "condition_to_expand_scope": "Future Gatekeeper permission",
                "safety_boundary": "Permission boundary only.",
            }
            for code, status, allowed, blocked in [
                (
                    "progression",
                    "gatekeeper_return_package_only",
                    "gatekeeper return package only",
                    "unrestricted progression",
                ),
                (
                    "gatekeeper_return_package_preparation",
                    "allowed",
                    "prepare closure/review package",
                    "investor-facing action",
                ),
                (
                    "persona_review_preparation",
                    "not_allowed",
                    "none",
                    "actual persona review",
                ),
                ("actual_persona_review", "not_allowed", "none", "running persona review"),
                ("investor_agent_execution", "not_allowed", "none", "agent runs"),
                ("investor_decision_generation", "not_allowed", "none", "decisions"),
                ("company_ranking", "not_allowed", "none", "rankings"),
                ("investment_recommendation", "not_allowed", "none", "recommendations"),
                ("allocation_or_rebalancing", "not_allowed", "none", "allocation"),
                ("trade_signal_generation", "not_allowed", "none", "trade signals"),
                ("auto_promotion", "disabled", "none", "auto-promotion"),
            ]
        ],
        "re_review_status": "completed_with_warnings",
    }


def _write_fixture(outputs_root: Path) -> Path:
    re_review = _re_review()
    root = outputs_root / "gatekeeper_stabilization_re_reviews"
    run_dir = root / re_review["gatekeeper_stabilization_re_review_run_id"]
    run_dir.mkdir(parents=True)
    report_path = run_dir / "gatekeeper_stabilization_re_review.json"
    report_path.write_text(json.dumps(re_review), encoding="utf-8")
    (root / "latest_gatekeeper_stabilization_re_review_manifest.json").write_text(
        json.dumps(
            {
                "gatekeeper_stabilization_re_review_run_id": re_review[
                    "gatekeeper_stabilization_re_review_run_id"
                ],
                "report_json_path": str(report_path),
            }
        ),
        encoding="utf-8",
    )
    return outputs_root


def _codes(rows: list[dict], key: str) -> set[str]:
    return {str(row[key]) for row in rows}


def test_loads_latest_re_review_manifest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_gatekeeper_stabilization_re_review_manifest(outputs_root=outputs_root)

    assert manifest["gatekeeper_stabilization_re_review_run_id"] == "review_run"


def test_loads_explicit_re_review_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_gatekeeper_stabilization_re_review_manifest(
        outputs_root=outputs_root,
        gatekeeper_stabilization_re_review_run_id="review_run",
    )
    report = load_gatekeeper_stabilization_re_review(
        outputs_root=outputs_root,
        gatekeeper_stabilization_re_review_run_id="review_run",
    )

    assert manifest["gatekeeper_stabilization_re_review_run_id"] == "review_run"
    assert report["gatekeeper_stabilization_re_review_run_id"] == "review_run"


def test_handles_missing_re_review_manifest(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_gatekeeper_stabilization_re_review_manifest(outputs_root=tmp_path)


def test_handles_missing_re_review_report(tmp_path: Path) -> None:
    root = tmp_path / "gatekeeper_stabilization_re_reviews"
    root.mkdir()
    (root / "latest_gatekeeper_stabilization_re_review_manifest.json").write_text(
        json.dumps({"gatekeeper_stabilization_re_review_run_id": "missing"}),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError):
        load_gatekeeper_stabilization_re_review(
            outputs_root=tmp_path,
            gatekeeper_stabilization_re_review_run_id="missing",
        )


def test_phase_17_closure_summary_is_created() -> None:
    summary = build_phase_17_closure_summary(
        phase_17_closure_run_id="closure_run",
        re_review=_re_review(),
    )

    assert summary["current_task_id"] == 131
    assert summary["phase_completion_status"] == "completed"
    assert summary["final_gatekeeper_stabilization_outcome"] == (
        "hold_with_stabilization_progress"
    )
    assert summary["final_progression_status"] == "gatekeeper_return_package_only"
    assert summary["final_persona_review_status"] == "false"
    assert summary["final_outcome_confidence"] == "conservative_moderate"
    assert summary["final_auto_promotion_status"] == "disabled"
    assert summary["recommended_next_phase"].startswith("Phase 18")
    assert summary["recommended_next_task"].startswith("Task 132")


def test_phase_17_task_status_matrix_includes_tasks_125_to_131() -> None:
    rows = build_phase_17_task_status_matrix(
        phase_17_closure_run_id="closure_run",
        re_review=_re_review(),
    )

    assert {row["task_id"] for row in rows} == {125, 126, 127, 128, 129, 130, 131}
    assert rows[-1]["next_task_from_artifact"].startswith("Task 132")


def test_final_gatekeeper_summary_preserves_blocked_scope() -> None:
    summary = build_final_gatekeeper_stabilization_summary(_re_review())

    assert summary["baseline_gatekeeper_outcome"] == "hold_with_repair_progress"
    assert summary["final_gatekeeper_stabilization_outcome"] == (
        "hold_with_stabilization_progress"
    )
    assert summary["final_progression_status"] == "gatekeeper_return_package_only"
    assert summary["final_persona_review_status"] == "false"
    assert summary["final_auto_promotion_status"] == "disabled"
    assert "gatekeeper_return_package_only" in summary["final_permission_scope"]
    assert "actual persona review" in summary["final_blocked_scope"]
    assert "investor agent execution" in summary["final_blocked_scope"]
    assert "recommendations" in summary["final_blocked_scope"]


def test_final_permission_boundary_summary_is_created() -> None:
    rows = build_final_permission_boundary_summary(_re_review())
    by_code = {row["permission_code"]: row for row in rows}

    assert by_code["progression"]["final_status"] == "gatekeeper_return_package_only"
    assert by_code["gatekeeper_return_package_preparation"]["final_status"] == "allowed"
    assert by_code["actual_persona_review"]["final_status"] == "not_allowed"
    assert by_code["investor_agent_execution"]["final_status"] == "not_allowed"
    assert by_code["auto_promotion"]["final_status"] == "disabled"


def test_remaining_blockers_after_phase_17_matrix_has_required_blockers() -> None:
    rows = build_remaining_blockers_after_phase_17_matrix()
    codes = _codes(rows, "blocker_code")

    assert "unresolved_material_blockers" in codes
    assert "partially_improved_evidence_blockers" in codes
    assert "persona_review_not_allowed" in codes
    assert "investor_agent_execution_not_allowed" in codes
    assert "local_artifact_limitations" in codes
    assert "residual_metadata_concentration" in codes
    assert "residual_period_sensitivity" in codes
    assert "residual_outlier_dependence" in codes
    assert "gatekeeper_return_package_needed" in codes
    assert "auto_promotion_disabled" in codes


def test_phase_18_recommendation_matrix_has_required_recommendations() -> None:
    rows = build_phase_18_recommendation_matrix()
    by_code = {row["recommendation_code"]: row for row in rows}

    assert by_code["start_phase_18_gatekeeper_return_package_layer"][
        "recommendation_status"
    ] == "recommended_with_warnings"
    assert by_code["define_gatekeeper_return_package_plan"][
        "recommendation_status"
    ] == "recommended"
    assert by_code["preserve_persona_review_block"]["recommendation_status"] == "required"
    assert by_code["preserve_investor_agent_execution_block"][
        "recommendation_status"
    ] == "required"
    assert by_code["preserve_no_recommendations"]["recommendation_status"] == "required"
    assert by_code["preserve_no_rankings"]["recommendation_status"] == "required"
    assert by_code["preserve_no_trade_signals"]["recommendation_status"] == "required"
    assert by_code["preserve_auto_promotion_disabled"][
        "recommendation_status"
    ] == "required"
    assert by_code["prepare_gatekeeper_return_package_only"][
        "recommendation_status"
    ] == "allowed"


def test_task_132_handoff_manifest_is_created() -> None:
    handoff = build_task_132_handoff_manifest(
        phase_17_closure_run_id="closure_run",
        re_review=_re_review(),
    )

    assert handoff["future_phase_id"] == 18
    assert handoff["future_task_id"] == 132
    assert handoff["readiness_status"] == "ready_to_define_gatekeeper_return_package_plan"
    assert handoff["execution_allowed_now"] is True
    assert "investor decisions" in handoff["prohibited_outputs"]
    assert "actual persona reviews" in handoff["prohibited_outputs"]


def test_phase_17_closure_checks_are_created() -> None:
    rows = build_phase_17_closure_checks()
    codes = _codes(rows, "check_code")

    assert "gatekeeper_stabilization_re_review_loaded" in codes
    assert "phase_17_task_status_matrix_created" in codes
    assert "final_gatekeeper_stabilization_summary_created" in codes
    assert "final_permission_boundary_summary_created" in codes
    assert "remaining_blockers_matrix_created" in codes
    assert "phase_18_recommendation_matrix_created" in codes
    assert "task_132_handoff_manifest_created" in codes
    assert "persona_review_block_preserved" in codes
    assert "investor_agent_execution_block_preserved" in codes
    assert "auto_promotion_disabled_preserved" in codes
    assert "no_recommendation_outputs" in codes
    assert "no_ranking_outputs" in codes
    assert "no_trade_signal_outputs" in codes
    assert all(row["status"] == "satisfied" for row in rows)


def test_build_phase_17_closure_report_has_sections() -> None:
    report = build_phase_17_closure(
        phase_17_closure_run_id="closure_run",
        generated_at="2026-06-19T00:00:00+00:00",
        re_review=_re_review(),
    )
    data = report.to_dict()

    assert data["phase_17_closure_summary"]
    assert data["phase_17_task_status_matrix"]
    assert data["final_gatekeeper_stabilization_summary"]
    assert data["final_permission_boundary_summary"]
    assert data["remaining_blockers_after_phase_17_matrix"]
    assert data["phase_18_recommendation_matrix"]
    assert data["task_132_handoff_manifest"]
    assert data["phase_17_closure_checks"]


def test_write_phase_17_closure_report_writes_files(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    files = write_phase_17_closure_report(
        outputs_root=outputs_root,
        gatekeeper_stabilization_re_review_run_id="review_run",
    )

    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.task_status_csv_path.is_file()
    assert files.gatekeeper_summary_csv_path.is_file()
    assert files.permission_summary_csv_path.is_file()
    assert files.remaining_blockers_csv_path.is_file()
    assert files.phase_18_recommendation_csv_path.is_file()
    assert files.task_132_handoff_manifest_path.is_file()
    assert files.checks_csv_path.is_file()
    assert files.latest_manifest_path.is_file()
    markdown = files.markdown_path.read_text(encoding="utf-8")
    assert "## Important Boundary" in markdown
    assert "## Where We Are Now" in markdown
    assert "## Phase 17 Closure Summary" in markdown
    assert "## Phase 17 Task Status Matrix" in markdown
    assert "## Final Gatekeeper Stabilization Summary" in markdown
    assert "## Final Permission Boundary Summary" in markdown
    assert "## Remaining Blockers After Phase 17" in markdown
    assert "## Phase 18 Recommendation Matrix" in markdown
    assert "## Task 132 Handoff Manifest" in markdown
    assert "## What This Does Not Suggest" in markdown


def test_cli_works_with_explicit_re_review_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "close-phase-17",
            "--gatekeeper-stabilization-re-review-run-id",
            "review_run",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "phase_17_closure_run_id=" in result.output
    assert "gatekeeper_stabilization_re_review_run_id=review_run" in result.output
    assert "final_gatekeeper_stabilization_outcome=hold_with_stabilization_progress" in (
        result.output
    )
    assert "recommended_next_task=Task 132" in result.output


def test_cli_works_with_auto_latest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "close-phase-17",
            "--auto-latest",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "gatekeeper_stabilization_re_review_run_id=review_run" in result.output
    assert "closure_status=closed_for_gatekeeper_return_package_only" in result.output
