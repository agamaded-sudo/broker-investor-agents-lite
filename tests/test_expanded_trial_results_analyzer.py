"""Tests for expanded readiness trial attribution analysis."""

import csv
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner
import yaml

from broker_agents.backtesting.expanded_trial_results_analyzer import (
    analyze_expanded_trial_results,
    load_expanded_trial_manifest,
    write_expanded_trial_analysis_report,
)
from broker_agents.cli import app

TICKER_METADATA = [
    {
        "ticker": "COREP",
        "sector": "Technology",
        "category": "software_platform",
        "universe_group": "current_core",
        "main_limitation": "delayed_price_anchor",
    },
    {
        "ticker": "COREM",
        "sector": "Consumer Staples",
        "category": "consumer_platform",
        "universe_group": "current_core",
        "main_limitation": "delayed_price_anchor",
    },
    {
        "ticker": "NEWN",
        "sector": "Communication Services",
        "category": "consumer_platform",
        "universe_group": "consumer_platforms",
        "main_limitation": "delayed_price_anchor",
    },
    {
        "ticker": "NEWS",
        "sector": "Technology",
        "category": "semiconductor",
        "universe_group": "semiconductors",
        "main_limitation": "delayed_price_anchor",
    },
]


def _write_fixture(outputs: Path) -> dict:
    expanded_run = "expanded"
    backtest_run = "backtest"
    prior_run = "prior"
    source_run = "coverage"
    expanded_folder = outputs / "expanded_ticker_trials" / expanded_run
    backtest_folder = outputs / "backtests" / backtest_run
    prior_folder = outputs / "backtests" / prior_run
    coverage_folder = outputs / "expanded_ticker_coverage" / source_run
    for folder in (
        expanded_folder,
        backtest_folder,
        prior_folder,
        coverage_folder,
    ):
        folder.mkdir(parents=True)

    eligible_path = coverage_folder / "expanded_ticker_eligible_universe.yaml"
    eligible_path.write_text(
        yaml.safe_dump({"eligible_tickers": TICKER_METADATA}),
        encoding="utf-8",
    )
    coverage_path = coverage_folder / "expanded_ticker_coverage_report.json"
    coverage_path.write_text(
        json.dumps({"ticker_summaries": TICKER_METADATA}),
        encoding="utf-8",
    )
    expanded_summary = {
        "expanded_trial_run_id": expanded_run,
        "backtest_run_id": backtest_run,
        "source_validation_run_id": source_run,
        "eligible_universe_path": str(eligible_path),
        "sample_size_after_dedupe": 12,
    }
    summary_path = expanded_folder / "expanded_ticker_trial_summary.json"
    summary_path.write_text(json.dumps(expanded_summary), encoding="utf-8")
    latest_path = (
        outputs
        / "expanded_ticker_trials"
        / "latest_expanded_ticker_trial_manifest.json"
    )
    latest_path.write_text(json.dumps(expanded_summary), encoding="utf-8")

    profiles = {
        "COREP": [0.20, 0.10, 0.08],
        "COREM": [0.02, 0.01, 0.00],
        "NEWN": [-0.12, -0.08, -0.04],
        "NEWS": [-0.10, -0.06, -0.02],
    }
    rows = []
    dates = ["2021-06-30", "2022-06-30", "2023-06-30"]
    for ticker, relatives in profiles.items():
        for index, relative in enumerate(relatives):
            clean = index != 1
            rows.append(
                {
                    "ticker": ticker,
                    "as_of_date": dates[index],
                    "forward_return_12m": str(relative + 0.12),
                    "relative_return_12m": str(relative),
                    "max_drawdown_12m": str(-0.05 - index * 0.01),
                    "coverage_guardrail_status": (
                        "clean"
                        if clean
                        else "research_usable_with_warnings"
                    ),
                    "coverage_quality_label": (
                        "clean" if clean else "delayed_price_anchor"
                    ),
                    "has_delayed_price_anchor": str(not clean),
                    "readiness_label": (
                        "Ready" if ticker in {"COREP", "COREM"} else "Gaps"
                    ),
                    "source_verification_status": (
                        "mixed" if ticker != "NEWS" else "placeholder-heavy"
                    ),
                    "promotion_blocking_bucket": "moderate_blockers",
                    "buffett_interest_level": "Watchlist Interest",
                    "munger_interest_level": "Conditional Interest",
                    "fisher_interest_level": "Needs More Evidence",
                    "lynch_interest_level": "Watchlist Interest",
                    "bogle_interest_level": "Low Interest",
                }
            )
    results_path = backtest_folder / "backtest_results.csv"
    with results_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        "backtest_run_id": backtest_run,
        "backtest_run_type": "readiness_trial",
        "overall_sample_size": 12,
        "clean_record_count": 8,
        "warning_record_count": 4,
        "warning_heavy_record_count": 0,
        "diagnostic_status": "unstable_needs_deeper_review",
        "decision_status": "needs_more_samples",
        "walk_forward_stability_judgment": "unstable",
        "outlier_dependence_status": "result_sensitive_to_top_outliers",
        "delayed_anchor_present": True,
    }
    (backtest_folder / "backtest_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    metrics = {
        "median_forward_return_12m": 0.1,
        "median_relative_return_12m": -0.02,
        "hit_rate_vs_benchmark_12m": 0.4,
    }
    (backtest_folder / "backtest_metrics_summary.json").write_text(
        json.dumps(metrics), encoding="utf-8"
    )
    for filename in (
        "readiness_trial_diagnostic_report.json",
        "readiness_trial_decision_report.json",
        "clean_coverage_sensitivity_report.json",
        "delayed_anchor_impact_report.json",
        "outlier_sensitivity_report.json",
        "walk_forward_metrics.json",
    ):
        (backtest_folder / filename).write_text("{}", encoding="utf-8")

    prior_manifest = {
        "backtest_run_id": prior_run,
        "overall_sample_size": 6,
        "clean_record_count": 4,
        "warning_record_count": 2,
        "warning_heavy_record_count": 0,
        "diagnostic_status": "promising_but_unproven",
        "decision_status": "needs_more_samples",
        "walk_forward_stability_judgment": "stable_positive",
    }
    (prior_folder / "backtest_manifest.json").write_text(
        json.dumps(prior_manifest), encoding="utf-8"
    )
    (prior_folder / "backtest_metrics_summary.json").write_text(
        json.dumps(
            {
                "median_relative_return_12m": 0.12,
                "hit_rate_vs_benchmark_12m": 0.7,
            }
        ),
        encoding="utf-8",
    )
    (prior_folder / "clean_coverage_sensitivity_report.json").write_text(
        json.dumps(
            {
                "subset_diagnostics": {
                    "clean_records": {
                        "median_relative_return_12m": 0.1,
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    return {
        "expanded_run": expanded_run,
        "backtest_run": backtest_run,
        "prior_run": prior_run,
        "summary_path": summary_path,
        "latest_path": latest_path,
        "results_path": results_path,
        "coverage_path": coverage_path,
        "eligible_path": eligible_path,
    }


def test_loads_explicit_and_latest_expanded_trial(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    source = _write_fixture(outputs)
    explicit = load_expanded_trial_manifest(
        outputs_root=outputs,
        expanded_trial_run_id=source["expanded_run"],
    )
    latest = load_expanded_trial_manifest(outputs_root=outputs)
    assert explicit["backtest_run_id"] == source["backtest_run"]
    assert latest["expanded_trial_run_id"] == source["expanded_run"]


def test_missing_expanded_manifest_and_results_raise(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    with pytest.raises(FileNotFoundError, match="manifest not found"):
        load_expanded_trial_manifest(outputs_root=outputs)

    source = _write_fixture(outputs)
    source["results_path"].unlink()
    with pytest.raises(FileNotFoundError, match="Backtest results not found"):
        analyze_expanded_trial_results(
            outputs_root=outputs,
            expanded_trial_run_id=source["expanded_run"],
            prior_backtest_run_id=source["prior_run"],
        )


def test_attribution_and_instability_explanation(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    source = _write_fixture(outputs)
    report = analyze_expanded_trial_results(
        outputs_root=outputs,
        expanded_trial_run_id=source["expanded_run"],
        prior_backtest_run_id=source["prior_run"],
        analysis_run_id="analysis",
        generated_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
    )
    labels = {
        item["ticker"]: item["contribution_to_instability"]
        for item in report.ticker_attribution
    }
    assert labels["COREP"] == "positive_contributor"
    assert labels["COREM"] == "neutral_mixed"
    assert labels["NEWN"] == "negative_contributor"
    assert {item["sector"] for item in report.sector_attribution} == {
        "Technology",
        "Consumer Staples",
        "Communication Services",
    }
    assert {item["category"] for item in report.category_attribution} == {
        "software_platform",
        "consumer_platform",
        "semiconductor",
    }
    groups = {
        item["universe_group"]: item
        for item in report.universe_group_attribution
    }
    assert groups["current_core"]["median_relative_return_12m"] > 0
    assert groups["expanded_cohort"]["median_relative_return_12m"] < 0
    assert len(report.date_attribution) == 3
    assert {item["subset"] for item in report.clean_warning_attribution} == {
        "clean_records",
        "warning_records",
        "delayed_price_anchor",
        "no_delayed_anchor",
    }
    assert report.metadata_diversity_recheck[
        "metadata_diversity_status"
    ] == "concentrated_needs_expansion"
    assert report.prior_trial_comparison["prior"]["sample_size"] == 6
    assert "benchmark_underperformance" in report.expanded_trial_instability_explanation[
        "primary_instability_drivers"
    ]
    assert report.next_research_action == "build_research_evidence_scorecard"
    assert report.prior_trial_comparison["expanded"]["decision_status"] == (
        "needs_more_samples"
    )


def test_missing_universe_metadata_is_partial_not_crash(
    tmp_path: Path,
) -> None:
    outputs = tmp_path / "outputs"
    source = _write_fixture(outputs)
    source["coverage_path"].unlink()
    source["eligible_path"].unlink()
    report = analyze_expanded_trial_results(
        outputs_root=outputs,
        expanded_trial_run_id=source["expanded_run"],
        prior_backtest_run_id=source["prior_run"],
    )
    assert report.analysis_status == "instability_partially_explained"
    assert {item["sector"] for item in report.sector_attribution} == {"Unknown"}


def test_writer_creates_reports_csvs_and_latest_manifest(
    tmp_path: Path,
) -> None:
    outputs = tmp_path / "outputs"
    source = _write_fixture(outputs)
    files = write_expanded_trial_analysis_report(
        outputs_root=outputs,
        expanded_trial_run_id=source["expanded_run"],
        prior_backtest_run_id=source["prior_run"],
        generated_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
    )
    for path in (
        files.markdown_path,
        files.json_path,
        files.ticker_csv_path,
        files.sector_csv_path,
        files.category_csv_path,
        files.universe_group_csv_path,
        files.date_csv_path,
        files.clean_warning_csv_path,
        files.latest_manifest_path,
    ):
        assert path.is_file()
    payload = json.loads(files.json_path.read_text(encoding="utf-8"))
    assert payload["ticker_attribution"]
    assert payload["metadata_diversity_recheck"]
    assert payload["expanded_trial_instability_explanation"]
    markdown = files.markdown_path.read_text(encoding="utf-8")
    for section in (
        "What Changed from the Prior Trial",
        "Ticker Attribution",
        "Universe Group Attribution",
        "Clean vs Warning Attribution",
        "Metadata Diversity Recheck",
        "Instability Explanation",
    ):
        assert section in markdown


@pytest.mark.parametrize("auto_latest", [False, True])
def test_cli_explicit_and_auto_latest(
    tmp_path: Path,
    auto_latest: bool,
) -> None:
    outputs = tmp_path / "outputs"
    source = _write_fixture(outputs)
    args = [
        "analyze-expanded-trial-results",
        "--outputs-root",
        str(outputs),
        "--prior-backtest-run-id",
        source["prior_run"],
    ]
    if auto_latest:
        args.append("--auto-latest")
    else:
        args.extend(
            ["--expanded-trial-run-id", source["expanded_run"]]
        )
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "Expanded Trial Results Analysis" in result.output
    assert "next_research_action=build_research_evidence_scorecard" in (
        result.output
    )
