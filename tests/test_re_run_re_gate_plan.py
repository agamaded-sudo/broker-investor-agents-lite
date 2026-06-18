"""Tests for Task 119 re-run and re-gate planning."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.regate.re_run_re_gate_plan import (
    build_controlled_trial_plan,
    build_gatekeeper_rerun_criteria,
    build_phase_16_context,
    build_phase_16_task_roadmap,
    build_re_gate_decision_branches,
    build_re_run_re_gate_plan,
    build_re_run_scope_matrix,
    build_safety_plan,
    load_research_audit_trail_bundle,
    load_research_audit_trail_manifest,
    write_re_run_re_gate_plan_report,
)


def _audit() -> dict:
    return {
        "research_audit_trail_run_id": "audit",
        "buffett_munger_pack_run_id": "buffett_munger",
        "fisher_growth_pack_run_id": "fisher",
        "bogle_benchmark_pack_run_id": "bogle",
        "persona_evidence_pack_run_id": "persona_pack",
        "metadata_diversity_recheck_run_id": "metadata",
        "delayed_anchor_repair_run_id": "delayed",
        "walk_forward_repair_run_id": "walk",
        "outlier_repair_run_id": "outlier",
        "decomposition_run_id": "decomposition",
        "backoffice_attribution_run_id": "backoffice",
        "investor_persona_attribution_run_id": "persona",
        "gatekeeper_run_id": "gatekeeper",
        "scorecard_run_id": "scorecard",
        "analysis_run_id": "analysis",
        "expanded_trial_run_id": "expanded",
        "backtest_run_id": "backtest",
        "phase_closure_summary": {
            "phase_status": "completed_after_audit_bundle",
            "final_gatekeeper_decision": "hold",
            "progression_allowed": False,
        },
    }


def _write_fixture(outputs: Path) -> None:
    folder = outputs / "research_audit_trail_bundles" / "audit"
    folder.mkdir(parents=True)
    (folder / "research_audit_trail_bundle.json").write_text(
        json.dumps(_audit()),
        encoding="utf-8",
    )
    (
        outputs
        / "research_audit_trail_bundles"
        / "latest_research_audit_trail_bundle_manifest.json"
    ).write_text(
        json.dumps({"research_audit_trail_run_id": "audit"}),
        encoding="utf-8",
    )


def test_loads_latest_research_audit_manifest(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    manifest = load_research_audit_trail_manifest(outputs_root=tmp_path)
    assert manifest["research_audit_trail_run_id"] == "audit"


def test_loads_explicit_research_audit_run_id(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    report = load_research_audit_trail_manifest(
        outputs_root=tmp_path,
        research_audit_trail_run_id="audit",
    )
    assert report["backtest_run_id"] == "backtest"
    assert (
        load_research_audit_trail_bundle(
            outputs_root=tmp_path,
            research_audit_trail_run_id="audit",
        )["expanded_trial_run_id"]
        == "expanded"
    )


def test_handles_missing_research_audit_manifest(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_research_audit_trail_manifest(outputs_root=tmp_path)


def test_handles_missing_research_audit_report(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_research_audit_trail_bundle(
            outputs_root=tmp_path,
            research_audit_trail_run_id="missing",
        )


def test_phase_16_context_defines_current_and_next_tasks() -> None:
    context = build_phase_16_context(audit=_audit())
    assert context["phase_id"] == 16
    assert context["previous_phase_id"] == 15
    assert context["current_task_id"] == 119
    assert context["next_task_id"] == 120
    assert context["gatekeeper_decision"] == "hold"
    assert context["progression_allowed"] is False
    assert context["persona_reviews_allowed"] is False


def test_scope_matrix_includes_required_controls() -> None:
    rows = build_re_run_scope_matrix()
    scope_areas = {row["scope_area"] for row in rows}
    assert "full_sample_re_run" in scope_areas
    assert "clean_vs_warning_split" in scope_areas
    assert "clean_anchor_vs_delayed_anchor_split" in scope_areas
    assert "current_core_vs_expanded_cohort_split" in scope_areas
    assert "ex_nvda_control" in scope_areas
    assert "ex_supportive_date_control" in scope_areas
    assert "metadata_concentration_disclosure" in scope_areas
    assert "no_persona_review_before_gatekeeper_allows" in scope_areas
    assert all(row["included_in_plan"] is True for row in rows)


def test_controlled_trial_plan_is_not_executed() -> None:
    plan = build_controlled_trial_plan(audit=_audit())
    assert plan["proposed_trial_mode"] == "controlled_re_run_only"
    assert plan["readiness_status"] == "planned_not_executed"
    assert "ex_nvda" in plan["required_controls"]
    assert "trade_signal" in plan["prohibited_outputs"]


def test_gatekeeper_rerun_criteria_are_planned_not_satisfied() -> None:
    criteria = build_gatekeeper_rerun_criteria()
    by_code = {row["criteria_code"]: row for row in criteria}
    assert by_code["controlled_re_run_completed"]["current_status"] == (
        "planned_not_completed"
    )
    assert by_code["pre_post_repair_comparison_completed"]["current_status"] == (
        "planned_not_completed"
    )
    assert by_code["persona_review_block_preserved"]["current_status"] == "satisfied"
    assert by_code["no_recommendation_outputs_confirmed"]["current_status"] == (
        "satisfied"
    )


def test_phase_16_roadmap_blocks_persona_review_until_future_gate() -> None:
    roadmap = build_phase_16_task_roadmap()
    assert [row["task_id"] for row in roadmap] == [119, 120, 121, 122, 123, 124]
    assert roadmap[0]["execution_status"] == "completed"
    assert all(row["allows_persona_review"] is False for row in roadmap)
    gatekeeper_tasks = [
        row["task_id"] for row in roadmap if row["allows_gatekeeper_rerun"]
    ]
    assert gatekeeper_tasks == [123]


def test_re_gate_decision_branches_are_defined() -> None:
    branches = build_re_gate_decision_branches()
    codes = {row["branch_code"] for row in branches}
    assert "hold_continues" in codes
    assert "hold_with_repair_progress" in codes
    assert "pass_with_warnings" in codes
    assert "research_ready_for_limited_persona_review" in codes
    assert "block" in codes
    assert "insufficient_re_run_evidence" in codes


def test_safety_plan_contains_no_violations() -> None:
    plan = build_safety_plan()
    rules = {row["safety_rule"] for row in plan}
    assert "no_gatekeeper_rerun_in_task_119" in rules
    assert "no_persona_review_before_gatekeeper_allows" in rules
    assert "no_trade_signal" in rules
    assert all(row["violation_found"] is False for row in plan)


def test_build_report_includes_all_task_119_sections() -> None:
    report = build_re_run_re_gate_plan(
        re_run_re_gate_plan_run_id="plan",
        generated_at="2026-06-18T00:00:00+00:00",
        audit=_audit(),
    )
    payload = report.to_dict()
    assert payload["phase_16_context"]["current_task_id"] == 119
    assert payload["re_run_scope_matrix"]
    assert payload["controlled_trial_plan"]["readiness_status"] == (
        "planned_not_executed"
    )
    assert payload["gatekeeper_rerun_criteria"]
    assert payload["phase_16_task_roadmap"]
    assert payload["re_gate_decision_branches"]
    assert payload["safety_plan"]
    assert payload["recommended_next_task"] == "Task 120 - Build Re-Run Input Package"


def test_writer_creates_task_119_artifacts(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    files = write_re_run_re_gate_plan_report(
        outputs_root=tmp_path,
        research_audit_trail_run_id="audit",
    )

    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.scope_matrix_csv_path.is_file()
    assert files.controlled_trial_plan_path.is_file()
    assert files.gatekeeper_criteria_csv_path.is_file()
    assert files.roadmap_csv_path.is_file()
    assert files.decision_branches_csv_path.is_file()
    assert files.safety_plan_csv_path.is_file()
    assert files.latest_manifest_path.is_file()

    markdown = files.markdown_path.read_text(encoding="utf-8")
    assert "# Re-Run & Re-Gate Plan" in markdown
    assert "## Re-Run Scope Matrix" in markdown
    assert "## Controlled Trial Plan" in markdown
    assert "## Gatekeeper Rerun Criteria" in markdown
    assert "## Phase 16 Task Roadmap" in markdown
    assert "## Future Re-Gate Decision Branches" in markdown
    assert "## Safety Plan" in markdown

    payload = json.loads(files.json_path.read_text(encoding="utf-8"))
    assert payload["plan_status"] == "completed"
    assert payload["phase_16_context"]["persona_reviews_allowed"] is False


def test_cli_builds_explicit_re_run_re_gate_plan(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "build-re-run-re-gate-plan",
            "--research-audit-trail-run-id",
            "audit",
            "--outputs-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert "Re-Run & Re-Gate Plan" in result.output
    assert "research_audit_trail_run_id=audit" in result.output
    assert "current_task=Define Re-Run & Re-Gate Plan" in result.output
    assert "persona_reviews_allowed=false" in result.output
    assert "recommended_next_task=Task 120 - Build Re-Run Input Package" in result.output
    assert "status=completed" in result.output


def test_cli_builds_auto_latest_re_run_re_gate_plan(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "build-re-run-re-gate-plan",
            "--auto-latest",
            "--outputs-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert "Re-Run & Re-Gate Plan" in result.output
    assert "research_audit_trail_run_id=audit" in result.output
    assert "roadmap_tasks=6" in result.output
