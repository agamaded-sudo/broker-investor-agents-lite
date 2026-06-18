"""Tests for Task 122 pre/post repair comparison."""

import csv
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.regate.pre_post_repair_comparison import (
    build_comparison_summary,
    build_evidence_delta_matrix,
    build_gatekeeper_readiness_delta,
    build_limitation_resolution_matrix,
    build_post_repair_re_run_matrix,
    build_pre_post_comparison_validation_checks,
    build_pre_post_repair_comparison,
    build_pre_repair_baseline_matrix,
    build_scenario_delta_matrix,
    build_stability_delta_matrix,
    build_task_123_handoff_manifest,
    load_controlled_re_run_trial,
    load_controlled_re_run_trial_manifest,
    write_pre_post_repair_comparison_report,
)


def _scenario(
    code: str,
    sample_size: int,
    relative: float,
    hit_rate: float,
) -> dict:
    return {
        "scenario_code": code,
        "scenario_label": code.replace("_", " "),
        "execution_status": "executed_from_local_artifacts",
        "sample_size": sample_size,
        "tickers_count": 2,
        "dates_count": 2,
        "absolute_median_forward_12m": 0.1,
        "benchmark_relative_median_12m": relative,
        "benchmark_relative_hit_rate": hit_rate,
        "main_diagnostic_label": "test_diagnostic",
    }


def _trial() -> dict:
    scenarios = [
        _scenario("full_sample", 6, -0.05, 0.4),
        _scenario("clean_only", 4, -0.04, 0.5),
        _scenario("warning_only", 2, -0.08, 0.25),
        _scenario("clean_anchor", 4, -0.04, 0.5),
        _scenario("delayed_anchor", 2, -0.08, 0.25),
        _scenario("current_core", 3, 0.12, 0.67),
        _scenario("expanded_cohort", 3, -0.07, 0.2),
        _scenario("ex_nvda", 5, -0.06, 0.4),
        _scenario("ex_top_contributors", 4, -0.07, 0.25),
        _scenario("ex_supportive_date", 4, -0.07, 0.25),
        _scenario("post_2021_only", 2, -0.06, 0.25),
        _scenario("walk_forward", 6, -0.05, 0.4),
        _scenario("metadata_concentration_disclosure", 6, -0.05, 0.4),
    ]
    return {
        "controlled_re_run_trial_run_id": "trial",
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
        "scenario_results_matrix": scenarios,
    }


def _write_fixture(outputs: Path) -> None:
    trial_folder = outputs / "controlled_re_run_trials" / "trial"
    trial_folder.mkdir(parents=True)
    (trial_folder / "controlled_re_run_trial.json").write_text(
        json.dumps(_trial()),
        encoding="utf-8",
    )
    (
        outputs
        / "controlled_re_run_trials"
        / "latest_controlled_re_run_trial_manifest.json"
    ).write_text(
        json.dumps({"controlled_re_run_trial_run_id": "trial"}),
        encoding="utf-8",
    )
    backtest_folder = outputs / "backtests" / "backtest"
    backtest_folder.mkdir(parents=True)
    with (backtest_folder / "backtest_results.csv").open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.writer(file)
        writer.writerow(["ticker", "as_of_date", "forward_return_12m", "relative_return_12m"])
        writer.writerow(["MSFT", "2021-06-30", "0.10", "0.20"])
        writer.writerow(["AAPL", "2021-06-30", "0.20", "0.18"])
        writer.writerow(["META", "2022-06-30", "0.05", "-0.08"])


