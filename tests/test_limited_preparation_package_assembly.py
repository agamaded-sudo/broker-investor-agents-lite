import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.limited_preparation.limited_preparation_artifact_inventory import (
    build_limited_preparation_artifact_inventory,
)
from broker_agents.limited_preparation.limited_preparation_governance_plan import (
    build_limited_preparation_governance_plan,
)
from broker_agents.limited_preparation.limited_preparation_package_assembly import (
    ARTIFACT_ORDER,
    build_limited_preparation_package,
    build_limited_preparation_package_assembly_checks,
    build_limited_preparation_package_future_approval_matrix,
    build_limited_preparation_package_index_matrix,
    build_limited_preparation_package_permission_boundary_matrix,
    build_limited_preparation_package_prohibited_output_matrix,
    build_limited_preparation_package_warning_matrix,
    load_limited_preparation_artifact_inventory,
    load_limited_preparation_artifact_inventory_manifest,
    write_limited_preparation_package_report,
)


def _closure() -> dict:
    return {
        "phase_18_closure_run_id": "phase18_run",
        "gatekeeper_return_review_run_id": "review_run",
        "gatekeeper_return_package_validation_run_id": "validation_run",
        "gatekeeper_return_package_run_id": "package_run",
        "phase_18_closure_summary": {
            "final_gatekeeper_return_outcome": "return_package_accepted_for_limited_preparation",
            "final_post_review_progression_status": "limited_preparation_only",
            "final_post_review_persona_review_status": "false",
        },
        "remaining_warnings_after_phase_18_matrix": [{"warning_code": "warning"}],
    }


def _inventory() -> dict:
    plan = build_limited_preparation_governance_plan(
        limited_preparation_plan_run_id="plan_run",
        generated_at="2026-06-19T00:00:00+00:00",
        closure=_closure(),
    ).to_dict()
    return build_limited_preparation_artifact_inventory(
        inventory_run_id="inventory_run",
        generated_at="2026-06-19T00:00:00+00:00",
        plan=plan,
    ).to_dict()


def _write_fixture(root: Path) -> Path:
    inventory = _inventory()
    folder = root / "limited_preparation_artifact_inventories" / "inventory_run"
    folder.mkdir(parents=True)
    report_path = folder / "limited_preparation_artifact_inventory.json"
    report_path.write_text(json.dumps(inventory), encoding="utf-8")
    (folder.parent / "latest_limited_preparation_artifact_inventory_manifest.json").write_text(
        json.dumps({"limited_preparation_artifact_inventory_run_id": "inventory_run"}),
        encoding="utf-8",
    )
    return root


def _codes(rows: list[dict], key: str) -> set[str]:
    return {str(row[key]) for row in rows}


def test_loads_latest_and_explicit_inventory(tmp_path: Path) -> None:
    root = _write_fixture(tmp_path)
    assert (
        load_limited_preparation_artifact_inventory_manifest(outputs_root=root)[
            "limited_preparation_artifact_inventory_run_id"
        ]
        == "inventory_run"
    )
    assert (
        load_limited_preparation_artifact_inventory_manifest(
            outputs_root=root, limited_preparation_artifact_inventory_run_id="inventory_run"
        )["limited_preparation_artifact_inventory_run_id"]
        == "inventory_run"
    )
    assert (
        load_limited_preparation_artifact_inventory(
            outputs_root=root, limited_preparation_artifact_inventory_run_id="inventory_run"
        )["limited_preparation_artifact_inventory_run_id"]
        == "inventory_run"
    )


