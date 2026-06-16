"""Tests for BO-002 outlier and Ex-NVDA repair path."""

from datetime import datetime, timezone
import csv
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.backtesting.outlier_repair_path import (
    attribute_outlier_dependence,
    build_outlier_repair_path,
    compute_exclusion_scenarios,
    load_backtest_driver_decomposition_manifest,
    write_outlier_repair_path_report,
)
from broker_agents.cli import app


def _rows() -> list[dict]:
    specs = [
        ("NVDA", "current_core", "Technology", "semiconductor", 0.24),
        ("AAPL", "current_core", "Technology", "consumer_platform", 0.16),
        ("MSFT", "current_core", "Technology", "software_platform", 0.12),
        ("COST", "current_core", "Consumer Staples", "retail", 0.08),
        ("NFLX", "expanded_cohort", "Communication Services", "consumer_platform", -0.24),
        ("ADBE", "expanded_cohort", "Technology", "software_platform", -0.11),
        ("CRM", "expanded_cohort", "Technology", "software_platform", -0.09),
        ("AMZN", "expanded_cohort", "Consumer Discretionary", "consumer_platform", -0.07),
        ("GOOGL", "expanded_cohort", "Communication Services", "consumer_platform", -0.06),
        ("ORCL", "expanded_cohort", "Technology", "software_platform", -0.05),
    ]
    dates = ["2021-06-30", "2022-06-30", "2023-06-30"]
    rows = []
    for ticker, group, sector, category, base_relative in specs:
        for index, date in enumerate(dates):
            date_effect = 0.09 if date == "2021-06-30" else -0.04
            relative = base_relative + date_effect
            rows.append(
                {
                    "ticker": ticker,
                    "signal_date": date,
                    "coverage_guardrail_status": (
                        "clean" if index == 0 else "research_usable_with_warnings"
                    ),
                    "coverage_quality_label": (
                        "clean" if index == 0 else "delayed_price_anchor"
                    ),
                    "forward_return_12m": "0.10",
                    "relative_return_12m": str(relative),
                    "max_drawdown_12m": "-0.20",
                    "universe_group": group,
                    "sector": sector,
                    "category": category,
                }
            )
    return rows


def _analysis() -> dict:
    return {
        "analysis_run_id": "analysis",
        "ticker_attribution": [
            {
                "ticker": ticker,
                "sector": sector,
                "category": category,
                "universe_group": group,
            }
            for ticker, group, sector, category, _value in [
                ("NVDA", "current_core", "Technology", "semiconductor", 0),
                ("AAPL", "current_core", "Technology", "consumer_platform", 0),
                ("MSFT", "current_core", "Technology", "software_platform", 0),
                ("COST", "current_core", "Consumer Staples", "retail", 0),
                (
                    "NFLX",
                    "expanded_cohort",
                    "Communication Services",
                    "consumer_platform",
                    0,
                ),
                ("ADBE", "expanded_cohort", "Technology", "software_platform", 0),
                ("CRM", "expanded_cohort", "Technology", "software_platform", 0),
                (
                    "AMZN",
                    "expanded_cohort",
                    "Consumer Discretionary",
                    "consumer_platform",
                    0,
                ),
                (
                    "GOOGL",
                    "expanded_cohort",
                    "Communication Services",
                    "consumer_platform",
                    0,
                ),
                ("ORCL", "expanded_cohort", "Technology", "software_platform", 0),
            ]
        ],
        "date_attribution": [
            {"as_of_date": "2021-06-30", "period_label": "supportive_period"},
            {"as_of_date": "2022-06-30", "period_label": "negative_period"},
            {"as_of_date": "2023-06-30", "period_label": "negative_period"},
        ],
    }


def _decomposition() -> dict:
    return {
        "decomposition_run_id": "decomp",
        "backoffice_attribution_run_id": "backoffice",
        "investor_persona_attribution_run_id": "persona",
        "gatekeeper_run_id": "gatekeeper",
        "scorecard_run_id": "scorecard",
        "analysis_run_id": "analysis",
        "expanded_trial_run_id": "expanded",
        "backtest_run_id": "backtest",
    }


def _scorecard() -> dict:
    return {
        "factor_results": [
            {"factor_code": "outlier_dependence", "status": "negative"},
        ],
    }


