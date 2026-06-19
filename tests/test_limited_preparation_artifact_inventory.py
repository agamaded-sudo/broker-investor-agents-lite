import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.limited_preparation.limited_preparation_artifact_inventory import (
    ARTIFACT_ORDER,
    build_allowed_artifact_inventory_matrix,
    build_artifact_assembly_priority_matrix,
    build_artifact_input_requirement_matrix,
    build_artifact_inventory_summary,
    build_artifact_prohibited_content_matrix,
    build_artifact_readiness_matrix,
    build_limited_preparation_artifact_inventory,
    build_limited_preparation_artifact_inventory_checks,
    build_task_140_handoff_manifest,
    build_warning_and_constraint_matrix,
    load_limited_preparation_governance_plan,
    load_limited_preparation_governance_plan_manifest,
    write_limited_preparation_artifact_inventory_report,
)
from broker_agents.limited_preparation.limited_preparation_governance_plan import (
    build_limited_preparation_governance_plan,
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


def _plan() -> dict:
    return build_limited_preparation_governance_plan(
        limited_preparation_plan_run_id="plan_run",
        generated_at="2026-06-19T00:00:00+00:00",
        closure=_closure(),
    ).to_dict()


def _write_fixture(outputs_root: Path) -> Path:
    plan = _plan()
    root = outputs_root / "limited_preparation_governance_plans"
    folder = root / plan["limited_preparation_plan_run_id"]
    folder.mkdir(parents=True)
    report_path = folder / "limited_preparation_governance_plan.json"
    report_path.write_text(json.dumps(plan), encoding="utf-8")
    (root / "latest_limited_preparation_governance_plan_manifest.json").write_text(
        json.dumps(
            {
                "limited_preparation_plan_run_id": plan[
                    "limited_preparation_plan_run_id"
                ],
                "report_json_path": str(report_path),
            }
        ),
        encoding="utf-8",
    )
    return outputs_root


def _codes(rows: list[dict], key: str) -> set[str]:
    return {str(row[key]) for row in rows}


def test_loads_latest_governance_plan_manifest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_limited_preparation_governance_plan_manifest(
        outputs_root=outputs_root
    )

    assert manifest["limited_preparation_plan_run_id"] == "plan_run"


def test_loads_explicit_governance_plan_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_limited_preparation_governance_plan_manifest(
        outputs_root=outputs_root,
        limited_preparation_plan_run_id="plan_run",
    )
    plan = load_limited_preparation_governance_plan(
        outputs_root=outputs_root,
        limited_preparation_plan_run_id="plan_run",
    )

    assert manifest["limited_preparation_plan_run_id"] == "plan_run"
    assert plan["limited_preparation_plan_run_id"] == "plan_run"


def test_handles_missing_governance_plan_manifest(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_limited_preparation_governance_plan_manifest(outputs_root=tmp_path)


def test_handles_missing_governance_plan_report(tmp_path: Path) -> None:
    root = tmp_path / "limited_preparation_governance_plans"
    root.mkdir()
    (root / "latest_limited_preparation_governance_plan_manifest.json").write_text(
        json.dumps({"limited_preparation_plan_run_id": "missing"}),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError):
        load_limited_preparation_governance_plan(
            outputs_root=tmp_path,
            limited_preparation_plan_run_id="missing",
        )


def test_artifact_inventory_summary_is_created() -> None:
    plan = _plan()
    allowed = build_allowed_artifact_inventory_matrix(plan)
    readiness = build_artifact_readiness_matrix(plan)

    summary = build_artifact_inventory_summary(
        inventory_run_id="inventory_run",
        plan=plan,
        allowed_rows=allowed,
        readiness_rows=readiness,
    )

    assert summary["phase_id"] == 19
    assert summary["current_task_id"] == 139
    assert summary["source_gatekeeper_return_outcome"] == (
        "return_package_accepted_for_limited_preparation"
    )
    assert summary["source_post_review_progression_status"] == (
        "limited_preparation_only"
    )
    assert summary["source_post_review_persona_review_status"] == "false"
    assert summary["artifact_inventory_status"] in {
        "complete",
        "complete_with_warnings",
    }
    assert summary["actual_persona_review_allowed"] is False
    assert summary["investor_agents_allowed"] is False
    assert summary["recommendations_allowed"] is False
    assert summary["rankings_allowed"] is False
    assert summary["allocations_allowed"] is False
    assert summary["trade_signals_allowed"] is False
    assert summary["auto_promotion_status"] == "disabled"
    assert summary["recommended_next_task"].startswith("Task 140")


def test_allowed_artifact_inventory_matrix_has_required_rows() -> None:
    rows = build_allowed_artifact_inventory_matrix(_plan())
    codes = _codes(rows, "artifact_code")

    assert set(ARTIFACT_ORDER).issubset(codes)
    assert all(row["assembly_candidate"] is True for row in rows)
    assert all("Preparation-only" in row["safety_boundary"] for row in rows)


def test_artifact_input_requirement_matrix_has_required_inputs() -> None:
    rows = build_artifact_input_requirement_matrix(_plan())
    codes = _codes(rows, "required_input_code")

    assert "phase_18_closure" in codes
    assert "gatekeeper_return_review" in codes
    assert "limited_preparation_governance_plan" in codes
    assert "limited_preparation_scope_matrix" in codes
    assert "allowed_preparation_artifact_matrix" in codes
    assert "prohibited_output_matrix" in codes
    assert "future_gatekeeper_approval_matrix" in codes
    assert "phase_19_roadmap_matrix" in codes


def test_artifact_prohibited_content_matrix_has_required_content() -> None:
    rows = build_artifact_prohibited_content_matrix()
    codes = _codes(rows, "prohibited_content_code")

    assert "actual_persona_judgment" in codes
    assert "investor_agent_execution" in codes
    assert "investor_decision" in codes
    assert "recommendation_language" in codes
    assert "ranking_language" in codes
    assert "allocation_language" in codes
    assert "rebalancing_language" in codes
    assert "trade_signal_language" in codes
    assert "execution_instruction_language" in codes
    assert "strategy_validation_language" in codes
    assert "auto_promotion_language" in codes


def test_artifact_readiness_matrix_blocks_no_prohibited_scope() -> None:
    rows = build_artifact_readiness_matrix(_plan())
    joined = " ".join(row["safety_boundary"] for row in rows)

    assert rows
    assert all(row["allowed_to_assemble_in_task_140"] is True for row in rows)
    assert "does not allow persona review" in joined
    assert "investor execution" in joined
    assert "recommendations" in joined
    assert "rankings" in joined
    assert "trade signals" in joined


def test_artifact_assembly_priority_matrix_has_required_order() -> None:
    rows = build_artifact_assembly_priority_matrix()

    assert rows[0]["artifact_code"] == "permission_boundary_checklist"
    assert rows[1]["artifact_code"] == "no_recommendation_safety_notice"
    assert rows[2]["artifact_code"] == "no_ranking_safety_notice"
    assert rows[3]["artifact_code"] == "no_trade_signal_safety_notice"
    assert rows[4]["artifact_code"] == "evidence_pack_structure_outline"
    assert rows[5]["artifact_code"] == "company_data_pack_completeness_template"
    assert rows[6]["artifact_code"] == "persona_review_readiness_checklist"
    assert rows[7]["artifact_code"] == "investor_agent_execution_preconditions"
    assert rows[8]["artifact_code"] == "residual_risk_follow_up_list"
    assert rows[-1]["artifact_code"] == "gatekeeper_pre_approval_request_template"


def test_warning_and_constraint_matrix_has_required_warnings() -> None:
    rows = build_warning_and_constraint_matrix(_plan())
    codes = _codes(rows, "warning_code")

    assert "limited_preparation_defined_with_warnings" in codes
    assert "phase_18_closed_for_limited_preparation_only" in codes
    assert "persona_review_false" in codes
    assert "investor_agents_not_allowed" in codes
    assert "recommendations_not_allowed" in codes
    assert "rankings_not_allowed" in codes
    assert "trade_signals_not_allowed" in codes
    assert "auto_promotion_disabled" in codes
    assert "local_artifact_only_scope" in codes
    assert "future_gatekeeper_approval_required" in codes


def test_task_140_handoff_manifest_is_created() -> None:
    plan = _plan()
    allowed = build_allowed_artifact_inventory_matrix(plan)
    readiness = build_artifact_readiness_matrix(plan)
    summary = build_artifact_inventory_summary(
        inventory_run_id="inventory_run",
        plan=plan,
        allowed_rows=allowed,
        readiness_rows=readiness,
    )

    handoff = build_task_140_handoff_manifest(summary=summary, allowed_rows=allowed)

    assert handoff["future_phase_id"] == 19
    assert handoff["future_task_id"] == 140
    assert handoff["readiness_status"] in {
        "ready_to_assemble_limited_preparation_package",
        "ready_with_warnings",
    }
    assert handoff["execution_allowed_now"] is True
    assert "actual persona reviews" in handoff["prohibited_outputs"]
    assert "investor agent execution" in handoff["prohibited_outputs"]
    assert "recommendations" in handoff["prohibited_outputs"]
    assert "rankings" in handoff["prohibited_outputs"]
    assert "trade signals" in handoff["prohibited_outputs"]


def test_validation_checks_are_created() -> None:
    rows = build_limited_preparation_artifact_inventory_checks()
    codes = _codes(rows, "check_code")

    assert "limited_preparation_governance_plan_loaded" in codes
    assert "limited_preparation_only_preserved" in codes
    assert "persona_review_false_preserved" in codes
    assert "actual_persona_review_not_allowed" in codes
    assert "investor_agents_not_allowed" in codes
    assert "no_recommendation_outputs" in codes
    assert "auto_promotion_disabled" in codes
    assert all(row["status"] == "satisfied" for row in rows)


def test_build_artifact_inventory_has_sections() -> None:
    report = build_limited_preparation_artifact_inventory(
        inventory_run_id="inventory_run",
        generated_at="2026-06-19T00:00:00+00:00",
        plan=_plan(),
    )
    data = report.to_dict()

    assert data["artifact_inventory_summary"]
    assert data["allowed_artifact_inventory_matrix"]
    assert data["artifact_input_requirement_matrix"]
    assert data["artifact_prohibited_content_matrix"]
    assert data["artifact_readiness_matrix"]
    assert data["artifact_assembly_priority_matrix"]
    assert data["warning_and_constraint_matrix"]
    assert data["task_140_handoff_manifest"]
    assert data["limited_preparation_artifact_inventory_checks"]


def test_write_artifact_inventory_report_writes_files(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    files = write_limited_preparation_artifact_inventory_report(
        outputs_root=outputs_root,
        limited_preparation_plan_run_id="plan_run",
    )

    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.allowed_artifacts_csv_path.is_file()
    assert files.input_requirements_csv_path.is_file()
    assert files.prohibited_content_csv_path.is_file()
    assert files.readiness_csv_path.is_file()
    assert files.assembly_priority_csv_path.is_file()
    assert files.warnings_csv_path.is_file()
    assert files.task_140_handoff_manifest_path.is_file()
    assert files.checks_csv_path.is_file()
    assert files.latest_manifest_path.is_file()
    markdown = files.markdown_path.read_text(encoding="utf-8")
    assert "## Important Boundary" in markdown
    assert "## Where We Are Now" in markdown
    assert "## Allowed Artifact Inventory" in markdown
    assert "## Artifact Input Requirements" in markdown
    assert "## Artifact Prohibited Content" in markdown
    assert "## Artifact Readiness" in markdown
    assert "## Artifact Assembly Priority" in markdown
    assert "## Warnings and Constraints" in markdown
    assert "## Task 140 Handoff" in markdown
    assert "## What This Does Not Suggest" in markdown


def test_cli_works_with_explicit_governance_plan_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "build-limited-preparation-artifact-inventory",
            "--limited-preparation-plan-run-id",
            "plan_run",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "limited_preparation_artifact_inventory_run_id=" in result.output
    assert "limited_preparation_plan_run_id=plan_run" in result.output
    assert "current_phase=19 - Limited Preparation Governance Layer" in result.output
    assert "recommended_next_task=Task 140" in result.output


def test_cli_works_with_auto_latest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "build-limited-preparation-artifact-inventory",
            "--auto-latest",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "limited_preparation_plan_run_id=plan_run" in result.output
    assert "status=complete_with_warnings" in result.output
