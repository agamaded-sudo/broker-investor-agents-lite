import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.limited_preparation.limited_preparation_governance_plan import (
    build_allowed_preparation_artifact_matrix,
    build_future_gatekeeper_approval_matrix,
    build_limited_preparation_governance_checks,
    build_limited_preparation_governance_plan,
    build_limited_preparation_plan_summary,
    build_limited_preparation_scope_matrix,
    build_phase_19_roadmap_matrix,
    build_prohibited_output_matrix,
    build_task_139_handoff_manifest,
    load_phase_18_closure,
    load_phase_18_closure_manifest,
    write_limited_preparation_governance_plan_report,
)


def _closure() -> dict:
    return {
        "phase_18_closure_run_id": "phase18_run",
        "gatekeeper_return_review_run_id": "review_run",
        "gatekeeper_return_package_validation_run_id": "validation_run",
        "gatekeeper_return_package_run_id": "package_run",
        "phase_18_closure_summary": {
            "final_gatekeeper_return_outcome": (
                "return_package_accepted_for_limited_preparation"
            ),
            "final_post_review_progression_status": "limited_preparation_only",
            "final_post_review_persona_review_status": "false",
        },
        "remaining_warnings_after_phase_18_matrix": [
            {"warning_code": "complete_with_warnings"}
        ],
    }


def _write_fixture(outputs_root: Path) -> Path:
    closure = _closure()
    root = outputs_root / "phase_18_closures"
    folder = root / closure["phase_18_closure_run_id"]
    folder.mkdir(parents=True)
    report_path = folder / "phase_18_closure.json"
    report_path.write_text(json.dumps(closure), encoding="utf-8")
    (root / "latest_phase_18_closure_manifest.json").write_text(
        json.dumps(
            {
                "phase_18_closure_run_id": closure["phase_18_closure_run_id"],
                "report_json_path": str(report_path),
            }
        ),
        encoding="utf-8",
    )
    return outputs_root


def _codes(rows: list[dict], key: str) -> set[str]:
    return {str(row[key]) for row in rows}


def test_loads_latest_phase_18_closure_manifest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_phase_18_closure_manifest(outputs_root=outputs_root)

    assert manifest["phase_18_closure_run_id"] == "phase18_run"


def test_loads_explicit_phase_18_closure_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_phase_18_closure_manifest(
        outputs_root=outputs_root,
        phase_18_closure_run_id="phase18_run",
    )
    closure = load_phase_18_closure(
        outputs_root=outputs_root,
        phase_18_closure_run_id="phase18_run",
    )

    assert manifest["phase_18_closure_run_id"] == "phase18_run"
    assert closure["phase_18_closure_run_id"] == "phase18_run"


