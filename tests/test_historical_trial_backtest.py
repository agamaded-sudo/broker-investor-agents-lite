"""Tests for the synthetic historical CSV trial path."""

import csv
import json
from pathlib import Path

from typer.testing import CliRunner

from broker_agents.cli import app

ROOT = Path(__file__).resolve().parents[1]
TRIAL_LEDGER = (
    ROOT
    / "data"
    / "inputs"
    / "trial_ledgers"
    / "sample_historical_signal_ledger.csv"
)
HISTORICAL_PRICES = (
    ROOT / "tests" / "fixtures" / "historical_price_history"
)


def test_historical_trial_inputs_are_documented_and_complete() -> None:
    trial_readme = (
        ROOT / "data" / "inputs" / "trial_ledgers" / "README.md"
    )
    assert trial_readme.exists()
    readme_text = " ".join(
        trial_readme.read_text(encoding="utf-8").lower().split()
    )
    for text in (
        "historical signal ledgers",
        "real local csv price",
        "synthetic",
        "pipeline validation",
        "not a source of investment recommendations",
    ):
        assert text in readme_text

    assert TRIAL_LEDGER.exists()
    ledger_text = TRIAL_LEDGER.read_text(encoding="utf-8")
    for ticker in ("MSFT", "AAPL", "NVDA", "COST"):
        assert ticker in ledger_text
    for signal_date in ("2021-06-30", "2022-06-30", "2023-06-30"):
        assert signal_date in ledger_text
    assert "synthetic_trial_ledger" in ledger_text

    for ticker in ("msft", "aapl", "nvda", "cost", "spy"):
        assert (HISTORICAL_PRICES / f"{ticker}.csv").exists()


def test_historical_price_csvs_validate() -> None:
    result = CliRunner().invoke(
        app,
        [
            "validate-price-csv",
            "--price-provider",
            "csv",
            "--price-fixtures",
            str(HISTORICAL_PRICES),
            "--tickers",
            "MSFT,AAPL,NVDA,COST,SPY",
        ],
    )

    assert result.exit_code == 0, result.output
    for ticker in ("MSFT", "AAPL", "NVDA", "COST", "SPY"):
        assert f"ticker={ticker}" in result.output
    assert result.output.count("file_found=true") == 5
    assert result.output.count("price_column_used=adjusted_close") == 5
    assert result.output.count("status=available") == 5
    assert "min_date=2021-06-30" in result.output
    assert "max_date=2024-06-30" in result.output


def test_historical_trial_backtest_generates_forward_returns(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    result = CliRunner().invoke(
        app,
        [
            "backtest-signals",
            "--ledger",
            str(TRIAL_LEDGER),
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
        ],
    )

    assert result.exit_code == 0, result.output
    latest_manifest = (
        outputs_root / "backtests" / "latest_backtest_manifest.json"
    )
    manifest = json.loads(latest_manifest.read_text(encoding="utf-8"))
    assert manifest["historical_trial_ledger"] is True
    assert manifest["trial_signal_source"] == "synthetic_trial_ledger"
    assert manifest["evaluated_records"] == 12
    assert manifest["skipped_records"] == 0
    assert set(manifest["price_column_used_by_ticker"].values()) == {
        "adjusted_close"
    }

    with Path(manifest["results_path"]).open(
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 12
    required_fields = (
        "signal_date",
        "price_start_date",
        "price_end_date_3m",
        "price_end_date_6m",
        "price_end_date_12m",
        "forward_return_3m",
        "forward_return_6m",
        "forward_return_12m",
        "relative_return_12m",
        "data_status",
    )
    for row in rows:
        assert row["trial_signal_source"] == "synthetic_trial_ledger"
        assert row["price_column_used"] == "adjusted_close"
        assert row["data_status"] == "complete_local_csv"
        for field in required_fields:
            assert row[field]

    summary = Path(manifest["summary_path"]).read_text(encoding="utf-8")
    summary_lower = summary.lower()
    assert "historical trial ledger: true" in summary_lower
    assert "trial signal source: synthetic_trial_ledger" in summary_lower
    assert "research and pipeline validation only" in summary_lower
    assert "not a recommendation" in summary_lower
    assert "ranking" in summary_lower
    assert "allocation instruction" in summary_lower
    assert "trade signal" in summary_lower


def test_historical_trial_is_documented_in_main_readme() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Historical CSV Backtest Trial" in readme
    assert "sample_historical_signal_ledger.csv" in readme
    assert "data/inputs/market_prices" in readme
    assert "2021-06-30" in readme
    assert "2022-06-30" in readme