def test_loads_latest_controlled_re_run_trial_manifest(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    manifest = load_controlled_re_run_trial_manifest(outputs_root=tmp_path)
    assert manifest["controlled_re_run_trial_run_id"] == "trial"


def test_loads_explicit_controlled_re_run_trial_run_id(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    trial = load_controlled_re_run_trial_manifest(
        outputs_root=tmp_path,
        controlled_re_run_trial_run_id="trial",
    )
    assert trial["backtest_run_id"] == "backtest"
    assert (
        load_controlled_re_run_trial(
            outputs_root=tmp_path,
            controlled_re_run_trial_run_id="trial",
        )["re_run_input_package_run_id"]
        == "package"
    )


def test_handles_missing_controlled_re_run_trial_manifest(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_controlled_re_run_trial_manifest(outputs_root=tmp_path)


def test_handles_missing_controlled_re_run_trial_report(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_controlled_re_run_trial(
            outputs_root=tmp_path,
            controlled_re_run_trial_run_id="missing",
        )


def test_comparison_summary_is_created() -> None:
    summary = build_comparison_summary(
        pre_post_repair_comparison_run_id="comparison",
        trial=_trial(),
    )
    assert summary["current_task_id"] == 122
    assert summary["recommended_next_task"] == "Task 123 — Run Gatekeeper Re-Evaluation"
    assert summary["comparison_status"] == "completed"
    assert summary["persona_reviews_allowed"] is False


def test_baseline_and_post_matrices_are_created(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    report = build_pre_post_repair_comparison(
        pre_post_repair_comparison_run_id="comparison",
        generated_at="2026-06-18T00:00:00+00:00",
        outputs_root=tmp_path,
        trial=_trial(),
    )
    baselines = {row["baseline_code"] for row in report.pre_repair_baseline_matrix}
    assert "original_full_sample" in baselines
    assert "original_expanded_trial" in baselines
    assert "original_current_core" in baselines
    assert "original_expanded_cohort" in baselines
    assert "original_clean_anchor" in baselines
    assert "original_delayed_anchor" in baselines
    assert "original_supportive_period" in baselines
    assert "original_post_2021" in baselines
    post = {row["scenario_code"] for row in report.post_repair_re_run_matrix}
    assert "full_sample" in post
    assert "current_core" in post
    assert "expanded_cohort" in post
    assert "clean_anchor" in post
    assert "delayed_anchor" in post
    assert "ex_supportive_date" in post


def test_delta_matrices_are_created(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    pre = build_pre_repair_baseline_matrix(trial=_trial(), backtest_rows=[])
    post = build_post_repair_re_run_matrix(trial=_trial())
    evidence = build_evidence_delta_matrix(
        pre_repair_baseline_matrix=pre,
        post_repair_re_run_matrix=post,
    )
    codes = {row["comparison_code"] for row in evidence}
    assert "full_sample_delta" in codes
    assert "current_core_delta" in codes
    assert "expanded_cohort_delta" in codes
    assert "clean_anchor_delta" in codes
    assert "delayed_anchor_delta" in codes
    assert "supportive_period_delta" in codes
    scenario = {row["scenario_group"] for row in build_scenario_delta_matrix(evidence_delta_matrix=evidence)}
    assert "full_sample" in scenario
    assert "clean_vs_warning" in scenario
    assert "anchor_split" in scenario
    assert "cohort_split" in scenario
    assert "outlier_split" in scenario
    assert "supportive_date_split" in scenario


def test_stability_readiness_limitations_and_handoff_are_created() -> None:
    stability = build_stability_delta_matrix()
    stability_codes = {row["stability_dimension"] for row in stability}
    assert "walk_forward_stability" in stability_codes
    assert "period_sensitivity" in stability_codes
    assert "supportive_period_dependence" in stability_codes
    assert "benchmark_relative_stability" in stability_codes
    readiness = build_gatekeeper_readiness_delta()
    readiness_codes = {row["readiness_code"] for row in readiness}
    assert "controlled_re_run_completed" in readiness_codes
    assert "pre_post_repair_comparison_completed" in readiness_codes
    assert "persona_review_block_preserved" in readiness_codes
    assert "safety_ledger_clear" in readiness_codes
    assert "no_recommendation_outputs_confirmed" in readiness_codes
    limitations = build_limitation_resolution_matrix()
    limitation_codes = {row["limitation_code"] for row in limitations}
    assert "local_artifacts_only" in limitation_codes
    assert "possible_missing_exact_delay_days" in limitation_codes
    assert "metadata_concentration_remaining" in limitation_codes
    assert "gatekeeper_not_rerun" in limitation_codes
    handoff = build_task_123_handoff_manifest(
        pre_post_repair_comparison_run_id="comparison",
        controlled_re_run_trial_run_id="trial",
        gatekeeper_rerun_ready=True,
    )
    assert handoff["future_task_id"] == 123
    assert handoff["required_gatekeeper_inputs"]
    assert handoff["readiness_status"] == "comparison_ready_for_gatekeeper_re_evaluation"


def test_validation_checks_preserve_safety_boundaries() -> None:
    checks = build_pre_post_comparison_validation_checks()
    codes = {row["check_code"] for row in checks}
    assert "gatekeeper_not_rerun" in codes
    assert "persona_review_block_preserved" in codes
    assert "no_recommendation_outputs" in codes
    assert "no_network_calls" in codes
    assert all(row["status"] == "satisfied" for row in checks)


def test_comparison_json_contains_required_sections(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    report = build_pre_post_repair_comparison(
        pre_post_repair_comparison_run_id="comparison",
        generated_at="2026-06-18T00:00:00+00:00",
        outputs_root=tmp_path,
        trial=_trial(),
    )
    payload = report.to_dict()
    assert payload["comparison_summary"]
    assert payload["pre_repair_baseline_matrix"]
    assert payload["post_repair_re_run_matrix"]
    assert payload["evidence_delta_matrix"]
    assert payload["scenario_delta_matrix"]
    assert payload["stability_delta_matrix"]
    assert payload["gatekeeper_readiness_delta"]
    assert payload["limitation_resolution_matrix"]
    assert payload["task_123_handoff_manifest"]
    assert payload["pre_post_repair_validation_checks"]
    assert payload["comparison_summary"]["persona_reviews_allowed"] is False


def test_writer_creates_pre_post_comparison_artifacts(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    files = write_pre_post_repair_comparison_report(
        outputs_root=tmp_path,
        controlled_re_run_trial_run_id="trial",
    )

    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.pre_repair_baseline_matrix_csv_path.is_file()
    assert files.post_repair_re_run_matrix_csv_path.is_file()
    assert files.evidence_delta_matrix_csv_path.is_file()
    assert files.scenario_delta_matrix_csv_path.is_file()
    assert files.stability_delta_matrix_csv_path.is_file()
    assert files.gatekeeper_readiness_delta_csv_path.is_file()
    assert files.limitation_resolution_matrix_csv_path.is_file()
    assert files.task_123_handoff_manifest_path.is_file()
    assert files.validation_checks_csv_path.is_file()
    assert files.latest_manifest_path.is_file()
    markdown = files.markdown_path.read_text(encoding="utf-8")
    assert "## Important Boundary" in markdown
    assert "## Where We Are Now" in markdown
    assert "## Pre-Repair Baseline Matrix" in markdown
    assert "## Post-Repair Controlled Re-Run Matrix" in markdown
    assert "## Evidence Delta Matrix" in markdown
    assert "## Scenario Delta Matrix" in markdown
    assert "## Stability Delta Matrix" in markdown
    assert "## Gatekeeper Readiness Delta" in markdown
    assert "## Limitation Resolution Matrix" in markdown
    assert "## Task 123 Handoff" in markdown
    assert "## What This Does Not Suggest" in markdown


def test_cli_builds_explicit_pre_post_comparison(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "compare-pre-post-repair-evidence",
            "--controlled-re-run-trial-run-id",
            "trial",
            "--outputs-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert "Pre/Post Repair Evidence Comparison" in result.output
    assert "controlled_re_run_trial_run_id=trial" in result.output
    assert "persona_reviews_allowed=false" in result.output
    assert "recommended_next_task=Task 123 — Run Gatekeeper Re-Evaluation" in result.output
    assert "status=completed" in result.output


def test_cli_builds_auto_latest_pre_post_comparison(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "compare-pre-post-repair-evidence",
            "--auto-latest",
            "--outputs-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert "Pre/Post Repair Evidence Comparison" in result.output
    assert "evidence_delta_rows=10" in result.output
    assert "scenario_delta_rows=8" in result.output
    assert "stability_rows=8" in result.output