def test_handles_missing_inventory_inputs(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_limited_preparation_artifact_inventory_manifest(outputs_root=tmp_path)
    with pytest.raises(FileNotFoundError):
        load_limited_preparation_artifact_inventory(
            outputs_root=tmp_path, limited_preparation_artifact_inventory_run_id="missing"
        )


def test_package_summary_has_expected_status_and_counts() -> None:
    report = build_limited_preparation_package(
        package_run_id="package_run",
        generated_at="2026-06-19T00:00:00+00:00",
        inventory=_inventory(),
    )
    summary = report.limited_preparation_package_summary
    assert summary["phase_id"] == 19
    assert summary["current_task_id"] == 140
    assert (
        summary["source_gatekeeper_return_outcome"]
        == "return_package_accepted_for_limited_preparation"
    )
    assert summary["source_post_review_progression_status"] == "limited_preparation_only"
    assert summary["source_post_review_persona_review_status"] == "false"
    assert summary["source_artifact_inventory_status"] == "complete_with_warnings"
    assert summary["package_assembly_status"] == "assembled_with_warnings"
    assert (
        summary["artifacts_total"],
        summary["artifacts_included"],
        summary["artifacts_included_with_warnings"],
        summary["artifacts_blocked"],
    ) == (10, 10, 10, 0)
    assert summary["recommended_next_task"].startswith("Task 141")


def test_index_and_artifact_sections_cover_required_items() -> None:
    index = build_limited_preparation_package_index_matrix()
    codes = _codes(index, "package_section_code")
    assert {
        "executive_summary",
        "limited_preparation_boundary",
        "future_gatekeeper_approval_requirements",
        "prohibited_outputs_summary",
        "task_141_handoff",
    }.issubset(codes)
    assert set(ARTIFACT_ORDER).issubset(codes)
    report = build_limited_preparation_package(
        package_run_id="package_run",
        generated_at="2026-06-19T00:00:00+00:00",
        inventory=_inventory(),
    )
    assert _codes(
        report.limited_preparation_package_artifact_section_matrix, "artifact_code"
    ) == set(ARTIFACT_ORDER)
    joined = " ".join(
        row["safety_boundary"] for row in report.limited_preparation_package_artifact_section_matrix
    )
    assert (
        "No investor analysis" in joined
        and "persona judgment" in joined
        and "recommendations" in joined
        and "rankings" in joined
        and "trade signals" in joined
    )


def test_warning_permission_prohibited_and_approval_matrices_preserve_blocks() -> None:
    assert {
        "artifacts_ready_with_warnings",
        "limited_preparation_only",
        "persona_review_false",
        "investor_agents_not_allowed",
        "recommendations_not_allowed",
        "rankings_not_allowed",
        "trade_signals_not_allowed",
        "auto_promotion_disabled",
        "future_gatekeeper_approval_required",
        "local_artifact_only_scope",
    }.issubset(_codes(build_limited_preparation_package_warning_matrix(), "warning_code"))
    permissions = {
        row["permission_code"]: row["package_status"]
        for row in build_limited_preparation_package_permission_boundary_matrix()
    }
    assert permissions["limited_preparation_package_assembly"] == "allowed"
    assert permissions["package_validation"] == "next_task"
    assert permissions["future_gatekeeper_review"] == "future_task"
    assert all(
        permissions[key] == "not_allowed"
        for key in [
            "actual_persona_review",
            "investor_agent_execution",
            "investor_decision_generation",
            "recommendations",
            "rankings",
            "allocations_or_rebalancing",
            "trade_signals",
        ]
    )
    assert permissions["auto_promotion"] == "disabled"
    prohibited = _codes(
        build_limited_preparation_package_prohibited_output_matrix(), "prohibited_code"
    )
    assert {
        "actual_persona_review",
        "investor_agent_execution",
        "investor_decision_generation",
        "buy_sell_hold_recommendations",
        "company_rankings",
        "portfolio_allocations",
        "portfolio_rebalancing",
        "trade_signals",
        "execution_instructions",
        "strategy_validation",
        "auto_promotion",
    }.issubset(prohibited)
    assert {
        row["current_status"] for row in build_limited_preparation_package_future_approval_matrix()
    } == {"required_not_granted"}


def test_handoff_and_checks_are_created() -> None:
    report = build_limited_preparation_package(
        package_run_id="package_run",
        generated_at="2026-06-19T00:00:00+00:00",
        inventory=_inventory(),
    )
    handoff = report.task_141_handoff_manifest
    assert handoff["future_phase_id"] == 19 and handoff["future_task_id"] == 141
    assert handoff["readiness_status"] in {
        "ready_to_validate_limited_preparation_package",
        "ready_with_warnings",
    }
    assert handoff["execution_allowed_now"] is True
    assert {
        "actual persona reviews",
        "investor agent execution",
        "recommendations",
        "rankings",
        "trade signals",
    }.issubset(set(handoff["prohibited_outputs"]))
    assert all(
        row["status"] == "satisfied" for row in build_limited_preparation_package_assembly_checks()
    )


def test_write_report_and_markdown(tmp_path: Path) -> None:
    files = write_limited_preparation_package_report(
        outputs_root=_write_fixture(tmp_path),
        limited_preparation_artifact_inventory_run_id="inventory_run",
    )
    assert all(
        path.is_file()
        for path in [
            files.markdown_path,
            files.json_path,
            files.index_csv_path,
            files.artifact_sections_csv_path,
            files.warnings_csv_path,
            files.permissions_csv_path,
            files.prohibited_csv_path,
            files.approvals_csv_path,
            files.handoff_path,
            files.checks_csv_path,
            files.latest_manifest_path,
        ]
    )
    markdown = files.markdown_path.read_text(encoding="utf-8")
    for heading in [
        "Important Boundary",
        "Where We Are Now",
        "Package Index",
        "Package Artifact Sections",
        "Warnings Carried Forward",
        "Permission Boundary",
        "Prohibited Outputs",
        "Future Gatekeeper Approval Requirements",
        "Task 141 Handoff",
        "What This Does Not Suggest",
    ]:
        assert f"## {heading}" in markdown


def test_cli_explicit_and_auto_latest(tmp_path: Path) -> None:
    root = _write_fixture(tmp_path)
    runner = CliRunner()
    explicit = runner.invoke(
        app,
        [
            "assemble-limited-preparation-package",
            "--limited-preparation-artifact-inventory-run-id",
            "inventory_run",
            "--outputs-root",
            str(root),
        ],
    )
    latest = runner.invoke(
        app, ["assemble-limited-preparation-package", "--auto-latest", "--outputs-root", str(root)]
    )
    assert explicit.exit_code == 0, explicit.output
    assert latest.exit_code == 0, latest.output
    assert "limited_preparation_artifact_inventory_run_id=inventory_run" in explicit.output
    assert "recommended_next_task=Task 141" in explicit.output
    assert "status=assembled_with_warnings" in latest.output