def test_handles_missing_phase_18_closure_manifest(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_phase_18_closure_manifest(outputs_root=tmp_path)


def test_handles_missing_phase_18_closure_report(tmp_path: Path) -> None:
    root = tmp_path / "phase_18_closures"
    root.mkdir()
    (root / "latest_phase_18_closure_manifest.json").write_text(
        json.dumps({"phase_18_closure_run_id": "missing"}),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError):
        load_phase_18_closure(
            outputs_root=tmp_path,
            phase_18_closure_run_id="missing",
        )


def test_limited_preparation_plan_summary_is_created() -> None:
    summary = build_limited_preparation_plan_summary(
        limited_preparation_plan_run_id="plan_run",
        closure=_closure(),
    )

    assert summary["phase_id"] == 19
    assert summary["current_task_id"] == 138
    assert summary["source_gatekeeper_return_outcome"] == (
        "return_package_accepted_for_limited_preparation"
    )
    assert summary["source_post_review_progression_status"] == (
        "limited_preparation_only"
    )
    assert summary["source_post_review_persona_review_status"] == "false"
    assert summary["limited_preparation_status"] in {
        "defined",
        "defined_with_warnings",
    }
    assert summary["actual_persona_review_allowed"] is False
    assert summary["investor_agents_allowed"] is False
    assert summary["recommendations_allowed"] is False
    assert summary["rankings_allowed"] is False
    assert summary["allocations_allowed"] is False
    assert summary["trade_signals_allowed"] is False
    assert summary["auto_promotion_status"] == "disabled"
    assert summary["recommended_next_task"].startswith("Task 139")


def test_limited_preparation_scope_matrix_has_required_rows() -> None:
    rows = build_limited_preparation_scope_matrix()
    by_code = {row["scope_code"]: row for row in rows}

    assert by_code["limited_preparation_governance"]["scope_status"] == "allowed"
    assert by_code["artifact_inventory_preparation"]["scope_status"] == "allowed"
    assert by_code["preparation_package_assembly"]["scope_status"] == (
        "future_phase_task"
    )
    assert by_code["preparation_package_validation"]["scope_status"] == (
        "future_phase_task"
    )
    assert by_code["future_gatekeeper_approval_request"]["scope_status"] == (
        "required_before_scope_expansion"
    )
    assert by_code["actual_persona_review"]["scope_status"] == "not_allowed"
    assert by_code["investor_agent_execution"]["scope_status"] == "not_allowed"
    assert by_code["recommendations"]["scope_status"] == "not_allowed"
    assert by_code["rankings"]["scope_status"] == "not_allowed"
    assert by_code["allocations_or_rebalancing"]["scope_status"] == "not_allowed"
    assert by_code["trade_signals"]["scope_status"] == "not_allowed"
    assert by_code["auto_promotion"]["scope_status"] == "disabled"


def test_allowed_preparation_artifact_matrix_has_required_rows() -> None:
    rows = build_allowed_preparation_artifact_matrix()
    codes = _codes(rows, "artifact_code")

    assert "persona_review_readiness_checklist" in codes
    assert "investor_agent_execution_preconditions" in codes
    assert "evidence_pack_structure_outline" in codes
    assert "company_data_pack_completeness_template" in codes
    assert "permission_boundary_checklist" in codes
    assert "residual_risk_follow_up_list" in codes
    assert "gatekeeper_pre_approval_request_template" in codes
    assert "no_recommendation_safety_notice" in codes
    assert "no_ranking_safety_notice" in codes
    assert "no_trade_signal_safety_notice" in codes


def test_prohibited_output_matrix_has_required_rows() -> None:
    rows = build_prohibited_output_matrix()
    codes = _codes(rows, "prohibited_code")

    assert "actual_persona_review" in codes
    assert "investor_agent_execution" in codes
    assert "investor_decision_generation" in codes
    assert "buy_sell_hold_recommendations" in codes
    assert "company_rankings" in codes
    assert "portfolio_allocations" in codes
    assert "portfolio_rebalancing" in codes
    assert "trade_signals" in codes
    assert "execution_instructions" in codes
    assert "strategy_validation" in codes
    assert "auto_promotion" in codes
    assert all(row["final_status"] == "prohibited" for row in rows)


def test_future_gatekeeper_approval_matrix_has_required_rows() -> None:
    rows = build_future_gatekeeper_approval_matrix()
    codes = _codes(rows, "approval_code")

    assert "approval_for_actual_persona_review" in codes
    assert "approval_for_investor_agent_execution" in codes
    assert "approval_for_investor_decision_generation" in codes
    assert "approval_for_company_comparison_or_ranking" in codes
    assert "approval_for_recommendation_language" in codes
    assert "approval_for_allocation_or_trade_signal_language" in codes
    assert "approval_for_auto_promotion_change" in codes
    assert {row["current_status"] for row in rows} == {"required_not_granted"}


def test_phase_19_roadmap_matrix_has_tasks_138_to_143() -> None:
    rows = build_phase_19_roadmap_matrix()
    codes = _codes(rows, "task_id")

    assert {"138", "139", "140", "141", "142", "143"}.issubset(codes)


def test_task_139_handoff_manifest_is_created() -> None:
    summary = build_limited_preparation_plan_summary(
        limited_preparation_plan_run_id="plan_run",
        closure=_closure(),
    )

    handoff = build_task_139_handoff_manifest(plan_summary=summary)

    assert handoff["future_phase_id"] == 19
    assert handoff["future_task_id"] == 139
    assert handoff["readiness_status"] == (
        "ready_to_build_limited_preparation_artifact_inventory"
    )
    assert handoff["execution_allowed_now"] is True
    assert "actual persona reviews" in handoff["prohibited_outputs"]
    assert "investor agent execution" in handoff["prohibited_outputs"]
    assert "recommendations" in handoff["prohibited_outputs"]
    assert "rankings" in handoff["prohibited_outputs"]
    assert "trade signals" in handoff["prohibited_outputs"]


def test_validation_checks_are_created() -> None:
    rows = build_limited_preparation_governance_checks()
    codes = _codes(rows, "check_code")

    assert "phase_18_closure_loaded" in codes
    assert "gatekeeper_return_outcome_preserved" in codes
    assert "limited_preparation_only_preserved" in codes
    assert "persona_review_false_preserved" in codes
    assert "actual_persona_review_not_allowed" in codes
    assert "investor_agents_not_allowed" in codes
    assert "no_recommendation_outputs" in codes
    assert "auto_promotion_disabled" in codes
    assert all(row["status"] == "satisfied" for row in rows)


def test_build_limited_preparation_governance_plan_has_sections() -> None:
    report = build_limited_preparation_governance_plan(
        limited_preparation_plan_run_id="plan_run",
        generated_at="2026-06-19T00:00:00+00:00",
        closure=_closure(),
    )
    data = report.to_dict()

    assert data["limited_preparation_plan_summary"]
    assert data["limited_preparation_scope_matrix"]
    assert data["allowed_preparation_artifact_matrix"]
    assert data["prohibited_output_matrix"]
    assert data["future_gatekeeper_approval_matrix"]
    assert data["phase_19_roadmap_matrix"]
    assert data["task_139_handoff_manifest"]
    assert data["limited_preparation_governance_checks"]


def test_write_limited_preparation_governance_plan_writes_files(
    tmp_path: Path,
) -> None:
    outputs_root = _write_fixture(tmp_path)

    files = write_limited_preparation_governance_plan_report(
        outputs_root=outputs_root,
        phase_18_closure_run_id="phase18_run",
    )

    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.scope_csv_path.is_file()
    assert files.allowed_artifacts_csv_path.is_file()
    assert files.prohibited_outputs_csv_path.is_file()
    assert files.future_gatekeeper_approval_csv_path.is_file()
    assert files.roadmap_csv_path.is_file()
    assert files.task_139_handoff_manifest_path.is_file()
    assert files.checks_csv_path.is_file()
    assert files.latest_manifest_path.is_file()
    markdown = files.markdown_path.read_text(encoding="utf-8")
    assert "## Important Boundary" in markdown
    assert "## Where We Are Now" in markdown
    assert "## Limited Preparation Scope" in markdown
    assert "## Allowed Preparation Artifacts" in markdown
    assert "## Prohibited Outputs" in markdown
    assert "## Future Gatekeeper Approval Requirements" in markdown
    assert "## Phase 19 Roadmap" in markdown
    assert "## Task 139 Handoff" in markdown
    assert "## What This Does Not Suggest" in markdown


def test_cli_works_with_explicit_phase_18_closure_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "define-limited-preparation-governance-plan",
            "--phase-18-closure-run-id",
            "phase18_run",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "limited_preparation_plan_run_id=" in result.output
    assert "phase_18_closure_run_id=phase18_run" in result.output
    assert "current_phase=19 - Limited Preparation Governance Layer" in result.output
    assert "recommended_next_task=Task 139" in result.output


def test_cli_works_with_auto_latest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "define-limited-preparation-governance-plan",
            "--auto-latest",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "phase_18_closure_run_id=phase18_run" in result.output
    assert "status=defined_with_warnings" in result.output
