"""Tests for Task 120 re-run input package."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.regate.re_run_input_package import (
    build_input_package_summary,
    build_input_package_validation_checks,
    build_re_run_artifact_source_map,
    build_re_run_control_matrix,
    build_re_run_date_matrix,
    build_re_run_input_package,
    build_re_run_universe_matrix,
    build_task_121_execution_manifest,
    load_re_run_re_gate_plan,
    load_re_run_re_gate_plan_manifest,
    write_re_run_input_package_report,
)


def _plan() -> dict:
    return {
        "re_run_re_gate_plan_run_id": "plan",
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
        "re_run_scope_matrix": [
            {"required_control": "clean_vs_warning_split", "included_in_plan": True},
            {
                "required_control": "current_core_vs_expanded_cohort_split",
                "included_in_plan": True,
            },
            {"required_control": "outlier_dependence", "included_in_plan": True},
            {
                "required_control": "no_persona_review_before_gatekeeper_allows",
                "included_in_plan": True,
            },
        ],
        "controlled_trial_plan": {
            "required_controls": [
                "full_sample",
                "clean_only",
                "warning_only",
                "current_core",
                "expanded_cohort",
                "ex_nvda",
                "ex_top_contributors",
                "ex_supportive_date",
                "benchmark_relative",
                "walk_forward",
                "metadata_concentration",
            ]
        },
    }


def _write_fixture(outputs: Path) -> None:
    plan_folder = outputs / "re_run_re_gate_plans" / "plan"
    plan_folder.mkdir(parents=True)
    (plan_folder / "re_run_re_gate_plan.json").write_text(
        json.dumps(_plan()),
        encoding="utf-8",
    )
    (outputs / "re_run_re_gate_plans" / "latest_re_run_re_gate_plan_manifest.json").write_text(
        json.dumps({"re_run_re_gate_plan_run_id": "plan"}),
        encoding="utf-8",
    )
    audit_folder = outputs / "research_audit_trail_bundles" / "audit"
    audit_folder.mkdir(parents=True)
    (audit_folder / "research_audit_trail_bundle.json").write_text(
        json.dumps({"research_audit_trail_run_id": "audit"}),
        encoding="utf-8",
    )


def test_loads_latest_re_run_re_gate_plan_manifest(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    manifest = load_re_run_re_gate_plan_manifest(outputs_root=tmp_path)
    assert manifest["re_run_re_gate_plan_run_id"] == "plan"


def test_loads_explicit_re_run_re_gate_plan_run_id(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    plan = load_re_run_re_gate_plan_manifest(
        outputs_root=tmp_path,
        re_run_re_gate_plan_run_id="plan",
    )
    assert plan["research_audit_trail_run_id"] == "audit"
    assert (
        load_re_run_re_gate_plan(
            outputs_root=tmp_path,
            re_run_re_gate_plan_run_id="plan",
        )["backtest_run_id"]
        == "backtest"
    )


def test_handles_missing_re_run_re_gate_plan_manifest(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_re_run_re_gate_plan_manifest(outputs_root=tmp_path)


def test_handles_missing_re_run_re_gate_plan_report(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_re_run_re_gate_plan(
            outputs_root=tmp_path,
            re_run_re_gate_plan_run_id="missing",
        )


def test_input_package_summary_is_created() -> None:
    summary = build_input_package_summary(
        re_run_input_package_run_id="package",
        plan=_plan(),
    )
    assert summary["current_task_id"] == 120
    assert summary["recommended_next_task"] == "Task 121 — Execute Controlled Re-Run Trial"
    assert summary["package_status"] == "completed"
    assert summary["progression_allowed"] is False
    assert summary["persona_reviews_allowed"] is False


def test_universe_matrix_contains_required_groups() -> None:
    rows = build_re_run_universe_matrix()
    groups = {row["universe_group"] for row in rows}
    assert "full_expanded_universe" in groups
    assert "current_core" in groups
    assert "expanded_cohort" in groups
    assert "ex_nvda_universe" in groups
    assert "ex_top_contributors_universe" in groups
    assert "metadata_concentration_groups" in groups
    assert "MSFT;AAPL;NVDA;COST" in {
        row["tickers_or_definition"] for row in rows
    }


def test_date_matrix_contains_required_groups() -> None:
    rows = build_re_run_date_matrix()
    groups = {row["date_group"] for row in rows}
    assert "full_date_set" in groups
    assert "clean_periods" in groups
    assert "warning_periods" in groups
    assert "supportive_period_only" in groups
    assert "ex_supportive_date_periods" in groups
    assert "post_2021_periods" in groups
    assert "anchor_split_periods" in groups


def test_control_matrix_contains_required_controls() -> None:
    rows = build_re_run_control_matrix(_plan())
    controls = {row["control_code"] for row in rows}
    assert "full_sample" in controls
    assert "clean_only" in controls
    assert "warning_only" in controls
    assert "clean_anchor" in controls
    assert "delayed_anchor" in controls
    assert "current_core" in controls
    assert "expanded_cohort" in controls
    assert "ex_nvda" in controls
    assert "ex_top_contributors" in controls
    assert "ex_supportive_date" in controls
    assert "benchmark_relative" in controls
    assert "walk_forward" in controls
    assert "metadata_concentration" in controls


def test_artifact_source_map_contains_required_categories(tmp_path: Path) -> None:
    rows = build_re_run_artifact_source_map(outputs_root=tmp_path, plan=_plan())
    categories = {row["source_category"] for row in rows}
    assert "research_audit_trail_bundle" in categories
    assert "backtest_results" in categories
    assert "driver_decomposition" in categories
    assert "outlier_repair" in categories
    assert "walk_forward_repair" in categories
    assert "delayed_anchor_repair" in categories
    assert "metadata_diversity_recheck" in categories
    assert "persona_evidence_pack_requirements" in categories
    assert "bogle_benchmark_index_pack" in categories
    assert "fisher_qualitative_growth_pack" in categories
    assert "buffett_munger_quality_risk_pack" in categories


def test_task_121_execution_manifest_is_ready() -> None:
    controls = build_re_run_control_matrix(_plan())
    manifest = build_task_121_execution_manifest(
        re_run_input_package_run_id="package",
        controls=controls,
    )
    assert manifest["future_task_id"] == 121
    assert manifest["readiness_status"] == "input_package_ready"
    assert manifest["execution_allowed_now"] is True
    assert "gatekeeper_rerun" in manifest["prohibited_outputs"]


def test_validation_checks_are_satisfied() -> None:
    checks = build_input_package_validation_checks()
    codes = {row["check_code"] for row in checks}
    assert "no_re_run_executed" in codes
    assert "no_gatekeeper_rerun_executed" in codes
    assert "no_recommendation_outputs" in codes
    assert all(row["status"] == "satisfied" for row in checks)


def test_build_report_includes_all_package_sections(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    report = build_re_run_input_package(
        re_run_input_package_run_id="package",
        generated_at="2026-06-18T00:00:00+00:00",
        outputs_root=tmp_path,
        plan=_plan(),
    )
    payload = report.to_dict()
    assert payload["package_status"] == "completed"
    assert payload["input_package_summary"]["current_task_id"] == 120
    assert payload["re_run_universe_matrix"]
    assert payload["re_run_date_matrix"]
    assert payload["re_run_control_matrix"]
    assert payload["artifact_source_map"]
    assert payload["task_121_execution_manifest"]["future_task_id"] == 121
    assert payload["input_package_validation_checks"]


def test_writer_creates_package_artifacts(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    files = write_re_run_input_package_report(
        outputs_root=tmp_path,
        re_run_re_gate_plan_run_id="plan",
    )

    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.universe_matrix_csv_path.is_file()
    assert files.date_matrix_csv_path.is_file()
    assert files.control_matrix_csv_path.is_file()
    assert files.artifact_source_map_csv_path.is_file()
    assert files.task_121_execution_manifest_path.is_file()
    assert files.validation_checks_csv_path.is_file()
    assert files.latest_manifest_path.is_file()

    markdown = files.markdown_path.read_text(encoding="utf-8")
    assert "## Important Boundary" in markdown
    assert "## Where We Are Now" in markdown
    assert "## Re-Run Universe Matrix" in markdown
    assert "## Re-Run Date Matrix" in markdown
    assert "## Re-Run Control Matrix" in markdown
    assert "## Task 121 Execution Manifest" in markdown
    assert "## What This Does Not Suggest" in markdown

    payload = json.loads(files.json_path.read_text(encoding="utf-8"))
    assert payload["re_run_universe_matrix"]
    assert payload["re_run_date_matrix"]
    assert payload["re_run_control_matrix"]
    assert payload["artifact_source_map"]
    assert payload["task_121_execution_manifest"]
    assert payload["input_package_validation_checks"]


def test_cli_builds_explicit_re_run_input_package(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "build-re-run-input-package",
            "--re-run-re-gate-plan-run-id",
            "plan",
            "--outputs-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert "Re-Run Input Package" in result.output
    assert "re_run_re_gate_plan_run_id=plan" in result.output
    assert "current_task=Build Re-Run Input Package" in result.output
    assert "persona_reviews_allowed=false" in result.output
    assert "recommended_next_task=Task 121 — Execute Controlled Re-Run Trial" in (
        result.output
    )
    assert "status=completed" in result.output


def test_cli_builds_auto_latest_re_run_input_package(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "build-re-run-input-package",
            "--auto-latest",
            "--outputs-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert "Re-Run Input Package" in result.output
    assert "universe_rows=7" in result.output
    assert "date_rows=7" in result.output
    assert "control_rows=19" in result.output
