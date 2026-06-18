"""Tests for Task 121 controlled re-run trial."""

import csv
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.regate.controlled_re_run_trial import (
    build_control_diagnostics_matrix,
    build_controlled_re_run_summary,
    build_controlled_re_run_trial,
    build_controlled_re_run_validation_checks,
    build_re_run_limitations_matrix,
    build_scenario_execution_plan,
    build_scenario_results_matrix,
    build_task_122_handoff_manifest,
    load_re_run_input_package,
    load_re_run_input_package_manifest,
    write_controlled_re_run_trial_report,
)


def _package() -> dict:
    controls = [
        "full_sample",
        "clean_only",
        "warning_only",
        "clean_vs_warning_split",
        "clean_anchor",
        "delayed_anchor",
        "clean_anchor_vs_delayed_anchor_split",
        "current_core",
        "expanded_cohort",
        "current_core_vs_expanded_cohort_split",
        "ex_nvda",
        "ex_top_contributors",
        "ex_supportive_date",
        "benchmark_relative",
        "walk_forward",
        "outlier_dependence",
        "metadata_concentration",
        "persona_evidence_requirement_linkage",
        "no_persona_review_before_gatekeeper_allows",
    ]
    return {
        "re_run_input_package_run_id": "package",
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
        "re_run_control_matrix": [
            {"control_code": control}
            for control in controls
        ],
    }


def _write_fixture(outputs: Path) -> None:
    package_folder = outputs / "re_run_input_packages" / "package"
    package_folder.mkdir(parents=True)
    (package_folder / "re_run_input_package.json").write_text(
        json.dumps(_package()),
        encoding="utf-8",
    )
    (
        outputs / "re_run_input_packages" / "latest_re_run_input_package_manifest.json"
    ).write_text(
        json.dumps({"re_run_input_package_run_id": "package"}),
        encoding="utf-8",
    )
    backtest_folder = outputs / "backtests" / "backtest"
    backtest_folder.mkdir(parents=True)
    rows = [
        ("MSFT", "2021-06-30", "clean", "False", "0.10", "0.05"),
        ("NVDA", "2021-06-30", "clean", "False", "0.40", "0.30"),
        ("GOOGL", "2021-12-31", "warning", "True", "0.02", "-0.10"),
        ("AMZN", "2021-12-31", "warning", "True", "0.03", "-0.08"),
        ("COST", "2022-06-30", "clean", "False", "0.04", "-0.02"),
        ("META", "2023-06-30", "clean", "False", "0.12", "-0.04"),
    ]
    with (backtest_folder / "backtest_results.csv").open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "ticker",
                "as_of_date",
                "coverage_quality_label",
                "has_delayed_price_anchor",
                "forward_return_12m",
                "relative_return_12m",
            ]
        )
        writer.writerows(rows)


