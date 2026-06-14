"""Tests for readiness trial attribution diagnostics."""

import csv
import json
from pathlib import Path

from typer.testing import CliRunner

from broker_agents.backtesting.readiness_trial_diagnostic_report import (
    build_readiness_trial_diagnostic_report,
    render_readiness_trial_diagnostic_report,
)
from broker_agents.backtesting.readiness_trial_export import (
    SAFETY_NOTICE,
    TRIAL_LEDGER_FIELDS,
)
from broker_agents.cli import app

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_PRICES = ROOT / "tests" / "fixtures" / "historical_price_history"
TICKERS = ("MSFT", "AAPL", "NVDA", "COST")
DATES = ("2021-06-30", "2022-06-30", "2023-06-30")


def _trial_row(ticker: str, as_of_date: str) -> dict:
    run_id = f"{ticker.lower()}-{as_of_date}"
    row = {field: "" for field in TRIAL_LEDGER_FIELDS}
    row.update(
        {
            "ticker": ticker,
            "signal_date": as_of_date,
            "as_of_date": as_of_date,
            "generated_at": f"{as_of_date}T00:00:00+00:00",
            "run_id": run_id,
            "archive_record_id": f"{ticker}-{run_id}",
            "status": "completed",
            "trial_signal_source": "historical_readiness_ledger",
            "record_type": "historical_signal_readiness_candidate",
            "source_run_id": run_id,
            "source_run_folder": f"runs/{run_id}",
            "source_candidate_file": "candidate.json",
            "source_assembly_file": "assembly.json",
            "signal_generation_status": "readiness_only",
            "safe_for_historical_signal_generation": "False",
            "not_trade_signal": "True",
            "not_recommendation": "True",
            "not_allocation_instruction": "True",
            "assembly_status": "partial_historical_input",
            "partial_sections_count": "2",
            "readiness_only_sections_count": "8",
            "leakage_risk_sections_count": "10",
            "blocking_reasons_count": "10",
            "warnings_count": "4",
            "coverage_quality_label": "limited_financials",
            "coverage_quality_severity": "moderate",
            "date_coverage_status": "usable_with_warnings",
            "has_delayed_price_anchor": "False",
            "has_limited_financials": "True",
            "warning_count": "2",
            "coverage_guardrail_status": "research_usable_with_warnings",
            "trial_backtest_label": "readiness_only_trial",
            "trial_backtest_allowed": "True",
            "safety_notice": SAFETY_NOTICE,
        }
    )
    return row


def _write_ledger(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRIAL_LEDGER_FIELDS)
        writer.writeheader()
        writer.writerows(
            _trial_row(ticker, date)
            for date in DATES
            for ticker in TICKERS
        )


def _run_backtest(ledger: Path, outputs_root: Path):
    return CliRunner().invoke(
        app,
        [
            "backtest-signals",
            "--ledger",
            str(ledger),
            "--price-provider",
            "csv",
            "--price-fixtures",
            str(HISTORICAL_PRICES),
            "--outputs-root",
            str(outputs_root),
            "--lookback-years",
            "5",
            "--dedupe-mode",
            "latest_per_ticker_per_day",
            "--walk-forward",
            "--walk-forward-frequency",
            "yearly",
        ],
    )


