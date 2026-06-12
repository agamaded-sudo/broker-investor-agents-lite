"""Tests for the research-only archived signal backtesting skeleton."""

import csv
import json
from pathlib import Path

from typer.testing import CliRunner

from broker_agents.backtesting.price_history import (
    forward_return,
    load_price_history,
    max_drawdown,
)
from broker_agents.cli import app

ROOT = Path(__file__).resolve().parents[1]
PRICE_FIXTURES = ROOT / "tests" / "fixtures" / "price_history"


def _write_test_ledger(path: Path) -> None:
    """Create a small ledger containing one complete and one missing ticker."""
    fieldnames = [
        "archive_record_id",
        "ticker",
        "run_id",
        "generated_at",
        "status",
        "readiness_label",
        "source_verification_status",
        "promotion_blocking_categories",
        "total_work_orders",
        "buffett_interest_level",
        "munger_interest_level",
        "fisher_interest_level",
        "lynch_interest_level",
        "bogle_interest_level",
    ]
    rows = [
        {
            "archive_record_id": "COST-test-run-early",
            "ticker": "COST",
            "run_id": "test-run-early",
            "generated_at": "2026-06-11T12:00:00+00:00",
            "status": "completed",
            "readiness_label": "Investor Review Possible with Evidence Gaps",
            "source_verification_status": (
                "partially verified (placeholder-heavy)"
            ),
            "promotion_blocking_categories": (
                "scuttlebutt;management_incentives;index_overlap"
            ),
            "total_work_orders": "21",
            "buffett_interest_level": "Watchlist Interest",
            "munger_interest_level": "Conditional Interest",
            "fisher_interest_level": "Needs More Evidence",
            "lynch_interest_level": "Watchlist Interest",
            "bogle_interest_level": "Low Interest",
        },
        {
            "archive_record_id": "COST-test-run-latest",
            "ticker": "COST",
            "run_id": "test-run-latest",
            "generated_at": "2026-06-11T18:00:00+00:00",
            "status": "completed",
            "readiness_label": "Investor Review Possible with Evidence Gaps",
            "source_verification_status": (
                "partially verified (placeholder-heavy)"
            ),
            "promotion_blocking_categories": (
                "scuttlebutt;management_incentives;index_overlap"
            ),
            "total_work_orders": "21",
            "buffett_interest_level": "Watchlist Interest",
            "munger_interest_level": "Conditional Interest",
            "fisher_interest_level": "Needs More Evidence",
            "lynch_interest_level": "Watchlist Interest",
            "bogle_interest_level": "Low Interest",
        },
        {
            "archive_record_id": "MISSING-test-run",
            "ticker": "MISSING",
            "run_id": "missing-run",
            "generated_at": "2026-06-11T12:00:00+00:00",
            "status": "completed",
            "readiness_label": "Needs Evidence",
            "source_verification_status": "weak",
            "promotion_blocking_categories": "scuttlebutt",
            "total_work_orders": "4",
            "buffett_interest_level": "Needs More Evidence",
            "munger_interest_level": "Needs More Evidence",
            "fisher_interest_level": "Needs More Evidence",
            "lynch_interest_level": "Needs More Evidence",
            "bogle_interest_level": "Needs More Evidence",
        },
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_backtest_signals_creates_research_outputs(tmp_path: Path) -> None:
    ledger_path = tmp_path / "signal_ledger.csv"
    outputs_root = tmp_path / "outputs"
    _write_test_ledger(ledger_path)

    result = CliRunner().invoke(
        app,
        [
            "backtest-signals",
            "--ledger",
            str(ledger_path),
            "--price-fixtures",
            str(PRICE_FIXTURES),
            "--outputs-root",
            str(outputs_root),
            "--lookback-years",
            "5",
            "--dedupe-mode",
            "latest_per_ticker_per_day",
        ],
    )

    assert result.exit_code == 0, result.output
    for field in (
        "Archived Signal Backtest",
        "Backtest Run ID",
        "Backtest Folder",
        "Backtest Summary",
        "Backtest Results",
        "Backtest Manifest",
        "Evaluated Records",
        "Skipped Records",
        "completed",
    ):
        assert field in result.output

    latest_path = outputs_root / "backtests" / "latest_backtest_manifest.json"
    assert latest_path.exists()
    manifest = json.loads(latest_path.read_text(encoding="utf-8"))
    backtest_folder = outputs_root / "backtests" / manifest["backtest_run_id"]
    summary_path = backtest_folder / "backtest_summary.md"
    results_path = backtest_folder / "backtest_results.csv"
    manifest_path = backtest_folder / "backtest_manifest.json"
    assert summary_path.exists()
    assert results_path.exists()
    assert manifest_path.exists()
    assert manifest["ledger_path"] == str(ledger_path)
    assert manifest["lookback_years"] == 5
    assert manifest["dedupe_mode"] == "latest_per_ticker_per_day"
    assert manifest["total_records_before_dedupe"] == 3
    assert manifest["evaluated_records_after_dedupe"] == 2
    assert manifest["duplicate_records_removed"] == 1
    assert manifest["evaluated_records"] == 1
    assert manifest["skipped_records"] == 1
    assert manifest["small_sample_warning"] is True
    assert manifest["minimum_group_size"] == 5
    assert manifest["price_data_type"] == "synthetic_fixture"
    assert manifest["quality_warnings"]
    assert manifest["status"] == "completed"
    assert manifest["benchmark"] == "SPY synthetic fixture"

    with results_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    required_columns = {
        "ticker",
        "run_id",
        "readiness_label",
        "source_verification_status",
        "signal_date",
        "price_start_date",
        "price_end_date_3m",
        "price_end_date_6m",
        "price_end_date_12m",
        "promotion_blocking_count",
        "forward_return_3m",
        "forward_return_6m",
        "forward_return_12m",
        "relative_return_12m",
        "data_status",
    }
    assert required_columns.issubset(rows[0])
    cost = next(row for row in rows if row["ticker"] == "COST")
    missing = next(row for row in rows if row["ticker"] == "MISSING")
    assert cost["forward_return_3m"]
    assert cost["forward_return_6m"]
    assert cost["forward_return_12m"]
    assert cost["relative_return_12m"]
    assert cost["max_drawdown_12m"]
    assert cost["run_id"] == "test-run-latest"
    assert cost["signal_date"] == "2026-06-11"
    assert cost["price_start_date"] == "2026-06-11"
    assert cost["price_end_date_3m"] == "2026-09-11"
    assert cost["price_end_date_6m"] == "2026-12-11"
    assert cost["price_end_date_12m"] == "2027-06-11"
    assert cost["promotion_blocking_count"] == "3"
    assert cost["data_status"] == "complete_synthetic_fixture"
    assert missing["data_status"] == "missing_price_data"
    assert missing["forward_return_12m"] == ""

    summary = summary_path.read_text(encoding="utf-8")
    for text in (
        "Lookback Years: 5",
        "Dedupe Mode: latest_per_ticker_per_day",
        "Records Before Dedupe: 3",
        "Records After Dedupe: 2",
        "Duplicate Records Removed: 1",
        "Evaluated Records: 1",
        "Forward Windows",
        "readiness_label",
        "source_verification_status",
        "Safety Note",
        "synthetic fixtures",
        "Synthetic fixture warning",
        "Small Sample Warning: true",
        "Small sample: category has fewer than 5 records.",
        "buffett_interest_level",
        "munger_interest_level",
        "fisher_interest_level",
        "lynch_interest_level",
        "bogle_interest_level",
    ):
        assert text in summary
    summary_lower = summary.lower()
    for unsafe_phrase in (
        "buy recommendation",
        "sell recommendation",
        "top ranked",
        "best stock",
    ):
        assert unsafe_phrase not in summary_lower
    assert "not a recommendation" in summary_lower
    assert "or trade signal" in summary_lower
    assert "research-only associations" in summary_lower


def test_dedupe_none_keeps_all_records(tmp_path: Path) -> None:
    ledger_path = tmp_path / "signal_ledger.csv"
    outputs_root = tmp_path / "outputs"
    _write_test_ledger(ledger_path)

    result = CliRunner().invoke(
        app,
        [
            "backtest-signals",
            "--ledger",
            str(ledger_path),
            "--price-fixtures",
            str(PRICE_FIXTURES),
            "--outputs-root",
            str(outputs_root),
            "--dedupe-mode",
            "none",
        ],
    )

    assert result.exit_code == 0, result.output
    manifest = json.loads(
        (
            outputs_root
            / "backtests"
            / "latest_backtest_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["dedupe_mode"] == "none"
    assert manifest["total_records_before_dedupe"] == 3
    assert manifest["evaluated_records_after_dedupe"] == 3
    assert manifest["duplicate_records_removed"] == 0
    with Path(manifest["results_path"]).open(
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 3


def test_missing_signal_date_is_reported_without_crashing(
    tmp_path: Path,
) -> None:
    ledger_path = tmp_path / "missing_date_ledger.csv"
    outputs_root = tmp_path / "outputs"
    with ledger_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "archive_record_id",
                "ticker",
                "run_id",
                "generated_at",
                "status",
            ),
        )
        writer.writeheader()
        writer.writerow(
            {
                "archive_record_id": "COST-missing-date",
                "ticker": "COST",
                "run_id": "missing-date",
                "generated_at": "",
                "status": "completed",
            }
        )

    result = CliRunner().invoke(
        app,
        [
            "backtest-signals",
            "--ledger",
            str(ledger_path),
            "--price-fixtures",
            str(PRICE_FIXTURES),
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    manifest = json.loads(
        (
            outputs_root
            / "backtests"
            / "latest_backtest_manifest.json"
        ).read_text(encoding="utf-8")
    )
    with Path(manifest["results_path"]).open(
        encoding="utf-8",
        newline="",
    ) as handle:
        row = next(csv.DictReader(handle))
    assert row["signal_date"] == ""
    assert row["data_status"] == "missing_signal_date"
    assert manifest["evaluated_records"] == 0
    assert manifest["skipped_records"] == 1


def test_price_fixture_calculations_are_deterministic() -> None:
    points = load_price_history(PRICE_FIXTURES / "cost.csv")
    start = points[0].date

    assert forward_return(points, start, 3) == (945 - 920) / 920
    assert forward_return(points, start, 6) == (970 - 920) / 920
    assert forward_return(points, start, 12) == (1025 - 920) / 920
    assert max_drawdown(points, start, 12) == (900 - 920) / 920


def test_backtesting_is_documented_and_demo_runner_remains() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Backtesting Framework Skeleton" in readme
    assert (
        "python -m broker_agents.cli backtest-signals --ledger "
        "data/outputs/signal_archive/signal_ledger.csv"
    ) in readme
    assert "Default lookback is 5 years" in readme
    assert "Backtest Quality Controls" in readme
    assert "--dedupe-mode latest_per_ticker_per_day" in readme
    assert "Default dedupe mode is `latest_per_ticker_per_day`" in readme

    demo_script = (ROOT / "scripts" / "run_first_demo.ps1").read_text(
        encoding="utf-8"
    )
    assert "python -m ruff check ." in demo_script
    assert "python -m pytest --basetemp=.pytest_tmp_demo" in demo_script
    assert "python -m broker_agents.cli deal-intakes" in demo_script
    assert "python -m broker_agents.cli run-deals" in demo_script
