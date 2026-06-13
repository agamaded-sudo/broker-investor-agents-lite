"""Tests for readiness-aware yearly walk-forward diagnostics."""

import csv
import json
from pathlib import Path

from typer.testing import CliRunner

from broker_agents.backtesting.readiness_trial_export import (
    SAFETY_NOTICE,
    TRIAL_LEDGER_FIELDS,
)
from broker_agents.cli import app

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_PRICES = ROOT / "tests" / "fixtures" / "historical_price_history"
TICKERS = ("MSFT", "AAPL", "NVDA", "COST")
DATES = ("2021-06-30", "2022-06-30", "2023-06-30")


def _readiness_row(ticker: str, as_of_date: str) -> dict:
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
            _readiness_row(ticker, as_of_date)
            for as_of_date in DATES
            for ticker in TICKERS
        )


def test_readiness_trial_walk_forward_outputs_and_stability(
    tmp_path: Path,
) -> None:
    ledger = tmp_path / "readiness_trial.csv"
    outputs_root = tmp_path / "outputs"
    _write_ledger(ledger)

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
            "--lookback-years",
            "5",
            "--dedupe-mode",
            "latest_per_ticker_per_day",
            "--walk-forward",
            "--walk-forward-frequency",
            "yearly",
        ],
    )

    assert result.exit_code == 0, result.output
    for text in (
        "Backtest Run Type",
        "readiness_trial",
        "Walk-Forward",
        "enabled",
        "Periods Evaluated",
        "3",
        "Walk-Forward Summary",
        "Decision Report",
        "Decision Status",
        "Statistical Validity",
        "Walk-Forward Stability",
    ):
        assert text in result.output

    manifest = json.loads(
        (
            outputs_root / "backtests" / "latest_backtest_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["backtest_run_type"] == "readiness_trial"
    assert manifest["readiness_only"] is True
    assert manifest["not_trade_signal"] is True
    assert manifest["not_recommendation"] is True
    assert manifest["not_allocation_instruction"] is True
    assert manifest["walk_forward_enabled"] is True
    assert manifest["walk_forward_frequency"] == "yearly"
    assert manifest["walk_forward_periods_evaluated"] == 3
    assert manifest["readiness_trial_walk_forward"] is True
    assert manifest["readiness_trial_walk_forward_notice"]
    assert manifest["decision_status"]
    assert manifest["statistical_validity"]
    assert manifest["next_required_action"]
    assert manifest["walk_forward_stability_judgment"] in {
        "unstable",
        "mixed",
        "stable_positive",
        "stable_negative",
    }

    for field in (
        "walk_forward_summary_path",
        "walk_forward_results_path",
        "walk_forward_metrics_path",
        "readiness_trial_decision_report_path",
        "readiness_trial_decision_report_json_path",
    ):
        assert Path(manifest[field]).is_file()

    summary = Path(manifest["walk_forward_summary_path"]).read_text(
        encoding="utf-8"
    )
    assert "Readiness Trial Walk-Forward Notice" in summary
    assert "Backtest Run Type: readiness_trial" in summary
    assert "Readiness Only: Yes" in summary
    assert "Not Trade Signal: Yes" in summary
    assert "Not Recommendation: Yes" in summary
    assert "Not Allocation Instruction: Yes" in summary
    assert (
        "These walk-forward results must not be interpreted as investment "
        "recommendations or trading signals."
    ) in summary

    with Path(manifest["walk_forward_results_path"]).open(
        encoding="utf-8",
        newline="",
    ) as handle:
        period_rows = list(csv.DictReader(handle))
    assert [row["period"] for row in period_rows] == ["2021", "2022", "2023"]
    for row in period_rows:
        assert row["period_start_date"]
        assert row["period_end_date"]
        assert row["period_start"] == row["period_start_date"]
        assert row["period_end"] == row["period_end_date"]
        assert row["sample_size"] == "4"
        assert set(row["tickers"].split(";")) == set(TICKERS)
        for field in (
            "median_forward_return_3m",
            "median_forward_return_6m",
            "median_forward_return_12m",
            "average_forward_return_12m",
            "median_relative_return_12m",
            "hit_rate_vs_benchmark_12m",
            "positive_return_rate_12m",
            "median_max_drawdown_12m",
            "small_sample_warning",
            "concentration_warning",
        ):
            assert row[field] != ""

    metrics = json.loads(
        Path(manifest["walk_forward_metrics_path"]).read_text(
            encoding="utf-8"
        )
    )
    assert metrics["total_periods"] == 3
    assert [period["period"] for period in metrics["periods"]] == [
        "2021",
        "2022",
        "2023",
    ]

    report = json.loads(
        Path(manifest["readiness_trial_decision_report_json_path"]).read_text(
            encoding="utf-8"
        )
    )
    assert report["walk_forward_enabled"] is True
    assert report["walk_forward_periods_evaluated"] == 3
    assert report["walk_forward_stability_judgment"] in {
        "unstable",
        "mixed",
        "stable_positive",
        "stable_negative",
    }
    assert report["best_period"] in {"2021", "2022", "2023"}
    assert report["weakest_period"] in {"2021", "2022", "2023"}
    assert len(report["period_summaries"]) == 3
    decision_markdown = Path(
        manifest["readiness_trial_decision_report_path"]
    ).read_text(encoding="utf-8")
    assert "Walk-Forward Stability" in decision_markdown
    assert "Walk-Forward Enabled: Yes" in decision_markdown
    assert "Periods Evaluated: 3" in decision_markdown
    assert "Stability Judgment:" in decision_markdown


def test_task89_documentation_and_demo_runner_remain() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    for text in (
        "readiness trial walk-forward backtest",
        "readiness-only artifacts by time period",
        "driven by a single year",
        "--walk-forward --walk-forward-frequency yearly",
        "after multi-date sample generation",
        "missing metadata and readiness-only sections",
        "dedupe remains important",
    ):
        assert text in readme

    demo = (ROOT / "scripts" / "run_first_demo.ps1").read_text(
        encoding="utf-8"
    )
    assert "python -m ruff check ." in demo
    assert "python -m pytest --basetemp=.pytest_tmp_demo" in demo
    assert "python -m broker_agents.cli" in demo