def test_diagnostic_builder_detects_outliers_horizon_and_nvda(
    tmp_path: Path,
) -> None:
    walk_forward_path = tmp_path / "walk_forward_metrics.json"
    walk_forward_path.write_text(
        json.dumps(
            {
                "periods": [
                    {
                        "period": "2021",
                        "sample_size": 4,
                        "tickers": "AAPL;COST;MSFT;NVDA",
                        "median_forward_return_3m": 0.04,
                        "median_forward_return_6m": 0.10,
                        "median_forward_return_12m": -0.02,
                        "median_relative_return_12m": 0.08,
                        "hit_rate_vs_benchmark_12m": 0.75,
                        "positive_return_rate_12m": 0.25,
                        "median_max_drawdown_12m": -0.20,
                        "concentration_warning": False,
                    },
                    {
                        "period": "2022",
                        "sample_size": 4,
                        "tickers": "AAPL;COST;MSFT;NVDA",
                        "median_forward_return_3m": -0.04,
                        "median_forward_return_6m": -0.03,
                        "median_forward_return_12m": 0.37,
                        "median_relative_return_12m": 0.20,
                        "hit_rate_vs_benchmark_12m": 0.75,
                        "positive_return_rate_12m": 1.0,
                        "median_max_drawdown_12m": -0.06,
                        "concentration_warning": False,
                    },
                    {
                        "period": "2023",
                        "sample_size": 4,
                        "tickers": "AAPL;COST;MSFT;NVDA",
                        "median_forward_return_3m": -0.01,
                        "median_forward_return_6m": 0.15,
                        "median_forward_return_12m": 0.46,
                        "median_relative_return_12m": 0.23,
                        "hit_rate_vs_benchmark_12m": 0.75,
                        "positive_return_rate_12m": 1.0,
                        "median_max_drawdown_12m": -0.02,
                        "concentration_warning": False,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    rows = []
    returns = {
        "MSFT": (0.31, 0.34, 0.04),
        "AAPL": (-0.01, 0.43, 0.09),
        "COST": (0.13, 0.22, 0.58),
        "NVDA": (-0.26, 1.86, 1.98),
    }
    for ticker, values in returns.items():
        for date, value in zip(DATES, values, strict=True):
            rows.append(
                {
                    "ticker": ticker,
                    "signal_date": date,
                    "forward_return_3m": "0.01",
                    "forward_return_6m": "0.08",
                    "forward_return_12m": str(value),
                    "relative_return_12m": str(value - 0.1),
                    "data_status": "complete_local_csv",
                }
            )
    manifest = {
        "backtest_run_id": "diagnostic-run",
        "backtest_run_type": "readiness_trial",
        "walk_forward_enabled": True,
        "walk_forward_metrics_path": str(walk_forward_path),
        "walk_forward_stability_judgment": "unstable",
        "duplicate_records_removed": 7,
    }
    metrics = {
        "median_forward_return_3m": 0.02,
        "median_forward_return_6m": 0.11,
        "median_forward_return_12m": 0.27,
        "average_forward_return_12m": 0.47,
        "median_relative_return_12m": 0.13,
        "hit_rate_vs_benchmark_3m": 0.67,
        "hit_rate_vs_benchmark_6m": 0.58,
        "hit_rate_vs_benchmark_12m": 0.75,
        "worst_max_drawdown_12m": -0.49,
        "concentration_warning": True,
        "concentration_details": ["readiness_label:Missing=1.000"],
        "coverage_quality_counts": {"limited_financials": 12},
        "coverage_severity_counts": {"moderate": 12},
        "coverage_guardrail_status_counts": {
            "research_usable_with_warnings": 12
        },
        "clean_record_count": 0,
        "warning_record_count": 12,
        "warning_heavy_record_count": 0,
        "grouped_metrics": {
            "coverage_quality_label": [],
            "coverage_quality_severity": [],
            "coverage_guardrail_status": [
                {
                    "group_name": "research_usable_with_warnings",
                    "sample_size": 12,
                    "median_forward_return_12m": 0.27,
                    "median_relative_return_12m": 0.13,
                    "hit_rate_vs_benchmark_12m": 0.75,
                }
            ],
        },
    }

    report = build_readiness_trial_diagnostic_report(
        manifest=manifest,
        metrics=metrics,
        rows=rows,
    )

    assert report.diagnostic_status == "unstable_needs_deeper_review"
    assert report.sample_size == 12
    assert report.periods_evaluated == 3
    assert len(report.ticker_diagnostics) == 4
    assert len(report.outlier_diagnostics["top_records"]) == 3
    assert len(report.outlier_diagnostics["bottom_records"]) == 3
    assert report.outlier_diagnostics["material_outlier_influence"] is True
    assert (
        report.outlier_diagnostics["interpretation"]
        == "Average return appears lifted by high-return outliers."
    )
    assert report.concentration_diagnostics["nvda_major_driver"] is True
    assert (
        report.concentration_diagnostics["top_contributor_by_average_12m"]
        == "NVDA"
    )
    assert report.horizon_diagnostics["twelve_month_materially_stronger"]
    assert report.coverage_quality_diagnostics[
        "warning_record_count"
    ] == 12
    assert report.coverage_quality_diagnostics[
        "clean_record_count"
    ] == 0
    assert (
        report.stability_diagnostics[
            "strongest_period_by_median_relative_12m"
        ]
        == "2023"
    )
    assert (
        report.stability_diagnostics[
            "weakest_period_by_median_relative_12m"
        ]
        == "2021"
    )
    assert "readiness_label" in report.missing_metadata_fields
    markdown = render_readiness_trial_diagnostic_report(report)
    for heading in (
        "Diagnostic Summary",
        "Aggregate Result Review",
        "Walk-Forward Period Review",
        "Ticker Contribution Review",
        "Outlier Review",
        "Horizon Review",
        "Stability Review",
        "Coverage Quality Guardrails",
        "Data Quality / Metadata Gaps",
        "What This Suggests",
        "What This Does Not Suggest",
        "Next Research Action",
        "Safety Notice",
    ):
        assert heading in markdown
    assert "NVDA Major Driver: True" in markdown
    assert "Strongest Period by Median Relative 12M: 2023" in markdown
    assert "Weakest Period by Median Relative 12M: 2021" in markdown
    assert "Duplicate Records Removed: 7" in markdown
    assert "Concentration Warning: True" in markdown
    assert "Warning Records: 12" in markdown
    assert "It does not prove a strategy." in markdown
    assert (
        "not a recommendation, ranking, vote, average score, consensus, "
        "allocation instruction, rebalancing instruction, trade signal, "
        "execution instruction, or investment advice."
    ) in markdown


def test_readiness_backtest_writes_links_and_regenerates_diagnostic(
    tmp_path: Path,
) -> None:
    ledger = tmp_path / "readiness_trial.csv"
    outputs_root = tmp_path / "outputs"
    _write_ledger(ledger)

    result = _run_backtest(ledger, outputs_root)

    assert result.exit_code == 0, result.output
    assert "Diagnostic Report" in result.output
    assert "Diagnostic Status" in result.output
    assert "Coverage Quality" in result.output
    assert "Warning Records" in result.output
    assert "Clean-Coverage Sensitivity" in result.output
    assert "Sensitivity Status" in result.output
    assert "Clean-Only Available" in result.output
    manifest = json.loads(
        (
            outputs_root / "backtests" / "latest_backtest_manifest.json"
        ).read_text(encoding="utf-8")
    )
    report_path = Path(manifest["readiness_trial_diagnostic_report_path"])
    json_path = Path(
        manifest["readiness_trial_diagnostic_report_json_path"]
    )
    assert report_path.is_file()
    assert json_path.is_file()
    assert manifest["diagnostic_status"] == (
        "unstable_needs_deeper_review"
    )
    assert manifest["next_research_action"] == (
        "expand_dates_tickers_and_enrich_metadata"
    )
    sensitivity_path = Path(
        manifest["clean_coverage_sensitivity_report_path"]
    )
    sensitivity_json_path = Path(
        manifest["clean_coverage_sensitivity_report_json_path"]
    )
    assert sensitivity_path.is_file()
    assert sensitivity_json_path.is_file()
    assert manifest["clean_coverage_sensitivity_status"] == (
        "clean_not_available"
    )
    assert manifest["clean_only_available"] is False
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["sample_size"] == 12
    assert len(payload["period_diagnostics"]) == 3
    assert len(payload["ticker_diagnostics"]) == 4
    assert payload["outlier_diagnostics"]["material_outlier_influence"]
    assert payload["concentration_diagnostics"]["nvda_major_driver"]
    assert payload["horizon_diagnostics"]["twelve_month_materially_stronger"]
    assert "coverage_quality_diagnostics" in payload
    assert "clean_coverage_sensitivity" in payload
    assert payload["clean_coverage_sensitivity"][
        "sensitivity_status"
    ] == "clean_not_available"
    metrics = json.loads(
        Path(manifest["metrics_summary_path"]).read_text(encoding="utf-8")
    )
    assert metrics["grouped_metrics"]["coverage_quality_label"]
    assert metrics["grouped_metrics"]["coverage_quality_severity"]
    assert metrics["grouped_metrics"]["coverage_guardrail_status"]
    with Path(manifest["results_path"]).open(
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["coverage_quality_label"] == "limited_financials"
    assert rows[0]["coverage_quality_severity"] == "moderate"
    assert rows[0]["coverage_guardrail_status"] == (
        "research_usable_with_warnings"
    )
    assert "Clean-Coverage Sensitivity" in report_path.read_text(
        encoding="utf-8"
    )
    decision = Path(
        manifest["readiness_trial_decision_report_path"]
    ).read_text(encoding="utf-8")
    assert "Clean-Coverage Sensitivity Status" in decision
    assert "Clean-Only Available: No" in decision

    regenerate = CliRunner().invoke(
        app,
        [
            "generate-readiness-trial-diagnostic-report",
            "--backtest-folder",
            str(report_path.parent),
        ],
    )
    assert regenerate.exit_code == 0, regenerate.output
    assert "Readiness Trial Diagnostic Report" in regenerate.output
    assert "unstable_needs_deeper_review" in regenerate.output
    assert "Status" in regenerate.output
    assert "completed" in regenerate.output


def test_standard_backtest_does_not_create_diagnostic_report(
    tmp_path: Path,
) -> None:
    ledger = tmp_path / "standard.csv"
    outputs_root = tmp_path / "outputs"
    with ledger.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("ticker", "run_id", "generated_at", "status"),
        )
        writer.writeheader()
        writer.writerow(
            {
                "ticker": "COST",
                "run_id": "standard-run",
                "generated_at": "2023-06-30T00:00:00+00:00",
                "status": "completed",
            }
        )

    result = CliRunner().invoke(
        app,
        [
            "backtest-signals",
            "--ledger",
            str(ledger),
            "--price-provider",
            "csv",
            "--price-fixtures",
            str(HISTORICAL_PRICES),
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    manifest = json.loads(
        (
            outputs_root / "backtests" / "latest_backtest_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["backtest_run_type"] == "standard"
    assert manifest["readiness_trial_diagnostic_report_path"] is None
    assert manifest["readiness_trial_diagnostic_report_json_path"] is None
    assert manifest["diagnostic_status"] is None


def test_task90_documentation_and_demo_runner_remain() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    for text in (
        "readiness trial diagnostic report",
        "period, ticker, outlier, horizon, concentration",
        "what is driving results",
        "generate-readiness-trial-diagnostic-report",
        "research-only",
    ):
        assert text in readme

    demo = (ROOT / "scripts" / "run_first_demo.ps1").read_text(
        encoding="utf-8"
    )
    assert "python -m ruff check ." in demo
    assert "python -m pytest --basetemp=.pytest_tmp_demo" in demo
    assert "python -m broker_agents.cli" in demo