def _write_fixture(outputs: Path) -> dict:
    decomp_folder = outputs / "backtest_driver_decompositions" / "decomp"
    decomp_folder.mkdir(parents=True)
    decomp_path = decomp_folder / "backtest_driver_decomposition_report.json"
    decomp_path.write_text(json.dumps(_decomposition()), encoding="utf-8")
    (
        outputs
        / "backtest_driver_decompositions"
        / "latest_backtest_driver_decomposition_manifest.json"
    ).write_text(
        json.dumps({"decomposition_run_id": "decomp"}),
        encoding="utf-8",
    )
    backoffice_folder = (
        outputs / "backoffice_evidence_quality_attributions" / "backoffice"
    )
    backoffice_folder.mkdir(parents=True)
    (backoffice_folder / "backoffice_evidence_quality_attribution_report.json").write_text(
        json.dumps({"backoffice_attribution_run_id": "backoffice"}),
        encoding="utf-8",
    )
    scorecard_folder = outputs / "research_evidence_scorecards" / "scorecard"
    scorecard_folder.mkdir(parents=True)
    (scorecard_folder / "research_evidence_scorecard_report.json").write_text(
        json.dumps(_scorecard()),
        encoding="utf-8",
    )
    analysis_folder = outputs / "expanded_trial_analyses" / "analysis"
    analysis_folder.mkdir(parents=True)
    (analysis_folder / "expanded_trial_analysis_report.json").write_text(
        json.dumps(_analysis()),
        encoding="utf-8",
    )
    backtest_folder = outputs / "backtests" / "backtest"
    backtest_folder.mkdir(parents=True)
    with (backtest_folder / "backtest_results.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(_rows()[0]))
        writer.writeheader()
        writer.writerows(_rows())
    return {"decomp_path": decomp_path}


def test_loads_latest_and_explicit_decomposition_manifest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    latest = load_backtest_driver_decomposition_manifest(outputs_root=outputs)
    explicit = load_backtest_driver_decomposition_manifest(
        outputs_root=outputs,
        decomposition_run_id="decomp",
    )
    assert latest["decomposition_run_id"] == "decomp"
    assert explicit["backtest_run_id"] == "backtest"


def test_missing_decomposition_manifest_and_report_raise(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    with pytest.raises(FileNotFoundError, match="manifest not found"):
        load_backtest_driver_decomposition_manifest(outputs_root=outputs)
    source = _write_fixture(outputs)
    source["decomp_path"].unlink()
    with pytest.raises(FileNotFoundError, match="report not found"):
        write_outlier_repair_path_report(outputs_root=outputs)


def test_required_scenarios_are_created() -> None:
    scenarios = compute_exclusion_scenarios(_rows(), _analysis())
    codes = {item["scenario_code"] for item in scenarios}
    assert codes == {
        "full_sample",
        "ex_nvda",
        "ex_top_1_positive_contributor",
        "ex_top_2_positive_contributors",
        "ex_top_3_positive_contributors",
        "ex_current_core",
        "expanded_cohort_only",
        "current_core_only",
        "ex_supportive_date_2021_06_30",
        "negative_dates_only",
        "ex_severe_negative_ticker_nflx",
        "ex_expanded_negative_tickers",
    }


def test_contributors_dependence_and_retest_spec_are_created() -> None:
    report = build_outlier_repair_path(
        outlier_repair_run_id="repair",
        generated_at="2026-06-16T00:00:00+00:00",
        decomposition=_decomposition(),
        backoffice={},
        scorecard=_scorecard(),
        analysis=_analysis(),
        rows=_rows(),
    )
    assert report.work_order_id == "BO-002"
    assert report.contributor_attribution
    assert report.dependence_classification["nvda_dependence_status"]
    assert report.dependence_classification["cohort_dependence_status"]
    assert (
        report.dependence_classification["recommended_next_work_order"]
        == "BO-003 Walk-Forward Stability Repair Plan"
    )
    spec_text = json.dumps(report.retest_spec)
    assert "ex_nvda" in spec_text
    assert "ex_top_2_positive_contributors" in spec_text
    assert "current_core" in spec_text
    assert "expanded_cohort" in spec_text
    assert "ex_supportive_date_2021_06_30" in spec_text


def test_writer_outputs_json_markdown_csv_spec_and_latest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    files = write_outlier_repair_path_report(
        outputs_root=outputs,
        decomposition_run_id="decomp",
        generated_at=datetime(2026, 6, 16, tzinfo=timezone.utc),
    )
    for path in (
        files.markdown_path,
        files.json_path,
        files.scenario_csv_path,
        files.contributor_csv_path,
        files.retest_spec_path,
        files.latest_manifest_path,
    ):
        assert path.is_file()
    payload = json.loads(files.json_path.read_text(encoding="utf-8"))
    assert payload["scenario_analysis"]
    assert payload["contributor_attribution"]
    assert payload["dependence_classification"]
    assert payload["retest_spec"]
    assert payload["recommended_next_work_order"] == (
        "BO-003 Walk-Forward Stability Repair Plan"
    )
    markdown = files.markdown_path.read_text(encoding="utf-8")
    for section in (
        "Important Boundary",
        "Ex-NVDA Analysis",
        "Ex-Top Contributors Analysis",
        "Core vs Expanded Cohort Analysis",
        "Retest Specification",
    ):
        assert section in markdown


def test_attribute_outlier_dependence_returns_required_buckets() -> None:
    contributors = attribute_outlier_dependence(_rows(), _analysis())
    assert contributors["top_positive_contributors_by_average_relative"]
    assert contributors["top_negative_dates"]
    assert contributors["top_positive_cohorts"]
    assert contributors["top_negative_sectors"]


@pytest.mark.parametrize("auto_latest", [False, True])
def test_cli_explicit_and_auto_latest(
    tmp_path: Path, auto_latest: bool
) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    args = [
        "build-outlier-repair-path",
        "--outputs-root",
        str(outputs),
    ]
    if auto_latest:
        args.append("--auto-latest")
    else:
        args.extend(["--decomposition-run-id", "decomp"])
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "Outlier and Ex-NVDA Repair Path" in result.output
    assert "scenario_count=12" in result.output
    assert "recommended_next_work_order=BO-003 Walk-Forward Stability Repair Plan" in (
        result.output
    )