def test_loads_latest_re_run_input_package_manifest(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    manifest = load_re_run_input_package_manifest(outputs_root=tmp_path)
    assert manifest["re_run_input_package_run_id"] == "package"


def test_loads_explicit_re_run_input_package_run_id(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    package = load_re_run_input_package_manifest(
        outputs_root=tmp_path,
        re_run_input_package_run_id="package",
    )
    assert package["backtest_run_id"] == "backtest"
    assert (
        load_re_run_input_package(
            outputs_root=tmp_path,
            re_run_input_package_run_id="package",
        )["re_run_re_gate_plan_run_id"]
        == "plan"
    )


def test_handles_missing_re_run_input_package_manifest(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_re_run_input_package_manifest(outputs_root=tmp_path)


def test_handles_missing_re_run_input_package_report(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_re_run_input_package(
            outputs_root=tmp_path,
            re_run_input_package_run_id="missing",
        )


def test_controlled_re_run_summary_is_created() -> None:
    summary = build_controlled_re_run_summary(
        controlled_re_run_trial_run_id="trial",
        package=_package(),
    )
    assert summary["current_task_id"] == 121
    assert summary["recommended_next_task"] == (
        "Task 122 — Compare Pre-Repair vs Post-Repair Evidence"
    )
    assert summary["controlled_re_run_status"] == "completed"
    assert summary["progression_allowed"] is False
    assert summary["persona_reviews_allowed"] is False


def test_scenario_execution_plan_contains_required_scenarios() -> None:
    plan = build_scenario_execution_plan(_package())
    scenarios = {row["scenario_code"] for row in plan}
    assert "full_sample" in scenarios
    assert "clean_only" in scenarios
    assert "warning_only" in scenarios
    assert "clean_vs_warning_split" in scenarios
    assert "clean_anchor" in scenarios
    assert "delayed_anchor" in scenarios
    assert "clean_anchor_vs_delayed_anchor_split" in scenarios
    assert "current_core" in scenarios
    assert "expanded_cohort" in scenarios
    assert "current_core_vs_expanded_cohort_split" in scenarios
    assert "ex_nvda" in scenarios
    assert "ex_top_contributors" in scenarios
    assert "ex_supportive_date" in scenarios
    assert "post_2021_only" in scenarios
    assert all(row["included"] is True for row in plan)


def test_scenario_results_matrix_contains_required_results(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    report = build_controlled_re_run_trial(
        controlled_re_run_trial_run_id="trial",
        generated_at="2026-06-18T00:00:00+00:00",
        outputs_root=tmp_path,
        package=_package(),
    )
    scenarios = {row["scenario_code"]: row for row in report.scenario_results_matrix}
    assert scenarios["full_sample"]["sample_size"] == 6
    assert scenarios["current_core"]["sample_size"] == 3
    assert scenarios["expanded_cohort"]["sample_size"] == 3
    assert scenarios["clean_anchor"]["sample_size"] == 4
    assert scenarios["delayed_anchor"]["sample_size"] == 2
    assert scenarios["ex_supportive_date"]["sample_size"] == 4
    assert scenarios["post_2021_only"]["sample_size"] == 2
    assert all(row["safety_boundary"] for row in report.scenario_results_matrix)


def test_missing_data_scenarios_are_documented(tmp_path: Path) -> None:
    plan = build_scenario_execution_plan(_package())
    results = build_scenario_results_matrix(
        scenario_execution_plan=plan,
        backtest_rows=[],
    )
    assert all(
        row["execution_status"] == "not_executable_due_to_missing_local_input"
        for row in results
    )
    assert all(row["main_diagnostic_label"] == "missing_local_input" for row in results)


def test_control_diagnostics_matrix_contains_required_controls() -> None:
    rows = build_control_diagnostics_matrix(_package())
    controls = {row["control_code"] for row in rows}
    assert "full_sample" in controls
    assert "clean_vs_warning_split" in controls
    assert "clean_anchor_vs_delayed_anchor_split" in controls
    assert "current_core_vs_expanded_cohort_split" in controls
    assert "ex_nvda" in controls
    assert "ex_top_contributors" in controls
    assert "ex_supportive_date" in controls
    assert "metadata_concentration" in controls
    assert "post_2021_only" in controls
    assert all(row["required_for_task_122"] is True for row in rows)


def test_limitations_matrix_contains_required_limitations() -> None:
    rows = build_re_run_limitations_matrix()
    limitations = {row["limitation_code"] for row in rows}
    assert "local_artifacts_only" in limitations
    assert "no_new_market_data" in limitations
    assert "no_live_api_calls" in limitations
    assert "gatekeeper_not_rerun_in_task_121" in limitations
    assert "persona_review_not_allowed" in limitations


def test_task_122_handoff_manifest_is_ready() -> None:
    handoff = build_task_122_handoff_manifest(
        controlled_re_run_trial_run_id="trial",
    )
    assert handoff["future_task_id"] == 122
    assert handoff["readiness_status"] == "controlled_re_run_ready_for_comparison"
    assert handoff["execution_allowed_now"] is True
    assert "gatekeeper_decision" in handoff["prohibited_outputs"]


def test_validation_checks_preserve_safety_boundaries() -> None:
    checks = build_controlled_re_run_validation_checks()
    codes = {row["check_code"] for row in checks}
    assert "gatekeeper_not_rerun" in codes
    assert "persona_review_block_preserved" in codes
    assert "no_recommendation_outputs" in codes
    assert "no_ranking_outputs" in codes
    assert "no_trade_signal_outputs" in codes
    assert "no_network_calls" in codes
    assert all(row["status"] == "satisfied" for row in checks)


def test_trial_json_contains_required_sections(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    report = build_controlled_re_run_trial(
        controlled_re_run_trial_run_id="trial",
        generated_at="2026-06-18T00:00:00+00:00",
        outputs_root=tmp_path,
        package=_package(),
    )
    payload = report.to_dict()
    assert payload["controlled_re_run_summary"]
    assert payload["scenario_execution_plan"]
    assert payload["scenario_results_matrix"]
    assert payload["control_diagnostics_matrix"]
    assert payload["limitations_matrix"]
    assert payload["task_122_handoff_manifest"]
    assert payload["controlled_re_run_validation_checks"]
    assert payload["controlled_re_run_summary"]["persona_reviews_allowed"] is False


def test_writer_creates_controlled_re_run_artifacts(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    files = write_controlled_re_run_trial_report(
        outputs_root=tmp_path,
        re_run_input_package_run_id="package",
    )

    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.scenario_execution_plan_csv_path.is_file()
    assert files.scenario_results_matrix_csv_path.is_file()
    assert files.control_diagnostics_matrix_csv_path.is_file()
    assert files.limitations_matrix_csv_path.is_file()
    assert files.task_122_handoff_manifest_path.is_file()
    assert files.validation_checks_csv_path.is_file()
    assert files.latest_manifest_path.is_file()

    markdown = files.markdown_path.read_text(encoding="utf-8")
    assert "## Important Boundary" in markdown
    assert "## Where We Are Now" in markdown
    assert "## Scenario Execution Plan" in markdown
    assert "## Scenario Results Matrix" in markdown
    assert "## Control Diagnostics Matrix" in markdown
    assert "## Limitations" in markdown
    assert "## Task 122 Handoff" in markdown
    assert "## What This Does Not Suggest" in markdown


def test_cli_builds_explicit_controlled_re_run_trial(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "execute-controlled-re-run-trial",
            "--re-run-input-package-run-id",
            "package",
            "--outputs-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert "Controlled Re-Run Trial" in result.output
    assert "re_run_input_package_run_id=package" in result.output
    assert "persona_reviews_allowed=false" in result.output
    assert "recommended_next_task=Task 122 — Compare Pre-Repair vs Post-Repair Evidence" in (
        result.output
    )
    assert "status=completed" in result.output


def test_cli_builds_auto_latest_controlled_re_run_trial(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "execute-controlled-re-run-trial",
            "--auto-latest",
            "--outputs-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert "Controlled Re-Run Trial" in result.output
    assert "scenario_rows=17" in result.output
    assert "result_rows=17" in result.output
    assert "control_rows=20" in result.output
